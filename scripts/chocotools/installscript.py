"""Read and rewrite URL/checksum fields and install-directory tokens in ``tools\\*.ps1``.

Only quoted single-line assignments are recognized (``Key = 'value'`` or
``$var = "value"``). Edits replace just the text between the quotes, so key
casing, quote style, spacing, a UTF-8 BOM and CRLF line endings are kept.
Unquoted values (``url64bit = $url64``) are references and are ignored.

Variable styles found in this repo:

=====  ==========================  ==========================  ===========================
Style  x64 URL                     x86 / neutral URL           checksum keys
=====  ==========================  ==========================  ===========================
A      ``Url64bit = '...'``        --                          Checksum64, ChecksumType64
A+x86  ``Url64bit``                ``Url = '...'``             + Checksum, ChecksumType
B      ``Url64 = '...'``           --                          Checksum64, ChecksumType64
C      --                          ``Url = '...'`` (neutral)   Checksum, ChecksumType
D      top-level ``$url64 = '..'`` --                          checksum64, checksumType64
=====  ==========================  ==========================  ===========================

Logical field names used by callers: ``url64``, ``checksum64``,
``checksumtype64`` (x64) and ``url``, ``checksum``, ``checksumtype`` (x86 or
neutral). Keys match case-insensitively; a leading ``$`` is allowed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

BOM = b"\xef\xbb\xbf"

ALIASES: dict[str, tuple[str, ...]] = {
    "url64": ("url64bit", "url64"),
    "checksum64": ("checksum64",),
    "checksumtype64": ("checksumtype64",),
    "url": ("url",),
    "checksum": ("checksum",),
    "checksumtype": ("checksumtype",),
}
ARCH_FIELDS: dict[str, tuple[str, str, str]] = {
    "x64": ("url64", "checksum64", "checksumtype64"),
    "x86": ("url", "checksum", "checksumtype"),
    "neutral": ("url", "checksum", "checksumtype"),
}
_KEY_TO_LOGICAL = {alias: logical for logical, names in ALIASES.items() for alias in names}

_ASSIGN = re.compile(
    r"^[ \t]*(?P<dollar>\$?)(?P<key>[A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*"
    r"(?P<q>['\"])(?P<value>[^'\"\r\n]*)(?P=q)",
    re.MULTILINE,
)
_MVND_DIR = re.compile(r"(?<!/)maven-mvnd-[0-9][0-9A-Za-z.\-]*?-windows-amd64")


class ScriptError(Exception):
    """A required field is missing, duplicated, or cannot be edited."""


@dataclass(frozen=True)
class Assignment:
    key: str  # as written, without "$"
    dollar: bool
    value: str
    start: int  # character offsets of the value (between the quotes)
    end: int


def decode(data: bytes) -> tuple[bool, str]:
    bom = data.startswith(BOM)
    try:
        return bom, data[len(BOM) if bom else 0 :].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ScriptError(f"script is not UTF-8: {exc}") from exc


def encode(bom: bool, text: str) -> bytes:
    out = text.encode("utf-8")
    return (BOM + out) if bom else out


def assignments(text: str) -> list[Assignment]:
    return [
        Assignment(m["key"], bool(m["dollar"]), m["value"], m.start("value"), m.end("value"))
        for m in _ASSIGN.finditer(text)
    ]


def fields(text: str) -> dict[str, list[Assignment]]:
    """Logical field name -> every quoted assignment that maps to it."""
    out: dict[str, list[Assignment]] = {}
    for a in assignments(text):
        logical = _KEY_TO_LOGICAL.get(a.key.lower())
        if logical is not None:
            out.setdefault(logical, []).append(a)
    return out


@dataclass(frozen=True)
class ScriptFields:
    """Single-valued view: logical name -> value. ``duplicates`` lists names seen twice."""

    values: dict[str, str]
    duplicates: tuple[str, ...]

    def get(self, name: str) -> str | None:
        return self.values.get(name)


def read(data: bytes) -> ScriptFields:
    _, text = decode(data)
    found = fields(text)
    values = {name: items[0].value for name, items in found.items()}
    dups = tuple(sorted(name for name, items in found.items() if len(items) > 1))
    return ScriptFields(values=values, duplicates=dups)


def _replace_spans(text: str, spans: list[tuple[int, int, str]]) -> str:
    for start, end, value in sorted(spans, reverse=True):
        text = text[:start] + value + text[end:]
    return text


def update(data: bytes, changes: dict[str, str]) -> bytes:
    """Replace logical fields (each must appear exactly once, quoted)."""
    bom, text = decode(data)
    found = fields(text)
    spans = []
    for name, value in changes.items():
        if name not in ALIASES:
            raise ScriptError(f"unknown field {name!r}")
        if any(ch in value for ch in "'\"\r\n"):
            raise ScriptError(f"refusing to write {name} value containing quotes or newlines")
        items = found.get(name, [])
        if not items:
            raise ScriptError(f"field {name} not found (quoted assignment required)")
        if len(items) > 1:
            raise ScriptError(f"field {name} appears {len(items)} times")
        spans.append((items[0].start, items[0].end, value))
    return encode(bom, _replace_spans(text, spans))


def arch_changes(arch: str, url: str, sha256: str) -> dict[str, str]:
    """The field changes for one arch: URL, sha256 checksum and type 'sha256'."""
    url_key, sum_key, type_key = ARCH_FIELDS[arch]
    return {url_key: url, sum_key: sha256, type_key: "sha256"}


# ----- install-directory tokens ---------------------------------------------


def set_variable(data: bytes, name: str, value: str) -> tuple[bytes, int]:
    """Set every quoted ``$<name> = '...'`` assignment. Returns (bytes, count)."""
    if any(ch in value for ch in "'\"\r\n"):
        raise ScriptError(f"refusing to write ${name} value {value!r}")
    bom, text = decode(data)
    spans = [
        (a.start, a.end, value)
        for a in assignments(text)
        if a.dollar and a.key.lower() == name.lower()
    ]
    return encode(bom, _replace_spans(text, spans)), len(spans)


def get_variable(data: bytes, name: str) -> list[str]:
    _, text = decode(data)
    return [a.value for a in assignments(text) if a.dollar and a.key.lower() == name.lower()]


def set_mvnd_dir(data: bytes, new_dir: str) -> tuple[bytes, int]:
    """Replace literal ``maven-mvnd-<v>-windows-amd64`` dir tokens (not inside URLs)."""
    if not _MVND_DIR.fullmatch(new_dir):
        raise ScriptError(f"unexpected mvnd directory name {new_dir!r}")
    bom, text = decode(data)
    new, count = _MVND_DIR.subn(new_dir, text)
    return encode(bom, new), count


def get_mvnd_dirs(data: bytes) -> list[str]:
    _, text = decode(data)
    return _MVND_DIR.findall(text)
