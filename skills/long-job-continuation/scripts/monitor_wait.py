#!/usr/bin/env python3
"""Wait for durable job monitors without invoking a model."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import io
import json
import math
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

import job_monitor as monitor


# Sessions directory relative to the project root; a wait contract lives directly in
# one session folder below it. Override with AGENT_SESSIONS_DIR.
SESSIONS_DIR = Path(os.environ.get("AGENT_SESSIONS_DIR", "sessions"))


SUCCESS_OUTCOMES = {"terminal_clean", "ready", "topology_stable"}
OBSERVATION_TRANSITIONS = {
    "registered": {"waiting", "completed"},
    "waiting": {"completed"},
    "completed": set(),
}
DELIVERY_TRANSITIONS = {
    "pending": {"delivered_to_tool", "orphaned"},
    "delivered_to_tool": {"acknowledged"},
    "orphaned": {"notifying", "acknowledged"},
    "notifying": {"notified", "notification_failed", "notification_unknown"},
    "notified": {"acknowledged"},
    "notification_failed": {"acknowledged"},
    "notification_unknown": {"acknowledged"},
    "acknowledged": set(),
}


class WaitError(RuntimeError):
    pass


class WaitInterrupted(WaitError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        raise WaitError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WaitError(f"expected JSON object in {path}")
    return value


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise WaitError(f"cannot hash {path}: {exc}") from exc


def confined(root: Path, value: str | Path, label: str) -> Path:
    candidate = Path(value)
    candidate = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise WaitError(f"{label} is outside project: {candidate}") from exc
    return candidate


def load_contract(path: Path, session_id: str | None = None) -> dict[str, Any]:
    path = path.resolve()
    root = monitor.project_root(path.parent)
    confined(root, path, "contract")
    try:
        session_relative = path.relative_to(root / SESSIONS_DIR)
    except ValueError as exc:
        raise WaitError("wait contract must live in the project's sessions directory") from exc
    if len(session_relative.parts) != 2:
        raise WaitError("wait contract must live directly in one owning session")
    contract = read_json(path)
    if contract is None:
        raise WaitError(f"contract does not exist: {path}")
    if contract.get("schema_version") != 1:
        raise WaitError("wait contract schema_version must be 1")
    if contract.get("policy", "fail_fast_all") != "fail_fast_all":
        raise WaitError("wait contract policy must be fail_fast_all")
    owner = contract.get("owner_session_id", "caller")
    if session_id and owner not in {"caller", session_id}:
        raise WaitError(f"contract belongs to another session: {owner!r}")
    raw_specs = contract.get("monitor_specs")
    if not isinstance(raw_specs, list) or not raw_specs:
        raise WaitError("wait contract requires a non-empty monitor_specs list")
    if not all(isinstance(value, str) and value for value in raw_specs):
        raise WaitError("monitor_specs entries must be non-empty strings")
    specs = []
    for value in raw_specs:
        spec_path = confined(root, value, "monitor spec")
        spec = monitor.load_spec(spec_path)
        specs.append(
            {
                "path": str(spec_path.relative_to(root)),
                "absolute_path": str(spec_path),
                "sha256": monitor.spec_hash(spec),
            }
        )
    specs.sort(key=lambda row: row["path"])
    poll = contract.get("wait", {})
    if not isinstance(poll, dict):
        raise WaitError("wait must be an object")
    check_interval = float(poll.get("check_interval_seconds", 5))
    startup_grace = float(poll.get("startup_grace_seconds", 120))
    timeout = float(poll.get("timeout_seconds", 7 * 86400))
    if (
        not all(math.isfinite(value) for value in (check_interval, startup_grace, timeout))
        or check_interval <= 0
        or startup_grace < 0
        or timeout <= 0
    ):
        raise WaitError("wait timing values must be positive")
    post_handback = contract.get("post_handback")
    if not isinstance(post_handback, dict) or not all(
        isinstance(post_handback.get(key), str) and post_handback[key].strip()
        for key in ("authorization", "completion_contract")
    ):
        raise WaitError("post_handback requires authorization and completion_contract")
    notification = contract.get("notification", {"authorized": False})
    if not isinstance(notification, dict):
        raise WaitError("notification must be an object")
    if notification.get("authorized"):
        command = notification.get("command")
        if not isinstance(command, list) or not command or not all(
            isinstance(value, str) and value for value in command
        ):
            raise WaitError("authorized notification requires an exact command array")
        destination = notification.get("destination")
        if not isinstance(destination, str) or not destination.strip():
            raise WaitError("authorized notification requires destination evidence")
    return {
        "root": root,
        "path": path,
        "relative_path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "raw": contract,
        "specs": specs,
        "check_interval_seconds": check_interval,
        "startup_grace_seconds": startup_grace,
        "timeout_seconds": timeout,
        "notification": notification,
    }


HARNESSES = ("opencode", "claude", "codex")


def event_id_for(session_id: str, message_id: str | None, contract_sha256: str) -> str:
    material = f"{session_id}\0{message_id or ''}\0{contract_sha256}".encode()
    return hashlib.sha256(material).hexdigest()[:32]


def validate_event_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{8,128}", value):
        raise WaitError("event ID is unsafe")
    return value


def wait_paths(contract: dict[str, Any], event_id: str) -> dict[str, Path]:
    event_id = validate_event_id(event_id)
    directory = contract["path"].parent / "monitor" / "waits" / event_id
    confined(contract["root"], directory, "wait directory")
    return {
        "directory": directory,
        "lock": directory / "wait.lock",
        "registration": directory / "registration.json",
        "state": directory / "state.json",
        "result": directory / "result.json",
        "notification": directory / "notification.json",
        "unit": directory / "unit.json",
    }


def lock_wait(paths: dict[str, Path]):
    paths["directory"].mkdir(parents=True, exist_ok=True)
    handle = paths["lock"].open("a+")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def append_history(state: dict[str, Any], event: str) -> None:
    state.setdefault("history", []).append({"event": event, "timestamp": utc_now()})
    state["updated"] = utc_now()


def process_identity(pid: int) -> str | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
        return fields[19]
    except (FileNotFoundError, OSError, IndexError):
        return None


def register_wait(
    contract: dict[str, Any],
    event_id: str,
    session_id: str,
    message_id: str | None,
    owner_pid: int,
    harness: str = "opencode",
) -> dict[str, Any]:
    paths = wait_paths(contract, event_id)
    identity = {
        "schema_version": 1,
        "event_id": event_id,
        "harness": harness,
        "session_id": session_id,
        "message_id": message_id,
        "owner_pid": owner_pid,
        "owner_start_time": process_identity(owner_pid),
        "contract": contract["relative_path"],
        "contract_sha256": contract["sha256"],
        "specs": [
            {"path": row["path"], "sha256": row["sha256"]}
            for row in contract["specs"]
        ],
    }
    handle = lock_wait(paths)
    try:
        existing = read_json(paths["registration"])
        if existing:
            comparable = {key: existing.get(key) for key in identity}
            # Registrations written before the harness field were OpenCode-owned.
            comparable["harness"] = existing.get("harness", "opencode")
            if comparable != identity:
                raise WaitError("wait registration drift")
            if read_json(paths["state"]) is None:
                state = {
                    "schema_version": 1,
                    "event_id": event_id,
                    "observation": "registered",
                    "delivery": "pending",
                    "updated": utc_now(),
                    "history": [{"event": "registration_repaired", "timestamp": utc_now()}],
                }
                monitor.atomic_json(paths["state"], state)
            return existing
        registration = {**identity, "created": utc_now()}
        monitor.atomic_json(paths["registration"], registration)
        state = {
            "schema_version": 1,
            "event_id": event_id,
            "observation": "registered",
            "delivery": "pending",
            "updated": utc_now(),
            "history": [{"event": "registered", "timestamp": utc_now()}],
        }
        monitor.atomic_json(paths["state"], state)
        return registration
    finally:
        handle.close()


def transition(
    paths: dict[str, Path],
    *,
    observation: str | None = None,
    delivery: str | None = None,
) -> dict[str, Any]:
    handle = lock_wait(paths)
    try:
        state = read_json(paths["state"])
        if state is None:
            raise WaitError("wait is not registered")
        if observation:
            current = state["observation"]
            if observation != current and observation not in OBSERVATION_TRANSITIONS.get(current, set()):
                raise WaitError(f"invalid observation transition {current} -> {observation}")
            if observation != current:
                state["observation"] = observation
                append_history(state, observation)
        if delivery:
            current = state["delivery"]
            if delivery != current and delivery not in DELIVERY_TRANSITIONS.get(current, set()):
                raise WaitError(f"invalid delivery transition {current} -> {delivery}")
            if delivery != current:
                state["delivery"] = delivery
                append_history(state, delivery)
        monitor.atomic_json(paths["state"], state)
        return state
    finally:
        handle.close()


def validate_registration(contract: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    registration = read_json(paths["registration"])
    if registration is None:
        raise WaitError("wait registration is missing")
    expected_specs = [
        {"path": row["path"], "sha256": row["sha256"]}
        for row in contract["specs"]
    ]
    if registration.get("event_id") != paths["directory"].name:
        raise WaitError("wait event identity drift")
    if registration.get("contract_sha256") != contract["sha256"]:
        raise WaitError("wait contract drift")
    if registration.get("specs") != expected_specs:
        raise WaitError("wait monitor identity drift")
    return registration


def systemd_active(unit: str) -> bool:
    completed = subprocess.run(
        ["systemctl", "--user", "show", unit, "--property=ActiveState", "--value"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and completed.stdout.strip() == "active"


def monitor_runtime(
    spec_row: dict[str, Any],
    *,
    active: Callable[[str], bool] = systemd_active,
) -> dict[str, Any]:
    spec_path = Path(spec_row["absolute_path"])
    spec = monitor.load_spec(spec_path)
    paths = monitor.state_paths(spec_path, spec)
    result = read_json(paths["result"])
    latest = read_json(paths["latest"])
    unit = read_json(paths["unit"])
    unit_name = (unit or {}).get("unit")
    unit_valid = bool(
        unit_name
        and unit.get("spec_sha256") == spec_row["sha256"]
        and unit_name == monitor.unit_name(spec)
    )
    return {
        "spec": spec,
        "paths": paths,
        "result": result,
        "latest": latest,
        "unit": unit,
        "unit_active": unit_valid and active(unit_name),
    }


def ensure_monitors(
    contract: dict[str, Any],
    start_missing: bool,
    *,
    active: Callable[[str], bool] = systemd_active,
    starter: Callable[[Path], int] | None = None,
) -> list[dict[str, Any]]:
    if starter is None:
        def starter(path: Path) -> int:
            with contextlib.redirect_stdout(io.StringIO()):
                return monitor.command_start(path)

    statuses = []
    for row in contract["specs"]:
        runtime = monitor_runtime(row, active=active)
        status = "terminal" if runtime["result"] else "adopted" if runtime["unit_active"] else "missing"
        if status == "missing" and start_missing:
            code = starter(Path(row["absolute_path"]))
            if code != monitor.EXIT_READY:
                raise WaitError(f"could not start monitor {row['path']}")
            status = "started"
        statuses.append({"path": row["path"], "status": status})
    return statuses


def valid_expiry(snapshot: dict[str, Any], now: dt.datetime) -> bool:
    try:
        expiry = dt.datetime.fromisoformat(snapshot["expires_at"])
        return expiry > now
    except (KeyError, TypeError, ValueError):
        return False


def evaluate_spec(
    row: dict[str, Any],
    elapsed: float,
    startup_grace: float,
    *,
    now: dt.datetime | None = None,
    active: Callable[[str], bool] = systemd_active,
) -> dict[str, Any]:
    now = now or dt.datetime.now(dt.timezone.utc)
    runtime = monitor_runtime(row, active=active)
    result = runtime["result"]
    if result:
        if result.get("spec_sha256") != row["sha256"]:
            return {"path": row["path"], "status": "failure", "outcome": "spec_drift"}
        outcome = result.get("outcome", "invalid_result")
        return {
            "path": row["path"],
            "status": "success" if outcome in SUCCESS_OUTCOMES else "failure",
            "outcome": outcome,
            "evidence": result,
        }
    latest = runtime["latest"]
    if latest and latest.get("spec_sha256") != row["sha256"]:
        return {"path": row["path"], "status": "failure", "outcome": "spec_drift"}
    if latest and valid_expiry(latest, now):
        outcome = latest.get("outcome", "invalid_snapshot")
        if outcome == "active":
            return {"path": row["path"], "status": "pending", "outcome": outcome}
        return {
            "path": row["path"],
            "status": "success" if outcome in SUCCESS_OUTCOMES else "failure",
            "outcome": outcome,
            "evidence": latest,
        }
    if runtime["unit_active"] and elapsed < startup_grace:
        return {"path": row["path"], "status": "pending", "outcome": "starting"}
    outcome = "stale" if latest else "monitor_absent"
    return {"path": row["path"], "status": "failure", "outcome": outcome}


def evaluate_group(
    contract: dict[str, Any],
    elapsed: float,
    *,
    now: dt.datetime | None = None,
    active: Callable[[str], bool] = systemd_active,
) -> dict[str, Any]:
    rows = [
        evaluate_spec(
            row,
            elapsed,
            contract["startup_grace_seconds"],
            now=now,
            active=active,
        )
        for row in contract["specs"]
    ]
    failure = next((row for row in rows if row["status"] == "failure"), None)
    if failure:
        return {"status": "failure", "outcome": failure["outcome"], "monitors": rows}
    if all(row["status"] == "success" for row in rows):
        return {"status": "success", "outcome": "ready", "monitors": rows}
    return {"status": "pending", "outcome": "active", "monitors": rows}


def complete_wait(paths: dict[str, Path], contract: dict[str, Any], group: dict[str, Any]) -> dict[str, Any]:
    handle = lock_wait(paths)
    try:
        registration = read_json(paths["registration"])
        state = read_json(paths["state"])
        if registration is None or state is None:
            raise WaitError("wait registration or state is missing")
        if registration.get("contract_sha256") != contract["sha256"]:
            raise WaitError("wait contract drift")
        if state["observation"] not in {"registered", "waiting", "completed"}:
            raise WaitError("wait cannot be completed from current state")
        existing = read_json(paths["result"])
        if existing and (
            existing.get("event_id") not in {None, paths["directory"].name}
            or existing.get("contract_sha256") not in {None, contract["sha256"]}
        ):
            raise WaitError("durable wait result drift")
        result = existing or {
            "schema_version": 1,
            "event_id": paths["directory"].name,
            "timestamp": utc_now(),
            "contract": contract["relative_path"],
            "contract_sha256": contract["sha256"],
            **group,
        }
        if not existing:
            monitor.atomic_json(paths["result"], result)
        if state["observation"] != "completed":
            if "completed" not in OBSERVATION_TRANSITIONS.get(state["observation"], set()):
                raise WaitError("wait cannot be completed from current state")
            state["observation"] = "completed"
            append_history(state, "completed")
            monitor.atomic_json(paths["state"], state)
        return result
    finally:
        handle.close()


def deliver_to_tool(paths: dict[str, Path]) -> dict[str, Any]:
    handle = lock_wait(paths)
    try:
        state = read_json(paths["state"])
        if state is None:
            raise WaitError("wait state is missing")
        if state["observation"] != "completed":
            raise WaitError("cannot deliver an incomplete wait")
        if state["delivery"] == "pending":
            state["delivery"] = "delivered_to_tool"
            append_history(state, "delivered_to_tool")
            monitor.atomic_json(paths["state"], state)
        elif state["delivery"] != "delivered_to_tool":
            # The notifier won the ownership race. Return the durable result
            # without invalidating its orphan-delivery state.
            state["tool_return_after_orphan"] = utc_now()
            append_history(state, "tool_return_after_orphan")
            monitor.atomic_json(paths["state"], state)
        return state
    finally:
        handle.close()


def owner_alive(pid: int, start_time: str | None = None) -> bool:
    try:
        os.kill(pid, 0)
        return start_time is None or process_identity(pid) == start_time
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def notifier_unit(event_id: str) -> str:
    suffix = hashlib.sha256(event_id.encode()).hexdigest()[:10]
    return f"agent-wait-{event_id[:20]}-{suffix}"


def start_notifier(contract: dict[str, Any], event_id: str, owner_pid: int) -> dict[str, Any]:
    paths = wait_paths(contract, event_id)
    unit = notifier_unit(event_id)
    handle = lock_wait(paths)
    try:
        existing = read_json(paths["unit"])
        if systemd_active(unit):
            if not existing or existing.get("event_id") != event_id or existing.get("contract_sha256") != contract["sha256"]:
                raise WaitError(f"active notifier unit identity drift: {unit}")
            return {**existing, "status": "adopted"}
        command = [
            "systemd-run",
            "--user",
            "--collect",
            f"--unit={unit}",
            f"--property=WorkingDirectory={contract['root']}",
            sys.executable,
            str(Path(__file__).resolve()),
            "watch-notify",
            "--contract",
            str(contract["path"]),
            "--event-id",
            event_id,
            "--owner-pid",
            str(owner_pid),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise WaitError(f"could not start wait notifier: {completed.stderr.strip()}")
        metadata = {
            "unit": unit,
            "event_id": event_id,
            "contract_sha256": contract["sha256"],
            "status": "started",
            "started": utc_now(),
            "command": command,
        }
        monitor.atomic_json(paths["unit"], metadata)
        return metadata
    finally:
        handle.close()


def notification_environment(paths: dict[str, Path], registration: dict[str, Any], destination: str) -> dict[str, str]:
    return {
        **os.environ,
        "JOB_WAIT_EVENT_ID": registration["event_id"],
        "JOB_WAIT_SESSION_ID": registration["session_id"],
        "JOB_WAIT_RESULT_PATH": str(paths["result"]),
        "JOB_WAIT_DESTINATION": destination,
    }


def notify_once(contract: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    notification = contract["notification"]
    registration = validate_registration(contract, paths)
    if not notification.get("authorized"):
        value = {"status": "held", "timestamp": utc_now(), "reason": "notification not authorized"}
        monitor.atomic_json(paths["notification"], value)
        return value
    handle = lock_wait(paths)
    try:
        state = read_json(paths["state"])
        if state is None:
            raise WaitError("wait state is missing")
        if state["delivery"] != "orphaned":
            return read_json(paths["notification"]) or {"status": state["delivery"]}
        state["delivery"] = "notifying"
        append_history(state, "notifying")
        monitor.atomic_json(paths["state"], state)
        claimed = {"status": "claimed", "timestamp": utc_now(), "attempts": 1}
        monitor.atomic_json(paths["notification"], claimed)
    finally:
        handle.close()
    completed = subprocess.run(
        notification["command"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=notification_environment(paths, registration, str(notification["destination"])),
    )
    value = {
        "status": "sent" if completed.returncode == 0 else "failed",
        "timestamp": utc_now(),
        "attempts": 1,
        "returncode": completed.returncode,
        "destination": notification["destination"],
    }
    monitor.atomic_json(paths["notification"], value)
    transition(paths, delivery="notified" if completed.returncode == 0 else "notification_failed")
    return value


def wait_loop(
    contract: dict[str, Any],
    paths: dict[str, Path],
    *,
    timeout_seconds: float,
    interrupt: Callable[[], bool] = lambda: False,
    active: Callable[[str], bool] = systemd_active,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    started = clock()
    transition(paths, observation="waiting")
    while True:
        elapsed = clock() - started
        if interrupt():
            transition(paths, delivery="orphaned")
            raise WaitInterrupted("wait interrupted; durable notifier retains ownership")
        group = evaluate_group(contract, elapsed, active=active)
        if group["status"] != "pending":
            return complete_wait(paths, contract, group)
        if elapsed >= timeout_seconds:
            return complete_wait(
                paths,
                contract,
                {"status": "failure", "outcome": "wait_timeout", "monitors": group["monitors"]},
            )
        sleeper(min(contract["check_interval_seconds"], timeout_seconds - elapsed))


def command_wait(args: argparse.Namespace) -> int:
    if args.harness == "opencode" and not args.message_id:
        raise WaitError("--message-id is required for the opencode harness")
    contract = load_contract(args.contract, args.session_id)
    event_id = validate_event_id(
        args.event_id or event_id_for(args.session_id, args.message_id, contract["sha256"])
    )
    paths = wait_paths(contract, event_id)
    register_wait(
        contract, event_id, args.session_id, args.message_id, args.owner_pid, args.harness
    )
    validate_registration(contract, paths)
    requested_timeout = args.timeout_seconds or contract["timeout_seconds"]
    if (
        not math.isfinite(requested_timeout)
        or requested_timeout <= 0
        or requested_timeout > contract["timeout_seconds"]
    ):
        raise WaitError("wait timeout must be positive and no longer than the contract timeout")
    state = read_json(paths["state"])
    if state and state["observation"] == "completed":
        result = read_json(paths["result"])
        if result is None:
            raise WaitError("completed wait has no durable result")
        deliver_to_tool(paths)
        print(json.dumps(result, indent=2, sort_keys=True))
        return monitor.result_exit(result["outcome"])
    if state and state["delivery"] != "pending":
        raise WaitError(f"wait delivery is already owned by {state['delivery']}")
    ensure_monitors(contract, not args.no_start)
    if not args.no_notifier:
        start_notifier(contract, event_id, args.owner_pid)
    interrupted = False

    def stop(_signum: int, _frame: Any) -> None:
        nonlocal interrupted
        interrupted = True

    previous_term = signal.signal(signal.SIGTERM, stop)
    previous_int = signal.signal(signal.SIGINT, stop)
    try:
        result = wait_loop(
            contract,
            paths,
            timeout_seconds=requested_timeout,
            interrupt=lambda: interrupted,
        )
        deliver_to_tool(paths)
        print(json.dumps(result, indent=2, sort_keys=True))
        return monitor.result_exit(result["outcome"])
    except WaitInterrupted as exc:
        print(str(exc), file=sys.stderr)
        return 130
    finally:
        signal.signal(signal.SIGTERM, previous_term)
        signal.signal(signal.SIGINT, previous_int)


def command_watch_notify(args: argparse.Namespace) -> int:
    contract = load_contract(args.contract)
    paths = wait_paths(contract, args.event_id)
    registration = validate_registration(contract, paths)
    if registration["owner_pid"] != args.owner_pid:
        raise WaitError("notifier owner identity drift")
    started = time.monotonic()
    while True:
        state = read_json(paths["state"])
        if state is None:
            raise WaitError("wait state is missing")
        if state["delivery"] in {
            "delivered_to_tool",
            "acknowledged",
            "notified",
            "notification_failed",
            "notification_unknown",
        }:
            return 0
        if state["delivery"] == "notifying":
            return monitor.EXIT_TRANSPORT
        if state["delivery"] == "pending" and not owner_alive(
            args.owner_pid, registration.get("owner_start_time")
        ):
            transition(paths, delivery="orphaned")
            state = read_json(paths["state"])
        if state and state["observation"] != "completed":
            group = evaluate_group(contract, time.monotonic() - started)
            if group["status"] != "pending":
                complete_wait(paths, contract, group)
            elif time.monotonic() - started >= contract["timeout_seconds"]:
                complete_wait(
                    paths,
                    contract,
                    {"status": "failure", "outcome": "wait_timeout", "monitors": group["monitors"]},
                )
        state = read_json(paths["state"])
        if state and state["observation"] == "completed" and state["delivery"] == "orphaned":
            value = notify_once(contract, paths)
            print(json.dumps(value, indent=2, sort_keys=True))
            return 0 if value["status"] in {"sent", "held"} else monitor.EXIT_TRANSPORT
        time.sleep(contract["check_interval_seconds"])


def command_transition(args: argparse.Namespace, target: str) -> int:
    contract = load_contract(args.contract)
    paths = wait_paths(contract, args.event_id)
    validate_registration(contract, paths)
    state = transition(paths, delivery=target)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


def command_status(args: argparse.Namespace) -> int:
    contract = load_contract(args.contract)
    paths = wait_paths(contract, args.event_id)
    validate_registration(contract, paths)
    payload = {
        key: read_json(paths[key])
        for key in ("registration", "state", "result", "notification", "unit")
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    wait = subparsers.add_parser("wait")
    wait.add_argument("--contract", required=True, type=Path)
    wait.add_argument("--session-id", required=True)
    wait.add_argument("--harness", choices=HARNESSES, default="opencode")
    wait.add_argument("--message-id", help="required for opencode; optional elsewhere")
    wait.add_argument("--owner-pid", required=True, type=int)
    wait.add_argument("--event-id")
    wait.add_argument("--timeout-seconds", type=float)
    wait.add_argument("--no-start", action="store_true")
    wait.add_argument("--no-notifier", action="store_true")

    watch = subparsers.add_parser("watch-notify")
    watch.add_argument("--contract", required=True, type=Path)
    watch.add_argument("--event-id", required=True)
    watch.add_argument("--owner-pid", required=True, type=int)

    for name in ("orphan", "notification-unknown", "ack", "status"):
        command = subparsers.add_parser(name)
        command.add_argument("--contract", required=True, type=Path)
        command.add_argument("--event-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "wait":
            return command_wait(args)
        if args.command == "watch-notify":
            return command_watch_notify(args)
        if args.command == "orphan":
            return command_transition(args, "orphaned")
        if args.command == "notification-unknown":
            return command_transition(args, "notification_unknown")
        if args.command == "ack":
            return command_transition(args, "acknowledged")
        return command_status(args)
    except (WaitError, monitor.MonitorError, OSError, subprocess.SubprocessError) as exc:
        print(f"wait error: {exc}", file=sys.stderr)
        return monitor.EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
