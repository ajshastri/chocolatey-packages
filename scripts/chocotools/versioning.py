"""Version normalization and NuGet-style comparison.

Every helper here is a pure function. Vendor modules in ``sources/`` combine
them into a ``normalize(raw)`` for their own version strings.

Output form (``format``):
- leading zeros dropped per segment (``8.504.04.1`` -> ``8.504.4.1``);
- trailing ``.0`` segments beyond the third removed (``21.52.203.0`` -> ``21.52.203``);
- padded to at least 3 segments (``27`` -> ``27.0.0``);
- never more than 4 segments (raises ``VersionError``).

Comparison pads with zeros, so ``21.52.203.0`` equals ``21.52.203``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

__all__ = [
    "VersionError",
    "parse",
    "format",
    "compare_nuget",
    "equal",
    "is_valid",
    "strip_v",
    "strip_final",
    "strip_ga",
    "strip_windows_n",
    "strip_build",
    "join_parts",
    "corretto_tag",
]

MAX_PARTS = 4
_NUMERIC = re.compile(r"^\d+(\.\d+)*$")


class VersionError(ValueError):
    """Raised for a version string that cannot be used as a package version."""


def parse(version: str) -> tuple[int, ...]:
    """Parse a dotted numeric version into integers (1 to 4 parts)."""
    if version is None:
        raise VersionError("version is missing")
    text = version.strip()
    if not text:
        raise VersionError("version is empty")
    if not _NUMERIC.match(text):
        raise VersionError(f"not a numeric dotted version: {version!r}")
    parts = tuple(int(p) for p in text.split("."))
    if len(parts) > MAX_PARTS:
        raise VersionError(f"more than {MAX_PARTS} parts: {version!r}")
    return parts


def is_valid(version: str) -> bool:
    """True if ``version`` parses as a 1-4 part numeric NuGet version."""
    try:
        parse(version)
    except VersionError:
        return False
    return True


def format(version: str | Iterable[int]) -> str:  # noqa: A001 - module API name
    """Return the NuGet-normalized form used for nuspec ``<version>``."""
    if isinstance(version, str):
        text = version.strip()
        if not text or not _NUMERIC.match(text):
            raise VersionError(f"not a numeric dotted version: {version!r}")
        parts = [int(p) for p in text.split(".")]
    else:
        parts = [int(p) for p in version]
        if not parts:
            raise VersionError("version is empty")
    while len(parts) > 3 and parts[-1] == 0:
        parts.pop()
    if len(parts) > MAX_PARTS:
        raise VersionError(f"more than {MAX_PARTS} parts: {'.'.join(map(str, parts))}")
    while len(parts) < 3:
        parts.append(0)
    return ".".join(str(p) for p in parts)


def _key(version: str) -> tuple[int, ...]:
    parts = list(parse(version))
    parts += [0] * (MAX_PARTS - len(parts))
    return tuple(parts)


def compare_nuget(a: str, b: str) -> int:
    """Return -1, 0 or 1 comparing two versions, zero-padded to 4 parts."""
    ka, kb = _key(a), _key(b)
    return (ka > kb) - (ka < kb)


def equal(a: str, b: str) -> bool:
    """True if ``a`` and ``b`` are the same version (trailing zeros ignored)."""
    return compare_nuget(a, b) == 0


def strip_v(text: str) -> str:
    """``v1.0.6`` -> ``1.0.6``."""
    return text[1:] if text[:1] in ("v", "V") and text[1:2].isdigit() else text


def strip_final(text: str) -> str:
    """``41.0.1.Final`` -> ``41.0.1``."""
    return re.sub(r"\.Final$", "", text)


def strip_ga(text: str) -> str:
    """``9.1.2-ga`` -> ``9.1.2``."""
    return re.sub(r"-ga$", "", text)


def strip_windows_n(text: str) -> str:
    """``2.56.0.windows.1`` -> ``2.56.0``."""
    return re.sub(r"\.windows\.\d+$", "", text)


def strip_build(text: str) -> str:
    """Strip a ``+N`` build suffix: ``21.0.12.1+1`` -> ``21.0.12.1``."""
    return re.sub(r"\+\d+$", "", text)


def join_parts(parts: Iterable[int | str]) -> str:
    """Join an Azul-style version array: ``[21, 52, 203, 0]`` -> ``21.52.203.0``."""
    items = [str(int(p)) for p in parts]
    if not items:
        raise VersionError("empty version array")
    return ".".join(items)


def corretto_tag(tag: str) -> str:
    """Map a Corretto tag to a package version.

    5 parts ``A.B.C.D.E`` become ``A.B.C.<D><E>`` (``21.0.12.12.1`` -> ``21.0.12.121``).
    4-part tags (Corretto 8, e.g. ``8.504.04.1``) are kept as-is. Leading zeros
    are dropped by ``format``.
    """
    parts = tag.strip().split(".")
    if not all(p.isdigit() for p in parts):
        raise VersionError(f"unexpected Corretto tag: {tag!r}")
    if len(parts) == 5:
        parts = parts[:3] + [str(int(parts[3])) + str(int(parts[4]))]
    elif len(parts) != 4:
        raise VersionError(f"unexpected Corretto tag: {tag!r}")
    return format(".".join(parts))
