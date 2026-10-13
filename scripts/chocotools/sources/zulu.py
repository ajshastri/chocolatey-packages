"""Azul Zulu via the Azul metadata API (same query as the old zulu-sync.sh).

List: ``GET https://api.azul.com/metadata/v1/zulu/packages/?java_version=<m>&os=windows&arch=x64&archive_type=msi&java_package_type=jdk&javafx_bundled=true&latest=true&distro_version=<m>&release_status=ga&crac_supported=false&availability_types=CA&certifications=tck&page=1&page_size=1``
then ``GET https://api.azul.com/metadata/v1/zulu/packages/<package_uuid>`` for
``sha256_hash``, ``download_url`` (cdn.azul.com) and ``distro_version``.

Zulu 7 (frozen; compare only) has no JavaFX/TCK/CRaC metadata, so its query
uses ``javafx_bundled=false`` and drops ``distro_version``, ``crac_supported``
and ``certifications``.
"""

from __future__ import annotations

from .. import versioning
from ..http import Client
from ..manifest import Package
from . import Release, SourceError, formatted, no_pinned_version, require, sha256_hex

API = "https://api.azul.com/metadata/v1/zulu/packages/"


def normalize(distro_version: list[int]) -> str:
    """``[21, 52, 203, 0]`` -> ``21.52.203``."""
    return formatted(versioning.join_parts(require(distro_version, "distro_version")), "Zulu distro_version")


def list_url(major: int) -> str:
    if major == 7:
        return (
            f"{API}?java_version=7&os=windows&arch=x64&archive_type=msi&java_package_type=jdk"
            f"&javafx_bundled=false&latest=true&release_status=ga&availability_types=CA&page=1&page_size=1"
        )
    return (
        f"{API}?java_version={major}&os=windows&arch=x64&archive_type=msi&java_package_type=jdk"
        f"&javafx_bundled=true&latest=true&distro_version={major}&release_status=ga"
        f"&crac_supported=false&availability_types=CA&certifications=tck&page=1&page_size=1"
    )


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    no_pinned_version("zulu", version)
    if tuple(pkg.arch) != ("x64",):
        raise SourceError("Zulu packages are x64 only")
    if pkg.image != "jdk":
        raise SourceError("only Zulu JDK packages are supported")
    listing = client.get_json(list_url(pkg.major)) or []
    if not listing:
        raise SourceError(f"Azul returned no package for Zulu {pkg.major}")
    uuid = require(listing[0].get("package_uuid"), "package_uuid")
    detail = client.get_json(API + uuid)
    raw = require(detail.get("distro_version"), "distro_version")
    url = require(detail.get("download_url"), "download_url")
    if not str(url).endswith(".msi"):
        raise SourceError(f"unexpected Zulu download {url}")
    return Release(
        version=normalize(raw),
        version_raw=versioning.join_parts(raw),
        urls={"x64": url},
        sha256={"x64": sha256_hex(detail.get("sha256_hash"), "sha256_hash")},
        checksum_source="azul sha256_hash",
        raw={"package_uuid": uuid, "name": detail.get("name")},
    )
