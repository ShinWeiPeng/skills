from __future__ import annotations

import unittest
from pathlib import Path

import test_managed_delivery as delivery
from test_managed_delivery import execute_request
from discussion_state import discussion_request


class FixContractReviewTests(unittest.TestCase):
    setUp = delivery.ManagedDeliveryTests.setUp
    authorize = delivery.ManagedDeliveryTests.authorize
    patch = delivery.ManagedDeliveryTests.patch

    def enter(self, turn="diagnosis", prompt="Investigate Reset failure"):
        self.turn = turn
        return discussion_request(
            self.root,
            dict(
                operation="enter",
                task_ref="task-A",
                turn_id=turn,
                prompt=prompt,
                source_ref="user-" + turn,
                engineering=True,
                working_reference=self.base["working_reference"],
            ),
        )

    def owner(self, operation, **fields):
        state = discussion_request(
            self.root,
            dict(
                operation="status",
                task_ref="task-A",
                turn_id=self.turn,
            ),
        )
        return discussion_request(
            self.root,
            dict(
                operation=operation,
                task_ref="task-A",
                turn_id=self.turn,
                binding=state["binding"],
                **fields,
            ),
        )

    def save(self):
        state = self.owner("status")
        self.owner("observe", source_refs=state["source_refs"], items=[])
        return self.owner(
            "record",
            source_ref="assistant-" + self.turn,
            summary="Read-only diagnosis; no adopted change.",
            reply_text="Diagnosed the failure; fix review follows.",
            candidates=[],
            item_bindings={},
        )

    def propose(
        self,
        text="Retry the failed operation using the existing retry limit.",
        source="diagnosis-1",
    ):
        return self.owner("propose-fix", fix_id="FIX-001", fix=text, source_ref=source)

    def test_fix_requires_current_comparison(self):
        self.assertEqual("PASS", self.authorize()["verdict"])
        self.enter()
        self.assertEqual("PASS", self.propose()["verdict"])
        self.assertEqual("PASS", self.save()["verdict"])
        result = self.patch()
        self.assertEqual("BLOCKED", result["verdict"], result)
        self.assertIn("fix comparison", result["reason"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def dimensions(self, status="covered"):
        return {
            name: {
                "status": status,
                "rationale": "The existing retry bound is preserved.",
                "clauses": [{"id": "REQ-001", "text": "Retry at most three times."}],
            }
            for name in (
                "applicable_states",
                "ordering",
                "success",
                "failure",
                "rollback",
                "retry",
            )
        }

    def compare(self, proposal, **changes):
        return self.owner(
            "compare-fix",
            fix_id="FIX-001",
            proposal_event_hash=proposal["proposal_event_hash"],
            source_ref="assistant-comparison",
            presentation_ref="visible-comparison",
            summary="All six behaviors retain the existing contract.",
            **({"dimensions": self.dimensions()} | changes),
        )

    def prepare(self):
        self.assertEqual("PASS", self.authorize()["verdict"])
        self.enter()
        return self.propose()

    def test_covered_fix_keeps_authority(self):
        from execution_state import read_execution_state

        proposal = self.prepare()
        original = read_execution_state(self.root, "task-A")["receipt"]
        self.assertEqual("PASS", self.compare(proposal)["verdict"])
        self.save()
        self.assertEqual("PASS", self.patch()["verdict"])
        self.assertEqual(original, read_execution_state(self.root, "task-A")["receipt"])

    def test_comparison_rejects_invalid_citations(self):
        proposal = self.prepare()
        for key, value in (
            ("id", "REQ-999"),
            ("text", "Retries always restart sampling."),
            ("text", "REQ-001"),
        ):
            with self.subTest(key=key, value=value):
                dimensions = self.dimensions()
                dimensions["retry"]["clauses"][0][key] = value
                with self.assertRaisesRegex(ValueError, "behavioral clause"):
                    self.compare(proposal, dimensions=dimensions)
        self.save()
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_incomplete_comparison_rejects(self):
        proposal = self.prepare()
        dimensions = self.dimensions()
        del dimensions["rollback"]
        with self.assertRaisesRegex(ValueError, "six"):
            self.compare(proposal, dimensions=dimensions)
        dimensions = self.dimensions()
        dimensions["failure"]["clauses"] = []
        with self.assertRaisesRegex(ValueError, "actual contract"):
            self.compare(proposal, dimensions=dimensions)

    def test_stale_or_noncovered_fix_blocks(self):
        proposal = self.prepare()
        for status in ("changed", "unknown"):
            dimensions = self.dimensions()
            dimensions["failure"] = {
                "status": status,
                "rationale": "Reset restart policy is not established.",
                "clauses": [],
            }
            result = self.compare(proposal, dimensions=dimensions)
            self.assertEqual("BLOCKED", result["verdict"])
            self.assertFalse(result["product_code_allowed"])
            self.save()
            self.assertEqual("BLOCKED", self.patch()["verdict"])
            self.assertEqual(b"before\n", self.target.read_bytes())

    def test_new_fix_cannot_reuse_previous_comparison(self):
        proposal = self.prepare()
        self.compare(proposal)
        next_proposal = self.propose(
            "Allow Reset staging only when stopped.", "diagnosis-2"
        )
        self.assertNotEqual(
            proposal["proposal_event_hash"], next_proposal["proposal_event_hash"]
        )
        with self.assertRaisesRegex(ValueError, "latest exact proposal"):
            self.compare(proposal)
        self.save()
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_stale_binding_cannot_append_comparison(self):
        proposal = self.prepare()
        binding = self.owner("status")["binding"]
        with self.assertRaisesRegex(ValueError, "binding"):
            discussion_request(
                self.root,
                dict(
                    operation="compare-fix",
                    task_ref="task-A",
                    turn_id=self.turn,
                    binding=binding | {"revision": binding["revision"] + 1},
                    fix_id="FIX-001",
                    source_ref="stale",
                    proposal_event_hash=proposal["proposal_event_hash"],
                    dimensions=self.dimensions(),
                    summary="Stale",
                    presentation_ref="stale",
                ),
            )

    def test_unchanged_retry_and_history_preserve_comparison(self):
        proposal = self.prepare()
        self.compare(proposal)
        self.assertTrue(self.propose()["replayed"])
        self.assertTrue(self.compare(proposal)["replayed"])
        self.save()
        for _ in range(3):
            result = execute_request(self.root, self.base | {"operation": "status"})
            self.assertEqual("PASS", result["verdict"], result)
        self.enter("retest", "Retry the same test without changing the fix")
        self.save()
        self.assertEqual("PASS", self.patch()["verdict"])

    def test_factual_followup_preserves_pending_fix(self):
        from test_turn_continuity import spec

        self.prepare()
        reopened = spec.reopen_spec(
            self.root,
            Path(self.path),
            expected_revision=self.ref["revision"],
            reason="Confirm Reset staging and failure behavior",
        )
        self.assertEqual("PASS", reopened["verdict"], reopened)
        w = reopened["working_spec"]
        result = spec.record_question(
            self.root,
            w["working_id"],
            "Q-reset",
            "Reset 停止採樣後是否允許 staging，再完整重啟？",
            [],
            expected_revision=w["revision"],
            expected_hash=w["snapshot_hash"],
            question_kind="open-text",
        )
        self.assertEqual("BLOCKED", result["verdict"])
        before = spec.assess_turn_context(
            self.root, reference=w["working_id"], task_ref="task-A"
        )["pending_question"]
        for turn, prompt in (
            ("why", "我想了解為什麼會套用失敗？"),
            ("timeout", "No answer received"),
            ("mode", "已切回自動模式"),
        ):
            self.enter(turn, prompt)
            self.save()
            after = spec.assess_turn_context(
                self.root, reference=w["working_id"], task_ref="task-A"
            )["pending_question"]
            self.assertEqual(before, after)
            self.assertEqual("BLOCKED", self.patch()["verdict"])
            self.assertEqual(b"before\n", self.target.read_bytes())

    def test_contract_revision_stales_covered_comparison(self):
        from test_turn_continuity import spec
        from discussion_state import assess_fix_comparisons

        proposal = self.prepare()
        self.compare(proposal)
        self.save()
        result = spec.reopen_spec(
            self.root,
            Path(self.path),
            expected_revision=self.ref["revision"],
            reason="Review a changed failure policy",
        )
        self.assertEqual("PASS", result["verdict"])
        review = assess_fix_comparisons(self.root, result["working_spec"], "task-A")
        self.assertEqual("BLOCKED", review["verdict"])
        self.assertEqual("missing-or-stale", review["fixes"]["FIX-001"]["status"])
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_observed_fix_trace_rejects_factual_followup_write(self):
        from managed_delivery import audit_trace

        proposal = self.prepare()
        events = [
            dict(kind="admission", verdict="PASS", product_code_allowed=True),
            dict(
                kind="fix_proposed",
                fix_id="FIX-001",
                proposal_event_hash=proposal["proposal_event_hash"],
                binding=self.owner("status")["binding"],
            ),
            dict(kind="read", text="我想了解為什麼會套用失敗？"),
            dict(kind="managed_write", verdict="PASS"),
        ]
        result = audit_trace(events)
        self.assertEqual("FAIL", result["verdict"])
        self.assertTrue(
            any("fix comparison" in row["reason"] for row in result["violations"])
        )

    def test_observed_covered_fix_does_not_grant_authority(self):
        from managed_delivery import audit_trace

        proposal = self.prepare()
        review = self.compare(proposal)
        events = [
            dict(
                kind="fix_proposed",
                fix_id="FIX-001",
                proposal_event_hash=proposal["proposal_event_hash"],
                binding=self.owner("status")["binding"],
            ),
            dict(kind="fix_comparison", review=review),
            dict(kind="managed_write", verdict="PASS"),
        ]
        self.assertEqual("FAIL", audit_trace(events)["verdict"])
        events.insert(
            2, dict(kind="admission", verdict="PASS", product_code_allowed=True)
        )
        self.assertEqual("PASS", audit_trace(events)["verdict"])

    def admission(self, task=None):
        import hashlib
        from spec_delivery import verify_delivery_admission

        return verify_delivery_admission(
            self.root,
            self.path,
            expected_hash=hashlib.sha256(
                (self.root / self.path).read_bytes()
            ).hexdigest(),
            authorization="開始執行",
            working_reference=self.base["working_reference"],
            task_ref=task,
        )

    def test_public_admission_cannot_skip_review_by_omitting_task(self):
        proposal = self.prepare()
        self.save()
        self.assertEqual("BLOCKED", self.admission()["verdict"])
        self.assertEqual("BLOCKED", self.admission("task-B")["verdict"])
        self.compare(proposal)
        self.save()
        self.assertEqual("PASS", self.admission()["verdict"])
        self.assertEqual("PASS", self.admission("task-A")["verdict"])
        self.assertEqual("BLOCKED", self.admission("task-B")["verdict"])

    def test_observed_same_binding_save_preserves_covered_fix(self):
        from managed_delivery import audit_trace

        proposal = self.prepare()
        review = self.compare(proposal)
        binding = self.owner("status")["binding"]
        events = [
            dict(
                kind="fix_proposed",
                fix_id="FIX-001",
                proposal_event_hash=proposal["proposal_event_hash"],
                binding=binding,
            ),
            dict(kind="fix_comparison", review=review),
            dict(kind="spec_saved", verdict="PASS", binding=binding),
            dict(kind="admission", verdict="PASS", product_code_allowed=True),
            dict(kind="managed_write", verdict="PASS"),
        ]
        self.assertEqual("PASS", audit_trace(events)["verdict"])
        events[2]["binding"] = binding | {"revision": binding["revision"] + 1}
        self.assertEqual("FAIL", audit_trace(events)["verdict"])

    def test_observed_noncovered_review_allows_discussion_only(self):
        from managed_delivery import audit_trace

        proposal = self.prepare()
        review = self.compare(proposal, dimensions=self.dimensions("unknown"))
        events = [
            dict(
                kind="fix_proposed",
                fix_id="FIX-001",
                proposal_event_hash=proposal["proposal_event_hash"],
                binding=self.owner("status")["binding"],
            ),
            dict(kind="fix_comparison", review=review),
            dict(kind="read"),
        ]
        self.assertEqual("PASS", audit_trace(events)["verdict"])
        events.extend(
            [
                dict(kind="admission", verdict="PASS", product_code_allowed=True),
                dict(kind="managed_write", verdict="PASS"),
            ]
        )
        self.assertEqual("FAIL", audit_trace(events)["verdict"])
        events[1]["review"] = review | {
            "fixes": {"FIX-001": review["fixes"]["FIX-001"] | {"status": "covered"}}
        }
        self.assertEqual("FAIL", audit_trace(events)["verdict"])
        events[1]["review"] = review | {"fixes": {"FIX-001": []}}
        self.assertEqual("FAIL", audit_trace(events)["verdict"])

    def test_comparison_survives_process_restart_but_new_fix_does_not(self):
        import json, subprocess, sys
        from managed_delivery import __file__ as writer

        proposal = self.prepare()
        self.compare(proposal)
        self.save()
        request = self.root / "spec-governance/fixture-status.json"
        request.write_text(
            json.dumps(self.base | {"operation": "status"}), encoding="utf-8"
        )

        def status():
            process = subprocess.run(
                [
                    sys.executable,
                    writer,
                    "--project-root",
                    str(self.root),
                    "--request",
                    str(request),
                ],
                capture_output=True,
                text=True,
            )
            return json.loads(process.stdout)

        self.assertEqual("PASS", status()["verdict"])
        self.propose("Change the failure recovery sequence.", "diagnosis-after-restart")
        self.save()
        self.assertEqual("BLOCKED", status()["verdict"])

    def test_comparison_replay_after_full_reconciliation_is_rejected(self):
        from test_turn_continuity import spec
        from discussion_state import assess_fix_comparisons

        proposal = self.prepare()
        self.compare(proposal)
        self.save()
        result = spec.reopen_spec(
            self.root,
            Path(self.path),
            expected_revision=self.ref["revision"],
            reason="Change the adopted retry bound",
        )
        working = result["working_spec"]
        path = self.root / working["snapshot_path"]
        changed = path.read_text(encoding="utf-8").replace(
            "Retry at most three times.", "Retry at most two times."
        )
        reconciled = spec.reconcile_working_bundle(
            self.root,
            working["working_id"],
            changed,
            {},
            expected_revision=working["revision"],
            expected_hash=working["snapshot_hash"],
        )
        self.assertEqual("PASS", reconciled["verdict"], reconciled)
        self.assertEqual(
            "BLOCKED",
            assess_fix_comparisons(self.root, reconciled["working_spec"], "task-A")[
                "verdict"
            ],
        )
        with self.assertRaisesRegex(ValueError, "behavioral clause"):
            self.compare(proposal)
        self.assertEqual("BLOCKED", self.patch()["verdict"])


if __name__ == "__main__":
    unittest.main()
