import subprocess
from pathlib import Path

import pytest

from chocotools import chocolatey, cli
from conftest import FakeClient, copy_pkg

MANIFEST = """
[[package]]
id = "zulu8"
folder = "zulu-8"
vendor = "zulu"
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
"""
ZULU_URL = "https://cdn.azul.com/zulu/bin/zulu8.96.0.205-ca-fx-jdk8.0.504-win_x64.msi"


@pytest.fixture
def env(tmp_path, monkeypatch):
    (tmp_path / "packages.toml").write_text(MANIFEST, encoding="utf-8")
    copy_pkg("zulu-8", tmp_path)
    copy_pkg("GraalVM-17", tmp_path)
    state = {"cmds": [], "status": "", "approved": "8.90.0.1", "fail": set()}

    def fake_run(cmd, *, cwd=None):
        state["cmds"].append(list(cmd))
        stdout, code = "", 0
        if cmd[:2] == ["git", "status"]:
            stdout = state["status"]
        elif cmd[:2] == ["choco", "pack"]:
            out_dir = Path(cmd[cmd.index("--output-directory") + 1])
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "zulu8.8.96.0.205.nupkg").write_bytes(b"nupkg")
        if cmd[1] in state["fail"]:
            code = 1
        return subprocess.CompletedProcess(cmd, code, stdout, "")

    monkeypatch.setattr(cli, "_run", fake_run)
    monkeypatch.setattr(cli, "choco_available", lambda: "C:/choco/choco.exe")
    monkeypatch.setattr(chocolatey, "approved_version", lambda pid, client=None: state["approved"])
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("CHOCO_KEY", raising=False)
    state["root"] = tmp_path
    state["client"] = FakeClient(head={ZULU_URL: {"status": 200, "headers": {}}}, use_index=False)
    return state


def run(env, *args):
    return cli.main(["--root", str(env["root"]), "publish", *args], client=env["client"])


def choco_cmds(env):
    return [c[1] for c in env["cmds"] if c[0] == "choco"]


def test_dirty_tree_is_refused(env, capsys):
    env["status"] = " M zulu-8/zulu-8.nuspec\n"
    assert run(env, "--id", "zulu8", "--dry-run") == 1
    assert choco_cmds(env) == []
    assert "working tree is not clean" in capsys.readouterr().out


def test_dry_run_packs_but_never_installs_or_pushes_outside_ci(env, capsys):
    assert run(env, "--id", "zulu8", "--dry-run") == 0
    assert choco_cmds(env) == ["pack"]
    out = capsys.readouterr().out
    assert "test install runs in CI only" in out and "not pushed" in out


def test_ci_installs_and_pushes_with_masked_key(env, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("CHOCO_KEY", "secret-key")
    assert run(env, "--id", "zulu8") == 0
    assert choco_cmds(env) == ["pack", "install", "uninstall", "push"]
    push = next(c for c in env["cmds"] if c[:2] == ["choco", "push"])
    assert push[push.index("--source") + 1] == "https://push.chocolatey.org/"
    assert push[push.index("-k") + 1] == "secret-key"
    out = capsys.readouterr().out
    assert "secret-key" not in out and "-k ***" in out


def test_ci_dry_run_installs_but_does_not_push(env, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert run(env, "--id", "zulu8", "--dry-run") == 0
    assert choco_cmds(env) == ["pack", "install", "uninstall"]


def test_missing_key_is_prerequisite_error(env):
    assert run(env, "--id", "zulu8") == 3
    assert env["cmds"] == []


def test_no_choco_is_prerequisite_error(env, monkeypatch):
    monkeypatch.setattr(cli, "choco_available", lambda: None)
    assert run(env, "--id", "zulu8", "--dry-run") == 3


def test_version_equal_to_approved_is_skipped(env, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("CHOCO_KEY", "k")
    env["approved"] = "8.96.0.205"
    assert run(env, "--id", "zulu8") == 0
    assert choco_cmds(env) == []
    assert "skip  zulu8: 8.96.0.205 already approved on Chocolatey" in capsys.readouterr().out


def test_version_below_approved_fails(env, capsys):
    env["approved"] = "8.97.0.1"
    assert run(env, "--id", "zulu8", "--dry-run") == 1
    assert choco_cmds(env) == []
    assert "not greater than Chocolatey approved 8.97.0.1" in capsys.readouterr().out


def test_failed_install_stops_push(env, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("CHOCO_KEY", "k")
    env["fail"].add("install")
    assert run(env, "--id", "zulu8") == 1
    assert "push" not in choco_cmds(env)


def test_frozen_packages_are_skipped(env, capsys):
    assert run(env, "--id", "graalvm-java17", "--dry-run") == 0
    assert env["cmds"] == []
    assert "skip  graalvm-java17: frozen" in capsys.readouterr().out


def test_changed_range_maps_folders(env, monkeypatch):
    def fake_run(cmd, *, cwd=None):
        env["cmds"].append(list(cmd))
        out = "zulu-8/zulu-8.nuspec\nREADME.md\nGraalVM-17/tools/chocolateyinstall.ps1\n" if cmd[:2] == ["git", "diff"] else ""
        return subprocess.CompletedProcess(cmd, 0, out, "")

    monkeypatch.setattr(cli, "_run", fake_run)
    from chocotools import manifest

    mf = manifest.load(env["root"])
    pkgs = cli.changed_packages(env["root"], mf, "0000000000000000000000000000000000000000..abc123")
    assert [p.id for p in pkgs] == ["graalvm-java17", "zulu8"]
    assert ["git", "diff", "--name-only", "abc123~1", "abc123"] in env["cmds"]
