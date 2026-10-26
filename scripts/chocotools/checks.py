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
- URL/version consistency: every install-script URL must carry the nuspec
  version in the vendor's own form (``versioning.url_version``). With
  ``package_fix`` the fix suffix is stripped first (``21.0.12.101`` -> URL
  ``21.0.12.1``); a nuspec that is not on ``package_fix_line`` is reported as
  a stale fix. Frozen packages are checked too. ``URL_VERSION_EXCEPTIONS``
  pins the one known historical mismatch to its exact version, so a later
  hand edit of that package still fails.
- Nuspec metadata (Chocolatey package validator rules): an empty or missing
  ``<releaseNotes>`` is an error (CPMR0042; sync writes it with each version).
  Warnings: empty projectSourceUrl/docsUrl/bugTrackerUrl/iconUrl/licenseUrl/
  projectUrl/summary/authors (CPMR0057/0033/0047), a packageSourceUrl that is
  not this repo's folder (CPMR0040), any ``http://`` *Url, a releaseNotes URL
  that is not https, tags with commas, uppercase or "chocolatey" (CPMR0014),
  and a description under 30 characters.
- Side-by-side uninstall: a ``tools/chocolateyuninstall.ps1`` that pins a quoted
  ``$major`` must match the manifest major, its ``$softwareName`` must be the
  vendor MSI's product name (``uninstall_display_name``), and
  ``tools/.skipAutoUninstall`` must exist, so uninstalling one major never
  removes another major of the same vendor. Each failure is an error, so a
  manifest major bump fails until the script is updated.
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
# (id, nuspec version) -> version the URL carries.
# graalvm-java17 was approved as 22.3.3 (the old GraalVM CE release number) but
# installs graalvm-community jdk-17.0.9, the last CE 17 build. It is frozen and
# cannot move to 17.0.9 (that sorts below 22.3.3), so the pair is pinned here.
URL_VERSION_EXCEPTIONS = {("graalvm-java17", "22.3.3"): "17.0.9"}
CHECKSUM_LENGTHS = {"sha256": 64, "sha1": 40, "md5": 32}
WEAK_TYPES = {"sha1", "md5"}
REPO_TREE = "https://github.com/ajshastri/chocolatey-packages/tree/master/"
RECOMMENDED_FIELDS = ("projectSourceUrl", "docsUrl", "bugTrackerUrl", "iconUrl", "licenseUrl", "projectUrl",
                      "summary", "authors")
MIN_DESCRIPTION = 30
UNINSTALL_SCRIPT = "tools/chocolateyuninstall.ps1"
SKIP_AUTO_UNINSTALL = "tools/.skipAutoUninstall"
_LIBERICA_SUFFIX = {None: "", "std": "", "full": " Full", "lite": " Lite"}


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


def check_url_version(pkg: Package, version: str, url: str, label: str = "URL") -> list[str]:
    """``url`` must carry ``version`` (package fix stripped) in the vendor's form."""
    if not versioning.is_valid(version):
        return []  # reported by check_version
    expected = URL_VERSION_EXCEPTIONS.get((pkg.id, version), version)
    if pkg.package_fix and pkg.package_fix_line and not versioning.same_line(version, pkg.package_fix_line):
        # Do not suggest sync: the fix belongs to another line and must not be carried over.
        return [f"{label}: package_fix {pkg.package_fix} is stale: it was declared for {pkg.package_fix_line} "
                f"but the nuspec version {version} is on another A.B.C line; remove package_fix and "
                f"package_fix_line from packages.toml"]
    if pkg.package_fix and expected == version:
        try:
            expected = versioning.strip_package_fix(version, pkg.package_fix)
        except versioning.VersionError as exc:
            return [f"{label}: {exc} (run sync to apply package_fix)"]
    try:
        found = versioning.url_version(pkg.vendor, url)
    except versioning.VersionError as exc:
        return [f"{label}: {exc}"]
    if not versioning.equal(found, expected):
        if pkg.package_fix and versioning.equal(found, version):
            return [f"{label} matches nuspec {version} but package_fix {pkg.package_fix} is not applied "
                    f"(run sync to apply package_fix): {url}"]
        shown = expected if expected == version else f"{expected} (from nuspec {version})"
        return [f"{label} is for version {found} but the nuspec expects {shown}: {url}"]
    return []


def check_metadata(pkg: Package, meta: dict[str, str]) -> Result:
    """Chocolatey guideline checks on the nuspec metadata (``nuspec.metadata``)."""
    res = Result()
    notes = meta.get("releaseNotes", "")
    if not notes:
        res.errors.append("<releaseNotes> is missing or empty (run sync, or add the release-notes URL)")
    else:
        if "://" in notes and not notes.lower().startswith("https://"):
            res.warnings.append(f"<releaseNotes> URL is not https: {notes}")
    for name in RECOMMENDED_FIELDS:
        if not meta.get(name):
            res.warnings.append(f"<{name}> is missing or empty")
    expected = REPO_TREE + pkg.folder
    if meta.get("packageSourceUrl") != expected:
        res.warnings.append(f"<packageSourceUrl> is {meta.get('packageSourceUrl')!r}, expected {expected}")
    for name, value in sorted(meta.items()):
        if name.endswith("Url") and value.lower().startswith("http://"):
            res.warnings.append(f"<{name}> is not https: {value}")
    tags = meta.get("tags", "")
    if "," in tags:
        res.warnings.append(f"<tags> must be space separated, not comma separated: {tags!r}")
    if tags != tags.lower():
        res.warnings.append(f"<tags> should be lowercase: {tags!r}")
    if "chocolatey" in tags.lower().replace(",", " ").split():
        res.warnings.append(f"<tags> should not contain 'chocolatey': {tags!r}")
    if len(meta.get("description", "")) < MIN_DESCRIPTION:
        res.warnings.append(f"<description> is shorter than {MIN_DESCRIPTION} characters")
    return res


def uninstall_display_name(pkg: Package) -> str | None:
    """The vendor MSI's product name (ARP DisplayName) for ``pkg``, or None if not pinned.

    Corretto uses one name for every major, so its uninstall script tells the
    majors apart by DisplayVersion only.
    """
    if pkg.vendor == "sapmachine" and pkg.image:
        return f"SapMachine {pkg.major} {pkg.image.upper()}"
    if pkg.vendor == "liberica" and pkg.image:
        return f"Liberica {pkg.image.upper()} {pkg.major}{_LIBERICA_SUFFIX[pkg.variant]} (64-bit)"
    if pkg.vendor == "corretto":
        return "Amazon Corretto (x64)"
    return None


def check_uninstall(pkg: Package, files: dict[str, bytes]) -> list[str]:
    """Side-by-side rule for a ``tools/chocolateyuninstall.ps1`` that pins ``$major``."""
    data = files.get(UNINSTALL_SCRIPT)
    if data is None:
        return []
    try:
        majors = installscript.get_variable(data, "major")
        names = installscript.get_variable(data, "softwareName")
    except installscript.ScriptError as exc:
        return [f"{UNINSTALL_SCRIPT}: {exc}"]
    if not majors:
        return []
    errors = []
    if majors != [str(pkg.major)]:
        errors.append(f"{UNINSTALL_SCRIPT}: $major is {majors}, manifest major is {pkg.major}")
    expected = uninstall_display_name(pkg)
    if expected is not None and names != [expected]:
        errors.append(f"{UNINSTALL_SCRIPT}: $softwareName is {names}, expected {expected!r}")
    if SKIP_AUTO_UNINSTALL not in files:
        errors.append(f"{SKIP_AUTO_UNINSTALL} is missing (Chocolatey's auto-uninstaller could remove "
                      f"another major's build)")
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
        meta = nuspec.metadata(files[nuspecs[0]])
    except nuspec.NuspecError as exc:
        res.errors.append(str(exc))
        return res
    if info.id != pkg.id:
        res.errors.append(f"nuspec <id> is {info.id!r}, manifest id is {pkg.id!r}")
    res.errors += check_version(info.version, "nuspec version")
    res.extend(check_metadata(pkg, meta))

    for name, data in files.items():
        denied = find_denied(data.decode("utf-8", errors="ignore"))
        if denied:
            res.errors.append(f"{name} mentions denied host(s): {', '.join(denied)}")
    res.errors += check_uninstall(pkg, files)

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
            url_errors = check_url(url, f"{arch} URL")
            res.errors += url_errors
            if not url_errors and info.version:
                res.errors += check_url_version(pkg, info.version, url, f"{arch} URL")
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
