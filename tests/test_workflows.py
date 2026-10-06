"""Structural checks on the workflow files that actionlint cannot express."""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"


def jobs(path: Path) -> dict[str, str]:
    """Job id -> the job's text block (2-space-indented keys under ``jobs:``)."""
    text = path.read_text(encoding="utf-8")
    body = text.split("\njobs:\n", 1)[1]
    blocks: dict[str, str] = {}
    current = None
    for line in body.splitlines():
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if m:
            current = m.group(1)
            blocks[current] = ""
        elif current:
            blocks[current] += line + "\n"
    return blocks


def test_publish_real_push_is_gated_by_chocolatey_environment():
    blocks = jobs(WORKFLOWS / "publish.yaml")
    assert set(blocks) == {"check", "publish"}
    publish = blocks["publish"]
    assert re.search(r"^    environment: chocolatey$", publish, re.M)
    assert "chocotools publish --changed" in publish
    # Every non-dry-run publish command lives in the gated job.
    for job, block in blocks.items():
        for cmd in re.findall(r"chocotools publish[^\n]*", block):
            if "--dry-run" not in cmd:
                assert job == "publish", f"{job} runs a real publish outside the environment: {cmd}"


def test_publish_waits_for_the_ungated_check_job():
    """The reviewer approves after validate/pack/test-install have run."""
    publish = jobs(WORKFLOWS / "publish.yaml")["publish"]
    assert re.search(r"^    needs: check$", publish, re.M)
    assert "!inputs.dry_run" in publish


def test_publish_check_job_has_no_key_and_no_environment():
    check = jobs(WORKFLOWS / "publish.yaml")["check"]
    assert "CHOCO_KEY" not in check
    assert "environment:" not in check
    assert re.findall(r"chocotools publish[^\n]*", check) == [
        'chocotools publish --changed "$env:BEFORE..$env:SHA" --dry-run',
        'chocotools publish --id "$env:IDS" --dry-run',
    ]


def test_publish_has_no_concurrency_group():
    """A shared group would cancel pending runs while one waits for approval."""
    assert "concurrency:" not in (WORKFLOWS / "publish.yaml").read_text(encoding="utf-8")
