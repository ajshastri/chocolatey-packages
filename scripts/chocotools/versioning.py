"""Version normalization and NuGet-style comparison.

Every helper here is a pure function. Vendor modules in ``sources/`` combine
them into a ``normalize(raw)`` for their own version strings.

Output form (``format``):
- leading zeros dropped per segment (``8.504.04.1`` -> ``8.504.4.1``);
- trailing ``.0`` segments beyond the third removed (``21.52.203.0`` -> ``21.52.203``);
- padded to at least 3 segments (``27`` -> ``27.0.0``);
- never more than 4 segments (raises ``VersionError``).

Comparison pads with zeros, so ``21.52.203.0`` equals ``21.52.203``.

Package fix versions (``package_fix = N`` in ``packages.toml``, 1 <= N <= 99)
------------------------------------------------------------------------------
Needed when a version can never be pushed again (Chocolatey rejected it, and
rejected versions cannot be modified) but the upstream version has not moved.
Upstream already uses the 4th segment (Temurin ``21.0.12.1``), so the fix
follows Chocolatey's "add two zeroes" rule: the 4th segment becomes
``P * 100 + N``, where ``P`` is the upstream 4th segment (0 if absent).

The fix is declared for one line with ``package_fix_line = "A.B.C"``. While
it is set, *every* upstream version on that line keeps the two-digit suffix,
so a later upstream respin still sorts above the fix:

=========================  =======================  ============================
upstream                   package_fix = 1          why it is safe
=========================  =======================  ============================
``21.0.12.1`` (rejected)   ``21.0.12.101``          ``101 > 1``
``21.0.12.2`` (respin)     ``21.0.12.201``          ``201 > 101``
``21.0.13`` (next update)  ``21.0.13`` (fix cleared) ``13 > 12`` in the 3rd segment
``8.504.1`` (Temurin 8)    ``8.504.1.1``            ``8.504.1.1 > 8.504.1``
``25.0.4.10.1`` Corretto   ``25.0.4.10101``         ``10101 > 101``; respin ``.10.2`` -> ``10201``
=========================  =======================  ============================

``sync`` clears ``package_fix`` and ``package_fix_line`` from the manifest,
in the same run that writes the new version, as soon as upstream is on
another ``A.B.C`` than ``package_fix_line`` (see ``target_version``). Nobody
needs to remove them by hand. If the nuspec ends up on another line while the
fix is still set, ``validate`` reports the fix as stale instead of applying it.
"""

from __future__ import annotations

import re
import urllib.parse
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
    "graalvm_tag",
    "FIX_FACTOR",
    "apply_package_fix",
    "strip_package_fix",
    "same_line",
    "target_version",
    "url_version",
]

MAX_PARTS = 4
FIX_FACTOR = 100
MAX_PACKAGE_FIX = FIX_FACTOR - 1
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


# ----- package fix versions --------------------------------------------------


def _check_fix(fix: int) -> None:
    if isinstance(fix, bool) or not isinstance(fix, int) or not 1 <= fix <= MAX_PACKAGE_FIX:
        raise VersionError(f"package_fix must be an integer 1-{MAX_PACKAGE_FIX}, got {fix!r}")


def _four(version: str) -> list[int]:
    parts = list(parse(version))
    return parts + [0] * (MAX_PARTS - len(parts))


def apply_package_fix(upstream: str, fix: int) -> str:
    """``A.B.C[.P]`` + fix ``N`` -> ``A.B.C.(P*100+N)``.

    ``21.0.12.1`` + 1 -> ``21.0.12.101``; ``8.504.1`` + 1 -> ``8.504.1.1``.
    """
    _check_fix(fix)
    parts = _four(upstream)
    parts[3] = parts[3] * FIX_FACTOR + fix
    return format(parts)


def strip_package_fix(version: str, fix: int) -> str:
    """Inverse of ``apply_package_fix``: ``21.0.12.101`` (fix 1) -> ``21.0.12.1``.

    Raises ``VersionError`` if the 4th segment does not end in the fix digits.
    """
    _check_fix(fix)
    parts = _four(version)
    if parts[3] % FIX_FACTOR != fix:
        raise VersionError(f"version {version} does not carry package fix {fix} (4th segment must end in {fix:02d})")
    parts[3] //= FIX_FACTOR
    return format(parts)


def same_line(a: str, b: str) -> bool:
    """True if ``a`` and ``b`` share the first three segments (``A.B.C``)."""
    return _four(a)[:3] == _four(b)[:3]


def target_version(upstream: str, fix: int | None, line: str | None) -> tuple[str, bool]:
    """The version sync should hold for ``upstream``, and whether ``package_fix`` still applies.

    ``line`` is ``package_fix_line``, the ``A.B.C`` the fix was declared for.
    The repo's current version plays no part, so a nuspec that reached a new
    line while the fix was still set (hand edit, or a failed manifest write)
    never gets the fix carried over.

    - no fix: ``(upstream, False)``
    - fix set and ``upstream`` is on ``line``: ``(apply_package_fix(upstream, fix), True)``
    - fix set and ``upstream`` is on another ``A.B.C``: ``(upstream, False)``;
      the caller clears ``package_fix`` and ``package_fix_line`` from the manifest.
    """
    if not fix:
        return upstream, False
    if not line:
        raise VersionError("package_fix is set without package_fix_line")
    if not same_line(upstream, line):
        return upstream, False
    return apply_package_fix(upstream, fix), True


# ----- version carried by a download URL ------------------------------------------

_V = r"(\d+(?:\.\d+)*)"


def graalvm_tag(m: re.Match) -> str:
    """Package version of a GraalVM CE ``graal-`` release URL (tag and asset name).

    The tag is ``<M>.<I>.<rest>`` and the asset ``graalvm-community-jdk-<M>i<I>-<M>.0.<rest>``:

    - ``graal-25.3.4.1``   / ``25i3-25.0.4.1``   -> ``25.3.4.1``
    - ``graal-25.4.4.1.1`` / ``25i4-25.0.4.1.1`` -> ``25.4.4.1``

    The package version is foojay's ``java_version``, the tag's first four
    parts, so a 5th tag part (a GraalVM respin) is dropped. Tag and asset must
    describe the same build, otherwise ``VersionError``.
    """
    tag, major, iteration, asset = m[1], m[2], m[3], m[4]
    asset_parts = asset.split(".")
    if asset_parts[:2] != [major, "0"] or len(asset_parts) < 3:
        raise VersionError(f"GraalVM asset version {major}i{iteration}-{asset} is not {major}i{iteration}-{major}.0.<update>")
    if tag.split(".") != [major, iteration, *asset_parts[2:]]:
        raise VersionError(f"GraalVM tag graal-{tag} does not match asset {major}i{iteration}-{asset}")
    parts = tag.split(".")
    if len(parts) > MAX_PARTS + 1:
        raise VersionError(f"GraalVM tag graal-{tag} has more than {MAX_PARTS + 1} parts")
    return ".".join(parts[:MAX_PARTS])


# vendor -> [(regex on the URL-decoded URL, mapping of the match to a package version)]
# Each mapping mirrors that vendor's ``sources.<vendor>.normalize`` so the URL
# version is compared in the same form sync writes to the nuspec.
_URL_RULES = {
    "temurin": [
        # release tag jdk8u504-b01 -> 8.504.1 (8.<update>.<build>)
        (re.compile(r"/download/jdk8u(\d+)-b(\d+)/"), lambda m: f"8.{int(m[1])}.{int(m[2])}"),
        # release tag jdk-21.0.12.1+1 -> 21.0.12.1 (build dropped)
        (re.compile(rf"/download/jdk-{_V}\+\d+/"), lambda m: m[1]),
    ],
    # resources/<tag>/: 21.0.12.12.1 -> 21.0.12.121, 8.504.04.1 -> 8.504.4.1
    "corretto": [(re.compile(rf"/resources/{_V}/"), lambda m: corretto_tag(m[1]))],
    # the Zulu package version is the distro version (zulu21.52.203), not the JDK version
    "zulu": [(re.compile(rf"/zulu{_V}-ca-"), lambda m: m[1])],
    "liberica": [
        (re.compile(r"/download/8u(\d+)\+(\d+)/"), lambda m: f"8.0.{int(m[1])}.{int(m[2])}"),
        (re.compile(rf"/download/{_V}\+\d+/"), lambda m: m[1]),
    ],
    "sapmachine": [(re.compile(rf"/download/sapmachine-{_V}/"), lambda m: m[1])],
    "graalvm": [
        # graal-<tag>/graalvm-community-jdk-<M>i<I>-<M>.0.<rest>_: see graalvm_tag
        (re.compile(rf"/download/graal-{_V}/graalvm-community-jdk-(\d+)i(\d+)-{_V}_"), graalvm_tag),
        # any other graal- tag must itself be a package version (1-4 parts)
        (re.compile(rf"/download/graal-{_V}/"), lambda m: m[1]),
        # jdk-21.0.2 for the old CE builds
        (re.compile(rf"/download/jdk-{_V}/"), lambda m: m[1]),
    ],
    # openjdk-27_windows -> 27.0.0, openjdk-26.0.2_windows -> 26.0.2
    "openjdk": [(re.compile(rf"/openjdk-{_V}_windows"), lambda m: m[1])],
    "jmc": [(re.compile(rf"/jmc-{_V}_windows"), lambda m: m[1])],
    "mvnd": [(re.compile(rf"/download/v?{_V}/maven-mvnd-"), lambda m: m[1])],
    "wildfly": [(re.compile(rf"/download/{_V}\.Final/"), lambda m: m[1])],
    "lmc": [(re.compile(rf"/lmc/{_V}/"), lambda m: m[1])],
}


def url_version(vendor: str, url: str) -> str:
    """The package version implied by a vendor download URL (normalized).

    Raises ``VersionError`` if the URL carries no version token for that vendor.
    """
    rules = _URL_RULES.get(vendor)
    if rules is None:
        raise VersionError(f"no URL version rule for vendor {vendor!r}")
    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    for pattern, mapping in rules:
        m = pattern.search(path)
        if m:
            return format(mapping(m))
    raise VersionError(f"no {vendor} version token found in URL {url}")
