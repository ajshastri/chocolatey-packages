"""Safety checks shared by ``validate`` and ``sync``.

- Install-script URLs must be https and on an exact-host allowlist.
  ``d3pxv6yz143wms.cloudfront.net`` and ``download.oracle.com`` (allowed by the
  spec "only if used") are left out because no package uses them. GitHub
  downloads redirect to ``release-assets.githubusercontent.com``; that is a
  redirect target, not a package-file URL, so it is not listed.
- Denylisted hosts (``*.foojay.io``, ``aka.ms``) may not appear in any file of
  a package folder.
- Checksums: sha256 passes; sha1/md5 are warnings; empty or wrong length is an error.
- Versions: 1-4 numeric parts; a new version must be strictly greater than the
  repo version and Chocolatey's approved version.
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

from . import installscript, nuspec, versioning
from .manifest import Package

ALLOWED_HOSTS = frozenset(
    {
        "github.com",
        "objects.githubusercontent.com",
        "download.bell-sw.com",
        "cdn.azul.com",
        "corretto.aws",
        "download.java.net",
    }
)
DENIED_HOSTS = ("api.foojay.io", "*.foojay.io", "aka.ms")
_DENIED_RE = re.compile(
    r"(?i)(?<![a-z0-9-])(?:(?:[a-z0-9-]+\.)*foojay\.io|aka\.ms)(?![a-z0-9-])"
)
_HEX = re.compile(r"^[0-9a-fA-F]+$")
CHECKSUM_LENGTHS = {"sha256": 64, "sha1": 40, "md5": 32}
WEAK_TYPES = {"sha1", "md5"}


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: "Result") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def is_denied_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    return host == "aka.ms" or host == "foojay.io" or host.endswith(".foojay.io")


def check_url(url: str, label: str = "URL") -> list[str]:
    if not url or not url.strip():
        return [f"{label} is empty"]
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme != "https":
        return [f"{label} is not https: {url}"]
    if is_denied_host(host):
        return [f"{label} uses a denied host ({host}): {url}"]
    if host not in ALLOWED_HOSTS:
        return [f"{label} host {host!r} is not on the allowlist: {url}"]
    return []


def find_denied(text: str) -> list[str]:
    """Every denylisted host mentioned in ``text``."""
    return sorted({m.group(0).lower() for m in _DENIED_RE.finditer(text)})


def check_sha256(value: str | None, label: str = "sha256") -> list[str]:
    if not value:
        return [f"{label} is empty"]
    if len(value) != 64 or not _HEX.match(value):
        return [f"{label} is not a 64-hex sha256: {value!r}"]
    return []


def check_checksum(value: str | None, ctype: str | None, label: str) -> Result:
    res = Result()
    kind = (ctype or "").lower()
    if not value:
        res.errors.append(f"{label} is empty")
        return res
    if kind not in CHECKSUM_LENGTHS:
        res.errors.append(f"{label} type {ctype!r} is not sha256/sha1/md5")
        return res
    if len(value) != CHECKSUM_LENGTHS[kind] or not _HEX.match(value):
        res.errors.append(f"{label} is not a valid {kind} ({len(value)} chars)")
        return res
    if kind in WEAK_TYPES:
        res.warnings.append(f"{label} uses {kind}, not sha256 (sync writes sha256 on the next version bump)")
    return res


def check_version(version: str | None, label: str = "version") -> list[str]:
    if not version:
        return [f"{label} is empty"]
    try:
        versioning.parse(version)
    except versioning.VersionError as exc:
        return [f"{label}: {exc}"]
    return []


def check_increase(new: str, current: str | None, approved: str | None) -> list[str]:
    """``new`` must be strictly greater than the repo and the approved version."""
    errors = check_version(new, "new version")
    if errors:
        return errors
    if current and versioning.is_valid(current) and versioning.compare_nuget(new, current) <= 0:
        errors.append(f"new version {new} is not greater than repo version {current}")
    if approved and versioning.compare_nuget(new, approved) <= 0:
        errors.append(f"new version {new} is not greater than Chocolatey approved {approved}")
    return errors


def check_release(pkg: Package, release) -> list[str]:
    """Check a ``sources.Release`` before anything is written."""
    errors = check_version(release.version, "upstream version")
    if not errors and release.version != versioning.format(release.version):
        errors.append(f"upstream version {release.version} is not normalized")
    if set(release.urls) != set(pkg.arch):
        errors.append(f"release arches {sorted(release.urls)} do not match manifest {list(pkg.arch)}")
    for arch in pkg.arch:
        errors += check_url(release.urls.get(arch, ""), f"{arch} URL")
        errors += check_sha256(release.sha256.get(arch), f"{arch} sha256")
    if "x86" in release.urls and release.urls.get("x86") == release.urls.get("x64"):
        errors.append("x86 URL equals the x64 URL")
    return errors


def _read_files(folder: Path, overrides: dict[str, bytes]) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    if folder.is_dir():
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                files[path.relative_to(folder).as_posix()] = path.read_bytes()
    files.update(overrides)
    return files


def validate_package(root: Path, pkg: Package, overrides: dict[str, bytes] | None = None) -> Result:
    """Offline checks for one package folder.

    ``overrides`` maps folder-relative posix paths to replacement bytes, so sync
    can validate its computed files before writing them.
    """
    res = Result()
    folder = Path(root) / pkg.folder
    files = _read_files(folder, overrides or {})
    nuspecs = [name for name in files if "/" not in name and name.endswith(".nuspec")]
    if len(nuspecs) != 1:
        res.errors.append(f"expected exactly one *.nuspec, found {len(nuspecs)}")
        return res
    try:
        info = nuspec.read(files[nuspecs[0]])
    except nuspec.NuspecError as exc:
        res.errors.append(str(exc))
        return res
    if info.id != pkg.id:
        res.errors.append(f"nuspec <id> is {info.id!r}, manifest id is {pkg.id!r}")
    res.errors += check_version(info.version, "nuspec version")

    for name, data in files.items():
        denied = find_denied(data.decode("utf-8", errors="ignore"))
        if denied:
            res.errors.append(f"{name} mentions denied host(s): {', '.join(denied)}")

    script_name = "tools/chocolateyinstall.ps1"
    if script_name not in files:
        res.errors.append(f"{script_name} is missing")
        return res
    try:
        script = installscript.read(files[script_name])
    except installscript.ScriptError as exc:
        res.errors.append(f"{script_name}: {exc}")
        return res
    for dup in script.duplicates:
        res.errors.append(f"{script_name}: field {dup} appears more than once")

    wanted = {f for arch in pkg.arch for f in installscript.ARCH_FIELDS[arch]}
    for arch in pkg.arch:
        url_key, sum_key, type_key = installscript.ARCH_FIELDS[arch]
        url = script.get(url_key)
        if url is None:
            res.errors.append(f"{arch} URL field ({url_key}) is missing")
        else:
            res.errors += check_url(url, f"{arch} URL")
        if script.get(sum_key) is None:
            res.errors.append(f"{arch} checksum field ({sum_key}) is missing")
        else:
            res.extend(check_checksum(script.get(sum_key), script.get(type_key), f"{arch} checksum"))
    extra = sorted(name for name in script.values if name not in wanted)
    if extra:
        res.errors.append(
            f"fields {', '.join(extra)} present but manifest arch is {list(pkg.arch)}"
        )
    if script.get("url") and script.get("url") == script.get("url64"):
        res.errors.append("x86 URL equals the x64 URL")
    return res
