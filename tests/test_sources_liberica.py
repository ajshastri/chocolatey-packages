import json

import pytest

from chocotools import sources
from chocotools.sources import liberica
from conftest import FIXTURES, FakeClient, pkg


def digest_for(tag_file: str, name: str) -> str:
    rel = json.loads((FIXTURES / "liberica" / tag_file).read_text(encoding="utf-8"))
    return next(a["digest"] for a in rel["assets"] if a["name"] == name).split(":", 1)[1]


def test_liberica21_std_picks_cspu(fake_client):
    r = liberica.fetch(pkg(vendor="liberica", major=21, image="jdk", variant="std"), client=fake_client)
    assert r.version == "21.0.12.1"
    assert r.version_raw == "21.0.12.1+1"
    name = "bellsoft-jdk21.0.12.1+1-windows-amd64.msi"
    assert r.urls["x64"] == f"https://github.com/bell-sw/Liberica/releases/download/21.0.12.1+1/{name}"
    assert r.sha256["x64"] == digest_for("github-releases-tags-21.0.12.1-1.json", name)
    assert r.checksum_source == "github asset digest"


def test_liberica17_lite_restored_from_bellsoft(fake_client):
    r = liberica.fetch(pkg(vendor="liberica", major=17, image="jdk", variant="lite"), client=fake_client)
    assert r.version == "17.0.20.1"
    assert r.urls["x64"].endswith("bellsoft-jdk17.0.20.1+1-windows-amd64-lite.msi")


def test_liberica8_version_scheme(fake_client):
    r = liberica.fetch(pkg(vendor="liberica", major=8, image="jre", variant="std"), client=fake_client)
    assert r.version == "8.0.504.1"


def test_bundle_types():
    assert liberica.bundle_type(pkg(vendor="liberica", image="jre", variant="full")) == "jre-full"
    with pytest.raises(sources.SourceError):
        liberica.bundle_type(pkg(vendor="liberica", image="jre", variant="lite"))


def test_missing_asset_fails_closed(fake_client):
    url = next(u for u in fake_client.get_map if "releases/tags/21.0.12.1%2B1" in u)
    rel = json.loads(fake_client.get_map[url])
    rel["assets"] = []
    fake_client.get_map[url] = json.dumps(rel).encode()
    with pytest.raises(sources.SourceError, match="no asset"):
        liberica.fetch(pkg(vendor="liberica", major=21, image="jdk", variant="std"), client=fake_client)


def test_digest_missing_falls_back_to_download(fake_client):
    url = next(u for u in fake_client.get_map if "releases/tags/21.0.12.1%2B1" in u)
    rel = json.loads(fake_client.get_map[url])
    for a in rel["assets"]:
        a["digest"] = None
    fake_client.get_map[url] = json.dumps(rel).encode()
    name = "bellsoft-jdk21.0.12.1+1-windows-amd64.msi"
    dl = next(a["browser_download_url"] for a in rel["assets"] if a["name"] == name)
    fake_client.sha256_map[dl] = "c" * 64
    r = liberica.fetch(pkg(vendor="liberica", major=21, image="jdk", variant="std"), client=fake_client)
    assert r.sha256["x64"] == "c" * 64 and r.checksum_source == "computed from download"


def test_no_ga_entries():
    url = (
        "https://api.bell-sw.com/v1/liberica/releases?version-feature=21&bundle-type=jdk&os=windows&arch=x86"
        "&bitness=64&package-type=msi&version-modifier=latest"
    )
    client = FakeClient(get={url: "[]"}, use_index=False)
    with pytest.raises(sources.SourceError, match="no GA"):
        liberica.fetch(pkg(vendor="liberica", major=21, image="jdk", variant="std"), client=client)
