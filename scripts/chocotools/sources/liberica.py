"""BellSoft Liberica via the BellSoft API (replaces the old foojay lookup).

Query: ``GET https://api.bell-sw.com/v1/liberica/releases?version-feature=<major>&bundle-type=<bt>&os=windows&arch=x86&bitness=64&package-type=msi&version-modifier=latest``
with ``bt`` from (image, variant): jdk std ``jdk``, jdk full ``jdk-full``,
jdk lite ``jdk-lite``, jre std ``jre``, jre full ``jre-full``.

Keeps ``GA == true`` entries and picks the max of (every numeric part of
``version``, build); the API lists both the PSU (``21.0.12+10``) and the CSPU
(``21.0.12.1+1``), and the CSPU wins; ``21.0.13.0.2+5`` beats ``21.0.13+11``.
URL is ``downloadUrl`` (github.com/bell-sw).

Checksum: BellSoft publishes sha1 only, so sha256 comes from the GitHub
release asset ``digest`` (``repos/bell-sw/Liberica/releases/tags/<tag>``,
matched by ``filename``; the tag is the path segment after ``/download/``).
Fallback: a .sha256 asset, else a streamed download.
"""

from __future__ import annotations

import re
import urllib.parse

from .. import versioning
from ..http import Client
from ..manifest import Package
from . import (
    Release,
    SourceError,
    asset_sha256,
    find_asset,
    formatted,
    github_release_by_tag,
    no_pinned_version,
    require,
)

API = "https://api.bell-sw.com/v1/liberica/releases"
REPO = "bell-sw/Liberica"
BUNDLE_TYPES = {
    ("jdk", "std"): "jdk",
    ("jdk", "full"): "jdk-full",
    ("jdk", "lite"): "jdk-lite",
    ("jre", "std"): "jre",
    ("jre", "full"): "jre-full",
}
_V8 = re.compile(r"^8u(\d+)\+(\d+)$")
_VN = re.compile(r"^(\d+(?:\.\d+)*)\+\d+$")


def normalize(version: str) -> str:
    """``8u504+1`` -> ``8.0.504.1``; ``21.0.12.1+1`` -> ``21.0.12.1``; ``21.0.13.0.2+5`` -> ``21.0.13.2``.

    The build is dropped; a 5-part version maps with ``versioning.jdk_five_part``.
    """
    m = _V8.match(version)
    if m:
        return formatted(f"8.0.{int(m[1])}.{int(m[2])}", "Liberica version")
    m = _VN.match(version)
    if m:
        try:
            return versioning.jdk_five_part(m[1])
        except versioning.VersionError as exc:
            raise SourceError(f"Liberica version {m[1]!r}: {exc}") from exc
    raise SourceError(f"unrecognized Liberica version {version!r}")


def _key(entry: dict) -> tuple[tuple[int, ...], int]:
    """Every numeric part of ``version``, then the build.

    The API has no field for a 5th part (``21.0.13.0.2+5`` has ``patchVersion``
    0 and ``buildVersion`` 5), so ordering on the fields would put ``21.0.13+11``
    above it. ``8u…`` versions use (feature, interim, update, patch).
    """
    m = _VN.match(str(entry.get("version") or ""))
    if m:
        parts = [int(p) for p in m[1].split(".")]
    else:
        parts = [int(entry.get(k) or 0) for k in ("featureVersion", "interimVersion", "updateVersion", "patchVersion")]
    parts += [0] * (5 - len(parts))
    return tuple(parts), int(entry.get("buildVersion") or 0)


def bundle_type(pkg: Package) -> str:
    try:
        return BUNDLE_TYPES[(pkg.image, pkg.variant)]
    except KeyError:
        raise SourceError(f"no Liberica bundle type for image={pkg.image} variant={pkg.variant}") from None


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("liberica", version)
    if tuple(pkg.arch) != ("x64",):
        raise SourceError("Liberica packages are x64 only")
    bt = bundle_type(pkg)
    url = (
        f"{API}?version-feature={pkg.major}&bundle-type={bt}&os=windows&arch=x86"
        f"&bitness=64&package-type=msi&version-modifier=latest"
    )
    entries = [
        e
        for e in client.get_json(url) or []
        if e.get("GA") is True
        and e.get("os") == "windows"
        and e.get("bitness") == 64
        and e.get("packageType") == "msi"
        and e.get("bundleType") == bt
        and int(e.get("featureVersion") or 0) == pkg.major
    ]
    if not entries:
        raise SourceError(f"BellSoft has no GA {bt} MSI for Liberica {pkg.major}")
    best = max(entries, key=_key)
    raw_version = require(best.get("version"), "version")
    download = require(best.get("downloadUrl"), "downloadUrl")
    filename = require(best.get("filename"), "filename")
    path = urllib.parse.urlsplit(download).path
    if "/download/" not in path or not path.endswith("/" + filename):
        raise SourceError(f"unexpected Liberica download URL {download}")
    tag = urllib.parse.unquote(path.split("/download/", 1)[1].split("/", 1)[0])
    gh = github_release_by_tag(client, REPO, tag)
    sha, source = asset_sha256(client, gh, find_asset(gh, filename))
    return Release(
        version=normalize(raw_version),
        version_raw=raw_version,
        urls={"x64": download},
        sha256={"x64": sha},
        checksum_source=source,
        raw=best,
    )
