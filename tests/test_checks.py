import shutil

import pytest

from chocotools import checks, cli
from chocotools.sources import Release
from conftest import PKG_FIXTURES, FakeClient, pkg

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


GOOD_META = {
    "id": "x",
    "version": "1.0.0",
    "authors": "Vendor",
    "packageSourceUrl": checks.REPO_TREE + "x",
    "projectUrl": "https://vendor.example/",
    "projectSourceUrl": "https://github.com/vendor/x",
    "docsUrl": "https://vendor.example/docs/",
    "bugTrackerUrl": "https://github.com/vendor/x/issues",
    "iconUrl": "https://cdn.jsdelivr.net/gh/ajshastri/chocolatey-packages@0123456/icons/x.png",
    "licenseUrl": "https://vendor.example/license",
    "mailingListUrl": "https://vendor.example/lists",
    "summary": "A short summary",
    "description": "A description that is long enough for Chocolatey.",
    "tags": "x java jvm",
    "releaseNotes": "https://github.com/vendor/x/releases/tag/1.0.0",
}


def metadata_result(**changes):
    meta = {k: v for k, v in {**GOOD_META, **changes}.items() if v is not None}
    return checks.check_metadata(pkg(id="x", folder="x"), meta)


def test_metadata_complete_is_clean():
    res = metadata_result()
    assert (res.errors, res.warnings) == ([], [])


@pytest.mark.parametrize("value", [None, ""])
def test_release_notes_missing_is_an_error(value):
    res = metadata_result(releaseNotes=value)
    assert res.errors == ["<releaseNotes> is missing or empty (run sync, or add the release-notes URL)"]


def test_release_notes_text_is_accepted_and_http_warns():
    assert metadata_result(releaseNotes="Bug fixes, see the vendor site.").warnings == []
    assert metadata_result(releaseNotes="http://vendor.example/notes").warnings == [
        "<releaseNotes> URL is not https: http://vendor.example/notes"]


@pytest.mark.parametrize("name", checks.RECOMMENDED_FIELDS)
@pytest.mark.parametrize("value", [None, ""])
def test_missing_recommended_field_warns(name, value):
    res = metadata_result(**{name: value})
    assert res.errors == []
    assert f"<{name}> is missing or empty" in res.warnings


@pytest.mark.parametrize("value", [None, "https://github.com/ajshastri/chocolatey-packages",
                                   "https://github.com/johanjanssen/ChocolateyPackages/tree/master/x"])
def test_package_source_url_must_be_the_repo_folder(value):
    res = metadata_result(packageSourceUrl=value)
    assert res.errors == []
    assert res.warnings == [f"<packageSourceUrl> is {value!r}, expected {checks.REPO_TREE}x"]


def test_http_url_warns():
    res = metadata_result(mailingListUrl="http://mail.openjdk.java.net/mailman/listinfo", docsUrl="HTTP://a.example/")
    assert res.warnings == ["<docsUrl> is not https: HTTP://a.example/",
                            "<mailingListUrl> is not https: http://mail.openjdk.java.net/mailman/listinfo"]


@pytest.mark.parametrize(
    "tags, fragment",
    [("x,java", "space separated"), ("x Java", "lowercase"), ("x chocolatey java", "'chocolatey'")],
)
def test_bad_tags_warn(tags, fragment):
    res = metadata_result(tags=tags)
    assert res.errors == [] and len(res.warnings) == 1 and fragment in res.warnings[0]


def test_short_description_warns():
    assert metadata_result(description="Too short").warnings == ["<description> is shorter than 30 characters"]


def test_validate_package_requires_release_notes(tmp_path):
    shutil.copytree(PKG_FIXTURES / "zulu-8", tmp_path / "zulu-8")
    p = pkg(id="zulu8", folder="zulu-8", vendor="zulu", major=8)
    res = checks.validate_package(tmp_path, p)
    assert res.errors == []
    # zulu has no public source repository or bug tracker
    assert set(res.warnings) == {"<projectSourceUrl> is missing or empty", "<bugTrackerUrl> is missing or empty"}
    nuspec_file = tmp_path / "zulu-8/zulu-8.nuspec"
    data = nuspec_file.read_bytes()
    line = b"    <releaseNotes>https://docs.azul.com/core/release-notes</releaseNotes>\r\n"
    assert data.count(line) == 1
    nuspec_file.write_bytes(data.replace(line, b""))
    assert checks.validate_package(tmp_path, p).errors == [
        "<releaseNotes> is missing or empty (run sync, or add the release-notes URL)"]


def test_online_check_warns_on_unreachable_release_notes(tmp_path, capsys):
    shutil.copytree(PKG_FIXTURES / "zulu-8", tmp_path / "zulu-8")
    p = pkg(id="zulu8", folder="zulu-8", vendor="zulu", major=8)
    msi = "https://cdn.azul.com/zulu/bin/zulu8.96.0.205-ca-fx-jdk8.0.504-win_x64.msi"
    notes = "https://docs.azul.com/core/release-notes"
    ok = FakeClient(use_index=False, head={msi: {"status": 200}, notes: {"status": 200}})
    res = cli.online_check(tmp_path, p, ok)
    assert (res.errors, res.warnings) == ([], [])
    assert "HEAD " + notes in ok.calls
    gone = FakeClient(use_index=False, head={msi: {"status": 200}})  # release notes: HttpError 404
    res = cli.online_check(tmp_path, p, gone)
    assert res.errors == []
    assert res.warnings == [f"releaseNotes URL unreachable: HTTP 404 for {notes}"]
    moved = FakeClient(use_index=False, head={msi: {"status": 200}, notes: {"status": 410}})
    assert cli.online_check(tmp_path, p, moved).warnings == [f"releaseNotes URL answered HTTP 410: {notes}"]


def uninstall_script(name: str, major: str) -> bytes:
    return (
        "$ErrorActionPreference = 'Stop'\r\n"
        f"$softwareName = '{name}'\r\n"
        f"$major        = '{major}'\r\n"
        "[array]$keys = Get-UninstallRegistryKey -SoftwareName $softwareName |\r\n"
        "  Where-Object { $_.DisplayVersion -like \"$major.*\" }\r\n"
    ).encode()


@pytest.mark.parametrize(
    "kw, name",
    [
        (dict(vendor="sapmachine", major=25, image="jdk"), "SapMachine 25 JDK"),
        (dict(vendor="sapmachine", major=25, image="jre"), "SapMachine 25 JRE"),
        (dict(vendor="liberica", major=25, image="jdk", variant="std"), "Liberica JDK 25 (64-bit)"),
        (dict(vendor="liberica", major=25, image="jdk", variant="full"), "Liberica JDK 25 Full (64-bit)"),
        (dict(vendor="liberica", major=25, image="jdk", variant="lite"), "Liberica JDK 25 Lite (64-bit)"),
        (dict(vendor="liberica", major=25, image="jre", variant="std"), "Liberica JRE 25 (64-bit)"),
        (dict(vendor="liberica", major=25, image="jre", variant="full"), "Liberica JRE 25 Full (64-bit)"),
        (dict(vendor="corretto", major=25, image="jdk"), "Amazon Corretto (x64)"),
        (dict(vendor="temurin", major=25, image="jdk"), None),
    ],
)
def test_uninstall_display_name(kw, name):
    assert checks.uninstall_display_name(pkg(**kw)) == name


SAP25 = pkg(id="sapmachine", folder="sapmachine-jdk", vendor="sapmachine", major=25, image="jdk")
SKIP = {checks.SKIP_AUTO_UNINSTALL: b""}


def test_uninstall_rule_matching_script_passes():
    files = {checks.UNINSTALL_SCRIPT: uninstall_script("SapMachine 25 JDK", "25"), **SKIP}
    assert checks.check_uninstall(SAP25, files) == []


def test_uninstall_rule_ignores_scripts_without_major():
    assert checks.check_uninstall(SAP25, {}) == []
    assert checks.check_uninstall(SAP25, {checks.UNINSTALL_SCRIPT: b"Uninstall-ChocolateyPackage @args\r\n"}) == []


def test_uninstall_rule_wrong_major_fails():
    files = {checks.UNINSTALL_SCRIPT: uninstall_script("SapMachine 25 JDK", "21"), **SKIP}
    assert checks.check_uninstall(SAP25, files) == [
        "tools/chocolateyuninstall.ps1: $major is ['21'], manifest major is 25"]


def test_uninstall_rule_wrong_name_fails():
    files = {checks.UNINSTALL_SCRIPT: uninstall_script("SapMachine 21 JDK", "25"), **SKIP}
    assert checks.check_uninstall(SAP25, files) == [
        "tools/chocolateyuninstall.ps1: $softwareName is ['SapMachine 21 JDK'], expected 'SapMachine 25 JDK'"]


def test_uninstall_rule_missing_skip_file_fails():
    files = {checks.UNINSTALL_SCRIPT: uninstall_script("SapMachine 25 JDK", "25")}
    errors = checks.check_uninstall(SAP25, files)
    assert len(errors) == 1 and errors[0].startswith("tools/.skipAutoUninstall is missing")


def test_validate_package_runs_uninstall_rule(tmp_path):
    shutil.copytree(PKG_FIXTURES / "zulu-8", tmp_path / "zulu-8")
    p = pkg(id="zulu8", folder="zulu-8", vendor="zulu", major=8)
    tools = tmp_path / "zulu-8/tools"
    (tools / "chocolateyuninstall.ps1").write_bytes(uninstall_script("Zulu 8", "8"))
    assert checks.validate_package(tmp_path, p).errors == [
        "tools/.skipAutoUninstall is missing (Chocolatey's auto-uninstaller could remove another major's build)"]
    (tools / ".skipAutoUninstall").write_bytes(b"")
    assert checks.validate_package(tmp_path, p).errors == []  # zulu: no pinned product name
    moved = pkg(id="zulu8", folder="zulu-8", vendor="zulu", major=25)
    assert "tools/chocolateyuninstall.ps1: $major is ['8'], manifest major is 25" in checks.validate_package(
        tmp_path, moved).errors


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
