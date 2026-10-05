"""Eclipse Temurin via the Adoptium API (replaces the old foojay lookup).

Query: ``GET https://api.adoptium.net/v3/assets/latest/<major>/hotspot?architecture=<x64|x86>&image_type=<jdk|jre>&os=windows&vendor=eclipse``
and use the entry that has ``binary.installer`` (MSI). URL is
``installer.link`` (github.com/adoptium), sha256 is ``installer.checksum``.

x86 is only queried when the manifest arch lists it, and it must carry the same
``release_name`` as x64, otherwise the package fails (no mixed builds).
"""

from __future__ import annotations

import re

from ..http import Client
from ..manifest import Package
from . import Release, SourceError, formatted, no_pinned_version, require, sha256_hex

API = "https://api.adoptium.net/v3"
_JDK8 = re.compile(r"^jdk8u(\d+)-b(\d+)$")
_JDK = re.compile(r"^jdk-(\d+(?:\.\d+)*)(?:\+\d+)?$")


def normalize(release_name: str) -> str:
    """``jdk8u504-b01`` -> ``8.504.1``; ``jdk-21.0.12.1+1`` -> ``21.0.12.1``."""
    m = _JDK8.match(release_name)
    if m:
        return formatted(f"8.{int(m[1])}.{int(m[2])}", "Temurin version")
    m = _JDK.match(release_name)
    if m:
        return formatted(m[1], "Temurin version")
    raise SourceError(f"unrecognized Temurin release name {release_name!r}")


def _installer(client: Client, pkg: Package, arch: str) -> tuple[str, dict]:
    url = (
        f"{API}/assets/latest/{pkg.major}/hotspot?architecture={arch}"
        f"&image_type={pkg.image}&os=windows&vendor=eclipse"
    )
    data = client.get_json(url)
    matches = []
    for entry in data or []:
        binary = entry.get("binary") or {}
        if (
            binary.get("installer")
            and binary.get("os") == "windows"
            and binary.get("architecture") == arch
            and binary.get("image_type") == pkg.image
            and binary.get("heap_size", "normal") == "normal"
        ):
            matches.append(entry)
    if not matches:
        raise SourceError(f"Adoptium has no {arch} {pkg.image} MSI for Temurin {pkg.major}")
    names = {m.get("release_name") for m in matches}
    if len(names) != 1:
        raise SourceError(f"Adoptium returned several releases for Temurin {pkg.major} {arch}: {sorted(names)}")
    entry = matches[0]
    return require(entry.get("release_name"), "release_name"), entry["binary"]["installer"]


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("temurin", version)
    urls: dict[str, str] = {}
    sums: dict[str, str] = {}
    names: dict[str, str] = {}
    raw = {}
    for arch in pkg.arch:
        if arch not in ("x64", "x86"):
            raise SourceError(f"Temurin does not support arch {arch}")
        name, installer = _installer(client, pkg, arch)
        names[arch] = name
        urls[arch] = require(installer.get("link"), f"{arch} installer.link")
        sums[arch] = sha256_hex(installer.get("checksum"), f"{arch} installer.checksum")
        raw[arch] = installer
    if len(set(names.values())) != 1:
        raise SourceError(f"x86 and x64 builds differ: {names}")
    release_name = next(iter(names.values()))
    return Release(
        version=normalize(release_name),
        version_raw=release_name,
        urls=urls,
        sha256=sums,
        checksum_source="adoptium installer.checksum",
        raw=raw,
    )
