"""Amazon Corretto: version from GitHub, files and checksum from corretto.aws.

- Version: ``GET https://api.github.com/repos/corretto/corretto-<m>/releases/latest`` -> ``tag_name``.
- URL: ``https://corretto.aws/downloads/resources/<tag>/amazon-corretto-<tag>-windows-x64.msi``
  (Corretto 8: ``…-windows-x64-<jdk|jre>.msi``).
- Consistency: ``HEAD https://corretto.aws/downloads/latest/amazon-corretto-<m>-x64-windows-<jdk|jre>.msi``
  without following redirects must answer 302 with ``Location`` =
  ``/downloads/resources/<tag>/<same filename>``; otherwise fail (the latest
  link moved or the GitHub tag is out of step).
- sha256: ``GET https://corretto.aws/downloads/latest_sha256/amazon-corretto-<m>-x64-windows-<jdk|jre>.msi``
  (the versioned ``.sha256`` path answers 403, so it is not used). Guarded by
  the redirect check above.
- Version mapping: ``A.B.C.D.E`` -> ``A.B.C.<D><E>`` (``21.0.12.12.1`` -> ``21.0.12.121``).
"""

from __future__ import annotations

import urllib.parse

from .. import versioning
from ..http import Client
from ..manifest import Package
from . import Release, SourceError, github_api, no_pinned_version, require, sha256_file

BASE = "https://corretto.aws"


def normalize(tag: str) -> str:
    try:
        return versioning.corretto_tag(tag)
    except versioning.VersionError as exc:
        raise SourceError(str(exc)) from exc


def filename(pkg: Package, tag: str) -> str:
    if pkg.major == 8:
        return f"amazon-corretto-{tag}-windows-x64-{pkg.image}.msi"
    if pkg.image != "jdk":
        raise SourceError(f"Corretto {pkg.major} has no {pkg.image} MSI")
    return f"amazon-corretto-{tag}-windows-x64.msi"


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("corretto", version)
    if tuple(pkg.arch) != ("x64",):
        raise SourceError("Corretto packages are x64 only")
    latest = client.get_json(github_api(f"repos/corretto/corretto-{pkg.major}/releases/latest"))
    tag = str(require(latest.get("tag_name"), "tag_name")).strip()
    name = filename(pkg, tag)
    url = f"{BASE}/downloads/resources/{tag}/{name}"
    latest_name = f"amazon-corretto-{pkg.major}-x64-windows-{pkg.image}.msi"
    head = client.head(f"{BASE}/downloads/latest/{latest_name}", follow_redirects=False)
    location = head.header("location")
    if head.status != 302 or not location:
        raise SourceError(f"corretto.aws latest link did not redirect (HTTP {head.status})")
    if urllib.parse.urlsplit(urllib.parse.urljoin(BASE + "/", location)).path != f"/downloads/resources/{tag}/{name}":
        raise SourceError(f"corretto.aws latest points to {location}, GitHub tag is {tag}")
    sha = sha256_file(client, f"{BASE}/downloads/latest_sha256/{latest_name}", "corretto latest_sha256")
    return Release(
        version=normalize(tag),
        version_raw=tag,
        urls={"x64": url},
        sha256={"x64": sha},
        checksum_source="corretto.aws latest_sha256",
        raw={"tag_name": tag, "location": location},
    )
