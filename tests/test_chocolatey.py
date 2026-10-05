import pytest

from chocotools import chocolatey
from conftest import FIXTURES, FakeClient


def test_feed_url_quotes_id():
    assert chocolatey.feed_url("openjdk") == "https://community.chocolatey.org/api/v2/FindPackagesById()?id=%27openjdk%27"


def test_parse_page_has_next_link():
    entries, nxt = chocolatey.parse_page((FIXTURES / "chocolatey" / "openjdk-page1.xml").read_bytes())
    assert entries and all(isinstance(v, str) for v, _ in entries)
    assert nxt and "skiptoken" in nxt


def test_two_page_feed_follows_next(fake_client):
    versions = chocolatey.versions("openjdk", fake_client)
    pages = [c for c in fake_client.calls if "FindPackagesById" in c]
    assert len(pages) >= 2
    assert len(versions) > len(chocolatey.parse_page((FIXTURES / "chocolatey" / "openjdk-page1.xml").read_bytes())[0])
    assert chocolatey.approved_version("openjdk", fake_client) == "26.0.2.2"


def test_approved_ignores_unapproved():
    feed = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
      xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
 <entry><content><m:properties><d:Version>1.0.0</d:Version><d:IsApproved m:type="Edm.Boolean">true</d:IsApproved></m:properties></content></entry>
 <entry><content><m:properties><d:Version>2.0.0</d:Version><d:IsApproved m:type="Edm.Boolean">false</d:IsApproved></m:properties></content></entry>
 <entry><content><m:properties><d:Version>1.5.0-beta</d:Version><d:IsApproved m:type="Edm.Boolean">true</d:IsApproved></m:properties></content></entry>
</feed>"""
    client = FakeClient(get={chocolatey.feed_url("x"): feed}, use_index=False)
    assert chocolatey.approved_version("x", client) == "1.0.0"


def test_no_approved_versions_returns_none():
    feed = b'<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    client = FakeClient(get={chocolatey.feed_url("x"): feed}, use_index=False)
    assert chocolatey.approved_version("x", client) is None


def test_unreachable_feed_raises():
    with pytest.raises(chocolatey.ChocolateyError):
        chocolatey.approved_version("x", FakeClient(use_index=False))
