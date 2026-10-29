import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("check_repo", Path(__file__).parents[1] / "tools" / "check_repo.py")
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)

SOURCE = "metadata:\n  source: https://github.com/o/r/blob/abc1234/base/skills/alpha/SKILL.md\n"
GOOD = "---\nname: alpha\ndescription: Does a thing.\nlicense: MIT; see LICENSE.txt\n" + SOURCE + "---\n\n# Alpha\n"


def tree(tmp_path, skill=GOOD, readme="See [alpha](skills/alpha/SKILL.md#x), [web](https://x.org), [here](#top).\n"):
    folder = tmp_path / "skills" / "alpha"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(skill)
    (folder / "LICENSE.txt").write_text("MIT")
    (tmp_path / "README.md").write_text(readme)
    return tmp_path


def run(root, capsys):
    code = check.main([str(root)])
    return code, capsys.readouterr().out


def test_passing_tree(tmp_path, capsys):
    assert run(tree(tmp_path), capsys) == (0, "\n")


def test_wrong_name(tmp_path, capsys):
    code, out = run(tree(tmp_path, GOOD.replace("name: alpha", "name: beta")), capsys)
    assert code == 1 and "skills/alpha/SKILL.md" in out and "'beta'" in out


def test_missing_description(tmp_path, capsys):
    code, out = run(tree(tmp_path, GOOD.replace("description: Does a thing.\n", "")), capsys)
    assert code == 1 and "empty description" in out


def test_missing_license_file(tmp_path, capsys):
    root = tree(tmp_path)
    (root / "skills" / "alpha" / "LICENSE.txt").unlink()
    code, out = run(root, capsys)
    assert code == 1 and "LICENSE.txt" in out


def test_broken_link(tmp_path, capsys):
    code, out = run(tree(tmp_path, readme="[gone](docs/missing.md#a)\n```\n[ignored](nope.md)\n```\n"), capsys)
    assert code == 1
    assert out.strip() == "README.md: broken link docs/missing.md#a"


def test_adapted_skill_needs_pin(tmp_path, capsys):
    code, out = run(tree(tmp_path, GOOD.replace(SOURCE, "")), capsys)
    assert code == 1 and "metadata.source" in out


def test_adapted_skill_quoted_pin_passes(tmp_path, capsys):
    for quote in "'\"":
        quoted = SOURCE.replace("https", quote + "https").replace("SKILL.md", "SKILL.md" + quote)
        assert run(tree(tmp_path / ("q" + str(ord(quote))), GOOD.replace(SOURCE, quoted)), capsys) == (0, "\n")


def test_adapted_skill_malformed_pin(tmp_path, capsys):
    code, out = run(tree(tmp_path, GOOD.replace("blob", "tree")), capsys)
    assert code == 1 and "metadata.source" in out


def test_plugin_manifest_must_list_each_skill(tmp_path, capsys):
    root = tree(tmp_path)
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text('{"skills": ["./skills/gone"]}')
    code, out = run(root, capsys)
    assert code == 1
    assert "add ./skills/alpha" in out and "remove ./skills/gone" in out
