import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "skills" / "report-writing" / "scripts" / "check_report_sources.py"
spec = importlib.util.spec_from_file_location("check_report_sources", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

pytestmark = pytest.mark.skipif(shutil.which("latexindent") is None, reason="needs latexindent")

TEX = "\\documentclass{article}\n\\addbibresource{BIB}\n\\begin{document}\nText.\n\\end{document}\n"


def tex_with(bib):
    return TEX.replace("BIB", bib)


def run(root, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args],
                          text=True, capture_output=True)


def project(tmp_path, tex=tex_with("bib/lib.bib"), bib="@book{a,\n title={A},\n shorthand={A}\n}\n"):
    (tmp_path / "bib").mkdir()
    (tmp_path / "bib" / "lib.bib").write_text(bib)
    (tmp_path / "report.tex").write_text(tex)
    return tmp_path / "report.tex"


def formatted(tmp_path):
    """Return a source latexindent leaves unchanged."""
    src = project(tmp_path)
    run(tmp_path, "--write", str(src))
    return src


def test_clean_source_passes(tmp_path):
    src = formatted(tmp_path)
    result = run(tmp_path, str(src))
    assert result.returncode == 0, result.stdout + result.stderr


def test_unresolved_resource_and_duplicate_key_fail(tmp_path):
    src = project(tmp_path, tex=tex_with("bib/missing.bib"),
                  bib="@book{a,\n title={A}\n}\n@book{a,\n title={B}\n}\n")
    result = run(tmp_path, str(src))
    assert result.returncode == 1
    assert "DUPLICATE BIBLIOGRAPHY KEY a" in result.stdout
    assert "INVALID SHARED RESOURCE" in result.stdout


def test_resource_outside_library_fails(tmp_path):
    (tmp_path / "other.bib").write_text("@book{b,\n title={B}\n}\n")
    src = project(tmp_path, tex=tex_with("other.bib"))
    result = run(tmp_path, str(src))
    assert "INVALID SHARED RESOURCE" in result.stdout


def test_handwritten_bibliography_and_quantity_flagged(tmp_path):
    body = "\\begin{thebibliography}{1}\\end{thebibliography}\nA cut at 25 GeV.\n"
    src = project(tmp_path, tex=tex_with("bib/lib.bib").replace("Text.\n", body))
    result = run(tmp_path, "--quantities", str(src))
    assert "HANDWRITTEN BIBLIOGRAPHY" in result.stdout
    assert "REVIEW QUANTITY" in result.stdout


def test_omitted_sources_is_a_usage_error(tmp_path):
    result = run(tmp_path)
    assert result.returncode == 2
    assert "sources" in result.stderr


def test_source_outside_root_is_rejected(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "x.tex"
    outside.write_text(tex_with("x.bib"))
    result = run(root, str(outside))
    assert result.returncode != 0


def test_without_library_resources_only_need_to_exist(tmp_path):
    (tmp_path / "refs.bib").write_text("@book{a,\n title={A}\n}\n")
    src = tmp_path / "report.tex"
    src.write_text(tex_with("refs.bib"))
    run(tmp_path, "--write", str(src))
    assert run(tmp_path, str(src)).returncode == 0
    src.write_text(tex_with("nope.bib"))
    assert "INVALID SHARED RESOURCE" in run(tmp_path, str(src)).stdout
