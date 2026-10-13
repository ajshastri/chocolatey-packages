"""bot/sync branch and PR decisions (``chocotools syncpr plan``)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from chocotools import cli, syncpr
from chocotools.syncpr import Plan, State

# ----- pure decisions ------------------------------------------------------------


def test_no_branch():
    assert syncpr.plan(State(exists=False)).base == "new"
    assert syncpr.plan(State(exists=False, dirty=False)) == Plan("new", False, "none", "none", "no bot/sync branch; no package changes")
    p = syncpr.plan(State(exists=False, dirty=True))
    assert (p.base, p.commit, p.push, p.pr) == ("new", True, "push", "create")


def test_branch_ahead_with_open_pr_is_left_alone():
    s = State(exists=True, unmerged=True, open_pr=12, dirty=False)
    p = syncpr.plan(s)
    assert (p.base, p.commit, p.push, p.pr) == ("reuse", False, "none", "keep")


def test_branch_ahead_with_open_pr_and_new_changes_edits_pr():
    p = syncpr.plan(State(exists=True, unmerged=True, open_pr=12, dirty=True))
    assert (p.base, p.commit, p.push, p.pr) == ("reuse", True, "push", "edit")


def test_branch_ahead_without_pr_reopens_it():
    """Closed unmerged: the branch still carries updates, so open the PR again."""
    p = syncpr.plan(State(exists=True, unmerged=True, open_pr=None, dirty=False))
    assert (p.base, p.commit, p.push, p.pr) == ("reuse", False, "none", "create")
    assert p.note == syncpr.REOPEN_NOTE
    p = syncpr.plan(State(exists=True, unmerged=True, open_pr=None, dirty=True))
    assert (p.base, p.commit, p.push, p.pr) == ("reuse", True, "push", "create")
    assert p.note == ""


@pytest.mark.parametrize("ancestor", [True, False])
def test_branch_merged_or_equal_is_rebuilt_from_master(ancestor):
    clean = syncpr.plan(State(exists=True, unmerged=False, ancestor=ancestor, dirty=False))
    assert (clean.base, clean.commit, clean.push, clean.pr) == ("reset", False, "none", "none")
    dirty = syncpr.plan(State(exists=True, unmerged=False, ancestor=ancestor, dirty=True))
    # Merge-commit merges (ancestor) fast-forward; squash/rebase merges need the branch replaced.
    expected_push = "push" if ancestor else "replace"
    assert (dirty.base, dirty.commit, dirty.push, dirty.pr) == ("reset", True, expected_push, "create")


def test_stale_branch_with_open_pr_and_new_changes():
    p = syncpr.plan(State(exists=True, unmerged=False, ancestor=True, open_pr=7, dirty=True))
    assert (p.push, p.pr) == ("push", "edit")
    p = syncpr.plan(State(exists=True, unmerged=False, ancestor=False, open_pr=7, dirty=True))
    assert (p.push, p.pr) == ("replace", "create")  # deleting the head branch closes the PR


def test_conflicting_branch_is_rebuilt():
    p = syncpr.plan(State(exists=True, unmerged=True, conflict=True, ancestor=False, dirty=True))
    assert (p.base, p.commit, p.push, p.pr) == ("reset", True, "replace", "create")


def test_conflicting_branch_with_open_pr_and_no_changes_closes_the_pr():
    """master is already current, so the conflicting PR is stale: close it, not keep it."""
    p = syncpr.plan(State(exists=True, unmerged=True, conflict=True, ancestor=False, open_pr=9, dirty=False))
    assert (p.base, p.commit, p.push, p.pr) == ("reset", False, "none", "close")
    assert p.note == syncpr.CLOSE_NOTE
    assert "closing stale PR #9" in p.reason


@pytest.mark.parametrize("ancestor", [True, False])
def test_merged_branch_with_open_pr_and_no_changes_closes_the_pr(ancestor):
    p = syncpr.plan(State(exists=True, unmerged=False, ancestor=ancestor, open_pr=4, dirty=False))
    assert (p.base, p.commit, p.push, p.pr) == ("reset", False, "none", "close")


def test_close_is_only_for_a_clean_reset_with_an_open_pr():
    states = [
        State(exists=False, open_pr=None, dirty=False),
        State(exists=True, unmerged=True, open_pr=3, dirty=False),  # reuse: keep
        State(exists=True, unmerged=True, open_pr=None, dirty=False),  # reuse: reopen
        State(exists=True, unmerged=True, conflict=True, open_pr=None, dirty=False),  # nothing to close
        State(exists=True, unmerged=True, conflict=True, open_pr=3, dirty=True),  # replace + create
    ]
    assert [syncpr.plan(s).pr for s in states] == ["none", "keep", "create", "none", "create"]


def test_dirty_tree_always_commits():
    for state in (
        State(exists=False, dirty=True),
        State(exists=True, unmerged=True, dirty=True),
        State(exists=True, unmerged=True, open_pr=3, dirty=True),
        State(exists=True, unmerged=False, ancestor=True, dirty=True),
        State(exists=True, unmerged=False, ancestor=False, dirty=True),
    ):
        p = syncpr.plan(state)
        assert p.commit and p.push in ("push", "replace") and p.pr in ("edit", "create"), state


# ----- facts from real git repositories ------------------------------------------------


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false",
         "-c", "core.autocrlf=false", *args],
        cwd=cwd, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


MINI_MANIFEST = '[[package]]\nid = "wildfly"\nfolder = "WildFly"\nvendor = "wildfly"\narch = ["neutral"]\n'


def bump(work: Path, branch: str, name: str, value: str) -> None:
    """Commit ``name = value`` on ``branch`` (started from origin/master) and push it."""
    git(work, "checkout", "-B", branch, "origin/master")
    (work / name).write_text(value + "\n", encoding="utf-8")
    git(work, "commit", "-qam", f"{name}={value}")
    git(work, "push", "-q", "origin", branch)
    git(work, "fetch", "-q", "origin")
    git(work, "checkout", "-q", "-B", "master", "origin/master")


@pytest.fixture(scope="module")
def clone(tmp_path_factory):
    """One clone whose origin holds every branch shape (git is slow to start on Windows).

    bot/sync      ahead of master (unmerged update, PR closed or open)
    bot/merged    merged into master with a merge commit
    bot/squashed  squash-merged into master
    bot/equal     same commit as master
    bot/conflict  edits a line master changed afterwards
    """
    tmp = tmp_path_factory.mktemp("syncpr")
    remote, work = tmp / "remote.git", tmp / "work"
    git(tmp, "init", "-q", "--bare", "-b", "master", str(remote))
    git(tmp, "init", "-q", "-b", "master", str(work))
    git(work, "remote", "add", "origin", str(remote))
    (work / "packages.toml").write_text(MINI_MANIFEST, encoding="utf-8")
    for name in "abcd":
        (work / f"{name}.nuspec").write_text("1\n", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-qm", "base")
    git(work, "push", "-q", "origin", "master")
    git(work, "fetch", "-q", "origin")
    bump(work, "bot/sync", "a.nuspec", "2")
    bump(work, "bot/merged", "b.nuspec", "2")
    bump(work, "bot/squashed", "c.nuspec", "2")
    bump(work, "bot/conflict", "d.nuspec", "2")
    git(work, "merge", "-q", "--no-ff", "--no-edit", "origin/bot/merged")
    git(work, "merge", "-q", "--squash", "origin/bot/squashed")
    git(work, "commit", "-qm", "squash")
    (work / "d.nuspec").write_text("9\n", encoding="utf-8")
    git(work, "commit", "-qam", "d=9")
    git(work, "push", "-q", "origin", "master", "master:bot/equal")
    git(work, "fetch", "-q", "origin")
    return work


def test_gather_no_branch(clone):
    assert syncpr.gather(clone, None, after_sync=False, branch="bot/none") == State(exists=False)


def test_gather_branch_ahead(clone):
    s = syncpr.gather(clone, 5, after_sync=True)
    assert s == State(exists=True, unmerged=True, conflict=False, ancestor=False, open_pr=5, dirty=False)
    assert syncpr.plan(s).pr == "keep"  # open PR: leave it
    assert syncpr.plan(syncpr.gather(clone, None, after_sync=True)).pr == "create"  # closed unmerged: reopen


def test_gather_branch_merged_with_merge_commit(clone):
    s = syncpr.gather(clone, None, after_sync=False, branch="bot/merged")
    assert (s.exists, s.unmerged, s.conflict, s.ancestor) == (True, False, False, True)
    assert syncpr.plan(s).base == "reset"


def test_gather_branch_squash_merged(clone):
    s = syncpr.gather(clone, None, after_sync=False, branch="bot/squashed")
    assert (s.exists, s.unmerged, s.conflict, s.ancestor) == (True, False, False, False)
    p = syncpr.plan(State(s.exists, s.unmerged, s.conflict, s.ancestor, None, dirty=True))
    assert (p.base, p.commit, p.push, p.pr) == ("reset", True, "replace", "create")


def test_gather_branch_equal_to_master(clone):
    s = syncpr.gather(clone, None, after_sync=False, branch="bot/equal")
    assert (s.exists, s.unmerged, s.conflict, s.ancestor) == (True, False, False, True)
    assert syncpr.plan(s).base == "reset"


def test_gather_branch_conflicts_with_master(clone):
    s = syncpr.gather(clone, None, after_sync=False, branch="bot/conflict")
    assert (s.exists, s.unmerged, s.conflict, s.ancestor) == (True, True, True, False)
    assert syncpr.plan(s).base == "reset"
    # After sync on the rebuilt branch: clean tree, PR still open -> close it.
    s = syncpr.gather(clone, 8, after_sync=True, branch="bot/conflict")
    assert syncpr.plan(s).pr == "close"


def test_gather_dirty_tree(clone):
    target = clone / "a.nuspec"
    original = target.read_bytes()
    try:
        target.write_text("5\n", encoding="utf-8")
        s = syncpr.gather(clone, None, after_sync=True, branch="bot/none")
    finally:
        target.write_bytes(original)
    assert s.dirty is True
    p = syncpr.plan(s)
    assert (p.base, p.commit, p.push, p.pr) == ("new", True, "push", "create")


def test_cli_writes_github_output_and_body(clone, tmp_path, capsys):
    report = tmp_path / "sync-report.md"
    report.write_text("## chocotools sync\n\n0 changed, 0 failed, 1 checked.\n", encoding="utf-8")
    gh_out = tmp_path / "gh_output"
    body = tmp_path / "pr-body.md"
    code = cli.main(["--root", str(clone), "syncpr", "plan", "--after-sync", "--open-pr", "",
                     "--report", str(report), "--body", str(body), "--github-output", str(gh_out)])
    assert code == 0
    pairs = dict(line.split("=", 1) for line in gh_out.read_text(encoding="utf-8").splitlines())
    assert {k: v for k, v in pairs.items() if k != "reason"} == {
        "base": "reuse", "commit": "false", "push": "none", "pr": "create"}
    text = body.read_text(encoding="utf-8")
    assert text.startswith(syncpr.REOPEN_NOTE) and "0 changed, 0 failed, 1 checked." in text
    assert "pr=create" in capsys.readouterr().out


def test_cli_close_writes_the_close_note(clone, tmp_path, monkeypatch):
    real_gather = syncpr.gather
    monkeypatch.setattr(syncpr, "gather", lambda root, open_pr, after_sync: real_gather(
        root, open_pr, after_sync, branch="bot/conflict"))
    report = tmp_path / "sync-report.md"
    report.write_text("0 changed, 0 failed, 1 checked.\n", encoding="utf-8")
    body = tmp_path / "pr-body.md"
    gh_out = tmp_path / "gh_output"
    code = cli.main(["--root", str(clone), "syncpr", "plan", "--after-sync", "--open-pr", "8",
                     "--report", str(report), "--body", str(body), "--github-output", str(gh_out)])
    assert code == 0
    assert "pr=close" in gh_out.read_text(encoding="utf-8").splitlines()
    assert body.read_text(encoding="utf-8").startswith(syncpr.CLOSE_NOTE)


def test_cli_rejects_bad_pr_number(clone):
    assert cli.main(["--root", str(clone), "syncpr", "plan", "--open-pr", "abc"]) == cli.EXIT_USAGE
