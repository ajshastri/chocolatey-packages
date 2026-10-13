import pytest

from chocotools import sources
from conftest import FakeClient, pkg


def test_lmc_is_unsupported():
    with pytest.raises(sources.SourceUnsupported, match="manual package"):
        sources.fetch(pkg(id="liberica-mission-control", vendor="lmc", major=None, image=None),
                      client=FakeClient(use_index=False))


def test_unknown_vendor():
    with pytest.raises(sources.SourceError):
        sources.module("foojay")
