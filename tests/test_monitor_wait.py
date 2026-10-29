import datetime as dt
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SCRIPTS = Path(__file__).parents[1] / "skills" / "long-job-continuation" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("monitor_wait", SCRIPTS / "monitor_wait.py")
wait = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(wait)


class WaitFixture:
    def __init__(self, root: Path, count: int = 1, notification=None):
        self.root = root
        (root / ".git").mkdir()
        self.session = root / "sessions" / "test"
        self.session.mkdir(parents=True)
        self.specs = []
        for index in range(count):
            marker = self.session / f"marker-{index}.json"
            marker.write_text(json.dumps({"schema_version": 1, "session_status": "in_progress"}))
            spec_path = self.session / f"monitor-{index}.json"
            spec_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "name": f"test-{index}",
                        "backend": "dependencies",
                        "output_dir": f"monitor/task-{index}",
                        "dependencies": [
                            {
                                "name": f"marker-{index}",
                                "marker": str(marker.relative_to(root)),
                                "require": {"session_status": "complete"},
                            }
                        ],
                        "poll": {
                            "interval_seconds": 30,
                            "lease_seconds": 300,
                            "snapshot_ttl_seconds": 60,
                        },
                    }
                )
            )
            self.specs.append(spec_path)
        self.contract_path = self.session / "wait-contract.json"
        self.contract_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "owner_session_id": "caller",
                    "policy": "fail_fast_all",
                    "monitor_specs": [str(path.relative_to(root)) for path in self.specs],
                    "wait": {
                        "check_interval_seconds": 1,
                        "startup_grace_seconds": 2,
                        "timeout_seconds": 10,
                    },
                    "post_handback": {
                        "authorization": "read_only",
                        "completion_contract": "return synthetic evidence",
                    },
                    "notification": notification or {"authorized": False},
                }
            )
        )
        self.contract = wait.load_contract(self.contract_path, "ses-test")
        self.event_id = "12345678-test"
        self.paths = wait.wait_paths(self.contract, self.event_id)

    def register(self):
        return wait.register_wait(self.contract, self.event_id, "ses-test", "msg-test", os.getpid())

    def runtime_paths(self, index=0):
        spec = wait.monitor.load_spec(self.specs[index])
        return wait.monitor.state_paths(self.specs[index], spec)

    def write_result(self, index=0, outcome="terminal_clean"):
        row = self.contract["specs"][index]
        value = {
            "schema_version": 1,
            "outcome": outcome,
            "terminal": True,
            "spec_sha256": row["sha256"],
        }
        wait.monitor.atomic_json(self.runtime_paths(index)["result"], value)

    def write_latest(self, index=0, outcome="active", seconds=60):
        row = self.contract["specs"][index]
        expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds)
        value = {
            "schema_version": 1,
            "outcome": outcome,
            "terminal": False,
            "expires_at": expires.isoformat(),
            "spec_sha256": row["sha256"],
        }
        wait.monitor.atomic_json(self.runtime_paths(index)["latest"], value)


class WaitRegistrationTests(unittest.TestCase):
    def test_registration_is_written_before_result_inspection(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.write_result()
            fixture.register()
            self.assertTrue(fixture.paths["registration"].exists())
            result = wait.evaluate_group(fixture.contract, 0, active=lambda _unit: False)
            self.assertEqual(result["status"], "success")

    def test_equivalent_registration_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            first = fixture.register()
            second = fixture.register()
            self.assertEqual(first, second)
            state = json.loads(fixture.paths["state"].read_text())
            self.assertEqual([row["event"] for row in state["history"]], ["registered"])

    def test_registration_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            with self.assertRaises(wait.WaitError):
                wait.register_wait(
                    fixture.contract, fixture.event_id, "ses-test", "different-message", os.getpid()
                )

    def test_equivalent_registration_repairs_missing_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            fixture.paths["state"].unlink()
            fixture.register()
            state = json.loads(fixture.paths["state"].read_text())
            self.assertEqual(state["observation"], "registered")
            self.assertEqual(state["history"][0]["event"], "registration_repaired")

    def test_detached_commands_reject_contract_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            value = json.loads(fixture.contract_path.read_text())
            value["wait"]["timeout_seconds"] = 20
            fixture.contract_path.write_text(json.dumps(value))
            drifted = wait.load_contract(fixture.contract_path)
            with self.assertRaises(wait.WaitError):
                wait.validate_registration(drifted, fixture.paths)

    def test_contract_rejects_spec_outside_project(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            root = Path(temporary)
            (root / ".git").mkdir()
            external = Path(outside) / "spec.json"
            external.write_text("{}")
            contract = root / "contract.json"
            contract.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "monitor_specs": [str(external)],
                    }
                )
            )
            with self.assertRaises(wait.WaitError):
                wait.load_contract(contract, "ses-test")

    def test_contract_requires_explicit_post_handback_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            value = json.loads(fixture.contract_path.read_text())
            del value["post_handback"]
            fixture.contract_path.write_text(json.dumps(value))
            with self.assertRaises(wait.WaitError):
                wait.load_contract(fixture.contract_path, "ses-test")

    def test_contract_must_live_directly_in_owning_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            nested = fixture.session / "nested"
            nested.mkdir()
            path = nested / "wait-contract.json"
            path.write_text(fixture.contract_path.read_text())
            with self.assertRaises(wait.WaitError):
                wait.load_contract(path, "ses-test")


class WaitEvaluationTests(unittest.TestCase):
    def test_group_success_requires_all_monitors(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary), count=2)
            fixture.write_result(0)
            fixture.write_result(1, "ready")
            result = wait.evaluate_group(fixture.contract, 0, active=lambda _unit: False)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["outcome"], "ready")

    def test_group_fails_fast(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary), count=2)
            fixture.write_result(0, "terminal_with_failures")
            fixture.write_latest(1)
            result = wait.evaluate_group(fixture.contract, 0, active=lambda _unit: False)
            self.assertEqual(result["status"], "failure")
            self.assertEqual(result["outcome"], "terminal_with_failures")

    def test_absent_and_stale_monitors_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            absent = wait.evaluate_group(fixture.contract, 3, active=lambda _unit: False)
            self.assertEqual(absent["outcome"], "monitor_absent")
            fixture.write_latest(seconds=-1)
            stale = wait.evaluate_group(fixture.contract, 3, active=lambda _unit: False)
            self.assertEqual(stale["outcome"], "stale")

    def test_spec_hash_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.write_result()
            path = fixture.runtime_paths()["result"]
            value = json.loads(path.read_text())
            value["spec_sha256"] = "wrong"
            path.write_text(json.dumps(value))
            result = wait.evaluate_group(fixture.contract, 0, active=lambda _unit: False)
            self.assertEqual(result["outcome"], "spec_drift")


class WaitStateTests(unittest.TestCase):
    def test_state_transitions_are_idempotent_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            wait.transition(fixture.paths, observation="waiting")
            wait.transition(fixture.paths, observation="waiting")
            with self.assertRaises(wait.WaitError):
                wait.transition(fixture.paths, observation="registered")

    def test_existing_result_repairs_incomplete_state_transition(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            wait.monitor.atomic_json(fixture.paths["result"], {"outcome": "ready"})
            wait.complete_wait(fixture.paths, fixture.contract, {"status": "success", "outcome": "ready"})
            state = json.loads(fixture.paths["state"].read_text())
            self.assertEqual(state["observation"], "completed")

    def test_completed_undelivered_wait_resumes_without_polling(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            result = wait.complete_wait(
                fixture.paths,
                fixture.contract,
                {"status": "success", "outcome": "ready", "monitors": []},
            )
            args = SimpleNamespace(
                contract=fixture.contract_path,
                session_id="ses-test",
                harness="opencode",
                message_id="msg-test",
                owner_pid=os.getpid(),
                event_id=fixture.event_id,
                timeout_seconds=None,
                no_start=False,
                no_notifier=False,
            )
            with mock.patch.object(wait, "ensure_monitors") as ensure, mock.patch.object(
                wait, "start_notifier"
            ) as notifier, mock.patch("builtins.print"):
                code = wait.command_wait(args)
            self.assertEqual(code, wait.monitor.result_exit(result["outcome"]))
            ensure.assert_not_called()
            notifier.assert_not_called()
            state = json.loads(fixture.paths["state"].read_text())
            self.assertEqual(state["delivery"], "delivered_to_tool")

    def test_orphan_wins_delivery_race_without_losing_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            wait.complete_wait(
                fixture.paths,
                fixture.contract,
                {"status": "success", "outcome": "ready", "monitors": []},
            )
            wait.transition(fixture.paths, delivery="orphaned")
            state = wait.deliver_to_tool(fixture.paths)
            self.assertEqual(state["delivery"], "orphaned")
            self.assertTrue(fixture.paths["result"].exists())

    def test_timeout_override_cannot_exceed_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            args = SimpleNamespace(
                contract=fixture.contract_path,
                session_id="ses-test",
                harness="opencode",
                message_id="msg-test",
                owner_pid=os.getpid(),
                event_id=fixture.event_id,
                timeout_seconds=11,
                no_start=True,
                no_notifier=True,
            )
            with self.assertRaises(wait.WaitError):
                wait.command_wait(args)

    def wait_args(self, fixture, *extra):
        return wait.build_parser().parse_args(
            [
                "wait", "--contract", str(fixture.contract_path), "--session-id", "ses-test",
                "--owner-pid", str(os.getpid()), "--event-id", fixture.event_id,
                "--timeout-seconds", "11", "--no-start", "--no-notifier", *extra,
            ]
        )

    def test_claude_owner_without_message_id_is_recorded(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            args = self.wait_args(fixture, "--harness", "claude")
            with self.assertRaises(wait.WaitError):  # timeout rejected after registration
                wait.command_wait(args)
            registration = json.loads(fixture.paths["registration"].read_text())
            self.assertEqual(registration["harness"], "claude")
            self.assertIsNone(registration["message_id"])

    def test_legacy_registration_without_harness_is_opencode(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            path = fixture.paths["registration"]
            legacy = json.loads(path.read_text())
            del legacy["harness"]
            path.write_text(json.dumps(legacy))
            self.assertEqual(fixture.register(), legacy)
            with self.assertRaisesRegex(wait.WaitError, "drift"):
                wait.register_wait(
                    fixture.contract, fixture.event_id, "ses-test", "msg-test",
                    os.getpid(), "claude",
                )

    def test_opencode_requires_message_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            with self.assertRaisesRegex(wait.WaitError, "message-id"):
                wait.command_wait(self.wait_args(fixture))
            self.assertFalse(fixture.paths["registration"].exists())

    def test_interrupted_wait_becomes_orphaned(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            fixture.write_latest()
            with self.assertRaises(wait.WaitInterrupted):
                wait.wait_loop(
                    fixture.contract,
                    fixture.paths,
                    timeout_seconds=5,
                    interrupt=lambda: True,
                    active=lambda _unit: False,
                )
            state = json.loads(fixture.paths["state"].read_text())
            self.assertEqual(state["delivery"], "orphaned")

    def test_active_wait_reaches_success_without_model_polling(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            fixture.write_latest()
            ticks = [0.0]

            def clock():
                return ticks[0]

            def sleeper(seconds):
                ticks[0] += seconds
                fixture.write_result()

            result = wait.wait_loop(
                fixture.contract,
                fixture.paths,
                timeout_seconds=5,
                active=lambda _unit: False,
                sleeper=sleeper,
                clock=clock,
            )
            self.assertEqual(result["outcome"], "ready")
            self.assertEqual(ticks[0], 1)

    def test_timeout_is_a_durable_handback(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            fixture.write_latest()
            ticks = [0.0]

            def clock():
                return ticks[0]

            def sleeper(seconds):
                ticks[0] += seconds

            result = wait.wait_loop(
                fixture.contract,
                fixture.paths,
                timeout_seconds=2,
                active=lambda _unit: False,
                sleeper=sleeper,
                clock=clock,
            )
            self.assertEqual(result["outcome"], "wait_timeout")
            self.assertTrue(fixture.paths["result"].exists())


class NotificationTests(unittest.TestCase):
    def test_authorized_notification_is_attempted_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "sent.txt"
            sender = root / "sender.py"
            sender.write_text(
                "import os, pathlib, sys\n"
                "pathlib.Path(sys.argv[1]).open('a').write(os.environ['JOB_WAIT_EVENT_ID'] + '\\n')\n"
            )
            fixture = WaitFixture(
                root,
                notification={
                    "authorized": True,
                    "destination": "test@example.invalid",
                    "command": [sys.executable, str(sender), str(output)],
                },
            )
            fixture.register()
            wait.transition(fixture.paths, delivery="orphaned")
            first = wait.notify_once(fixture.contract, fixture.paths)
            second = wait.notify_once(fixture.contract, fixture.paths)
            self.assertEqual(first["status"], "sent")
            self.assertEqual(second["status"], "sent")
            self.assertEqual(output.read_text().splitlines(), [fixture.event_id])

    def test_unauthorized_notification_remains_held(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            wait.transition(fixture.paths, delivery="orphaned")
            result = wait.notify_once(fixture.contract, fixture.paths)
            state = json.loads(fixture.paths["state"].read_text())
            self.assertEqual(result["status"], "held")
            self.assertEqual(state["delivery"], "orphaned")

    def test_uncertain_notification_must_be_recorded_before_ack(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            wait.transition(fixture.paths, delivery="orphaned")
            wait.transition(fixture.paths, delivery="notifying")
            with self.assertRaises(wait.WaitError):
                wait.transition(fixture.paths, delivery="acknowledged")
            wait.transition(fixture.paths, delivery="notification_unknown")
            state = wait.transition(fixture.paths, delivery="acknowledged")
            self.assertEqual(state["delivery"], "acknowledged")

    def test_notifier_unit_names_include_full_event_identity(self):
        prefix = "a" * 40
        self.assertNotEqual(wait.notifier_unit(prefix + "1"), wait.notifier_unit(prefix + "2"))

    def test_owner_identity_rejects_reused_pid(self):
        identity = wait.process_identity(os.getpid())
        self.assertIsNotNone(identity)
        self.assertTrue(wait.owner_alive(os.getpid(), identity))
        self.assertFalse(wait.owner_alive(os.getpid(), "different-start-time"))

    def test_ambiguous_notification_attempt_is_not_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(
                Path(temporary),
                notification={
                    "authorized": True,
                    "destination": "test@example.invalid",
                    "command": ["synthetic-sender"],
                },
            )
            fixture.register()
            wait.transition(fixture.paths, delivery="orphaned")
            with mock.patch.object(
                wait.subprocess,
                "run",
                side_effect=wait.subprocess.TimeoutExpired("synthetic-sender", 120),
            ):
                with self.assertRaises(wait.subprocess.TimeoutExpired):
                    wait.notify_once(fixture.contract, fixture.paths)
            state = json.loads(fixture.paths["state"].read_text())
            self.assertEqual(state["delivery"], "notifying")
            with mock.patch.object(wait.subprocess, "run") as sender:
                result = wait.notify_once(fixture.contract, fixture.paths)
            sender.assert_not_called()
            self.assertEqual(result["status"], "claimed")

    def test_active_notifier_without_matching_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = WaitFixture(Path(temporary))
            fixture.register()
            with mock.patch.object(wait, "systemd_active", return_value=True):
                with self.assertRaises(wait.WaitError):
                    wait.start_notifier(fixture.contract, fixture.event_id, os.getpid())


if __name__ == "__main__":
    unittest.main()
