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
    assert set(blocks) == {"dry-run", "publish"}
    publish = blocks["publish"]
    assert re.search(r"^    environment: chocolatey$", publish, re.M)
    assert "chocotools publish --changed" in publish
    # Every non-dry-run publish command lives in the gated job.
    for job, block in blocks.items():
        for cmd in re.findall(r"chocotools publish[^\n]*", block):
            if "--dry-run" not in cmd:
                assert job == "publish", f"{job} runs a real publish outside the environment: {cmd}"


def test_publish_dry_run_job_has_no_key_and_no_environment():
    dry = jobs(WORKFLOWS / "publish.yaml")["dry-run"]
    assert "CHOCO_KEY" not in dry
    assert "environment:" not in dry
    assert "inputs.dry_run" in dry
    assert re.findall(r"chocotools publish[^\n]*", dry) == [
        'chocotools publish --id "$env:IDS" --dry-run'
    ]
