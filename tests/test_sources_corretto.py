import pytest

from chocotools import sources
from chocotools.sources import corretto
from conftest import FIXTURES, pkg

LATEST21 = "https://corretto.aws/downloads/latest/amazon-corretto-21-x64-windows-jdk.msi"


def test_corretto21(fake_client):
    r = corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)
    assert r.version == "21.0.12.121"
    assert r.version_raw == "21.0.12.12.1"
    assert r.urls["x64"] == "https://corretto.aws/downloads/resources/21.0.12.12.1/amazon-corretto-21.0.12.12.1-windows-x64.msi"
    expected = (FIXTURES / "corretto" / "amazon-corretto-21-x64-windows-jdk.msi.latest_sha256.txt").read_text().strip()
    assert r.sha256["x64"] == expected
    assert r.checksum_source == "corretto.aws latest_sha256"


def test_corretto8_jre(fake_client):
    r = corretto.fetch(pkg(vendor="corretto", major=8, image="jre"), client=fake_client)
    assert r.version == "8.504.4.1"
    assert r.urls["x64"].endswith("/8.504.04.1/amazon-corretto-8.504.04.1-windows-x64-jre.msi")


def test_latest_redirect_mismatch_fails(fake_client):
    fake_client.head_map[LATEST21] = {
        "status": 302,
        "headers": {"location": "/downloads/resources/21.0.13.1.1/amazon-corretto-21.0.13.1.1-windows-x64.msi"},
    }
    with pytest.raises(sources.SourceError, match="GitHub tag is 21.0.12.12.1"):
        corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)


def test_no_redirect_fails(fake_client):
    fake_client.head_map[LATEST21] = {"status": 200, "headers": {}}
    with pytest.raises(sources.SourceError, match="did not redirect"):
        corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)


def test_jre_only_for_8():
    with pytest.raises(sources.SourceError):
        corretto.filename(pkg(vendor="corretto", major=21, image="jre"), "21.0.12.12.1")
