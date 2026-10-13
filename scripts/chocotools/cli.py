"""Command-line interface: ``python -m chocotools <command>``.

Commands:
  sync     [--vendor V] [--id ID ...] [--dry-run] [--report PATH]
  validate [--id ID ...] [--online]
  build    [--id ID ... | --changed BASE..HEAD] [--out DIR]
  publish  [--id ID ... | --changed BASE..HEAD] [--dry-run]
  compare  [--format md|json] [--output PATH]
  syncpr plan [--open-pr N] [--after-sync] [--report PATH --body PATH] [--github-output PATH]

``--id`` is repeatable and comma-splittable. Exit codes: 0 ok, 1 package
failures, 2 usage/manifest error, 3 missing prerequisite (no choco / not Windows
/ no CHOCO_KEY).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import secrets
import shutil
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__, checks, chocolatey, installscript, manifest, nuspec, sources, syncpr, versioning
from .http import Client, HttpError, default_client
from .manifest import Manifest, ManifestError, Package

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_PREREQ = 3

INSTALL_SCRIPT = "tools/chocolateyinstall.ps1"
PUSH_SOURCE = "https://push.chocolatey.org/"
ZERO_SHA = "0" * 40
# Vendors whose scripts carry a version-bearing install-directory token.
# vendor -> quoted script variable holding the token ($graalvmDir is the full zip root)
DIR_VARIABLE_VENDORS = {"graalvm": "graalvmDir", "openjdk": "version", "wildfly": "version"}
DIR_LITERAL_VENDORS = {"mvnd"}  # literal maven-mvnd-<v>-windows-amd64


class UsageError(Exception):
    pass


def out(line: str = "") -> None:
    print(line, flush=True)


def err(line: str) -> None:
    print(line, file=sys.stderr, flush=True)


# ----- helpers ---------------------------------------------------------------


def find_root(start: Path | None = None) -> Path:
    here = Path(start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / manifest.MANIFEST_NAME).is_file():
            return candidate
    raise ManifestError(f"{manifest.MANIFEST_NAME} not found in {here} or its parents")


def split_ids(values: list[str] | None) -> list[str]:
    ids: list[str] = []
    for value in values or []:
        ids += [v.strip() for v in value.split(",") if v.strip()]
    return ids


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    def cell(value) -> str:
        return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")

    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def _run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a command without a shell, capturing text output."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _display(cmd: list[str]) -> str:
    shown = list(cmd)
    for i, part in enumerate(shown[:-1]):
        if part in ("-k", "--key", "--api-key"):
            shown[i + 1] = "***"
    return " ".join(shown)


def _redact(text: str, cmd: list[str]) -> str:
    """Replace the API key (CHOCO_KEY, or a ``-k`` value in ``cmd``) with ``***``."""
    keys = {os.environ.get("CHOCO_KEY", "")}
    keys |= {cmd[i + 1] for i, part in enumerate(cmd[:-1]) if part in ("-k", "--key", "--api-key")}
    for key in sorted(filter(None, keys), key=len, reverse=True):
        text = text.replace(key, "***")
    return text


def run_choco(cmd: list[str], title: str, *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a choco command and print its output, so the log shows what choco did.

    In GitHub Actions (GITHUB_ACTIONS=true) the output is wrapped in a
    collapsible ``::group::<title>`` / ``::endgroup::`` block, and workflow
    commands are switched off while choco's output is echoed (``::stop-commands::``),
    so a ``::`` line in that output is shown, not executed. The API key is
    redacted from everything printed. A non-zero exit raises RuntimeError
    carrying the last 2000 characters of the output.
    """
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    proc = _run(cmd, cwd=cwd)
    output = _redact("\n".join(s.rstrip() for s in (proc.stdout, proc.stderr) if s and s.strip()), cmd)
    if in_ci:
        out(f"::group::{title}")
    out(f"$ {_display(cmd)}")
    if output:
        if in_ci:
            token = secrets.token_hex(16)
            out(f"::stop-commands::{token}")
            out(output)
            out(f"::{token}::")
        else:
            out(output)
    if in_ci:
        out("::endgroup::")
    if proc.returncode != 0:
        raise RuntimeError(f"{title} failed (exit {proc.returncode}): {output[-2000:]}")
    return proc


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return _run(["git", *args], cwd=root)


def changed_packages(root: Path, mf: Manifest, spec: str) -> list[Package]:
    """Packages whose folder has changes in ``git diff --name-only BASE HEAD``."""
    if ".." not in spec:
        raise UsageError(f"--changed expects BASE..HEAD, got {spec!r}")
    base, head = spec.split("..", 1)
    base, head = base.strip(), head.strip() or "HEAD"
    if not base or set(base) == {"0"}:
        base = f"{head}~1"
    proc = git(root, "diff", "--name-only", base, head)
    if proc.returncode != 0:
        raise UsageError(f"git diff {base} {head} failed: {proc.stderr.strip()}")
    folders = {line.split("/", 1)[0] for line in proc.stdout.splitlines() if "/" in line}
    by_folder = mf.by_folder()
    return [by_folder[f] for f in sorted(folders) if f in by_folder]


def select(root: Path, mf: Manifest, args) -> list[Package]:
    ids = split_ids(getattr(args, "id", None))
    changed = getattr(args, "changed", None)
    if ids and changed:
        raise UsageError("use either --id or --changed, not both")
    if changed:
        return changed_packages(root, mf, changed)
    return mf.select(ids or None, getattr(args, "vendor", None))


def choco_available() -> str | None:
    if os.name != "nt":
        return None
    return shutil.which("choco")


# ----- sync --------------------------------------------------------------------


@dataclass
class SyncRow:
    id: str
    current: str
    new: str = ""
    status: str = ""
    urls: str = ""
    checksum_source: str = ""
    message: str = ""
    files: dict[str, bytes] = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        return self.status == "failed"


def compute_changes(root: Path, pkg: Package, release: sources.Release, version: str | None = None) -> dict[str, bytes]:
    """New bytes for every file that changes (folder-relative posix paths).

    ``version`` is the nuspec version to write (default ``release.version``;
    differs when a package fix applies).
    """
    folder = Path(root) / pkg.folder
    nuspec_file = manifest.nuspec_path(root, pkg)
    changes: dict[str, bytes] = {
        nuspec_file.name: nuspec.set_version(nuspec_file.read_bytes(), version or release.version)
    }
    fields: dict[str, str] = {}
    for arch in pkg.arch:
        fields.update(installscript.arch_changes(arch, release.urls[arch], release.sha256[arch]))
    changes[INSTALL_SCRIPT] = installscript.update((folder / INSTALL_SCRIPT).read_bytes(), fields)

    if pkg.vendor in DIR_VARIABLE_VENDORS.keys() | DIR_LITERAL_VENDORS:
        dir_version = release.extras.get("dir_version")
        if not dir_version:
            raise installscript.ScriptError("dir_version is required for this vendor but missing")
        total = 0
        for script in sorted((folder / "tools").glob("*.ps1")):
            rel = f"tools/{script.name}"
            data = changes.get(rel, script.read_bytes())
            if pkg.vendor in DIR_VARIABLE_VENDORS:
                new, count = installscript.set_variable(data, DIR_VARIABLE_VENDORS[pkg.vendor], dir_version)
            else:
                new, count = installscript.set_mvnd_dir(data, dir_version)
            total += count
            if count:
                changes[rel] = new
        if total == 0:
            raise installscript.ScriptError("no install-directory token found to update")

    current = {rel: (folder / rel).read_bytes() for rel in changes}
    return {rel: data for rel, data in changes.items() if data != current[rel]}


def write_files(folder: Path, files: dict[str, bytes]) -> None:
    tmp_paths = []
    try:
        for rel, data in files.items():
            target = folder / rel
            tmp = target.with_name(target.name + ".chocotools-tmp")
            tmp.write_bytes(data)
            tmp_paths.append((tmp, target))
        for tmp, target in tmp_paths:
            os.replace(tmp, target)
    finally:
        for tmp, _ in tmp_paths:
            if tmp.exists():
                tmp.unlink()


def sync_package(root: Path, pkg: Package, client: Client, dry_run: bool) -> SyncRow:
    folder = Path(root) / pkg.folder
    try:
        current = nuspec.read(manifest.nuspec_path(root, pkg).read_bytes()).version
    except (ManifestError, nuspec.NuspecError, OSError) as exc:
        return SyncRow(pkg.id, "?", status="failed", message=str(exc))
    row = SyncRow(pkg.id, current or "(empty)")
    try:
        release = sources.fetch(pkg, client=client)
    except sources.SourceError as exc:
        row.status, row.message = "failed", f"source: {exc}"
        return row
    row.new = release.version
    row.urls = " ".join(release.urls[a] for a in pkg.arch if a in release.urls)
    row.checksum_source = release.checksum_source
    problems = checks.check_release(pkg, release)
    if problems:
        row.status, row.message = "failed", "; ".join(problems)
        return row
    if current and not versioning.is_valid(current):
        row.status, row.message = "failed", f"repo version {current!r} is not a valid version"
        return row
    try:
        target, keep_fix = versioning.target_version(release.version, pkg.package_fix, pkg.package_fix_line)
    except versioning.VersionError as exc:
        row.status, row.message = "failed", f"package fix: {exc}"
        return row
    clear_fix = bool(pkg.package_fix) and not keep_fix
    notes = []
    if keep_fix:
        notes.append(f"package fix {pkg.package_fix} (upstream {release.version})")
    if clear_fix:
        notes.append(f"upstream left {pkg.package_fix_line}; package_fix {pkg.package_fix} cleared")
    row.new = target
    if current:
        cmp = versioning.compare_nuget(target, current)
        if cmp == 0:
            if clear_fix:
                # The nuspec already left the fix's line (hand edit): nothing is written, so say so.
                notes = [f"package_fix {pkg.package_fix} is stale (declared for {pkg.package_fix_line}); "
                         "remove package_fix and package_fix_line from packages.toml"]
            row.status, row.message = "up-to-date", "; ".join(notes)
            return row
        if cmp < 0:
            row.status = "failed"
            row.message = f"upstream {target} is lower than repo {current}"
            return row
    try:
        approved = chocolatey.approved_version(pkg.id, client)
    except chocolatey.ChocolateyError as exc:
        row.status, row.message = "failed", str(exc)
        return row
    problems = checks.check_increase(target, current, approved)
    if problems:
        row.status, row.message = "failed", "; ".join(problems)
        return row
    new_manifest = None
    try:
        release.extras.update(sources.resolve_extras(pkg, release, client))
        files = compute_changes(root, pkg, release, target)
        if clear_fix:
            manifest_file = Path(root) / manifest.MANIFEST_NAME
            new_manifest = manifest.clear_package_fix(manifest_file.read_bytes().decode("utf-8"), pkg.id)
    except (sources.SourceError, installscript.ScriptError, nuspec.NuspecError, ManifestError, OSError) as exc:
        row.status, row.message = "failed", str(exc)
        return row
    checked_pkg = dataclasses.replace(pkg, package_fix=None, package_fix_line=None) if clear_fix else pkg
    result = checks.validate_package(root, checked_pkg, overrides=files)
    if result.errors:
        row.status, row.message = "failed", "after update: " + "; ".join(result.errors)
        return row
    row.files = files
    if dry_run:
        row.status = "would update"
    else:
        try:
            write_files(folder, files)
            if new_manifest is not None:
                write_files(Path(root), {manifest.MANIFEST_NAME: new_manifest.encode("utf-8")})
        except OSError as exc:
            row.status, row.message = "failed", f"write failed: {exc}"
            return row
        row.status = "updated"
    if release.extras.get("dir_version"):
        notes.append(f"dir_version {release.extras['dir_version']}")
    row.message = "; ".join(notes)
    return row


def sync_report(rows: list[SyncRow], dry_run: bool) -> str:
    headers = ["Id", "Current", "New", "Status", "URLs", "Checksum source", "Message"]
    table = md_table(
        headers,
        [[r.id, r.current, r.new, r.status, r.urls, r.checksum_source, r.message] for r in rows],
    )
    changed = [r for r in rows if r.status in ("updated", "would update")]
    failed = [r for r in rows if r.failed]
    title = "chocotools sync (dry run)" if dry_run else "chocotools sync"
    lines = [f"## {title}", "", table, ""]
    lines.append(f"{len(changed)} changed, {len(failed)} failed, {len(rows)} checked.")
    if failed:
        lines += ["", "### Failures", ""]
        lines += [f"- {r.id}: {r.message}" for r in failed]
    return "\n".join(lines) + "\n"


def cmd_sync(args, root: Path, mf: Manifest, client: Client) -> int:
    rows: list[SyncRow] = []
    for pkg in select(root, mf, args):
        if pkg.frozen:
            if split_ids(args.id):
                rows.append(SyncRow(pkg.id, "", status="skipped", message="frozen"))
            continue
        try:
            rows.append(sync_package(root, pkg, client, args.dry_run))
        except Exception as exc:  # noqa: BLE001 - one package's bug must not stop the others
            rows.append(SyncRow(pkg.id, "?", status="failed", message=f"internal error: {type(exc).__name__}: {exc}"))
    report = sync_report(rows, args.dry_run)
    out(report)
    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
    return EXIT_FAILED if any(r.failed for r in rows) else EXIT_OK


# ----- validate ----------------------------------------------------------------


def online_check(root: Path, pkg: Package, client: Client) -> checks.Result:
    res = checks.Result()
    data = (Path(root) / pkg.folder / INSTALL_SCRIPT).read_bytes()
    script = installscript.read(data)
    for arch in pkg.arch:
        url = script.get(installscript.ARCH_FIELDS[arch][0])
        if not url:
            continue  # already reported offline
        try:
            resp = client.head(url)
        except HttpError as exc:
            res.errors.append(f"{arch} URL unreachable: {exc}")
            continue
        if resp.status not in (200, 206):
            res.errors.append(f"{arch} URL answered HTTP {resp.status}: {url}")
        else:
            final_host = urllib.parse.urlsplit(resp.url or url).hostname
            out(f"ok    {pkg.id}: {arch} URL HTTP {resp.status} (final host {final_host})")
    return res


def run_validate(root: Path, mf: Manifest, pkgs: list[Package], online: bool, client: Client, tree: bool) -> int:
    errors = warnings = 0
    if tree:
        for problem in manifest.check_tree(root, mf):
            out(f"ERROR manifest: {problem}")
            errors += 1
    for pkg in pkgs:
        if not (Path(root) / pkg.folder).is_dir():
            continue  # reported by the tree check
        res = checks.validate_package(root, pkg)
        if online and not pkg.frozen:
            res.extend(online_check(root, pkg, client))
        for e in res.errors:
            out(f"ERROR {pkg.id}: {e}")
        for w in res.warnings:
            out(f"WARN  {pkg.id}: {w}")
        errors += len(res.errors)
        warnings += len(res.warnings)
    out(f"validate: {len(pkgs)} packages, {errors} errors, {warnings} warnings")
    return EXIT_FAILED if errors else EXIT_OK


def cmd_validate(args, root: Path, mf: Manifest, client: Client) -> int:
    ids = split_ids(args.id)
    pkgs = mf.select(ids or None)
    return run_validate(root, mf, pkgs, args.online, client, tree=not ids)


# ----- build / publish -----------------------------------------------------------


def pack(root: Path, pkg: Package, out_dir: Path) -> Path:
    """``choco pack`` one package into ``out_dir``; returns the nupkg path."""
    nuspec_file = manifest.nuspec_path(root, pkg)
    version = nuspec.read(nuspec_file.read_bytes()).version
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["choco", "pack", str(nuspec_file), "--output-directory", str(out_dir), "--limit-output"]
    run_choco(cmd, f"choco pack {pkg.id} {version}", cwd=root)
    nupkg = out_dir / f"{pkg.id}.{version}.nupkg"
    if not nupkg.is_file():
        matches = sorted(out_dir.glob(f"{pkg.id}.*.nupkg"))
        if not matches:
            raise RuntimeError(f"choco pack produced no nupkg for {pkg.id}")
        nupkg = matches[-1]
    return nupkg


def cmd_build(args, root: Path, mf: Manifest, client: Client) -> int:
    pkgs = select(root, mf, args)
    if not pkgs:
        out("build: no packages selected")
        return EXIT_OK
    if run_validate(root, mf, pkgs, False, client, tree=False) != EXIT_OK:
        return EXIT_FAILED
    if not choco_available():
        err("choco not found: build requires Windows + Chocolatey")
        return EXIT_PREREQ
    out_dir = (Path(root) / args.out).resolve()
    failed = 0
    for pkg in pkgs:
        try:
            out(f"built {pack(root, pkg, out_dir)}")
        except (RuntimeError, ManifestError, OSError) as exc:
            out(f"FAIL  {pkg.id}: {exc}")
            failed += 1
    return EXIT_FAILED if failed else EXIT_OK


def tree_problems(root: Path, pkgs: list[Package]) -> list[str]:
    problems = []
    status = git(root, "status", "--porcelain")
    if status.returncode != 0:
        return [f"git status failed: {status.stderr.strip()}"]
    if status.stdout.strip():
        problems.append("working tree is not clean (git status --porcelain is non-empty)")
    for pkg in pkgs:
        if git(root, "diff", "--quiet", "HEAD", "--", pkg.folder).returncode != 0:
            problems.append(f"{pkg.folder} differs from HEAD")
        untracked = git(root, "ls-files", "--others", "--exclude-standard", "--", pkg.folder)
        if untracked.stdout.strip():
            problems.append(f"{pkg.folder} has untracked files")
    return problems


def cmd_publish(args, root: Path, mf: Manifest, client: Client) -> int:
    selected = select(root, mf, args)
    pkgs = [p for p in selected if not p.frozen]
    for p in selected:
        if p.frozen:
            out(f"skip  {p.id}: frozen")
    if not pkgs:
        out("publish: no packages to publish")
        return EXIT_OK
    if not choco_available():
        err("choco not found: publish requires Windows + Chocolatey")
        return EXIT_PREREQ
    key = os.environ.get("CHOCO_KEY", "")
    if not args.dry_run and not key:
        err("CHOCO_KEY is not set: publish needs it to push (use --dry-run to skip the push)")
        return EXIT_PREREQ
    problems = tree_problems(root, pkgs)
    if problems:
        for p in problems:
            out(f"REFUSE {p}")
        return EXIT_FAILED
    if run_validate(root, mf, pkgs, True, client, tree=False) != EXIT_OK:
        return EXIT_FAILED
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    out_dir = (Path(root) / "out").resolve()
    failed = 0
    for pkg in pkgs:
        try:
            version = nuspec.read(manifest.nuspec_path(root, pkg).read_bytes()).version
            approved = chocolatey.approved_version(pkg.id, client)
            if approved and versioning.compare_nuget(version, approved) == 0:
                # Files changed without a version bump (e.g. a checksum edit): nothing to push.
                out(f"skip  {pkg.id}: {version} already approved on Chocolatey")
                continue
            if approved and versioning.compare_nuget(version, approved) < 0:
                raise RuntimeError(f"version {version} is not greater than Chocolatey approved {approved}")
            nupkg = pack(root, pkg, out_dir)
            if in_ci:
                install = ["choco", "install", pkg.id, "--version", version, "--source", str(out_dir), "-y",
                           "--no-progress"]
                run_choco(install, f"choco install {pkg.id} {version}", cwd=root)
                run_choco(["choco", "uninstall", pkg.id, "-y"], f"choco uninstall {pkg.id} {version}", cwd=root)
            else:
                out(f"skip  {pkg.id}: test install runs in CI only (GITHUB_ACTIONS != true)")
            if args.dry_run:
                out(f"dry-run {pkg.id} {version}: not pushed")
                continue
            cmd = ["choco", "push", str(nupkg), "--source", PUSH_SOURCE, "-k", key]
            run_choco(cmd, f"choco push {pkg.id} {version}", cwd=root)
            out(f"pushed {pkg.id} {version}")
        except (RuntimeError, ManifestError, nuspec.NuspecError, chocolatey.ChocolateyError, OSError) as exc:
            out(f"FAIL  {pkg.id}: {exc}")
            failed += 1
    return EXIT_FAILED if failed else EXIT_OK


# ----- compare -----------------------------------------------------------------


def compare_row(root: Path, pkg: Package, client: Client) -> dict:
    row = {"folder": pkg.folder, "id": pkg.id, "repo": "", "choco_approved": "", "source_raw": "",
           "source": "", "status": "", "note": ""}
    try:
        row["repo"] = nuspec.read(manifest.nuspec_path(root, pkg).read_bytes()).version
    except (ManifestError, nuspec.NuspecError, OSError) as exc:
        row["status"] = f"error: {exc}"
        return row
    try:
        row["choco_approved"] = chocolatey.approved_version(pkg.id, client) or "none"
    except chocolatey.ChocolateyError as exc:
        row["choco_approved"] = f"error: {exc}"
    if pkg.vendor == "lmc":
        row["status"] = "manual"
        return row
    try:
        release = sources.fetch(pkg, client=client)
        row["source_raw"], row["source"] = release.version_raw, release.version
    except sources.SourceError as exc:
        row["status"] = "frozen" if pkg.frozen else f"error: {exc}"
        row["source"] = f"error: {exc}" if pkg.frozen else ""
        return row
    if pkg.frozen:
        row["status"] = "frozen"
    elif not row["repo"] or not versioning.is_valid(row["repo"]):
        row["status"] = "behind"
    else:
        try:
            target, keep_fix = versioning.target_version(row["source"], pkg.package_fix, pkg.package_fix_line)
        except versioning.VersionError as exc:
            row["status"] = f"error: package fix: {exc}"
            return row
        cmp = versioning.compare_nuget(row["repo"], target)
        row["status"] = "in-sync" if cmp == 0 else ("behind" if cmp < 0 else "ahead")
        if keep_fix:
            row["note"] = f"package fix {pkg.package_fix}: {row['source']} -> {target}"
    return row


def cmd_compare(args, root: Path, mf: Manifest, client: Client) -> int:
    rows = [compare_row(root, pkg, client) for pkg in mf.packages]
    if args.format == "json":
        text = json.dumps(rows, indent=2) + "\n"
    else:
        table = md_table(
            ["Folder", "Id", "Repo", "Choco approved", "Source (raw -> normalized)", "Status", "Note"],
            [
                [r["folder"], r["id"], r["repo"] or "(empty)", r["choco_approved"],
                 f"{r['source_raw']} -> {r['source']}" if r["source_raw"] else r["source"], r["status"],
                 r["note"]]
                for r in rows
            ],
        )
        text = table + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        out(f"compare: wrote {len(rows)} rows to {path}")
    else:
        out(text.rstrip("\n"))
    return EXIT_FAILED if any(r["status"].startswith("error") for r in rows) else EXIT_OK


# ----- syncpr ------------------------------------------------------------------


def cmd_syncpr(args, root: Path, mf: Manifest, client: Client) -> int:
    text = (args.open_pr or "").strip()
    if text and not text.isdigit():
        raise UsageError(f"--open-pr expects a PR number, got {text!r}")
    open_pr = int(text) if text else None
    try:
        state = syncpr.gather(root, open_pr, args.after_sync)
    except syncpr.SyncPrError as exc:
        err(f"chocotools syncpr: {exc}")
        return EXIT_FAILED
    plan = syncpr.plan(state)
    values = syncpr.outputs(plan, args.after_sync)
    for key, value in values.items():
        out(f"{key}={value}")
    if args.body:
        syncpr.write_body(Path(args.report) if args.report else None, Path(args.body), plan.note)
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as fh:
            fh.writelines(f"{key}={value}\n" for key, value in values.items())
    return EXIT_OK


# ----- entry point -------------------------------------------------------------


class _Parser(argparse.ArgumentParser):
    def error(self, message):  # exit 2 on usage errors (argparse default) with our prefix
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"chocotools: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="chocotools", description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=f"chocotools {__version__}")
    parser.add_argument("--root", help="repo root (default: nearest parent with packages.toml)")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)

    def ids(p, help_text="package id (repeatable, comma-separated)"):
        p.add_argument("--id", action="append", metavar="ID", help=help_text)

    p = sub.add_parser("sync", help="update packages whose upstream version increased")
    p.add_argument("--vendor", choices=manifest.VENDORS)
    ids(p)
    p.add_argument("--dry-run", action="store_true", help="print the table, write nothing")
    p.add_argument("--report", metavar="PATH", help="also write the markdown report here")

    p = sub.add_parser("validate", help="check package files against the manifest")
    ids(p)
    p.add_argument("--online", action="store_true", help="also HEAD every URL (non-frozen packages)")

    for name, help_text in (("build", "validate and choco pack"), ("publish", "pack, test and push")):
        p = sub.add_parser(name, help=help_text)
        group = p.add_mutually_exclusive_group()
        group.add_argument("--id", action="append", metavar="ID", help="package id (repeatable, comma-separated)")
        group.add_argument("--changed", metavar="BASE..HEAD", help="packages changed in this git range")
        if name == "build":
            p.add_argument("--out", default="out", help="output directory (default: out)")
        else:
            p.add_argument("--dry-run", action="store_true", help="everything except choco push")

    p = sub.add_parser("compare", help="repo vs Chocolatey vs upstream report")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--output", metavar="PATH")

    p = sub.add_parser("syncpr", help="decide bot/sync branch and PR actions for the sync workflow")
    p.add_argument("action", choices=("plan",))
    p.add_argument("--open-pr", default="", metavar="N", help="open bot/sync PR number (empty = none)")
    p.add_argument("--after-sync", action="store_true", help="also decide commit, push and PR")
    p.add_argument("--report", metavar="PATH", help="sync report to use as the PR body")
    p.add_argument("--body", metavar="PATH", help="write the PR body here")
    p.add_argument("--github-output", metavar="PATH", help="append key=value lines (e.g. $GITHUB_OUTPUT)")
    return parser


COMMANDS = {
    "sync": cmd_sync,
    "validate": cmd_validate,
    "build": cmd_build,
    "publish": cmd_publish,
    "compare": cmd_compare,
    "syncpr": cmd_syncpr,
}


def main(argv: list[str] | None = None, client: Client | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = Path(args.root).resolve() if args.root else find_root()
        mf = manifest.load(root)
        return COMMANDS[args.command](args, root, mf, client or default_client())
    except (ManifestError, UsageError) as exc:
        err(f"chocotools: {exc}")
        return EXIT_USAGE
