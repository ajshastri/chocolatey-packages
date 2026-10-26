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


# jdk.java.net/27 on 2026-10-25 (h1 and the Windows zip href)
URL_27_0_1_0_3 = ("https://download.java.net/java/GA/jdk27.0.1.0.3/b14170c9b2de463d9b89442c6db3e384/1/GPL/"
                  "openjdk-27.0.1.0.3_windows-x64_bin.zip")


def test_openjdk_five_part_ga_maps_to_four_parts():
    page = f'<h1>OpenJDK JDK 27.0.1.0.3 GA Release Builds</h1>\n<a href="{URL_27_0_1_0_3}">zip</a>'
    client = FakeClient(get={"https://jdk.java.net/27/": page, URL_27_0_1_0_3 + ".sha256": "a" * 64}, use_index=False)
    r = openjdk.fetch(pkg(vendor="openjdk", major=27), client=client)
    assert r.version == "27.0.1.3"
    assert r.version_raw == "27.0.1.0.3"
    assert r.urls == {"x64": URL_27_0_1_0_3}


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
