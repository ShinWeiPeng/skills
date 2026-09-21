"""Contract regressions for SPEC-derived definitions and bounded shared edits."""

import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_spec_governance import SPEC_CONTRACT as contract, confirmed_spec


class ConsolidationTests(unittest.TestCase):
    def test_projection_rebuilds_added_removed_and_changed_criteria(self):
        source = confirmed_spec()
        line = "| AC-001 | REQ-001 | A fourth attempt is never made. | `test_retry_limit` | pending |"
        self.assertIn(line, source)

        def version(count):
            rows = "\n".join(
                line.replace("AC-001", f"AC-{n:03d}") for n in range(1, count + 1)
            )
            return source.replace(line, rows)

        five = contract.generated_acceptance(version(5))
        eight = contract.generated_acceptance(version(8))
        self.assertEqual(5, len(five["acceptance"]))
        self.assertEqual(8, len(eight["acceptance"]))
        self.assertNotIn(
            "AC-006", contract.generated_acceptance(version(5))["acceptance"]
        )
        changed = contract.generated_acceptance(
            version(8).replace("fourth attempt", "fifth attempt")
        )
        self.assertNotEqual(eight["source"], changed["source"])
        self.assertEqual(
            "`test_retry_limit`",
            eight["acceptance"]["AC-001"]["definition"]["validation method"],
        )
        self.assertNotIn("evidence", eight["acceptance"]["AC-001"]["definition"])

    def test_generation_does_not_write_or_infer_missing_selectors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "specs").mkdir()
            spec = "specs/SPEC-0001-payment-retry.md"
            (root / spec).write_text(confirmed_spec(), encoding="utf-8")
            result = contract.acceptance_generation_plan(root, spec)
            self.assertEqual("PASS", result["verdict"], result)
            self.assertEqual(["AC-001"], result["unresolved_selectors"])
            self.assertFalse(result["acceptance_complete"])
            self.assertEqual("BLOCKED", result["planning_verdict"])
            self.assertFalse((root / result["patch"]["path"]).exists())
            target = root / result["patch"]["path"]
            target.parent.mkdir()
            target.write_text(result["patch"]["content"], encoding="utf-8")
            self.assertIsNone(contract.acceptance_generation_plan(root, spec)["patch"])
            evidence = root / "artifacts" / "evidence.json"
            evidence.parent.mkdir()
            evidence.write_bytes(b"original evidence")
            target.write_text("{}", encoding="utf-8")
            rebuilt = contract.acceptance_generation_plan(root, spec)
            self.assertEqual(result["patch"]["content"], rebuilt["patch"]["content"])
            self.assertEqual(b"original evidence", evidence.read_bytes())

    def test_explicit_selectors_come_from_spec_and_unknown_ac_is_rejected(self):
        mapping = {
            "AC-001": {
                "evidence_claims": ["host-semantics"],
                "rationale": "Host retry test.",
            }
        }
        source = (
            confirmed_spec()
            + "\n## Acceptance Mapping\n\n```json\n"
            + json.dumps(mapping)
            + "\n```\n"
        )
        projected = contract.generated_acceptance(source)
        self.assertEqual(
            ["host-semantics"], projected["acceptance"]["AC-001"]["evidence_claims"]
        )
        with self.assertRaises(ValueError):
            contract.generated_acceptance(source.replace('"AC-001":', '"AC-999":'))

    def test_lock_timeout_is_bounded_and_preserves_unsaved_edits(self):
        self.assertEqual(
            30.0,
            inspect.signature(contract.project_state_lock)
            .parameters["timeout"]
            .default,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(
                contract, "project_state_lock", side_effect=TimeoutError("busy")
            ):
                result = contract.reconcile_working_bundle(
                    root,
                    "working-fixture",
                    "pending edits",
                    {},
                    expected_revision=1,
                    expected_hash="old",
                )
            self.assertEqual("BLOCKED", result["verdict"])
            self.assertTrue(result["pending_edits_preserved"])
            self.assertFalse((root / "specs").exists())

    def test_shared_lock_blocks_other_process_then_releases(self):
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as directory:
            child = "import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from spec_contract import project_state_lock;\nwith project_state_lock(Path(sys.argv[2]),'shared'):\n print('ready',flush=True); sys.stdin.read(1)"
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    child,
                    str(Path(contract.__file__).parent),
                    directory,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertEqual("ready", process.stdout.readline().strip())
                with self.assertRaises(TimeoutError):
                    with contract.project_state_lock(
                        Path(directory), "shared", timeout=0.05
                    ):
                        self.fail("concurrent process acquired exclusive lock")
                process.communicate("x", timeout=5)
                with contract.project_state_lock(
                    Path(directory), "shared", timeout=0.05
                ):
                    pass
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate()

    def test_stale_nonconflicting_edits_merge_and_conflicts_preserve_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref = contract.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(status="working"),
                task_ref="merge-task",
            )["working_spec"]
            path = root / ref["snapshot_path"]
            baseline = path.read_text(encoding="utf-8")
            first = contract.reconcile_working_bundle(
                root,
                ref["working_id"],
                baseline.replace(
                    "Retries are inconsistent.", "Retries need a consistent policy."
                ),
                {},
                expected_revision=ref["revision"],
                expected_hash=ref["snapshot_hash"],
            )
            self.assertEqual("PASS", first["verdict"], first)
            second = contract.reconcile_working_bundle(
                root,
                ref["working_id"],
                baseline.replace(
                    "Use one bounded retry policy.",
                    "Use the existing bounded retry policy.",
                ),
                {},
                expected_revision=ref["revision"],
                expected_hash=ref["snapshot_hash"],
                base_snapshot=baseline,
            )
            self.assertEqual("PASS", second["verdict"], second)
            self.assertIn(
                "Retries need a consistent policy.", path.read_text(encoding="utf-8")
            )
            self.assertIn(
                "Use the existing bounded retry policy.",
                path.read_text(encoding="utf-8"),
            )
            before = path.read_bytes()
            conflict = contract.reconcile_working_bundle(
                root,
                ref["working_id"],
                baseline.replace("Retries are inconsistent.", "Conflicting purpose."),
                {},
                expected_revision=ref["revision"],
                expected_hash=ref["snapshot_hash"],
                base_snapshot=baseline,
            )
            self.assertEqual("BLOCKED", conflict["verdict"])
            self.assertEqual(before, path.read_bytes())

    def test_new_questions_require_three_but_legacy_two_remains_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref = contract.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(status="working"),
                task_ref="question-task",
            )["working_spec"]
            result = contract.record_question(
                root,
                ref["working_id"],
                "Q-001",
                "Which strategy?",
                ["bounded", "unbounded"],
                expected_revision=ref["revision"],
                expected_hash=ref["snapshot_hash"],
            )
            self.assertEqual("BLOCKED", result["verdict"])
            result = contract.record_question(
                root,
                ref["working_id"],
                "Q-001",
                "Which strategy?",
                ["bounded", "unbounded", "no retry"],
                expected_revision=ref["revision"],
                expected_hash=ref["snapshot_hash"],
            )
            self.assertEqual("BLOCKED", result["verdict"], result)
            self.assertEqual(["Q-001@2"], result["open_decisions"])
            current = (root / result["working_spec"]["snapshot_path"]).read_text(
                encoding="utf-8"
            )
            self.assertEqual(3, len(contract.pending_decision(current)["options"]))
            legacy = contract._replace_pending_decision(
                confirmed_spec(status="working"),
                {
                    "id": "Q-001",
                    "version": 1,
                    "question": "Which strategy?",
                    "options": ["bounded", "unbounded"],
                },
            )
            self.assertEqual(2, len(contract.pending_decision(legacy)["options"]))

    def test_reopen_failure_never_restores_over_concurrent_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref = contract.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(status="working"),
                task_ref="reopen-task",
            )["working_spec"]
            ref = contract.materialize_working_bundle(
                root,
                ref["working_id"],
                expected_revision=ref["revision"],
                expected_hash=ref["snapshot_hash"],
            )["working_spec"]
            path = root / ref["snapshot_path"]
            original = contract.start_working_bundle
            concurrent = []

            def changed(*args, **kwargs):
                contract._append_journal_event(
                    path,
                    event_type="discussion",
                    working_id=ref["working_id"],
                    revision=ref["revision"],
                    previous_snapshot_hash=ref["snapshot_hash"],
                    snapshot_hash=ref["snapshot_hash"],
                    continuity="continuous",
                    verdict="PASS",
                    delta={"discussion": {"summary": "Concurrent saved observation"}},
                )
                concurrent.append(path.read_bytes())
                return original(*args, **kwargs)

            with patch.object(contract, "start_working_bundle", side_effect=changed):
                result = contract.reopen_spec(
                    root,
                    path,
                    expected_revision=ref["revision"],
                    reason="clarify",
                    task_ref="reopen-task",
                )
            self.assertEqual("BLOCKED", result["verdict"], result)
            self.assertEqual(concurrent[0], path.read_bytes())
            self.assertIn(b"status: confirmed", path.read_bytes())

    def test_noncontention_os_error_does_not_wait_or_claim_another_editor(self):
        import errno
        import os

        if os.name == "nt":
            import msvcrt as locks

            method = "locking"
        else:
            import fcntl as locks

            method = "flock"
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(
                    locks,
                    method,
                    side_effect=OSError(errno.EIO, "injected I/O failure"),
                ),
                patch.object(contract.time, "sleep") as sleep,
            ):
                with self.assertRaises(OSError) as caught:
                    with contract.project_state_lock(Path(directory), "io-error"):
                        self.fail("failed OS lock acquired")
                self.assertEqual(errno.EIO, caught.exception.errno)
                sleep.assert_not_called()

    def test_legacy_and_canonical_references_use_the_same_lock(self):
        from contextlib import contextmanager

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref = contract.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(status="working"),
                task_ref="alias-task",
            )["working_spec"]
            keys = []

            @contextmanager
            def observe_lock(root, key):
                keys.append(key)
                yield

            wrapped = contract._serialize_spec_update(
                lambda root, working_id: working_id
            )
            with patch.object(contract, "project_state_lock", side_effect=observe_lock):
                wrapped(root, ref["working_id"])
                wrapped(root, ref["working_id"].replace("WORKING-SPEC-", "WSP-", 1))
            self.assertEqual(["spec:" + ref["working_id"]] * 2, keys)

    def test_reconcile_preserves_audit_appended_after_caller_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ref = contract.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(status="working"),
                task_ref="audit-task",
            )["working_spec"]
            path = root / ref["snapshot_path"]
            baseline = path.read_text(encoding="utf-8")
            event = contract._append_journal_event(
                path,
                event_type="discussion",
                working_id=ref["working_id"],
                revision=ref["revision"],
                previous_snapshot_hash=ref["snapshot_hash"],
                snapshot_hash=ref["snapshot_hash"],
                continuity="continuous",
                verdict="PASS",
                delta={"discussion": {"summary": "Concurrent discussion must survive"}},
            )
            changed = baseline.replace(
                "Retries are inconsistent.", "Retries need a consistent policy."
            )
            result = contract.reconcile_working_bundle(
                root,
                ref["working_id"],
                changed,
                {},
                expected_revision=ref["revision"],
                expected_hash=ref["snapshot_hash"],
            )
            self.assertEqual("PASS", result["verdict"], result)
            events, continuity = contract._read_journal(path)
            self.assertEqual("continuous", continuity)
            self.assertIn(event["event_hash"], [item["event_hash"] for item in events])
            self.assertEqual("reconcile", events[-1]["event_type"])

    def test_selector_gaps_collect_all_criteria_and_reject_invalid_types(self):
        errors = contract.acceptance_selector_gaps(
            {
                "AC-001": {},
                "AC-002": {"evidence_claims": ["invented-claim"], "rationale": " "},
                "AC-003": {"evidence_claims": "host-semantics", "rationale": 1},
            }
        )
        for ac in ("AC-001", "AC-002", "AC-003"):
            self.assertTrue(any(ac in error for error in errors), errors)
        self.assertGreaterEqual(len(errors), 6)

    def test_confirmation_blocks_missing_selectors_but_draft_is_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = confirmed_spec() + "\n## Acceptance Mapping\n{}\n"
            started = contract.start_working_bundle(
                root, "payment-retry", source, task_ref="selection-test"
            )
            self.assertEqual("PASS", started["verdict"], started)
            ref = started["working_spec"]
            self.assertTrue((root / ref["snapshot_path"]).is_file())
            result = contract.materialize_working_bundle(
                root,
                ref["working_id"],
                expected_revision=ref["revision"],
                expected_hash=ref["snapshot_hash"],
            )
            self.assertEqual("BLOCKED", result["verdict"], result)
            self.assertIn("AC-001", str(result))
            self.assertEqual(
                "working",
                contract.resolve_working_bundle(root, reference=ref["working_id"])[
                    "working_spec"
                ]["status"],
            )

    def test_generation_reports_planning_independently_of_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "specs").mkdir()
            path = root / "specs/SPEC-0001-payment-retry.md"
            path.write_text(
                confirmed_spec() + "\n## Acceptance Mapping\n{}\n", encoding="utf-8"
            )
            missing = contract.acceptance_generation_plan(
                root, path.relative_to(root).as_posix()
            )
            self.assertEqual("PASS", missing["generation_verdict"])
            self.assertEqual("BLOCKED", missing["planning_verdict"])
            self.assertFalse(missing["acceptance_complete"])
            selectors = {
                "AC-001": {
                    "evidence_claims": ["host-semantics"],
                    "rationale": "Host retry behavior with no device claim.",
                }
            }
            path.write_text(
                confirmed_spec()
                + "\n## Acceptance Mapping\n"
                + json.dumps(selectors)
                + "\n",
                encoding="utf-8",
            )
            complete = contract.acceptance_generation_plan(
                root, path.relative_to(root).as_posix()
            )
            self.assertEqual("PASS", complete["planning_verdict"], complete)
            self.assertFalse(complete["acceptance_complete"])

    def test_device_claim_cannot_be_relabelled_by_host_rationale_or_waiver(self):
        matrix = {
            "layers": {"module-contract": {}, "hil": {}},
            "rules": [
                {
                    "id": "physical",
                    "contract_dimensions": [],
                    "execution_changes": [],
                    "evidence_claims": ["physical-integration"],
                    "layers": ["hil"],
                    "execution_profiles": [],
                    "on_device_scenarios": [],
                }
            ],
        }
        errors = contract.acceptance_selector_gaps(
            {
                "AC-001": {
                    "evidence_claims": ["physical-integration"],
                    "rationale": "User waived Linux installation only.",
                }
            },
            matrix,
        )
        self.assertTrue(any("scenario_layers" in e for e in errors), errors)
        self.assertTrue(any("build_artifact" in e for e in errors), errors)

    def test_legacy_ungoverned_host_remains_compatible(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                [],
                contract.acceptance_plan_completeness(
                    Path(directory), confirmed_spec()
                ),
            )

    def test_invalid_matrix_is_reported_without_losing_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "validation").mkdir()
            (root / "validation/verification-ladder.yaml").write_text(
                "layers: [", encoding="utf-8"
            )
            gaps = contract.acceptance_plan_completeness(root, confirmed_spec())
            self.assertTrue(gaps)
            self.assertIn("Acceptance planning", str(gaps))


if __name__ == "__main__":
    unittest.main()
