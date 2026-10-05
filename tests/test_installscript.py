import pytest

from chocotools import installscript as isc
from conftest import pkg_bytes

SHA = "a" * 64


def only_spans_changed(old: bytes, new: bytes, replacements: list[tuple[bytes, bytes]]) -> bool:
    expected = old
    for before, after in replacements:
        assert expected.count(before) == 1, before
        expected = expected.replace(before, after)
    return expected == new


def test_style_a_plus_x86_fields():
    f = isc.read(pkg_bytes("temurin-8-jdk", "tools/chocolateyinstall.ps1"))
    assert f.get("url64").endswith("OpenJDK8U-jdk_x64_windows_hotspot_8u504b01.msi")
    assert f.get("url") == f.get("url64")
    assert f.get("checksum") == f.get("checksum64")
    assert f.get("checksumtype64") == "sha256"
    assert f.duplicates == ()


def test_style_a_plus_x86_update_x64_only_changes_x64_lines():
    old = pkg_bytes("temurin-8-jdk", "tools/chocolateyinstall.ps1")
    new = isc.update(old, isc.arch_changes("x64", "https://github.com/x/y.msi", SHA))
    text_old, text_new = old.decode(), new.decode()
    assert "  Url64bit        = 'https://github.com/x/y.msi'\r\n" in text_new
    assert f"  Checksum64      = '{SHA}'\r\n" in text_new
    # x86 lines untouched
    url_line = next(l for l in text_old.split("\r\n") if l.strip().startswith("Url  "))
    assert url_line in text_new
    assert old.count(b"\r\n") == new.count(b"\r\n")


def test_style_d_zulu_top_level_url64_and_unquoted_refs():
    old = pkg_bytes("zulu-8", "tools/chocolateyinstall.ps1")
    f = isc.read(old)
    assert f.get("url64").startswith("https://cdn.azul.com/")
    assert f.get("url") is None  # `url = $url` is an unquoted reference
    assert f.get("checksumtype64") == "sha256"
    url = "https://cdn.azul.com/zulu/bin/zulu8.98.0.1-ca-fx-jdk8.0.512-win_x64.msi"
    new = isc.update(old, isc.arch_changes("x64", url, SHA))
    assert only_spans_changed(
        old,
        new,
        [
            (f.get("url64").encode(), url.encode()),
            (f.get("checksum64").encode(), SHA.encode()),
        ],
    )
    assert b"checksumType64= 'sha256'" in new


def test_style_c_wildfly_neutral():
    old = pkg_bytes("WildFly", "tools/chocolateyinstall.ps1")
    f = isc.read(old)
    assert f.get("url64") is None
    assert f.get("url").endswith("wildfly-41.0.0.Final.zip")
    new = isc.update(old, isc.arch_changes("neutral", "https://github.com/w/wildfly-41.0.1.Final.zip", SHA))
    assert b"    Url = 'https://github.com/w/wildfly-41.0.1.Final.zip'\r\n" in new
    assert f"    Checksum = '{SHA}'\r\n".encode() in new


def test_style_b_openjdk_and_dir_variable():
    old = pkg_bytes("OpenJDK", "tools/chocolateyinstall.ps1")
    assert isc.read(old).get("url64").startswith("https://download.java.net/")
    new, count = isc.set_variable(old, "version", "27")
    assert count == 1
    assert only_spans_changed(old, new, [(b'$version = "26.0.2.1"', b'$version = "27"')])
    un = pkg_bytes("OpenJDK", "tools/chocolateyuninstall.ps1")
    new_un, count = isc.set_variable(un, "version", "27")
    assert count == 1 and b"$version = '27'" in new_un  # single quotes preserved


def test_bom_preserved_graalvm17():
    old = pkg_bytes("GraalVM-17", "tools/chocolateyinstall.ps1")
    assert old.startswith(isc.BOM)
    new = isc.update(old, isc.arch_changes("x64", "https://github.com/g/a.zip", SHA))
    assert new.startswith(isc.BOM)
    new2, count = isc.set_variable(new, "version", "17.0.10+1.1")
    assert count == 1 and new2.startswith(isc.BOM)
    assert b'$version = "17.0.10+1.1"\r\n' in new2


def test_mvnd_literal_dir_skips_urls():
    old = pkg_bytes("mvndaemon", "tools/chocolateyinstall.ps1")
    new, count = isc.set_mvnd_dir(old, "maven-mvnd-1.0.7-windows-amd64")
    assert count == 1  # the install path, not the URL
    assert b"/download/1.0.6/maven-mvnd-1.0.6-windows-amd64.zip" in new
    assert b"$targetDir\\maven-mvnd-1.0.7-windows-amd64\\bin" in new
    un = pkg_bytes("mvndaemon", "tools/chocolateyuninstall.ps1")
    assert isc.get_mvnd_dirs(un) == ["maven-mvnd-1.0.5-windows-amd64"]
    with pytest.raises(isc.ScriptError):
        isc.set_mvnd_dir(old, "not-a-dir")


def test_missing_and_duplicate_fields_are_errors():
    with pytest.raises(isc.ScriptError, match="not found"):
        isc.update(pkg_bytes("zulu-8", "tools/chocolateyinstall.ps1"), {"url": "https://x"})
    dup = b"$url64 = 'https://a'\r\n@{\r\n  Url64bit = 'https://b'\r\n}\r\n"
    assert isc.read(dup).duplicates == ("url64",)
    with pytest.raises(isc.ScriptError, match="appears 2 times"):
        isc.update(dup, {"url64": "https://c"})


def test_refuses_values_with_quotes():
    with pytest.raises(isc.ScriptError):
        isc.update(pkg_bytes("zulu-8", "tools/chocolateyinstall.ps1"), {"url64": "https://x/'; evil"})
