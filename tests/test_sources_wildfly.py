import pytest

from chocotools import sources
from chocotools.sources import wildfly
from conftest import pkg

URL = "https://github.com/wildfly/wildfly/releases/download/41.0.1.Final/wildfly-41.0.1.Final.zip"


def test_wildfly(fake_client):
    r = wildfly.fetch(pkg(vendor="wildfly", major=None, image=None, arch=("neutral",)), client=fake_client)
    assert r.version == "41.0.1"
    assert r.urls == {"neutral": URL}
    assert r.checksum_source == "github asset digest"
    fake_client.zip_roots[URL] = "wildfly-41.0.1.Final"
    assert sources.resolve_extras(pkg(vendor="wildfly", arch=("neutral",)), r, fake_client) == {
        "dir_version": "41.0.1.Final"
    }


def test_wildfly_requires_neutral(fake_client):
    with pytest.raises(sources.SourceError):
        wildfly.fetch(pkg(vendor="wildfly"), client=fake_client)
