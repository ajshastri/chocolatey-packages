import os
import subprocess
import sys
import time
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
    # "hang": choco subcommands that run past their timeout (TimeoutExpired with the output so far)
    # "pushes": per-call choco push results (exit code, stdout) consumed in order; "hang" times that call out
    state = {"cmds": [], "status": "", "approved": "8.90.0.1", "fail": set(), "output": {}, "hang": set(),
             "timeouts": {}, "pushes": []}

    def fake_run(cmd, *, cwd=None, timeout=None):
        state["cmds"].append(list(cmd))
        if cmd[:2] == ["choco", "push"] and state["pushes"]:
            code, stdout = state["pushes"].pop(0)
            if code == "hang":
                raise subprocess.TimeoutExpired(cmd, timeout, output=stdout, stderr="")
            return subprocess.CompletedProcess(cmd, code, stdout, "")
        if cmd[0] == "choco":
            state["timeouts"][cmd[1]] = timeout
            if cmd[1] in state["hang"]:
                stdout, stderr = state["output"].get(cmd[1], ("", ""))
                raise subprocess.TimeoutExpired(cmd, timeout, output=stdout, stderr=stderr)
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
    monkeypatch.delenv("CHOCOTOOLS_FEED_RETRY_BUDGET", raising=False)
    state["root"] = tmp_path
    client = FakeClient(head={ZULU_URL: {"status": 200, "headers": {}}}, use_index=False)
    # push retries take their backoff from the client: record waits instead of sleeping
    state["sleeps"] = []
    clock = {"t": 0.0}
    client.clock = lambda: clock["t"]
    client.sleep = lambda s: (state["sleeps"].append(s), clock.__setitem__("t", clock["t"] + s))
    client.uniform = lambda low, high: high
    client.feed_budget = None
    state["client"] = client
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


def guarded_block(lines: list[str], title: str) -> list[str]:
    """The lines between ``::stop-commands::<token>`` and ``::<token>::`` in the group ``title``."""
    i = lines.index(f"::group::{title}")
    assert lines[i + 2].startswith("::stop-commands::")
    token = lines[i + 2].removeprefix("::stop-commands::")
    end = lines.index(f"::{token}::", i)
    assert lines[end + 1] == "::endgroup::"
    return lines[i + 3:end]


def test_failed_install_output_is_printed_once_inside_the_guard(env, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    env["fail"].add("install")
    log = "x" * 3000 + "\n::error::injected by an install script\nERROR: Running msiexec failed with exit code 1603."
    env["output"] = {"install": (log, "")}
    assert run(env, "--id", "zulu8", "--dry-run") == 1
    assert choco_cmds(env) == ["pack", "install"]
    out = capsys.readouterr().out
    lines = out.splitlines()
    # choco's output appears once, all of it inside the stop-commands block of the install group
    assert guarded_block(lines, "choco install zulu8 8.96.0.205") == log.splitlines()
    assert out.count("::error::injected by an install script") == 1
    assert out.count("exit code 1603.") == 1 and out.count("x" * 3000) == 1
    # the FAIL line is one short line after the group: id, step, exit code
    assert [line for line in lines if line.startswith("FAIL")] == [
        "FAIL  zulu8: choco install zulu8 8.96.0.205 failed (exit 1)"]
    assert lines.index("FAIL  zulu8: choco install zulu8 8.96.0.205 failed (exit 1)") > lines.index("::endgroup::")
    assert out.count("::endgroup::") == 2  # the failed install's group is closed too


def test_successful_output_with_workflow_command_stays_inside_the_guard(env, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    env["output"] = {"install": ("::set-output name=x::y\nThe install of zulu8 was successful.", "")}
    assert run(env, "--id", "zulu8", "--dry-run") == 0
    out = capsys.readouterr().out
    assert guarded_block(out.splitlines(), "choco install zulu8 8.96.0.205") == [
        "::set-output name=x::y", "The install of zulu8 was successful."]
    assert out.count("::set-output name=x::y") == 1


def test_choco_timeouts_per_subcommand(env, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("CHOCO_KEY", "k")
    assert run(env, "--id", "zulu8") == 0
    assert env["timeouts"] == {"pack": 600, "install": 1800, "uninstall": 900, "push": 600}
    assert env["timeouts"] == cli.CHOCO_TIMEOUTS


def test_install_timeout_fails_package_with_partial_output(env, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("CHOCO_KEY", "secret-key")
    env["hang"].add("install")
    # TimeoutExpired carries bytes on POSIX even with text=True; both forms are handled
    env["output"] = {"install": ("Installing zulu8 8.96.0.205\nkey secret-key", b"msiexec still running")}
    assert run(env, "--id", "zulu8") == 1
    assert choco_cmds(env) == ["pack", "install"]  # no uninstall, no push
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert guarded_block(lines, "choco install zulu8 8.96.0.205") == [
        "Installing zulu8 8.96.0.205", "key ***", "msiexec still running"]
    assert "secret-key" not in out
    assert [line for line in lines if line.startswith("FAIL")] == [
        "FAIL  zulu8: choco install zulu8 8.96.0.205 timed out after 30 min and was stopped "
        "(its output so far is above)"]


def test_pack_timeout_fails_the_package_outside_ci(env, capsys):
    env["hang"].add("pack")
    assert run(env, "--id", "zulu8", "--dry-run") == 1
    out = capsys.readouterr().out
    # pack printed nothing before it hung, so the FAIL line does not point at output above
    assert "FAIL  zulu8: choco pack zulu8 8.96.0.205 timed out after 10 min and was stopped\n" in out
    assert "output so far" not in out
    assert "::group::" not in out  # plain output outside CI


# _kill_tree uses taskkill /T on Windows; elsewhere it only kills the direct child,
# so the grandchild here would hold the pipes for its full 60 s. Publish runs on Windows.
@pytest.mark.skipif(os.name != "nt", reason="tree kill via taskkill is Windows-only")
def test_run_kills_a_hung_process_and_keeps_its_output():
    # Like choco starting msiexec: a grandchild inherits the pipes and outlives a plain kill.
    script = ("import subprocess, sys, time; "
              "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], stdout=sys.stdout, "
              "stderr=sys.stderr); print('partial line', flush=True); time.sleep(60)")
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired) as info:
        cli._run([sys.executable, "-c", script], timeout=2)
    assert time.monotonic() - started < 30
    assert "partial line" in cli._text(info.value.stdout)


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
    assert "FAIL  zulu8: choco push zulu8 8.96.0.205 failed (exit 1)\n" in out and "401 for ***" in out


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


# ----- choco push retries ------------------------------------------------------

UNAVAILABLE = "Attempting to push zulu8.8.96.0.205.nupkg to https://push.chocolatey.org/\n" \
              "Response status code does not indicate success: 503 (Service Unavailable)."
CONFLICT = "Response status code does not indicate success: 409 (Conflict)."


def feed_with(version, approved="false"):
    return (f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:m="m" xmlns:d="d"><entry><content><m:properties>'
            f'<d:Version>{version}</d:Version><d:IsApproved>{approved}</d:IsApproved>'
            f'</m:properties></content></entry></feed>').encode()


def push_env(env, monkeypatch, *pushes):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("CHOCO_KEY", "secret-key")
    env["pushes"] = list(pushes)


def test_push_retries_on_503_then_succeeds(env, monkeypatch, capsys):
    push_env(env, monkeypatch, (1, UNAVAILABLE), (1, "connection was closed"), (0, "pushed ok"))
    assert run(env, "--id", "zulu8") == 0
    assert choco_cmds(env) == ["pack", "install", "uninstall", "push", "push", "push"]
    assert env["sleeps"] == [5.0, 10.0]
    captured = capsys.readouterr()
    assert captured.err.splitlines() == [
        "retry 1 for push.chocolatey.org: choco push zulu8 8.96.0.205 failed (exit 1), output mentions '503'; "
        "waiting 5.0s (budget left 900s)",
        "retry 2 for push.chocolatey.org: choco push zulu8 8.96.0.205 (retry 1) failed (exit 1), output mentions "
        "'connection was closed'; waiting 10.0s (budget left 895s)",
    ]
    assert "::group::choco push zulu8 8.96.0.205 (retry 2)" in captured.out
    assert "pushed zulu8 8.96.0.205\n" in captured.out
    assert "secret-key" not in captured.out + captured.err


def test_push_timeout_is_retried(env, monkeypatch, capsys):
    push_env(env, monkeypatch, ("hang", "Uploading..."), (0, "pushed ok"))
    assert run(env, "--id", "zulu8") == 0
    assert choco_cmds(env).count("push") == 2
    assert "retry 1 for push.chocolatey.org: choco push zulu8 8.96.0.205 timed out after 10 min" in capsys.readouterr().err


def test_push_retry_conflict_confirmed_on_the_feed_is_success(env, monkeypatch, capsys):
    env["client"].get_map[chocolatey.feed_url("zulu8")] = feed_with("8.96.0.205")
    push_env(env, monkeypatch, (1, UNAVAILABLE), (1, CONFLICT))
    assert run(env, "--id", "zulu8") == 0
    out = capsys.readouterr().out
    assert ("pushed zulu8 8.96.0.205 (retry 1 got a conflict; Chocolatey lists the version, so an earlier attempt "
            "went through)") in out
    assert "FAIL" not in out


def test_push_retry_conflict_confirmed_by_package_page(env, monkeypatch):
    env["client"].get_map[chocolatey.feed_url("zulu8")] = feed_with("8.90.0.1", "true")
    env["client"].head_map[chocolatey.package_page("zulu8", "8.96.0.205")] = {"status": 200, "headers": {}}
    push_env(env, monkeypatch, (1, UNAVAILABLE), (1, "The package version already exists on the feed."))
    assert run(env, "--id", "zulu8") == 0


def test_push_retry_conflict_not_on_the_feed_fails(env, monkeypatch, capsys):
    env["client"].get_map[chocolatey.feed_url("zulu8")] = feed_with("8.90.0.1", "true")
    push_env(env, monkeypatch, (1, UNAVAILABLE), (1, CONFLICT))
    assert run(env, "--id", "zulu8") == 1
    assert ("FAIL  zulu8: choco push zulu8 8.96.0.205 (retry 1) failed (exit 1): Chocolatey reports a conflict but "
            "does not list zulu8 8.96.0.205") in capsys.readouterr().out


def test_push_conflict_on_the_first_attempt_is_not_retried(env, monkeypatch, capsys):
    env["client"].get_map[chocolatey.feed_url("zulu8")] = feed_with("8.96.0.205")
    push_env(env, monkeypatch, (1, CONFLICT))
    assert run(env, "--id", "zulu8") == 1
    assert choco_cmds(env).count("push") == 1 and env["sleeps"] == []
    assert "FAIL  zulu8: choco push zulu8 8.96.0.205 failed (exit 1)" in capsys.readouterr().out


def test_push_non_transient_failure_is_not_retried(env, monkeypatch, capsys):
    push_env(env, monkeypatch, (1, "Response status code does not indicate success: 401 (Unauthorized)."))
    assert run(env, "--id", "zulu8") == 1
    assert choco_cmds(env).count("push") == 1 and env["sleeps"] == []
    assert capsys.readouterr().err == ""


def test_push_gives_up_when_the_budget_is_spent(env, monkeypatch, capsys):
    env["client"].feed_budget = 12
    push_env(env, monkeypatch, *[(1, UNAVAILABLE)] * 10)
    assert run(env, "--id", "zulu8") == 1
    assert env["sleeps"] == [5.0, 7.0]  # 5, then the 7 s left of the 12 s budget
    assert choco_cmds(env).count("push") == 3
    assert ("FAIL  zulu8: choco push zulu8 8.96.0.205 (retry 2) failed (exit 1); gave up after 12s of push retries"
            in capsys.readouterr().out)


def test_push_retry_logs_redact_the_key(env, monkeypatch, capsys):
    push_env(env, monkeypatch, (1, "503 from proxy for key secret-key"), (0, "ok"))
    assert run(env, "--id", "zulu8") == 0
    captured = capsys.readouterr()
    assert "secret-key" not in captured.out + captured.err
    assert "503 from proxy for key ***" in captured.out and "retry 1 for push.chocolatey.org" in captured.err


def test_push_retry_line_redacts_a_key_in_the_reason(monkeypatch):
    # The reason is choco's step line plus the matched text; redaction covers both CHOCO_KEY and -k.
    monkeypatch.delenv("CHOCO_KEY", raising=False)
    assert cli._redact("retry 1 for push.chocolatey.org: k-abc503; waiting 5.0s", ["choco", "push", "x", "-k", "k-abc503"]) \
        == "retry 1 for push.chocolatey.org: ***; waiting 5.0s"