"""Package fix versions: scheme, manifest field, sync and compare behaviour."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chocotools import chocolatey, cli, manifest, sources, versioning
from chocotools.sources import Release
from conftest import FakeClient, copy_pkg

# ----- scheme ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("upstream", "fix", "expected"),
    [
        ("21.0.12.1", 1, "21.0.12.101"),  # the rejected Temurin versions
        ("11.0.32.1", 1, "11.0.32.101"),
        ("17.0.20.1", 1, "17.0.20.101"),
        ("25.0.4.1", 1, "25.0.4.101"),
        ("21.0.12.1", 2, "21.0.12.102"),  # a second fix of the same upstream
        ("21.0.12.2", 1, "21.0.12.201"),  # upstream respin while the fix is active
        ("8.504.1", 1, "8.504.1.1"),  # Temurin 8, 3 parts
        ("21.0.13", 1, "21.0.13.1"),
        ("25.0.4.101", 1, "25.0.4.10101"),  # Corretto 25.0.4.10.1
        ("21.52.203", 1, "21.52.203.1"),  # Zulu
    ],
)
def test_apply_and_strip_round_trip(upstream, fix, expected):
    assert versioning.apply_package_fix(upstream, fix) == expected
    assert versioning.equal(versioning.strip_package_fix(expected, fix), upstream)


@pytest.mark.parametrize(
    ("rejected", "fixed", "later"),
    [
        ("21.0.12.1", "21.0.12.101", ["21.0.12.201", "21.0.13", "21.0.13.1", "22.0.0"]),
        ("11.0.32.1", "11.0.32.101", ["11.0.32.201", "11.0.33", "11.0.33.1"]),
        ("17.0.20.1", "17.0.20.101", ["17.0.20.201", "17.0.21"]),
        ("25.0.4.1", "25.0.4.101", ["25.0.4.201", "25.0.5", "25.0.5.1"]),
    ],
)
def test_fix_sorts_above_rejected_and_below_every_later_release(rejected, fixed, later):
    """The fix is above the rejected version; the next respin (as sync writes it
    while the fix is active) and the next update (fix cleared) are above the fix."""
    assert versioning.compare_nuget(fixed, rejected) > 0
    assert len(versioning.parse(fixed)) <= versioning.MAX_PARTS
    for version in later:
        assert versioning.compare_nuget(version, fixed) > 0, version


def test_target_version_rules():
    tv = versioning.target_version
    assert tv("21.0.12.1", None, None) == ("21.0.12.1", False)
    assert tv("21.0.12.1", 1, "21.0.12") == ("21.0.12.101", True)  # on the declared line
    assert tv("21.0.12.2", 1, "21.0.12") == ("21.0.12.201", True)  # respin keeps the suffix
    assert tv("21.0.13", 1, "21.0.12") == ("21.0.13", False)  # new A.B.C: fix cleared
    with pytest.raises(versioning.VersionError, match="package_fix_line"):
        tv("21.0.12.1", 1, None)


def test_target_version_ignores_the_repo_line():
    """The fix is keyed to the declared line, not to wherever the nuspec is now:
    a nuspec hand-bumped to 21.0.13 never turns upstream 21.0.13 into 21.0.13.1."""
    assert versioning.target_version("21.0.13", 1, "21.0.12") == ("21.0.13", False)
    assert versioning.target_version("21.0.13.1", 1, "21.0.12") == ("21.0.13.1", False)


@pytest.mark.parametrize("bad", [0, 100, -1, True, "1"])
def test_invalid_fix_values(bad):
    with pytest.raises(versioning.VersionError):
        versioning.apply_package_fix("21.0.12.1", bad)


def test_strip_rejects_version_without_the_fix_digits():
    # 21.0.12.1 with fix 1 is the fix of upstream 21.0.12 (P = 0), so it is valid.
    assert versioning.strip_package_fix("21.0.12.1", 1) == "21.0.12"
    with pytest.raises(versioning.VersionError):
        versioning.strip_package_fix("21.0.12.1", 2)
    with pytest.raises(versioning.VersionError):
        versioning.strip_package_fix("21.0.12.102", 1)


# ----- manifest ----------------------------------------------------------------

MANIFEST = """# header
[[package]]
id = "Temurin21"
folder = "temurin-21-jdk"
vendor = "temurin"
major = 21
image = "jdk"
arch = ["x64"]
frozen = false
package_fix = 1  # 21.0.12.1 was rejected on Chocolatey (16 Sep 2026); sync removes both lines
package_fix_line = "21.0.12"
notes = ""

[[package]]
id = "Temurin21jre"
folder = "temurin-21-jre"
vendor = "temurin"
major = 21
image = "jre"
arch = ["x64"]
package_fix = 3
package_fix_line = "21.0.12"
"""
FIX_LINES = (
    "package_fix = 1  # 21.0.12.1 was rejected on Chocolatey (16 Sep 2026); sync removes both lines\n"
    'package_fix_line = "21.0.12"\n'
)


def test_manifest_parses_package_fix():
    mf = manifest.parse(MANIFEST)
    assert {p.id: (p.package_fix, p.package_fix_line) for p in mf.packages} == {
        "Temurin21": (1, "21.0.12"), "Temurin21jre": (3, "21.0.12")}


@pytest.mark.parametrize("bad", ["0", "100", "true", '"1"', "1.5"])
def test_manifest_rejects_bad_package_fix(bad):
    with pytest.raises(manifest.ManifestError, match="package_fix"):
        manifest.parse(MANIFEST.replace("package_fix = 3", f"package_fix = {bad}"))


@pytest.mark.parametrize("bad", ['"21.0"', '"21.0.12.1"', '"21.0.x"', "21", '""'])
def test_manifest_rejects_bad_package_fix_line(bad):
    with pytest.raises(manifest.ManifestError, match="package_fix_line"):
        manifest.parse(MANIFEST.replace('package_fix = 3\npackage_fix_line = "21.0.12"',
                                        f"package_fix = 3\npackage_fix_line = {bad}"))


def test_manifest_requires_fix_and_line_together():
    with pytest.raises(manifest.ManifestError, match="must be set together"):
        manifest.parse(MANIFEST.replace('package_fix = 3\npackage_fix_line = "21.0.12"\n', "package_fix = 3\n"))
    with pytest.raises(manifest.ManifestError, match="must be set together"):
        manifest.parse(MANIFEST.replace("package_fix = 3\n", ""))


def test_clear_package_fix_is_a_minimal_edit():
    new = manifest.clear_package_fix(MANIFEST, "Temurin21")
    assert new == MANIFEST.replace(FIX_LINES, "")
    assert {p.id: (p.package_fix, p.package_fix_line) for p in manifest.parse(new).packages} == {
        "Temurin21": (None, None), "Temurin21jre": (3, "21.0.12")}
    crlf = MANIFEST.replace("\n", "\r\n")
    assert manifest.clear_package_fix(crlf, "Temurin21jre") == crlf.replace(
        'package_fix = 3\r\npackage_fix_line = "21.0.12"\r\n', "")


def test_clear_package_fix_errors():
    with pytest.raises(manifest.ManifestError, match="no \\[\\[package\\]\\]"):
        manifest.clear_package_fix(MANIFEST, "Temurin17")
    once = manifest.clear_package_fix(MANIFEST, "Temurin21")
    with pytest.raises(manifest.ManifestError, match="expected one package_fix line"):
        manifest.clear_package_fix(once, "Temurin21")


# ----- sync and compare ----------------------------------------------------------

SHA = "454cfd334b9ca91c96dd8c2de97fcef6b9f1f98be9172ff076711f1c6b44e4e0"
URL_12_1 = ("https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/"
            "OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.msi")
URL_12_2 = ("https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.2%2B1/"
            "OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.2_1.msi")
URL_13 = ("https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B8/"
          "OpenJDK21U-jdk_x64_windows_hotspot_21.0.13_8.msi")
ONE_PACKAGE = MANIFEST.split("\n[[package]]\nid = \"Temurin21jre\"")[0] + "\n"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "packages.toml").write_bytes(ONE_PACKAGE.encode("utf-8"))
    copy_pkg("temurin-21-jdk", tmp_path)
    state = {"root": tmp_path, "release": ("21.0.12.1", "jdk-21.0.12.1+1", URL_12_1, SHA)}

    def fake_fetch(pkg, *, version=None, client=None):
        v, raw, url, sha = state["release"]
        return Release(v, raw, {"x64": url}, {"x64": sha}, "adoptium installer.checksum")

    monkeypatch.setattr(sources, "fetch", fake_fetch)
    monkeypatch.setattr(sources, "resolve_extras", lambda pkg, release, client=None: {})
    monkeypatch.setattr(chocolatey, "approved_version", lambda pid, client=None: "21.0.9.10")
    return state


def run(root: Path, *args: str) -> int:
    return cli.main(["--root", str(root), *args], client=FakeClient(use_index=False))


def nuspec_version(root: Path) -> bytes:
    return (root / "temurin-21-jdk/temurin21.nuspec").read_bytes()


def test_sync_applies_fix_then_reports_no_change(repo, capsys):
    root = repo["root"]
    script_before = (root / "temurin-21-jdk/tools/chocolateyinstall.ps1").read_bytes()
    nuspec_before = nuspec_version(root)
    assert run(root, "sync", "--dry-run") == 0
    assert "| Temurin21 | 21.0.12.1 | 21.0.12.101 | would update |" in capsys.readouterr().out
    assert run(root, "sync") == 0
    assert nuspec_version(root) == nuspec_before.replace(b"<version>21.0.12.1</version>", b"<version>21.0.12.101</version>")
    assert (root / "temurin-21-jdk/tools/chocolateyinstall.ps1").read_bytes() == script_before  # same binary
    assert (root / "packages.toml").read_bytes() == ONE_PACKAGE.encode("utf-8")  # fix stays
    capsys.readouterr()
    assert run(root, "sync", "--dry-run") == 0
    out = capsys.readouterr().out
    assert "| Temurin21 | 21.0.12.101 | 21.0.12.101 | up-to-date |" in out
    assert "package fix 1 (upstream 21.0.12.1)" in out
    assert "0 changed, 0 failed, 1 checked." in out
    assert run(root, "validate") == 0


def test_sync_respin_keeps_fix_suffix(repo, capsys):
    root = repo["root"]
    assert run(root, "sync") == 0
    repo["release"] = ("21.0.12.2", "jdk-21.0.12.2+1", URL_12_2, "a" * 64)
    assert run(root, "sync") == 0
    assert b"<version>21.0.12.201</version>" in nuspec_version(root)
    assert b"package_fix = 1" in (root / "packages.toml").read_bytes()


def test_sync_next_update_clears_fix(repo, capsys):
    root = repo["root"]
    assert run(root, "sync") == 0
    repo["release"] = ("21.0.13", "jdk-21.0.13+8", URL_13, "b" * 64)
    manifest_before = (root / "packages.toml").read_bytes()
    capsys.readouterr()
    assert run(root, "sync", "--dry-run") == 0
    out = capsys.readouterr().out
    assert "| Temurin21 | 21.0.12.101 | 21.0.13 | would update |" in out
    assert "package_fix 1 cleared" in out
    assert (root / "packages.toml").read_bytes() == manifest_before  # dry run writes nothing
    assert run(root, "sync") == 0
    assert b"<version>21.0.13</version>" in nuspec_version(root)
    assert (root / "packages.toml").read_bytes() == manifest_before.replace(FIX_LINES.encode("utf-8"), b"")
    capsys.readouterr()
    assert run(root, "sync", "--dry-run") == 0
    assert "| Temurin21 | 21.0.13 | 21.0.13 | up-to-date |" in capsys.readouterr().out


def hand_bump_to_21_0_13(root: Path) -> None:
    """The nuspec and URL reach 21.0.13 while package_fix is still declared for 21.0.12
    (a hand edit, or sync's folder write succeeding and its packages.toml write failing)."""
    nuspec_file = root / "temurin-21-jdk/temurin21.nuspec"
    data = nuspec_file.read_bytes()
    nuspec_file.write_bytes(data.replace(b"<version>21.0.12.1</version>", b"<version>21.0.13</version>"))
    script = root / "temurin-21-jdk/tools/chocolateyinstall.ps1"
    old = URL_12_1.encode("utf-8")
    assert old in script.read_bytes()
    script.write_bytes(script.read_bytes().replace(old, URL_13.encode("utf-8")))


def test_stale_fix_is_reported_not_carried_to_the_new_line(repo, capsys):
    root = repo["root"]
    hand_bump_to_21_0_13(root)
    manifest_before = (root / "packages.toml").read_bytes()
    assert run(root, "validate") == cli.EXIT_FAILED
    out = capsys.readouterr().out
    assert "package_fix 1 is stale: it was declared for 21.0.12 but the nuspec version 21.0.13" in out
    assert "run sync" not in out
    repo["release"] = ("21.0.13", "jdk-21.0.13+8", URL_13, SHA)
    assert run(root, "sync") == 0
    out = capsys.readouterr().out
    assert "| Temurin21 | 21.0.13 | 21.0.13 | up-to-date |" in out
    assert "package_fix 1 is stale (declared for 21.0.12)" in out
    assert b"<version>21.0.13</version>" in nuspec_version(root)  # never 21.0.13.1
    assert (root / "packages.toml").read_bytes() == manifest_before
    # Removing the two lines, as the message says, makes the package valid again.
    (root / "packages.toml").write_bytes(manifest_before.replace(FIX_LINES.encode("utf-8"), b""))
    assert run(root, "validate") == 0


def test_compare_reports_fix_as_in_sync(repo):
    root = repo["root"]
    assert run(root, "sync") == 0
    out = root / "compare.json"
    assert run(root, "compare", "--format", "json", "--output", str(out)) == 0
    (row,) = json.loads(out.read_text(encoding="utf-8"))
    assert row["repo"] == "21.0.12.101" and row["source"] == "21.0.12.1"
    assert row["status"] == "in-sync"
    assert row["note"] == "package fix 1: 21.0.12.1 -> 21.0.12.101"
    md = root / "compare.md"
    assert run(root, "compare", "--output", str(md)) == 0
    assert "| in-sync | package fix 1: 21.0.12.1 -> 21.0.12.101 |" in md.read_text(encoding="utf-8")
