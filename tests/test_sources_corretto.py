import json
from datetime import datetime, timezone

import pytest

from chocotools import sources
from chocotools.sources import corretto
from conftest import FIXTURES, pkg

LATEST21 = "https://corretto.aws/downloads/latest/amazon-corretto-21-x64-windows-jdk.msi"


def test_corretto21(fake_client):
    r = corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)
    assert r.version == "21.0.12.121"
    assert r.version_raw == "21.0.12.12.1"
    assert r.urls["x64"] == "https://corretto.aws/downloads/resources/21.0.12.12.1/amazon-corretto-21.0.12.12.1-windows-x64.msi"
    expected = (FIXTURES / "corretto" / "amazon-corretto-21-x64-windows-jdk.msi.latest_sha256.txt").read_text().strip()
    assert r.sha256["x64"] == expected
    assert r.checksum_source == "corretto.aws latest_sha256"
    assert r.pending is None


def test_corretto8_jre(fake_client):
    r = corretto.fetch(pkg(vendor="corretto", major=8, image="jre"), client=fake_client)
    assert r.version == "8.504.4.1"
    assert r.urls["x64"].endswith("/8.504.04.1/amazon-corretto-8.504.04.1-windows-x64-jre.msi")


def test_latest_redirect_mismatch_fails(fake_client):
    fake_client.head_map[LATEST21] = {
        "status": 302,
        "headers": {"location": "/downloads/resources/21.0.13.1.1/amazon-corretto-21.0.13.1.1-windows-x64.msi"},
    }
    with pytest.raises(sources.SourceError, match="GitHub tag is 21.0.12.12.1"):
        corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)


GITHUB21 = "https://api.github.com/repos/corretto/corretto-21/releases/latest"
MSI21 = "https://corretto.aws/downloads/resources/{0}/amazon-corretto-{0}-windows-x64.msi"


def github_ahead(fake_client, tag="21.0.12.13.1", published="2026-10-13T18:02:11Z"):
    """GitHub has a newer tag than the corretto.aws latest link (live state on 2026-10-14)."""
    body = {"tag_name": tag, "draft": False, "prerelease": False, "assets": []}
    if published is not None:
        body["published_at"] = published
    fake_client.get_map[GITHUB21] = json.dumps(body).encode()
    fake_client.head_map[MSI21.format(tag)] = {"status": 403, "headers": {}}


def test_github_ahead_of_latest_link_is_pending(fake_client):
    github_ahead(fake_client)
    r = corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)
    # The served build is used: version, URL and checksum all from the latest link.
    assert (r.version, r.version_raw) == ("21.0.12.121", "21.0.12.12.1")
    assert r.urls["x64"] == MSI21.format("21.0.12.12.1")
    assert r.sha256["x64"] == "1e60e8033e843b29692a56a4dbaf5bcff13f39968fdd467699c14ae4ac88fad6"
    assert r.pending.version_raw == "21.0.12.13.1"
    assert r.pending.published_at == datetime(2026, 10, 13, 18, 2, 11, tzinfo=timezone.utc)
    assert r.pending.message() == ("GitHub 21.0.12.13.1 released 2026-10-13, corretto.aws latest still serves "
                                   "21.0.12.12.1 (versioned MSI HTTP 403)")
    assert "HEAD " + MSI21.format("21.0.12.13.1") in fake_client.calls


def test_pending_reports_unreachable_versioned_msi(fake_client):
    github_ahead(fake_client)
    del fake_client.head_map[MSI21.format("21.0.12.13.1")]  # FakeClient raises HttpError(404)
    r = corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)
    assert r.pending.detail == "corretto.aws latest still serves 21.0.12.12.1 (versioned MSI HTTP 404)"


def test_latest_link_moved_but_github_newer_still(fake_client):
    # corretto.aws moved to 21.0.12.13.1 while GitHub is already at 21.0.13.5.1: use the served build.
    github_ahead(fake_client, tag="21.0.13.5.1")
    fake_client.head_map[LATEST21] = {"status": 302, "headers": {"location": MSI21.format("21.0.12.13.1")}}
    r = corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)
    assert (r.version, r.version_raw) == ("21.0.12.131", "21.0.12.13.1")
    assert r.urls["x64"] == MSI21.format("21.0.12.13.1")
    assert r.checksum_source == "corretto.aws latest_sha256"
    assert r.pending.version_raw == "21.0.13.5.1"


def test_pending_needs_published_at(fake_client):
    github_ahead(fake_client, published=None)
    with pytest.raises(sources.SourceError, match="published_at is missing"):
        corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)


def test_latest_link_to_another_file_fails(fake_client):
    fake_client.head_map[LATEST21] = {"status": 302, "headers": {"location": "/downloads/latest/other.msi"}}
    with pytest.raises(sources.SourceError, match="not a jdk MSI"):
        corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)


def test_no_redirect_fails(fake_client):
    fake_client.head_map[LATEST21] = {"status": 200, "headers": {}}
    with pytest.raises(sources.SourceError, match="did not redirect"):
        corretto.fetch(pkg(vendor="corretto", major=21), client=fake_client)


def test_jre_only_for_8():
    with pytest.raises(sources.SourceError):
        corretto.filename(pkg(vendor="corretto", major=21, image="jre"), "21.0.12.12.1")
