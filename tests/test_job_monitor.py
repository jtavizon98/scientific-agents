import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "skills" / "long-job-continuation" / "scripts" / "job_monitor.py"
SPEC = importlib.util.spec_from_file_location("job_monitor", MODULE_PATH)
monitor = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(monitor)


def panda_spec(**expected_overrides):
    expected = {
        "owner": "Test User",
        "files": 10,
        "events": 1000,
        "bytes": 5000,
        "max_attempt": 1,
        "payload_progression_limit": 2,
        "payload_hard_ceiling": 10,
    }
    expected.update(expected_overrides)
    return {
        "schema_version": 1,
        "name": "test-panda",
        "backend": "panda",
        "target": {"task_id": 123},
        "expected": expected,
        "failure_policy": "record",
        "goal": "terminal",
        "poll": {"interval_seconds": 30, "lease_seconds": 30},
    }


def panda_task(status="running"):
    return {
        "task": {
            "jeditaskid": 123,
            "username": "Test User",
            "status": status,
            "superstatus": status,
            "attemptnr": 0,
            "dsinfo": {"nfiles": 10, "neventsTot": 1000},
        }
    }


def panda_job(status="running", transformation="runGen-00-00-02", pandaid=1, **extra):
    row = {
        "pandaid": pandaid,
        "jobstatus": status,
        "transformation": transformation,
        "attemptnr": 1,
        "computingsite": "SITE",
        "ninputdatafiles": 5,
        "inputfilebytes": 2500,
        "nevents": 500,
    }
    row.update(extra)
    return row


def jobs_payload(jobs, reported=None):
    if reported is None:
        reported = len(jobs)
    return {
        "jobs": jobs,
        "errsByCount": [],
        "selectionsummary": [
            {"field": "jobstatus", "list": [{"kname": "all", "kvalue": reported}]}
        ],
    }


class PandaTests(unittest.TestCase):
    def test_merging_is_not_failure(self):
        jobs = [panda_job("merging"), panda_job("finished", pandaid=2)]
        result = monitor.normalize_panda(panda_task(), jobs_payload(jobs), panda_spec())
        self.assertEqual(result["outcome"], "active")
        self.assertEqual(result["observed"]["failures"], [])
        self.assertEqual(result["observed"]["payload_count"], 2)

    def test_terminal_failure_is_recorded(self):
        jobs = [panda_job("failed", piloterrorcode=42, piloterrordiag="network")]
        result = monitor.normalize_panda(
            panda_task("done"), jobs_payload(jobs), panda_spec()
        )
        self.assertEqual(result["outcome"], "terminal_with_failures")
        self.assertEqual(result["observed"]["failures"][0]["piloterrorcode"], 42)

    def test_scope_drift_fails_closed(self):
        task = panda_task()
        task["task"]["dsinfo"]["nfiles"] = 11
        result = monitor.normalize_panda(task, jobs_payload([]), panda_spec())
        self.assertEqual(result["outcome"], "invariant_violation")
        self.assertTrue(any("file-count drift" in value for value in result["invariants"]))

    def test_retry_fails_closed(self):
        result = monitor.normalize_panda(
            panda_task(), jobs_payload([panda_job(attemptnr=2)]), panda_spec()
        )
        self.assertEqual(result["outcome"], "invariant_violation")
        self.assertTrue(any("attempt" in value for value in result["invariants"]))

    def test_truncated_response_fails_closed(self):
        result = monitor.normalize_panda(
            panda_task(), jobs_payload([panda_job()], reported=20), panda_spec()
        )
        self.assertEqual(result["outcome"], "invariant_violation")
        self.assertTrue(result["observed"]["jobs_truncated"])

    def test_full_payload_byte_drift_fails_closed(self):
        jobs = [panda_job(inputfilebytes=2400), panda_job(pandaid=2)]
        result = monitor.normalize_panda(panda_task(), jobs_payload(jobs), panda_spec())
        self.assertEqual(result["outcome"], "invariant_violation")
        self.assertTrue(any("byte-count drift" in value for value in result["invariants"]))

    def test_kind_classification(self):
        self.assertEqual(monitor.panda_job_kind(panda_job(transformation="buildGen-x")), "build")
        self.assertEqual(monitor.panda_job_kind(panda_job(transformation="runMerge-x")), "merge")
        self.assertEqual(monitor.panda_job_kind(panda_job()), "payload")


class SlurmTests(unittest.TestCase):
    def spec(self, indices=(0, 1)):
        return {
            "schema_version": 1,
            "name": "test-slurm",
            "backend": "slurm",
            "target": {"job_id": "99", "ssh_alias": "cluster-login"},
            "expected": {"array_indices": list(indices)},
            "poll": {"interval_seconds": 30, "lease_seconds": 30},
        }

    def test_completed_array_ignores_steps(self):
        output = "\n".join(
            [
                "__SACCT__",
                "99_0|99_0|COMPLETED|0:0|10|1M|1|1G|n1",
                "99_0.batch|99_0.batch|COMPLETED|0:0|10|1M|1|1G|n1",
                "99_1|99_1|COMPLETED|0:0|11|2M|1|1G|n2",
                "__SQUEUE__",
            ]
        )
        result = monitor.parse_slurm_output(output, self.spec())
        self.assertEqual(result["outcome"], "terminal_clean")
        self.assertEqual(set(result["observed"]["tasks"]), {"0", "1"})

    def test_mixed_terminal_array_reports_failure(self):
        output = "\n".join(
            [
                "__SACCT__",
                "99_0|99_0|COMPLETED|0:0|10|1M|1|1G|n1",
                "99_1|99_1|FAILED|1:0|11|2M|1|1G|n2",
                "__SQUEUE__",
            ]
        )
        result = monitor.parse_slurm_output(output, self.spec())
        self.assertEqual(result["outcome"], "terminal_with_failures")
        self.assertIn("1", result["observed"]["failures"])

    def test_missing_terminal_index_is_invariant(self):
        output = "\n".join(
            ["__SACCT__", "99_0|99_0|COMPLETED|0:0|10|1M|1|1G|n1", "__SQUEUE__"]
        )
        result = monitor.parse_slurm_output(output, self.spec())
        self.assertEqual(result["outcome"], "invariant_violation")

    def test_active_squeue_row(self):
        output = "\n".join(
            ["__SACCT__", "__SQUEUE__", "99_0|RUNNING|n1", "99_1|PENDING|Priority"]
        )
        result = monitor.parse_slurm_output(output, self.spec())
        self.assertEqual(result["outcome"], "active")
        self.assertEqual(result["observed"]["states"]["RUNNING"], 1)


class DependencyTests(unittest.TestCase):
    def test_complete_and_released_dependencies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            complete = root / "complete.json"
            released = root / "released.json"
            complete.write_text(
                json.dumps({"schema_version": 1, "session_status": "complete", "updated": "now"})
            )
            released.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "session_status": "paused",
                        "updated": "now",
                        "releases": {"report": {"status": "released"}},
                    }
                )
            )
            spec = {
                "dependencies": [
                    {
                        "name": "complete",
                        "marker": "complete.json",
                        "require": {"session_status": "complete"},
                    },
                    {
                        "name": "released",
                        "marker": "released.json",
                        "require": {"release": "report"},
                    },
                ]
            }
            result = monitor.normalize_dependencies(spec, root)
            self.assertEqual(result["outcome"], "ready")

    def test_missing_dependency_is_pending(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            spec = {
                "dependencies": [
                    {
                        "name": "missing",
                        "marker": "missing.json",
                        "require": {"session_status": "complete"},
                    }
                ]
            }
            result = monitor.normalize_dependencies(spec, root)
            self.assertEqual(result["outcome"], "active")


class StateTests(unittest.TestCase):
    def test_atomic_json_and_jsonl(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "latest.json"
            log = root / "snapshots.jsonl"
            monitor.atomic_json(target, {"value": 1})
            monitor.append_jsonl(log, {"value": 1})
            self.assertEqual(json.loads(target.read_text()), {"value": 1})
            self.assertEqual(json.loads(log.read_text().strip()), {"value": 1})

    def test_state_paths_are_isolated_by_output_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = root / "session" / "monitor-spec.json"
            paths = monitor.state_paths(spec_path, {"output_dir": "monitor/task-123"})
            self.assertEqual(paths["latest"], root / "session/monitor/task-123/latest.json")

    def test_recorded_snapshot_has_expiry(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = {
                "snapshots": Path(temporary) / "snapshots.jsonl",
                "latest": Path(temporary) / "latest.json",
            }
            spec = {
                "poll": {"snapshot_ttl_seconds": 60},
                "name": "expiry-test",
            }
            monitor.record_snapshot(paths, spec, {"outcome": "active"})
            latest = json.loads(paths["latest"].read_text())
            self.assertIn("expires_at", latest)


if __name__ == "__main__":
    unittest.main()
