import json

from chocotools import chocolatey, cli, sources
from chocotools.sources import Release
from conftest import FakeClient, copy_pkg

MANIFEST = """
[[package]]
id = "zulu8"
folder = "zulu-8"
vendor = "zulu"
major = 8
image = "jdk"
arch = ["x64"]

[[package]]
id = "graalvm-java17"
folder = "GraalVM-17"
vendor = "graalvm"
major = 17
image = "jdk"
arch = ["x64"]
frozen = true
"""


def make_repo(tmp_path):
    (tmp_path / "packages.toml").write_text(MANIFEST, encoding="utf-8")
    copy_pkg("zulu-8", tmp_path)
    copy_pkg("GraalVM-17", tmp_path)
    return tmp_path


def test_build_without_choco_exits_3(tmp_path, monkeypatch, capsys):
    root = make_repo(tmp_path)
    monkeypatch.setattr(cli, "choco_available", lambda: None)
    assert cli.main(["--root", str(root), "build", "--id", "zulu8"], client=FakeClient(use_index=False)) == 3
    assert "choco not found: build requires Windows + Chocolatey" in capsys.readouterr().err


def test_build_validates_first(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    script = root / "zulu-8/tools/chocolateyinstall.ps1"
    script.write_bytes(script.read_bytes().replace(b"https://cdn.azul.com/", b"https://aka.ms/"))
    monkeypatch.setattr(cli, "choco_available", lambda: None)
    assert cli.main(["--root", str(root), "build", "--id", "zulu8"], client=FakeClient(use_index=False)) == 1


def test_compare_md_and_json(tmp_path, monkeypatch):
    root = make_repo(tmp_path)

    def fetch(pkg, *, version=None, client=None):
        v = {"zulu8": "8.96.0.205", "graalvm-java17": "17.0.9"}[pkg.id]
        return Release(v, v, {"x64": "https://cdn.azul.com/a.msi"}, {"x64": "f" * 64}, "t")

    monkeypatch.setattr(sources, "fetch", fetch)
    monkeypatch.setattr(chocolatey, "approved_version", lambda pid, client=None: "8.96.0.205")
    out = root / "compare.md"
    assert cli.main(["--root", str(root), "compare", "--output", str(out)], client=FakeClient(use_index=False)) == 0
    text = out.read_text(encoding="utf-8")
    assert "| zulu-8 | zulu8 | 8.96.0.205 | 8.96.0.205 | 8.96.0.205 -> 8.96.0.205 | in-sync |" in text
    assert "| frozen |" in text
    out_json = root / "compare.json"
    cli.main(["--root", str(root), "compare", "--format", "json", "--output", str(out_json)],
             client=FakeClient(use_index=False))
    rows = json.loads(out_json.read_text(encoding="utf-8"))
    assert {r["id"]: r["status"] for r in rows} == {"zulu8": "in-sync", "graalvm-java17": "frozen"}
