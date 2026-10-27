"""The nuspec ``<releaseNotes>`` URL for a package version (Chocolatey rule CPMR0042).

Chocolatey accepts a URL to external release notes. ``url_for`` derives it
from the install-script download URL, with no network access, so sync can
write it with each version bump:

- temurin: ``https://adoptium.net/temurin/release-notes/?version=<tag>``
  (tag = the path segment after ``/releases/download/``)
- liberica: ``https://github.com/bell-sw/Liberica/releases/tag/<tag>``
- sapmachine: ``https://github.com/SAP/SapMachine/releases/tag/<tag>``
- graalvm: ``https://github.com/graalvm/graalvm-ce-builds/releases/tag/<tag>``
- wildfly: ``https://github.com/wildfly/wildfly/releases/tag/<tag>``
- mvnd: ``https://github.com/apache/maven-mvnd/releases/tag/<tag>``
- corretto: ``https://github.com/corretto/corretto-<major>/releases/tag/<tag>``
  (tag = the path segment after ``/downloads/resources/``). ``corretto.fetch``
  sets ``Release.release_notes_url`` to the CHANGELOG instead when GitHub has
  no release for the served tag yet.
- jmc: ``https://github.com/openjdk/jmc/releases/tag/<v>-ga`` (``v`` from ``/jmc-<v>_windows``)
- openjdk: ``https://jdk.java.net/<major>/release-notes``
- zulu: ``https://docs.azul.com/core/release-notes`` (Azul has no per-version page)
- lmc: ``https://bell-sw.com/liberica-mission-control/`` (no release-notes page exists)

The tag is URL-decoded (``+`` stays ``+``) and re-quoted with
``urllib.parse.quote(tag, safe="")``, so ``21.0.13.0.2+5`` and
``jdk-25.0.4.1%2B1`` both come out quoted (``%2B``). A URL without the
expected token raises ``ReleaseNotesError``, so sync fails closed.
"""

from __future__ import annotations

import re
import urllib.parse

from .manifest import Package

GITHUB_TAG = {
    "liberica": "https://github.com/bell-sw/Liberica/releases/tag/{tag}",
    "sapmachine": "https://github.com/SAP/SapMachine/releases/tag/{tag}",
    "graalvm": "https://github.com/graalvm/graalvm-ce-builds/releases/tag/{tag}",
    "wildfly": "https://github.com/wildfly/wildfly/releases/tag/{tag}",
    "mvnd": "https://github.com/apache/maven-mvnd/releases/tag/{tag}",
}
TEMURIN = "https://adoptium.net/temurin/release-notes/?version={tag}"
CORRETTO = "https://github.com/corretto/corretto-{major}/releases/tag/{tag}"
CORRETTO_CHANGELOG = "https://github.com/corretto/corretto-{major}/blob/develop/CHANGELOG.md"
JMC = "https://github.com/openjdk/jmc/releases/tag/{tag}"
OPENJDK = "https://jdk.java.net/{major}/release-notes"
STATIC = {
    "zulu": "https://docs.azul.com/core/release-notes",
    "lmc": "https://bell-sw.com/liberica-mission-control/",
}
_JMC_FILE = re.compile(r"^jmc-(\d[^/_]*)_windows")


class ReleaseNotesError(ValueError):
    """No release-notes URL can be derived for this package and download URL."""


def _segment_after(url: str, marker: str) -> str:
    """The URL-decoded path segment that follows ``marker``."""
    path = urllib.parse.urlsplit(url).path
    _, found, rest = path.partition(marker)
    tag = urllib.parse.unquote(rest.split("/", 1)[0]) if found else ""
    if not tag:
        raise ReleaseNotesError(f"no tag after {marker!r} in {url}")
    return tag


def _quote(tag: str) -> str:
    return urllib.parse.quote(tag, safe="")


def _major(pkg: Package) -> int:
    if not pkg.major:
        raise ReleaseNotesError(f"{pkg.id}: vendor {pkg.vendor} needs a major version")
    return pkg.major


def url_for(pkg: Package, download_url: str) -> str:
    """The release-notes URL for the version that ``download_url`` installs."""
    vendor = pkg.vendor
    if vendor in STATIC:
        return STATIC[vendor]
    if vendor == "openjdk":
        return OPENJDK.format(major=_major(pkg))
    if vendor == "temurin":
        return TEMURIN.format(tag=_quote(_segment_after(download_url, "/releases/download/")))
    if vendor in GITHUB_TAG:
        return GITHUB_TAG[vendor].format(tag=_quote(_segment_after(download_url, "/releases/download/")))
    if vendor == "corretto":
        tag = _segment_after(download_url, "/downloads/resources/")
        return CORRETTO.format(major=_major(pkg), tag=_quote(tag))
    if vendor == "jmc":
        name = urllib.parse.unquote(urllib.parse.urlsplit(download_url).path.rsplit("/", 1)[-1])
        match = _JMC_FILE.match(name)
        if not match:
            raise ReleaseNotesError(f"no jmc-<version>_windows file name in {download_url}")
        return JMC.format(tag=_quote(match.group(1) + "-ga"))
    raise ReleaseNotesError(f"no release-notes rule for vendor {vendor!r}")
