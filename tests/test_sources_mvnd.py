import pytest

from chocotools import sources
from chocotools.sources import mvnd
from conftest import pkg

URL = "https://github.com/apache/maven-mvnd/releases/download/1.0.6/maven-mvnd-1.0.6-windows-amd64.zip"


def test_mvnd(fake_client):
    r = mvnd.fetch(pkg(vendor="mvnd", major=None, image=None), client=fake_client)
    assert r.version == "1.0.6"
    assert r.urls == {"x64": URL}
    assert r.sha256 == {"x64": "caba9e00736b8c0c62b9238ee75bc64294a0df42e45ecd513fee1914da3fd6cf"}
    fake_client.zip_roots[URL] = "maven-mvnd-1.0.6-windows-amd64"
    assert sources.resolve_extras(pkg(vendor="mvnd"), r, fake_client) == {"dir_version": "maven-mvnd-1.0.6-windows-amd64"}


def test_dir_version_rejects_other_roots():
    with pytest.raises(sources.SourceError):
        mvnd.dir_version("mvnd-1.0.6")
