import pytest

from chocotools import sources
from chocotools.sources import zulu
from conftest import FakeClient, pkg


def test_zulu21(fake_client):
    r = zulu.fetch(pkg(vendor="zulu", major=21), client=fake_client)
    assert r.version == "21.52.203"
    assert r.version_raw == "21.52.203.0"
    assert r.urls["x64"] == "https://cdn.azul.com/zulu/bin/zulu21.52.203-ca-fx-jdk21.0.12.1-win_x64.msi"
    assert r.sha256["x64"] == "b8267385658ac2a6d51448fbd27d37dc685f41720f62519e0d41ca01ddb9b61f"


def test_zulu8_four_parts(fake_client):
    assert zulu.fetch(pkg(vendor="zulu", major=8), client=fake_client).version == "8.96.0.205"


def test_zulu7_query_and_value(fake_client):
    assert "javafx_bundled=false" in zulu.list_url(7) and "distro_version" not in zulu.list_url(7)
    r = zulu.fetch(pkg(vendor="zulu", major=7), client=fake_client)
    assert r.version == "7.56.0.11"


def test_empty_listing_fails_closed():
    client = FakeClient(get={zulu.list_url(21): "[]"}, use_index=False)
    with pytest.raises(sources.SourceError, match="no package"):
        zulu.fetch(pkg(vendor="zulu", major=21), client=client)
