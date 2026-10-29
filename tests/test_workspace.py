import fcntl
import importlib.util
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "skills" / "workspace-lifecycle" / "scripts" / "workspace.py"
SPEC = importlib.util.spec_from_file_location("workspace", MODULE_PATH)
lifecycle = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(lifecycle)

ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, env=ENV, check=True, capture_output=True, text=True
    ).stdout.strip()


def later(days=40):
    """Pretend the sweep runs `days` days from now."""
    return mock.patch.object(lifecycle, "current_time", lambda: time.time() + days * 86400)


class Workspace(unittest.TestCase):
    """A metadata checkout, a pushed source repository, and a worktree root."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "meta"
        self.src = self.base / "src"
        self.worktrees = self.base / "worktrees"
        self.worktrees.mkdir()
        for name in ("meta.git", "src.git"):
            git(self.base, "init", "-q", "--bare", "-b", "main", name)
        for path, remote in ((self.root, "meta.git"), (self.src, "src.git")):
            git(self.base, "init", "-q", "-b", "main", path.name)
            (path / "README.md").write_text("start\n")
            git(path, "remote", "add", "origin", str(self.base / remote))
        (self.root / ".gitignore").write_text("*.pdf\n.cache/\n__pycache__/\n.lifecycle/\n")
        (self.src / ".gitignore").write_text("__pycache__/\n.pytest_cache/\nbuild/\n")
        (self.root / "sessions").mkdir(parents=True)
        self.manifest_path = self.root / "lifecycle" / "topology.json"
        self.manifest_path.parent.mkdir(parents=True)
        self.write_manifest(self.manifest())
        for path in (self.root, self.src):
            git(path, "add", "-A")
            git(path, "commit", "-q", "-m", "start")
            git(path, "push", "-q", "-u", "origin", "main")

    def tearDown(self):
        self.temporary.cleanup()

    def manifest(self):
        return {
            "schema_version": 1,
            "minimum_age_days": 30,
            "artifact_minimum_age_days": 0,
            "hosts": [{"id": "test", "transport": "local", "project_root": str(self.root),
                       "hostnames": ["test-host.example"]}],
            "repositories": [
                {"id": "meta", "host": "test", "path": str(self.root), "role": "metadata"},
                {"id": "src", "host": "test", "path": str(self.src), "role": "source"},
            ],
            "storage_tiers": [{"id": "all", "host": "test", "path": str(self.base),
                               "recovery": "backed_up", "purpose": "test"}],
            "inventory": {
                "local_roots": [
                    {"id": "sessions", "path": "sessions", "category": "session",
                     "max_depth": 1, "cleanup_eligible": True},
                    {"id": "cache", "path": ".cache", "category": "cache", "max_depth": 0,
                     "include_root": True, "cleanup_eligible": True},
                ],
                "worktree_roots": [{"host": "test", "path": str(self.worktrees)}],
            },
        }

    def write_manifest(self, manifest):
        self.manifest_path.write_text(json.dumps(manifest, indent=2))

    def add_worktree(self, name, push=True, upstream=True):
        path = self.worktrees / name
        git(self.src, "worktree", "add", "-q", "-b", name, str(path))
        (path / "work.txt").write_text(name)
        git(path, "add", "work.txt")
        git(path, "commit", "-q", "-m", name)
        if push:
            git(path, "push", "-q", *(["-u"] if upstream else []), "origin", name)
        return path

    def add_session(self, name, status="complete", review="accepted", extra=None):
        path = self.root / "sessions" / name
        path.mkdir()
        (path / "STATE.md").write_text(f"# State\n\n- Status: `{status}`\n")
        (path / "RESULT.md").write_text(
            "# Result\n\n## Outcome\n\nThe study finished | cleanly.\n\n"
            f"## Handoff\n\n- Human review: `{review}`\n- Artifact and delivery: `report.pdf`\n"
            + (extra or "")
        )
        git(self.root, "add", "-A", str(path))
        git(self.root, "commit", "-q", "-m", f"session {name}")
        return path

    def sweep(self, settle=False):
        manifest = json.loads(self.manifest_path.read_text())
        return lifecycle.sweep(manifest, self.root, "test", settle)

    def item(self, report, path, kind=None):
        matches = [row for row in report["items"] if Path(row["path"]) == Path(path)
                   and kind in (None, row["kind"])]
        self.assertEqual(len(matches), 1, report["items"])
        return matches[0]

    def apply(self, report, approved=None):
        manifest = json.loads(self.manifest_path.read_text())
        return lifecycle.apply_report(report, manifest, self.root, approved)

    def context(self):
        return lifecycle.make_context(json.loads(self.manifest_path.read_text()), self.root, "test")


EXAMPLE = Path(__file__).parents[1] / "skills" / "workspace-lifecycle" / "references" / "topology.example.json"


class ManifestTests(unittest.TestCase):
    def test_tracked_topology_is_valid(self):
        lifecycle.validate_manifest(lifecycle.read_json(EXAMPLE))

    def test_rejects_short_age_and_unsafe_paths(self):
        manifest = lifecycle.read_json(EXAMPLE)
        for change in (
            {"minimum_age_days": 7},
            {"inventory": {**manifest["inventory"], "local_roots": [
                {"id": "x", "path": "../escape", "category": "cache", "max_depth": 0,
                 "cleanup_eligible": True}]}},
            {"inventory": {**manifest["inventory"], "worktree_roots": [{"host": "cluster", "path": "/tmp/*"}]}},
        ):
            with self.subTest(change=list(change)), self.assertRaises(lifecycle.LifecycleError):
                lifecycle.validate_manifest({**manifest, **change})


class HostTests(Workspace):
    def test_hostname_selects_host(self):
        with mock.patch.object(lifecycle.socket, "gethostname", return_value="test-host.example"):
            self.assertEqual(lifecycle.local_host(self.manifest(), self.root), "test")

    def test_project_root_is_the_fallback(self):
        with mock.patch.object(lifecycle.socket, "gethostname", return_value="elsewhere"), \
                mock.patch.object(lifecycle.socket, "getfqdn", return_value="elsewhere"):
            self.assertEqual(lifecycle.local_host(self.manifest(), self.root), "test")

    def test_wrong_project_root_is_refused(self):
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.local_host(self.manifest(), self.src, "test")


class WorktreeTests(Workspace):
    def test_clean_confirmed_old_worktree_is_removed_with_its_branch(self):
        path = self.add_worktree("done-20260801")
        (path / "__pycache__").mkdir()
        (path / "__pycache__" / "x.pyc").write_text("x")
        with later():
            report = self.sweep()
            self.assertEqual(self.item(report, path)["disposition"], "remove")
            results = self.apply(report)
        self.assertEqual(results[0]["result"], "done", results)
        self.assertFalse(path.exists())
        self.assertEqual(git(self.src, "branch", "--list", "done-20260801"), "")
        self.assertEqual(self.item(report, self.src)["disposition"], "kept")

    def test_branch_that_git_branch_d_refuses_is_kept(self):
        path = self.add_worktree("nomerge-20260801", upstream=False)
        with later():
            results = self.apply(self.sweep())
        self.assertFalse(path.exists())
        self.assertIn("kept branch", results[0]["detail"])
        self.assertNotEqual(git(self.src, "branch", "--list", "nomerge-20260801"), "")

    def test_unique_or_young_worktrees_are_kept(self):
        dirty = self.add_worktree("dirty-20260801")
        (dirty / "work.txt").write_text("changed")
        untracked = self.add_worktree("untracked-20260801")
        (untracked / "new.txt").write_text("new")
        unpushed = self.add_worktree("unpushed-20260801", push=False)
        ignored = self.add_worktree("ignored-20260801")
        (ignored / "build").mkdir()
        (ignored / "build" / "notes.txt").write_text("unique")
        with later():
            report = self.sweep()
        for path in (dirty, untracked, unpushed, ignored):
            with self.subTest(path=path.name):
                self.assertEqual(self.item(report, path)["disposition"], "needs_owner")
        self.assertIn("remote-tracking", self.item(report, unpushed)["reason"])
        self.assertIn("rebuildable allowlist (build/)", self.item(report, ignored)["reason"])
        young = self.add_worktree("young-20260801")
        self.assertEqual(self.item(self.sweep(), young)["disposition"], "kept")

    def test_assume_unchanged_edit_blocks_removal(self):
        path = self.add_worktree("hidden-20260801")
        git(path, "update-index", "--assume-unchanged", "work.txt")
        (path / "work.txt").write_text("edited")
        with later():
            item = self.item(self.sweep(), path)
        self.assertEqual(item["disposition"], "needs_owner")
        self.assertIn("assume-unchanged", item["reason"])

    def test_allowlisted_caches_are_inspected(self):
        cases = {
            "pyc-20260801": ("__pycache__/a.cpython-313.pyc", "remove"),
            "pytest-20260801": (".pytest_cache/v/cache/nodeids", "remove"),
            "pyvother-20260801": (".pytest_cache/v/other/x", "needs_owner"),
            "pycustom-20260801": (".pytest_cache/v/cache/custom", "needs_owner"),
            "notes-20260801": ("__pycache__/notes.txt", "needs_owner"),
            "nested-20260801": ("__pycache__/.git/HEAD", "needs_owner"),
            "extra-20260801": (".pytest_cache/results.csv", "needs_owner"),
        }
        paths = {}
        for name, (inside, _) in cases.items():
            paths[name] = self.add_worktree(name)
            target = paths[name] / inside
            target.parent.mkdir(parents=True)
            target.write_text("x")
        with later():
            report = self.sweep()
        for name, (_, expected) in cases.items():
            with self.subTest(name=name):
                self.assertEqual(self.item(report, paths[name])["disposition"], expected)

    def test_self_remote_never_confirms(self):
        dot = self.add_worktree("dot-20260801")
        git(dot, "config", "branch.dot-20260801.remote", ".")
        mirror = self.add_worktree("mirror-20260801")
        git(self.src, "remote", "add", "self", str(self.src))
        git(mirror, "config", "branch.mirror-20260801.remote", "self")
        with later():
            report = self.sweep()
        self.assertIn("remote '.'", self.item(report, dot)["reason"])
        self.assertIn("same repository", self.item(report, mirror)["reason"])

    @unittest.skipIf(os.geteuid() == 0, "root can read anything")
    def test_unreadable_session_protects_everything(self):
        path = self.add_worktree("done-20260801")
        state = self.add_session("2026-08-01-secret") / "STATE.md"
        state.chmod(0)
        try:
            with later():
                report = self.sweep()
        finally:
            state.chmod(0o644)
        self.assertIn("unreadable", self.item(report, path)["reason"])
        self.assertEqual(self.item(report, state.parent)["disposition"], "needs_owner")

    def test_protected_parent_shields_child_worktree(self):
        task = self.worktrees / "task-20260801"
        task.mkdir()
        child = task / "child-20260801"
        git(self.src, "worktree", "add", "-q", "-b", "child-20260801", str(child))
        (child / "work.txt").write_text("child")
        git(child, "add", "work.txt")
        git(child, "commit", "-q", "-m", "child")
        git(child, "push", "-q", "-u", "origin", "child-20260801")
        with later():
            self.assertEqual(self.item(self.sweep(), child)["disposition"], "remove")
        self.add_session("2026-08-01-closed", extra=(
            f"\n## Leftovers\n\n- `{task}` `unique-never-delete` - task area\n"))
        with later():
            item = self.item(self.sweep(), child)
        self.assertEqual(item["disposition"], "kept")
        self.assertIn("unique-never-delete", item["reason"])

    def test_open_session_mention_of_parent_shields_child(self):
        task = self.worktrees / "task-20260802"
        task.mkdir()
        child = task / "child-20260802"
        git(self.src, "worktree", "add", "-q", "-b", "child-20260802", str(child))
        self.add_session("2026-08-01-open", status="in progress", extra=f"\nWork lives in `{task}/`.\n")
        with later():
            self.assertIn("open session", self.item(self.sweep(), child)["reason"])

    def test_registered_linked_checkout_is_protected(self):
        path = self.add_worktree("durable-20260801")
        manifest = self.manifest()
        manifest["repositories"].append({"id": "durable", "host": "test", "path": str(path), "role": "source"})
        self.write_manifest(manifest)
        with later():
            item = self.item(self.sweep(), path)
        self.assertEqual(item["disposition"], "kept")
        self.assertIn("protected", item["reason"])

    def test_worktree_outside_roots_is_kept(self):
        outside = self.base / "elsewhere-20260801"
        git(self.src, "worktree", "add", "-q", "-b", "elsewhere", str(outside))
        with later():
            self.assertEqual(self.item(self.sweep(), outside)["disposition"], "kept")
        link = self.base / "link"
        link.symlink_to(self.worktrees)
        self.assertFalse(lifecycle.contained(link / "x", [self.base]))
        self.assertTrue(lifecycle.contained(self.worktrees / "x", [self.base]))

    def test_live_remote_check_keeps_unconfirmed_branches(self):
        stale = self.add_worktree("stale-20260801")
        git(self.base / "src.git", "branch", "-D", "stale-20260801")
        with later():
            report = self.sweep()
        self.assertIn("is not on origin", self.item(report, stale)["reason"])
        git(self.src, "remote", "set-url", "origin", str(self.base / "missing.git"))
        failing = self.add_worktree("failing-20260801", push=False)
        git(self.src, "update-ref", "refs/remotes/origin/failing-20260801", git(failing, "rev-parse", "HEAD"))
        with later():
            item = self.item(self.sweep(), failing)
        self.assertEqual(item["disposition"], "needs_owner")
        self.assertIn("ls-remote origin failed", item["reason"])

    def test_open_or_pending_session_or_unique_leftover_protects_worktree(self):
        referenced = self.add_worktree("referenced-20260801")
        pending = self.add_worktree("pending-20260801")
        leftover = self.add_worktree("leftover-20260801")
        self.add_session("2026-08-01-open", status="in progress", extra=f"\nSee `{referenced}`.\n")
        self.add_session("2026-08-02-review", review="pending", extra=f"\nSee `{pending}`.\n")
        self.add_session("2026-08-03-closed", extra=(
            f"\n## Leftovers\n\n- `{leftover}` `unique-never-delete` - only copy\n"))
        with later():
            report = self.sweep()
        self.assertIn("open session 2026-08-01-open", self.item(report, referenced)["reason"])
        self.assertIn("open session 2026-08-02-review", self.item(report, pending)["reason"])
        self.assertIn("unique-never-delete", self.item(report, leftover)["reason"])

    def test_disposable_leftover_releases_only_its_own_session_mention(self):
        released = self.add_worktree("released-20260801")
        shared = self.add_worktree("shared-20260801")
        disposal = (f"\nRemove `{released}` and `{shared}`.\n\n## Leftovers\n\n"
                    f"- `{released}` `disposable-once-pushed` - pushed\n"
                    f"- `{shared}` `disposable-once-pushed` - pushed\n")
        self.add_session("2026-08-01-cleanup", status="in progress", extra=disposal)
        self.add_session("2026-08-02-other", status="in progress", extra=f"\nSee `{shared}`.\n")
        with later():
            report = self.sweep()
        self.assertEqual(self.item(report, released)["disposition"], "remove")
        self.assertIn("open session 2026-08-02-other", self.item(report, shared)["reason"])

    def test_change_after_scan_skips_removal(self):
        path = self.add_worktree("racing-20260801")
        with later():
            report = self.sweep()
            (path / "late.txt").write_text("late")
            results = self.apply(report)
        self.assertEqual(results[0]["result"], "skipped")
        self.assertTrue(path.exists())

    def test_git_query_failure_fails_closed(self):
        path = self.add_worktree("broken-20260801")
        real = lifecycle.git

        def failing(where, *args):
            if args[:2] == ("branch", "-r"):
                return subprocess.CompletedProcess(args, 128, "", "fatal: broken")
            return real(where, *args)

        with later(), mock.patch.object(lifecycle, "git", failing):
            item = self.item(self.sweep(), path)
        self.assertEqual(item["disposition"], "needs_owner")
        self.assertIn("cannot inspect", item["reason"])

    def test_non_git_directory_needs_owner(self):
        (self.worktrees / "loose-20260801").mkdir()
        report = self.sweep()
        self.assertEqual(self.item(report, self.worktrees / "loose-20260801")["disposition"], "needs_owner")


class ArtifactTests(Workspace):
    def test_oversized_tree_is_reported_without_aborting(self):
        cache = self.root / ".cache"
        cache.mkdir()
        for index in range(6):
            (cache / f"{index}.bin").write_text("x")
        path = self.add_worktree("done-20260801")
        with mock.patch.object(lifecycle, "MAX_ENTRIES", 5), later():
            report = self.sweep()
        self.assertEqual(self.item(report, cache)["disposition"], "too_large")
        self.assertEqual(self.item(report, path)["disposition"], "remove")

    def test_disposable_leftover_of_closed_session_needs_approval(self):
        bulk = self.base / "bulk-20260801"
        bulk.mkdir()
        (bulk / "out.root").write_text("data")
        self.add_session("2026-08-01-closed", extra=(
            f"\n## Leftovers\n\n- `{bulk}` `disposable-once-pushed` - outputs\n"))
        self.assertEqual(self.item(self.sweep(), bulk)["disposition"], "needs_approval")

    def test_large_standalone_file_is_not_hashed(self):
        (self.root / ".cache").write_text("x" * 100)
        with mock.patch.object(lifecycle, "MAX_BYTES", 10), \
                mock.patch.object(lifecycle, "file_sha256", side_effect=AssertionError("hashed")):
            self.assertEqual(self.item(self.sweep(), self.root / ".cache")["disposition"], "too_large")

    def test_protected_or_tracked_artifacts_are_not_approval_items(self):
        cache = self.root / ".cache"
        cache.mkdir()
        self.add_session("2026-08-01-closed", extra=(
            f"\n## Leftovers\n\n- `{cache}` `unique-never-delete` - keep\n"))
        self.assertEqual(self.item(self.sweep(), cache, "artifact")["disposition"], "kept")

    def test_symlink_component_blocks_deletion(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "unique.log").write_text("x")
        (self.root / "notes").symlink_to(outside)
        problem = lifecycle.deletion_problem(self.context(), self.root / "notes" / "unique.log")
        self.assertIn("symlink", problem)
        self.assertIn("registered checkout", lifecycle.deletion_problem(self.context(), self.base))
        self.assertIn("registered checkout", lifecycle.deletion_problem(self.context(), self.src / "inside"))


class ApproveTests(Workspace):
    def run_cli(self, *extra):
        return lifecycle.main(["sweep", "--manifest", str(self.manifest_path), "--local-host", "test", *extra])

    def latest_report(self):
        return lifecycle.read_json(sorted((self.root / lifecycle.RUNTIME).glob("sweep-*.json"))[-1])

    def test_matching_hash_deletes_and_mismatch_is_refused(self):
        cache = self.root / ".cache"
        cache.mkdir()
        (cache / "entry").write_text("x")
        self.assertEqual(self.run_cli(), 0)
        report = self.latest_report()
        self.assertEqual(self.item(report, cache)["disposition"], "needs_approval")
        self.assertEqual(self.run_cli("--apply", "--approve", "0" * 64), 50)
        self.assertEqual(self.run_cli("--approve", report["report_sha256"]), 50)
        self.assertTrue(cache.exists())
        self.assertEqual(self.run_cli("--apply", "--approve", report["report_sha256"]), 0)
        self.assertFalse(cache.exists())

    def test_tampered_report_is_refused(self):
        (self.root / ".cache").mkdir()
        self.assertEqual(self.run_cli(), 0)
        path = sorted((self.root / lifecycle.RUNTIME).glob("sweep-*.json"))[-1]
        report = json.loads(path.read_text())
        report["items"][0]["path"] = str(self.src)
        path.write_text(json.dumps(report))
        self.assertEqual(self.run_cli("--apply", "--approve", report["report_sha256"]), 50)
        self.assertTrue(self.src.exists())

    def test_same_size_same_mtime_content_change_is_skipped(self):
        cache = self.root / ".cache"
        cache.mkdir()
        (cache / "entry").write_text("aaaa")
        self.assertEqual(self.run_cli(), 0)
        approved = self.latest_report()
        stamp = (cache / "entry").stat()
        (cache / "entry").write_text("bbbb")
        os.utime(cache / "entry", ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        os.utime(cache, ns=(cache.stat().st_atime_ns, cache.stat().st_mtime_ns))
        results = self.apply(self.sweep(), approved)
        self.assertEqual([row["result"] for row in results], ["skipped"])
        self.assertTrue(cache.exists())

    def test_approval_is_revalidated_against_current_protection(self):
        bulk = self.base / "bulk-20260801"
        bulk.mkdir()
        (bulk / "out.root").write_text("data")
        session = self.add_session("2026-08-01-closed", extra=(
            f"\n## Leftovers\n\n- `{bulk}` `disposable-once-pushed` - outputs\n"))
        self.assertEqual(self.run_cli(), 0)
        approved = self.latest_report()
        result = session / "RESULT.md"
        result.write_text(result.read_text().replace("disposable-once-pushed", "unique-never-delete"))
        results = self.apply(self.sweep(), approved)
        self.assertEqual([row["result"] for row in results], ["skipped"])
        self.assertIn("now kept", results[0]["detail"])
        self.assertTrue(bulk.exists())

    def test_leftover_committed_after_approval_is_skipped(self):
        other = self.base / "other"
        git(self.base, "init", "-q", "-b", "main", "other")
        bulk = other / "bulk-20260801"
        bulk.mkdir()
        (bulk / "out.root").write_text("data")
        self.add_session("2026-08-01-closed", extra=(
            f"\n## Leftovers\n\n- `{bulk}` `disposable-once-pushed` - outputs\n"))
        self.assertEqual(self.run_cli(), 0)
        approved = self.latest_report()
        self.assertEqual(self.item(approved, bulk)["disposition"], "needs_approval")
        git(other, "add", "bulk-20260801")
        git(other, "commit", "-q", "-m", "keep outputs")
        results = self.apply(self.sweep(), approved)
        self.assertEqual([row["result"] for row in results], ["skipped"])
        self.assertIn("tracked by Git", results[0]["detail"])
        self.assertTrue(bulk.exists())

    def test_artifact_protected_after_approval_is_skipped(self):
        cache = self.root / ".cache"
        cache.mkdir()
        self.assertEqual(self.run_cli(), 0)
        approved = self.latest_report()
        self.add_session("2026-08-01-closed", extra=(
            f"\n## Leftovers\n\n- `{cache}` `unique-never-delete` - keep\n"))
        manifest = json.loads(self.manifest_path.read_text())
        item = self.item(approved, cache, "artifact")
        with self.assertRaises(lifecycle.Changed):
            lifecycle.delete_approved(lifecycle.make_context(manifest, self.root, "test"), item)
        results = self.apply(self.sweep(), approved)
        self.assertEqual([row["result"] for row in results], ["skipped"])
        self.assertTrue(cache.exists())

    def test_approved_parent_with_protected_child_is_refused(self):
        bulk = self.base / "bulk-20260803"
        (bulk / "keep").mkdir(parents=True)
        (bulk / "keep" / "unique.txt").write_text("data")
        self.add_session("2026-08-01-closed", extra=(
            f"\n## Leftovers\n\n- `{bulk}` `disposable-once-pushed` - outputs\n"))
        self.assertEqual(self.run_cli(), 0)
        approved = self.latest_report()
        self.assertEqual(self.item(approved, bulk)["disposition"], "needs_approval")
        self.add_session("2026-08-02-closed", extra=(
            f"\n## Leftovers\n\n- `{bulk / 'keep'}` `unique-never-delete` - only copy\n"))
        current = self.sweep()
        self.assertEqual(self.item(current, bulk)["disposition"], "kept")
        results = self.apply(current, approved)
        self.assertEqual([row["result"] for row in results], ["skipped"])
        with self.assertRaises(lifecycle.Changed):
            lifecycle.delete_approved(self.context(), self.item(approved, bulk))
        self.assertTrue((bulk / "keep" / "unique.txt").exists())

    def test_reports_are_never_overwritten(self):
        self.assertEqual(self.run_cli(), 0)
        self.assertEqual(self.run_cli(), 0)
        reports = sorted((self.root / lifecycle.RUNTIME).glob("sweep-*.json"))
        self.assertEqual(len(reports), 2)
        before = reports[0].read_text()
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.write_new(reports[0], "replacement")
        self.assertEqual(reports[0].read_text(), before)

    def test_publication_links_atomically_and_leaves_no_temporary(self):
        target = self.base / "report.json"
        lifecycle.write_new(target, "first")
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.write_new(target, "second")
        self.assertEqual(target.read_text(), "first")
        self.assertEqual(sorted(p.name for p in self.base.iterdir() if p.name.endswith(".tmp")), [])

    def test_malformed_report_does_not_block_approval(self):
        cache = self.root / ".cache"
        cache.mkdir()
        self.assertEqual(self.run_cli(), 0)
        approved = self.latest_report()
        (self.root / lifecycle.RUNTIME / "sweep-00000000T000000.000000Z-1-bad.json").write_text("{broken")
        manifest = json.loads(self.manifest_path.read_text())
        loaded = lifecycle.load_approved(self.root, approved["report_sha256"], "test", manifest)
        self.assertEqual(loaded["report_sha256"], approved["report_sha256"])
        with self.assertRaisesRegex(lifecycle.LifecycleError, "skipped malformed"):
            lifecycle.load_approved(self.root, "f" * 64, "test", manifest)
        self.assertEqual(self.run_cli("--apply", "--approve", approved["report_sha256"]), 0)
        self.assertFalse(cache.exists())

    def test_apply_holds_an_exclusive_lock(self):
        runtime = self.root / lifecycle.RUNTIME
        runtime.mkdir(parents=True)
        with (runtime / "sweep.lock").open("w") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.run_cli("--apply"), 50)
        self.assertEqual(self.run_cli("--apply"), 0)


class SessionTests(Workspace):
    def test_eligibility(self):
        cases = {
            "2026-08-01-done": ({}, "settle"),
            "2026-08-02-active": ({"status": "in progress"}, "kept"),
            "2026-08-03-review": ({"review": "pending"}, "kept"),
            "2026-08-04-awaiting": ({"status": "complete; physics decision pending"}, "kept"),
        }
        for name, (options, _) in cases.items():
            self.add_session(name, **options)
        (self.add_session("2026-08-05-untracked") / "notes.txt").write_text("unique")
        (self.add_session("2026-08-06-ignored") / "report.pdf").write_text("unique")
        flagged = self.add_session("2026-08-07-flagged")
        git(self.root, "update-index", "--assume-unchanged", str(flagged / "STATE.md"))
        (flagged / "STATE.md").write_text("- Status: `complete`\nlocal edit\n")
        self.add_session("2026-08-08-dirty")
        (self.root / "sessions/2026-08-08-dirty/STATE.md").write_text("- Status: `complete`\nmore\n")
        with later():
            report = self.sweep(settle=True)
        self.assertFalse([row for row in self.sweep()["items"] if row["kind"] == "session"])
        for name, (_, expected) in cases.items():
            with self.subTest(name=name):
                self.assertEqual(self.item(report, self.root / "sessions" / name)["disposition"], expected)
        reasons = {
            "2026-08-05-untracked": "1 untracked files",
            "2026-08-06-ignored": "rebuildable allowlist",
            "2026-08-07-flagged": "assume-unchanged",
            "2026-08-08-dirty": "uncommitted tracked changes",
        }
        for name, reason in reasons.items():
            with self.subTest(name=name):
                item = self.item(report, self.root / "sessions" / name)
                self.assertEqual(item["disposition"], "needs_owner")
                self.assertIn(reason, item["reason"])
        self.assertEqual(self.item(self.sweep(settle=True), self.root / "sessions/2026-08-01-done")
                         ["disposition"], "kept")

    def test_settle_stages_git_rm_and_appends_archive_line(self):
        path = self.add_session("2026-08-01-done")
        (path / "__pycache__").mkdir()
        (path / "__pycache__" / "x.pyc").write_text("x")
        commit = git(self.root, "log", "-1", "--format=%H")
        with later():
            report = self.sweep(settle=True)
            results = self.apply(report)
        self.assertEqual([row["result"] for row in results], ["done"], results)
        self.assertIn("folder kept with rebuildable entries __pycache__", results[0]["detail"])
        self.assertEqual(git(self.root, "ls-files", "sessions/2026-08-01-done"), "")
        self.assertIn("D  sessions/2026-08-01-done/RESULT.md", git(self.root, "status", "--porcelain"))
        row = (self.root / "sessions/ARCHIVE.md").read_text().splitlines()[-1]
        self.assertIn("| 2026-08-01-done | 2026-08-01..", row)
        self.assertIn(commit, row)
        self.assertIn("The study finished / cleanly.", row)
        git(self.root, "checkout", commit, "--", "sessions/2026-08-01-done")
        self.assertTrue((path / "RESULT.md").exists())

    def test_permanent_leftover_protections_block_settling(self):
        kept = self.base / "kept-20260801"
        kept.mkdir()
        self.add_session("2026-08-01-unique", extra=(
            f"\n## Leftovers\n\n- `{self.base / 'gone'}` `unique-never-delete` - removed later\n"))
        self.add_session("2026-08-02-review", extra=(
            f"\n## Leftovers\n\n- `{kept}` `keep-until-review` - outputs\n"))
        self.add_session("2026-08-03-review-gone", extra=(
            f"\n## Leftovers\n\n- `{self.base / 'gone'}` `keep-until-review` - outputs\n"))
        with later():
            report = self.sweep(settle=True)
        for name in ("2026-08-01-unique", "2026-08-02-review"):
            with self.subTest(name=name):
                item = self.item(report, self.root / "sessions" / name)
                self.assertEqual(item["disposition"], "kept")
                self.assertIn("settling would drop that protection", item["reason"])
        self.assertEqual(self.item(report, self.root / "sessions/2026-08-03-review-gone")["disposition"],
                         "settle")

    def test_settle_requires_flag_in_report(self):
        self.add_session("2026-08-01-done")
        with later():
            report = self.sweep(settle=True)
        report["settle_sessions"] = False
        self.assertEqual(self.apply(report), [])

    def test_outcome_skips_headings(self):
        self.assertEqual(lifecycle.outcome_line("# Result\n\nShort | answer.\n\nMore."), "Short / answer.")

    def test_status_parsing(self):
        self.assertEqual(lifecycle.session_status("Old note. Status: complete\n- Status: `in progress`\n"),
                         "in progress")
        self.assertEqual(lifecycle.session_status("Status: complete\n"), "complete")
        self.assertEqual(lifecycle.session_status("Updated 2026-09-07. Status: complete\n"), "")
        self.assertTrue(lifecycle.is_closed("superseded operationally"))
        self.assertFalse(lifecycle.is_closed("local installation complete"))
        self.assertTrue(lifecycle.live_owner('{"session_status": "in_progress"}', ""))
        self.assertTrue(lifecycle.live_owner("", "- Jobs or delegated monitors: Slurm 123\n"))
        self.assertFalse(lifecycle.live_owner("", "- Jobs or delegated monitors: `none`\n"))


if __name__ == "__main__":
    unittest.main()
