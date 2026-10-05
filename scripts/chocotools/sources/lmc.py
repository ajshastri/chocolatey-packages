"""Liberica Mission Control: no machine-readable source.

The baseline report (section 7) found none: ``api.bell-sw.com/v1/lmc/releases``
and the BellSoft download page return 404, and guessed download URLs 404 too.
The package is maintained by hand and is frozen in packages.toml; ``compare``
shows it as ``manual``.
"""

from __future__ import annotations

from ..http import Client
from ..manifest import Package
from . import Release, SourceUnsupported


def normalize(raw: str) -> str:
    raise SourceUnsupported("no machine-readable Liberica Mission Control source; manual package")


def fetch(pkg: Package, *, version: str | None = None, client: Client) -> Release:
    raise SourceUnsupported("no machine-readable Liberica Mission Control source; manual package")
