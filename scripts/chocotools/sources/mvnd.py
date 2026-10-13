"""Apache Maven Daemon (mvnd) via GitHub releases.

- ``GET https://api.github.com/repos/apache/maven-mvnd/releases/latest`` -> tag (e.g. ``1.0.6``).
- Asset ``maven-mvnd-<tag>-windows-amd64.zip``: ``browser_download_url`` and ``digest``.
- ``dir_version`` (``resolve_extras``): the zip root itself
  (``maven-mvnd-<tag>-windows-amd64``), which the scripts use as a literal path.
- Version mapping: strip a leading ``v``.
"""

from __future__ import annotations

import re

from .. import versioning
from ..http import Client
from ..manifest import Package
from . import Release, SourceError, asset_sha256, find_asset, github_api, no_pinned_version, require

REPO = "apache/maven-mvnd"


def normalize(tag: str) -> str:
    """``1.0.6`` / ``v1.0.6`` -> ``1.0.6``."""
    try:
        return versioning.format(versioning.strip_v(tag.strip()))
    except versioning.VersionError as exc:
        raise SourceError(f"mvnd tag {tag!r}: {exc}") from exc


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("mvnd", version)
    if tuple(pkg.arch) != ("x64",):
        raise SourceError("mvnd packages are x64 only")
    rel = client.get_json(github_api(f"repos/{REPO}/releases/latest"))
    tag = str(require(rel.get("tag_name"), "tag_name"))
    asset = find_asset(rel, f"maven-mvnd-{versioning.strip_v(tag)}-windows-amd64.zip")
    sha, source = asset_sha256(client, rel, asset)
    return Release(
        version=normalize(tag),
        version_raw=tag,
        urls={"x64": require(asset.get("browser_download_url"), "browser_download_url")},
        sha256={"x64": sha},
        checksum_source=source,
        raw={"tag_name": tag},
    )


def dir_version(root: str) -> str:
    if not re.fullmatch(r"maven-mvnd-[0-9][0-9A-Za-z.\-]*?-windows-amd64", root):
        raise SourceError(f"unexpected mvnd zip root {root!r}")
    return root


def resolve_extras(pkg: Package, release: Release, client: Client) -> dict[str, str]:
    return {"dir_version": dir_version(client.zip_root_dir(release.urls["x64"]))}
