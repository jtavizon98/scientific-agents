import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("upstream_issues", Path(__file__).parents[1] / "tools" / "upstream_issues.py")
ui = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ui)

TITLE = "Upstream changed: unslop (o/r/base/skills/unslop)"


def pin(sha="b", commit="abc1234", **extra):
    return {"pins": [dict({"skill": "unslop", "owner": "o", "repo": "r", "commit": commit, "parent": "base/skills",
                           "dir": "unslop", "status": "changed", "branch": "main", "upstream_sha": sha}, **extra)],
            "new_folders": []}


@pytest.fixture
def calls(monkeypatch):
    class Log(list):
        pass
    log = Log()
    log.state = state = {"found": []}

    def fake(*args):
        log.append(args)
        return json.dumps(state["found"]) if args[:2] == ("issue", "list") else ""
    monkeypatch.setattr(ui, "gh", fake)
    return log


def run(report, capsys):
    for title, body, state in ui.issues(report):
        ui.upsert(title, body, state)
    return capsys.readouterr().out


def verbs(calls):
    return [c[1] for c in calls if c[1] != "list"]


def test_title_has_no_pin():
    assert next(ui.issues(pin()))[0] == TITLE


def test_open_match_edited(calls, capsys):
    calls.state["found"] = [{"number": 7, "title": TITLE, "state": "OPEN", "body": "", "closedAt": None}]
    assert "updated #7" in run(pin(), capsys)
    assert verbs(calls) == ["edit"] and "<!-- upstream-tree: b -->" in calls[-1][-1]


def test_closed_same_sha_skipped(calls, capsys):
    calls.state["found"] = [{"number": 3, "title": TITLE, "state": "CLOSED", "body": ui.marker("b") + "\nold",
                             "closedAt": "2026-01-02T00:00:00Z"}]
    assert "acknowledged in #3" in run(pin(), capsys)
    assert verbs(calls) == []


def test_closed_different_sha_creates(calls, capsys):
    calls.state["found"] = [
        {"number": 3, "title": TITLE, "state": "CLOSED", "body": ui.marker("a"), "closedAt": "2026-01-02T00:00:00Z"},
        {"number": 2, "title": TITLE, "state": "CLOSED", "body": ui.marker("b"), "closedAt": "2026-01-01T00:00:00Z"}]
    assert "created" in run(pin(), capsys)  # only the most recent closed issue counts
    assert verbs(calls) == ["create"]


def test_no_match_creates(calls, capsys):
    assert "created" in run(pin(), capsys) and verbs(calls) == ["create"]


def test_repin_same_title(calls, capsys):
    calls.state["found"] = [{"number": 7, "title": TITLE, "state": "OPEN", "body": "", "closedAt": None}]
    run(pin(commit="def5678"), capsys)
    assert verbs(calls) == ["edit"]


def test_missing_filed(calls, capsys):
    report = pin(status="missing", detail="base/skills no longer exists on main (removed or moved)")
    del report["pins"][0]["upstream_sha"]
    run(report, capsys)
    assert verbs(calls) == ["create"] and "no longer exists" in calls[-1][-1] and "upstream-tree: missing" in calls[-1][-1]
