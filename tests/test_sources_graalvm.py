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
    assert (r.version, r.version_raw) == ("25.4.4.1", "25.4.4.1")
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
