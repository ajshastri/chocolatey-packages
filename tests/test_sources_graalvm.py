import copy
import json

import pytest

from chocotools import checks, sources, versioning
from chocotools.sources import graalvm
from conftest import FIXTURES, pkg

URL = (
    "https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.3.4.1/"
    "graalvm-community-jdk-25i3-25.0.4.1_windows-x64_bin.zip"
)
URL_25I4 = (
    "https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.4.4.1.1/"
    "graalvm-community-jdk-25i4-25.0.4.1.1_windows-x64_bin.zip"
)
FOOJAY_25 = (
    "https://api.foojay.io/disco/v3.0/packages?version=25&distribution=graalvm_community&architecture=amd64"
    "&archive_type=zip&operating_system=windows&package_type=jdk&latest=available"
)
RELEASES = "https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=40"
NAME_25I4 = "graalvm-community-jdk-25i4-25.0.4.1.1_windows-x64_bin.zip"
# foojay-25-dup.json, live 2026-10-27: two records for the 25i4 zip
ORIGINAL = "a02a1aa7aa6b7aa4d99b152cd2867d22"  # java_version 25.4.4.1, distribution_version 25.0.4.1.1
SWAPPED = "1b445e98b0d30b2a78e48ee39c4137d1"  # java_version 25.0.4.1, distribution_version 25.4.4.1.1


def foojay_dup() -> list[dict]:
    return json.loads((FIXTURES / "graalvm" / "foojay-25-dup.json").read_text(encoding="utf-8"))["result"]


def serve_foojay(fake_client, records):
    fake_client.get_map[FOOJAY_25] = json.dumps({"result": records}).encode("utf-8")


def github_releases(fake_client) -> list[dict]:
    return json.loads(fake_client.get_map[RELEASES])


def serve_releases(fake_client, releases):
    fake_client.get_map[RELEASES] = json.dumps(releases).encode("utf-8")


@pytest.mark.parametrize("drop", [ORIGINAL, None, SWAPPED], ids=["swapped-only", "both", "original-only"])
def test_graalvm25_version_from_tag_not_foojay_java_version(fake_client, drop):
    # sync run 40489959531 saw only the swapped record and computed 25.0.4.1 for the 25i4 zip
    serve_foojay(fake_client, [e for e in foojay_dup() if e["id"] != drop])
    p = pkg(vendor="graalvm", major=25)
    r = graalvm.fetch(p, client=fake_client)
    assert (r.version, r.version_raw) == ("25.4.4.1", "graal-25.4.4.1.1")
    assert r.urls == {"x64": URL_25I4}
    assert r.raw == {"filename": NAME_25I4, "tag_name": "graal-25.4.4.1.1"}
    assert checks.check_release(p, r) == []
    assert checks.check_url_version(p, r.version, r.urls["x64"]) == []


def test_graalvm25_older_layout_still_maps(fake_client):
    serve_foojay(fake_client, [e for e in foojay_dup() if e["filename"] != NAME_25I4])
    r = graalvm.fetch(pkg(vendor="graalvm", major=25), client=fake_client)
    assert (r.version, r.version_raw) == ("25.3.4.1", "graal-25.3.4.1")
    assert r.urls == {"x64": URL}


def test_graalvm25_newer_release_wins(fake_client):
    # a later innovation release listed in the swapped form: its java_version (25.0.4.1) sorts
    # below the 25i4 original's (25.4.4.1), but its file name and tag are newer
    name = "graalvm-community-jdk-25i5-25.0.4.1.1_windows-x64_bin.zip"
    records = foojay_dup()
    newer = copy.deepcopy(next(e for e in records if e["id"] == SWAPPED))
    newer.update(id="f" * 32, filename=name)
    serve_foojay(fake_client, [*records, newer])
    releases = github_releases(fake_client)
    rel = copy.deepcopy(next(r for r in releases if r["tag_name"] == "graal-25.4.4.1.1"))
    rel["tag_name"] = "graal-25.5.4.1.1"
    rel["assets"] = [{"name": name, "digest": "sha256:" + "a" * 64,
                      "browser_download_url": f"https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.5.4.1.1/{name}"}]
    serve_releases(fake_client, [rel, *releases])
    p = pkg(vendor="graalvm", major=25)
    r = graalvm.fetch(p, client=fake_client)
    assert (r.version, r.raw["filename"]) == ("25.5.4.1", name)
    assert r.sha256 == {"x64": "a" * 64}
    assert checks.check_url_version(p, r.version, r.urls["x64"]) == []


@pytest.mark.parametrize("tag, match", [
    ("graal-25.4.4.1.1-rc1", "no graalvm version token"),  # tag the URL rule cannot parse
    ("graal-25.3.4.1", "does not match asset"),  # tag and asset name disagree
    ("jdk-25.0.4", r"maps to 25\.0\.4, but its asset .* is 25\.4\.4\.1"),  # parses, but to another version
])
def test_graalvm25_unparseable_tag_fails(fake_client, tag, match):
    serve_foojay(fake_client, foojay_dup())
    releases = github_releases(fake_client)
    for rel in releases:
        if rel["tag_name"] == "graal-25.4.4.1.1":
            rel["tag_name"] = tag
            for asset in rel["assets"]:
                asset["browser_download_url"] = asset["browser_download_url"].replace("graal-25.4.4.1.1", tag)
    serve_releases(fake_client, releases)
    with pytest.raises(sources.SourceError, match=match):
        graalvm.fetch(pkg(vendor="graalvm", major=25), client=fake_client)


def test_graalvm25_unexpected_file_name_fails(fake_client):
    records = foojay_dup()
    records.append({**records[0], "id": "e" * 32, "filename": "graalvm-community-jdk-25i6-26.0.1_windows-x64_bin.zip"})
    serve_foojay(fake_client, records)
    with pytest.raises(sources.SourceError, match=r"is not <M>i<I>-<M>\.0\.<update>"):
        graalvm.fetch(pkg(vendor="graalvm", major=25), client=fake_client)


def test_graalvm25_two_files_for_newest_version_fail(fake_client):
    records = foojay_dup()
    records.append({**records[0], "id": "d" * 32, "filename": "graalvm-community-jdk-25.4.4.1.1_windows-x64_bin.zip"})
    serve_foojay(fake_client, records)
    with pytest.raises(sources.SourceError, match="more than one GraalVM file for the same version"):
        graalvm.fetch(pkg(vendor="graalvm", major=25), client=fake_client)


def test_file_version():
    assert graalvm.file_version(NAME_25I4) == (25, 4, 4, 1, 1)
    assert graalvm.file_version("graalvm-community-jdk-25i3-25.0.4.1_windows-x64_bin.zip") == (25, 3, 4, 1)
    assert graalvm.file_version("graalvm-community-jdk-25.0.2_windows-x64_bin.zip") == (25, 0, 2)
    with pytest.raises(sources.SourceError, match="unexpected GraalVM file name"):
        graalvm.file_version("graalvm-community-jdk-25i4-25.0.4.1.1_linux-x64_bin.tar.gz")


def test_graalvm25_version_from_foojay_files_from_github(fake_client):
    # foojay-25.json was recorded while 25.3.4.1 was the newest GraalVM 25 build
    r = graalvm.fetch(pkg(vendor="graalvm", major=25), client=fake_client)
    assert r.version == "25.3.4.1"
    assert r.urls == {"x64": URL}
    assert r.checksum_source == "github asset digest"
    assert "foojay" not in r.urls["x64"]
    assert r.raw["tag_name"] == "graal-25.3.4.1"
    assert versioning.url_version("graalvm", r.urls["x64"]) == r.version


def test_graalvm25_five_part_tag(fake_client):
    # foojay-25-25.4.4.1.json: recorded when graal-25.4.4.1.1 (asset 25i4-25.0.4.1.1) came out
    fake_client.get_map[FOOJAY_25] = (FIXTURES / "graalvm" / "foojay-25-25.4.4.1.json").read_bytes()
    p = pkg(vendor="graalvm", major=25)
    r = graalvm.fetch(p, client=fake_client)
    assert (r.version, r.version_raw) == ("25.4.4.1", "graal-25.4.4.1.1")
    assert r.urls == {"x64": URL_25I4}
    assert r.sha256 == {"x64": "2733ea1331f1a98b05dd55a768b07347051dad48f030dbbfa191b11a2ccf4144"}
    assert r.raw == {"filename": "graalvm-community-jdk-25i4-25.0.4.1.1_windows-x64_bin.zip",
                     "tag_name": "graal-25.4.4.1.1"}
    assert checks.check_release(p, r) == []
    # the URL check maps the 5-part tag to the same 4-part version sync writes
    assert versioning.url_version("graalvm", r.urls["x64"]) == r.version
    assert checks.check_url_version(p, r.version, r.urls["x64"]) == []


def test_graalvm17_frozen_lookup_uses_sha256_asset(fake_client):
    r = graalvm.fetch(pkg(vendor="graalvm", major=17), client=fake_client)
    assert r.version == "17.0.9"
    assert r.sha256["x64"] == "285e045bfc0b87d2b61958fea97444c3c6c7e68fba3fdbbe146622328b52ec38"


def test_dir_version_accepts_both_layouts():
    # up to 25.0.2 the zip root carried "openjdk-"; 25i3 zips dropped it
    assert graalvm.dir_version("graalvm-community-openjdk-25.0.2+10.1") == "graalvm-community-openjdk-25.0.2+10.1"
    assert graalvm.dir_version("graalvm-community-25.3.4.1+1.1") == "graalvm-community-25.3.4.1+1.1"
    assert graalvm.dir_version("graalvm-community-25.4.4.1.1+1.1") == "graalvm-community-25.4.4.1.1+1.1"  # 25i4


@pytest.mark.parametrize("root", ["graalvm-ce-25.3.4.1", "graalvm-community-", "graalvm-community-openjdk-",
                                  "graalvm-community-25 1", "x/graalvm-community-25.3.4.1"])
def test_dir_version_rejects_other_roots(root):
    with pytest.raises(sources.SourceError, match="unexpected GraalVM zip root"):
        graalvm.dir_version(root)


def test_resolve_extras(fake_client):
    r = graalvm.fetch(pkg(vendor="graalvm", major=25), client=fake_client)
    fake_client.zip_roots[URL] = "graalvm-community-25.3.4.1+1.1"
    assert sources.resolve_extras(pkg(vendor="graalvm", major=25), r, fake_client) == {
        "dir_version": "graalvm-community-25.3.4.1+1.1"
    }
