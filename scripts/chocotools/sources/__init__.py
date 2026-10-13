"""Upstream release sources, one module per vendor.

Each vendor module exposes:

- ``fetch(pkg, *, version=None, client=None) -> Release``: query the vendor and
  return the latest (or pinned) release. Raises ``SourceError`` when nothing
  matches or a field is missing/empty (fail closed).
- ``normalize(raw) -> str``: pure mapping from the vendor's version string to
  the package version (unit tested with real values).
- optionally ``resolve_extras(pkg, release, client) -> dict``: values that need
  extra network work (zip root directory) and are only computed when sync is
  about to write a new version.
"""

from __future__ import annotations

import importlib
import re
import urllib.parse
from dataclasses import dataclass, field
from types import ModuleType

from ..http import Client, HttpError, default_client
from ..manifest import Package
from ..versioning import VersionError

VENDOR_MODULES = (
    "temurin",
    "liberica",
    "sapmachine",
    "zulu",
    "corretto",
    "graalvm",
    "openjdk",
    "wildfly",
    "mvnd",
    "jmc",
    "lmc",
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class SourceError(Exception):
    """The upstream source returned nothing usable for this package."""


class SourceUnsupported(SourceError):
    """There is no machine-readable source for this package."""


@dataclass
class Release:
    version: str  # normalized package version
    version_raw: str  # as published upstream
    urls: dict[str, str]  # arch -> URL
    sha256: dict[str, str]  # arch -> lowercase hex
    checksum_source: str  # where the checksum came from
    extras: dict[str, str] = field(default_factory=dict)  # e.g. dir_version
    raw: object = None


def module(vendor: str) -> ModuleType:
    if vendor not in VENDOR_MODULES:
        raise SourceError(f"unknown vendor {vendor!r}")
    return importlib.import_module(f"{__name__}.{vendor}")


def fetch(pkg: Package, *, version: str | None = None, client: Client | None = None) -> Release:
    try:
        return module(pkg.vendor).fetch(pkg, version=version, client=client or default_client())
    except (HttpError, VersionError) as exc:
        raise SourceError(f"{pkg.vendor}: {exc}") from exc
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        # Unexpected response shape: fail closed with a clear message.
        raise SourceError(f"{pkg.vendor}: unexpected response ({type(exc).__name__}: {exc})") from exc


def resolve_extras(pkg: Package, release: Release, client: Client | None = None) -> dict[str, str]:
    mod = module(pkg.vendor)
    hook = getattr(mod, "resolve_extras", None)
    if hook is None:
        return {}
    try:
        return hook(pkg, release, client or default_client())
    except (HttpError, VersionError) as exc:
        raise SourceError(f"{pkg.vendor}: {exc}") from exc


# ----- shared helpers --------------------------------------------------------


def formatted(text: str, what: str = "version") -> str:
    """``versioning.format`` that raises SourceError (fail closed)."""
    from .. import versioning

    try:
        return versioning.format(text)
    except VersionError as exc:
        raise SourceError(f"{what} {text!r}: {exc}") from exc


def require(value, what: str):
    """Return ``value`` or raise SourceError if it is None/empty."""
    if value is None or (isinstance(value, (str, list, dict)) and not value):
        raise SourceError(f"{what} is missing or empty")
    return value


def sha256_hex(value, what: str) -> str:
    text = str(require(value, what)).strip().lower()
    if not _HEX64.match(text):
        raise SourceError(f"{what} is not a sha256 hex digest: {value!r}")
    return text


def no_pinned_version(vendor: str, version: str | None) -> None:
    if version is not None:
        raise SourceUnsupported(f"{vendor}: fetching a pinned version is not supported")


def sha256_file(client: Client, url: str, what: str) -> str:
    """Download a ``.sha256``-style file and return its first token."""
    text = client.get_text(url).strip()
    return sha256_hex(text.split()[0] if text else "", what)


def github_api(path: str) -> str:
    return "https://api.github.com/" + path.lstrip("/")


def github_release_by_tag(client: Client, repo: str, tag: str) -> dict:
    return client.get_json(github_api(f"repos/{repo}/releases/tags/{urllib.parse.quote(tag, safe='')}"))


def find_asset(release: dict, name: str) -> dict:
    for asset in release.get("assets") or []:
        if asset.get("name") == name:
            return asset
    raise SourceError(f"release {release.get('tag_name')!r} has no asset {name!r}")


def asset_sha256(client: Client, release: dict, asset: dict) -> tuple[str, str]:
    """sha256 for a GitHub release asset: ``digest``, else a .sha256/.sha256.txt
    asset, else a streamed download. Returns (hex, source description)."""
    digest = asset.get("digest")
    if digest:
        algo, _, value = str(digest).partition(":")
        if algo != "sha256":
            raise SourceError(f"asset {asset.get('name')} digest is {algo}, not sha256")
        return sha256_hex(value, f"digest of {asset.get('name')}"), "github asset digest"
    for suffix in (".sha256", ".sha256.txt"):
        try:
            side = find_asset(release, asset["name"] + suffix)
        except SourceError:
            continue
        url = require(side.get("browser_download_url"), "checksum asset URL")
        return sha256_file(client, url, f"{side['name']}"), f"github asset {side['name']}"
    url = require(asset.get("browser_download_url"), "asset URL")
    return sha256_hex(client.sha256_of(url), f"download of {asset.get('name')}"), "computed from download"
