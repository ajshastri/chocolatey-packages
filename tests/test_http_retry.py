"""Retry policy, backoff budget and circuit breaker of ``http.Client`` (fake sleep/clock/jitter)."""

import io
import urllib.error

import pytest

from chocotools import chocolatey, http

FEED = "https://community.chocolatey.org/api/v2/FindPackagesById()?id=%27x%27"
OTHER = "https://api.example.com/v1/x"


class Clock:
    def __init__(self):
        self.t = 1000.0
        self.sleeps: list[float] = []

    def __call__(self):
        return self.t

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.t += seconds


class Resp(io.BytesIO):
    def __init__(self, url, body=b"ok"):
        super().__init__(body)
        self.status = 200
        self.headers = {}
        self._url = url

    def geturl(self):
        return self._url


def http_error(url, code, headers=None):
    return urllib.error.HTTPError(url, code, "x", headers or {}, None)


def make_client(outcomes, **kw):
    """A Client whose ``_open`` plays ``outcomes`` (exceptions are raised, None answers 200)."""
    clock = Clock()
    lines: list[str] = []
    jitter: list[tuple[float, float]] = []

    def uniform(low, high):
        jitter.append((low, high))
        return high  # the top of the full-jitter range, so waits are predictable

    client = http.Client(sleep=clock.sleep, clock=clock, uniform=uniform, log=lines.append, **kw)
    calls: list[str] = []
    queue = list(outcomes)

    def fake_open(req, follow_redirects):
        calls.append(req.full_url)
        outcome = queue.pop(0) if queue else None
        if isinstance(outcome, BaseException):
            raise outcome
        return Resp(req.full_url)

    client._open = fake_open
    client.outcomes = queue  # tests may clear or refill it
    return client, clock, lines, jitter, calls


def test_other_host_retries_then_succeeds():
    client, clock, lines, jitter, calls = make_client([http_error(OTHER, 503), TimeoutError("The read operation timed out")])
    assert client.request(OTHER).body == b"ok"
    assert len(calls) == 3
    assert lines == [
        "retry 1 for api.example.com: HTTP 503; waiting 2.0s (3 of 4 retries left)",
        "retry 2 for api.example.com: The read operation timed out; waiting 4.0s (2 of 4 retries left)",
    ]
    assert jitter == [(0.0, 2.0), (0.0, 4.0)]


def test_other_host_gives_up_after_4_retries():
    client, clock, lines, jitter, calls = make_client([http_error(OTHER, 503)] * 10)
    with pytest.raises(http.HttpError, match=r"^HTTP 503 for https://api.example.com/v1/x$") as info:
        client.request(OTHER)
    assert info.value.status == 503
    assert len(calls) == 1 + http.DEFAULT_RETRIES == 5
    assert jitter == [(0.0, 2.0), (0.0, 4.0), (0.0, 8.0), (0.0, 16.0)]
    assert lines[-1] == "retry 4 for api.example.com: HTTP 503; waiting 16.0s (0 of 4 retries left)"


def test_other_host_wait_is_capped_at_30s():
    backoff = http.Backoff(http.RetryPolicy("h", http.DEFAULT_RETRY_BASE, http.DEFAULT_RETRY_CAP), clock=Clock(),
                           uniform=lambda low, high: high)
    assert [backoff.next_wait() for _ in range(6)] == [2.0, 4.0, 8.0, 16.0, 30.0, 30.0]


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_non_retryable_status_fails_at_once(code):
    client, clock, lines, jitter, calls = make_client([http_error(FEED, code)])
    with pytest.raises(http.HttpError, match=f"HTTP {code} for") as info:
        client.request(FEED)
    assert info.value.status == code
    assert len(calls) == 1 and lines == [] and jitter == []


def test_feed_retries_with_backoff_then_succeeds():
    client, clock, lines, jitter, calls = make_client([http_error(FEED, 503), http_error(FEED, 504),
                                                       ConnectionResetError("connection reset")])
    assert client.request(FEED).body == b"ok"
    assert jitter == [(0.0, 5.0), (0.0, 10.0), (0.0, 20.0)]
    assert lines == [
        "retry 1 for community.chocolatey.org: HTTP 503; waiting 5.0s (budget left 900s)",
        "retry 2 for community.chocolatey.org: HTTP 504; waiting 10.0s (budget left 895s)",
        "retry 3 for community.chocolatey.org: connection reset; waiting 20.0s (budget left 885s)",
    ]


def test_feed_honors_retry_after_capped_at_120s():
    client, clock, lines, jitter, calls = make_client([http_error(FEED, 429, {"Retry-After": "7"}),
                                                       http_error(FEED, 503, {"Retry-After": "600"})])
    assert client.request(FEED).body == b"ok"
    assert jitter == []  # Retry-After replaces the jittered wait
    assert lines == [
        "retry 1 for community.chocolatey.org: HTTP 429; waiting 7.0s (budget left 900s)",
        "retry 2 for community.chocolatey.org: HTTP 503; waiting 120.0s (budget left 893s)",
    ]


def test_feed_budget_exhaustion_then_circuit_breaker():
    client, clock, lines, jitter, calls = make_client([http_error(FEED, 503)] * 50, feed_budget=300)
    start = clock.t
    with pytest.raises(http.HttpError) as info:
        client.request(FEED)
    assert str(info.value) == ("Chocolatey feed unavailable: gave up after 5 min of retries; last error: "
                               f"HTTP 503 for {FEED}")
    assert info.value.status == 503
    # 5 + 10 + 20 + 40 + 80 + 120, then the 25 s left of the budget
    assert clock.t - start == 300
    assert [line.split("waiting ")[1] for line in lines] == [
        "5.0s (budget left 300s)", "10.0s (budget left 295s)", "20.0s (budget left 285s)",
        "40.0s (budget left 265s)", "80.0s (budget left 225s)", "120.0s (budget left 145s)",
        "25.0s (budget left 25s)"]
    assert len(calls) == 8

    # Later feed requests in the same run fail at once, without touching the network.
    other_feed = "https://community.chocolatey.org/api/v2/FindPackagesById()?id=%27y%27"
    before = (len(calls), clock.t)
    with pytest.raises(http.HttpError, match=r"^Chocolatey feed unavailable \(gave up after 5 min of retries "
                                             r"earlier in this run\)$"):
        client.request(other_feed)
    assert (len(calls), clock.t) == before
    # Other hosts are not affected.
    client.outcomes.clear()
    assert client.request(OTHER).body == b"ok"


def test_feed_circuit_breaker_message_through_chocolatey():
    client, *_ = make_client([http_error(FEED, 503)] * 50, feed_budget=0)
    with pytest.raises(chocolatey.ChocolateyError, match="Chocolatey feed unreachable for x: Chocolatey feed "
                                                         "unavailable: gave up after 0s of retries"):
        chocolatey.approved_version("x", client)
    with pytest.raises(chocolatey.ChocolateyError, match=r"unavailable \(gave up after 0s of retries earlier"):
        chocolatey.approved_version("y", client)


def test_feed_budget_from_environment(monkeypatch):
    monkeypatch.setenv(http.FEED_RETRY_BUDGET_ENV, "12")
    assert http.retry_policy("community.chocolatey.org").budget == 12
    assert http.retry_policy("push.chocolatey.org").budget == 12
    assert http.retry_policy("community.chocolatey.org", feed_budget=3).budget == 3
    monkeypatch.delenv(http.FEED_RETRY_BUDGET_ENV)
    assert http.retry_policy("community.chocolatey.org").budget == http.FEED_RETRY_BUDGET == 900
    monkeypatch.setenv(http.FEED_RETRY_BUDGET_ENV, "soon")
    with pytest.raises(http.HttpError, match="CHOCOTOOLS_FEED_RETRY_BUDGET must be a number of seconds"):
        http.retry_policy("community.chocolatey.org")


def test_policy_constants():
    feed = http.retry_policy("community.chocolatey.org")
    assert (feed.base, feed.cap, feed.max_retries, feed.circuit_breaker) == (5.0, 120.0, None, True)
    other = http.retry_policy("api.github.com")
    assert (other.base, other.cap, other.max_retries, other.budget, other.circuit_breaker) == (2.0, 30.0, 4, None,
                                                                                              False)


def test_retry_log_goes_to_stderr_with_key_redacted(monkeypatch, capsys):
    monkeypatch.setenv("CHOCO_KEY", "secret-key")
    client, clock, lines, jitter, calls = make_client([urllib.error.URLError("refused by secret-key proxy")])
    client.log = http.log_stderr
    assert client.request(FEED).body == b"ok"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ("retry 1 for community.chocolatey.org: <urlopen error refused by *** proxy>; "
                            "waiting 5.0s (budget left 900s)\n")
