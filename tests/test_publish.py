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
    # "output": choco subcommand -> (stdout, stderr) the fake choco prints
    state = {"cmds": [], "status": "", "approved": "8.90.0.1", "fail": set(), "output": {}}

    def fake_run(cmd, *, cwd=None):
        state["cmds"].append(list(cmd))
        stdout, stderr, code = "", "", 0
        if cmd[:2] == ["git", "status"]:
            stdout = state["status"]
        elif cmd[0] == "choco":
            stdout, stderr = state["output"].get(cmd[1], ("", ""))
        if cmd[:2] == ["choco", "pack"]:
            out_dir = Path(cmd[cmd.index("--output-directory") + 1])
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "zulu8.8.96.0.205.nupkg").write_bytes(b"nupkg")
        if cmd[1] in state["fail"]:
            code = 1
        return subprocess.CompletedProcess(cmd, code, stdout, stderr)

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


def test_ci_prints_choco_output_in_log_groups(env, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    env["output"] = {
        "pack": ("Successfully created package 'zulu8.8.96.0.205.nupkg'", ""),
        "install": ("Installing zulu8 8.96.0.205\nThe install of zulu8 was successful.", ""),
        "uninstall": ("zulu8 has been successfully uninstalled.", "a warning on stderr"),
    }
    assert run(env, "--id", "zulu8", "--dry-run") == 0
    lines = capsys.readouterr().out.splitlines()
    starts = [line for line in lines if line.startswith("::group::")]
    assert starts == ["::group::choco pack zulu8 8.96.0.205", "::group::choco install zulu8 8.96.0.205",
                      "::group::choco uninstall zulu8 8.96.0.205"]
    assert lines.count("::endgroup::") == 3
    # every group: title, command line, workflow commands paused around choco's output, end
    i = lines.index("::group::choco install zulu8 8.96.0.205")
    assert lines[i + 1].startswith("$ choco install zulu8 --version 8.96.0.205")
    token = lines[i + 2].removeprefix("::stop-commands::")
    assert lines[i + 2].startswith("::stop-commands::") and len(token) == 32
    assert lines[i + 3:i + 7] == ["Installing zulu8 8.96.0.205", "The install of zulu8 was successful.",
                                  f"::{token}::", "::endgroup::"]
    j = lines.index("::group::choco uninstall zulu8 8.96.0.205")
    assert "zulu8 has been successfully uninstalled." in lines[j:j + 8]
    assert "a warning on stderr" in lines[j:j + 8]


def test_local_output_is_plain(env, capsys):
    env["output"] = {"pack": ("Successfully created package 'zulu8.8.96.0.205.nupkg'", "")}
    assert run(env, "--id", "zulu8", "--dry-run") == 0
    out = capsys.readouterr().out
    assert "Successfully created package 'zulu8.8.96.0.205.nupkg'" in out
    assert "::group::" not in out and "::endgroup::" not in out and "::stop-commands::" not in out


def test_failed_install_error_carries_output_tail(env, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    env["fail"].add("install")
    env["output"] = {"install": ("x" * 3000 + "\nERROR: Running msiexec failed with exit code 1603.", "")}
    assert run(env, "--id", "zulu8", "--dry-run") == 1
    assert choco_cmds(env) == ["pack", "install"]
    out = capsys.readouterr().out
    fail = next(line for line in out.splitlines() if line.startswith("FAIL  zulu8: "))
    assert fail.startswith("FAIL  zulu8: choco install zulu8 8.96.0.205 failed (exit 1): ")
    tail = out[out.index("failed (exit 1): ") + len("failed (exit 1): "):]
    assert "exit code 1603." in tail and len(tail.rstrip("\n")) == 2000
    assert out.count("::endgroup::") == 2  # the failed install's group is closed too


def test_key_is_redacted_from_choco_output(env, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("CHOCO_KEY", "secret-key")
    env["fail"].add("push")
    env["output"] = {
        "install": ("echoing secret-key from an install script", ""),
        "push": ("Attempting to push with key secret-key", "401 for secret-key"),
    }
    assert run(env, "--id", "zulu8") == 1
    out = capsys.readouterr().out
    assert "secret-key" not in out
    assert "echoing *** from an install script" in out
    assert "Attempting to push with key ***" in out and "-k ***" in out
    assert "FAIL  zulu8: choco push zulu8 8.96.0.205 failed (exit 1): " in out and "401 for ***" in out


def test_redact_covers_key_argument_without_env(monkeypatch):
    monkeypatch.delenv("CHOCO_KEY", raising=False)
    assert cli._redact("key=abc123 ok", ["choco", "push", "x", "-k", "abc123"]) == "key=*** ok"
    assert cli._redact("nothing secret", ["choco", "pack", "x"]) == "nothing secret"


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
