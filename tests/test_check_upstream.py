import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("check_upstream", Path(__file__).parents[1] / "tools" / "check_upstream.py")
up = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(up)

SKILL = ("---\nname: unslop\ndescription: x\nmetadata:\n"
         "  source: https://github.com/o/r/blob/abc1234/base/skills/unslop/SKILL.md\n---\nbody\n")


def listing(**shas):
    return [{"name": n, "type": "dir", "sha": s} for n, s in shas.items()]


@pytest.fixture
def root(tmp_path):
    (tmp_path / "skills" / "unslop").mkdir(parents=True)
    (tmp_path / "skills" / "unslop" / "SKILL.md").write_text(SKILL)
    return tmp_path


def serve(monkeypatch, old, new):
    def fake(path):
        if path == "/repos/o/r":
            return {"default_branch": "main"}
        assert path.startswith("/repos/o/r/contents/base/skills?ref=")
        ref = path.rsplit("=", 1)[1]
        if isinstance(new, up.ApiError) and ref == "main":
            raise new
        return old if ref == "abc1234" else new
    monkeypatch.setattr(up, "fetch", fake)


def run(root, capsys):
    code = up.main(["--json", "--root", str(root)])
    return code, json.loads(capsys.readouterr().out)


def test_read_pins(root):
    assert up.read_pins(root) == [{"skill": "unslop", "owner": "o", "repo": "r", "commit": "abc1234",
                                   "parent": "base/skills", "dir": "unslop"}]


def test_unchanged(root, monkeypatch, capsys):
    serve(monkeypatch, listing(unslop="a"), listing(unslop="a"))
    code, report = run(root, capsys)
    assert code == 0 and report["pins"][0]["status"] == "unchanged" and report["new_folders"] == []


def test_changed(root, monkeypatch, capsys):
    serve(monkeypatch, listing(unslop="a"), listing(unslop="b"))
    code, report = run(root, capsys)
    assert code == 1
    assert report["pins"][0]["compare"] == "https://github.com/o/r/compare/abc1234...main"


def test_missing(root, monkeypatch, capsys):
    serve(monkeypatch, listing(unslop="a"), listing(other="b"))
    code, report = run(root, capsys)
    assert code == 1 and report["pins"][0]["status"] == "missing"


def test_new_folder(root, monkeypatch, capsys):
    serve(monkeypatch, listing(unslop="a"), listing(unslop="a", fresh="c"))
    code, report = run(root, capsys)
    assert code == 1 and report["new_folders"][0]["folders"] == ["fresh"]


def test_api_error(root, monkeypatch, capsys):
    serve(monkeypatch, listing(unslop="a"), up.ApiError(403, "rate limited"))
    code, report = run(root, capsys)
    assert code == 2 and report["pins"][0]["status"] == "error" and "403" in report["pins"][0]["detail"]


def test_text_output(root, monkeypatch, capsys):
    serve(monkeypatch, listing(unslop="a"), listing(unslop="b"))
    assert up.main(["--root", str(root)]) == 1
    assert capsys.readouterr().out.startswith("unslop: changed https://github.com/o/r/compare/")


def quoted(quote):
    return SKILL.replace("source: ", f"source: {quote}").replace("SKILL.md\n", f"SKILL.md{quote}\n")


def test_read_pins_also_source(root):
    text = SKILL.replace("---\nbody", "  also-source: https://github.com/o/r/blob/abc1234/base/skills/how/SKILL.md\n---\nbody")
    (root / "skills" / "unslop" / "SKILL.md").write_text(text)
    assert [pin["dir"] for pin in up.read_pins(root)] == ["unslop", "how"]


@pytest.mark.parametrize("quote", ["'", '"'])
def test_read_pins_quoted(root, quote):
    (root / "skills" / "unslop" / "SKILL.md").write_text(quoted(quote))
    assert up.read_pins(root)[0]["dir"] == "unslop"


@pytest.mark.parametrize("text", [
    SKILL.replace("  source: https://github.com/o/r/blob/abc1234/base/skills/unslop/SKILL.md\n", ""),
    SKILL.replace("blob/abc1234", "tree/abc1234"),
    SKILL.replace("/SKILL.md", ""),
])
def test_parse_pin_rejects(text):
    assert up.parse_pin(text) is None


def test_no_pins_exits_2(tmp_path, capsys):
    (tmp_path / "skills").mkdir()
    code, report = run(tmp_path, capsys)
    assert code == 2 and report["pins"] == []


def test_upstream_sha_reported(root, monkeypatch, capsys):
    serve(monkeypatch, listing(unslop="a"), listing(unslop="b"))
    assert run(root, capsys)[1]["pins"][0]["upstream_sha"] == "b"


def test_renamed_parent_is_missing(root, monkeypatch, capsys):
    def fake(path):
        if path == "/repos/o/r":
            return {"default_branch": "main"}
        if path.endswith("ref=main"):
            raise up.ApiError(404, "Not Found")
        return listing(unslop="a")
    monkeypatch.setattr(up, "fetch", fake)
    code, report = run(root, capsys)
    pin = report["pins"][0]
    assert code == 1 and pin["status"] == "missing" and "base/skills no longer exists" in pin["detail"]
    assert report["new_folders"] == []


def test_missing_repo_is_error(root, monkeypatch, capsys):
    monkeypatch.setattr(up, "fetch", lambda path: (_ for _ in ()).throw(up.ApiError(404, "Not Found")))
    code, report = run(root, capsys)
    assert code == 2 and report["pins"][0]["status"] == "error"
