"""Branch and PR decisions for the sync workflow (``chocotools syncpr plan``).

The workflow asks twice: before ``sync`` (which base to start ``bot/sync`` from)
and after it (commit / push / PR). Both answers come from the same remote
refs, so they agree.

Facts (``gather``), all from ``refs/remotes/origin/*``:

- ``exists``: ``origin/bot/sync`` exists.
- ``unmerged``: merging ``origin/bot/sync`` into ``origin/master`` would change
  master's tree (``git merge-tree --write-tree``). False when the branch was
  merged (merge commit, squash or rebase), is equal to, or is behind master.
- ``conflict``: that merge has conflicts.
- ``ancestor``: ``origin/bot/sync`` is an ancestor of ``origin/master``, so a
  branch rebuilt from master fast-forwards it.
- ``open_pr``: number of the open ``bot/sync`` -> ``master`` PR (from ``gh``).
- ``dirty``: ``git status --porcelain`` is non-empty after sync.

Base (``choose_base``):

- ``new``: no branch; start from ``origin/master``.
- ``reuse``: the branch carries updates master lacks; check it out and merge
  master into it.
- ``reset``: the branch is stale (nothing master lacks) or conflicts with
  master; start from ``origin/master``. Everything sync writes is regenerated
  from upstream, so dropping stale commits loses nothing.

After sync (``plan``):

- ``push = push``: a normal (fast-forward) push.
- ``push = replace``: the rebuilt branch does not descend from the remote one
  (squash/rebase-merged or conflicting). The workflow deletes the remote
  branch and pushes it again, which needs no force-push. Deleting the head
  branch closes an open PR, so the PR is created again.
- ``pr = create`` also covers a clean run whose branch still carries updates
  but has no open PR (closed unmerged): the PR is opened again.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

BRANCH = "bot/sync"
REMOTE_MASTER = "refs/remotes/origin/master"
REOPEN_NOTE = (
    "`bot/sync` still carries upstream updates from earlier sync runs that are not on `master`, "
    "and it had no open PR, so this PR was opened again. The table below is this run's sync report "
    "(packages already updated on the branch show as up-to-date)."
)


class SyncPrError(Exception):
    pass


@dataclass(frozen=True)
class State:
    exists: bool
    unmerged: bool = False
    conflict: bool = False
    ancestor: bool = False
    open_pr: int | None = None
    dirty: bool | None = None


@dataclass(frozen=True)
class Plan:
    base: str  # new | reuse | reset
    commit: bool = False
    push: str = "none"  # none | push | replace
    pr: str = "none"  # none | keep | edit | create
    reason: str = ""
    note: str = ""


def choose_base(state: State) -> tuple[str, str]:
    if not state.exists:
        return "new", f"no {BRANCH} branch"
    if state.conflict:
        return "reset", f"{BRANCH} conflicts with master; rebuilding it from master"
    if state.unmerged:
        return "reuse", f"{BRANCH} has updates that are not on master"
    return "reset", f"{BRANCH} has nothing master lacks (merged, equal or behind); rebuilding it from master"


def plan(state: State) -> Plan:
    base, reason = choose_base(state)
    if state.dirty is None:
        return Plan(base=base, reason=reason)
    if state.dirty:
        if base == "reset" and not state.ancestor:
            # Deleting the remote head branch closes any open PR.
            return Plan(base, True, "replace", "create", reason + "; replacing the remote branch")
        return Plan(base, True, "push", "edit" if state.open_pr else "create", reason)
    # Clean tree: sync changed nothing on top of the base.
    if base == "reuse":
        if state.open_pr:
            return Plan(base, False, "none", "keep", reason + f"; PR #{state.open_pr} is open")
        return Plan(base, False, "none", "create", reason + "; no open PR, opening it again", REOPEN_NOTE)
    return Plan(base, False, "none", "keep" if state.open_pr else "none", reason + "; no package changes")


# ----- facts from git ------------------------------------------------------------


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def gather(root: Path, open_pr: int | None, after_sync: bool, branch: str = BRANCH) -> State:
    """Read the facts from git. ``branch`` is only overridden by tests."""
    remote_branch = f"refs/remotes/origin/{branch}"
    if _git(root, "rev-parse", "--verify", "--quiet", REMOTE_MASTER).returncode != 0:
        raise SyncPrError(f"{REMOTE_MASTER} not found (fetch origin first)")
    dirty = None
    if after_sync:
        status = _git(root, "status", "--porcelain")
        if status.returncode != 0:
            raise SyncPrError(f"git status failed: {status.stderr.strip()}")
        dirty = bool(status.stdout.strip())
    if _git(root, "rev-parse", "--verify", "--quiet", remote_branch).returncode != 0:
        return State(exists=False, open_pr=open_pr, dirty=dirty)
    master_tree = _git(root, "rev-parse", f"{REMOTE_MASTER}^{{tree}}")
    merged = _git(root, "merge-tree", "--write-tree", REMOTE_MASTER, remote_branch)
    if master_tree.returncode != 0 or merged.returncode not in (0, 1):
        raise SyncPrError(f"git merge-tree failed: {merged.stderr.strip() or master_tree.stderr.strip()}")
    conflict = merged.returncode == 1
    merged_tree = merged.stdout.splitlines()[0].strip() if merged.stdout else ""
    unmerged = conflict or merged_tree != master_tree.stdout.strip()
    ancestor = _git(root, "merge-base", "--is-ancestor", remote_branch, REMOTE_MASTER).returncode == 0
    return State(True, unmerged, conflict, ancestor, open_pr, dirty)


def write_body(report: Path | None, body: Path, note: str) -> None:
    parts = [note] if note else []
    if report and report.is_file():
        parts.append(report.read_text(encoding="utf-8").rstrip("\n"))
    else:
        parts.append("(sync report missing)")
    body.parent.mkdir(parents=True, exist_ok=True)
    body.write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def outputs(p: Plan, after_sync: bool) -> dict[str, str]:
    values = {"base": p.base, "reason": p.reason}
    if after_sync:
        values.update(commit=str(p.commit).lower(), push=p.push, pr=p.pr)
    return values
