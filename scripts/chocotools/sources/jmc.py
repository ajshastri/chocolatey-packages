"""JDK Mission Control: version from ``openjdk/jmc`` tags, files from jdk.java.net.

- Version: ``GET https://api.github.com/repos/openjdk/jmc/tags?per_page=100``;
  the max tag matching ``^<m>\\.\\d+\\.\\d+-ga$``.
- URL: on ``https://jdk.java.net/jmc/<m>/`` the href
  ``https://download.java.net/java/GA/jmc<m>/…/jmc-<v>_windows-x64.zip``. Its
  ``<v>`` must equal the tag version, else fail ("download page not updated
  yet"). This keeps the current download host.
- sha256: ``<href>.sha256``.
- Version mapping: strip ``-ga``.
"""

from __future__ import annotations

import re

from .. import versioning
from ..http import Client
from ..manifest import Package
from . import Release, SourceError, github_api, no_pinned_version, sha256_file

PAGE = "https://jdk.java.net/jmc/{major}/"


def normalize(tag: str) -> str:
    """``9.1.2-ga`` -> ``9.1.2``."""
    try:
        return versioning.format(versioning.strip_ga(tag.strip()))
    except versioning.VersionError as exc:
        raise SourceError(f"JMC tag {tag!r}: {exc}") from exc


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("jmc", version)
    if tuple(pkg.arch) != ("x64",):
        raise SourceError("JMC packages are x64 only")
    tag_re = re.compile(rf"^{pkg.major}\.\d+\.\d+-ga$")
    tags = [t.get("name", "") for t in client.get_json(github_api("repos/openjdk/jmc/tags?per_page=100")) or []]
    tags = [t for t in tags if tag_re.match(t)]
    if not tags:
        raise SourceError(f"no openjdk/jmc tag matches {pkg.major}.x.y-ga")
    tag = max(tags, key=lambda t: versioning.parse(normalize(t)) + (0,) * 4)
    version_tag = versioning.strip_ga(tag)
    page = client.get_text(PAGE.format(major=pkg.major))
    href = re.compile(
        r"https://download\.java\.net/java/GA/jmc" + str(pkg.major)
        + r"/[^\"'\s<>]*/jmc-(?P<v>[\d.]+)_windows-x64\.zip(?=[\"'])"
    )
    links = {m.group(0): m["v"] for m in href.finditer(page)}
    if len(links) != 1:
        raise SourceError(f"expected one Windows x64 zip on jdk.java.net/jmc/{pkg.major}, found {len(links)}")
    url, page_version = next(iter(links.items()))
    if page_version != version_tag:
        raise SourceError(
            f"download page not updated yet: jdk.java.net has {page_version}, latest tag is {tag}"
        )
    return Release(
        version=normalize(tag),
        version_raw=tag,
        urls={"x64": url},
        sha256={"x64": sha256_file(client, url + ".sha256", "JMC .sha256")},
        checksum_source="jdk.java.net .sha256",
        raw={"tag": tag},
    )
