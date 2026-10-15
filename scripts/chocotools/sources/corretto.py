"""Amazon Corretto: the build corretto.aws serves as latest, cross-checked with GitHub.

- Served build (authoritative): ``HEAD https://corretto.aws/downloads/latest/amazon-corretto-<m>-x64-windows-<jdk|jre>.msi``
  without following redirects must answer 302 with ``Location`` =
  ``/downloads/resources/<tag>/<filename for that tag>``; otherwise fail.
- URL: ``https://corretto.aws/downloads/resources/<tag>/amazon-corretto-<tag>-windows-x64.msi``
  (Corretto 8: ``…-windows-x64-<jdk|jre>.msi``), ``<tag>`` from the redirect.
- sha256: ``GET https://corretto.aws/downloads/latest_sha256/amazon-corretto-<m>-x64-windows-<jdk|jre>.msi``
  (the versioned ``.sha256`` path answers 403, so it is not used). It describes
  the same served build as the redirect.
- GitHub hint: ``GET https://api.github.com/repos/corretto/corretto-<m>/releases/latest`` -> ``tag_name``.
  Equal to the served tag: a normal release. Newer: the release carries
  ``pending`` (GitHub tag, ``published_at``, HTTP status of the tag's MSI URL);
  GitHub tags can be fixes for other platforms that never get a Windows MSI, so
  ``sync`` waits instead of failing (see ``sources.PENDING_ESCALATION_DAYS``).
  Older than the served tag: the served build is used, with a note.
- Version mapping: ``A.B.C.D.E`` -> ``A.B.C.<D><E>`` (``21.0.12.12.1`` -> ``21.0.12.121``).
"""

from __future__ import annotations

import urllib.parse

from .. import versioning
from ..http import Client, HttpError
from ..manifest import Package
from . import (
    Pending,
    Release,
    SourceError,
    github_api,
    no_pinned_version,
    parse_timestamp,
    require,
    sha256_file,
)

BASE = "https://corretto.aws"
RESOURCES = "/downloads/resources/"


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


def served_tag(pkg: Package, location: str) -> str | None:
    """The tag in a latest-link ``Location`` of the form ``/downloads/resources/<tag>/<filename>``."""
    path = urllib.parse.urlsplit(urllib.parse.urljoin(BASE + "/", location)).path
    if not path.startswith(RESOURCES):
        return None
    tag, sep, name = path[len(RESOURCES):].partition("/")
    if not sep or not tag or name != filename(pkg, tag):
        return None
    return tag


def msi_status(client: Client, url: str) -> str:
    """HTTP status of a versioned MSI URL, for the pending message."""
    try:
        return str(client.head(url, follow_redirects=False).status)
    except HttpError as exc:
        return str(exc.status) if exc.status else "unreachable"


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("corretto", version)
    if tuple(pkg.arch) != ("x64",):
        raise SourceError("Corretto packages are x64 only")
    latest = client.get_json(github_api(f"repos/corretto/corretto-{pkg.major}/releases/latest"))
    github_tag = str(require(latest.get("tag_name"), "tag_name")).strip()
    latest_name = f"amazon-corretto-{pkg.major}-x64-windows-{pkg.image}.msi"
    head = client.head(f"{BASE}/downloads/latest/{latest_name}", follow_redirects=False)
    location = head.header("location")
    if head.status != 302 or not location:
        raise SourceError(f"corretto.aws latest link did not redirect (HTTP {head.status})")
    tag = served_tag(pkg, location)
    if tag is None:
        raise SourceError(f"corretto.aws latest points to {location}, not a {pkg.image} MSI under {RESOURCES}")
    pending = None
    notes = []
    if tag != github_tag and versioning.compare_nuget(normalize(github_tag), normalize(tag)) <= 0:
        # GitHub is only a hint: a release it has not caught up with is still the served build.
        notes.append(f"GitHub latest tag {github_tag} is behind corretto.aws latest {tag}")
    elif tag != github_tag:
        # GitHub is ahead of corretto.aws: wait for the latest link (which may never move,
        # if the tag only fixes another platform).
        status = msi_status(client, f"{BASE}{RESOURCES}{github_tag}/{filename(pkg, github_tag)}")
        pending = Pending(
            version_raw=github_tag,
            published_at=parse_timestamp(latest.get("published_at"), "GitHub release published_at"),
            detail=f"corretto.aws latest still serves {tag} (versioned MSI HTTP {status})",
        )
    sha = sha256_file(client, f"{BASE}/downloads/latest_sha256/{latest_name}", "corretto latest_sha256")
    return Release(
        version=normalize(tag),
        version_raw=tag,
        urls={"x64": f"{BASE}{RESOURCES}{tag}/{filename(pkg, tag)}"},
        sha256={"x64": sha},
        checksum_source="corretto.aws latest_sha256",
        raw={"github_tag": github_tag, "served_tag": tag, "location": location},
        pending=pending,
        notes=notes,
    )
