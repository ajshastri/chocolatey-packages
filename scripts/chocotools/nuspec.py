"""Read a nuspec's id/version and rewrite ``<version>`` in place.

Edits are byte-minimal: only the text between the first ``<version>`` and
``</version>`` inside ``<metadata>`` changes. A UTF-8 BOM and the existing
line endings are preserved because nothing else is touched.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

BOM = b"\xef\xbb\xbf"
_METADATA = re.compile(r"<metadata\b[^>]*>")
_VERSION = re.compile(r"(<version>)([^<]*)(</version>)")


class NuspecError(Exception):
    """The nuspec could not be parsed or edited."""


@dataclass(frozen=True)
class NuspecInfo:
    id: str
    version: str


def _decode(data: bytes) -> tuple[bool, str]:
    bom = data.startswith(BOM)
    try:
        return bom, data[len(BOM) if bom else 0 :].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise NuspecError(f"nuspec is not UTF-8: {exc}") from exc


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def read(data: bytes) -> NuspecInfo:
    """Parse ``id`` and ``version`` (namespace-agnostic). Empty version is ''."""
    _, text = _decode(data)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise NuspecError(f"nuspec does not parse: {exc}") from exc
    metadata = next((el for el in root if _local(el.tag) == "metadata"), None)
    if metadata is None:
        raise NuspecError("nuspec has no <metadata>")
    values: dict[str, str] = {}
    for el in metadata:
        name = _local(el.tag)
        if name in ("id", "version") and name not in values:
            values[name] = (el.text or "").strip()
    if "id" not in values:
        raise NuspecError("nuspec has no <id>")
    if "version" not in values:
        raise NuspecError("nuspec has no <version>")
    return NuspecInfo(id=values["id"], version=values["version"])


def set_version(data: bytes, version: str) -> bytes:
    """Return ``data`` with the metadata ``<version>`` replaced by ``version``."""
    if not version or "<" in version or "&" in version:
        raise NuspecError(f"refusing to write version {version!r}")
    bom, text = _decode(data)
    meta = _METADATA.search(text)
    if meta is None:
        raise NuspecError("nuspec has no <metadata>")
    match = _VERSION.search(text, meta.end())
    if match is None:
        raise NuspecError("nuspec has no <version> inside <metadata>")
    new = text[: match.start(2)] + version + text[match.end(2) :]
    out = new.encode("utf-8")
    return (BOM + out) if bom else out
