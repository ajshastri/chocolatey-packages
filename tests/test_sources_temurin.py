import json

import pytest

from chocotools import sources
from chocotools.sources import temurin
from conftest import FIXTURES, FakeClient, pkg

URL8 = "https://api.adoptium.net/v3/assets/latest/8/hotspot?architecture={a}&image_type=jdk&os=windows&vendor=eclipse"


def test_temurin8_jdk(fake_client):
    r = sources.fetch(pkg(id="Temurin8", vendor="temurin", major=8, image="jdk"), client=fake_client)
    assert r.version == "8.504.1"
    assert r.version_raw == "jdk8u504-b01"
    assert r.urls == {"x64": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u504-b01/OpenJDK8U-jdk_x64_windows_hotspot_8u504b01.msi"}
    assert r.sha256 == {"x64": "5115720df210f3c98b592ea2cb9981f48ba6b6942a7c40ba7fe4a59c37d5b815"}
    assert r.checksum_source == "adoptium installer.checksum"


@pytest.mark.parametrize("major, image, expected", [(21, "jre", "21.0.12.1"), (25, "jdk", "25.0.4.1"), (11, "jdk", "11.0.32.1")])
def test_temurin_majors(fake_client, major, image, expected):
    r = temurin.fetch(pkg(vendor="temurin", major=major, image=image), client=fake_client)
    assert r.version == expected
    assert r.urls["x64"].startswith("https://github.com/adoptium/")


def test_x86_must_match_x64_release():
    x64 = (FIXTURES / "temurin" / "adoptium-8-jdk-x64.json").read_text(encoding="utf-8")
    data = json.loads(x64)
    data[0]["release_name"] = "jdk8u472-b08"
    data[0]["binary"]["architecture"] = "x86"
    client = FakeClient(get={URL8.format(a="x86"): json.dumps(data)})
    with pytest.raises(sources.SourceError, match="x86 and x64 builds differ"):
        temurin.fetch(pkg(vendor="temurin", major=8, arch=("x64", "x86")), client=client)


def test_no_installer_fails_closed():
    client = FakeClient(get={URL8.format(a="x86"): "[]"})
    with pytest.raises(sources.SourceError, match="no x86 jdk MSI"):
        temurin.fetch(pkg(vendor="temurin", major=8, arch=("x64", "x86")), client=client)


def test_empty_checksum_fails_closed():
    data = json.loads((FIXTURES / "temurin" / "adoptium-8-jdk-x64.json").read_text(encoding="utf-8"))
    data[0]["binary"]["installer"]["checksum"] = ""
    client = FakeClient(get={URL8.format(a="x64"): json.dumps(data)})
    with pytest.raises(sources.SourceError, match="checksum"):
        temurin.fetch(pkg(vendor="temurin", major=8), client=client)
