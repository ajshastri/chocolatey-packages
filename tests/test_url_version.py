"""validate: the install-script URL must match the nuspec version."""

from __future__ import annotations

import re
import shutil

import pytest

from chocotools import checks, versioning
from chocotools.sources import corretto, graalvm, jmc, liberica, mvnd, openjdk, sapmachine, temurin, wildfly
from conftest import PKG_FIXTURES, pkg

# (vendor, URL as committed in the repo on 2026-10-04, package version it carries)
REAL = [
    ("corretto", "https://corretto.aws/downloads/resources/21.0.12.12.1/amazon-corretto-21.0.12.12.1-windows-x64.msi", "21.0.12.121"),
    ("corretto", "https://corretto.aws/downloads/resources/8.504.04.1/amazon-corretto-8.504.04.1-windows-x64-jdk.msi", "8.504.4.1"),
    ("corretto", "https://corretto.aws/downloads/resources/25.0.4.10.1/amazon-corretto-25.0.4.10.1-windows-x64.msi", "25.0.4.101"),
    ("zulu", "https://cdn.azul.com/zulu/bin/zulu21.52.203-ca-fx-jdk21.0.12.1-win_x64.msi", "21.52.203.0"),
    ("zulu", "https://cdn.azul.com/zulu/bin/zulu7.56.0.11-ca-jdk7.0.352-win_x64.msi", "7.56.0.11"),
    ("zulu", "https://cdn.azul.com/zulu/bin/zulu8.96.0.205-ca-fx-jdk8.0.504-win_x64.msi", "8.96.0.205"),
    ("temurin", "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u504-b01/OpenJDK8U-jdk_x64_windows_hotspot_8u504b01.msi", "8.504.1"),
    ("temurin", "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.msi", "21.0.12.1"),
    ("temurin", "https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.4.1%2B1/OpenJDK25U-jre_x64_windows_hotspot_25.0.4.1_1.msi", "25.0.4.1"),
    ("liberica", "https://github.com/bell-sw/Liberica/releases/download/8u504+1/bellsoft-jdk8u504+1-windows-amd64.msi", "8.0.504.1"),
    ("liberica", "https://github.com/bell-sw/Liberica/releases/download/21.0.12.1+1/bellsoft-jdk21.0.12.1+1-windows-amd64-lite.msi", "21.0.12.1"),
    ("sapmachine", "https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.25/sapmachine-jdk-11.0.25_windows-x64_bin.msi", "11.0.25"),
    ("sapmachine", "https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.12.1/sapmachine-jre-21.0.12.1_windows-x64_bin.msi", "21.0.12.1"),
    ("graalvm", "https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.3.4.1/graalvm-community-jdk-25i3-25.0.4.1_windows-x64_bin.zip", "25.3.4.1"),
    ("graalvm", "https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-21.0.2/graalvm-community-jdk-21.0.2_windows-x64_bin.zip", "21.0.2"),
    ("openjdk", "https://download.java.net/java/GA/jdk27/55ce5470a6294008af0057ff4626d0e5/35/GPL/openjdk-27_windows-x64_bin.zip", "27.0.0"),
    ("jmc", "https://download.java.net/java/GA/jmc9/05/binaries/jmc-9.1.2_windows-x64.zip", "9.1.2"),
    ("mvnd", "https://github.com/apache/maven-mvnd/releases/download/1.0.6/maven-mvnd-1.0.6-windows-amd64.zip", "1.0.6"),
    ("wildfly", "https://github.com/wildfly/wildfly/releases/download/41.0.1.Final/wildfly-41.0.1.Final.zip", "41.0.1"),
    ("lmc", "https://download.bell-sw.com/lmc/8.3.0/bellsoft-lmc8.3.0-windows-amd64.zip", "8.3.0"),
    # GraalVM 25i4: 5-part tag, package version = foojay java_version (first four parts)
    ("graalvm", "https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.4.4.1.1/graalvm-community-jdk-25i4-25.0.4.1.1_windows-x64_bin.zip", "25.4.4.1"),
    # corretto.aws latest on 2026-10-25: new-style Corretto tags (4th part 0) and Corretto 8
    ("corretto", "https://corretto.aws/downloads/resources/21.0.13.0.10/amazon-corretto-21.0.13.0.10-windows-x64.msi", "21.0.13.10"),
    ("corretto", "https://corretto.aws/downloads/resources/11.0.33.0.9/amazon-corretto-11.0.33.0.9-windows-x64.msi", "11.0.33.9"),
    ("corretto", "https://corretto.aws/downloads/resources/8.512.08.1/amazon-corretto-8.512.08.1-windows-x64-jdk.msi", "8.512.8.1"),
]


@pytest.mark.parametrize(("vendor", "url", "version"), REAL)
def test_url_version_real_urls(vendor, url, version):
    assert versioning.equal(versioning.url_version(vendor, url), version)


@pytest.mark.parametrize(
    ("vendor", "raw", "normalize", "url"),
    [
        ("temurin", "jdk8u504-b01", temurin.normalize, REAL[6][1]),
        ("temurin", "jdk-21.0.12.1+1", temurin.normalize, REAL[7][1]),
        ("corretto", "21.0.12.12.1", corretto.normalize, REAL[0][1]),
        ("corretto", "8.504.04.1", corretto.normalize, REAL[1][1]),
        ("liberica", "8u504+1", liberica.normalize, REAL[9][1]),
        ("liberica", "21.0.12.1+1", liberica.normalize, REAL[10][1]),
        ("sapmachine", "sapmachine-21.0.12.1", sapmachine.normalize, REAL[12][1]),
        ("graalvm", "25.3.4.1", graalvm.normalize, REAL[13][1]),
        ("graalvm", "25.4.4.1", graalvm.normalize, REAL[20][1]),
        ("openjdk", "27", openjdk.normalize, REAL[15][1]),
        ("jmc", "9.1.2-ga", jmc.normalize, REAL[16][1]),
        ("mvnd", "1.0.6", mvnd.normalize, REAL[17][1]),
        ("wildfly", "41.0.1.Final", wildfly.normalize, REAL[18][1]),
    ],
)
def test_url_version_agrees_with_vendor_normalize(vendor, raw, normalize, url):
    """The URL rule gives the same version sync derives from the upstream tag."""
    assert versioning.url_version(vendor, url) == normalize(raw)


def test_url_version_corretto_ambiguous_tag_fails():
    url = "https://corretto.aws/downloads/resources/21.0.13.1.10/amazon-corretto-21.0.13.1.10-windows-x64.msi"
    with pytest.raises(versioning.VersionError, match="ambiguous Corretto tag"):
        versioning.url_version("corretto", url)


def test_url_version_zulu_uses_distro_not_java_version():
    assert versioning.url_version("zulu", REAL[3][1]) == "21.52.203"


def test_url_version_without_token():
    with pytest.raises(versioning.VersionError, match="no temurin version token"):
        versioning.url_version("temurin", "https://github.com/adoptium/x/latest.msi")


# ----- validate_package -----------------------------------------------------------


def bump_nuspec(folder, old: bytes, new: bytes) -> None:
    (nuspec,) = folder.glob("*.nuspec")
    data = nuspec.read_bytes()
    assert old in data
    nuspec.write_bytes(data.replace(old, new))


def url_errors(errors: list[str]) -> list[str]:
    return [e for e in errors if "nuspec expects" in e or "package_fix" in e or "token" in e]


def test_hand_bumped_version_with_stale_url_fails(tmp_path):
    shutil.copytree(PKG_FIXTURES / "zulu-8", tmp_path / "zulu-8")
    p = pkg(id="zulu8", folder="zulu-8", vendor="zulu", major=8)
    assert checks.validate_package(tmp_path, p).errors == []
    bump_nuspec(tmp_path / "zulu-8", b"<version>8.96.0.205</version>", b"<version>8.98.0.1</version>")
    errors = checks.validate_package(tmp_path, p).errors
    assert errors == [
        "x64 URL is for version 8.96.0.205 but the nuspec expects 8.98.0.1: "
        "https://cdn.azul.com/zulu/bin/zulu8.96.0.205-ca-fx-jdk8.0.504-win_x64.msi"
    ]


def test_temurin_bump_with_stale_url_fails(tmp_path):
    shutil.copytree(PKG_FIXTURES / "temurin-21-jdk", tmp_path / "t")
    p = pkg(id="Temurin21", folder="t", major=21)
    assert checks.validate_package(tmp_path, p).errors == []
    bump_nuspec(tmp_path / "t", b"<version>21.0.12.1</version>", b"<version>21.0.13</version>")
    assert url_errors(checks.validate_package(tmp_path, p).errors) == [
        "x64 URL is for version 21.0.12.1 but the nuspec expects 21.0.13: "
        "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/"
        "OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.msi"
    ]


def test_neutral_url_is_checked(tmp_path):
    shutil.copytree(PKG_FIXTURES / "WildFly", tmp_path / "WildFly")
    p = pkg(id="wildfly", folder="WildFly", vendor="wildfly", major=None, image=None, arch=["neutral"])
    assert checks.validate_package(tmp_path, p).errors == []
    (nuspec,) = (tmp_path / "WildFly").glob("*.nuspec")
    data = nuspec.read_bytes()
    old = re.search(rb"<version>[^<]+</version>", data).group(0)
    nuspec.write_bytes(data.replace(old, b"<version>99.0.0</version>"))
    assert any("neutral URL is for version" in e for e in checks.validate_package(tmp_path, p).errors)


def test_package_fix_version_matches_upstream_url(tmp_path):
    shutil.copytree(PKG_FIXTURES / "temurin-21-jdk", tmp_path / "t")
    fixed = pkg(id="Temurin21", folder="t", major=21, package_fix=1, package_fix_line="21.0.12")
    # Fix declared but not applied yet: sync has to bump the nuspec first.
    assert url_errors(checks.validate_package(tmp_path, fixed).errors) == [
        "x64 URL matches nuspec 21.0.12.1 but package_fix 1 is not applied (run sync to apply package_fix): "
        "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/"
        "OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.msi"
    ]
    # A nuspec whose 4th segment does not end in the fix digits is reported as such.
    bump_nuspec(tmp_path / "t", b"<version>21.0.12.1</version>", b"<version>21.0.12.102</version>")
    assert any("does not carry package fix 1" in e for e in checks.validate_package(tmp_path, fixed).errors)
    bump_nuspec(tmp_path / "t", b"<version>21.0.12.102</version>", b"<version>21.0.12.1</version>")
    bump_nuspec(tmp_path / "t", b"<version>21.0.12.1</version>", b"<version>21.0.12.101</version>")
    assert checks.validate_package(tmp_path, fixed).errors == []
    # Without the manifest field, 21.0.12.101 does not match the 21.0.12.1 URL.
    assert url_errors(checks.validate_package(tmp_path, pkg(id="Temurin21", folder="t", major=21)).errors)
    # A hand bump of the fixed package to another line reports the fix as stale
    # (not "run sync", which would carry the fix over to the new line).
    bump_nuspec(tmp_path / "t", b"<version>21.0.12.101</version>", b"<version>21.0.13.1</version>")
    errors = url_errors(checks.validate_package(tmp_path, fixed).errors)
    assert errors == [
        "x64 URL: package_fix 1 is stale: it was declared for 21.0.12 but the nuspec version 21.0.13.1 is on "
        "another A.B.C line; remove package_fix and package_fix_line from packages.toml"
    ]
    # Once the fix is removed, the stale URL is still caught.
    assert any("is for version 21.0.12.1 but the nuspec expects 21.0.13.1" in e
               for e in checks.validate_package(tmp_path, pkg(id="Temurin21", folder="t", major=21)).errors)


def test_graalvm_java17_exception_is_pinned_to_its_version(tmp_path):
    shutil.copytree(PKG_FIXTURES / "GraalVM-17", tmp_path / "GraalVM-17")
    p = pkg(id="graalvm-java17", folder="GraalVM-17", vendor="graalvm", major=17, frozen=True)
    assert checks.validate_package(tmp_path, p).errors == []  # 22.3.3 installs jdk-17.0.9 (documented)
    bump_nuspec(tmp_path / "GraalVM-17", b"<version>22.3.3</version>", b"<version>22.3.4</version>")
    assert any("is for version 17.0.9 but the nuspec expects 22.3.4" in e
               for e in checks.validate_package(tmp_path, p).errors)


# ----- GraalVM 25 tags: graal-25.3.4.1 (4 parts) and graal-25.4.4.1.1 (5 parts) ------------

GRAAL = "https://github.com/graalvm/graalvm-ce-builds/releases/download/"
GRAAL_25_0_2 = GRAAL + "jdk-25.0.2/graalvm-community-jdk-25.0.2_windows-x64_bin.zip"  # in the fixture
GRAAL_25I3 = GRAAL + "graal-25.3.4.1/graalvm-community-jdk-25i3-25.0.4.1_windows-x64_bin.zip"
GRAAL_25I4 = GRAAL + "graal-25.4.4.1.1/graalvm-community-jdk-25i4-25.0.4.1.1_windows-x64_bin.zip"


def graalvm_folder(tmp_path, version: str, url: str):
    shutil.copytree(PKG_FIXTURES / "GraalVM", tmp_path / "GraalVM")
    script = tmp_path / "GraalVM/tools/chocolateyinstall.ps1"
    data = script.read_bytes()
    assert GRAAL_25_0_2.encode() in data
    script.write_bytes(data.replace(GRAAL_25_0_2.encode(), url.encode()))
    bump_nuspec(tmp_path / "GraalVM", b"<version>25.0.2</version>", f"<version>{version}</version>".encode())
    return pkg(id="graalvm", folder="GraalVM", vendor="graalvm", major=25)


@pytest.mark.parametrize(("version", "url"), [("25.3.4.1", GRAAL_25I3), ("25.4.4.1", GRAAL_25I4)])
def test_graalvm25_tag_layouts_validate(tmp_path, version, url):
    assert checks.validate_package(tmp_path, graalvm_folder(tmp_path, version, url)).errors == []


@pytest.mark.parametrize(
    ("version", "url", "found"),
    [
        ("25.4.4.1", GRAAL_25I3, "25.3.4.1"),  # nuspec bumped by hand, URL left on 25i3
        ("25.3.4.1", GRAAL_25I4, "25.4.4.1"),  # URL bumped, nuspec left behind
        ("25.4.4.2", GRAAL_25I4, "25.4.4.1"),  # nuspec ahead of the 5-part tag's version
        ("25.4.4.1", GRAAL_25_0_2, "25.0.2"),  # the pre-25i jdk- layout
    ],
)
def test_graalvm25_stale_url_fails(tmp_path, version, url, found):
    errors = checks.validate_package(tmp_path, graalvm_folder(tmp_path, version, url)).errors
    assert url_errors(errors) == [f"x64 URL is for version {found} but the nuspec expects {version}: {url}"]


@pytest.mark.parametrize(
    ("path", "message"),
    [
        ("graal-25.4.4.1.1/graalvm-community-jdk-25i3-25.0.4.1.1_windows-x64_bin.zip", "does not match asset"),
        ("graal-25.4.4.1.2/graalvm-community-jdk-25i4-25.0.4.1.1_windows-x64_bin.zip", "does not match asset"),
        ("graal-25.4.4.1.1/graalvm-community-jdk-25i4-25.1.4.1.1_windows-x64_bin.zip", "is not 25i4-25.0.<update>"),
        ("graal-25.4.4.1.1.1/graalvm-community-jdk-25i4-25.0.4.1.1.1_windows-x64_bin.zip", "more than 5 parts"),
        ("graal-25.4.4.1.1/graalvm-community-jdk-25.0.4.1.1_windows-x64_bin.zip", "more than 4 parts"),
    ],
)
def test_graalvm_tag_and_asset_must_agree(path, message):
    with pytest.raises(versioning.VersionError, match=re.escape(message)):
        versioning.url_version("graalvm", GRAAL + path)
