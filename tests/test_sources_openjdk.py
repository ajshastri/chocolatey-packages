import pytest

from chocotools import sources
from chocotools.sources import openjdk
from conftest import FakeClient, pkg

URL = "https://download.java.net/java/GA/jdk27/55ce5470a6294008af0057ff4626d0e5/35/GPL/openjdk-27_windows-x64_bin.zip"


def test_openjdk27(fake_client):
    r = openjdk.fetch(pkg(vendor="openjdk", major=27), client=fake_client)
    assert r.version == "27.0.0"
    assert r.version_raw == "27"
    assert r.urls == {"x64": URL}
    assert len(r.sha256["x64"]) == 64


def test_not_ga_page_fails():
    client = FakeClient(get={"https://jdk.java.net/28/": "<h1>JDK 28 Early-Access Builds</h1>"}, use_index=False)
    with pytest.raises(sources.SourceError, match="not a GA release page"):
        openjdk.fetch(pkg(vendor="openjdk", major=28), client=client)


def test_dir_version_and_extras(fake_client):
    assert openjdk.dir_version("jdk-27") == "27"
    with pytest.raises(sources.SourceError):
        openjdk.dir_version("openjdk-27")
    r = openjdk.fetch(pkg(vendor="openjdk", major=27), client=fake_client)
    fake_client.zip_roots[URL] = "jdk-27"
    assert sources.resolve_extras(pkg(vendor="openjdk", major=27), r, fake_client) == {"dir_version": "27"}
