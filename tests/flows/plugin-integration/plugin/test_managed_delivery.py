from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_turn_continuity import selection, spec

sys.path.insert(
    0,
    str(
        next(p for p in Path(__file__).resolve().parents if (p / "CLAUDE.md").is_file())
        / "dist/governed-engineering-skills/skills/implement/scripts"
    ),
)
sys.path.insert(
    0,
    str(
        next(p for p in Path(__file__).resolve().parents if (p / "CLAUDE.md").is_file())
        / "dist/governed-engineering-skills/skills/spec-governance/scripts"
    ),
)
from managed_delivery import audit_trace, execute_request
from test_spec_governance import confirmed_spec


class ManagedDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        r = spec.start_working_bundle(
            self.root,
            "payment-retry",
            confirmed_spec(status="working"),
            task_ref="task-A",
        )
        w = r["working_spec"]
        r = spec.materialize_working_bundle(
            self.root,
            w["working_id"],
            expected_revision=w["revision"],
            expected_hash=w["snapshot_hash"],
        )
        self.ref = r["working_spec"]
        self.path = r["canonical_spec"]["path"]
        self.base = {
            "spec": self.path,
            "working_reference": w["working_id"],
            "task_ref": "task-A",
        }
        self.target = self.root / "program.txt"
        self.target.write_bytes(b"before\n")

    def append_discussion(self):
        from discussion_state import _append

        ref = spec.resolve_working_bundle(
            self.root, reference=self.base["working_reference"]
        )["working_spec"]
        _append(
            self.root, ref, {"summary": "Clarified existing scope without changes."}
        )

    def test_discussion_only_append_keeps_authority_and_original_receipt(self):
        from execution_state import read_execution_state

        self.assertEqual("PASS", self.authorize()["verdict"])
        receipt = read_execution_state(self.root, "task-A")["receipt"]
        self.append_discussion()
        self.assertEqual("PASS", self.patch()["verdict"])
        self.assertEqual(receipt, read_execution_state(self.root, "task-A")["receipt"])
        self.assertEqual(
            "PASS",
            execute_request(self.root, self.base | {"operation": "status"})["verdict"],
        )

    def test_pending_authority_survives_discussion_but_not_revocation(self):
        (self.root / "validation").mkdir()
        self.assertEqual("pending", self.authorize()["authorization_status"])
        self.append_discussion()
        retried = self.authorize()
        self.assertEqual("pending", retried["authorization_status"], retried)
        self.assertTrue(retried["replayed"])
        execute_request(self.root, {"operation": "suspend", "task_ref": "task-A"})
        self.append_discussion()
        self.assertEqual("BLOCKED", self.authorize()["verdict"])

    def test_discussion_append_does_not_hide_body_or_history_tampering(self):
        for target in ("body", "history"):
            with self.subTest(target=target):
                self.assertEqual("PASS", self.authorize("event-" + target)["verdict"])
                self.append_discussion()
                path = self.root / self.path
                original = path.read_text(encoding="utf-8")
                if target == "body":
                    changed = original.replace("## Problem", "## Changed Problem", 1)
                else:
                    changed = original.replace(
                        '"event_type":"discussion"', '"event_type":"reconcile"', 1
                    )
                self.assertNotEqual(original, changed)
                path.write_text(changed, encoding="utf-8")
                self.assertEqual("BLOCKED", self.patch()["verdict"])
                path.write_text(original, encoding="utf-8")

    def test_legacy_binding_requires_proven_original_hashes(self):
        from execution_state import execution_binding, execution_binding_matches

        current = execution_binding(
            self.root, self.path, self.base["working_reference"], "task-A"
        )
        legacy = {k: v for k, v in current.items() if k != "journal_tip"}
        self.assertTrue(execution_binding_matches(self.root, legacy, current))
        self.append_discussion()
        after = execution_binding(
            self.root, self.path, self.base["working_reference"], "task-A"
        )
        self.assertTrue(execution_binding_matches(self.root, legacy, after))

    def legacy_receipt(self):
        from execution_state import read_execution_state, write_execution_state

        self.assertEqual("PASS", self.authorize()["verdict"])
        state = read_execution_state(self.root, "task-A")
        for key in ("receipt",):
            state[key]["binding"].pop("journal_tip", None)
        for receipt in state.get("receipts", {}).values():
            receipt["binding"].pop("journal_tip", None)
        write_execution_state(self.root, "task-A", state)
        return state["receipt"]

    def test_legacy_receipt_reconstructs_original_bytes_after_discussion(self):
        from execution_state import read_execution_state

        original = self.legacy_receipt()
        for _ in range(3):
            self.append_discussion()
        self.assertEqual("PASS", self.patch()["verdict"])
        self.assertEqual(original, read_execution_state(self.root, "task-A")["receipt"])

    def test_legacy_equivalent_snapshot_cannot_replace_original_hash(self):
        from execution_state import read_execution_state, write_execution_state

        self.legacy_receipt()
        self.append_discussion()
        state = read_execution_state(self.root, "task-A")
        for receipt in [state["receipt"], *state["receipts"].values()]:
            receipt["binding"]["spec_hash"] = "0" * 64
            receipt["binding"]["journal_hash"] = "0" * 64
        write_execution_state(self.root, "task-A", state)
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_legacy_receipt_rejects_contract_change_and_suspension(self):
        self.legacy_receipt()
        self.append_discussion()
        path = self.root / self.path
        before = path.read_bytes()
        path.write_bytes(before.replace(b"## Problem", b"## Different Problem", 1))
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        path.write_bytes(before)
        execute_request(self.root, {"operation": "suspend", "task_ref": "task-A"})
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def compatibility(self, version="v1", persist=True):
        from execution_state import assess_execution_compatibility

        return assess_execution_compatibility(
            self.root,
            self.path,
            self.base["working_reference"],
            "task-A",
            {"version": version, "rules_sha256": version},
            persist=persist,
            validation_assessor=lambda *a, **k: {"verdict": "PASS"},
        )

    def test_compatibility_cache_reuses_only_matching_inputs(self):
        self.assertEqual("PASS", self.authorize()["verdict"])
        first = self.compatibility()
        self.assertEqual("PASS", first["verdict"], first)
        self.assertFalse(first["reused"])
        self.assertTrue(self.compatibility()["reused"])
        self.append_discussion()
        self.assertTrue(self.compatibility()["reused"])
        self.assertFalse(self.compatibility("v2")["reused"])
        (self.root / "validation").mkdir()
        (self.root / "validation/layout.yaml").write_text(
            "schema_version: 1\n", encoding="utf-8"
        )
        changed = self.compatibility("v2")
        self.assertFalse(changed["reused"])
        self.assertFalse(changed["product_code_allowed"])
        self.assertTrue(self.compatibility("v2")["reused"])

    def test_compatibility_corrupt_cache_and_revoked_authority_not_reused(self):
        from execution_state import read_execution_state, write_execution_state

        self.authorize()
        self.compatibility()
        state = read_execution_state(self.root, "task-A")
        state["compatibility"]["report_hash"] = "corrupt"
        write_execution_state(self.root, "task-A", state)
        self.assertFalse(self.compatibility()["reused"])
        execute_request(self.root, {"operation": "suspend", "task_ref": "task-A"})
        report = self.compatibility()
        self.assertFalse(report["reused"])
        self.assertFalse(report["product_code_allowed"])
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_compatibility_write_failure_preserves_receipt(self):
        from unittest.mock import patch

        import execution_state

        self.authorize()
        before = execution_state.read_execution_state(self.root, "task-A")
        with patch.object(
            execution_state, "_atomic_write", side_effect=OSError("disk failure")
        ):
            result = self.compatibility()
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertEqual(
            before, execution_state.read_execution_state(self.root, "task-A")
        )

    def test_compatibility_compare_and_swap_rejects_concurrent_state_change(self):
        from unittest.mock import patch

        import execution_state

        self.authorize()
        original = execution_state.write_execution_state

        def concurrent(root, task, value):
            newer = execution_state.read_execution_state(root, task)
            newer["concurrent_marker"] = "preserve"
            original(root, task, newer)
            original(root, task, value)

        with patch.object(
            execution_state, "write_execution_state", side_effect=concurrent
        ):
            result = self.compatibility()
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertEqual(
            "preserve",
            execution_state.read_execution_state(self.root, "task-A")[
                "concurrent_marker"
            ],
        )

    def test_compatibility_managed_entry_does_not_grant_authority(self):
        report = execute_request(self.root, self.base | {"operation": "compatibility"})
        self.assertEqual("PASS", report["verdict"], report)
        self.assertFalse(report["product_code_allowed"])
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_compatibility_rechecks_unprovable_byte_drift(self):
        self.authorize()
        self.compatibility()
        path = self.root / self.path
        path.write_bytes(path.read_bytes() + b"\n")
        report = self.compatibility()
        self.assertEqual("BLOCKED", report["verdict"], report)
        self.assertFalse(report["reused"])
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_compatibility_malformed_binding_fails_closed(self):
        from execution_state import read_execution_state, write_execution_state

        self.authorize()
        for value in ([], None):
            state = read_execution_state(self.root, "task-A")
            state["receipt"]["binding"] = value
            write_execution_state(self.root, "task-A", state)
            report = self.compatibility()
            self.assertEqual("BLOCKED", report["verdict"], report)
            self.assertIn("binding", report["reason"])

    def test_direct_managed_mutations_check_compatibility_before_effects(self):
        from unittest.mock import patch

        import managed_delivery

        self.authorize()
        before = self.target.read_bytes()
        with patch.object(
            managed_delivery,
            "assess_delivery_compatibility",
            return_value={"verdict": "BLOCKED", "reason": "unknown rules"},
        ) as assess:
            for operation in (
                "apply",
                "prepare-validation",
                "repair-acceptance",
                "recover",
                "complete",
                "status",
            ):
                result = execute_request(
                    self.root, self.base | {"operation": operation}
                )
                self.assertEqual("BLOCKED", result["verdict"], result)
                self.assertFalse(result["product_code_allowed"])
            self.assertEqual(6, assess.call_count)
        self.assertEqual(before, self.target.read_bytes())

    def test_router_renders_fresh_and_blocked_compatibility_inventory(self):
        from guided_workflow_router import format_route_output

        for report in (
            {"verdict": "PASS", "reused": False, "inventory": []},
            {"verdict": "BLOCKED", "reused": True, "reason": "unknown"},
        ):
            rendered = format_route_output({"status": "PASS", "compatibility": report})
            self.assertEqual(report, json.loads(rendered)["compatibility"])

    def test_validation_unknown_is_reported_without_blocking_bounded_preparation(self):
        from execution_state import assess_execution_compatibility
        from project_validation_adapter import assess_project_validation

        self.authorize()
        (self.root / "validation").mkdir()
        (self.root / "validation/verification-ladder.yaml").write_text(
            "broken: [", encoding="utf-8"
        )
        report = assess_execution_compatibility(
            self.root,
            self.path,
            self.base["working_reference"],
            "task-A",
            {"version": "v1"},
            persist=True,
            validation_assessor=assess_project_validation,
        )
        self.assertEqual("BLOCKED", report["verdict"], report)
        self.assertTrue(report["preparation_allowed"])
        self.assertFalse(report["product_code_allowed"])
        self.assertNotEqual("PASS", report["validation_assessment"]["verdict"])
        self.assertTrue(
            any(
                r["kind"] == "validation" and r["disposition"] == "unknown"
                for r in report["inventory"]
            )
        )

    def test_planning_pass_does_not_hide_blocked_layout(self):
        from execution_state import assess_execution_compatibility

        self.authorize()
        report = assess_execution_compatibility(
            self.root,
            self.path,
            self.base["working_reference"],
            "task-A",
            {"version": "v1"},
            validation_assessor=lambda *a, **k: {
                "verdict": "PASS",
                "layout": {"verdict": "BLOCKED"},
            },
        )
        self.assertEqual("BLOCKED", report["verdict"], report)
        self.assertTrue(report["preparation_allowed"])
        self.assertFalse(report["product_code_allowed"])

    def test_cached_inventory_rechecks_changed_validation_outcome(self):
        from execution_state import assess_execution_compatibility

        self.authorize()
        current = {"verdict": "PASS", "layout": {"verdict": "PASS"}}

        def assessor(*args, **kwargs):
            return current

        args = (
            self.root,
            self.path,
            self.base["working_reference"],
            "task-A",
            {"version": "v1"},
        )
        first = assess_execution_compatibility(
            *args, persist=True, validation_assessor=assessor
        )
        self.assertEqual("PASS", first["verdict"])
        self.assertTrue(
            assess_execution_compatibility(*args, validation_assessor=assessor)[
                "reused"
            ]
        )
        current = {"verdict": "PASS", "layout": {"verdict": "BLOCKED"}}
        changed = assess_execution_compatibility(*args, validation_assessor=assessor)
        self.assertEqual("BLOCKED", changed["verdict"], changed)
        self.assertFalse(changed["reused"])

    def authorize(self, event="user-1", **changes):
        request = (
            self.base
            | {
                "operation": "authorize",
                "instruction": "開始執行",
                "source_event_id": event,
                "expected_hash": hashlib.sha256(
                    (self.root / self.path).read_bytes()
                ).hexdigest(),
            }
            | changes
        )
        return execute_request(self.root, request)

    def patch(self, candidate_validator=None, **changes):
        patch = {
            "path": "program.txt",
            "before_sha256": hashlib.sha256(b"before\n").hexdigest(),
            "content": "after\n",
        }
        return execute_request(
            self.root,
            self.base | {"operation": "apply", "patch": patch | changes},
            candidate_validator=candidate_validator,
        )

    def recovery_request(self, **updates):
        return (
            self.base
            | {
                "operation": "recover",
                "branch": "layout",
                "deterministic": True,
                "diagnosis": {
                    "category": "project-configuration",
                    "source": "test-validation-layout",
                    "evidence": "fixture missing layout",
                    "affected_scope": ["layout"],
                    "repair_suggestion": "restore declared layout",
                    "authorization": "current receipt",
                    "recheck_command": ["architecture_cli.py", "layout"],
                    "success_condition": "layout verdict PASS",
                    "resume_target": "validation",
                },
            }
            | updates
        )

    def test_pending_authorization_survives_planning_failure_and_retries(self):
        (self.root / "validation").mkdir()
        request = self.base | {
            "operation": "authorize",
            "instruction": "開始執行",
            "source_event_id": "pending-event",
            "expected_hash": hashlib.sha256(
                (self.root / self.path).read_bytes()
            ).hexdigest(),
        }
        first = execute_request(self.root, request)
        self.assertEqual("BLOCKED", first["verdict"])
        self.assertEqual("pending", first.get("authorization_status"), first)
        self.assertFalse(first["product_code_allowed"])
        again = execute_request(self.root, request)
        self.assertEqual(first["pending_authorization"], again["pending_authorization"])
        self.assertTrue(again["replayed"])
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())
        execute_request(self.root, {"operation": "suspend", "task_ref": "task-A"})
        suspended = execute_request(self.root, request)
        self.assertEqual("BLOCKED", suspended["verdict"])
        self.assertNotEqual("pending", suspended.get("authorization_status"))

    def preparation(self, path, content, **changes):
        target = self.root / path
        return (
            self.base
            | {
                "operation": "prepare-validation",
                "source_event_id": "user-1",
                "patch": {
                    "path": path,
                    "before_sha256": hashlib.sha256(target.read_bytes()).hexdigest()
                    if target.exists()
                    else None,
                    "content": content,
                },
            }
            | changes
        )

    def test_preparation_enables_implementation_then_requires_acceptance_evidence(self):
        (self.root / "validation").mkdir()
        (self.root / "architecture").mkdir()
        self.assertEqual("pending", self.authorize()["authorization_status"])
        state = {"enablement": False, "acceptance": False}
        # Start after acceptance repair; isolate sequencing at the validation port.
        (self.root / "validation/acceptance-SPEC-0001.json").write_text(
            json.dumps({"acceptance": {"AC-001": {}}}), encoding="utf-8"
        )

        def assessor(root, spec_path, *, phase, **kwargs):
            ready = all(
                (root / name).is_file()
                for name in (
                    "architecture/adoption.yaml",
                    "validation/on-device.yaml",
                    "validation/layout.yaml",
                    "validation/verification-ladder.yaml",
                )
            )
            passed = ready and (phase == "planning" or state.get(phase, False))
            return {"verdict": "PASS" if passed else "BLOCKED", "phase": phase}

        for path, content in (
            (
                "architecture/adoption.yaml",
                "runtime_validation:\n  applicability: required\n  rationale: Physical timing requires device evidence.\n",
            ),
            ("validation/on-device.yaml", "schema_version: '1.0'\nscenarios: []\n"),
            ("validation/layout.yaml", "schema_version: 1\nentries: []\n"),
            (
                "validation/verification-ladder.yaml",
                "schema_version: '1.0'\nlayers: {}\n",
            ),
        ):
            result = execute_request(
                self.root, self.preparation(path, content), validation_assessor=assessor
            )
            self.assertTrue(result.get("preparation_applied"), result)
            self.assertFalse(result["product_code_allowed"])
            self.assertFalse(result["device_actions_authorized"])
        enable = execute_request(
            self.root,
            self.base
            | {
                "operation": "enablement-status",
                "source_event_id": "user-1",
            },
            validation_assessor=assessor,
        )
        self.assertTrue(enable["enablement_allowed"], enable)
        self.assertFalse(enable["device_actions_authorized"])
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        state["enablement"] = True
        # Same retained user event, no new authorization or reset.
        result = execute_request(
            self.root,
            self.base
            | {
                "operation": "authorize",
                "instruction": "開始執行",
                "source_event_id": "user-1",
                "expected_hash": hashlib.sha256(
                    (self.root / self.path).read_bytes()
                ).hexdigest(),
            },
            validation_assessor=assessor,
        )
        self.assertTrue(result["product_code_allowed"], result)
        applied = execute_request(
            self.root,
            self.base
            | {
                "operation": "apply",
                "patch": {
                    "path": "program.txt",
                    "before_sha256": hashlib.sha256(b"before\n").hexdigest(),
                    "content": "after\n",
                },
            },
            validation_assessor=assessor,
        )
        self.assertEqual("PASS", applied["verdict"], applied)
        self.assertEqual(b"after\n", self.target.read_bytes())
        complete = self.base | {"operation": "complete"}
        self.assertEqual(
            "BLOCKED",
            execute_request(self.root, complete, validation_assessor=assessor)[
                "verdict"
            ],
        )
        state["acceptance"] = True
        self.assertEqual(
            "PASS",
            execute_request(self.root, complete, validation_assessor=assessor)[
                "verdict"
            ],
        )

    def test_preparation_rejects_source_downgrades_and_revoked_authority(self):
        directory = self.root / "validation"
        directory.mkdir()
        self.assertEqual("pending", self.authorize()["authorization_status"])
        for path, content in (
            ("program.txt", "unauthorized source"),
            ("validation/acceptance-SPEC-0001.json", "{}"),
            ("specs/other.yaml", "status: confirmed"),
            ("validation/on-device.yaml", "[not a mapping]"),
            ("validation/on-device.yaml", "malformed: ["),
        ):
            with self.subTest(path=path, content=content):
                result = execute_request(self.root, self.preparation(path, content))
                self.assertEqual("BLOCKED", result["verdict"], result)
        profile = directory / "on-device.yaml"
        profile.write_text("threshold: 10\nscenarios: [required]\n", encoding="utf-8")
        for content in (
            "threshold: 20\nscenarios: [required]\n",
            "threshold: 10\nscenarios: []\n",
        ):
            self.assertEqual(
                "BLOCKED",
                execute_request(
                    self.root, self.preparation("validation/on-device.yaml", content)
                )["verdict"],
            )
        request = self.preparation(
            "validation/on-device.yaml",
            profile.read_text() + "rationale: Preserve existing limits.\n",
        )
        execute_request(self.root, {"operation": "suspend", "task_ref": "task-A"})
        self.assertEqual("BLOCKED", execute_request(self.root, request)["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_preparation_rechecks_scope_and_hash_without_manufacturing_authority(self):
        (self.root / "validation").mkdir()
        request = self.preparation(
            "validation/layout.yaml", "schema_version: 1\nentries: []\n"
        )
        self.assertEqual("BLOCKED", execute_request(self.root, request)["verdict"])
        self.assertEqual("pending", self.authorize()["authorization_status"])
        wrong = request | {"source_event_id": "different-user-event"}
        self.assertEqual("BLOCKED", execute_request(self.root, wrong)["verdict"])
        (self.root / "validation/layout.yaml").write_text(
            "schema_version: 1\nentries: [concurrent]\n", encoding="utf-8"
        )
        self.assertEqual("BLOCKED", execute_request(self.root, request)["verdict"])
        self.assertIn("concurrent", (self.root / "validation/layout.yaml").read_text())

    def test_acceptance_repair_requires_a_bound_declared_plan(self):
        from spec_contract import acceptance_repair_plan

        directory = self.root / "validation"
        directory.mkdir()
        plan = acceptance_repair_plan(self.root, self.path)
        self.assertEqual("BLOCKED", plan["verdict"])
        self.assertTrue(plan["draft_required"])
        self.assertFalse((directory / "acceptance-SPEC-0001.json").exists())

        # The reviewed contract states the mapping explicitly. No prose-to-test
        # inference or caller deterministic flag can substitute for this source.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mapping = {
                "AC-001": {
                    "evidence_claims": ["host-semantics"],
                    "contract_dimensions": ["call-order"],
                    "execution_changes": [],
                    "rationale": "The retry contract requires a host call-order test.",
                }
            }
            created = spec.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(status="working")
                + "\n## Acceptance Mapping\n\n```json\n"
                + json.dumps(mapping)
                + "\n```\n",
                task_ref="repair-task",
            )["working_spec"]
            confirmed = spec.materialize_working_bundle(
                root,
                created["working_id"],
                expected_revision=created["revision"],
                expected_hash=created["snapshot_hash"],
            )
            path = confirmed["canonical_spec"]["path"]
            (root / "validation").mkdir()
            base = {
                "spec": path,
                "working_reference": created["working_id"],
                "task_ref": "repair-task",
            }
            auth = base | {
                "operation": "authorize",
                "instruction": "開始執行",
                "source_event_id": "reviewed-repair",
                "expected_hash": hashlib.sha256((root / path).read_bytes()).hexdigest(),
            }
            self.assertEqual(
                "pending", execute_request(root, auth)["authorization_status"]
            )
            plan = acceptance_repair_plan(root, path)
            self.assertEqual("PASS", plan["verdict"], plan)
            repair = base | {
                "operation": "repair-acceptance",
                "source_event_id": "reviewed-repair",
                "patch": plan["patch"],
            }
            bad = repair | {"patch": plan["patch"] | {"path": "program.txt"}}
            self.assertEqual("BLOCKED", execute_request(root, bad)["verdict"])
            result = execute_request(root, repair)
            self.assertTrue(result["repair_applied"], result)
            self.assertFalse(result["product_code_allowed"])
            # Missing external validation still prevents a receipt after repair.
            self.assertEqual("BLOCKED", result["verdict"])
            self.assertEqual(
                "PASS",
                execute_request(
                    root, auth, validation_assessor=lambda *a, **k: {"verdict": "PASS"}
                )["verdict"],
            )

    def test_completed_pending_authorization_replay_is_idempotent(self):
        (self.root / "validation").mkdir()
        request = self.base | {
            "operation": "authorize",
            "instruction": "開始執行",
            "source_event_id": "retry-pending",
            "expected_hash": hashlib.sha256(
                (self.root / self.path).read_bytes()
            ).hexdigest(),
        }
        self.assertEqual(
            "pending", execute_request(self.root, request)["authorization_status"]
        )
        # Removing the unconfigured empty fixture folder resolves this planning gap.
        (self.root / "validation").rmdir()
        self.assertEqual("PASS", execute_request(self.root, request)["verdict"])
        again = execute_request(self.root, request)
        self.assertEqual("PASS", again["verdict"], again)
        self.assertTrue(again["replayed"])
        changed = request | {"instruction": "開始執行 SPEC-9999"}
        self.assertEqual("BLOCKED", execute_request(self.root, changed)["verdict"])
        execute_request(self.root, {"operation": "suspend", "task_ref": "task-A"})
        self.assertEqual("BLOCKED", execute_request(self.root, request)["verdict"])

    def test_ambiguous_draft_and_revocation_survive_owner_restart(self):
        (self.root / "validation").mkdir()
        self.assertEqual("pending", self.authorize()["authorization_status"])
        draft = {
            "path": "validation/acceptance-SPEC-0001.json",
            "before_sha256": None,
            "content": '{"review": "Need to select validation methods from the specification."}',
        }
        repair = self.base | {
            "operation": "repair-acceptance",
            "source_event_id": "user-1",
            "patch": draft,
        }
        blocked = execute_request(self.root, repair)
        self.assertEqual("BLOCKED", blocked["verdict"])
        query = self.base | {
            "operation": "authorization-status",
            "source_event_id": "user-1",
        }
        self.assertEqual(draft, execute_request(self.root, query)["draft"]["patch"])
        execute_request(self.root, {"operation": "suspend", "task_ref": "task-A"})
        restored = execute_request(self.root, query)
        self.assertEqual("revoked", restored["authorization_status"])
        self.assertEqual(draft, restored["draft"]["patch"])
        self.assertFalse(restored["product_code_allowed"])

    def test_parameterized_additive_repair_handles_stale_inputs_and_interruption(self):
        import os
        from unittest.mock import patch

        from spec_contract import acceptance_repair_plan

        for identity, revision, ac in (
            ("SPEC-0013", 2, "AC-017"),
            ("SPEC-0241", 9, "AC-093"),
        ):
            with (
                self.subTest(spec=identity, revision=revision, ac=ac),
                tempfile.TemporaryDirectory() as temp,
            ):
                root = Path(temp)
                row = {
                    "evidence_claims": ["host-semantics"],
                    "contract_dimensions": ["call-order"],
                    "execution_changes": [],
                    "rationale": "Host retry call order is observable.",
                }
                declared = {ac: row, "AC-099": row}
                text = (
                    confirmed_spec(spec_id=identity, status="working")
                    .replace("revision: 1", f"revision: {revision}")
                    .replace("AC-001", ac)
                )
                text = text.replace(
                    "| "
                    + ac
                    + " | REQ-001 | A fourth attempt is never made. | `test_retry_limit` | pending |",
                    "| "
                    + ac
                    + " | REQ-001 | A fourth attempt is never made. | `test_retry_limit` | pending |\n| AC-099 | REQ-001 | Exhaustion stops further calls. | `test_exhaustion` | pending |",
                )
                text += (
                    "\n## Acceptance Mapping\n\n```json\n"
                    + json.dumps(declared)
                    + "\n```\n"
                )
                created = spec.start_working_bundle(
                    root,
                    "payment-retry",
                    text,
                    task_ref="repair-task",
                    preserve_spec_identity=True,
                )["working_spec"]
                confirmed = spec.materialize_working_bundle(
                    root,
                    created["working_id"],
                    expected_revision=created["revision"],
                    expected_hash=created["snapshot_hash"],
                )
                path = confirmed["canonical_spec"]["path"]
                self.assertIn(identity, path)
                self.assertEqual(revision, confirmed["working_spec"]["revision"])
                (root / "validation").mkdir()
                complete = acceptance_repair_plan(root, path)
                seeded = json.loads(complete["patch"]["content"])
                seeded["acceptance"].pop("AC-099")
                seeded["acceptance"][ac]["rationale"] = (
                    "Existing reviewed row must remain unchanged."
                )
                original_row = dict(seeded["acceptance"][ac])
                target = root / complete["patch"]["path"]
                target.write_text(json.dumps(seeded), encoding="utf-8")
                base = {
                    "spec": path,
                    "working_reference": created["working_id"],
                    "task_ref": "repair-task",
                }
                auth = base | {
                    "operation": "authorize",
                    "instruction": "開始執行",
                    "source_event_id": "matrix-event",
                    "expected_hash": hashlib.sha256(
                        (root / path).read_bytes()
                    ).hexdigest(),
                }
                self.assertEqual(
                    "pending", execute_request(root, auth)["authorization_status"]
                )
                plan = acceptance_repair_plan(root, path)
                repair = base | {
                    "operation": "repair-acceptance",
                    "source_event_id": "matrix-event",
                    "patch": plan["patch"],
                }
                before = target.read_bytes()
                altered = json.loads(plan["patch"]["content"])
                altered["acceptance"][ac]["evidence_claims"] = []
                result = execute_request(
                    root,
                    repair
                    | {"patch": plan["patch"] | {"content": json.dumps(altered)}},
                )
                self.assertEqual("BLOCKED", result["verdict"])
                self.assertEqual(before, target.read_bytes())
                self.assertEqual(
                    "BLOCKED",
                    execute_request(root, repair | {"task_ref": "other-task"})[
                        "verdict"
                    ],
                )
                target.write_bytes(before + b"\n")
                self.assertEqual("BLOCKED", execute_request(root, repair)["verdict"])
                self.assertEqual(before + b"\n", target.read_bytes())
                repair["patch"] = acceptance_repair_plan(root, path)["patch"]
                replace = os.replace

                def interrupted(source, destination, target=target, replace=replace):
                    if Path(destination).resolve() == target.resolve():
                        raise OSError("injected interruption before mapping commit")
                    return replace(source, destination)

                with patch.object(os, "replace", side_effect=interrupted):
                    result = execute_request(root, repair)
                self.assertEqual("BLOCKED", result["verdict"])
                self.assertEqual(before + b"\n", target.read_bytes())
                assessor = lambda *a, **k: {"verdict": "PASS"}
                result = execute_request(root, repair, validation_assessor=assessor)
                self.assertEqual("PASS", result["verdict"], result)
                self.assertEqual(
                    original_row,
                    json.loads(target.read_text(encoding="utf-8"))["acceptance"][ac],
                )
                replay = execute_request(root, repair, validation_assessor=assessor)
                self.assertEqual("PASS", replay["verdict"], replay)
                self.assertTrue(replay["repair_replayed"])
                history = execute_request(
                    root,
                    base
                    | {
                        "operation": "authorization-status",
                        "source_event_id": "matrix-event",
                    },
                )
                self.assertGreaterEqual(len(history["repair_history"]), 3)
                (root / path).write_bytes((root / path).read_bytes() + b"\n")
                self.assertEqual(
                    "BLOCKED",
                    execute_request(root, auth, validation_assessor=assessor)[
                        "verdict"
                    ],
                )

    def test_disjoint_stale_patch_is_integrated_but_overlap_is_rejected(self):
        self.assertEqual("PASS", self.authorize()["verdict"])
        base = "one\ntwo\nthree\n"
        self.target.write_text("ONE\ntwo\nthree\n", encoding="utf-8", newline="\n")
        result = self.patch(
            candidate_validator=lambda root, candidate: {
                "verdict": "PASS",
                "sha256": hashlib.sha256(candidate["content"].encode()).hexdigest(),
            },
            before_sha256=hashlib.sha256(base.encode()).hexdigest(),
            before_content=base,
            content="one\ntwo\nTHREE\n",
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertTrue(result["merged"])
        self.assertEqual("ONE\ntwo\nTHREE\n", self.target.read_text())
        rejected = self.patch(
            before_sha256=hashlib.sha256(base.encode()).hexdigest(),
            before_content=base,
            content="OTHER\ntwo\nthree\n",
        )
        self.assertEqual("BLOCKED", rejected["verdict"])
        self.assertEqual("ONE\ntwo\nTHREE\n", self.target.read_text())

    def test_merged_program_requires_content_validation(self):
        import ast

        base = "value = 1\nanswer = 2\n"
        self.assertEqual("PASS", self.authorize()["verdict"])
        self.target.write_bytes(b"value = 10\nanswer = 2\n")
        updates = {
            "before_sha256": hashlib.sha256(base.encode()).hexdigest(),
            "before_content": base,
            "content": "value = 1\nanswer = (\n",
        }
        missing = self.patch(**updates)
        self.assertEqual("BLOCKED", missing["verdict"])
        self.assertIn("reviewable_candidate", missing)

        def validate(root, candidate):
            try:
                ast.parse(candidate["content"])
            except SyntaxError:
                return {"verdict": "FAIL", "sha256": candidate["sha256"]}
            return {"verdict": "PASS", "sha256": candidate["sha256"]}

        denied = self.patch(candidate_validator=validate, **updates)
        self.assertEqual("BLOCKED", denied["verdict"])
        self.assertEqual(b"value = 10\nanswer = 2\n", self.target.read_bytes())
        updates["content"] = "value = 1\nanswer = 20\n"
        stale = self.patch(
            candidate_validator=lambda root, candidate: {
                "verdict": "PASS",
                "sha256": "wrong",
            },
            **updates,
        )
        self.assertEqual("BLOCKED", stale["verdict"])
        accepted = self.patch(candidate_validator=validate, **updates)
        self.assertEqual("PASS", accepted["verdict"], accepted)
        self.assertEqual(b"value = 10\nanswer = 20\n", self.target.read_bytes())

    def test_recovery_passes_merged_candidate_to_validator(self):
        import ast
        from unittest.mock import patch

        self.assertEqual("PASS", self.authorize()["verdict"])
        base = "value = 1\nanswer = 2\n"
        self.target.write_bytes(b"value = 10\nanswer = 2\n")
        request = self.recovery_request(
            patch={
                "path": "program.txt",
                "before_sha256": hashlib.sha256(base.encode()).hexdigest(),
                "before_content": base,
                "content": "value = 1\nanswer = 20\n",
            }
        )
        candidates = []

        def validate(root, candidate):
            ast.parse(candidate["content"])
            candidates.append(candidate)
            return {"verdict": "PASS", "sha256": candidate["sha256"]}

        with patch(
            "managed_delivery.assess_project_validation",
            return_value={"verdict": "PASS", "layout": {"verdict": "PASS"}},
        ):
            result = execute_request(self.root, request, candidate_validator=validate)
        self.assertEqual("PASS", result["verdict"], result)
        self.assertEqual(1, len(candidates))
        self.assertEqual(b"value = 10\nanswer = 20\n", self.target.read_bytes())

    def test_recovery_cache_binds_phase_and_success_condition(self):
        from unittest.mock import patch

        self.assertEqual("PASS", self.authorize()["verdict"])
        request = self.recovery_request()
        with patch(
            "managed_delivery.assess_project_validation",
            return_value={"verdict": "PASS", "layout": {"verdict": "PASS"}},
        ) as checked:
            self.assertEqual("PASS", execute_request(self.root, request)["verdict"])
            self.assertTrue(execute_request(self.root, request)["replayed"])
            request["diagnosis"]["phase"] = "release"
            self.assertEqual("PASS", execute_request(self.root, request)["verdict"])
            self.assertEqual("release", checked.call_args.kwargs["phase"])
            request["diagnosis"]["success_condition"] = (
                "valid CLI result and passing required check"
            )
            self.assertEqual("PASS", execute_request(self.root, request)["verdict"])
            self.assertEqual(3, checked.call_count)

    def test_new_authorization_recovers_stale_binding_and_keeps_history(self):
        from unittest.mock import patch

        from execution_state import read_execution_state

        self.assertEqual("PASS", self.authorize()["verdict"])
        with patch(
            "managed_delivery.assess_project_validation",
            return_value={"verdict": "PASS", "layout": {"verdict": "PASS"}},
        ):
            self.assertEqual(
                "PASS", execute_request(self.root, self.recovery_request())["verdict"]
            )
            reopened = spec.reopen_spec(
                self.root,
                Path(self.path),
                expected_revision=self.ref["revision"],
                reason="new reviewed revision",
                task_ref="task-A",
            )["working_spec"]
            spec.materialize_working_bundle(
                self.root,
                reopened["working_id"],
                expected_revision=reopened["revision"],
                expected_hash=reopened["snapshot_hash"],
            )
            self.assertEqual(
                "BLOCKED",
                execute_request(self.root, self.recovery_request())["verdict"],
            )
            self.assertEqual("PASS", self.authorize(event="fresh-grant")["verdict"])
            self.assertEqual(
                "PASS", execute_request(self.root, self.recovery_request())["verdict"]
            )
        state = read_execution_state(self.root, "task-A")
        self.assertEqual(1, len(state["recovery_history"]))
        self.assertNotEqual(
            state["recovery"]["layout"]["binding"],
            state["recovery_history"][0]["cycle"]["binding"],
        )

    def test_stale_state_writer_cannot_overwrite_suspension(self):
        from execution_state import read_execution_state, write_execution_state

        self.assertEqual("PASS", self.authorize()["verdict"])
        stale = read_execution_state(self.root, "task-A")
        self.assertEqual(
            "PASS",
            execute_request(self.root, self.base | {"operation": "suspend"})["verdict"],
        )
        with self.assertRaisesRegex(ValueError, "state changed"):
            write_execution_state(self.root, "task-A", stale)
        self.assertEqual(
            "suspended", read_execution_state(self.root, "task-A")["phase"]
        )

    def test_slow_validation_does_not_lock_an_unrelated_task(self):
        import threading

        other = spec.start_working_bundle(
            self.root,
            "independent",
            confirmed_spec(slug="independent", status="working"),
            task_ref="task-B",
        )["working_spec"]
        other = spec.materialize_working_bundle(
            self.root,
            other["working_id"],
            expected_revision=other["revision"],
            expected_hash=other["snapshot_hash"],
        )["working_spec"]
        base = {
            "task_ref": "task-B",
            "spec": other["snapshot_path"],
            "working_reference": other["working_id"],
        }
        self.assertEqual(
            "PASS",
            execute_request(
                self.root,
                base
                | {
                    "operation": "authorize",
                    "instruction": "開始執行",
                    "source_event_id": "B-grant",
                    "expected_hash": hashlib.sha256(
                        (self.root / base["spec"]).read_bytes()
                    ).hexdigest(),
                },
            )["verdict"],
        )
        self.assertEqual("PASS", self.authorize()["verdict"])
        entered, release = threading.Event(), threading.Event()
        results = []

        def assessor(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise ValueError("fixture wait expired")
            return {"verdict": "PASS"}

        worker = threading.Thread(
            target=lambda: results.append(
                execute_request(
                    self.root,
                    self.base | {"operation": "status"},
                    validation_assessor=assessor,
                )
            )
        )
        worker.start()
        try:
            self.assertTrue(entered.wait(5))
            result = execute_request(
                self.root,
                base
                | {
                    "operation": "apply",
                    "patch": {
                        "path": "independent.txt",
                        "before_sha256": None,
                        "content": "independent",
                    },
                },
            )
            self.assertEqual("PASS", result["verdict"], result)
        finally:
            release.set()
            worker.join(10)
        self.assertFalse(worker.is_alive())
        self.assertEqual("PASS", results[0]["verdict"])

    def test_parallel_spec_allocation_is_unique(self):
        from concurrent.futures import ThreadPoolExecutor

        def create(index):
            slug = "independent-" + str(index)
            return spec.start_working_bundle(
                self.root,
                slug,
                confirmed_spec(slug=slug, status="working"),
                task_ref=slug,
            )

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(create, range(8)))
        self.assertTrue(all(r["verdict"] == "PASS" for r in results), results)
        self.assertEqual(8, len({r["working_spec"]["spec_id"] for r in results}))

    def test_state_lock_is_released_when_process_is_killed(self):
        script = "import sys,time; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from spec_contract import project_state_lock; root=Path(sys.argv[2]);\nwith project_state_lock(root,'crash'):\n print('locked',flush=True); time.sleep(60)"
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                script,
                str(Path(spec.__file__).parent),
                str(self.root),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.assertEqual("locked", process.stdout.readline().strip())
        finally:
            process.kill()
            process.communicate(timeout=10)
        with spec.project_state_lock(self.root, "crash", timeout=1):
            pass

    def test_dependency_blocks_until_prerequisite_implemented(self):
        prerequisite = self.root / "specs/SPEC-0099-prerequisite.md"
        prerequisite.write_text(
            confirmed_spec(spec_id="SPEC-0099", slug="prerequisite"), encoding="utf-8"
        )
        reopened = spec.reopen_spec(
            self.root,
            Path(self.path),
            expected_revision=self.ref["revision"],
            reason="dependency fixture",
            task_ref="task-A",
        )["working_spec"]
        text = (
            (self.root / self.path)
            .read_text(encoding="utf-8")
            .replace(
                "| REQ-001 | depends_on | DEC-001 |",
                "| REQ-001 | depends_on | SPEC-0099 |",
            )
        )
        ref = spec.reconcile_working_bundle(
            self.root,
            reopened["working_id"],
            text,
            {},
            expected_revision=reopened["revision"],
            expected_hash=reopened["snapshot_hash"],
        )["working_spec"]
        spec.materialize_working_bundle(
            self.root,
            ref["working_id"],
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        denied = self.authorize()
        self.assertEqual("BLOCKED", denied["verdict"], denied)
        self.assertIn("prerequisite", denied["reason"])
        prerequisite.write_text(
            confirmed_spec(
                spec_id="SPEC-0099",
                slug="prerequisite",
                status="implemented",
                evidence="PASS fixture",
                review="PASS",
            ),
            encoding="utf-8",
        )
        self.assertEqual("PASS", self.authorize()["verdict"])
        self.assertEqual("PASS", self.patch()["verdict"])
        prerequisite.write_text(
            confirmed_spec(spec_id="SPEC-0099", slug="prerequisite"), encoding="utf-8"
        )
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_transitive_implemented_dependencies_and_cycle(self):
        b = self.root / "specs/SPEC-0098-middle.md"
        c = self.root / "specs/SPEC-0099-leaf.md"
        c.write_text(
            confirmed_spec(
                spec_id="SPEC-0099",
                slug="leaf",
                status="implemented",
                evidence="PASS fixture",
                review="PASS",
            ),
            encoding="utf-8",
        )
        b.write_text(
            confirmed_spec(
                spec_id="SPEC-0098",
                slug="middle",
                status="implemented",
                evidence="PASS fixture",
                review="PASS",
            ).replace(
                "| REQ-001 | depends_on | DEC-001 |",
                "| REQ-001 | depends_on | SPEC-0099 |",
            ),
            encoding="utf-8",
        )
        self.assertEqual([], spec.check_spec_dependencies(self.root, b))
        c.write_text(
            c.read_text(encoding="utf-8").replace(
                "| REQ-001 | depends_on | DEC-001 |",
                "| REQ-001 | depends_on | SPEC-0098 |",
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "cycle" in error for error in spec.check_spec_dependencies(self.root, b)
            )
        )

    def test_commit_serializes_with_authorization_revocation(self):
        import threading
        from unittest.mock import patch

        import managed_delivery
        from execution_state import read_execution_state, write_execution_state

        self.assertEqual("PASS", self.authorize()["verdict"])
        entered, completed = threading.Event(), threading.Event()
        outcomes = []

        def suspend():
            entered.set()
            state = read_execution_state(self.root, "task-A")
            state.update(phase="suspended", receipt=None, receipts={})
            write_execution_state(self.root, "task-A", state)
            completed.set()

        real_replace = managed_delivery.os.replace
        threads = []

        def replace(source, target):
            if Path(target) == self.target:
                thread = threading.Thread(target=suspend)
                threads.append(thread)
                thread.start()
                self.assertTrue(entered.wait(2))
                outcomes.append(completed.wait(0.1))
            return real_replace(source, target)

        with patch.object(managed_delivery.os, "replace", side_effect=replace):
            result = self.patch()
            for thread in threads:
                thread.join(5)
        self.assertEqual("PASS", result["verdict"], result)
        self.assertEqual([False], outcomes)
        self.assertTrue(completed.is_set())
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_pending_entry_is_not_promoted_to_sync_pass(self):
        from unittest.mock import patch

        from test_turn_continuity import router

        pending = {
            "verdict": "BLOCKED",
            "entry_saved": True,
            "sync_status": "pending",
            "discussion_allowed": True,
        }
        with patch.object(router, "manage_delivery_discussion", return_value=pending):
            result = router.route(
                "Explain this code",
                self.root,
                explicit_skill="explain-code-flow",
                task_ref="task-A",
                turn_ref="turn-test",
                source_ref="test",
                turn_kind="read-only",
            )
        self.assertEqual("BLOCKED", result["discussion_entry"]["verdict"])
        self.assertEqual("pending", result["discussion_entry"]["sync_status"])
        self.assertTrue(result["discussion_recovery"]["discussion_allowed"])
        self.assertFalse(result["product_code_allowed"])

    def test_finish_turn_bad_json_reports_gap_and_can_finish(self):
        observation = self.root / "bad.json"
        observation.write_text("{", encoding="utf-8")
        run = subprocess.run(
            [
                sys.executable,
                spec.__file__,
                "finish-turn",
                "--project-root",
                str(self.root),
                "--reference",
                self.ref["working_id"],
                "--task-ref",
                "task-A",
                "--observation",
                str(observation),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        result = json.loads(run.stdout)
        self.assertEqual(2, run.returncode)
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertTrue(result["can_end_turn"])
        self.assertEqual("unverifiable", result["sync_status"])

    def test_recovery_cannot_resolve_an_unrelated_condition(self):
        self.assertEqual("PASS", self.authorize()["verdict"])
        request = self.recovery_request()
        request["diagnosis"]["source"] = "unrelated-runtime-condition"
        result = execute_request(self.root, request)
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertEqual("investigate", result["recovery"]["status"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_recovery_reserves_and_does_not_repeat_identical_failure(self):
        from unittest.mock import patch

        self.assertEqual("PASS", self.authorize()["verdict"])
        request = self.recovery_request()
        with patch(
            "managed_delivery.assess_project_validation",
            return_value={"verdict": "PASS", "layout": {"verdict": "BLOCKED"}},
        ) as check:
            first = execute_request(self.root, request)
            second = execute_request(self.root, request)
        self.assertEqual("BLOCKED", first["verdict"])
        self.assertEqual("BLOCKED", second["verdict"])
        self.assertEqual(1, check.call_count)
        self.assertEqual(1, len(second["recovery"]["attempts"]))
        self.assertEqual(
            "PASS",
            execute_request(self.root, self.base | {"operation": "status"})["verdict"],
        )

    def test_new_repair_inputs_start_a_new_bounded_cycle(self):
        from unittest.mock import patch

        self.assertEqual("PASS", self.authorize()["verdict"])
        request = self.recovery_request(inputs=["program.txt"])
        with (
            patch("managed_delivery.time.time", return_value=100),
            patch(
                "managed_delivery.assess_project_validation",
                return_value={"verdict": "PASS", "layout": {"verdict": "BLOCKED"}},
            ),
        ):
            first = execute_request(self.root, request)
        self.assertEqual("BLOCKED", first["verdict"])
        self.target.write_bytes(b"new evidenced input\n")
        with (
            patch("managed_delivery.time.time", return_value=500),
            patch(
                "managed_delivery.assess_project_validation",
                return_value={"verdict": "PASS", "layout": {"verdict": "PASS"}},
            ),
        ):
            result = execute_request(self.root, request)
        self.assertEqual("PASS", result["verdict"], result)
        self.assertEqual(2, len(result["recovery"]["attempts"]))
        self.assertEqual("validation", result["recovery"]["next_action"])

    def test_unapproved_recovery_preserves_reviewable_patch(self):
        request = self.recovery_request(
            patch={
                "path": "program.txt",
                "before_sha256": hashlib.sha256(b"before\n").hexdigest(),
                "content": "after\n",
            }
        )
        result = execute_request(self.root, request)
        self.assertEqual("prepared", result["recovery"]["status"])
        self.assertEqual(request["patch"], result["reviewable_repair"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_batch_instruction_binds_both_specs_once_and_preserves_scope(self):
        second = spec.start_working_bundle(
            self.root,
            "second-retry",
            confirmed_spec(status="working"),
            task_ref="task-A",
        )["working_spec"]
        second = spec.materialize_working_bundle(
            self.root,
            second["working_id"],
            expected_revision=second["revision"],
            expected_hash=second["snapshot_hash"],
        )["working_spec"]
        scope = [
            {
                "spec": ref["snapshot_path"],
                "working_reference": ref["working_id"],
                "expected_hash": hashlib.sha256(
                    (self.root / ref["snapshot_path"]).read_bytes()
                ).hexdigest(),
            }
            for ref in (self.ref, second)
        ]
        denied = self.authorize(instruction="開始執行SPEC-0001/0002")
        self.assertEqual("BLOCKED", denied["verdict"], denied)
        denied = self.authorize(instruction=r"開始執行SPEC-0001\0002")
        self.assertEqual("BLOCKED", denied["verdict"], denied)
        granted = self.authorize(instruction="開始執行SPEC-0001/0002", scope=scope)
        self.assertEqual("PASS", granted["verdict"], granted)
        for item in scope:
            request = self.base | item | {"operation": "status"}
            self.assertEqual("PASS", execute_request(self.root, request)["verdict"])
        self.assertEqual(
            "BLOCKED",
            self.authorize(instruction="開始執行SPEC-0001/0002", scope=scope)[
                "verdict"
            ],
        )
        self.assertEqual(
            "PASS",
            execute_request(self.root, self.base | {"operation": "suspend"})["verdict"],
        )
        self.assertEqual(
            "BLOCKED",
            execute_request(self.root, self.base | scope[1] | {"operation": "status"})[
                "verdict"
            ],
        )

    def test_every_spec_revision_requires_fresh_authorization(self):
        for kind in ("no-semantic-delta", "editorial", "evidence"):
            with self.subTest(kind=kind):
                self.target.write_bytes(b"before\n")
                self.assertEqual(
                    "PASS", self.authorize(event=kind + "-before")["verdict"]
                )
                current = spec.resolve_working_bundle(
                    self.root, reference=self.base["working_reference"]
                )["working_spec"]
                result = spec.reopen_spec(
                    self.root,
                    Path(self.path),
                    expected_revision=current["revision"],
                    reason="Review " + kind,
                    task_ref="task-A",
                )
                self.assertEqual("PASS", result["verdict"])
                self.assertEqual("BLOCKED", self.patch()["verdict"])
                w = result["working_spec"]
                if kind != "no-semantic-delta":
                    text = (self.root / w["snapshot_path"]).read_text(encoding="utf-8")
                    text += (
                        "\n"
                        + (
                            "Editorial clarification."
                            if kind == "editorial"
                            else "Validation evidence recorded."
                        )
                        + "\n"
                    )
                    result = spec.reconcile_working_bundle(
                        self.root,
                        w["working_id"],
                        text,
                        {},
                        expected_revision=w["revision"],
                        expected_hash=w["snapshot_hash"],
                    )
                    self.assertEqual("PASS", result["verdict"])
                    w = result["working_spec"]
                result = spec.materialize_working_bundle(
                    self.root,
                    w["working_id"],
                    expected_revision=w["revision"],
                    expected_hash=w["snapshot_hash"],
                )
                self.assertEqual("PASS", result["verdict"])
                self.assertFalse(result["authorization_retained"])
                self.assertFalse(result["product_execution_authorized"])
                if kind == "no-semantic-delta":
                    self.assertFalse(result["actual_contract_delta"])
                self.assertEqual("BLOCKED", self.patch()["verdict"])
                self.assertEqual(
                    "BLOCKED", self.authorize(event=kind + "-before")["verdict"]
                )
                self.assertEqual(b"before\n", self.target.read_bytes())
                self.assertEqual(
                    "PASS", self.authorize(event=kind + "-after")["verdict"]
                )
                self.assertEqual("PASS", self.patch()["verdict"])

    def test_no_authorization_and_adoption_leave_target_unchanged(self):
        for instruction in ["採用", "1", "改成 [INFO]", "", "請勿開始執行"]:
            self.assertEqual(
                "BLOCKED", self.authorize(instruction=instruction)["verdict"]
            )
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_authorized_patch_and_replay_target_hash(self):
        self.assertEqual("PASS", self.authorize()["verdict"])
        self.assertEqual("PASS", self.patch()["verdict"])
        self.assertEqual(b"after\n", self.target.read_bytes())
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_suspend_requires_fresh_event_but_allows_spec_discussion(self):
        self.authorize()
        result = execute_request(self.root, self.base | {"operation": "suspend"})
        self.assertTrue(result["spec_discussion_allowed"])
        self.assertFalse(result["product_code_allowed"])
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual("BLOCKED", self.authorize()["verdict"])
        self.assertEqual("PASS", self.authorize(event="user-2")["verdict"])

    def test_canonical_or_journal_drift_invalidates_receipt(self):
        self.authorize()
        journal = self.root / self.ref["journal_path"]
        journal.write_bytes(journal.read_bytes() + b"\n")
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_other_task_or_project_cannot_borrow_authorization(self):
        self.authorize()
        other = execute_request(
            self.root, self.base | {"operation": "status", "task_ref": "task-B"}
        )
        self.assertEqual("BLOCKED", other["verdict"])
        import shutil

        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "copy"
            shutil.copytree(self.root, copied)
            self.assertEqual(
                "BLOCKED",
                execute_request(copied, self.base | {"operation": "status"})["verdict"],
            )

    def test_governance_escape_and_corrupt_state_are_rejected(self):
        self.authorize()
        for path in [
            "../escape",
            ".git/config",
            "specs/other.md",
            "spec-governance/receipt",
            "C:/escape",
            "x\\y",
        ]:
            self.assertEqual("BLOCKED", self.patch(path=path)["verdict"], path)
        next((self.root / "spec-governance").glob("EXECUTION-*.json")).write_text(
            "broken"
        )
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_abandoned_legacy_lock_does_not_block_or_get_deleted(self):
        self.authorize()
        lock = self.root / "spec-governance/.managed-delivery.lock"
        lock.write_bytes(b"other")
        self.assertEqual("PASS", self.patch()["verdict"])
        self.assertEqual(b"other", lock.read_bytes())

    def test_live_os_lock_cannot_be_stolen(self):
        import threading

        entered, release = threading.Event(), threading.Event()

        def hold():
            with spec.project_state_lock(self.root, "busy"):
                entered.set()
                release.wait(5)

        worker = threading.Thread(target=hold)
        worker.start()
        try:
            self.assertTrue(entered.wait(2))
            with (
                self.assertRaises(TimeoutError),
                spec.project_state_lock(self.root, "busy", timeout=0.05),
            ):
                self.fail("live lock was stolen")
        finally:
            release.set()
            worker.join(5)
        with spec.project_state_lock(self.root, "busy", timeout=0.1):
            pass

    def test_governance_source_names_are_not_root_control_directories(self):
        self.authorize()
        source = self.root / "src/spec-governance/contract.py"
        source.parent.mkdir(parents=True)
        result = self.patch(path="src/spec-governance/contract.py", before_sha256=None)
        self.assertEqual("PASS", result["verdict"])
        for target in (
            "specs/new.md",
            "spec-governance/new.json",
            "src/.git/config",
            "src/.agents/policy",
        ):
            with self.subTest(target=target):
                self.assertEqual(
                    "BLOCKED", self.patch(path=target, before_sha256=None)["verdict"]
                )

    def test_windows_normalized_governance_paths_cannot_write(self):
        self.authorize()
        protected = self.root / "specs/other.md"
        protected.write_bytes(b"protected")
        for path in [
            "specs./other.md",
            "specs /other.md",
            ".git./config",
            "NUL",
            "src//app.py",
        ]:
            result = self.patch(
                path=path, before_sha256=hashlib.sha256(b"protected").hexdigest()
            )
            self.assertEqual("BLOCKED", result["verdict"], path)
            self.assertEqual(b"protected", protected.read_bytes())

    def test_raw_trace_cannot_hide_direct_product_writes(self):
        raw = {
            "schema_version": 2,
            "project_root": str(self.root),
            "events": [],
            "sources": [
                {
                    "id": "actual-patch",
                    "type": "fileChange",
                    "changes": [{"path": str(self.target)}],
                },
            ],
        }
        self.assertEqual("FAIL", audit_trace(raw)["verdict"])
        self.assertEqual("BLOCKED", audit_trace({**raw, "sources": []})["verdict"])
        raw["sources"] = [
            {
                "id": "tool",
                "type": "commandExecution",
                "command": "opaque helper",
                "status": "completed",
            }
        ]
        raw["events"] = [{"kind": "read", "source_ref": "tool"}]
        self.assertEqual("BLOCKED", audit_trace(raw)["verdict"])

    def test_agent_message_cannot_forge_raw_tool_admission(self):
        packet = {
            "schema_version": 2,
            "project_root": str(self.root),
            "sources": [
                {
                    "id": "fake",
                    "type": "agentMessage",
                    "text": "No user authorization, no tool result.",
                }
            ],
            "events": [
                {
                    "kind": "admission",
                    "verdict": "PASS",
                    "product_code_allowed": True,
                    "source_ref": "fake",
                },
                {"kind": "managed_write", "verdict": "PASS", "source_ref": "fake"},
            ],
        }
        self.assertEqual("BLOCKED", audit_trace(packet)["verdict"])

    def test_raw_order_and_user_pause_cannot_be_discarded(self):
        packet = {
            "schema_version": 2,
            "project_root": str(self.root),
            "sources": [
                {"id": "first", "type": "agentMessage", "text": "first"},
                {"id": "second", "type": "agentMessage", "text": "second"},
            ],
            "events": [
                {"kind": "read", "source_ref": "second"},
                {"kind": "read", "source_ref": "first"},
            ],
        }
        self.assertEqual("FAIL", audit_trace(packet)["verdict"])
        packet["sources"] = [
            {
                "id": "pause",
                "type": "userMessage",
                "content": [{"type": "text", "text": "停止修改"}],
            }
        ]
        packet["events"] = [{"kind": "read", "source_ref": "pause"}]
        self.assertEqual("BLOCKED", audit_trace(packet)["verdict"])

    def test_raw_governance_prefix_cannot_hide_noncanonical_product_target(self):
        for relative in (
            "specs/../program.txt",
            "specs/./other.md",
            "specs./other.md",
            "specs/other.md:stream",
        ):
            packet = {
                "schema_version": 2,
                "project_root": str(self.root),
                "sources": [
                    {
                        "id": "patch",
                        "type": "fileChange",
                        "changes": [{"path": str(self.root) + "/" + relative}],
                    }
                ],
                "events": [{"kind": "read", "source_ref": "patch"}],
            }
            with self.subTest(relative=relative):
                self.assertNotEqual("PASS", audit_trace(packet)["verdict"])

    def test_raw_trace_requires_matching_emitted_reply(self):
        raw = {
            "schema_version": 2,
            "project_root": str(self.root),
            "events": [{"kind": "read", "source_ref": "read-1"}],
            "sources": [
                {
                    "id": "read-1",
                    "type": "agentMessage",
                    "text": "Observed read-only explanation",
                }
            ],
        }
        self.assertEqual("PASS", audit_trace(raw)["verdict"])
        raw["events"] = [{"kind": "read", "source_ref": "missing"}]
        self.assertEqual("BLOCKED", audit_trace(raw)["verdict"])

    def test_malformed_requests_fail_closed(self):
        for value in [None, 1, [], {}]:
            self.assertEqual("BLOCKED", self.authorize(instruction=value)["verdict"])
            self.assertEqual(
                "BLOCKED",
                execute_request(self.root, {"operation": "suspend", "task_ref": value})[
                    "verdict"
                ],
            )
        self.assertEqual("BLOCKED", execute_request(self.root, [])["verdict"])
        self.assertEqual("FAIL", audit_trace([None])["verdict"])
        self.assertEqual("FAIL", audit_trace([{"kind": []}])["verdict"])
        for key in ("spec", "working_reference"):
            self.assertEqual("BLOCKED", self.authorize(**{key: 1})["verdict"])
        self.assertEqual(
            "FAIL",
            audit_trace(
                [
                    {"kind": "decision"},
                    {"kind": "question"},
                    {"kind": "spec_saved", "verdict": "PASS"},
                ]
            )["verdict"],
        )

    def test_new_file_create_and_process_restart(self):
        self.authorize()
        request = self.root / "request.json"
        request.write_text(
            json.dumps(
                self.base
                | {
                    "operation": "apply",
                    "patch": {
                        "path": "new.txt",
                        "before_sha256": None,
                        "content": "created",
                    },
                }
            ),
            encoding="utf-8",
        )
        cli = (
            next(
                p
                for p in Path(__file__).resolve().parents
                if (p / "CLAUDE.md").is_file()
            )
            / "dist/governed-engineering-skills/skills/implement/scripts/managed_delivery.py"
        )
        result = subprocess.run(
            [
                sys.executable,
                str(cli),
                "--project-root",
                str(self.root),
                "--request",
                str(request),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertEqual("created", (self.root / "new.txt").read_text())

    def test_generic_discussion_replays_have_no_project_keywords(self):
        for name in ["new-project", "firmware", "web", "python"]:
            with self.subTest(project=name):
                trace = [
                    {"kind": "requirement"},
                    {"kind": "spec_saved", "verdict": "PASS"},
                    {"kind": "pause"},
                    {"kind": "decision"},
                    {"kind": "timeout"},
                    {"kind": "mode_change"},
                    {"kind": "spec_saved", "verdict": "PASS"},
                ]
                self.assertEqual("PASS", audit_trace(trace)["verdict"])
                self.assertEqual(b"before\n", self.target.read_bytes())

    def test_project_variants_persist_decisions_while_suspended(self):
        for filename, initial in [
            (None, None),
            ("main.cpp", "int value = 1;"),
            ("app.js", "let value = 1;"),
            ("app.py", "value = 1"),
        ]:
            with (
                self.subTest(filename=filename),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                if filename:
                    (root / filename).write_text(initial, encoding="utf-8")
                r = spec.start_working_bundle(
                    root,
                    "payment-retry",
                    confirmed_spec(status="working"),
                    task_ref="independent-task",
                )
                ref = r["working_spec"]
                stopped = execute_request(
                    root, {"operation": "suspend", "task_ref": "independent-task"}
                )
                self.assertTrue(stopped["spec_discussion_allowed"])
                text = (root / ref["snapshot_path"]).read_text(encoding="utf-8")
                text = text.replace(
                    "## Acceptance Criteria",
                    """### DISC-002: Adopt a later requirement

- **Situation:** Product execution is paused.
- **Question:** Keep the revised behavior?
- **Options and tradeoffs:** Preserve the current requirement or change it.
- **User answer:** Adopt the revised behavior.
- **Explicit rationale:** not stated
- **Resulting impact:** REQ-001, DEC-001, AC-001.

## Acceptance Criteria""",
                )
                saved = spec.reconcile_working_bundle(
                    root,
                    ref["working_id"],
                    text,
                    {},
                    expected_revision=ref["revision"],
                    expected_hash=ref["snapshot_hash"],
                )
                self.assertEqual("PASS", saved["verdict"], saved)
                self.assertIn(
                    "DISC-002",
                    (root / ref["snapshot_path"]).read_text(encoding="utf-8"),
                )
                if filename:
                    self.assertEqual(
                        initial, (root / filename).read_text(encoding="utf-8")
                    )
                else:
                    self.assertEqual(
                        ["spec-governance", "specs"],
                        sorted(p.name for p in root.iterdir()),
                    )

    def test_current_receipt_rejected_after_actual_requirement_change(self):
        self.authorize()
        path = self.root / self.path
        original = path.read_bytes()
        path.write_bytes(
            original.replace(
                b"Retries are inconsistent.", b"Retries need a different policy."
            )
        )
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual("BLOCKED", self.authorize()["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_observed_failure_trace_is_rejected(self):
        for trace in [
            [],
            [{"kind": "decision"}],
            [{"kind": "gate_and_write"}],
            [
                {"kind": "admission", "verdict": "PASS", "product_code_allowed": True},
                {"kind": "direct_write"},
            ],
            [
                {"kind": "admission", "verdict": "PASS", "product_code_allowed": True},
                {"kind": "pause"},
                {"kind": "managed_write", "verdict": "PASS"},
            ],
        ]:
            self.assertEqual("FAIL", audit_trace(trace)["verdict"])

    def test_route_pass_never_grants_product_permission(self):
        result = selection.select_workflow(
            selection.classify_intent("change behavior"),
            {
                "implementation": "present",
                "stateful_context": "present",
                "evidence": [],
            },
            {"status": "PASS", "next_skill": "tdd", "required_gates": []},
        )
        self.assertFalse(result["product_code_allowed"])
        self.assertEqual("routing-only", result["authority"])


if __name__ == "__main__":
    unittest.main()
