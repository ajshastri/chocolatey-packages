"""OpenJDK GA builds from jdk.java.net.

- ``GET https://jdk.java.net/<m>/``; the ``<h1>`` must contain ``GA Release``.
- URL: the href ``https://download.java.net/java/GA/jdk<m>…/GPL/openjdk-<v>_windows-x64_bin.zip``.
- sha256: ``<href>.sha256``.
- ``dir_version`` (``resolve_extras``): zip root minus ``jdk-``, used by
  ``$version`` in the install, uninstall and beforeModify scripts.
- Version mapping: ``27`` -> ``27.0.0``; ``26.0.2.1`` stays.
"""

from __future__ import annotations

import html
import re

from .. import versioning
from ..http import Client
from ..manifest import Package
from . import Release, SourceError, no_pinned_version, sha256_file

PAGE = "https://jdk.java.net/{major}/"
_H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)


def _href(major: int) -> re.Pattern:
    return re.compile(
        r"https://download\.java\.net/java/GA/jdk" + str(major)
        + r"[^\"'\s<>]*/GPL/openjdk-(?P<v>[\d.]+)_windows-x64_bin\.zip(?=[\"'])"
    )


def normalize(version: str) -> str:
    try:
        return versioning.format(versioning.strip_build(version.strip()))
    except versioning.VersionError as exc:
        raise SourceError(f"OpenJDK version {version!r}: {exc}") from exc


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("openjdk", version)
    if tuple(pkg.arch) != ("x64",):
        raise SourceError("OpenJDK packages are x64 only")
    page = client.get_text(PAGE.format(major=pkg.major))
    h1 = _H1.search(page)
    if not h1 or "GA Release" not in html.unescape(h1.group(1)):
        raise SourceError(f"jdk.java.net/{pkg.major} is not a GA release page")
    matches = {m.group(0): m["v"] for m in _href(pkg.major).finditer(page)}
    if len(matches) != 1:
        raise SourceError(f"expected one Windows x64 zip on jdk.java.net/{pkg.major}, found {len(matches)}")
    url, raw = next(iter(matches.items()))
    sha = sha256_file(client, url + ".sha256", "OpenJDK .sha256")
    return Release(
        version=normalize(raw),
        version_raw=raw,
        urls={"x64": url},
        sha256={"x64": sha},
        checksum_source="jdk.java.net .sha256",
        raw={"h1": h1.group(1).strip()},
    )


def dir_version(root: str) -> str:
    if not re.fullmatch(r"jdk-[0-9][0-9A-Za-z.+_-]*", root):
        raise SourceError(f"unexpected OpenJDK zip root {root!r}")
    return root[len("jdk-") :]


def resolve_extras(pkg: Package, release: Release, client: Client) -> dict[str, str]:
    return {"dir_version": dir_version(client.zip_root_dir(release.urls["x64"]))}
