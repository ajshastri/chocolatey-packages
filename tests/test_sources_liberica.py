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


API_21 = ("https://api.bell-sw.com/v1/liberica/releases?version-feature=21&bundle-type=jdk&os=windows&arch=x86"
          "&bitness=64&package-type=msi&version-modifier=latest")


def api_entry(version: str, patch: int, build: int) -> dict:
    # BellSoft API fields as served on 2026-10-25: 21.0.13.0.2+5 has patchVersion 0 and no 5th-part field
    numeric = version.split("+")[0]
    if numeric.startswith("8u"):
        feature, interim, update = 8, 0, int(numeric[2:])
    else:
        feature, interim, update = (int(p) for p in numeric.split(".")[:3])
    name = f"bellsoft-jdk{version}-windows-amd64.msi"
    return {"version": version, "featureVersion": feature, "interimVersion": interim, "updateVersion": update,
            "patchVersion": patch, "buildVersion": build, "GA": True, "os": "windows", "bitness": 64,
            "packageType": "msi", "bundleType": "jdk", "filename": name,
            "downloadUrl": f"https://github.com/bell-sw/Liberica/releases/download/{version}/{name}"}


def test_key_orders_on_the_fifth_part_not_the_build():
    entries = [api_entry("21.0.13+11", 0, 11), api_entry("21.0.13.0.2+5", 0, 5), api_entry("21.0.12.1+1", 1, 1)]
    assert max(entries, key=liberica._key)["version"] == "21.0.13.0.2+5"
    respins = [api_entry("21.0.13.0.2+6", 0, 6), api_entry("21.0.13.0.3+1", 0, 1)]
    assert max(respins, key=liberica._key)["version"] == "21.0.13.0.3+1"
    builds = [api_entry("21.0.13.0.2+5", 0, 5), api_entry("21.0.13.0.2+6", 0, 6)]
    assert max(builds, key=liberica._key)["version"] == "21.0.13.0.2+6"
    eights = [api_entry("8u504+1", 0, 1), api_entry("8u512+5", 0, 5)]
    assert max(eights, key=liberica._key)["version"] == "8u512+5"


def test_full_api_list_picks_five_part_release():
    # Without version-modifier=latest the API also lists 21.0.13+11 (build 11 > 5): it must not win.
    entries = [api_entry("21.0.13+11", 0, 11), api_entry("21.0.13.0.2+5", 0, 5), api_entry("21.0.12.1+1", 1, 1)]
    name = "bellsoft-jdk21.0.13.0.2+5-windows-amd64.msi"
    rel = {"tag_name": "21.0.13.0.2+5", "assets": [{"name": name, "digest": "sha256:" + "b" * 64}]}
    client = FakeClient(get={API_21: json.dumps(entries),
                             "https://api.github.com/repos/bell-sw/Liberica/releases/tags/21.0.13.0.2%2B5": json.dumps(rel)},
                        use_index=False)
    r = liberica.fetch(pkg(vendor="liberica", major=21, image="jdk", variant="std"), client=client)
    assert r.version == "21.0.13.2"
    assert r.version_raw == "21.0.13.0.2+5"
    assert r.urls["x64"] == f"https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.2+5/{name}"
    assert r.sha256["x64"] == "b" * 64


def test_no_ga_entries():
    url = (
        "https://api.bell-sw.com/v1/liberica/releases?version-feature=21&bundle-type=jdk&os=windows&arch=x86"
        "&bitness=64&package-type=msi&version-modifier=latest"
    )
    client = FakeClient(get={url: "[]"}, use_index=False)
    with pytest.raises(sources.SourceError, match="no GA"):
        liberica.fetch(pkg(vendor="liberica", major=21, image="jdk", variant="std"), client=client)
