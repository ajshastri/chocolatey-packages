import shutil

import pytest

from chocotools import checks
from chocotools.sources import Release
from conftest import PKG_FIXTURES, pkg

SHA = "b" * 64


def release(**kw):
    base = dict(version="21.0.13", version_raw="jdk-21.0.13+8", urls={"x64": "https://github.com/a/b.msi"},
                sha256={"x64": SHA}, checksum_source="test")
    base.update(kw)
    return Release(**base)


@pytest.mark.parametrize(
    "url, fragment",
    [
        ("", "empty"),
        ("https://api.foojay.io/disco/v3.0/ids/abc/redirect", "denied host"),
        ("https://aka.ms/download-jdk/microsoft-jdk-21-windows-x64.msi", "denied host"),
        ("https://example.com/jdk.msi", "not on the allowlist"),
        ("http://github.com/a.msi", "not https"),
    ],
)
def test_check_url_rejects(url, fragment):
    errors = checks.check_url(url)
    assert errors and fragment in errors[0]


@pytest.mark.parametrize("host", sorted(checks.ALLOWED_HOSTS))
def test_check_url_allows(host):
    assert checks.check_url(f"https://{host}/x") == []


def test_find_denied():
    assert checks.find_denied("see https://api.foojay.io/x and aka.ms/y") == ["aka.ms", "api.foojay.io"]
    assert checks.find_denied("foojay badge text, kaka.mss") == []


def test_checksums():
    assert checks.check_checksum(SHA, "sha256", "c").ok
    weak = checks.check_checksum("a" * 40, "sha1", "c")
    assert weak.ok and weak.warnings
    assert not checks.check_checksum("", "sha256", "c").ok
    assert not checks.check_checksum("a" * 40, "sha256", "c").ok
    assert not checks.check_checksum(SHA, "crc32", "c").ok


def test_versions():
    assert checks.check_version("") == ["version is empty"]
    assert checks.check_version("21.0.12.1.1")
    assert checks.check_increase("21.0.13", "21.0.12.1", "21.0.9.10") == []
    lower = checks.check_increase("21.0.12", "21.0.12.1", None)
    assert lower and "not greater than repo" in lower[0]
    approved = checks.check_increase("11.0.32.101", "11.0.32.91", "11.0.32.102")
    assert approved and "Chocolatey approved" in approved[0]
    assert checks.check_increase("17.0.20.1", "", "17.0.13.12") == []  # empty repo version


def test_check_release():
    assert checks.check_release(pkg(), release()) == []
    assert checks.check_release(pkg(), release(sha256={"x64": ""}))
    assert checks.check_release(pkg(), release(urls={"x64": "https://api.foojay.io/x"}))
    assert checks.check_release(pkg(), release(version="21.52.203.0"))  # not normalized
    two = pkg(arch=("x64", "x86"))
    same = release(urls={"x64": "https://github.com/a.msi", "x86": "https://github.com/a.msi"},
                   sha256={"x64": SHA, "x86": SHA})
    assert "x86 URL equals the x64 URL" in checks.check_release(two, same)
    assert checks.check_release(two, release())  # x86 missing


def test_validate_package_real_files(tmp_path):
    shutil.copytree(PKG_FIXTURES / "zulu-8", tmp_path / "zulu-8")
    p = pkg(id="zulu8", folder="zulu-8", vendor="zulu", major=8)
    assert checks.validate_package(tmp_path, p).errors == []
    # Temurin 8: x86 Url equal to x64 and not in the manifest arch
    shutil.copytree(PKG_FIXTURES / "temurin-8-jdk", tmp_path / "temurin-8-jdk")
    t = pkg(id="Temurin8", folder="temurin-8-jdk", major=8)
    errors = checks.validate_package(tmp_path, t).errors
    assert any("present but manifest arch" in e for e in errors)
    assert "x86 URL equals the x64 URL" in errors


def test_validate_package_denylist_and_overrides(tmp_path):
    shutil.copytree(PKG_FIXTURES / "zulu-8", tmp_path / "zulu-8")
    p = pkg(id="zulu8", folder="zulu-8", vendor="zulu", major=8)
    bad_script = (tmp_path / "zulu-8/tools/chocolateyinstall.ps1").read_bytes().replace(
        b"https://cdn.azul.com/zulu/bin/", b"https://api.foojay.io/disco/v3.0/ids/"
    )
    errors = checks.validate_package(tmp_path, p, {"tools/chocolateyinstall.ps1": bad_script}).errors
    assert any("denied host" in e for e in errors)
    errors = checks.validate_package(tmp_path, p, {"legal/VERIFICATION.txt": b"get it from aka.ms/jdk"}).errors
    assert any("legal/VERIFICATION.txt mentions denied host" in e for e in errors)
    wrong_id = checks.validate_package(tmp_path, pkg(id="zulu", folder="zulu-8", vendor="zulu", major=8))
    assert any("nuspec <id>" in e for e in wrong_id.errors)
