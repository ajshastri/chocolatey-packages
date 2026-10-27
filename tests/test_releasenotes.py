import pytest

from chocotools import releasenotes
from conftest import pkg

# Real install-script URLs and the release-notes pages they map to (all answered HTTP 200).
CASES = [
    (pkg(vendor="temurin", major=25),
     "https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.4.1%2B1/"
     "OpenJDK25U-jdk_x64_windows_hotspot_25.0.4.1_1.msi",
     "https://adoptium.net/temurin/release-notes/?version=jdk-25.0.4.1%2B1"),
    (pkg(vendor="temurin", major=8),
     "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u504-b01/"
     "OpenJDK8U-jdk_x64_windows_hotspot_8u504b01.msi",
     "https://adoptium.net/temurin/release-notes/?version=jdk8u504-b01"),
    (pkg(vendor="liberica", major=21, variant="std"),
     "https://github.com/bell-sw/Liberica/releases/download/21.0.13.0.2+5/bellsoft-jdk21.0.13.0.2+5-windows-amd64.msi",
     "https://github.com/bell-sw/Liberica/releases/tag/21.0.13.0.2%2B5"),
    (pkg(vendor="liberica", major=8, variant="std"),
     "https://github.com/bell-sw/Liberica/releases/download/8u513+5/bellsoft-jdk8u513+5-windows-amd64.msi",
     "https://github.com/bell-sw/Liberica/releases/tag/8u513%2B5"),
    (pkg(vendor="sapmachine", major=21),
     "https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.13.0.3/"
     "sapmachine-jdk-21.0.13.0.3_windows-x64_bin.msi",
     "https://github.com/SAP/SapMachine/releases/tag/sapmachine-21.0.13.0.3"),
    (pkg(vendor="sapmachine", major=11),
     "https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.25/sapmachine-jdk-11.0.25_windows-x64_bin.msi",
     "https://github.com/SAP/SapMachine/releases/tag/sapmachine-11.0.25"),
    (pkg(vendor="corretto", major=8),
     "https://corretto.aws/downloads/resources/8.512.08.1/amazon-corretto-8.512.08.1-windows-x64-jdk.msi",
     "https://github.com/corretto/corretto-8/releases/tag/8.512.08.1"),
    (pkg(vendor="corretto", major=25),
     "https://corretto.aws/downloads/resources/25.0.5.0.9/amazon-corretto-25.0.5.0.9-windows-x64.msi",
     "https://github.com/corretto/corretto-25/releases/tag/25.0.5.0.9"),
    (pkg(vendor="zulu", major=8),
     "https://cdn.azul.com/zulu/bin/zulu8.96.0.205-ca-fx-jdk8.0.504-win_x64.msi",
     "https://docs.azul.com/core/release-notes"),
    (pkg(vendor="graalvm", major=25),
     "https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.4.4.1.1/"
     "graalvm-community-jdk-25i4-25.0.4.1.1_windows-x64_bin.zip",
     "https://github.com/graalvm/graalvm-ce-builds/releases/tag/graal-25.4.4.1.1"),
    (pkg(vendor="graalvm", major=17),
     "https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-17.0.9/graalvm-community-jdk-17.0.9_windows-x64_bin.zip",
     "https://github.com/graalvm/graalvm-ce-builds/releases/tag/jdk-17.0.9"),
    (pkg(vendor="openjdk", major=27),
     "https://download.java.net/java/GA/jdk27.0.1.0.3/b14170c9b2de463d9b89442c6db3e384/1/GPL/"
     "openjdk-27.0.1.0.3_windows-x64_bin.zip",
     "https://jdk.java.net/27/release-notes"),
    (pkg(vendor="wildfly", major=None, image=None, arch=("neutral",)),
     "https://github.com/wildfly/wildfly/releases/download/42.0.0.Final/wildfly-42.0.0.Final.zip",
     "https://github.com/wildfly/wildfly/releases/tag/42.0.0.Final"),
    (pkg(vendor="mvnd", major=None, image=None),
     "https://github.com/apache/maven-mvnd/releases/download/1.0.6/maven-mvnd-1.0.6-windows-amd64.zip",
     "https://github.com/apache/maven-mvnd/releases/tag/1.0.6"),
    (pkg(vendor="jmc", major=9, image=None),
     "https://download.java.net/java/GA/jmc9/05/binaries/jmc-9.1.2_windows-x64.zip",
     "https://github.com/openjdk/jmc/releases/tag/9.1.2-ga"),
    (pkg(vendor="lmc", major=None, image=None),
     "https://download.bell-sw.com/lmc/8.3.0/bellsoft-lmc8.3.0-windows-amd64.zip",
     "https://bell-sw.com/liberica-mission-control/"),
]


@pytest.mark.parametrize(("p", "download", "expected"), CASES, ids=[f"{c[0].vendor}{c[0].major or ''}" for c in CASES])
def test_url_for_real_urls(p, download, expected):
    assert releasenotes.url_for(p, download) == expected


@pytest.mark.parametrize(
    ("p", "download"),
    [
        (pkg(vendor="temurin"), "https://github.com/adoptium/temurin21-binaries/OpenJDK21U-jdk.msi"),
        (pkg(vendor="liberica", variant="std"), "https://github.com/bell-sw/Liberica/releases/download/"),
        (pkg(vendor="corretto"), "https://corretto.aws/downloads/latest/amazon-corretto-21-x64-windows-jdk.msi"),
        (pkg(vendor="jmc", major=9, image=None), "https://download.java.net/java/GA/jmc9/05/binaries/other.zip"),
        (pkg(vendor="openjdk", major=None), "https://download.java.net/java/GA/jdk27/openjdk-27_windows-x64_bin.zip"),
    ],
)
def test_missing_token_raises(p, download):
    with pytest.raises(releasenotes.ReleaseNotesError):
        releasenotes.url_for(p, download)


def test_error_is_a_value_error():
    assert issubclass(releasenotes.ReleaseNotesError, ValueError)
