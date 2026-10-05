import pytest

from chocotools import sources
from chocotools.sources import graalvm
from conftest import pkg

URL = (
    "https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.3.4.1/"
    "graalvm-community-jdk-25i3-25.0.4.1_windows-x64_bin.zip"
)


def test_graalvm25_version_from_foojay_files_from_github(fake_client):
    r = graalvm.fetch(pkg(vendor="graalvm", major=25), client=fake_client)
    assert r.version == "25.3.4.1"
    assert r.urls == {"x64": URL}
    assert r.checksum_source == "github asset digest"
    assert "foojay" not in r.urls["x64"]


def test_graalvm17_frozen_lookup_uses_sha256_asset(fake_client):
    r = graalvm.fetch(pkg(vendor="graalvm", major=17), client=fake_client)
    assert r.version == "17.0.9"
    assert r.sha256["x64"] == "285e045bfc0b87d2b61958fea97444c3c6c7e68fba3fdbbe146622328b52ec38"


def test_dir_version():
    assert graalvm.dir_version("graalvm-community-openjdk-25.0.2+10.1") == "25.0.2+10.1"
    # 25i3 zips changed their root dir; the scripts still expect the old prefix.
    with pytest.raises(sources.SourceError, match="graalvm-community-openjdk-"):
        graalvm.dir_version("graalvm-community-25.3.4.1+1.1")


def test_resolve_extras(fake_client):
    r = graalvm.fetch(pkg(vendor="graalvm", major=25), client=fake_client)
    fake_client.zip_roots[URL] = "graalvm-community-openjdk-25.0.4.1+1.1"
    assert sources.resolve_extras(pkg(vendor="graalvm", major=25), r, fake_client) == {"dir_version": "25.0.4.1+1.1"}
