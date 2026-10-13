"""chocotools: keep this repo's Chocolatey packages in step with their vendors.

The repo is the source of truth. ``packages.toml`` (repo root) lists every
managed package; the CLI (``python -m chocotools``) syncs, validates, builds,
publishes and compares them. Runtime code uses the standard library only.
"""

__version__ = "0.1.0"
