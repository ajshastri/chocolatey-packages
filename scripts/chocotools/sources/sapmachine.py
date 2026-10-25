"""SAP Machine via GitHub releases.

Query: ``GET https://api.github.com/repos/SAP/SapMachine/releases?per_page=100``
(up to 3 pages, stopping at the first page that has a match for the major).
Keeps ``prerelease == false`` releases tagged ``sapmachine-<major>`` or
``sapmachine-<major>.…`` that carry the asset
``sapmachine-<image>-<ver>_windows-x64_bin.msi``; the max version wins.

A pinned ``version`` is fetched by tag (``releases/tags/sapmachine-<version>``);
used to restore sapmachine11 at 11.0.25.

Checksum: asset ``digest``, falling back to the ``<asset>.sha256.txt`` asset.
"""

from __future__ import annotations

import re

from .. import versioning
from ..http import Client
from ..manifest import Package
from . import (
    Release,
    SourceError,
    asset_sha256,
    find_asset,
    github_api,
    github_release_by_tag,
    require,
)

REPO = "SAP/SapMachine"
MAX_PAGES = 3
_TAG = re.compile(r"^sapmachine-(\d+(?:\.\d+)*)(?:\+\d+)?$")


def normalize(tag: str) -> str:
    """``sapmachine-21.0.12.1`` -> ``21.0.12.1``; ``sapmachine-21.0.13.0.2`` -> ``21.0.13.2``.

    A 5-part version maps with ``versioning.jdk_five_part``.
    """
    m = _TAG.match(tag)
    if not m:
        raise SourceError(f"unrecognized SapMachine tag {tag!r}")
    try:
        return versioning.jdk_five_part(m[1])
    except versioning.VersionError as exc:
        raise SourceError(f"SapMachine version {m[1]!r}: {exc}") from exc


def asset_name(pkg: Package, tag: str) -> str:
    ver = re.sub(r"^sapmachine-", "", tag)
    return f"sapmachine-{pkg.image}-{ver}_windows-x64_bin.msi"


def _candidate(pkg: Package, rel: dict) -> bool:
    tag = rel.get("tag_name") or ""
    m = _TAG.match(tag)
    if rel.get("prerelease") or rel.get("draft") or not m:
        return False
    if m[1].split(".")[0] != str(pkg.major):
        return False
    return any(a.get("name") == asset_name(pkg, tag) for a in rel.get("assets") or [])


def _release(pkg: Package, rel: dict, client: Client) -> Release:
    tag = rel["tag_name"]
    asset = find_asset(rel, asset_name(pkg, tag))
    url = require(asset.get("browser_download_url"), "browser_download_url")
    sha, source = asset_sha256(client, rel, asset)
    return Release(
        version=normalize(tag),
        version_raw=tag,
        urls={"x64": url},
        sha256={"x64": sha},
        checksum_source=source,
        raw={"tag_name": tag, "asset": asset.get("name")},
    )


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    if tuple(pkg.arch) != ("x64",):
        raise SourceError("SapMachine packages are x64 only")
    if version is not None:
        rel = github_release_by_tag(client, REPO, f"sapmachine-{version}")
        if not _candidate(pkg, rel):
            raise SourceError(f"sapmachine-{version} has no {pkg.image} Windows MSI")
        return _release(pkg, rel, client)
    found: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        rels = client.get_json(github_api(f"repos/{REPO}/releases?per_page=100&page={page}")) or []
        found += [r for r in rels if _candidate(pkg, r)]
        if found or len(rels) < 100:
            break
    if not found:
        raise SourceError(f"no SapMachine {pkg.major} {pkg.image} Windows MSI release found")
    # Order on the raw tag numbers (any length); the winner must then map to a
    # package version (versioning.jdk_five_part), otherwise the package fails
    # rather than picking an older one.
    best = max(found, key=lambda r: _raw_key(r["tag_name"]))
    return _release(pkg, best, client)


def _raw_key(tag: str) -> tuple[int, ...]:
    parts = [int(p) for p in _TAG.match(tag)[1].split(".")]
    return tuple(parts + [0] * (8 - len(parts)))
