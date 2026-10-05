"""Shared test helpers.

``tests/fixtures/http_index.json`` maps recorded URLs to fixture files (GET)
and to recorded status/headers (HEAD). The fixtures were captured from the live
vendor APIs on 2026-10-04 with a throwaway recorder; GitHub release JSON is
trimmed to the fields chocotools reads (tag, draft/prerelease, Windows assets
with name/url/digest) and Chocolatey feeds to Version/IsApproved per entry.
``tests/fixtures/pkg/`` holds byte copies of real package folders.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from chocotools.http import HttpError, Response  # noqa: E402
from chocotools.manifest import Package  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
PKG_FIXTURES = FIXTURES / "pkg"


def load_index() -> dict:
    return json.loads((FIXTURES / "http_index.json").read_text(encoding="utf-8"))


class FakeClient:
    """Replays recorded responses; anything unknown raises HttpError(404)."""

    def __init__(self, get: dict[str, bytes | str] | None = None, head: dict | None = None,
                 use_index: bool = True):
        self.get_map: dict[str, bytes] = {}
        self.head_map: dict[str, dict] = {}
        if use_index:
            index = load_index()
            for url, rel in index["get"].items():
                self.get_map[url] = (FIXTURES / rel).read_bytes()
            self.head_map.update(index["head"])
        for url, body in (get or {}).items():
            self.get_map[url] = body.encode("utf-8") if isinstance(body, str) else body
        self.head_map.update(head or {})
        self.sha256_map: dict[str, str] = {}
        self.zip_roots: dict[str, str] = {}
        self.calls: list[str] = []

    def get_bytes(self, url, *, headers=None):
        self.calls.append(url)
        if url not in self.get_map:
            raise HttpError(f"HTTP 404 for {url}", 404, url)
        return self.get_map[url]

    def get_text(self, url):
        return self.get_bytes(url).decode("utf-8")

    def get_json(self, url):
        return json.loads(self.get_bytes(url).decode("utf-8"))

    def head(self, url, *, follow_redirects=True):
        self.calls.append("HEAD " + url)
        meta = self.head_map.get(url)
        if meta is None:
            raise HttpError(f"HTTP 404 for {url}", 404, url)
        return Response(meta["status"], {k.lower(): v for k, v in meta.get("headers", {}).items()}, b"",
                        meta.get("url", url))

    def sha256_of(self, url):
        self.calls.append("SHA " + url)
        if url not in self.sha256_map:
            raise HttpError(f"HTTP 404 for {url}", 404, url)
        return self.sha256_map[url]

    def zip_root_dir(self, url):
        self.calls.append("ZIP " + url)
        if url not in self.zip_roots:
            raise HttpError(f"HTTP 404 for {url}", 404, url)
        return self.zip_roots[url]


@pytest.fixture
def fake_client() -> FakeClient:
    return FakeClient()


def pkg(**kw) -> Package:
    defaults = dict(id="x", folder="x", vendor="temurin", major=21, image="jdk", arch=("x64",))
    defaults.update(kw)
    if isinstance(defaults.get("arch"), list):
        defaults["arch"] = tuple(defaults["arch"])
    return Package(**defaults)


def pkg_bytes(folder: str, rel: str) -> bytes:
    return (PKG_FIXTURES / folder / rel).read_bytes()


def copy_pkg(folder: str, dest_root: Path, as_folder: str | None = None) -> Path:
    target = dest_root / (as_folder or folder)
    shutil.copytree(PKG_FIXTURES / folder, target)
    return target
