"""Synthetic bibliography fixtures; no external source metadata is asserted."""

import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
from unittest import mock

import pytest


SCRIPT = Path(__file__).parents[1] / "skills" / "source-library" / "scripts" / "check_bibliography.py"
SPEC = importlib.util.spec_from_file_location("check_bibliography", SCRIPT)
bibliography = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bibliography)
needs_biber = pytest.mark.skipif(shutil.which("biber") is None, reason="Biber not installed")


def library(tmp_path, name="library.bib", text="@book{key,title={Synthetic}}"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_explicit_paths_required():
    with pytest.raises(SystemExit) as error:
        bibliography.main([])
    assert error.value.code == 2
    assert bibliography.check_bibliography([])


@pytest.mark.parametrize("value", ["0", "-1", "inf", "nan", "bad"])
def test_invalid_timeout(value):
    with pytest.raises(SystemExit) as error:
        bibliography.main(["--timeout", value, "library.bib"])
    assert error.value.code == 2


def test_invalid_paths_do_not_invoke_biber(tmp_path):
    with mock.patch.object(bibliography.subprocess, "run") as run:
        assert bibliography.check_bibliography([tmp_path])
        assert bibliography.check_bibliography([tmp_path / "missing.bib"])
        assert bibliography.check_bibliography([library(tmp_path, "wrong.txt")])
    run.assert_not_called()


def test_missing_biber(tmp_path):
    with mock.patch.object(bibliography.shutil, "which", return_value=None):
        assert "not found" in bibliography.check_bibliography([library(tmp_path)])[0]


@pytest.mark.parametrize("failure, expected", [
    (subprocess.TimeoutExpired("biber", 0.1), "timed out"),
    (OSError("cannot execute"), "could not run Biber"),
])
def test_subprocess_failure(tmp_path, failure, expected):
    source = library(tmp_path)
    with mock.patch.object(bibliography.shutil, "which", return_value="/fake/biber"), \
            mock.patch.object(bibliography.subprocess, "run", side_effect=failure) as run:
        findings = bibliography.check_bibliography([source], timeout=0.1)
    assert expected in findings[0]
    assert str(source) in findings[0]
    assert run.call_args.kwargs["timeout"] == 0.1
    assert not Path(run.call_args.kwargs["cwd"]).exists()


@pytest.mark.parametrize("code, output, expected", [
    (7, "unusual failure", "exit 7"),
    (0, "WARN - Duplicate entry key: 'key'", "Duplicate entry key"),
    (0, "", "missing Biber XML"),
])
def test_biber_failure_warning_or_missing_output(tmp_path, code, output, expected):
    source = library(tmp_path)
    result = subprocess.CompletedProcess([], code, output, "")
    with mock.patch.object(bibliography.shutil, "which", return_value="/fake/biber"), \
            mock.patch.object(bibliography.subprocess, "run", return_value=result):
        assert expected in bibliography.check_bibliography([source])[0]


def test_invalid_xml_and_portable_temporary_directory_fallback(tmp_path):
    source = library(tmp_path)
    working_directories = []

    def fake_biber(command, **kwargs):
        working_directories.append(kwargs["cwd"])
        output = next(item.split("=", 1)[1] for item in command
                      if item.startswith("--output-file="))
        Path(output).write_text("not XML", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    real_temporary_directory = bibliography.tempfile.TemporaryDirectory
    with mock.patch.object(bibliography.shutil, "which", return_value="/fake/biber"), \
            mock.patch.object(Path, "is_dir", return_value=False), \
            mock.patch.object(bibliography.tempfile, "TemporaryDirectory",
                              wraps=real_temporary_directory) as temporary, \
            mock.patch.object(bibliography.subprocess, "run", side_effect=fake_biber):
        findings = bibliography.check_bibliography([source])
    assert "invalid or missing Biber XML" in findings[0]
    assert temporary.call_args.kwargs["dir"] is None
    assert not working_directories[0].exists()


@needs_biber
def test_nested_comments_macros_and_no_input_writes(tmp_path):
    source = library(tmp_path, "spaces [literal].bib", r'''
% A line comment containing @book{not-an-entry}
@comment{An ignored comment with {nested braces} and @book{fake}}
@string{label = "Synthetic"}
@book{alpha, title={A {nested {title}}}, shorthand=label # " A"}
@article(beta, title="A {quoted} title", shorthand={})
@misc{gamma, title={Last}, shorthand={   }}
''')
    original = source.read_bytes()
    # A project-local Biber configuration must not alter the check.
    (tmp_path / "biber.conf").write_text("not valid XML", encoding="utf-8")
    before = set(tmp_path.iterdir())
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        assert bibliography.main([str(source)]) == 0
    assert "were not checked" in stdout.getvalue()
    assert source.read_bytes() == original
    assert set(tmp_path.iterdir()) == before


@needs_biber
def test_cross_library_duplicate_keys_and_expanded_shorthands(tmp_path):
    first = library(tmp_path, "first.bib", '''
@string{prefix="Shared"}
@book{same, title={First}, shorthand=prefix # " label"}
''')
    second = library(tmp_path, "second.bib", '''
@article{same, title={Second}, shorthand={different}}
@misc{other, title={Third}, shorthand={Shared label}}
''')
    findings = bibliography.check_bibliography([first, second])
    assert len(findings) == 2
    assert "Duplicate key 'same'" in findings[0]
    assert "Duplicate shorthand 'Shared label'" in findings[1]
    assert all(str(first) in item and str(second) in item for item in findings)


@needs_biber
@pytest.mark.parametrize("text, expected", [
    ("@book{same,title={One}}\n@misc{same,title={Two}}", "Duplicate entry key"),
    ("@book{a,shorthand={S}}\n@misc{b,shorthand={S}}", "Duplicate shorthand"),
    ("@book{broken,title={Unclosed}", "syntax error"),
    ("@book{broken title={Missing comma}}", "syntax error"),
    ("@book{a,shorthand=undefinedmacro}", "WARN"),
])
def test_real_biber_findings(tmp_path, text, expected):
    source = library(tmp_path, text=text)
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        assert bibliography.main([str(source)]) == 1
    assert expected in stderr.getvalue()
    assert str(source) in stderr.getvalue()


@needs_biber
def test_same_library_supplied_twice_is_not_silently_deduplicated(tmp_path):
    source = library(tmp_path)
    assert "Duplicate key" in bibliography.check_bibliography([source, source])[0]
