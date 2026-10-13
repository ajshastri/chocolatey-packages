from pathlib import Path

import pytest

from chocotools import manifest

REPO = Path(__file__).resolve().parents[1]

ENTRY = """
[[package]]
id = "{id}"
folder = "{folder}"
vendor = "{vendor}"
major = 21
image = "jdk"
arch = ["x64"]
"""


def toml(*entries, ignore=None):
    head = f"ignore = {ignore!r}\n".replace("'", '"') if ignore else ""
    return head + "".join(ENTRY.format(**e) for e in entries)


def write_pkg(root: Path, folder: str, pid: str):
    (root / folder / "tools").mkdir(parents=True)
    (root / folder / f"{pid.lower()}.nuspec").write_text(
        f"<package><metadata><id>{pid}</id><version>1.0.0</version></metadata></package>", encoding="utf-8"
    )
    (root / folder / "tools" / "chocolateyinstall.ps1").write_text("$x = 'y'\n", encoding="utf-8")


def test_real_manifest_counts():
    mf = manifest.load(REPO)
    assert len(mf.packages) == 63
    frozen = sorted(p.id for p in mf.packages if p.frozen)
    assert frozen == sorted(
        ["zulu7", "sapmachine11", "sapmachine11jre", "graalvm-java17", "graalvm-java21", "liberica-mission-control"]
    )
    by = mf.by_id()
    assert by["wildfly"].arch == ("neutral",)
    assert by["Temurin8"].arch == ("x64",)
    assert by["libericajdklite"].variant == "lite"
    assert mf.ignore == ["FreeDownloadManager"]


def test_duplicate_id():
    with pytest.raises(manifest.ManifestError, match="duplicate package id"):
        manifest.parse(toml(dict(id="a", folder="a", vendor="zulu"), dict(id="A", folder="b", vendor="zulu")))


def test_unknown_vendor():
    with pytest.raises(manifest.ManifestError, match="unknown vendor"):
        manifest.parse(toml(dict(id="a", folder="a", vendor="foojay")))


def test_java_vendor_needs_image():
    with pytest.raises(manifest.ManifestError, match="'image' is required"):
        manifest.parse('[[package]]\nid="a"\nfolder="a"\nvendor="zulu"\nmajor=8\n')


def test_liberica_needs_variant():
    with pytest.raises(manifest.ManifestError, match="variant"):
        manifest.parse(toml(dict(id="a", folder="a", vendor="liberica")))


def test_bad_arch():
    with pytest.raises(manifest.ManifestError, match="arch"):
        manifest.parse('[[package]]\nid="w"\nfolder="w"\nvendor="wildfly"\narch=["arm64"]\n')


def test_select_unknown_id():
    mf = manifest.parse(toml(dict(id="a", folder="a", vendor="zulu")))
    assert [p.id for p in mf.select(["A"])] == ["a"]
    with pytest.raises(manifest.ManifestError, match="unknown package id"):
        mf.select(["nope"])


def test_check_tree_missing_folder_id_mismatch_and_unlisted(tmp_path):
    write_pkg(tmp_path, "a", "a")
    write_pkg(tmp_path, "b", "wrong")
    write_pkg(tmp_path, "stray", "stray")
    write_pkg(tmp_path, "FreeDownloadManager", "fdm")
    mf = manifest.parse(
        toml(
            dict(id="a", folder="a", vendor="zulu"),
            dict(id="b", folder="b", vendor="zulu"),
            dict(id="c", folder="missing", vendor="zulu"),
            ignore=["FreeDownloadManager"],
        )
    )
    errors = manifest.check_tree(tmp_path, mf)
    assert any("c: folder missing does not exist" in e for e in errors)
    assert any("nuspec <id> is 'wrong'" in e for e in errors)
    assert any(e.startswith("stray: has a nuspec but is not in packages.toml") for e in errors)
    assert not any("FreeDownloadManager" in e for e in errors)
    assert len(errors) == 3
