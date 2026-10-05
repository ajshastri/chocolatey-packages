import pytest

from chocotools import nuspec
from conftest import pkg_bytes


def test_read_real_nuspecs():
    assert nuspec.read(pkg_bytes("temurin-8-jdk", "temurin8.nuspec")) == nuspec.NuspecInfo("Temurin8", "8.0.504")
    assert nuspec.read(pkg_bytes("GraalVM-17", "graalvm-java17.nuspec")) == nuspec.NuspecInfo("graalvm-java17", "22.3.3")
    assert nuspec.read(pkg_bytes("zulu-8", "zulu-8.nuspec")).version == "8.96.0.205"


def test_set_version_changes_only_the_version_span():
    old = pkg_bytes("temurin-8-jdk", "temurin8.nuspec")
    new = nuspec.set_version(old, "8.504.1")
    assert old.count(b"<version>8.0.504</version>") == 1
    assert new == old.replace(b"<version>8.0.504</version>", b"<version>8.504.1</version>")
    assert old.count(b"\r\n") == new.count(b"\r\n")
    assert nuspec.read(new).version == "8.504.1"


def test_set_version_keeps_bom_and_crlf():
    old = pkg_bytes("GraalVM-17", "graalvm-java17.nuspec")
    assert old.startswith(nuspec.BOM)
    new = nuspec.set_version(old, "22.3.4")
    assert new.startswith(nuspec.BOM)
    assert new.replace(b"22.3.4", b"22.3.3") == old
    assert b"\r\n" in new and new.count(b"\r\n") == old.count(b"\r\n")


def test_set_version_fills_empty_version():
    old = (
        b'<?xml version="1.0" encoding="utf-8"?>\r\n<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">\r\n'
        b"  <metadata>\r\n    <id>liberica17jdklite</id>\r\n    <version></version>\r\n  </metadata>\r\n</package>\r\n"
    )
    assert nuspec.read(old).version == ""
    new = nuspec.set_version(old, "17.0.20.1")
    assert new == old.replace(b"<version></version>", b"<version>17.0.20.1</version>")


def test_set_version_ignores_dependency_versions_before_metadata():
    old = b"<package><metadata><id>a</id><version>1.0.0</version><dependencies><dependency id='b' version='2' /></dependencies></metadata></package>"
    assert nuspec.set_version(old, "1.0.1").count(b"1.0.1") == 1


@pytest.mark.parametrize("bad", ["", "1<2", "a&b"])
def test_set_version_refuses_bad_values(bad):
    with pytest.raises(nuspec.NuspecError):
        nuspec.set_version(pkg_bytes("zulu-8", "zulu-8.nuspec"), bad)


def test_read_errors():
    with pytest.raises(nuspec.NuspecError):
        nuspec.read(b"<package><metadata><id>a</id>")
    with pytest.raises(nuspec.NuspecError):
        nuspec.read(b"<package><metadata><version>1</version></metadata></package>")
