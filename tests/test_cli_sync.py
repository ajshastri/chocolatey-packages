import os
import stat
from pathlib import Path

import pytest

from chocotools import chocolatey, cli, sources
from chocotools.sources import Release
from conftest import FakeClient, PKG_FIXTURES, copy_pkg

SHA = "e" * 64
MANIFEST = """
[[package]]
id = "zulu8"
folder = "zulu-8"
vendor = "zulu"
major = 8
image = "jdk"
arch = ["x64"]

[[package]]
id = "openjdk"
folder = "OpenJDK"
vendor = "openjdk"
major = 27
image = "jdk"
arch = ["x64"]

[[package]]
id = "mvndaemon"
folder = "mvndaemon"
vendor = "mvnd"
arch = ["x64"]

[[package]]
id = "wildfly"
folder = "WildFly"
vendor = "wildfly"
arch = ["neutral"]

[[package]]
id = "Temurin8"
folder = "temurin-8-jdk"
vendor = "temurin"
major = 8
image = "jdk"
arch = ["x64"]

[[package]]
id = "graalvm-java17"
folder = "GraalVM-17"
vendor = "graalvm"
major = 17
image = "jdk"
arch = ["x64"]
frozen = true

[[package]]
id = "graalvm"
folder = "GraalVM"
vendor = "graalvm"
major = 25
image = "jdk"
arch = ["x64"]
"""

GRAALVM_URL = ("https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.3.4.1/"
               "graalvm-community-jdk-25i3-25.0.4.1_windows-x64_bin.zip")

RELEASES = {
    "zulu8": Release("8.98.0.1", "8.98.0.1", {"x64": "https://cdn.azul.com/zulu/bin/zulu8.98.0.1-ca-fx-jdk8.0.512-win_x64.msi"},
                     {"x64": SHA}, "azul sha256_hash"),
    "openjdk": Release("27.0.0", "27", {"x64": "https://download.java.net/java/GA/jdk27/x/35/GPL/openjdk-27_windows-x64_bin.zip"},
                       {"x64": SHA}, "jdk.java.net .sha256"),
    "mvndaemon": Release("1.0.7", "1.0.7", {"x64": "https://github.com/apache/maven-mvnd/releases/download/1.0.7/maven-mvnd-1.0.7-windows-amd64.zip"},
                         {"x64": SHA}, "github asset digest"),
    "wildfly": Release("41.0.1", "41.0.1.Final", {"neutral": "https://github.com/wildfly/wildfly/releases/download/41.0.1.Final/wildfly-41.0.1.Final.zip"},
                       {"neutral": SHA}, "github asset digest"),
    "Temurin8": Release("8.504.1", "jdk8u504-b01", {"x64": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u504-b01/OpenJDK8U-jdk_x64_windows_hotspot_8u504b01.msi"},
                        {"x64": "5115720df210f3c98b592ea2cb9981f48ba6b6942a7c40ba7fe4a59c37d5b815"}, "adoptium installer.checksum"),
    "graalvm": Release("25.3.4.1", "25.3.4.1", {"x64": GRAALVM_URL}, {"x64": SHA}, "github asset digest"),
}
EXTRAS = {"openjdk": "27", "mvndaemon": "maven-mvnd-1.0.7-windows-amd64", "wildfly": "41.0.1.Final",
          "graalvm": "graalvm-community-25.3.4.1+1.1"}


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "packages.toml").write_text(MANIFEST, encoding="utf-8")
    for folder in ("zulu-8", "OpenJDK", "mvndaemon", "WildFly", "temurin-8-jdk", "GraalVM-17", "GraalVM"):
        copy_pkg(folder, tmp_path)
    state = {"approved": {}, "fail": set(), "releases": {k: v for k, v in RELEASES.items()}}

    def fake_fetch(pkg, *, version=None, client=None):
        if pkg.id in state["fail"]:
            raise sources.SourceError("upstream returned nothing")
        r = state["releases"][pkg.id]
        return Release(r.version, r.version_raw, dict(r.urls), dict(r.sha256), r.checksum_source,
                       release_notes_url=r.release_notes_url)

    def fake_extras(pkg, release, client=None):
        return {"dir_version": EXTRAS[pkg.id]} if pkg.id in EXTRAS else {}

    def fake_approved(pid, client=None):
        if pid in state["approved"] and isinstance(state["approved"][pid], Exception):
            raise state["approved"][pid]
        return state["approved"].get(pid)

    monkeypatch.setattr(sources, "fetch", fake_fetch)
    monkeypatch.setattr(sources, "resolve_extras", fake_extras)
    monkeypatch.setattr(chocolatey, "approved_version", fake_approved)
    state["root"] = tmp_path
    return state


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def run(root, *args):
    return cli.main(["--root", str(root), *args], client=FakeClient(use_index=False))


def test_dry_run_writes_nothing(repo, capsys):
    before = snapshot(repo["root"])
    code = run(repo["root"], "sync", "--dry-run", "--id", "zulu8,openjdk", "--id", "mvndaemon", "--id", "wildfly")
    assert code == 0
    assert snapshot(repo["root"]) == before
    text = capsys.readouterr().out
    assert text.count("would update") == 4
    assert "| zulu8 | 8.96.0.205 | 8.98.0.1 | would update |" in text


def test_fail_closed_leaves_files_identical(repo, capsys):
    repo["fail"].add("zulu8")
    before = snapshot(repo["root"])
    assert run(repo["root"], "sync", "--id", "zulu8,mvndaemon") == 1
    after = snapshot(repo["root"])
    assert {k: v for k, v in after.items() if k.startswith("zulu-8/")} == {
        k: v for k, v in before.items() if k.startswith("zulu-8/")
    }
    out = capsys.readouterr().out
    assert "zulu8: source: upstream returned nothing" in out
    assert after["mvndaemon/mvndaemon.nuspec"] != before["mvndaemon/mvndaemon.nuspec"]  # others proceed


def test_increase_writes_sha256_and_type(repo):
    root = repo["root"]
    script = root / "zulu-8/tools/chocolateyinstall.ps1"
    old_sum = b"db296152b2ebf940767e8e88145465a27c238de074760e32759fe168a0ed0dee"
    script.write_bytes(script.read_bytes().replace(old_sum, b"d" * 32).replace(b"checksumType64= 'sha256'", b"checksumType64= 'md5'"))
    before = script.read_bytes()
    assert run(root, "sync", "--id", "zulu8") == 0
    after = script.read_bytes()
    expected = (
        before.replace(b"zulu8.96.0.205-ca-fx-jdk8.0.504-win_x64.msi", b"zulu8.98.0.1-ca-fx-jdk8.0.512-win_x64.msi")
        .replace(b"d" * 32, SHA.encode())
        .replace(b"checksumType64= 'md5'", b"checksumType64= 'sha256'")
    )
    assert after == expected
    assert b"<version>8.98.0.1</version>" in (root / "zulu-8/zulu-8.nuspec").read_bytes()
    assert (root / "zulu-8/zulu-8.nuspec").read_bytes().count(b"\r\n") == (PKG_FIXTURES / "zulu-8/zulu-8.nuspec").read_bytes().count(b"\r\n")


def test_version_bump_writes_release_notes(repo):
    root = repo["root"]
    old = (root / "mvndaemon/mvndaemon.nuspec").read_bytes()
    assert b"<releaseNotes>" not in old
    assert run(root, "sync", "--id", "mvndaemon") == 0
    notes = b"    <releaseNotes>https://github.com/apache/maven-mvnd/releases/tag/1.0.7</releaseNotes>\r\n"
    assert (root / "mvndaemon/mvndaemon.nuspec").read_bytes() == (
        old.replace(b"<version>1.0.6</version>", b"<version>1.0.7</version>")
        .replace(b"  </metadata>", notes + b"  </metadata>")
    )


def test_version_bump_replaces_release_notes(repo, monkeypatch):
    root = repo["root"]
    assert run(root, "sync", "--id", "mvndaemon") == 0
    repo["releases"]["mvndaemon"] = Release(
        "1.0.8", "1.0.8", {"x64": "https://github.com/apache/maven-mvnd/releases/download/1.0.8/maven-mvnd-1.0.8-windows-amd64.zip"},
        {"x64": SHA}, "github asset digest")
    monkeypatch.setitem(EXTRAS, "mvndaemon", "maven-mvnd-1.0.8-windows-amd64")
    assert run(root, "sync", "--id", "mvndaemon") == 0
    data = (root / "mvndaemon/mvndaemon.nuspec").read_bytes()
    assert data.count(b"<releaseNotes>") == 1
    assert b"<releaseNotes>https://github.com/apache/maven-mvnd/releases/tag/1.0.8</releaseNotes>" in data


def test_release_override_wins_over_derived_notes(repo):
    root = repo["root"]
    changelog = "https://github.com/graalvm/graalvm-ce-builds/blob/main/CHANGELOG.md"
    r = repo["releases"]["graalvm"]
    repo["releases"]["graalvm"] = Release(r.version, r.version_raw, r.urls, r.sha256, r.checksum_source,
                                          release_notes_url=changelog)
    assert run(root, "sync", "--id", "graalvm") == 0
    assert f"<releaseNotes>{changelog}</releaseNotes>".encode() in (root / "GraalVM/graalvm.nuspec").read_bytes()


def test_approved_at_or_above_new_fails(repo, capsys):
    repo["approved"]["zulu8"] = "8.98.0.1"
    before = snapshot(repo["root"])
    assert run(repo["root"], "sync", "--id", "zulu8") == 1
    assert snapshot(repo["root"]) == before
    assert "not greater than Chocolatey approved 8.98.0.1" in capsys.readouterr().out


def test_chocolatey_unreachable_fails(repo, capsys):
    repo["approved"]["zulu8"] = chocolatey.ChocolateyError("Chocolatey feed unreachable for zulu8")
    assert run(repo["root"], "sync", "--id", "zulu8") == 1
    assert "unreachable" in capsys.readouterr().out


def test_upstream_lower_than_repo_fails(repo, capsys):
    repo["releases"]["zulu8"] = Release("8.90.0.1", "8.90.0.1", {"x64": "https://cdn.azul.com/a.msi"}, {"x64": SHA}, "t")
    before = snapshot(repo["root"])
    assert run(repo["root"], "sync", "--id", "zulu8") == 1
    assert snapshot(repo["root"]) == before
    assert "lower than repo" in capsys.readouterr().out


ZULU8_URL = "https://cdn.azul.com/zulu/bin/zulu8.96.0.205-ca-fx-jdk8.0.504-win_x64.msi"  # in the zulu-8 fixture


def test_equal_version_is_up_to_date(repo, capsys):
    repo["releases"]["zulu8"] = Release("8.96.0.205", "8.96.0.205", {"x64": ZULU8_URL}, {"x64": SHA}, "t")
    before = snapshot(repo["root"])
    assert run(repo["root"], "sync", "--id", "zulu8") == 0
    assert snapshot(repo["root"]) == before
    assert "| zulu8 | 8.96.0.205 | 8.96.0.205 | up-to-date |" in capsys.readouterr().out


def test_equal_version_with_another_url_fails(repo, capsys):
    # e.g. a rebuilt upstream build, or two upstream versions mapping to one package version
    new_url = "https://cdn.azul.com/zulu/bin/zulu8.96.0.205-ca-fx-jdk8.0.504-win_x64-rebuild.msi"
    repo["releases"]["zulu8"] = Release("8.96.0.205", "8.96.0.205", {"x64": new_url}, {"x64": SHA}, "t")
    before = snapshot(repo["root"])
    assert run(repo["root"], "sync", "--id", "zulu8") == 1
    assert snapshot(repo["root"]) == before
    out = capsys.readouterr().out
    assert "| zulu8 | 8.96.0.205 | 8.96.0.205 | failed |" in out
    assert (f"- zulu8: upstream build changed ({new_url}) but maps to the existing version 8.96.0.205; "
            f"refusing to treat as up-to-date (install script has {ZULU8_URL})") in out


def test_dir_version_tokens(repo):
    root = repo["root"]
    assert run(root, "sync", "--id", "openjdk,mvndaemon,wildfly") == 0
    for name in ("chocolateyinstall.ps1", "chocolateyuninstall.ps1", "chocolateyBeforeModify.ps1"):
        data = (root / "OpenJDK/tools" / name).read_bytes()
        assert b'$version = "27"' in data or b"$version = '27'" in data, name
    inst = (root / "mvndaemon/tools/chocolateyinstall.ps1").read_bytes()
    assert b"/download/1.0.7/maven-mvnd-1.0.7-windows-amd64.zip'" in inst
    assert b"$targetDir\\maven-mvnd-1.0.7-windows-amd64\\bin" in inst
    for name in ("chocolateyuninstall.ps1", "chocolateyBeforeModify.ps1"):
        assert b"maven-mvnd-1.0.7-windows-amd64" in (root / "mvndaemon/tools" / name).read_bytes()
    assert b'$version = "41.0.1.Final"' in (root / "WildFly/tools/chocolateyuninstall.ps1").read_bytes()
    assert b"<version>41.0.1</version>" in (root / "WildFly/wildfly.nuspec").read_bytes()


def test_graalvm_dir_follows_zip_root(repo):
    root = repo["root"]
    before = {n: (root / "GraalVM/tools" / n).read_bytes() for n in ("chocolateyinstall.ps1", "chocolateyuninstall.ps1")}
    assert run(root, "sync", "--id", "graalvm") == 0
    old_dir = b'$graalvmDir = "graalvm-community-openjdk-25.0.2+10.1"'
    new_dir = b'$graalvmDir = "graalvm-community-25.3.4.1+1.1"'
    for name, old in before.items():
        new = (root / "GraalVM/tools" / name).read_bytes()
        assert old_dir in old and new_dir in new, name
        assert new.count(b"\r\n") == old.count(b"\r\n"), name
    inst = (root / "GraalVM/tools/chocolateyinstall.ps1").read_bytes()
    assert inst == (
        before["chocolateyinstall.ps1"]
        .replace(old_dir, new_dir)
        .replace(b"releases/download/jdk-25.0.2/graalvm-community-jdk-25.0.2_windows-x64_bin.zip",
                 b"releases/download/graal-25.3.4.1/graalvm-community-jdk-25i3-25.0.4.1_windows-x64_bin.zip")
        .replace(b"72edc27ce2dd3c156332144a339c97995745cae291205ed2f9b5cc26aa9cb422", SHA.encode())
    )
    assert (root / "GraalVM/tools/chocolateyuninstall.ps1").read_bytes() == before["chocolateyuninstall.ps1"].replace(old_dir, new_dir)
    assert b"<version>25.3.4.1</version>" in (root / "GraalVM/graalvm.nuspec").read_bytes()


GRAALVM_25I4_URL = ("https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.4.4.1.1/"
                    "graalvm-community-jdk-25i4-25.0.4.1.1_windows-x64_bin.zip")


def test_graalvm_five_part_tag_syncs_to_four_part_version(repo, monkeypatch, capsys):
    # graal-25.4.4.1.1 used to fail with "after update: x64 URL: more than 4 parts: 25.4.4.1.1"
    root = repo["root"]
    repo["releases"]["graalvm"] = Release("25.4.4.1", "25.4.4.1", {"x64": GRAALVM_25I4_URL}, {"x64": SHA},
                                          "github asset digest")
    monkeypatch.setitem(EXTRAS, "graalvm", "graalvm-community-25.4.4.1.1+1.1")  # the real 25i4 zip root
    assert run(root, "sync", "--id", "graalvm") == 0, capsys.readouterr().out
    inst = (root / "GraalVM/tools/chocolateyinstall.ps1").read_bytes()
    assert GRAALVM_25I4_URL.encode() in inst
    for name in ("chocolateyinstall.ps1", "chocolateyuninstall.ps1"):
        assert b'$graalvmDir = "graalvm-community-25.4.4.1.1+1.1"' in (root / "GraalVM/tools" / name).read_bytes()
    assert b"<version>25.4.4.1</version>" in (root / "GraalVM/graalvm.nuspec").read_bytes()


OPENJDK_27_0_1_0_3 = ("https://download.java.net/java/GA/jdk27.0.1.0.3/b14170c9b2de463d9b89442c6db3e384/1/GPL/"
                      "openjdk-27.0.1.0.3_windows-x64_bin.zip")


def test_openjdk_five_part_version_syncs_to_mapped_version(repo, monkeypatch, capsys):
    # 27.0.1.0.3 used to fail with "source: OpenJDK version '27.0.1.0.3': more than 4 parts"
    root = repo["root"]
    repo["releases"]["openjdk"] = Release("27.0.1.3", "27.0.1.0.3", {"x64": OPENJDK_27_0_1_0_3}, {"x64": SHA},
                                          "jdk.java.net .sha256")
    monkeypatch.setitem(EXTRAS, "openjdk", "27.0.1.0.3")
    assert run(root, "sync", "--id", "openjdk") == 0, capsys.readouterr().out
    assert b"<version>27.0.1.3</version>" in (root / "OpenJDK/openjdk.nuspec").read_bytes()
    assert OPENJDK_27_0_1_0_3.encode() in (root / "OpenJDK/tools/chocolateyinstall.ps1").read_bytes()
    for name in ("chocolateyinstall.ps1", "chocolateyuninstall.ps1", "chocolateyBeforeModify.ps1"):
        data = (root / "OpenJDK/tools" / name).read_bytes()
        assert b'$version = "27.0.1.0.3"' in data or b"$version = '27.0.1.0.3'" in data, name


def test_post_update_validation_failure_writes_nothing(repo, capsys):
    before = snapshot(repo["root"])
    assert run(repo["root"], "sync", "--id", "Temurin8") == 1  # x86 Url still present
    assert snapshot(repo["root"]) == before
    assert "after update" in capsys.readouterr().out


def test_report_and_frozen_skip(repo, tmp_path):
    report = tmp_path / "out" / "sync-report.md"
    code = run(repo["root"], "sync", "--dry-run", "--id", "graalvm-java17,zulu8", "--report", str(report))
    assert code == 0
    text = report.read_text(encoding="utf-8")
    assert "| graalvm-java17 |  |  | skipped |" in text and "would update" in text


@pytest.mark.skipif(os.name == "nt", reason="Windows has no POSIX mode bits (os.chmod only sets read-only)")
def test_write_files_keeps_the_target_mode(tmp_path):
    # OpenJDK/ files are 100755 in git; sync used to commit them as 100644
    script = tmp_path / "tools" / "chocolateyinstall.ps1"
    script.parent.mkdir()
    script.write_bytes(b"old")
    script.chmod(0o755)
    cli.write_files(tmp_path, {"tools/chocolateyinstall.ps1": b"new", "tools/new.ps1": b"created"})
    assert script.read_bytes() == b"new"
    assert stat.S_IMODE(script.stat().st_mode) == 0o755
    assert (tmp_path / "tools" / "new.ps1").read_bytes() == b"created"
    assert not list(tmp_path.rglob("*.chocotools-tmp"))


def test_unknown_id_is_usage_error(repo):
    assert run(repo["root"], "sync", "--id", "nope") == 2
