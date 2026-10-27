"""GraalVM Community: newest file from foojay, version and files from GitHub.

- File: ``GET https://api.foojay.io/disco/v3.0/packages?version=<m>&distribution=graalvm_community&architecture=amd64&archive_type=zip&operating_system=windows&package_type=jdk&latest=available``;
  only each record's ``filename`` is used. foojay's ``java_version`` and
  ``distribution_version`` are ignored: since 2026-10 it can list the same file
  twice with the two fields swapped (``25.4.4.1`` / ``25.0.4.1.1`` and
  ``25.0.4.1`` / ``25.4.4.1.1``). Records are de-duplicated by ``filename`` and
  the newest file is chosen by the GraalVM version in its name (``file_version``):
  ``graalvm-community-jdk-<M>i<I>-<M>.0.<rest>_windows-x64_bin.zip`` is
  ``<M>.<I>.<rest>`` (all parts, so a respin ``.1.2`` beats ``.1.1``), the older
  ``graalvm-community-jdk-<v>_windows-x64_bin.zip`` is ``<v>``. A file name in
  neither form, or two different file names tied for newest, -> fail.
  foojay URLs never reach package files.
- Download: the asset with exactly that filename in
  ``GET https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=40``;
  ``browser_download_url`` (github.com) and ``digest``. No asset -> fail.
- Version: ``versioning.url_version("graalvm", <download URL>)``, the rule
  ``checks.check_url_version`` applies, so sync and validate always agree:
  ``graal-25.4.4.1.1`` / ``25i4-25.0.4.1.1`` -> ``25.4.4.1`` (``versioning.graalvm_tag``,
  5th part dropped), ``jdk-17.0.9`` -> ``17.0.9``. It must equal the file name
  version cut to four parts, otherwise -> fail.
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
# Windows zips: graalvm-community-jdk-25i4-25.0.4.1.1_windows-x64_bin.zip, graalvm-community-jdk-25.0.2_windows-x64_bin.zip
_FILENAME = re.compile(r"graalvm-community-jdk-(?:(\d+)i(\d+)-)?(\d+(?:\.\d+)*)_windows-x64_bin\.zip")


def normalize(java_version: str) -> str:
    """``25.3.4.1`` -> ``25.3.4.1``; a ``+N`` suffix is stripped; max 4 parts."""
    text = versioning.strip_build(java_version.strip())
    try:
        return versioning.format(text)
    except versioning.VersionError as exc:
        raise SourceError(f"GraalVM java_version {java_version!r}: {exc}") from exc


def file_version(filename: str) -> tuple[int, ...]:
    """The GraalVM version in a Windows zip name, all parts (the selection key).

    ``...-25i4-25.0.4.1.1_windows-x64_bin.zip`` -> ``(25, 4, 4, 1, 1)``,
    ``...-25i3-25.0.4.1_...`` -> ``(25, 3, 4, 1)``, ``...-25.0.2_...`` -> ``(25, 0, 2)``.
    """
    m = _FILENAME.fullmatch(filename)
    if not m:
        raise SourceError(f"unexpected GraalVM file name {filename!r} "
                          "(expected graalvm-community-jdk-<version>_windows-x64_bin.zip)")
    major, iteration, asset = m[1], m[2], [int(p) for p in m[3].split(".")]
    if iteration is None:
        return tuple(asset)
    if asset[:2] != [int(major), 0] or len(asset) < 3:
        raise SourceError(f"GraalVM file name {filename!r} is not <M>i<I>-<M>.0.<update>")
    return (int(major), int(iteration), *asset[2:])


def _key(version: tuple[int, ...]) -> tuple[int, ...]:
    """Pad so ``25.0.2`` and ``25.0.2.0`` compare (and tie) as equal."""
    return version + (0,) * (versioning.MAX_PARTS + 1 - len(version))


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
        and e.get("filename")
    ]
    if not entries:
        raise SourceError(f"foojay lists no GraalVM Community {pkg.major} Windows zip")
    # one entry per file: foojay may list the same file twice with different version fields
    files = {e["filename"]: file_version(e["filename"]) for e in entries}
    newest = max(_key(v) for v in files.values())
    tied = sorted(f for f, v in files.items() if _key(v) == newest)
    if len(tied) > 1:
        raise SourceError(f"foojay lists more than one GraalVM file for the same version: {', '.join(tied)}")
    name = tied[0]
    expected = versioning.format(files[name][: versioning.MAX_PARTS])
    releases = client.get_json(github_api(f"repos/{REPO}/releases?per_page=40")) or []
    for rel in releases:
        if rel.get("draft"):
            continue
        try:
            asset = find_asset(rel, name)
        except SourceError:
            continue
        url = require(asset.get("browser_download_url"), "browser_download_url")
        try:
            version = versioning.url_version("graalvm", url)
        except versioning.VersionError as exc:
            raise SourceError(f"GraalVM release {rel.get('tag_name')!r} asset {name}: {exc}") from exc
        if version != expected:
            raise SourceError(f"GraalVM release {rel.get('tag_name')!r} maps to {version}, "
                              f"but its asset {name} is {expected}")
        sha, source = asset_sha256(client, rel, asset)
        return Release(
            version=version,
            version_raw=require(rel.get("tag_name"), "tag_name"),
            urls={"x64": url},
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
