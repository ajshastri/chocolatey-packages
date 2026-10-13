"""Live smoke tests, one per source. Deselected by default; run with
``uv run pytest -m online`` (set CHOCOTOOLS_CACHE_DIR to save GitHub quota)."""

import pytest

from chocotools import checks, chocolatey, sources
from chocotools.http import Client
from conftest import pkg

pytestmark = pytest.mark.online

CASES = [
    pkg(vendor="temurin", major=21, image="jdk"),
    pkg(vendor="liberica", major=21, image="jdk", variant="lite"),
    pkg(vendor="sapmachine", major=21, image="jre"),
    pkg(vendor="zulu", major=21, image="jdk"),
    pkg(vendor="corretto", major=21, image="jdk"),
    pkg(vendor="graalvm", major=25, image="jdk"),
    pkg(vendor="openjdk", major=27, image="jdk"),
    pkg(vendor="wildfly", major=None, image=None, arch=("neutral",)),
    pkg(vendor="mvnd", major=None, image=None),
    pkg(vendor="jmc", major=9, image=None),
]


@pytest.fixture(scope="module")
def client():
    return Client.from_env()


@pytest.mark.parametrize("p", CASES, ids=lambda p: p.vendor)
def test_source_live(p, client):
    release = sources.fetch(p, client=client)
    assert checks.check_release(p, release) == []


def test_chocolatey_live(client):
    assert chocolatey.approved_version("zulu8", client)
