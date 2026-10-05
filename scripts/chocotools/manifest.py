"""Load and check ``packages.toml``, the single manifest for every managed package.

Schema (one ``[[package]]`` table per package):
- ``id`` (Chocolatey id, must equal the nuspec ``<id>``), ``folder``, ``vendor``
- ``major`` (int) and ``image`` (``jdk``/``jre``): required for the Java vendors;
  ``jmc`` requires ``major`` only; ``wildfly``/``mvnd``/``lmc`` need neither
- ``variant`` (Liberica only): ``std``, ``full`` or ``lite``
- ``arch``: list of ``x64``, ``x86``, ``neutral``
- ``frozen`` (bool, default false), ``notes`` (str)

A top-level ``ignore = [...]`` lists folders that hold a nuspec but are not
managed (e.g. FreeDownloadManager). ``check_tree`` reports any other nuspec
folder missing from the manifest.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

VENDORS = (
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
JAVA_VENDORS = {"temurin", "liberica", "sapmachine", "zulu", "corretto", "graalvm", "openjdk"}
ARCHES = ("x64", "x86", "neutral")
IMAGES = ("jdk", "jre")
VARIANTS = ("std", "full", "lite")
MANIFEST_NAME = "packages.toml"
_KNOWN_KEYS = {"id", "folder", "vendor", "major", "image", "variant", "arch", "frozen", "notes"}


class ManifestError(Exception):
    """The manifest is unreadable or structurally invalid."""


@dataclass(frozen=True)
class Package:
    id: str
    folder: str
    vendor: str
    major: int | None = None
    image: str | None = None
    variant: str | None = None
    arch: tuple[str, ...] = ("x64",)
    frozen: bool = False
    notes: str = ""


@dataclass
class Manifest:
    packages: list[Package]
    ignore: list[str] = field(default_factory=list)
    root: Path | None = None

    def by_id(self) -> dict[str, Package]:
        return {p.id: p for p in self.packages}

    def by_folder(self) -> dict[str, Package]:
        return {p.folder: p for p in self.packages}

    def select(self, ids: list[str] | None = None, vendor: str | None = None) -> list[Package]:
        """Packages matching ``ids`` (case-insensitive) and/or ``vendor``.

        Unknown ids raise ``ManifestError``.
        """
        pkgs = list(self.packages)
        if ids:
            lookup = {p.id.lower(): p for p in self.packages}
            missing = [i for i in ids if i.lower() not in lookup]
            if missing:
                raise ManifestError(f"unknown package id(s): {', '.join(missing)}")
            wanted = {i.lower() for i in ids}
            pkgs = [p for p in pkgs if p.id.lower() in wanted]
        if vendor:
            if vendor not in VENDORS:
                raise ManifestError(f"unknown vendor: {vendor}")
            pkgs = [p for p in pkgs if p.vendor == vendor]
        return pkgs


def _package(entry: dict, index: int) -> Package:
    where = f"package #{index + 1}"
    unknown = set(entry) - _KNOWN_KEYS
    if unknown:
        raise ManifestError(f"{where}: unknown keys {sorted(unknown)}")
    for key in ("id", "folder", "vendor"):
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            raise ManifestError(f"{where}: '{key}' is required")
    pid, vendor = entry["id"], entry["vendor"]
    where = f"package {pid!r}"
    if vendor not in VENDORS:
        raise ManifestError(f"{where}: unknown vendor {vendor!r}")
    major = entry.get("major")
    if major is not None and (not isinstance(major, int) or isinstance(major, bool) or major <= 0):
        raise ManifestError(f"{where}: 'major' must be a positive integer")
    image = entry.get("image")
    if image is not None and image not in IMAGES:
        raise ManifestError(f"{where}: 'image' must be one of {IMAGES}")
    variant = entry.get("variant")
    if vendor in JAVA_VENDORS or vendor == "jmc":
        if major is None:
            raise ManifestError(f"{where}: 'major' is required for vendor {vendor}")
    if vendor in JAVA_VENDORS and image is None:
        raise ManifestError(f"{where}: 'image' is required for vendor {vendor}")
    if vendor == "liberica":
        if variant not in VARIANTS:
            raise ManifestError(f"{where}: 'variant' must be one of {VARIANTS}")
    elif variant is not None:
        raise ManifestError(f"{where}: 'variant' applies to liberica only")
    arch = entry.get("arch", ["x64"])
    if not isinstance(arch, list) or not arch or any(a not in ARCHES for a in arch):
        raise ManifestError(f"{where}: 'arch' must be a non-empty list of {ARCHES}")
    if len(set(arch)) != len(arch):
        raise ManifestError(f"{where}: duplicate 'arch' values")
    if "neutral" in arch and len(arch) > 1:
        raise ManifestError(f"{where}: 'neutral' cannot be combined with other arches")
    frozen = entry.get("frozen", False)
    if not isinstance(frozen, bool):
        raise ManifestError(f"{where}: 'frozen' must be true or false")
    notes = entry.get("notes", "")
    if not isinstance(notes, str):
        raise ManifestError(f"{where}: 'notes' must be a string")
    return Package(
        id=pid,
        folder=entry["folder"],
        vendor=vendor,
        major=major,
        image=image,
        variant=variant,
        arch=tuple(arch),
        frozen=frozen,
        notes=notes,
    )


def parse(text: str, root: Path | None = None) -> Manifest:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(f"{MANIFEST_NAME}: {exc}") from exc
    unknown = set(data) - {"ignore", "package"}
    if unknown:
        raise ManifestError(f"{MANIFEST_NAME}: unknown top-level keys {sorted(unknown)}")
    ignore = data.get("ignore", [])
    if not isinstance(ignore, list) or not all(isinstance(i, str) for i in ignore):
        raise ManifestError("'ignore' must be a list of folder names")
    entries = data.get("package", [])
    if not isinstance(entries, list) or not entries:
        raise ManifestError(f"{MANIFEST_NAME}: no [[package]] entries")
    packages = [_package(e, i) for i, e in enumerate(entries)]
    seen_ids: dict[str, str] = {}
    seen_folders: set[str] = set()
    for p in packages:
        key = p.id.lower()
        if key in seen_ids:
            raise ManifestError(f"duplicate package id: {p.id}")
        seen_ids[key] = p.id
        if p.folder.lower() in seen_folders:
            raise ManifestError(f"duplicate package folder: {p.folder}")
        seen_folders.add(p.folder.lower())
        if p.folder in ignore:
            raise ManifestError(f"folder {p.folder} is both managed and ignored")
    return Manifest(packages=packages, ignore=list(ignore), root=root)


def load(root: Path) -> Manifest:
    path = Path(root) / MANIFEST_NAME
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(f"cannot read {path}: {exc}") from exc
    return parse(text, root=Path(root))


def nuspec_path(root: Path, pkg: Package) -> Path:
    """The single ``*.nuspec`` in the package folder (raises if not exactly one)."""
    folder = Path(root) / pkg.folder
    found = sorted(folder.glob("*.nuspec"))
    if len(found) != 1:
        raise ManifestError(f"{pkg.folder}: expected exactly one *.nuspec, found {len(found)}")
    return found[0]


def check_tree(root: Path, manifest: Manifest) -> list[str]:
    """Compare the manifest with the folders on disk. Returns error strings."""
    from . import nuspec  # local import to avoid a cycle at import time

    root = Path(root)
    errors: list[str] = []
    for pkg in manifest.packages:
        folder = root / pkg.folder
        if not folder.is_dir():
            errors.append(f"{pkg.id}: folder {pkg.folder} does not exist")
            continue
        try:
            path = nuspec_path(root, pkg)
        except ManifestError as exc:
            errors.append(f"{pkg.id}: {exc}")
            continue
        if not (folder / "tools" / "chocolateyinstall.ps1").is_file():
            errors.append(f"{pkg.id}: {pkg.folder}/tools/chocolateyinstall.ps1 is missing")
        try:
            info = nuspec.read(path.read_bytes())
        except nuspec.NuspecError as exc:
            errors.append(f"{pkg.id}: {exc}")
            continue
        if info.id != pkg.id:
            errors.append(f"{pkg.id}: nuspec <id> is {info.id!r}, manifest id is {pkg.id!r}")
    managed = {p.folder for p in manifest.packages} | set(manifest.ignore)
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name in managed:
            continue
        if any(child.glob("*.nuspec")):
            errors.append(f"{child.name}: has a nuspec but is not in {MANIFEST_NAME} (add it or list it in 'ignore')")
    return errors
