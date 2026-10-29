#!/usr/bin/env python3
"""Read-only, resumable monitoring for PanDA, Slurm, and session handoffs."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


EXIT_READY = 0
EXIT_ACTIVE = 10
EXIT_FAILURES = 20
EXIT_INVARIANT = 30
EXIT_TRANSPORT = 40
EXIT_INVALID = 50

TERMINAL_PANDA = {"done", "finished", "failed", "aborted", "cancelled", "broken"}
CLEAN_PANDA = {"done", "finished"}
FAILED_JOB_STATES = {"failed", "cancelled", "closed", "aborted", "broken"}
ACTIVE_SLURM = {"PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "SUSPENDED"}
FAILED_SLURM = {
    "BOOT_FAIL",
    "CANCELLED",
    "DEADLINE",
    "FAILED",
    "NODE_FAIL",
    "OUT_OF_MEMORY",
    "PREEMPTED",
    "REVOKED",
    "TIMEOUT",
}
TERMINAL_SLURM = FAILED_SLURM | {"COMPLETED"}
ERROR_CODE_FIELDS = (
    "piloterrorcode",
    "exeerrorcode",
    "superrorcode",
    "ddmerrorcode",
    "brokerageerrorcode",
    "jobdispatchererrorcode",
    "taskbuffererrorcode",
)
ERROR_DIAG_FIELDS = (
    "piloterrordiag",
    "exeerrordiag",
    "superrordiag",
    "ddmerrordiag",
    "brokerageerrordiag",
    "jobdispatchererrordiag",
    "taskbuffererrordiag",
)


class MonitorError(RuntimeError):
    pass


class TransportError(MonitorError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def spec_hash(spec: dict[str, Any]) -> str:
    payload = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def load_spec(path: Path) -> dict[str, Any]:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MonitorError(f"cannot read monitor spec {path}: {exc}") from exc
    if spec.get("schema_version") != 1:
        raise MonitorError("schema_version must be 1")
    if spec.get("backend") not in {"panda", "slurm", "dependencies"}:
        raise MonitorError("backend must be panda, slurm, or dependencies")
    if not isinstance(spec.get("name"), str) or not spec["name"].strip():
        raise MonitorError("name must be a non-empty string")
    poll = spec.setdefault("poll", {})
    poll.setdefault("interval_seconds", 300)
    poll.setdefault("lease_seconds", 86400)
    poll.setdefault("max_consecutive_transport_errors", 3)
    poll.setdefault("snapshot_ttl_seconds", max(120, 2 * poll["interval_seconds"]))
    if poll["interval_seconds"] < 30 or poll["lease_seconds"] < 30:
        raise MonitorError("poll interval and lease must be at least 30 seconds")
    output_dir = Path(spec.get("output_dir", "monitor"))
    if output_dir.is_absolute() or ".." in output_dir.parts:
        raise MonitorError("output_dir must stay within the spec directory")
    if spec["backend"] == "panda":
        validate_panda_spec(spec)
    elif spec["backend"] == "slurm":
        validate_slurm_spec(spec)
    else:
        validate_dependency_spec(spec)
    return spec


def validate_panda_spec(spec: dict[str, Any]) -> None:
    target = spec.get("target", {})
    expected = spec.get("expected", {})
    if not str(target.get("task_id", "")).isdigit():
        raise MonitorError("PanDA target.task_id must be numeric")
    for field in ("files", "events", "max_attempt", "payload_hard_ceiling"):
        if field not in expected or int(expected[field]) < 0:
            raise MonitorError(f"PanDA expected.{field} is required and non-negative")
    if not expected.get("owner"):
        raise MonitorError("PanDA expected.owner is required")
    if spec.get("failure_policy", "record") not in {"record", "stop"}:
        raise MonitorError("failure_policy must be record or stop")
    if spec.get("goal", "terminal") not in {"terminal", "topology_stable"}:
        raise MonitorError("PanDA goal must be terminal or topology_stable")


def validate_slurm_spec(spec: dict[str, Any]) -> None:
    target = spec.get("target", {})
    if not re.fullmatch(r"[0-9]+", str(target.get("job_id", ""))):
        raise MonitorError("Slurm target.job_id must be numeric")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", str(target.get("ssh_alias", ""))):
        raise MonitorError("Slurm target.ssh_alias is invalid")
    indices = spec.get("expected", {}).get("array_indices")
    if not isinstance(indices, list) or not all(isinstance(value, int) for value in indices):
        raise MonitorError("Slurm expected.array_indices must be an integer list")


def validate_dependency_spec(spec: dict[str, Any]) -> None:
    items = spec.get("dependencies", [])
    if not items or not isinstance(items, list):
        raise MonitorError("dependencies backend requires a non-empty dependencies list")
    for item in items:
        if not item.get("name") or not item.get("marker"):
            raise MonitorError("each dependency requires name and marker")
        requirement = item.get("require", {})
        if not ({"session_status", "release"} & set(requirement)):
            raise MonitorError("dependency requirement needs session_status or release")


def fetch_json(url: str, retries: int = 3, timeout: int = 60) -> Any:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": "job-monitor/1"}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(2**attempt)
    raise TransportError(f"request failed after {retries} attempts: {last_error}")


def panda_job_kind(job: dict[str, Any]) -> str:
    transformation = str(job.get("transformation") or "").lower()
    category = str(job.get("category") or "").lower()
    if "buildgen" in transformation or category == "build":
        return "build"
    if "runmerge" in transformation or "mergegen" in transformation or category == "merge":
        return "merge"
    if "rungen" in transformation or category == "run":
        return "payload"
    return "other"


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def panda_selection_total(payload: dict[str, Any]) -> int | None:
    for summary in payload.get("selectionsummary") or []:
        if summary.get("field") == "jobstatus":
            return sum(integer(row.get("kvalue")) for row in summary.get("list") or [])
    return None


def panda_error(job: dict[str, Any]) -> bool:
    if str(job.get("jobstatus") or "").lower() in FAILED_JOB_STATES:
        return True
    return any(integer(job.get(field)) != 0 for field in ERROR_CODE_FIELDS)


def panda_error_row(job: dict[str, Any]) -> dict[str, Any]:
    row = {
        "pandaid": job.get("pandaid"),
        "status": job.get("jobstatus"),
        "kind": panda_job_kind(job),
        "site": job.get("computingsite"),
        "attempt": job.get("attemptnr"),
    }
    for field in ERROR_CODE_FIELDS + ERROR_DIAG_FIELDS:
        if job.get(field) not in (None, "", 0, "0"):
            row[field] = job.get(field)
    return row


def normalize_panda(
    task_payload: dict[str, Any], jobs_payload: dict[str, Any], spec: dict[str, Any]
) -> dict[str, Any]:
    task = task_payload.get("task", task_payload)
    if isinstance(task, list):
        task = task[0] if task else {}
    jobs = jobs_payload.get("jobs") or []
    expected = spec["expected"]
    dsinfo = task.get("dsinfo") or {}
    kinds: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for job in jobs:
        kinds[panda_job_kind(job)].append(job)
    payload_jobs = kinds["payload"]

    status_counts = collections.Counter(str(job.get("jobstatus")) for job in jobs)
    kind_status: dict[str, dict[str, int]] = {}
    for kind, rows in kinds.items():
        kind_status[kind] = dict(
            collections.Counter(str(row.get("jobstatus")) for row in rows)
        )
    sites = collections.Counter(str(job.get("computingsite")) for job in payload_jobs)
    attempts = [integer(job.get("attemptnr"), 1) for job in jobs]
    failures = [panda_error_row(job) for job in jobs if panda_error(job)]
    listed_total = panda_selection_total(jobs_payload)
    truncated = listed_total is not None and listed_total > len(jobs)

    task_id = integer(task.get("jeditaskid"))
    owner = task.get("owner") or task.get("username")
    status = str(task.get("status") or "unknown").lower()
    observed = {
        "task_id": task_id,
        "task_name": task.get("taskname"),
        "owner": owner,
        "status": status,
        "superstatus": task.get("superstatus"),
        "task_attempt": integer(task.get("attemptnr")),
        "files": integer(dsinfo.get("nfiles")),
        "files_finished": integer(dsinfo.get("nfilesfinished")),
        "files_failed": integer(dsinfo.get("nfilesfailed")),
        "files_missing": integer(dsinfo.get("nfilesmissing")),
        "events": integer(dsinfo.get("neventsTot")),
        "events_used": integer(dsinfo.get("neventsUsedTot")),
        "events_output": integer(dsinfo.get("neventsOutput")),
        "jobs_listed": len(jobs),
        "jobs_reported": listed_total,
        "jobs_truncated": truncated,
        "jobs_by_status": dict(status_counts),
        "jobs_by_kind_status": kind_status,
        "payload_count": len(payload_jobs),
        "payload_sites": dict(sites),
        "payload_input_files": sum(integer(job.get("ninputdatafiles")) for job in payload_jobs),
        "payload_input_bytes": sum(integer(job.get("inputfilebytes")) for job in payload_jobs),
        "payload_events": sum(integer(job.get("nevents")) for job in payload_jobs),
        "max_job_attempt": max(attempts, default=0),
        "failures": failures,
        "errs_by_count": jobs_payload.get("errsByCount") or [],
    }

    invariants: list[str] = []
    attentions: list[str] = []
    if task_id != integer(spec["target"]["task_id"]):
        invariants.append(f"task id drift: {task_id}")
    if owner != expected["owner"]:
        invariants.append(f"owner drift: {owner!r}")
    if observed["files"] != integer(expected["files"]):
        invariants.append(f"file-count drift: {observed['files']}")
    if observed["events"] != integer(expected["events"]):
        invariants.append(f"event-count drift: {observed['events']}")
    if observed["max_job_attempt"] > integer(expected["max_attempt"]):
        invariants.append(f"job attempt exceeded: {observed['max_job_attempt']}")
    if observed["task_attempt"] > integer(expected.get("max_task_attempt", 1)):
        invariants.append(f"task attempt exceeded: {observed['task_attempt']}")
    if observed["payload_count"] > integer(expected["payload_hard_ceiling"]):
        invariants.append(f"payload hard ceiling exceeded: {observed['payload_count']}")
    if truncated:
        invariants.append(
            f"jobs response truncated: listed {len(jobs)} of reported {listed_total}"
        )
    progression = expected.get("payload_progression_limit")
    if progression is not None and observed["payload_count"] > integer(progression):
        attentions.append(
            f"payload progression limit exceeded: {observed['payload_count']} > {progression}"
        )
    expected_bytes = expected.get("bytes")
    if expected_bytes and observed["payload_input_bytes"]:
        difference = abs(observed["payload_input_bytes"] - integer(expected_bytes))
        observed["payload_bytes_relative_difference"] = difference / integer(expected_bytes)
        if (
            observed["payload_input_files"] >= integer(expected["files"])
            and difference != 0
        ):
            invariants.append(
                "payload byte-count drift: "
                f"{observed['payload_input_bytes']} != {integer(expected_bytes)}"
            )

    terminal = status in TERMINAL_PANDA
    if invariants:
        outcome = "invariant_violation"
    elif terminal and (status not in CLEAN_PANDA or failures):
        outcome = "terminal_with_failures"
    elif terminal:
        outcome = "terminal_clean"
    elif failures and spec.get("failure_policy", "record") == "stop":
        outcome = "failure_attention"
    else:
        outcome = "active"
    return {
        "schema_version": 1,
        "backend": "panda",
        "timestamp": utc_now(),
        "outcome": outcome,
        "terminal": terminal,
        "invariants": invariants,
        "attentions": attentions,
        "observed": observed,
    }


def probe_panda(spec: dict[str, Any]) -> dict[str, Any]:
    task_id = str(spec["target"]["task_id"])
    hard_ceiling = integer(spec["expected"]["payload_hard_ceiling"])
    display_limit = max(1000, min(10000, hard_ceiling + 1000))
    task_url = f"https://bigpanda.cern.ch/task/{task_id}/?json=1"
    jobs_url = (
        f"https://bigpanda.cern.ch/jobs/?jeditaskid={task_id}"
        f"&display_limit={display_limit}&json=1"
    )
    return normalize_panda(fetch_json(task_url), fetch_json(jobs_url), spec)


def clean_slurm_state(value: str) -> str:
    parts = value.strip().split()
    return parts[0].rstrip("+") if parts else "UNKNOWN"


def parse_slurm_output(output: str, spec: dict[str, Any]) -> dict[str, Any]:
    section = None
    sacct_rows: list[list[str]] = []
    squeue_rows: list[list[str]] = []
    for line in output.splitlines():
        if line == "__SACCT__":
            section = "sacct"
            continue
        if line == "__SQUEUE__":
            section = "squeue"
            continue
        if not line.strip():
            continue
        if section == "sacct":
            sacct_rows.append(line.split("|"))
        elif section == "squeue":
            squeue_rows.append(line.split("|"))

    job_id = str(spec["target"]["job_id"])
    expected = set(spec["expected"]["array_indices"])
    tasks: dict[int, dict[str, Any]] = {}
    pattern = re.compile(rf"^{re.escape(job_id)}_(\d+)$")
    for row in sacct_rows:
        if len(row) < 9:
            continue
        match = pattern.match(row[1])
        if not match:
            continue
        index = int(match.group(1))
        tasks[index] = {
            "state": clean_slurm_state(row[2]),
            "exit_code": row[3],
            "elapsed_seconds": integer(row[4]),
            "max_rss": row[5],
            "cpus": integer(row[6]),
            "requested_memory": row[7],
            "node": row[8],
        }
    for row in squeue_rows:
        if len(row) < 3:
            continue
        match = pattern.match(row[0])
        if not match:
            continue
        index = int(match.group(1))
        tasks.setdefault(index, {})
        tasks[index]["state"] = clean_slurm_state(row[1])
        tasks[index]["reason"] = row[2]

    missing = sorted(expected - set(tasks))
    unexpected = sorted(set(tasks) - expected)
    states = collections.Counter(row.get("state", "UNKNOWN") for row in tasks.values())
    failures = {
        str(index): row
        for index, row in tasks.items()
        if row.get("state") in FAILED_SLURM or row.get("exit_code", "0:0") not in {"", "0:0"}
    }
    observed_terminal = bool(tasks) and all(
        row.get("state") in TERMINAL_SLURM for row in tasks.values()
    )
    terminal = observed_terminal and not missing
    invariants: list[str] = []
    if unexpected:
        invariants.append(f"unexpected array indices: {unexpected}")
    if observed_terminal and missing:
        invariants.append(f"missing terminal array indices: {missing}")
    if invariants:
        outcome = "invariant_violation"
    elif terminal and failures:
        outcome = "terminal_with_failures"
    elif terminal:
        outcome = "terminal_clean"
    else:
        outcome = "active"
    return {
        "schema_version": 1,
        "backend": "slurm",
        "timestamp": utc_now(),
        "outcome": outcome,
        "terminal": terminal,
        "invariants": invariants,
        "attentions": [],
        "observed": {
            "job_id": job_id,
            "tasks": {str(index): row for index, row in sorted(tasks.items())},
            "states": dict(states),
            "missing_indices": missing,
            "unexpected_indices": unexpected,
            "failures": failures,
        },
    }


def probe_slurm(spec: dict[str, Any]) -> dict[str, Any]:
    job_id = str(spec["target"]["job_id"])
    alias = spec["target"]["ssh_alias"]
    remote = (
        "printf '__SACCT__\\n'; "
        f"sacct -j {job_id} -n -P --format=JobIDRaw,JobID,State,ExitCode,ElapsedRaw,MaxRSS,AllocCPUS,ReqMem,NodeList; "
        "printf '__SQUEUE__\\n'; "
        f"squeue -h -j {job_id} -o '%i|%T|%R'"
    )
    completed = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", alias, remote],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise TransportError(
            f"Slurm SSH probe failed ({completed.returncode}): {completed.stderr.strip()}"
        )
    return parse_slurm_output(completed.stdout, spec)


def project_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise MonitorError("cannot locate project root")


def safe_project_path(root: Path, value: str) -> Path:
    candidate = (root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise MonitorError(f"dependency marker is outside project: {candidate}") from exc
    return candidate


def normalize_dependencies(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    rows = []
    all_ready = True
    invariants: list[str] = []
    for item in spec["dependencies"]:
        marker_path = safe_project_path(root, item["marker"])
        row: dict[str, Any] = {"name": item["name"], "marker": str(marker_path.relative_to(root))}
        try:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            row.update(status="pending", reason="marker missing")
            all_ready = False
            rows.append(row)
            continue
        except (OSError, json.JSONDecodeError) as exc:
            row.update(status="invalid", reason=str(exc))
            invariants.append(f"invalid marker for {item['name']}: {exc}")
            all_ready = False
            rows.append(row)
            continue
        if marker.get("schema_version") != 1:
            row.update(status="invalid", reason="unsupported schema")
            invariants.append(f"unsupported marker schema for {item['name']}")
            all_ready = False
            rows.append(row)
            continue
        requirement = item["require"]
        ready = True
        reasons = []
        required_status = requirement.get("session_status")
        if required_status and marker.get("session_status") != required_status:
            ready = False
            reasons.append(
                f"session_status={marker.get('session_status')!r}, expected {required_status!r}"
            )
        release = requirement.get("release")
        if release:
            actual = (marker.get("releases") or {}).get(release, {}).get("status")
            expected_release = requirement.get("release_status", "released")
            if actual != expected_release:
                ready = False
                reasons.append(f"release {release}={actual!r}, expected {expected_release!r}")
        row.update(
            status="ready" if ready else "pending",
            reason="; ".join(reasons) if reasons else None,
            marker_updated=marker.get("updated"),
            marker_sha256=hashlib.sha256(marker_path.read_bytes()).hexdigest(),
        )
        all_ready &= ready
        rows.append(row)
    outcome = "invariant_violation" if invariants else ("ready" if all_ready else "active")
    return {
        "schema_version": 1,
        "backend": "dependencies",
        "timestamp": utc_now(),
        "outcome": outcome,
        "terminal": all_ready and not invariants,
        "invariants": invariants,
        "attentions": [],
        "observed": {"dependencies": rows},
    }


def probe_dependencies(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    return normalize_dependencies(spec, root)


def probe_backend(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    try:
        if spec["backend"] == "panda":
            return probe_panda(spec)
        if spec["backend"] == "slurm":
            return probe_slurm(spec)
        return probe_dependencies(spec, root)
    except TransportError as exc:
        return {
            "schema_version": 1,
            "backend": spec["backend"],
            "timestamp": utc_now(),
            "outcome": "transport_error",
            "terminal": False,
            "invariants": [],
            "attentions": [],
            "error": str(exc),
            "observed": {},
        }


def state_paths(spec_path: Path, spec: dict[str, Any]) -> dict[str, Path]:
    base = (spec_path.parent / spec.get("output_dir", "monitor")).resolve()
    try:
        base.relative_to(spec_path.parent.resolve())
    except ValueError as exc:
        raise MonitorError("output_dir must stay within the spec directory") from exc
    return {
        "lock": base / "monitor.lock",
        "snapshots": base / "snapshots.jsonl",
        "latest": base / "latest.json",
        "result": base / "result.json",
        "unit": base / "unit.json",
    }


def record_snapshot(paths: dict[str, Path], spec: dict[str, Any], snapshot: dict[str, Any]) -> None:
    expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
        seconds=integer(spec["poll"]["snapshot_ttl_seconds"])
    )
    snapshot = {
        **snapshot,
        "expires_at": expires.replace(microsecond=0).isoformat(),
        "spec_sha256": spec_hash(spec),
    }
    append_jsonl(paths["snapshots"], snapshot)
    atomic_json(paths["latest"], snapshot)


def result_exit(outcome: str) -> int:
    if outcome in {"terminal_clean", "ready", "topology_stable"}:
        return EXIT_READY
    if outcome == "terminal_with_failures":
        return EXIT_FAILURES
    if outcome in {"invariant_violation", "failure_attention"}:
        return EXIT_INVARIANT
    if outcome == "transport_error":
        return EXIT_TRANSPORT
    return EXIT_ACTIVE


def finish(paths: dict[str, Path], spec: dict[str, Any], snapshot: dict[str, Any], reason: str) -> int:
    result = {
        **snapshot,
        "result_timestamp": utc_now(),
        "reason": reason,
        "spec_sha256": spec_hash(spec),
    }
    atomic_json(paths["result"], result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result_exit(result["outcome"])


def locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise MonitorError(f"monitor already holds lock {path}") from exc
    return handle


def command_probe(spec_path: Path) -> int:
    spec = load_spec(spec_path)
    root = project_root(spec_path.parent)
    paths = state_paths(spec_path, spec)
    handle = locked(paths["lock"])
    try:
        snapshot = probe_backend(spec, root)
        record_snapshot(paths, spec, snapshot)
        if snapshot["outcome"] != "active":
            return finish(paths, spec, snapshot, "single probe reached a handback state")
        print(json.dumps(snapshot, indent=2, sort_keys=True))
        return EXIT_ACTIVE
    finally:
        handle.close()


def command_watch(spec_path: Path) -> int:
    spec = load_spec(spec_path)
    root = project_root(spec_path.parent)
    paths = state_paths(spec_path, spec)
    handle = locked(paths["lock"])
    poll = spec["poll"]
    deadline = time.monotonic() + integer(poll["lease_seconds"])
    consecutive_transport = 0
    previous_payload: int | None = None
    stable_polls = 0
    try:
        while True:
            snapshot = probe_backend(spec, root)
            record_snapshot(paths, spec, snapshot)
            outcome = snapshot["outcome"]
            if outcome == "transport_error":
                consecutive_transport += 1
                if consecutive_transport >= integer(poll["max_consecutive_transport_errors"]):
                    return finish(paths, spec, snapshot, "transport error limit reached")
            else:
                consecutive_transport = 0
                if outcome != "active":
                    return finish(paths, spec, snapshot, "backend reached a handback state")
                if spec["backend"] == "panda" and spec.get("goal", "terminal") == "topology_stable":
                    payload = snapshot["observed"]["payload_count"]
                    stable_polls = stable_polls + 1 if payload == previous_payload else 0
                    previous_payload = payload
                    status = snapshot["observed"]["status"]
                    scouting = set(spec.get("scouting_statuses", ["ready", "pending", "scouting", "submitting"]))
                    if status not in scouting and stable_polls >= integer(spec.get("stable_polls", 2)):
                        snapshot["outcome"] = "topology_stable"
                        return finish(paths, spec, snapshot, "payload topology stabilized")
            if time.monotonic() >= deadline:
                snapshot["outcome"] = "lease_expired"
                return finish(paths, spec, snapshot, "monitor lease expired")
            time.sleep(min(integer(poll["interval_seconds"]), max(1, deadline - time.monotonic())))
    finally:
        handle.close()


def unit_name(spec: dict[str, Any]) -> str:
    name = re.sub(r"[^A-Za-z0-9_.-]+", "-", spec["name"]).strip("-")
    return f"agent-monitor-{name[:42]}-{spec_hash(spec)[:8]}"


def command_start(spec_path: Path) -> int:
    spec = load_spec(spec_path)
    root = project_root(spec_path.parent)
    paths = state_paths(spec_path, spec)
    unit = unit_name(spec)
    command = [
        "systemd-run",
        "--user",
        "--collect",
        f"--unit={unit}",
        f"--property=WorkingDirectory={root}",
        sys.executable,
        str(Path(__file__).resolve()),
        "watch",
        "--spec",
        str(spec_path.resolve()),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MonitorError(f"systemd-run failed: {completed.stderr.strip()}")
    metadata = {
        "schema_version": 1,
        "unit": unit,
        "started": utc_now(),
        "spec_sha256": spec_hash(spec),
        "command": command,
    }
    atomic_json(paths["unit"], metadata)
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return EXIT_READY


def command_status(spec_path: Path) -> int:
    spec = load_spec(spec_path)
    paths = state_paths(spec_path, spec)
    payload: dict[str, Any] = {"spec_sha256": spec_hash(spec), "name": spec["name"]}
    for key in ("result", "latest", "unit"):
        try:
            payload[key] = json.loads(paths[key].read_text(encoding="utf-8"))
        except FileNotFoundError:
            payload[key] = None
    latest = payload.get("latest")
    if not latest and not payload.get("result"):
        payload["monitor_status"] = "stale"
    elif latest and not payload.get("result"):
        try:
            expires = dt.datetime.fromisoformat(latest["expires_at"])
            if expires <= dt.datetime.now(dt.timezone.utc):
                payload["monitor_status"] = "stale"
        except (KeyError, TypeError, ValueError):
            payload["monitor_status"] = "stale"
    unit = (payload.get("unit") or {}).get("unit")
    if unit:
        completed = subprocess.run(
            ["systemctl", "--user", "show", unit, "--property=ActiveState,SubState,Result"],
            capture_output=True,
            text=True,
            check=False,
        )
        payload["systemd"] = completed.stdout.strip() if completed.returncode == 0 else "inactive"
    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload.get("result"):
        return result_exit(payload["result"]["outcome"])
    return EXIT_ACTIVE


def command_validate(spec_path: Path) -> int:
    spec = load_spec(spec_path)
    print(json.dumps({"valid": True, "spec_sha256": spec_hash(spec)}, indent=2))
    return EXIT_READY


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate-spec", "probe", "watch", "start", "status"))
    parser.add_argument("--spec", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-spec":
            return command_validate(args.spec)
        if args.command == "probe":
            return command_probe(args.spec)
        if args.command == "watch":
            return command_watch(args.spec)
        if args.command == "start":
            return command_start(args.spec)
        return command_status(args.spec)
    except MonitorError as exc:
        print(f"monitor error: {exc}", file=sys.stderr)
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
