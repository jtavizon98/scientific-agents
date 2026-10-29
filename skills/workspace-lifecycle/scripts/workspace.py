#!/usr/bin/env python3
"""Sweep the project workspace on the current host.

The default dry run writes a JSON report and a Markdown summary under
.lifecycle/. --apply removes clean, idle linked worktrees whose branch
is confirmed on its remote by a live `git ls-remote`. --settle-sessions also
settles closed sessions with no untracked content into
sessions/ARCHIVE.md. --approve REPORT_SHA256 deletes the needs_approval
items of that report that are still needs_approval with unchanged fingerprints.
Every action reclassifies its target first and skips on any change.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import datetime as dt
import fcntl
import fnmatch
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator


SCHEMA_VERSION = 1
MINIMUM_AGE_DAYS = 30
MAX_ENTRIES = 10_000
MAX_BYTES = 64 * 1024 * 1024
LS_REMOTE_TIMEOUT = 30
CLOSED_STATUSES = ("complete", "completed", "closed", "superseded")
OPEN_WORDS = ("pending", "await")
LIVE_HANDOFF = {"in_progress", "in progress", "blocked", "paused", "awaiting human review", "awaiting_human_review"}
LEFTOVER_DISPOSITIONS = ("disposable-once-pushed", "keep-until-review", "unique-never-delete")
REBUILDABLE_DIRS = {"__pycache__", ".pytest_cache"}
PYTEST_CACHE_FILES = {".gitignore", "CACHEDIR.TAG", "README.md", "v", "v/cache",
                      "v/cache/lastfailed", "v/cache/nodeids", "v/cache/stepwise"}
PYTEST_CACHE_DIRS = {"v", "v/cache"}
ORDER = ("remove", "settle", "needs_approval", "needs_owner", "too_large", "kept")
# All paths are relative to the project root (the Git checkout above the manifest).
# AGENT_SESSIONS_DIR moves the session folders; the manifest defaults to lifecycle/topology.json.
MANIFEST = Path("lifecycle") / "topology.json"
SESSIONS = Path(os.environ.get("AGENT_SESSIONS_DIR", "sessions"))
RUNTIME = Path(".lifecycle")
STATUS_RE = re.compile(r"^(?:-\s+)?Status:\s*(.+)$")
LEFTOVER_RE = re.compile(
    r"^\s*-\s*`([^`]+)`\s*[-:]?\s*`?(" + "|".join(LEFTOVER_DISPOSITIONS) + r")`?(?:\s*[-:]\s*(.*))?$"
)
ARCHIVE_HEADER = """# Settled sessions

Rows are appended by `workspace.py sweep --apply --settle-sessions`. Restore a
folder from the project root with `git checkout <commit> -- sessions/<name>`.

| Session | Dates | Outcome | Deliverables | Restore commit |
| --- | --- | --- | --- | --- |
"""


class LifecycleError(RuntimeError):
    pass


class TooLarge(LifecycleError):
    pass


class Changed(LifecycleError):
    """The target changed or lost eligibility since the scan; the action is skipped."""


# Small utilities


def current_time() -> float:
    return time.time()


def days_since(timestamp: float) -> float:
    return max(0.0, (current_time() - timestamp) / 86400)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def report_hash(report: dict[str, Any]) -> str:
    return digest({key: value for key, value in report.items() if key != "report_sha256"})


def file_sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LifecycleError(f"{path} must contain a JSON object")
    return value


def read_text(path: Path) -> str:
    """A missing file reads as ''; an unreadable one is an error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    except OSError as exc:
        raise LifecycleError(f"cannot read {path}: {exc}") from exc


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def run(command: list[str], timeout: int = 120, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LifecycleError(f"command failed: {' '.join(command)}: {exc}") from exc


def git(path: Path | str, *args: str) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", str(path), *args])


def git_ok(path: Path | str, *args: str) -> str:
    """Run a Git query and fail closed: a nonzero exit is an error, never empty output."""
    completed = git(path, *args)
    check(completed.returncode == 0, f"git {' '.join(args[:2])} failed in {path}: {completed.stderr.strip()}")
    return completed.stdout


def git_optional(path: Path | str, *args: str) -> str:
    """Run a Git query whose exit 1 with no message means 'unset'; anything else must succeed."""
    completed = git(path, *args)
    if completed.returncode == 1 and not completed.stderr.strip():
        return ""
    check(completed.returncode == 0, f"git {' '.join(args[:2])} failed in {path}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def same_path(left: Path | str, right: Path | str) -> bool:
    try:
        return os.path.samefile(left, right)
    except OSError:
        return Path(left).resolve(strict=False) == Path(right).resolve(strict=False)


def is_inside(path: Path, roots: Iterable[Path]) -> bool:
    """True when path lies strictly below one of roots, comparing by inode."""
    roots = list(roots)
    return any(same_path(parent, root) for parent in path.parents for root in roots)


def overlaps(left: Path, right: Path) -> bool:
    """True when two paths are the same or one is an ancestor of the other, component by component."""
    return same_path(left, right) or is_inside(left, [right]) or is_inside(right, [left])


def contained(path: Path, roots: Iterable[Path]) -> bool:
    """True when path has no symlink component and its real path lies strictly below a root."""
    real = os.path.realpath(path)
    if real != os.path.abspath(path):
        return False
    return any(real.startswith(os.path.realpath(root).rstrip("/") + "/") for root in roots)


def check(condition: Any, message: str) -> None:
    if not condition:
        raise LifecycleError(message)


def entry(kind: str, path: Path | str, disposition: str, reason: str, **extra: Any) -> dict[str, Any]:
    """One report item."""
    return {"id": f"{kind}:{path}", "kind": kind, "path": str(path), "disposition": disposition,
            "reason": reason, **extra}


def reraise(exc: OSError) -> None:
    raise exc


def cache_entry_allowed(kind: str, relative: str, info: os.stat_result) -> bool:
    if stat.S_ISLNK(info.st_mode) or ".git" in relative.split("/"):
        return False
    if kind == "__pycache__":
        return stat.S_ISREG(info.st_mode) and "/" not in relative and relative.endswith((".pyc", ".pyo"))
    if stat.S_ISDIR(info.st_mode):
        return relative in PYTEST_CACHE_DIRS
    return stat.S_ISREG(info.st_mode) and relative in PYTEST_CACHE_FILES - PYTEST_CACHE_DIRS


def rebuildable_listing(base: Path, name: str) -> list[tuple[str, int, int, int]] | None:
    """List an ignored status entry when it is demonstrably rebuildable, else return None.

    Allowed: *.pyc and *.pyo files, `__pycache__/` holding only such files, and
    `.pytest_cache/` holding only pytest's standard files (`v/cache/` with
    `lastfailed`, `nodeids`, `stepwise`). Nothing else, no
    symlinks, and no nested `.git` qualifies.
    """
    target = base / name.rstrip("/")
    try:
        info = target.lstat()
        if not name.endswith("/"):
            if stat.S_ISREG(info.st_mode) and target.name.endswith((".pyc", ".pyo")):
                return [(name, info.st_mode, info.st_size, info.st_mtime_ns)]
            return None
        if target.name not in REBUILDABLE_DIRS or not stat.S_ISDIR(info.st_mode):
            return None
        rows = []
        for current, dirs, files in os.walk(target, onerror=reraise):
            for child in dirs + files:
                child_info = os.lstat(os.path.join(current, child))
                relative = os.path.relpath(os.path.join(current, child), target)
                if len(rows) >= MAX_ENTRIES or not cache_entry_allowed(target.name, relative, child_info):
                    return None
                rows.append((relative, child_info.st_mode, child_info.st_size, child_info.st_mtime_ns))
        return rows
    except OSError:
        return None


# Topology


def safe_absolute(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("/")
        and value != "/"
        and ".." not in Path(value).parts
        and not any(char in value for char in "*?[]{}\n\r\0")
    )


def safe_relative(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and not value.startswith("/")
        and ".." not in Path(value).parts
        and not {"admin", "credentials", "mnt"} & set(Path(value).parts)
    )


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Check the fields the sweep relies on; the JSON schema documents the full format."""
    check(manifest.get("schema_version") == SCHEMA_VERSION, "manifest schema_version must be 1")
    age, artifact_age = manifest.get("minimum_age_days"), manifest.get("artifact_minimum_age_days")
    check(isinstance(age, int) and age >= MINIMUM_AGE_DAYS,
          f"minimum_age_days must be an integer of at least {MINIMUM_AGE_DAYS}")
    check(isinstance(artifact_age, int) and 0 <= artifact_age < age,
          "artifact_minimum_age_days must be non-negative and below minimum_age_days")
    hosts = manifest.get("hosts")
    check(isinstance(hosts, list) and hosts and all(isinstance(host, dict) for host in hosts),
          "hosts must be a non-empty list of objects")
    ids = [host.get("id") for host in hosts]
    check(all(isinstance(value, str) and value for value in ids) and len(set(ids)) == len(ids),
          "host ids must be unique non-empty strings")
    for host in hosts:
        check(safe_absolute(host.get("project_root")), f"host {host['id']} project_root is unsafe")
        names = host.get("hostnames", [])
        check(isinstance(names, list) and all(isinstance(name, str) and name for name in names),
              f"host {host['id']} hostnames must be a string list")
    inventory = manifest.get("inventory")
    check(isinstance(inventory, dict), "inventory must be an object")
    for section in (manifest.get("repositories"), manifest.get("storage_tiers"), inventory.get("worktree_roots", [])):
        check(isinstance(section, list), "repositories, storage_tiers, and worktree_roots must be lists")
        for row in section:
            check(isinstance(row, dict) and row.get("host") in ids and safe_absolute(row.get("path")),
                  f"entry needs a known host and a safe absolute path: {row}")
    check(isinstance(inventory.get("local_roots"), list), "inventory.local_roots must be a list")
    for root in inventory["local_roots"]:
        check(isinstance(root, dict) and safe_relative(root.get("path")) and isinstance(root.get("category"), str)
              and isinstance(root.get("max_depth"), int) and 0 <= root["max_depth"] <= 4
              and isinstance(root.get("cleanup_eligible"), bool)
              and all(isinstance(item, str) and item for item in root.get("include", ["*"])),
              f"invalid local root: {root}")


def project_root(start: Path) -> Path:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / ".git").exists():
            return candidate
    raise LifecycleError(f"cannot locate the project checkout above {start}")


def local_host(manifest: dict[str, Any], root: Path, override: str | None = None) -> str:
    """Select the topology host by --local-host, hostname, or project root."""
    hosts = manifest["hosts"]
    if override:
        host = next((row for row in hosts if row["id"] == override), None)
        check(host, f"unknown host: {override}")
    else:
        names = {socket.gethostname().lower(), socket.getfqdn().lower()}
        host = next((row for row in hosts if names & {n.lower() for n in row.get("hostnames", [])}), None)
        host = host or next((row for row in hosts if same_path(row["project_root"], root)), None)
        check(host, f"no topology host matches {sorted(names)} or {root}; pass --local-host")
    check(same_path(host["project_root"], root),
          f"host {host['id']} project_root {host['project_root']} is not {root}")
    return host["id"]


class Context:
    """The topology, project root, host, and session records one scan or action works from."""

    def __init__(self, manifest: dict[str, Any], root: Path, host: str, sessions: list[dict[str, Any]]):
        self.manifest, self.root, self.host, self.sessions = manifest, root, host, sessions

    def paths(self, section: list[dict[str, Any]]) -> list[Path]:
        return [Path(row["path"]) for row in section if row["host"] == self.host]

    @property
    def registered(self) -> list[Path]:
        return self.paths(self.manifest["repositories"])

    @property
    def tiers(self) -> list[Path]:
        return self.paths(self.manifest["storage_tiers"])

    @property
    def worktree_roots(self) -> list[Path]:
        return self.paths(self.manifest["inventory"].get("worktree_roots", []))

    def anchor_problem(self, path: Path, inventoried: bool = False) -> str:
        """Why the topology protects path, or ''.

        Registered checkouts and the project root protect themselves, their
        ancestors, and everything below them. $HOME and storage tiers protect
        themselves and their ancestors. An inventoried artifact (a configured
        local root) may lie below the project root, never below another checkout.
        """
        for anchor in self.registered:
            below_ok = inventoried and same_path(anchor, self.root)
            if same_path(path, anchor) or is_inside(anchor, [path]) or (not below_ok and is_inside(path, [anchor])):
                return f"overlaps registered checkout {anchor}"
        if not inventoried and is_inside(path, [self.root]):
            return f"inside the project root {self.root}"
        for anchor in [self.root, Path.home(), *self.tiers]:
            if same_path(path, anchor) or is_inside(anchor, [path]):
                return f"is or contains {anchor}"
        return ""

    @property
    def boundaries(self) -> list[Path]:
        return [*self.worktree_roots, *self.tiers, *self.registered, self.root]


def make_context(manifest: dict[str, Any], root: Path, host: str) -> Context:
    return Context(manifest, root, host, load_sessions(root))


# Observation


def tree_fingerprint(path: Path) -> dict[str, Any]:
    """Fingerprint a small tree by content SHA-256, inode, mode, size, and mtime without following symlinks."""

    def row(target: Path, info: os.stat_result) -> dict[str, Any]:
        value = {"mode": info.st_mode, "size": info.st_size, "inode": info.st_ino, "mtime_ns": info.st_mtime_ns}
        if stat.S_ISLNK(info.st_mode):
            value["link_target"] = os.readlink(target)
        elif stat.S_ISREG(info.st_mode):
            value["sha256"] = file_sha256(target)
        return value

    try:
        info = path.lstat()
    except FileNotFoundError:
        return {"exists": False}
    total = info.st_size if stat.S_ISREG(info.st_mode) else 0
    if total > MAX_BYTES:
        raise TooLarge(f"more than {MAX_BYTES >> 20} MiB")
    rows: dict[str, dict[str, Any]] = {".": row(path, info)}
    stack = [path] if stat.S_ISDIR(info.st_mode) else []
    while stack:
        with os.scandir(stack.pop()) as entries:
            for child in entries:
                child_info = child.stat(follow_symlinks=False)
                total += child_info.st_size if stat.S_ISREG(child_info.st_mode) else 0
                if len(rows) > MAX_ENTRIES or total > MAX_BYTES:
                    raise TooLarge(f"more than {MAX_ENTRIES} entries or {MAX_BYTES >> 20} MiB")
                rows[os.path.relpath(child.path, path)] = row(Path(child.path), child_info)
                if child.is_dir(follow_symlinks=False):
                    stack.append(Path(child.path))
    newest = max(value["mtime_ns"] for value in rows.values())
    return {"exists": True, "entries": len(rows), "bytes": total, "newest_mtime_ns": newest,
            "has_git": any(".git" in name.split("/") for name in rows), "rows_sha256": digest(rows)}


def status_entries(path: Path, *pathspec: str) -> list[tuple[str, str]]:
    """Every status entry, including untracked and ignored files, as (code, path)."""
    output = git_ok(path, "status", "--porcelain", "-z", "--ignored=matching", "--untracked-files=all",
                    *(["--", *pathspec] if pathspec else []))
    records, rows, index = output.split("\0"), [], 0
    while index < len(records):
        record = records[index]
        index += 1
        if record:
            rows.append((record[:2], record[3:]))
            index += record[0] in "RC"
    return rows


def describe_status(base: Path, rows: list[tuple[str, str]], flags: int) -> tuple[list[str], str]:
    """Reasons that make content unique, and a digest of the allowlisted ignored content."""
    changed = sum(code not in {"??", "!!"} for code, _ in rows)
    untracked = sum(code == "??" for code, _ in rows)
    listings = {name: rebuildable_listing(base, name) for code, name in rows if code == "!!"}
    unknown = [name for name, listing in listings.items() if listing is None]
    reasons = [f"{changed} uncommitted tracked changes"] if changed else []
    reasons += [f"{untracked} untracked files"] if untracked else []
    reasons += [f"{len(unknown)} ignored entries outside the rebuildable allowlist ({unknown[0]})"] if unknown else []
    reasons += [f"{flags} files marked assume-unchanged or skip-worktree"] if flags else []
    return reasons, digest(listings)


def flagged_files(path: Path, *pathspec: str) -> int:
    """Count index entries whose assume-unchanged or skip-worktree flag can hide edits from status."""
    output = git_ok(path, "ls-files", "-v", *(["--", *pathspec] if pathspec else []))
    return sum(line[:1].islower() or line[:1] == "S" for line in output.splitlines())


def worktree_entries(path: Path) -> list[dict[str, Any]]:
    entries, current = [], {}
    for line in [*git_ok(path, "worktree", "list", "--porcelain").splitlines(), ""]:
        if not line:
            if current:
                entries.append(current)
            current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value or True
    return entries


def inspect_checkout(path: Path) -> dict[str, Any]:
    """Observe one Git checkout read-only, failing closed on any query error."""
    dirs = git_ok(path, "rev-parse", "--absolute-git-dir", "--git-common-dir").splitlines()
    check(len(dirs) == 2, f"unexpected rev-parse output in {path}")
    git_dir, common = dirs
    common_dir = (path / common).resolve()
    head = git_optional(path, "rev-parse", "--verify", "-q", "HEAD")
    branch = git_optional(path, "symbolic-ref", "-q", "--short", "HEAD")
    rows = status_entries(path)
    unique, ignored_sha256 = describe_status(path, rows, flagged_files(path))
    tracking = git_ok(path, "branch", "-r", "--contains", head).strip() if head else ""
    times = [float(git_ok(path, "show", "-s", "--format=%ct", head))] if head else [0.0]
    times += [item.stat().st_mtime for item in (Path(git_dir) / "HEAD", Path(git_dir) / "logs" / "HEAD")
              if item.exists()]
    entries = worktree_entries(path)
    registered = next((row["worktree"] for row in entries if same_path(row["worktree"], path)), "")
    return {
        "main": same_path(git_dir, common_dir),
        "main_worktree": entries[0]["worktree"] if entries else "",
        "locked": any(same_path(row["worktree"], path) and "locked" in row for row in entries),
        "common_dir": common_dir,
        "fingerprint": {"registered": registered, "head": head, "branch": branch, "status_sha256": digest(rows),
                        "ignored_sha256": ignored_sha256},
        "unique": unique + ([] if tracking or not head else [f"HEAD {head[:12]} is on no remote-tracking ref"]),
        "age_days": days_since(max(times)),
        "entries": entries,
    }


def same_repository(path: Path, url: str, common_dir: Path) -> bool:
    """True when a remote URL is a local path into the repository that owns path."""
    if url.startswith("file://"):
        url = url[len("file://"):]
    elif "://" in url or (re.match(r"^[^/]+:", url) and not os.path.exists(url)):
        return False
    local = Path(url) if os.path.isabs(url) else path / url
    if not local.exists():
        return False
    other = git(local, "rev-parse", "--git-common-dir")
    return other.returncode == 0 and same_path(local / other.stdout.strip(), common_dir)


def remote_durability(path: Path, branch: str, head: str, common_dir: Path) -> str:
    """Return '' when a live `git ls-remote` shows a branch tip that contains HEAD, else why not."""
    remote = git_optional(path, "config", "--get", f"branch.{branch}.remote")
    if not remote:
        remotes = git_ok(path, "remote").split()
        if len(remotes) != 1:
            return "no upstream remote configured"
        remote = remotes[0]
    if remote == ".":
        return "branch tracks the local repository (remote '.')"
    if same_repository(path, git_ok(path, "remote", "get-url", remote).strip(), common_dir):
        return f"remote {remote} is this same repository"
    ref = git_optional(path, "config", "--get", f"branch.{branch}.merge") or f"refs/heads/{branch}"
    env = {**os.environ, "GIT_SSH_COMMAND": "ssh -o BatchMode=yes", "GIT_TERMINAL_PROMPT": "0"}
    listed = run(["git", "-C", str(path), "ls-remote", remote, ref], timeout=LS_REMOTE_TIMEOUT, env=env)
    if listed.returncode != 0:
        message = (listed.stderr.strip().splitlines() or ["no message"])[-1]
        return f"git ls-remote {remote} failed: {message}"
    tips = [line.split("\t")[0] for line in listed.stdout.splitlines() if line.endswith("\t" + ref)]
    if len(tips) != 1:
        return f"{ref} is not on {remote}"
    if git(path, "cat-file", "-e", f"{tips[0]}^{{commit}}").returncode != 0:
        return f"{remote} tip {tips[0][:12]} is not present locally"
    ancestor = git(path, "merge-base", "--is-ancestor", head, tips[0])
    if ancestor.returncode == 1:
        return f"HEAD is not contained in {remote} {ref}"
    return "" if ancestor.returncode == 0 else f"merge-base failed: {ancestor.stderr.strip()}"


# Sessions


def field(text: str, label: str) -> str:
    match = re.search(rf"^\s*-\s*{re.escape(label)}:\s*(.*)$", text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).replace("`", "").strip() if match else ""


def session_status(state: str) -> str:
    """The template's `- Status:` line or a leading `Status:` line; prose sentences never count."""
    for line in state.splitlines():
        match = STATUS_RE.match(line)
        if match:
            return match.group(1).replace("`", "").strip().lower()
    return ""


def is_closed(status: str) -> bool:
    return bool(re.match(rf"({'|'.join(CLOSED_STATUSES)})\b", status)) and not any(
        word in status for word in OPEN_WORDS
    )


def live_owner(handoff: str, state: str) -> bool:
    try:
        value = json.loads(handoff) if handoff else {}
    except json.JSONDecodeError:
        return True
    status = value.get("session_status") or value.get("status") if isinstance(value, dict) else None
    jobs = field(state, "Jobs or delegated monitors").lower()
    return str(status).lower() in LIVE_HANDOFF or bool(jobs and not jobs.startswith("none"))


def parse_leftovers(result: str) -> list[dict[str, str]]:
    section = re.search(r"^## Leftovers\s*$(.*?)(?=^## |\Z)", result, re.MULTILINE | re.DOTALL)
    rows = []
    for line in section.group(1).splitlines() if section else []:
        match = LEFTOVER_RE.match(line)
        if match:
            rows.append({"target": match.group(1).strip(), "disposition": match.group(2),
                         "note": (match.group(3) or "").strip()})
    return rows


def load_sessions(root: Path) -> list[dict[str, Any]]:
    sessions = []
    for path in sorted((root / SESSIONS).iterdir()):
        if not path.is_dir() or path.is_symlink():
            continue
        try:
            texts = {name: read_text(path / name) for name in ("BRIEF.md", "STATE.md", "RESULT.md", "HANDOFF.json")}
        except LifecycleError as exc:
            sessions.append({"name": path.name, "path": path, "unreadable": str(exc), "open": True,
                             "closed": False, "text": "", "leftovers": []})
            continue
        state, result = texts["STATE.md"], texts["RESULT.md"]
        status = session_status(state)
        reviews = [field(state, "Review artifact and human state"), field(result, "Human review")]
        session = {
            "name": path.name,
            "path": path,
            "text": "\n".join(texts.values()),
            "result": result,
            "status": status,
            "closed": is_closed(status),
            "has_result": (path / "RESULT.md").is_file(),
            "review_pending": any(word in value.lower() for value in reviews for word in OPEN_WORDS),
            "live_owner": live_owner(texts["HANDOFF.json"], state),
            "leftovers": parse_leftovers(result),
        }
        session["open"] = not session["closed"] or session["review_pending"] or session["live_owner"]
        sessions.append(session)
    return sessions


def session_fingerprint(root: Path, relative: str) -> dict[str, Any]:
    rows = status_entries(root, relative)
    return {"commit": git_ok(root, "log", "-1", "--format=%H", "--", relative).strip(),
            "status_sha256": digest(rows), "ignored_sha256": describe_status(root, rows, 0)[1],
            "flags_sha256": digest(git_ok(root, "ls-files", "-v", "--", relative))}


def outcome_line(result: str) -> str:
    section = re.search(r"^## Outcome\s*$(.*?)(?=^## |\Z)", result, re.MULTILINE | re.DOTALL)
    paragraphs = (section.group(1) if section else result).strip().split("\n\n")
    paragraph = next((text for text in paragraphs if text.strip() and not text.lstrip().startswith("#")), "")
    return table_cell(" ".join(paragraph.split()) or "see RESULT.md")


def table_cell(text: str, limit: int = 240) -> str:
    text = text.replace("|", "/").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def classify_session(ctx: Context, session: dict[str, Any]) -> dict[str, Any]:
    root, minimum_age = ctx.root, ctx.manifest["minimum_age_days"]
    relative = (SESSIONS / session["name"]).as_posix()

    def done(disposition: str, reason: str, **extra: Any) -> dict[str, Any]:
        return entry("session", session["path"], disposition, reason, **extra)

    if not session["has_result"]:
        return done("kept", "no RESULT.md")
    if not session["closed"]:
        return done("kept", f"status: {session['status'] or 'missing'}")
    if session["review_pending"]:
        return done("kept", "human review pending")
    if session["live_owner"]:
        return done("kept", "live owner or delegated job recorded")
    owner = protection(ctx, session["path"])
    if owner:
        return done("kept", owner)
    for row in session["leftovers"]:
        target = os.path.expanduser(row["target"])
        if row["disposition"] == "unique-never-delete" or (
                row["disposition"] == "keep-until-review" and os.path.lexists(target)):
            return done("kept", f"RESULT.md carries a {row['disposition']} leftover ({row['target']}); "
                                "settling would drop that protection")
    unique, _ = describe_status(root, status_entries(root, relative), flagged_files(root, relative))
    if unique:
        return done("needs_owner", "; ".join(unique) + "; settling never deletes untracked content")
    log = git_ok(root, "log", "--format=%H %ct %cs", "--", relative).splitlines()
    if not log:
        return done("needs_owner", "never committed")
    commit, committed, last = log[0].split()
    if days_since(int(committed)) < minimum_age:
        return done("kept", f"last commit {days_since(int(committed)):.0f} days ago")
    deliverables = "; ".join(
        value for value in (field(session["result"], "Artifact and delivery"),
                            field(session["result"], "Starting and final commits")) if value
    )
    started = re.match(r"\d{4}-\d{2}-\d{2}", session["name"])
    record = {"commit": commit, "first": started.group(0) if started else log[-1].split()[2], "last": last,
              "outcome": outcome_line(session["result"]),
              "deliverables": table_cell(deliverables or "see RESULT.md at the restore commit")}
    return done("settle", f"closed, idle {days_since(int(committed)):.0f} days",
                fingerprint=session_fingerprint(root, relative), settle=record)


# Worktrees, checkouts, and leftover paths


def mention_needles(ctx: Context, path: Path, registered: str = "") -> list[re.Pattern[str]]:
    """Patterns naming path, anything below it, or an ancestor below the nearest configured boundary."""
    exact = [str(path), registered] + ([path.name] if re.search(r"\d", path.name) or len(path.name) >= 16 else [])
    needles = [re.compile(re.escape(text)) for text in exact if text]
    for parent in path.parents:
        if any(same_path(parent, boundary) for boundary in ctx.boundaries) or not is_inside(parent, ctx.boundaries):
            break
        needles.append(re.compile(re.escape(str(parent)) + r"/?(?=[\s`'\")\]>,;:]|$)", re.MULTILINE))
    return needles


def protection(ctx: Context, path: Path, registered: str = "") -> str:
    """Return why a session protects path, its ancestors, or its descendants, or ''."""
    unreadable = [s["name"] for s in ctx.sessions if s.get("unreadable")]
    if unreadable:
        return f"records of session {unreadable[0]} are unreadable, so every path is protected"
    needles = mention_needles(ctx, path, registered)
    # A session that lists this exact path as a disposable leftover mentions it
    # in order to release it, so its mention does not protect the path.
    releasing = {s["name"] for s, d in leftover_marks(ctx.sessions, path) if d == "disposable-once-pushed"}
    owners = [s["name"] for s in ctx.sessions
              if s["open"] and s["name"] not in releasing and any(n.search(s["text"]) for n in needles)]
    if owners:
        more = f" (+{len(owners) - 1} more)" if len(owners) > 1 else ""
        return f"mentioned by open session {owners[0]}{more}"
    for session in ctx.sessions:
        for row in session["leftovers"]:
            target = os.path.expanduser(row["target"])
            guarded = row["disposition"] == "unique-never-delete" or (
                row["disposition"] == "keep-until-review" and session["open"])
            if guarded and target.startswith("/") and overlaps(Path(target), path):
                return f"overlaps {target}, leftover {row['disposition']} in {session['name']}"
    return ""


def leftover_marks(sessions: list[dict[str, Any]], path: Path) -> list[tuple[dict[str, Any], str]]:
    marks = []
    for session in sessions:
        for row in session["leftovers"]:
            target = os.path.expanduser(row["target"])
            if target.startswith("/") and same_path(target, path):
                marks.append((session, row["disposition"]))
    return marks


def classify_checkout(ctx: Context, path: Path, info: dict[str, Any]) -> dict[str, Any]:
    fingerprint, unique = info["fingerprint"], info["unique"]

    def done(disposition: str, *reasons: str) -> dict[str, Any]:
        return entry("checkout" if info["main"] else "worktree", path, disposition, "; ".join(reasons),
                     main_worktree=info["main_worktree"], fingerprint=fingerprint)

    registered = Path(fingerprint["registered"] or path)
    owner = protection(ctx, path, fingerprint["registered"])
    anchored = ctx.anchor_problem(path) or ctx.anchor_problem(registered)
    if anchored:
        return done("kept", f"registered repository or protected path ({anchored})", *unique)
    if info["main"]:
        if owner:
            return done("kept", "unregistered clone", owner, *unique)
        return done("needs_owner", "unregistered clone", *(unique or ["clean, HEAD on a remote-tracking ref"]))
    if not fingerprint["registered"]:
        return done("needs_owner", "missing from its repository's worktree list")
    if not contained(registered, ctx.worktree_roots):
        return done("kept", "outside the configured worktree roots or behind a symlink")
    if owner:
        return done("kept", owner, *unique)
    if info["locked"]:
        return done("kept", "worktree is locked")
    if unique:
        return done("needs_owner", *unique)
    if not fingerprint["branch"]:
        return done("needs_owner", "detached HEAD; remote durability unknown")
    if info["age_days"] < ctx.manifest["minimum_age_days"]:
        return done("kept", f"last activity {info['age_days']:.0f} days ago")
    reason = remote_durability(path, fingerprint["branch"], fingerprint["head"], info["common_dir"])
    if reason:
        return done("needs_owner", f"remote durability unconfirmed: {reason}")
    return done("remove", f"clean; {fingerprint['branch']} confirmed by git ls-remote; "
                          f"idle {info['age_days']:.0f} days")


def deletion_problem(ctx: Context, path: Path, inventoried: bool = False) -> str:
    """Return why path may not be deleted by an approval, or ''."""
    if not safe_absolute(str(path)) or {"admin", "credentials"} & set(path.parts):
        return "unsafe or protected path"
    if os.path.realpath(path) != os.path.abspath(path):
        return "a path component is a symlink"
    anchored = ctx.anchor_problem(path, inventoried)
    if anchored:
        return anchored
    if contained(path, [ctx.root]):
        return "inside a mounted tree" if "mnt" in path.relative_to(ctx.root).parts else ""
    return "" if contained(path, ctx.tiers) else "outside the host storage tiers"


def tracking_problem(path: Path) -> str:
    """Return why Git owns path (tracked, or a repository below it), or ''."""
    top = git(path.parent, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        check("not a git repository" in top.stderr, f"git rev-parse failed in {path.parent}: {top.stderr.strip()}")
    elif git_ok(top.stdout.strip(), "ls-files", "--", str(path)).strip():
        return "tracked by Git"
    return ""


def approval_problem(ctx: Context, path: Path, inventoried: bool = False) -> tuple[str, str]:
    """Return (disposition, reason) blocking an approved deletion, or ('', '')."""
    problem = deletion_problem(ctx, path, inventoried)
    if problem:
        return "needs_owner", problem
    owner = protection(ctx, path)
    if owner:
        return "kept", owner
    tracked = tracking_problem(path)
    return ("needs_owner", tracked) if tracked else ("", "")


def approval_item(ctx: Context, kind: str, path: Path, reason: str) -> dict[str, Any]:
    disposition, problem = approval_problem(ctx, path, kind == "artifact")
    if problem:
        return entry(kind, path, disposition, problem)
    try:
        fingerprint = tree_fingerprint(path)
    except TooLarge as exc:
        return entry(kind, path, "too_large", str(exc))
    if (path / ".git").exists() or fingerprint.get("has_git"):
        return entry(kind, path, "needs_owner", "contains a Git repository")
    return entry(kind, path, "needs_approval", reason, fingerprint=fingerprint)


def classify_plain(ctx: Context, path: Path, default: tuple[str, str]) -> dict[str, Any]:
    """Classify a non-Git directory found in a worktree root or named as a leftover."""
    owner = protection(ctx, path)
    if owner:
        return entry("path", path, "kept", owner)
    disposable = [s for s, d in leftover_marks(ctx.sessions, path) if d == "disposable-once-pushed" and not s["open"]]
    if not disposable:
        return entry("path", path, *default)
    return approval_item(ctx, "path", path, f"disposable-once-pushed leftover of closed session "
                                            f"{disposable[0]['name']}; no archive")


def scan_paths(ctx: Context) -> list[dict[str, Any]]:
    queue: list[tuple[Path, tuple[str, str]]] = [(path, ("kept", "registered path, not a Git checkout"))
                                                 for path in ctx.registered]
    items: list[dict[str, Any]] = []
    for root in ctx.worktree_roots:
        try:
            children = sorted(child for child in root.iterdir() if child.is_dir() and not child.is_symlink())
        except OSError as exc:
            items.append(entry("root", root, "needs_owner", f"cannot list worktree root: {exc}"))
            continue
        queue += [(child, ("needs_owner", "not a Git checkout")) for child in children]
    for session in ctx.sessions:
        for row in session["leftovers"]:
            target = os.path.expanduser(row["target"])
            if safe_absolute(target):
                queue.append((Path(target), ("kept", f"leftover {row['disposition']} in {session['name']}")))
    seen: set[tuple[int, int]] = set()
    prunable: set[str] = set()
    while queue:
        path, default = queue.pop(0)
        try:
            info = path.stat()
        except OSError:
            if any(same_path(path, repo) for repo in ctx.registered) or path in ctx.registered:
                items.append(entry("path", path, "needs_owner", "registered path is missing"))
            continue
        if (info.st_dev, info.st_ino) in seen or not path.is_dir():
            continue
        seen.add((info.st_dev, info.st_ino))
        try:
            if not (path / ".git").exists():
                items.append(classify_plain(ctx, path, default))
                continue
            checkout = inspect_checkout(path)
            items.append(classify_checkout(ctx, path, checkout))
        except (LifecycleError, OSError) as exc:
            items.append(entry("path", path, "needs_owner", f"cannot inspect: {exc}"))
            continue
        for row in checkout["entries"]:
            if "prunable" not in row:
                queue.append((Path(row["worktree"]), default))
            elif row["worktree"] not in prunable:
                prunable.add(row["worktree"])
                items.append(entry("worktree", row["worktree"], "needs_owner",
                                   "registered worktree directory is missing (prunable)"))
    return items


# Rebuildable artifacts inside the project checkout


def bounded_walk(root: Path, max_depth: int) -> Iterable[Path]:
    stack = [(root, 0)] if root.is_dir() and not root.is_symlink() else []
    while stack:
        current, depth = stack.pop()
        if depth:
            yield current
        if depth < max_depth and current.is_dir() and not current.is_symlink():
            stack.extend((child, depth + 1) for child in sorted(current.iterdir(), reverse=True))


def scan_artifacts(ctx: Context) -> list[dict[str, Any]]:
    items = []
    for config in ctx.manifest["inventory"]["local_roots"]:
        if not config["cleanup_eligible"] or config["category"] not in {"cache", "generated_artifact"}:
            continue
        base = ctx.root / config["path"]
        try:
            tracked = set(git_ok(ctx.root, "ls-files", "--", config["path"]).splitlines())
        except LifecycleError as exc:
            items.append(entry("artifact", base, "needs_owner", f"cannot inspect: {exc}"))
            continue
        paths = [*([base] if config.get("include_root") and base.exists() else []),
                 *bounded_walk(base, config["max_depth"])]
        for path in paths:
            relative = path.relative_to(ctx.root).as_posix()
            name = path.relative_to(base).as_posix() if path != base else "."
            if not any(fnmatch.fnmatch(name, pattern) for pattern in config.get("include", ["*"])):
                continue
            if relative in tracked or any(row.startswith(relative + "/") for row in tracked):
                continue
            try:
                item = approval_item(ctx, "artifact", path, f"untracked rebuildable {config['category']}")
            except OSError as exc:
                item = entry("artifact", path, "needs_owner", f"cannot inspect: {exc}")
            if "fingerprint" in item:
                age = days_since(item["fingerprint"]["newest_mtime_ns"] / 1e9)
                if age < ctx.manifest["artifact_minimum_age_days"]:
                    item = entry("artifact", path, "kept", f"changed {age:.0f} days ago")
            items.append(item)
    return items


# Sweep and actions


def sweep(manifest: dict[str, Any], root: Path, host: str, settle_sessions: bool) -> dict[str, Any]:
    ctx = make_context(manifest, root, host)
    items = scan_paths(ctx) + scan_artifacts(ctx)
    items += [entry("session", s["path"], "needs_owner", f"unreadable session records: {s['unreadable']}")
              for s in ctx.sessions if s.get("unreadable")]
    for session in [s for s in ctx.sessions if not s.get("unreadable")] if settle_sessions else []:
        try:
            items.append(classify_session(ctx, session))
        except (LifecycleError, OSError) as exc:
            items.append(entry("session", session["path"], "needs_owner", f"cannot inspect: {exc}"))
    items.sort(key=lambda item: (ORDER.index(item["disposition"]), item["path"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "host": host,
        "project_root": str(root),
        "manifest_sha256": digest(manifest),
        "minimum_age_days": manifest["minimum_age_days"],
        "approver": manifest.get("approver", "the project owner"),
        "settle_sessions": settle_sessions,
        "items": items,
    }


def remove_worktree(ctx: Context, item: dict[str, Any]) -> str:
    path = Path(item["path"])
    current = classify_checkout(ctx, path, inspect_checkout(path))
    if current["disposition"] != "remove" or current["fingerprint"] != item["fingerprint"]:
        raise Changed(f"no longer removable: {current['reason']}")
    registered, branch = item["fingerprint"]["registered"], item["fingerprint"]["branch"]
    removed = git(item["main_worktree"], "worktree", "remove", registered)
    check(removed.returncode == 0, f"git worktree remove failed: {removed.stderr.strip()}")
    deleted = git(item["main_worktree"], "branch", "-d", branch)
    if deleted.returncode == 0:
        return f"removed worktree; deleted local branch {branch} (confirmed on its remote)"
    return f"removed worktree; kept branch {branch}: {deleted.stderr.strip()}"


def settle_session(ctx: Context, item: dict[str, Any]) -> str:
    folder = Path(item["path"])
    session = next((row for row in ctx.sessions if row["name"] == folder.name), None)
    check(session and not session.get("unreadable"), f"session {folder.name} disappeared or is unreadable")
    check(not any(row.get("unreadable") for row in ctx.sessions), "some session records are unreadable")
    current = classify_session(ctx, session)
    if current["disposition"] != "settle" or current["fingerprint"] != item["fingerprint"]:
        raise Changed(f"no longer settleable: {current['reason']}")
    relative = (SESSIONS / folder.name).as_posix()
    removed = git(ctx.root, "rm", "-r", "-q", "--", relative)
    check(removed.returncode == 0, f"git rm failed: {removed.stderr.strip()}")
    left = sorted(child.name for child in folder.iterdir()) if folder.exists() else []
    if folder.exists() and not left:
        folder.rmdir()
    record = item["settle"]
    index = ctx.root / SESSIONS / "ARCHIVE.md"
    write_atomic(index, (read_text(index) or ARCHIVE_HEADER) + (
        f"| {folder.name} | {record['first']}..{record['last']} | {record['outcome']} | "
        f"{record['deliverables']} | `{record['commit']}` |\n"))
    kept = f"; folder kept with rebuildable entries {', '.join(left)}" if left else ""
    return f"settled at {record['commit'][:12]} (git rm staged){kept}"


def delete_approved(ctx: Context, item: dict[str, Any]) -> str:
    path = Path(item["path"])
    _, problem = approval_problem(ctx, path, item["kind"] == "artifact")
    if problem:
        raise Changed(problem)
    try:
        current = tree_fingerprint(path)
    except TooLarge as exc:
        raise Changed(str(exc)) from exc
    if current != item["fingerprint"]:
        raise Changed("target changed since the approved report")
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return "deleted"


def attempt(item: dict[str, Any], action: Callable[[dict[str, Any]], str]) -> dict[str, Any]:
    try:
        return {"id": item["id"], "path": item["path"], "result": "done", "detail": action(item)}
    except Changed as exc:
        return {"id": item["id"], "path": item["path"], "result": "skipped", "detail": str(exc)}
    except (LifecycleError, OSError) as exc:
        return {"id": item["id"], "path": item["path"], "result": "failed", "detail": str(exc)}


def apply_report(report: dict[str, Any], manifest: dict[str, Any], root: Path,
                 approved: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Act on a fresh report; every action reclassifies its target with freshly loaded sessions."""
    fresh: Callable[[], Context] = lambda: make_context(manifest, root, report["host"])
    results = []
    for item in report["items"]:
        if item["disposition"] == "remove":
            results.append(attempt(item, lambda row: remove_worktree(fresh(), row)))
        elif item["disposition"] == "settle" and report["settle_sessions"]:
            results.append(attempt(item, lambda row: settle_session(fresh(), row)))
    current = {item["id"]: item for item in report["items"]}
    for item in (approved or {}).get("items", []):
        if item["disposition"] != "needs_approval":
            continue
        now = current.get(item["id"], {})
        if now.get("disposition") != "needs_approval" or now.get("fingerprint") != item["fingerprint"]:
            results.append({"id": item["id"], "path": item["path"], "result": "skipped",
                            "detail": f"now {now.get('disposition', 'absent')}: {now.get('reason', 'not observed')}"})
        else:
            results.append(attempt(item, lambda row: delete_approved(fresh(), row)))
    return results


def load_approved(root: Path, sha256: str, host: str, manifest: dict[str, Any]) -> dict[str, Any]:
    check(re.fullmatch(r"[0-9a-f]{64}", sha256), "--approve needs a lowercase SHA-256")
    malformed = []
    for path in sorted((root / RUNTIME).glob("sweep-*.json")):
        try:
            report = read_json(path)
        except LifecycleError:
            malformed.append(path.name)
            continue
        if report.get("report_sha256") == sha256:
            check(report_hash(report) == sha256, f"{path} does not match its recorded hash")
            check(report.get("host") == host and same_path(report.get("project_root", ""), root),
                  f"{path} was written for another host or checkout")
            check(report.get("manifest_sha256") == digest(manifest), f"{path} used a different topology")
            return report
    skipped = f"; skipped malformed {', '.join(malformed)}" if malformed else ""
    raise LifecycleError(f"no sweep report under {root / RUNTIME} has hash {sha256}{skipped}")


@contextlib.contextmanager
def exclusive_lock(runtime: Path) -> Iterator[None]:
    """Serialize every --apply run on this checkout."""
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime / "sweep.lock").open("w") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LifecycleError(f"another sweep --apply holds {runtime / 'sweep.lock'}") from exc
        yield


def write_new(path: Path, text: str) -> None:
    """Publish path atomically and never replace it: fsync a temporary file, then hard-link it into place."""
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(3)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise LifecycleError(f"refusing to overwrite {path}") from exc
    finally:
        temporary.unlink(missing_ok=True)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def publish_report(runtime: Path, report: dict[str, Any], text: str) -> Path:
    """Write the JSON report and Markdown summary under a unique name: UTC microseconds, pid, random suffix."""
    runtime.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    stem = f"sweep-{stamp}-{os.getpid()}-{secrets.token_hex(3)}"
    write_new(runtime / f"{stem}.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_new(runtime / f"{stem}.md", text)
    return runtime / f"{stem}.json"


def summary(report: dict[str, Any]) -> str:
    counts = collections.Counter(item["disposition"] for item in report["items"])
    mode = "apply" if "applied" in report else "dry run"
    lines = [f"# Workspace sweep {report['created_at']}", "",
             f"Host `{report['host']}`, {mode}, sessions {'evaluated' if report['settle_sessions'] else 'skipped'}.",
             f"Report sha256 `{report['report_sha256']}`.", "", "| Disposition | Count |", "| --- | ---: |"]
    lines += [f"| {name} | {counts[name]} |" for name in ORDER]
    for name in ORDER:
        rows = [item for item in report["items"] if item["disposition"] == name
                and not (name == "kept" and item["kind"] == "session")]
        if rows:
            lines += ["", f"## {name}", ""] + [f"- `{item['path']}`: {item['reason']}" for item in rows]
    if counts["needs_approval"]:
        lines += ["", f"{report.get('approver', 'The project owner')} approves the needs_approval deletions of this report by handing back its hash. Command:", "",
                  f"`python3 workspace.py sweep --apply --approve {report['report_sha256']}`"]
    if report.get("applied"):
        lines += ["", "## applied", ""]
        lines += [f"- `{row['path']}`: {row['result']}, {row['detail']}" for row in report["applied"]]
    return "\n".join(lines) + "\n"


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = value.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-manifest")
    validate.add_argument("--manifest", type=Path, default=None, help="default: lifecycle/topology.json at the project root")
    sweep_parser = commands.add_parser("sweep")
    sweep_parser.add_argument("--manifest", type=Path, default=None, help="default: lifecycle/topology.json at the project root")
    sweep_parser.add_argument("--local-host")
    sweep_parser.add_argument("--apply", action="store_true")
    sweep_parser.add_argument("--settle-sessions", action="store_true")
    sweep_parser.add_argument("--approve", metavar="REPORT_SHA256")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        args.manifest = args.manifest or project_root(Path.cwd()) / MANIFEST
        manifest = read_json(args.manifest)
        validate_manifest(manifest)
        if args.command == "validate-manifest":
            print(json.dumps({"valid": True, "manifest_sha256": digest(manifest)}, indent=2))
            return 0
        check(args.apply or not args.approve, "--approve requires --apply")
        root = project_root(args.manifest.parent)
        host = local_host(manifest, root, args.local_host)
        runtime = root / RUNTIME
        check(not runtime.is_symlink(), f"{runtime} must not be a symlink")
        with exclusive_lock(runtime) if args.apply else contextlib.nullcontext():
            approved = load_approved(root, args.approve, host, manifest) if args.approve else None
            report = sweep(manifest, root, host, args.settle_sessions)
            if args.apply:
                report["applied"] = apply_report(report, manifest, root, approved)
            report["report_sha256"] = report_hash(report)
            text = summary(report)
            written = publish_report(runtime, report, text)
        print(text + f"\nWrote {written} and .md")
        return 0
    except LifecycleError as exc:
        print(f"workspace lifecycle error: {exc}", file=sys.stderr)
        return 50


if __name__ == "__main__":
    raise SystemExit(main())
