import io
import struct
import zipfile

import pytest

from chocotools import http


def make_zip(names: list[str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name in names:
            zf.writestr(name, b"x" * 10)
    return buf.getvalue()


def test_root_from_central_directory_tail():
    data = make_zip(["jdk-27/", "jdk-27/bin/java.exe", "jdk-27/release"])
    tail_start = max(0, len(data) - 200)
    tail = data[tail_start:]
    offset, size = http._find_central_directory(tail, tail_start, lambda s, e: data[s : e + 1])
    cd = data[offset : offset + size]
    assert http.root_dir_from_names(http._central_directory_names(cd)) == "jdk-27"


def test_root_dir_rules():
    assert http.root_dir_from_names(["a/", "a/b"]) == "a"
    with pytest.raises(http.HttpError):
        http.root_dir_from_names(["a/b", "c/d"])
    with pytest.raises(http.HttpError):
        http.root_dir_from_names(["README", "a/b"])


def test_content_range_total():
    assert http._content_range_total("bytes 100-199/200") == 200
    with pytest.raises(http.HttpError):
        http._content_range_total("bytes 0-1/*")


class FakeResp(io.BytesIO):
    def __init__(self, status, body=b"", headers=None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}


def test_zip_root_dir_ranges_and_full_fallback(monkeypatch):
    data = make_zip(["wildfly-41.0.1.Final/", "wildfly-41.0.1.Final/bin/standalone.bat"])
    client = http.Client()

    def head(url, *, follow_redirects=True):
        return http.Response(200, {"content-length": str(len(data))}, b"", url)

    def request(url, *, method="GET", headers=None, follow_redirects=True, stream=False):
        rng = (headers or {}).get("Range")
        if rng is None:
            return FakeResp(200, data)
        start, end = (int(x) for x in rng.split("=")[1].split("-"))
        body = data[start : end + 1]
        resp = FakeResp(206, body, {"Content-Range": f"bytes {start}-{end}/{len(data)}"})
        return resp if stream else http.Response(206, {}, body, url)

    monkeypatch.setattr(client, "head", head)
    monkeypatch.setattr(client, "request", request)
    assert client.zip_root_dir("https://github.com/x.zip") == "wildfly-41.0.1.Final"

    # Server ignores Range -> full download path.
    monkeypatch.setattr(client, "request", lambda url, **kw: FakeResp(200, data))
    assert client.zip_root_dir("https://github.com/x.zip") == "wildfly-41.0.1.Final"


def test_github_token_only_for_api_host(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    client = http.Client()
    assert client._headers("https://api.github.com/repos/a/b", None)["Authorization"] == "Bearer tok"
    assert "Authorization" not in client._headers("https://github.com/a/b/releases/download/x", None)
    assert "Authorization" not in client._headers("https://api.adoptium.net/v3", None)


def test_safe_redirect_drops_authorization():
    import urllib.request

    req = urllib.request.Request("https://api.github.com/x", headers={"Authorization": "Bearer t"})
    new = http._SafeRedirect().redirect_request(req, None, 302, "Found", {}, "https://objects.githubusercontent.com/y")
    assert "Authorization" not in new.headers


def test_disk_cache_and_memo(tmp_path, monkeypatch):
    client = http.Client(cache_dir=tmp_path)
    calls = []

    def request(url, **kw):
        calls.append(url)
        return http.Response(200, {}, b'{"a": 1}', url)

    monkeypatch.setattr(client, "request", request)
    assert client.get_json("https://api.example/x") == {"a": 1}
    assert client.get_json("https://api.example/x") == {"a": 1}
    fresh = http.Client(cache_dir=tmp_path)
    monkeypatch.setattr(fresh, "request", request)
    assert fresh.get_json("https://api.example/x") == {"a": 1}
    assert calls == ["https://api.example/x"]


def test_retry_after_parsing():
    assert http.Client._retry_after({"Retry-After": "3"}) == 3.0
    assert http.Client._retry_after({}) is None


def test_eocd_struct_sanity():
    data = make_zip(["a/", "a/b"])
    pos = data.rfind(b"PK\x05\x06")
    size, offset = struct.unpack("<II", data[pos + 12 : pos + 20])
    assert data[offset : offset + 4] == b"PK\x01\x02" and size > 0
