import pytest

from chocotools import sources
from chocotools.sources import sapmachine
from conftest import FakeClient, pkg


@pytest.mark.parametrize("major, image", [(21, "jdk"), (21, "jre")])
def test_sapmachine21(fake_client, major, image):
    r = sapmachine.fetch(pkg(vendor="sapmachine", major=major, image=image), client=fake_client)
    assert r.version == "21.0.12.1"
    assert r.urls["x64"] == (
        f"https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.12.1/"
        f"sapmachine-{image}-21.0.12.1_windows-x64_bin.msi"
    )
    assert len(r.sha256["x64"]) == 64


def test_sapmachine17(fake_client):
    r = sapmachine.fetch(pkg(vendor="sapmachine", major=17, image="jdk"), client=fake_client)
    assert r.version == "17.0.20.1"


def test_pinned_11_0_25_uses_sha256_txt_fallback(fake_client):
    r = sapmachine.fetch(pkg(vendor="sapmachine", major=11, image="jdk"), version="11.0.25", client=fake_client)
    assert r.version == "11.0.25"
    assert r.urls["x64"].endswith("/sapmachine-11.0.25/sapmachine-jdk-11.0.25_windows-x64_bin.msi")
    assert r.sha256["x64"] == "35c9e4f580b8869700b75c57cac8f98b3c61693cbd261d4afeab293ab95eeaa2"
    assert r.checksum_source.endswith(".sha256.txt")


def test_latest_11_has_no_windows_msi_on_first_page(fake_client):
    # 11.0.26+ ship Linux only; page 2 was not recorded -> fails closed.
    with pytest.raises(sources.SourceError):
        sources.fetch(pkg(vendor="sapmachine", major=11, image="jdk"), client=fake_client)


def test_candidate_rules():
    p = pkg(vendor="sapmachine", major=21, image="jdk")
    asset = {"name": "sapmachine-jdk-21.0.13_windows-x64_bin.msi"}
    assert sapmachine._candidate(p, {"tag_name": "sapmachine-21.0.13", "prerelease": False, "assets": [asset]})
    assert not sapmachine._candidate(p, {"tag_name": "sapmachine-21.0.13", "prerelease": True, "assets": [asset]})
    assert not sapmachine._candidate(p, {"tag_name": "sapmachine-21.0.13", "prerelease": False, "assets": []})
    assert not sapmachine._candidate(p, {"tag_name": "sapmachine-17.0.13", "prerelease": False, "assets": [asset]})


def test_five_part_winner_fails_instead_of_picking_older():
    p = pkg(vendor="sapmachine", major=21, image="jdk")
    rels = [
        {"tag_name": t, "prerelease": False,
         "assets": [{"name": f"sapmachine-jdk-{t[11:]}_windows-x64_bin.msi", "digest": "sha256:" + "d" * 64,
                     "browser_download_url": f"https://github.com/SAP/SapMachine/releases/download/{t}/x.msi"}]}
        for t in ("sapmachine-21.0.12.1", "sapmachine-21.0.12.1.1")
    ]
    import json

    client = FakeClient(get={"https://api.github.com/repos/SAP/SapMachine/releases?per_page=100&page=1": json.dumps(rels)},
                        use_index=False)
    with pytest.raises(sources.SourceError, match="more than 4 parts"):
        sources.fetch(p, client=client)
