"""Read a nuspec's metadata and rewrite single metadata elements in place.

Edits are byte-minimal: ``set_version`` changes only the text between the
first ``<version>`` and ``</version>`` inside ``<metadata>``. ``set_element``
replaces the text of one simple metadata element (``<name>text</name>`` or
``<name />``), or inserts ``<name>value</name>`` as a new line just before
``</metadata>``, indented like the line above it and ended with the file's
line ending. A UTF-8 BOM and the existing line endings are preserved because
nothing else is touched.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from xml.sax.saxutils import escape

BOM = b"\xef\xbb\xbf"
_METADATA = re.compile(r"<metadata\b[^>]*>")
_METADATA_END = re.compile(r"</metadata\s*>")
_VERSION = re.compile(r"(<version>)([^<]*)(</version>)")
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


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


def _encode(bom: bool, text: str) -> bytes:
    out = text.encode("utf-8")
    return (BOM + out) if bom else out


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def metadata(data: bytes) -> dict[str, str]:
    """Text of each ``<metadata>`` child, first occurrence per name (namespace-agnostic).

    Values are stripped; an element without text (e.g. ``<dependencies>``) is ''.
    """
    _, text = _decode(data)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise NuspecError(f"nuspec does not parse: {exc}") from exc
    meta = next((el for el in root if _local(el.tag) == "metadata"), None)
    if meta is None:
        raise NuspecError("nuspec has no <metadata>")
    values: dict[str, str] = {}
    for el in meta:
        values.setdefault(_local(el.tag), (el.text or "").strip())
    return values


def read(data: bytes) -> NuspecInfo:
    """Parse ``id`` and ``version`` (namespace-agnostic). Empty version is ''."""
    values = metadata(data)
    if "id" not in values:
        raise NuspecError("nuspec has no <id>")
    if "version" not in values:
        raise NuspecError("nuspec has no <version>")
    return NuspecInfo(id=values["id"], version=values["version"])


def _metadata_span(text: str) -> tuple[int, int]:
    """(end of ``<metadata>``, start of ``</metadata>``)."""
    meta = _METADATA.search(text)
    if meta is None:
        raise NuspecError("nuspec has no <metadata>")
    close = _METADATA_END.search(text, meta.end())
    if close is None:
        raise NuspecError("nuspec has no </metadata>")
    return meta.end(), close.start()


def set_version(data: bytes, version: str) -> bytes:
    """Return ``data`` with the metadata ``<version>`` replaced by ``version``."""
    if not version or "<" in version or "&" in version:
        raise NuspecError(f"refusing to write version {version!r}")
    bom, text = _decode(data)
    start, _ = _metadata_span(text)
    match = _VERSION.search(text, start)
    if match is None:
        raise NuspecError("nuspec has no <version> inside <metadata>")
    return _encode(bom, text[: match.start(2)] + version + text[match.end(2) :])


def set_element(data: bytes, name: str, value: str) -> bytes:
    """Return ``data`` with metadata element ``name`` set to ``value`` (XML-escaped).

    Replaces the text of the first ``<name>...</name>`` or ``<name />`` inside
    ``<metadata>``; inserts the element before ``</metadata>`` if there is none.
    Refuses empty values, line breaks and elements with attributes or children.
    """
    if not _NAME.match(name or ""):
        raise NuspecError(f"refusing to write element name {name!r}")
    if not value or not value.strip() or "\r" in value or "\n" in value:
        raise NuspecError(f"refusing to write <{name}> value {value!r}")
    escaped = escape(value)
    bom, text = _decode(data)
    start, end = _metadata_span(text)
    simple = re.compile(rf"<{name}\s*/>|<{name}>([^<]*)</{name}>")
    match = simple.search(text, start, end)
    if match is not None:
        new = text[: match.start()] + f"<{name}>{escaped}</{name}>" + text[match.end() :]
    elif re.compile(rf"<{name}[\s/>]").search(text, start, end):
        raise NuspecError(f"<{name}> is not a simple text element; refusing to edit it")
    else:
        line_start = text.rfind("\n", start, end) + 1
        if line_start and not text[line_start:end].strip():
            # </metadata> is on its own line: add a line above it, like the previous child.
            prev_start = text.rfind("\n", 0, line_start - 1) + 1
            prev = text[prev_start : line_start - 1]
            indent = prev[: len(prev) - len(prev.lstrip(" \t"))]
            eol = "\r\n" if text[line_start - 2 : line_start] == "\r\n" else "\n"
            new = text[:line_start] + f"{indent}<{name}>{escaped}</{name}>{eol}" + text[line_start:]
        else:
            new = text[:end] + f"<{name}>{escaped}</{name}>" + text[end:]
    out = _encode(bom, new)
    if metadata(out).get(name) != value.strip():
        raise NuspecError(f"<{name}> did not round-trip; refusing to write it")
    return out


def set_release_notes(data: bytes, url: str) -> bytes:
    """Return ``data`` with ``<releaseNotes>`` set to ``url``."""
    return set_element(data, "releaseNotes", url)
