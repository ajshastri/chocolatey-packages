import json

import pytest

from chocotools import sources
from chocotools.sources import jmc
from conftest import pkg

TAGS = "https://api.github.com/repos/openjdk/jmc/tags?per_page=100"


def test_jmc9(fake_client):
    r = jmc.fetch(pkg(vendor="jmc", major=9, image=None), client=fake_client)
    assert r.version == "9.1.2"
    assert r.urls == {"x64": "https://download.java.net/java/GA/jmc9/05/binaries/jmc-9.1.2_windows-x64.zip"}
    assert r.sha256["x64"] == "2ccc7fd0c10b9da90cf0ac73c12c35358f233322c4362efcb17679f556495119"


def test_download_page_lagging_tag_fails(fake_client):
    tags = json.loads(fake_client.get_map[TAGS])
    tags.insert(0, {"name": "9.1.3-ga"})
    fake_client.get_map[TAGS] = json.dumps(tags).encode()
    with pytest.raises(sources.SourceError, match="download page not updated yet"):
        jmc.fetch(pkg(vendor="jmc", major=9, image=None), client=fake_client)
