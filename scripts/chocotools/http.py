"""HTTP helpers: GET/HEAD/download with timeouts, retries, rate limits and a cache.

- User-Agent ``chocotools/<ver> (+https://github.com/ajshastri/chocolatey-packages)``.
- 30 s timeout. Retries on 429/500/502/503/504, timeouts and connection errors
  with exponential backoff and full jitter (wait ``n`` is uniform in
  ``[0, min(cap, base * 2**(n-1))]``), honoring ``Retry-After`` up to the cap.
  Other statuses (400/401/403/404, ...) fail at once.
  - Chocolatey (``FEED_HOSTS``): base 5 s, cap 120 s, retried until 15 min
    (``FEED_RETRY_BUDGET``, env ``CHOCOTOOLS_FEED_RETRY_BUDGET`` in seconds) have
    passed since the request started. A request that uses up the budget opens
    a circuit breaker: later requests to that host from the same ``Client``
    fail at once instead of waiting another budget each.
  - Every other host: base 2 s, cap 30 s, at most 4 retries.
  Each retry logs one line to stderr:
  ``retry <n> for <host>: <reason>; waiting <s>s (budget left <s>s)``.
- Per-host minimum interval between requests: community.chocolatey.org 1.1 s,
  everything else 0.2 s.
- ``Authorization: Bearer $GITHUB_TOKEN`` (or ``$GH_TOKEN``) is sent only to
  api.github.com, and is dropped if a redirect leaves that host.
- If ``CHOCOTOOLS_CACHE_DIR`` is set, GET responses are cached on disk keyed by
  sha256(url + range), for ``CHOCOTOOLS_CACHE_TTL`` seconds (default 21600).
  Streaming downloads (``sha256_of``) are never cached.
- ``head`` falls back to ``GET`` with ``Range: bytes=0-0`` on 403/405.
"""

from __future__ import annotations

import email.utils
import hashlib
import json
import os
import random
import struct
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__

USER_AGENT = f"chocotools/{__version__} (+https://github.com/ajshastri/chocolatey-packages)"
TIMEOUT = 30
GITHUB_API_HOST = "api.github.com"
# Chocolatey community feed and push endpoint: outages last minutes, so wait them out.
FEED_HOSTS = frozenset({"community.chocolatey.org", "push.chocolatey.org"})
FEED_RETRY_BASE = 5.0  # seconds, first wait's upper bound
FEED_RETRY_CAP = 120.0  # seconds, longest single wait (also caps Retry-After)
FEED_RETRY_BUDGET = 15 * 60  # seconds per request, from its first attempt
FEED_RETRY_BUDGET_ENV = "CHOCOTOOLS_FEED_RETRY_BUDGET"
# Everything else (vendor APIs and CDNs).
DEFAULT_RETRY_BASE = 2.0
DEFAULT_RETRY_CAP = 30.0
DEFAULT_RETRIES = 4
_MIN_INTERVAL = {"community.chocolatey.org": 1.1}
_DEFAULT_INTERVAL = 0.2
_RETRY_STATUS = {429, 500, 502, 503, 504}
_CHUNK = 1024 * 1024


class HttpError(Exception):
    """A request failed (after retries) or returned an unexpected status."""

    def __init__(self, message: str, status: int | None = None, url: str | None = None):
        super().__init__(message)
        self.status = status
        self.url = url


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str

    def header(self, name: str) -> str | None:
        return self.headers.get(name.lower())

    def text(self) -> str:
        return self.body.decode("utf-8")

    def json(self):
        return json.loads(self.body.decode("utf-8"))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects but drop Authorization when leaving the original host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            old_host = urllib.parse.urlsplit(req.full_url).hostname
            new_host = urllib.parse.urlsplit(newurl).hostname
            if old_host != new_host:
                for key in list(new.headers):
                    if key.lower() == "authorization":
                        del new.headers[key]
                new.unredirected_hdrs.pop("Authorization", None)
        return new


def _host(url: str) -> str:
    return (urllib.parse.urlsplit(url).hostname or "").lower()


def github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None


# ----- retry policy ----------------------------------------------------------


@dataclass(frozen=True)
class RetryPolicy:
    label: str  # used in give-up messages, e.g. "Chocolatey feed"
    base: float  # seconds; wait n is uniform in [0, min(cap, base * 2**(n-1))]
    cap: float  # seconds; longest single wait, also caps Retry-After
    max_retries: int | None = None  # None: until the budget is spent
    budget: float | None = None  # seconds per request since its first attempt; None: no budget
    circuit_breaker: bool = False  # after a spent budget, fail later requests to the host at once


def feed_retry_budget() -> float:
    """``FEED_RETRY_BUDGET``, or ``$CHOCOTOOLS_FEED_RETRY_BUDGET`` seconds when set."""
    text = os.environ.get(FEED_RETRY_BUDGET_ENV, "").strip()
    if not text:
        return float(FEED_RETRY_BUDGET)
    try:
        value = float(text)
    except ValueError:
        value = -1.0
    if value < 0:
        raise HttpError(f"{FEED_RETRY_BUDGET_ENV} must be a number of seconds >= 0, got {text!r}")
    return value


def retry_policy(host: str, feed_budget: float | None = None) -> RetryPolicy:
    """The retry policy for ``host`` (``feed_budget`` overrides the feed's budget)."""
    if host in FEED_HOSTS:
        budget = feed_retry_budget() if feed_budget is None else feed_budget
        return RetryPolicy("Chocolatey feed", FEED_RETRY_BASE, FEED_RETRY_CAP, budget=budget, circuit_breaker=True)
    return RetryPolicy(host, DEFAULT_RETRY_BASE, DEFAULT_RETRY_CAP, max_retries=DEFAULT_RETRIES)


class Backoff:
    """Waits for one request's retries under a ``RetryPolicy``."""

    def __init__(self, policy: RetryPolicy, *, clock=time.monotonic, uniform=random.uniform):
        self.policy = policy
        self.clock = clock
        self.uniform = uniform
        self.start = clock()
        self.retries = 0

    def budget_left(self) -> float | None:
        if self.policy.budget is None:
            return None
        return max(0.0, self.policy.budget - (self.clock() - self.start))

    def next_wait(self, retry_after: float | None = None) -> float | None:
        """Seconds to wait before the next attempt, or None when out of retries or budget."""
        p = self.policy
        if p.max_retries is not None and self.retries >= p.max_retries:
            return None
        left = self.budget_left()
        if left is not None and left <= 0:
            return None
        if retry_after is not None:
            wait = min(retry_after, p.cap)
        else:
            wait = self.uniform(0.0, min(p.cap, p.base * 2**self.retries))
        if left is not None:
            wait = min(wait, left)
        self.retries += 1
        return wait

    def line(self, host: str, reason: str, wait: float) -> str:
        """The log line for the retry ``next_wait`` just granted."""
        left = self.budget_left()
        if left is not None:
            tail = f"budget left {left:.0f}s"
        else:
            tail = f"{self.policy.max_retries - self.retries} of {self.policy.max_retries} retries left"
        return f"retry {self.retries} for {host}: {reason}; waiting {wait:.1f}s ({tail})"


def duration(seconds: float) -> str:
    """``900`` -> ``15 min``, ``90`` -> ``90s``."""
    if seconds >= 60 and seconds % 60 == 0:
        return f"{seconds / 60:.0f} min"
    return f"{seconds:.0f}s"


def redact(text: str) -> str:
    """Hide ``$CHOCO_KEY`` (the Chocolatey API key) in a log line."""
    key = os.environ.get("CHOCO_KEY", "")
    return text.replace(key, "***") if key else text


def log_stderr(line: str) -> None:
    print(redact(line), file=sys.stderr, flush=True)


@dataclass
class Client:
    """Small urllib-based HTTP client. One shared instance via ``default_client()``."""

    cache_dir: Path | None = None
    cache_ttl: int = 21600
    sleep: object = time.sleep
    clock: object = time.monotonic
    uniform: object = random.uniform  # jitter source, (low, high) -> float
    log: object = log_stderr  # one line per retry
    feed_budget: float | None = None  # None: FEED_RETRY_BUDGET or $CHOCOTOOLS_FEED_RETRY_BUDGET
    _last: dict[str, float] = field(default_factory=dict)
    _memo: dict[str, bytes] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _gave_up: dict[str, float] = field(default_factory=dict)  # host -> budget it used up (circuit open)

    @classmethod
    def from_env(cls) -> "Client":
        cache = os.environ.get("CHOCOTOOLS_CACHE_DIR")
        ttl = int(os.environ.get("CHOCOTOOLS_CACHE_TTL", "21600"))
        return cls(cache_dir=Path(cache) if cache else None, cache_ttl=ttl)

    # ----- low level -------------------------------------------------
    def _headers(self, url: str, extra: dict[str, str] | None) -> dict[str, str]:
        headers = {"User-Agent": USER_AGENT}
        if _host(url) == GITHUB_API_HOST:
            headers["Accept"] = "application/vnd.github+json"
            token = github_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        if extra:
            headers.update(extra)
        return headers

    def _throttle(self, url: str) -> None:
        host = _host(url)
        interval = _MIN_INTERVAL.get(host, _DEFAULT_INTERVAL)
        with self._lock:
            last = self._last.get(host)
            now = self.clock()
            if last is not None and now - last < interval:
                self.sleep(interval - (now - last))
            self._last[host] = self.clock()

    def _open(self, req: urllib.request.Request, follow_redirects: bool):
        handler = _SafeRedirect() if follow_redirects else _NoRedirect()
        opener = urllib.request.build_opener(handler)
        return opener.open(req, timeout=TIMEOUT)

    @staticmethod
    def _retry_after(headers) -> float | None:
        value = headers.get("Retry-After") if headers else None
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            parsed = email.utils.parsedate_to_datetime(value)
            return max(0.0, parsed.timestamp() - time.time()) if parsed else None

    def request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        follow_redirects: bool = True,
        stream: bool = False,
    ):
        """Perform a request with retries. Returns ``Response`` (or the raw
        response object when ``stream=True``; caller must close it).

        3xx responses are returned (not raised) when ``follow_redirects`` is False.
        Retries follow ``retry_policy(host)`` (see the module docstring).
        """
        host = _host(url)
        policy = retry_policy(host, self.feed_budget)
        if policy.circuit_breaker and host in self._gave_up:
            raise HttpError(f"{policy.label} unavailable (gave up after {duration(self._gave_up[host])} of retries "
                            "earlier in this run)", None, url)
        backoff = Backoff(policy, clock=self.clock, uniform=self.uniform)
        while True:
            self._throttle(url)
            req = urllib.request.Request(url, method=method, headers=self._headers(url, headers))
            try:
                resp = self._open(req, follow_redirects)
                if stream:
                    return resp
                with resp:
                    body = resp.read()
                    return Response(
                        resp.status,
                        {k.lower(): v for k, v in resp.headers.items()},
                        body,
                        resp.geturl(),
                    )
            except urllib.error.HTTPError as exc:
                if not follow_redirects and 300 <= exc.code < 400:
                    return Response(exc.code, {k.lower(): v for k, v in exc.headers.items()}, b"", url)
                if exc.code not in _RETRY_STATUS:
                    raise HttpError(f"HTTP {exc.code} for {url}", exc.code, url) from exc
                error, status, reason = exc, exc.code, f"HTTP {exc.code}"
                retry_after = self._retry_after(exc.headers)
                message = f"HTTP {exc.code} for {url}"
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                error, status, reason, retry_after = exc, None, str(exc) or type(exc).__name__, None
                message = f"request failed for {url}: {exc}"
            wait = backoff.next_wait(retry_after)
            if wait is None:
                if policy.budget is None:
                    raise HttpError(message, status, url) from error
                if policy.circuit_breaker:
                    self._gave_up[host] = policy.budget
                raise HttpError(f"{policy.label} unavailable: gave up after {duration(policy.budget)} of retries; "
                                f"last error: {message}", status, url) from error
            self.log(backoff.line(host, reason, wait))
            self.sleep(wait)

    # ----- cache ------------------------------------------------------
    def _cache_path(self, key: str) -> Path | None:
        if not self.cache_dir:
            return None
        return Path(self.cache_dir) / hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _cache_get(self, key: str) -> bytes | None:
        path = self._cache_path(key)
        if path is None or not path.is_file():
            return None
        if time.time() - path.stat().st_mtime > self.cache_ttl:
            return None
        return path.read_bytes()

    def _cache_put(self, key: str, data: bytes) -> None:
        path = self._cache_path(key)
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)

    # ----- public helpers ----------------------------------------------
    def get_bytes(self, url: str, *, headers: dict[str, str] | None = None) -> bytes:
        """GET a URL (status 200 required). Memoized per process, plus the disk cache."""
        key = url + "|" + json.dumps(headers or {}, sort_keys=True)
        if key in self._memo:
            return self._memo[key]
        cached = self._cache_get(key)
        if cached is None:
            resp = self.request(url, headers=headers)
            if resp.status != 200:
                raise HttpError(f"HTTP {resp.status} for {url}", resp.status, url)
            cached = resp.body
            self._cache_put(key, cached)
        self._memo[key] = cached
        return cached

    def get_text(self, url: str) -> str:
        return self.get_bytes(url).decode("utf-8")

    def get_json(self, url: str):
        try:
            return json.loads(self.get_bytes(url).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HttpError(f"invalid JSON from {url}: {exc}", None, url) from exc

    def head(self, url: str, *, follow_redirects: bool = True) -> Response:
        """HEAD a URL. Falls back to a 1-byte ranged GET on 403/405."""
        try:
            return self.request(url, method="HEAD", follow_redirects=follow_redirects)
        except HttpError as exc:
            if exc.status not in (403, 405):
                raise
        return self.request(url, headers={"Range": "bytes=0-0"}, follow_redirects=follow_redirects)

    def sha256_of(self, url: str) -> str:
        """Stream-download ``url`` and return its sha256 hex digest."""
        digest = hashlib.sha256()
        resp = self.request(url, stream=True)
        with resp:
            while chunk := resp.read(_CHUNK):
                digest.update(chunk)
        return digest.hexdigest()

    def zip_root_dir(self, url: str) -> str:
        """Return the single top-level directory of a remote ZIP.

        Reads the end-of-central-directory and the central directory with HTTP
        Range requests. If the server ignores Range (answers 200), falls back to
        a full streamed download to a temp file and uses ``zipfile``.
        """
        # Suffix ranges ("bytes=-N") are not supported by every CDN (GitHub's
        # release-assets host answers 501), so learn the size first.
        size = _size_from(self.head(url))
        if not size:
            with self.request(url, stream=True) as full:
                return _root_from_full_download(full)
        start = max(0, size - _TAIL)
        resp = self.request(url, headers={"Range": f"bytes={start}-{size - 1}"}, stream=True)
        with resp:
            if resp.status == 200:
                return _root_from_full_download(resp)
            if resp.status != 206:
                raise HttpError(f"HTTP {resp.status} for {url}", resp.status, url)
            total = _content_range_total(resp.headers.get("Content-Range"))
            tail = resp.read()
        tail_start = total - len(tail)
        cd_offset, cd_size = _find_central_directory(tail, tail_start, lambda s, e: self._range(url, s, e))
        if cd_offset >= tail_start:
            cd = tail[cd_offset - tail_start : cd_offset - tail_start + cd_size]
        else:
            cd = self._range(url, cd_offset, cd_offset + cd_size - 1)
        return root_dir_from_names(_central_directory_names(cd))

    def _range(self, url: str, start: int, end: int) -> bytes:
        resp = self.request(url, headers={"Range": f"bytes={start}-{end}"})
        if resp.status != 206:
            raise HttpError(f"range request not honored for {url} (HTTP {resp.status})", resp.status, url)
        return resp.body


# ---------------------------------------------------------------------------
# ZIP parsing helpers (pure; unit tested)

_EOCD_SIG = b"PK\x05\x06"
_ZIP64_LOCATOR_SIG = b"PK\x06\x07"
_ZIP64_EOCD_SIG = b"PK\x06\x06"
_CD_SIG = b"PK\x01\x02"
_TAIL = 65557 + 20  # max comment + EOCD + zip64 locator


def _size_from(resp: Response) -> int | None:
    """Total size from a HEAD (Content-Length) or 1-byte ranged GET (Content-Range)."""
    if resp.status == 206:
        try:
            return _content_range_total(resp.header("content-range"))
        except HttpError:
            return None
    length = resp.header("content-length")
    return int(length) if length and length.isdigit() and int(length) > 0 else None


def _content_range_total(value: str | None) -> int:
    # "bytes 123-456/789"
    if not value or "/" not in value:
        raise HttpError(f"missing Content-Range total: {value!r}")
    total = value.rsplit("/", 1)[1].strip()
    if not total.isdigit():
        raise HttpError(f"unknown Content-Range total: {value!r}")
    return int(total)


def _find_central_directory(tail: bytes, tail_start: int, fetch) -> tuple[int, int]:
    """Return (offset, size) of the central directory from the file tail."""
    pos = tail.rfind(_EOCD_SIG)
    if pos < 0 or len(tail) - pos < 22:
        raise HttpError("ZIP end-of-central-directory not found")
    cd_size, cd_offset = struct.unpack("<II", tail[pos + 12 : pos + 20])
    if cd_offset == 0xFFFFFFFF or cd_size == 0xFFFFFFFF:
        loc = pos - 20
        if loc < 0 or tail[loc : loc + 4] != _ZIP64_LOCATOR_SIG:
            raise HttpError("ZIP64 locator not found")
        (eocd64_offset,) = struct.unpack("<Q", tail[loc + 8 : loc + 16])
        if eocd64_offset >= tail_start:
            rec = tail[eocd64_offset - tail_start : eocd64_offset - tail_start + 56]
        else:
            rec = fetch(eocd64_offset, eocd64_offset + 55)
        if rec[:4] != _ZIP64_EOCD_SIG:
            raise HttpError("ZIP64 end-of-central-directory not found")
        cd_size, cd_offset = struct.unpack("<QQ", rec[40:56])
    return cd_offset, cd_size


def _central_directory_names(cd: bytes) -> list[str]:
    names: list[str] = []
    pos = 0
    while pos + 46 <= len(cd) and cd[pos : pos + 4] == _CD_SIG:
        flags = struct.unpack("<H", cd[pos + 8 : pos + 10])[0]
        name_len, extra_len, comment_len = struct.unpack("<HHH", cd[pos + 28 : pos + 34])
        raw = cd[pos + 46 : pos + 46 + name_len]
        names.append(raw.decode("utf-8" if flags & 0x800 else "cp437"))
        pos += 46 + name_len + extra_len + comment_len
    if not names:
        raise HttpError("ZIP central directory is empty or unreadable")
    return names


def root_dir_from_names(names: list[str]) -> str:
    """The single top-level directory shared by every entry, else raise."""
    roots = set()
    for name in names:
        name = name.replace("\\", "/")
        head, sep, _ = name.partition("/")
        if not sep:
            raise HttpError(f"ZIP has a top-level file, not a single root directory: {name!r}")
        roots.add(head)
    if len(roots) != 1:
        raise HttpError(f"ZIP does not have exactly one top-level directory: {sorted(roots)[:5]}")
    return roots.pop()


def _root_from_full_download(resp) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "download.zip"
        with path.open("wb") as fh:
            while chunk := resp.read(_CHUNK):
                fh.write(chunk)
        with zipfile.ZipFile(path) as zf:
            return root_dir_from_names(zf.namelist())


_default: Client | None = None


def default_client() -> Client:
    """Process-wide client configured from the environment."""
    global _default
    if _default is None:
        _default = Client.from_env()
    return _default


def set_default_client(client: Client | None) -> None:
    """Replace the process-wide client (used by tests)."""
    global _default
    _default = client
