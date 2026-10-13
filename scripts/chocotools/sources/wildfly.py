"""WildFly via GitHub releases.

- ``GET https://api.github.com/repos/wildfly/wildfly/releases/latest`` -> tag (e.g. ``41.0.1.Final``).
- Asset ``wildfly-<tag>.zip``: ``browser_download_url`` and ``digest``.
- Arch is ``neutral`` (the install script uses ``Url``/``Checksum``).
- ``dir_version`` (``resolve_extras``): zip root minus ``wildfly-``, used by
  ``$version`` in the uninstall script.
- Version mapping: strip ``.Final``.
"""

from __future__ import annotations

import re

from .. import versioning
from ..http import Client
from ..manifest import Package
from . import Release, SourceError, asset_sha256, find_asset, github_api, no_pinned_version, require

REPO = "wildfly/wildfly"


def normalize(tag: str) -> str:
    """``41.0.1.Final`` -> ``41.0.1``."""
    try:
        return versioning.format(versioning.strip_final(tag.strip()))
    except versioning.VersionError as exc:
        raise SourceError(f"WildFly tag {tag!r}: {exc}") from exc


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("wildfly", version)
    if tuple(pkg.arch) != ("neutral",):
        raise SourceError("WildFly packages use arch 'neutral'")
    rel = client.get_json(github_api(f"repos/{REPO}/releases/latest"))
    tag = str(require(rel.get("tag_name"), "tag_name"))
    asset = find_asset(rel, f"wildfly-{tag}.zip")
    sha, source = asset_sha256(client, rel, asset)
    return Release(
        version=normalize(tag),
        version_raw=tag,
        urls={"neutral": require(asset.get("browser_download_url"), "browser_download_url")},
        sha256={"neutral": sha},
        checksum_source=source,
        raw={"tag_name": tag},
    )


def dir_version(root: str) -> str:
    if not re.fullmatch(r"wildfly-[0-9][0-9A-Za-z._-]*", root):
        raise SourceError(f"unexpected WildFly zip root {root!r}")
    return root[len("wildfly-") :]


def resolve_extras(pkg: Package, release: Release, client: Client) -> dict[str, str]:
    return {"dir_version": dir_version(client.zip_root_dir(release.urls["neutral"]))}
