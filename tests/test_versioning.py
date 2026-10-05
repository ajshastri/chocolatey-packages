import pytest

from chocotools import versioning
from chocotools.sources import SourceError, corretto, graalvm, jmc, liberica, mvnd, openjdk, sapmachine, temurin, wildfly, zulu


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("21.52.203.0", "21.52.203"),
        ("27", "27.0.0"),
        ("8.504.04.1", "8.504.4.1"),
        ("25.36.205", "25.36.205"),
        ("8.0.504", "8.0.504"),
        ("1.0", "1.0.0"),
        ("7.56.0.11", "7.56.0.11"),
    ],
)
def test_format(raw, expected):
    assert versioning.format(raw) == expected


def test_format_rejects_more_than_four_parts():
    with pytest.raises(versioning.VersionError):
        versioning.format("21.0.12.1.1")
    with pytest.raises(versioning.VersionError):
        versioning.parse("21.0.10.0.1")


def test_format_drops_trailing_zero_fifth_part_only_if_within_limit():
    assert versioning.format("21.0.12.0.0") == "21.0.12"


@pytest.mark.parametrize("bad", ["", "  ", "abc", "1..2", "1.2-beta", None])
def test_parse_rejects_bad(bad):
    with pytest.raises(versioning.VersionError):
        versioning.parse(bad)


def test_trailing_zero_equality_and_order():
    assert versioning.equal("21.52.203.0", "21.52.203")
    assert versioning.equal("8.502.07.1", "8.502.7.1")
    assert versioning.compare_nuget("8.0.504", "8.472.8") < 0  # the Temurin 8 scheme problem
    assert versioning.compare_nuget("8.504.1", "8.472.8") > 0
    assert versioning.compare_nuget("21.0.12.121", "21.0.12.81") > 0
    assert versioning.compare_nuget("27.0.0", "26.0.2.2") > 0
    assert versioning.compare_nuget("11.0.32.121", "11.0.32.102") > 0


def test_strip_helpers():
    assert versioning.strip_v("v1.0.6") == "1.0.6"
    assert versioning.strip_v("1.0.6") == "1.0.6"
    assert versioning.strip_final("41.0.1.Final") == "41.0.1"
    assert versioning.strip_ga("9.1.2-ga") == "9.1.2"
    assert versioning.strip_windows_n("2.56.0.windows.1") == "2.56.0"
    assert versioning.strip_build("21.0.12.1+1") == "21.0.12.1"
    assert versioning.join_parts([21, 52, 203, 0]) == "21.52.203.0"


# ----- per-vendor mappings with the real baseline values ---------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("jdk8u504-b01", "8.504.1"),
        ("jdk8u472-b08", "8.472.8"),
        ("jdk-21.0.12.1+1", "21.0.12.1"),
        ("jdk-25.0.4.1+1", "25.0.4.1"),
        ("jdk-21.0.13+8", "21.0.13"),
        ("jdk-11.0.32.1+1", "11.0.32.1"),
    ],
)
def test_temurin(raw, expected):
    assert temurin.normalize(raw) == expected


def test_temurin_rejects_unknown():
    with pytest.raises(SourceError):
        temurin.normalize("8.0.504+1")


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("8u504+1", "8.0.504.1"),
        ("21.0.12.1+1", "21.0.12.1"),
        ("17.0.20.1+1", "17.0.20.1"),
        ("11.0.32.1+1", "11.0.32.1"),
        ("21.0.12+10", "21.0.12"),
    ],
)
def test_liberica(raw, expected):
    assert liberica.normalize(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("21.0.12.12.1", "21.0.12.121"),
        ("11.0.32.12.1", "11.0.32.121"),
        ("17.0.20.12.1", "17.0.20.121"),
        ("25.0.4.10.1", "25.0.4.101"),
        ("21.0.12.8.1", "21.0.12.81"),
        ("8.504.04.1", "8.504.4.1"),
        ("8.502.07.1", "8.502.7.1"),
    ],
)
def test_corretto(raw, expected):
    assert corretto.normalize(raw) == expected


def test_corretto_rejects_odd_tags():
    with pytest.raises(SourceError):
        corretto.normalize("21.0.12")


def test_zulu():
    assert zulu.normalize([21, 52, 203, 0]) == "21.52.203"
    assert zulu.normalize([8, 96, 0, 205]) == "8.96.0.205"
    assert zulu.normalize([25, 36, 205, 0]) == "25.36.205"


def test_sapmachine():
    assert sapmachine.normalize("sapmachine-21.0.12.1") == "21.0.12.1"
    assert sapmachine.normalize("sapmachine-11.0.25") == "11.0.25"
    assert sapmachine.normalize("sapmachine-21") == "21.0.0"
    with pytest.raises(SourceError):
        sapmachine.normalize("sapmachine-21.0.10.0.1")


def test_graalvm():
    assert graalvm.normalize("25.3.4.1") == "25.3.4.1"
    assert graalvm.normalize("25.2.4") == "25.2.4"
    assert graalvm.normalize("21.0.2+13") == "21.0.2"
    with pytest.raises(SourceError):
        graalvm.normalize("17.0.9+9.1")
    with pytest.raises(SourceError):
        graalvm.normalize("25.4.4.1.1")


def test_openjdk():
    assert openjdk.normalize("27") == "27.0.0"
    assert openjdk.normalize("26.0.2.1") == "26.0.2.1"


def test_wildfly_mvnd_jmc():
    assert wildfly.normalize("41.0.1.Final") == "41.0.1"
    assert mvnd.normalize("1.0.6") == "1.0.6"
    assert mvnd.normalize("v1.0.6") == "1.0.6"
    assert jmc.normalize("9.1.2-ga") == "9.1.2"
