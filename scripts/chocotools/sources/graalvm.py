"""GraalVM Community: version from foojay, files from GitHub.

- Version: ``GET https://api.foojay.io/disco/v3.0/packages?version=<m>&distribution=graalvm_community&architecture=amd64&archive_type=zip&operating_system=windows&package_type=jdk&latest=available``;
  the max ``java_version`` (4-part, e.g. ``25.3.4.1``) and its ``filename``.
  foojay is used for the version only; its URLs never reach package files.
- Download: the asset with exactly that filename in
  ``GET https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=40``;
  ``browser_download_url`` (github.com) and ``digest``. No asset -> fail.
- ``dir_version`` (``resolve_extras``): the zip root directory itself, written
  to ``$graalvmDir`` in the install and uninstall scripts. Both layouts are
  accepted: ``graalvm-community-openjdk-<v>`` (up to 25.0.2) and
  ``graalvm-community-<v>`` (25i3 onwards, e.g. ``graalvm-community-25.3.4.1+1.1``).
"""

from __future__ import annotations

import re

from .. import versioning
from ..http import Client
from ..manifest import Package
from . import Release, SourceError, asset_sha256, find_asset, github_api, no_pinned_version, require

FOOJAY = "https://api.foojay.io/disco/v3.0/packages"
REPO = "graalvm/graalvm-ce-builds"
# Zip root layouts: graalvm-community-openjdk-25.0.2+10.1, graalvm-community-25.3.4.1+1.1
_DIR_ROOT = re.compile(r"graalvm-community-(?:openjdk-)?[0-9][0-9A-Za-z.+_-]*")


def normalize(java_version: str) -> str:
    """``25.3.4.1`` -> ``25.3.4.1``; a ``+N`` suffix is stripped; max 4 parts."""
    text = versioning.strip_build(java_version.strip())
    try:
        return versioning.format(text)
    except versioning.VersionError as exc:
        raise SourceError(f"GraalVM java_version {java_version!r}: {exc}") from exc


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("graalvm", version)
    if tuple(pkg.arch) != ("x64",):
        raise SourceError("GraalVM packages are x64 only")
    url = (
        f"{FOOJAY}?version={pkg.major}&distribution=graalvm_community&architecture=amd64"
        f"&archive_type=zip&operating_system=windows&package_type=jdk&latest=available"
    )
    result = (client.get_json(url) or {}).get("result") or []
    entries = [
        e
        for e in result
        if e.get("major_version") == pkg.major
        and e.get("release_status") == "ga"
        and e.get("operating_system") == "windows"
        and e.get("archive_type") == "zip"
        and e.get("java_version")
        and e.get("filename")
    ]
    if not entries:
        raise SourceError(f"foojay lists no GraalVM Community {pkg.major} Windows zip")
    best = max(entries, key=lambda e: versioning.parse(normalize(e["java_version"])) + (0,) * 4)
    name = best["filename"]
    releases = client.get_json(github_api(f"repos/{REPO}/releases?per_page=40")) or []
    for rel in releases:
        if rel.get("draft"):
            continue
        try:
            asset = find_asset(rel, name)
        except SourceError:
            continue
        sha, source = asset_sha256(client, rel, asset)
        return Release(
            version=normalize(best["java_version"]),
            version_raw=best["java_version"],
            urls={"x64": require(asset.get("browser_download_url"), "browser_download_url")},
            sha256={"x64": sha},
            checksum_source=source,
            raw={"filename": name, "tag_name": rel.get("tag_name")},
        )
    raise SourceError(f"no {REPO} release has asset {name}")


def dir_version(root: str) -> str:
    """The install folder name: the zip root itself (either layout)."""
    if not _DIR_ROOT.fullmatch(root):
        raise SourceError(
            f"unexpected GraalVM zip root {root!r} "
            "(expected graalvm-community-<version> or graalvm-community-openjdk-<version>)"
        )
    return root


def resolve_extras(pkg: Package, release: Release, client: Client) -> dict[str, str]:
    return {"dir_version": dir_version(client.zip_root_dir(release.urls["x64"]))}
