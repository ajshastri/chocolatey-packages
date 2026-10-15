"""Pending upstream releases end to end: real Corretto source, recorded fixtures, no network.

Live state on 2026-10-14: GitHub tagged 21.0.12.13.1 (2026-10-13) while
corretto.aws latest still served 21.0.12.12.1 and the tag's MSI answered 403.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from chocotools import chocolatey, cli, sources
from conftest import FakeClient, copy_pkg

MANIFEST = """
[[package]]
id = "corretto21jdk"
folder = "corretto-jdk-21"
vendor = "corretto"
major = 21
image = "jdk"
arch = ["x64"]

[[package]]
id = "zulu8"
folder = "zulu-8"
vendor = "zulu"
major = 8
image = "jdk"
arch = ["x64"]
"""
GITHUB21 = "https://api.github.com/repos/corretto/corretto-21/releases/latest"
LATEST21 = "https://corretto.aws/downloads/latest/amazon-corretto-21-x64-windows-jdk.msi"
SHA21 = "https://corretto.aws/downloads/latest_sha256/amazon-corretto-21-x64-windows-jdk.msi"
MSI21 = "https://corretto.aws/downloads/resources/{0}/amazon-corretto-{0}-windows-x64.msi"
PUBLISHED = datetime(2026, 10, 13, 18, 2, 11, tzinfo=timezone.utc)
PENDING_MSG = ("GitHub 21.0.12.13.1 released 2026-10-13, corretto.aws latest still serves 21.0.12.12.1 "
               "(versioned MSI HTTP 403)")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "packages.toml").write_text(MANIFEST, encoding="utf-8")
    copy_pkg("corretto-jdk-21", tmp_path)
    copy_pkg("zulu-8", tmp_path)
    client = FakeClient()
    state = {"root": tmp_path, "client": client, "now": PUBLISHED + timedelta(days=1), "fail": set()}
    set_github(client, "21.0.12.13.1")
    real_fetch = sources.fetch

    def fetch(pkg, *, version=None, client=None):
        if pkg.id in state["fail"]:
            raise sources.SourceError("upstream returned nothing")
        return real_fetch(pkg, version=version, client=client)

    monkeypatch.setattr(sources, "fetch", fetch)
    monkeypatch.setattr(sources, "utcnow", lambda: state["now"])
    monkeypatch.setattr(chocolatey, "approved_version", lambda pid, client=None: "21.0.12.121")
    return state


def set_github(client, tag):
    client.get_map[GITHUB21] = json.dumps({"tag_name": tag, "draft": False, "prerelease": False,
                                           "published_at": "2026-10-13T18:02:11Z", "assets": []}).encode()
    client.head_map[MSI21.format(tag)] = {"status": 403, "headers": {}}


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def run(repo, *args):
    return cli.main(["--root", str(repo["root"]), *args], client=repo["client"])


def test_pending_writes_nothing_and_exits_0(repo, capsys):
    before = snapshot(repo["root"])
    assert run(repo, "sync", "--id", "corretto21jdk") == 0
    assert snapshot(repo["root"]) == before
    out = capsys.readouterr().out
    assert f"| corretto21jdk | 21.0.12.121 | 21.0.12.121 | pending |" in out
    assert "0 changed, 1 pending, 0 failed, 1 checked." in out
    assert f"### Pending\n\n- pending corretto21jdk: {PENDING_MSG}\n" in out
    assert "### Failures" not in out


def test_pending_report_file_for_the_pr_body(repo, tmp_path):
    report = tmp_path / "out" / "sync-report.md"
    assert run(repo, "sync", "--report", str(report), "--id", "corretto21jdk") == 0
    assert f"- pending corretto21jdk: {PENDING_MSG}" in report.read_text(encoding="utf-8")


def test_pending_and_a_failure_exit_1(repo, capsys):
    repo["fail"].add("zulu8")
    assert run(repo, "sync") == 1
    out = capsys.readouterr().out
    assert "0 changed, 1 pending, 1 failed, 2 checked." in out
    assert "### Failures\n\n- zulu8: source: upstream returned nothing" in out
    assert f"- pending corretto21jdk: {PENDING_MSG}" in out


def test_latest_link_newer_than_repo_syncs_to_it(repo, capsys):
    # GitHub is at 21.0.13.5.1, corretto.aws latest moved to 21.0.12.13.1: sync to what is served.
    client = repo["client"]
    set_github(client, "21.0.13.5.1")
    client.head_map[LATEST21] = {"status": 302, "headers": {"location": MSI21.format("21.0.12.13.1")}}
    client.get_map[SHA21] = b"a" * 64 + b"\n"
    assert run(repo, "sync", "--id", "corretto21jdk") == 0
    root = repo["root"]
    assert b"<version>21.0.12.131</version>" in (root / "corretto-jdk-21/corretto21jdk.nuspec").read_bytes()
    script = (root / "corretto-jdk-21/tools/chocolateyinstall.ps1").read_bytes()
    assert MSI21.format("21.0.12.13.1").encode() in script and b"a" * 64 in script
    out = capsys.readouterr().out
    assert "| corretto21jdk | 21.0.12.121 | 21.0.12.131 | updated |" in out
    assert "newer release pending: GitHub 21.0.13.5.1 released 2026-10-13" in out
    assert "1 changed, 0 pending, 0 failed, 1 checked." in out


def test_github_behind_latest_link_syncs_with_a_note(repo, capsys):
    # GitHub still at 21.0.12.12.1, corretto.aws latest moved to 21.0.12.13.1: corretto.aws decides.
    client = repo["client"]
    set_github(client, "21.0.12.12.1")
    client.head_map[LATEST21] = {"status": 302, "headers": {"location": MSI21.format("21.0.12.13.1")}}
    client.get_map[SHA21] = b"a" * 64 + b"\n"
    assert run(repo, "sync", "--id", "corretto21jdk") == 0
    nuspec = (repo["root"] / "corretto-jdk-21/corretto21jdk.nuspec").read_bytes()
    assert b"<version>21.0.12.131</version>" in nuspec
    out = capsys.readouterr().out
    assert "| corretto21jdk | 21.0.12.121 | 21.0.12.131 | updated |" in out
    assert "GitHub latest tag 21.0.12.12.1 is behind corretto.aws latest 21.0.12.13.1" in out
    assert "1 changed, 0 pending, 0 failed, 1 checked." in out


@pytest.mark.parametrize("days, code, status", [(89, 0, "pending"), (91, 1, "failed")])
def test_pending_escalates_after_90_days(repo, capsys, days, code, status):
    repo["now"] = PUBLISHED + timedelta(days=days)
    before = snapshot(repo["root"])
    assert run(repo, "sync", "--id", "corretto21jdk") == code
    assert snapshot(repo["root"]) == before
    out = capsys.readouterr().out
    assert f"| corretto21jdk | 21.0.12.121 | 21.0.12.121 | {status} |" in out
    if status == "failed":
        assert (f"- corretto21jdk: {PENDING_MSG}; still not served after more than "
                f"{sources.PENDING_ESCALATION_DAYS} days") in out
        assert "0 changed, 0 pending, 1 failed, 1 checked." in out


def test_escalation_constant():
    assert sources.PENDING_ESCALATION_DAYS == 90


def test_latest_link_older_than_repo_fails(repo, capsys):
    nuspec = repo["root"] / "corretto-jdk-21/corretto21jdk.nuspec"
    nuspec.write_bytes(nuspec.read_bytes().replace(b"<version>21.0.12.121</version>", b"<version>21.0.12.131</version>"))
    before = snapshot(repo["root"])
    assert run(repo, "sync", "--id", "corretto21jdk") == 1
    assert snapshot(repo["root"]) == before
    assert "upstream 21.0.12.121 is lower than repo 21.0.12.131" in capsys.readouterr().out


def test_compare_shows_pending_upstream(repo, tmp_path):
    repo["fail"].add("zulu8")  # keep the zulu row out of the way; compare still lists it
    out_json = tmp_path / "compare.json"
    run(repo, "compare", "--format", "json", "--output", str(out_json))
    rows = {r["id"]: r for r in json.loads(out_json.read_text(encoding="utf-8"))}
    assert rows["corretto21jdk"]["status"] == "pending upstream"
    assert rows["corretto21jdk"]["source"] == "21.0.12.121"
    assert rows["corretto21jdk"]["note"] == PENDING_MSG
    out_md = tmp_path / "compare.md"
    run(repo, "compare", "--output", str(out_md))
    assert "| 21.0.12.12.1 -> 21.0.12.121 | pending upstream |" in out_md.read_text(encoding="utf-8")


def test_compare_pending_only_exits_0(repo, tmp_path):
    manifest = repo["root"] / "packages.toml"
    manifest.write_text(MANIFEST.split("\n[[package]]\nid = \"zulu8\"")[0], encoding="utf-8")
    assert run(repo, "compare", "--output", str(tmp_path / "c.md")) == 0
