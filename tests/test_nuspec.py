import re

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


NOTES = "https://github.com/graalvm/graalvm-ce-builds/releases/tag/jdk-17.0.9"
_NOTES_LINE = re.compile(rb"[ \t]*<releaseNotes>[^<]*</releaseNotes>\r?\n")


def graalvm17_without_notes() -> bytes:
    """The GraalVM-17 fixture (UTF-8 BOM, CRLF) with its <releaseNotes> line removed."""
    data, count = _NOTES_LINE.subn(b"", pkg_bytes("GraalVM-17", "graalvm-java17.nuspec"))
    assert count == 1
    return data


def test_metadata_first_occurrence_namespace_agnostic():
    meta = nuspec.metadata(pkg_bytes("GraalVM-17", "graalvm-java17.nuspec"))
    assert meta["id"] == "graalvm-java17"
    assert meta["projectUrl"] == "https://www.graalvm.org/"
    assert meta["releaseNotes"] == NOTES
    assert "releaseNotes" not in nuspec.metadata(graalvm17_without_notes())
    assert nuspec.metadata(pkg_bytes("zulu-8", "zulu-8.nuspec"))["releaseNotes"] == "https://docs.azul.com/core/release-notes"


def test_set_element_replaces_existing_text():
    old = pkg_bytes("zulu-8", "zulu-8.nuspec")
    new = nuspec.set_element(old, "releaseNotes", "https://example.org/notes")
    assert new == old.replace(b"<releaseNotes>https://docs.azul.com/core/release-notes</releaseNotes>",
                              b"<releaseNotes>https://example.org/notes</releaseNotes>")
    assert nuspec.set_element(old, "releaseNotes", "https://docs.azul.com/core/release-notes") == old


def test_set_element_fills_self_closing_element():
    old = b"<package><metadata><id>a</id><version>1</version><docsUrl /></metadata></package>"
    assert nuspec.set_element(old, "docsUrl", "https://a.example/") == old.replace(
        b"<docsUrl />", b"<docsUrl>https://a.example/</docsUrl>")


def test_set_element_inserts_into_crlf_bom_file():
    old = graalvm17_without_notes()
    new = nuspec.set_release_notes(old, NOTES)
    assert new == pkg_bytes("GraalVM-17", "graalvm-java17.nuspec")  # the fixture line was written this way
    assert new.startswith(nuspec.BOM)
    line = f"    <releaseNotes>{NOTES}</releaseNotes>\r\n".encode()
    assert new == old.replace(b"  </metadata>", line + b"  </metadata>")
    assert new.count(b"\r\n") == old.count(b"\r\n") + 1 and new.count(b"\n") == new.count(b"\r\n")
    assert nuspec.metadata(new)["releaseNotes"] == NOTES
    assert nuspec.read(new) == nuspec.read(old)


def test_set_element_inserts_into_lf_file():
    old = graalvm17_without_notes().replace(b"\r\n", b"\n")
    new = nuspec.set_release_notes(old, NOTES)
    assert new == old.replace(b"  </metadata>", f"    <releaseNotes>{NOTES}</releaseNotes>\n  </metadata>".encode())
    assert b"\r" not in new


def test_set_element_changes_only_metadata_bytes():
    old = pkg_bytes("temurin-8-jdk", "temurin8.nuspec")
    new = nuspec.set_element(nuspec.set_release_notes(old, NOTES), "docsUrl", "https://adoptium.net/docs/")
    head, tail = old.index(b"<metadata>"), old.index(b"</metadata>")
    assert new[:head] == old[:head]
    assert new.endswith(old[tail:])
    meta_old, meta_new = nuspec.metadata(old), nuspec.metadata(new)
    assert (meta_new["releaseNotes"], meta_new["docsUrl"]) == (NOTES, "https://adoptium.net/docs/")
    skip = ("releaseNotes", "docsUrl")
    assert {k: v for k, v in meta_new.items() if k not in skip} == {k: v for k, v in meta_old.items() if k not in skip}


def test_set_element_escapes_and_round_trips():
    value = "https://a.example/?a=1&b=<2>"
    new = nuspec.set_release_notes(pkg_bytes("GraalVM-17", "graalvm-java17.nuspec"), value)
    assert b"<releaseNotes>https://a.example/?a=1&amp;b=&lt;2&gt;</releaseNotes>" in new
    assert nuspec.metadata(new)["releaseNotes"] == value


@pytest.mark.parametrize("bad", ["", "   ", "a\nb", "a\r\nb"])
def test_set_element_refuses_bad_values(bad):
    with pytest.raises(nuspec.NuspecError):
        nuspec.set_release_notes(pkg_bytes("GraalVM-17", "graalvm-java17.nuspec"), bad)


@pytest.mark.parametrize("name", ["", "a b", "x>", "1abc"])
def test_set_element_refuses_bad_names(name):
    with pytest.raises(nuspec.NuspecError):
        nuspec.set_element(pkg_bytes("GraalVM-17", "graalvm-java17.nuspec"), name, "v")


def test_set_element_refuses_complex_elements():
    old = b"<package><metadata><id>a</id><version>1</version><license type='expression'>MIT</license></metadata></package>"
    with pytest.raises(nuspec.NuspecError, match="not a simple text element"):
        nuspec.set_element(old, "license", "Apache-2.0")


def test_set_element_inserts_inline_when_metadata_is_one_line():
    old = b"<package><metadata><id>a</id><version>1</version></metadata></package>"
    new = nuspec.set_release_notes(old, "https://a.example/")
    assert new == b"<package><metadata><id>a</id><version>1</version><releaseNotes>https://a.example/</releaseNotes></metadata></package>"


def test_read_errors():
    with pytest.raises(nuspec.NuspecError):
        nuspec.read(b"<package><metadata><id>a</id>")
    with pytest.raises(nuspec.NuspecError):
        nuspec.read(b"<package><metadata><version>1</version></metadata></package>")
