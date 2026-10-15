"""Chocolatey community feed (OData v2) client.

Query: ``https://community.chocolatey.org/api/v2/FindPackagesById()?id='<id>'``,
following ``<link rel="next">`` pages. Returns the highest NuGet version whose
``d:IsApproved`` is ``true``. Rejected versions are not listed by the feed.
Requests go through ``http.Client`` (>= 1.1 s apart for this host; 429/5xx,
timeouts and connection errors are retried with backoff for up to
``http.FEED_RETRY_BUDGET`` per request, then the client stops asking the feed).
"""

from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET

from . import versioning
from .http import Client, HttpError, default_client

FEED = "https://community.chocolatey.org/api/v2/"
PACKAGES = "https://community.chocolatey.org/packages/"
MAX_PAGES = 50


class ChocolateyError(Exception):
    """The feed could not be read or parsed."""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def feed_url(package_id: str) -> str:
    return FEED + "FindPackagesById()?id=" + urllib.parse.quote(f"'{package_id}'")


def parse_page(data: bytes) -> tuple[list[tuple[str, bool]], str | None]:
    """Return ([(version, approved), ...], next_url) for one Atom page."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ChocolateyError(f"feed does not parse: {exc}") from exc
    entries: list[tuple[str, bool]] = []
    next_url = None
    for child in root:
        name = _local(child.tag)
        if name == "link" and child.get("rel") == "next":
            next_url = child.get("href")
        elif name == "entry":
            props = next((el for el in child.iter() if _local(el.tag) == "properties"), None)
            if props is None:
                continue
            values = {_local(el.tag): (el.text or "").strip() for el in props}
            version = values.get("Version", "")
            approved = values.get("IsApproved", "").lower() == "true"
            if version:
                entries.append((version, approved))
    return entries, next_url


def package_page(package_id: str, version: str) -> str:
    return f"{PACKAGES}{urllib.parse.quote(package_id)}/{urllib.parse.quote(version)}"


def versions(package_id: str, client: Client | None = None, *, fresh: bool = False) -> list[tuple[str, bool]]:
    """Every listed (version, approved) pair. ``fresh`` skips this run's cached pages."""
    client = client or default_client()
    url: str | None = feed_url(package_id)
    out: list[tuple[str, bool]] = []
    # The memo/disk cache is keyed by URL and headers, so a different header set reads the feed again.
    headers = {"Cache-Control": "no-cache"} if fresh else None
    for _ in range(MAX_PAGES):
        if url is None:
            return out
        try:
            data = client.get_bytes(url, headers=headers)
        except HttpError as exc:
            raise ChocolateyError(f"Chocolatey feed unreachable for {package_id}: {exc}") from exc
        page, url = parse_page(data)
        out.extend(page)
    raise ChocolateyError(f"Chocolatey feed for {package_id} has more than {MAX_PAGES} pages")


def has_version(package_id: str, version: str, client: Client | None = None) -> bool:
    """True if the feed lists ``package_id`` ``version`` (approved or not) or its package page exists.

    Used after a push retry hit a conflict, to confirm an earlier attempt went through.
    """
    client = client or default_client()
    try:
        if any(versioning.is_valid(v) and versioning.compare_nuget(v, version) == 0
               for v, _ in versions(package_id, client, fresh=True)):
            return True
    except ChocolateyError:
        pass  # fall back to the package page
    try:
        # No redirects: a redirect to another version's page must not count.
        return client.head(package_page(package_id, version), follow_redirects=False).status == 200
    except HttpError:
        return False


def approved_version(package_id: str, client: Client | None = None) -> str | None:
    """Highest approved version, or None if the package has no approved version."""
    best: str | None = None
    for version, approved in versions(package_id, client):
        if not approved or not versioning.is_valid(version):
            continue  # skip unapproved and prerelease/non-numeric versions
        if best is None or versioning.compare_nuget(version, best) > 0:
            best = version
    return best
