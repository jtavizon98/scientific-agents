"""Exercise a renderer adapter without requiring analyb or real research inputs."""

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run(*arguments):
    return subprocess.run([sys.executable, *map(str, arguments)], cwd=ROOT,
                          text=True, capture_output=True, timeout=90)


def test_custom_renderer_and_evidence_failures(tmp_path):
    output = tmp_path / "example"
    result = run(ROOT / "examples/custom-plotting/render.py",
                 "--renderer", "matplotlib", "--out", output)
    assert result.returncode == 0, result.stderr
    counts = json.loads((output / "counts.json").read_text())
    assert counts["counts"] == [2, 3, 1]
    assert counts["total"] == 6

    checker = ROOT / "scripts/render_gate.py"
    pdf = output / "example-counts.pdf"
    values = output / "values.json"
    result = run(checker, "numbers", pdf, values)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["matched_once"] == 4

    result = run(checker, "gate", "--session", output, "--pdf", pdf,
                 "--values", values, "--contract", output / "applicability.json",
                 "--out", output / "gate")
    assert result.returncode == 0, result.stderr
    gate = json.loads((output / "gate/gate.json").read_text())
    assert gate["ready_for_review"] is True
    assert gate["coverage"]["checks"]["inventory"]["status"] == "external"

    altered = json.loads(values.read_text())
    altered["values"][0]["text"] = "999"
    missing = output / "missing-value.json"
    missing.write_text(json.dumps(altered))
    result = run(checker, "numbers", pdf, missing)
    assert result.returncode == 1
    assert any(item["check"] == "value-missing" for item in json.loads(result.stdout)["findings"])

    source = output / "counts.json"
    source.write_text(source.read_text() + "\n")
    result = run(checker, "numbers", pdf, values)
    assert result.returncode == 1
    assert any(item["check"] == "source-stale" for item in json.loads(result.stdout)["findings"])

    result = run(ROOT / "examples/custom-plotting/render.py",
                 "--renderer", "matplotlib", "--out", output)
    assert result.returncode != 0
    assert json.loads(source.read_text()) == counts
