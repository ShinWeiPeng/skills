from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from test_spec_governance import confirmed_spec


ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "dist/governed-engineering-skills/skills"
sys.path.insert(0, str(PLUGIN / "spec-governance/scripts"))
sys.path.insert(0, str(PLUGIN / "implement/scripts"))
sys.path.insert(0, str(PLUGIN / "engineering-risk-routing/scripts"))
import spec_contract as spec
import spec_delivery as delivery
import workflow_selection as selection
import guided_workflow_router as router


class TurnContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        result = spec.start_working_bundle(
            self.root,
            "payment-retry",
            confirmed_spec(status="working"),
            task_ref="task-A",
        )
        self.ref = result["working_spec"]
        self.wid = self.ref["working_id"]

    def reload(self):
        self.ref = spec.resolve_working_bundle(self.root, reference=self.wid)[
            "working_spec"
        ]
        return (self.root / self.ref["snapshot_path"]).read_text(encoding="utf-8")

    def question(self):
        result = spec.record_question(
            self.root,
            self.wid,
            "Q-tracking",
            "保留哪些檔案？",
            ["保留追蹤", "保留本機、排除 commit"],
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.reload()
        return result

    def answer(self, answer="保留本機、排除 commit", version=None):
        text = self.reload()
        question = spec.pending_decision(text)
        text = text.replace(
            "## Acceptance Criteria",
            f"""### DISC-002: Tracking answer

- **Situation:** The pending tracking choice needs an answer.
- **Question:** 保留哪些檔案？
- **Options and tradeoffs:** 保留追蹤 or 保留本機、排除 commit.
- **User answer:** {answer}
- **Explicit rationale:** not stated
- **Resulting impact:** REQ-001, DEC-001, AC-001.

## Acceptance Criteria""",
        )
        return spec.reconcile_working_bundle(
            self.root,
            self.wid,
            text,
            {},
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
            question_id="Q-tracking",
            question_version=version if version is not None else question["version"],
            answer=answer,
        )

    def materialize(self):
        self.reload()
        return spec.materialize_working_bundle(
            self.root,
            self.wid,
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )

    def route(self, prompt, kind="auto"):
        return selection.select_workflow(
            selection.classify_intent(prompt),
            {
                "implementation": "present",
                "stateful_context": "present",
                "evidence": [],
            },
            {"status": "PASS", "next_skill": "tdd", "required_gates": []},
            turn_context=spec.assess_turn_context(
                self.root, reference=self.wid, task_ref="task-A"
            ),
            turn_kind=kind,
        )

    def test_process_restart_retains_exact_options_without_deadline(self):
        self.question()
        result = subprocess.run(
            [
                sys.executable,
                str(PLUGIN / "spec-governance/scripts/spec_contract.py"),
                "turn-context",
                "--project-root",
                str(self.root),
                "--task-ref",
                "task-A",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        context = json.loads(result.stdout)
        self.assertEqual("pending", context["state"])
        self.assertEqual(
            ["保留追蹤", "保留本機、排除 commit"],
            context["pending_question"]["options"],
        )
        self.assertNotIn("deadline", context["pending_question"])
        self.assertIsNone(context["presentation"]["response_deadline"])
        self.assertFalse(context["presentation"]["request_mode_change"])
        self.assertEqual(
            "保留哪些檔案？\n\n1. 保留追蹤\n2. 保留本機、排除 commit",
            context["presentation"]["markdown"],
        )
        with mock.patch.object(spec, "datetime") as clock:
            clock.now.side_effect = AssertionError(
                "Question recovery must not depend on a clock"
            )
            self.assertEqual(
                context, spec.assess_turn_context(self.root, task_ref="task-A")
            )

    def test_empty_timeout_mode_change_and_short_answer_do_not_admit_delivery(self):
        self.question()
        for prompt in [
            "",
            "timeout",
            "Default",
            "1",
            "採用",
            "開始執行",
            "保留本機、排除 commit",
        ]:
            with self.subTest(prompt=prompt):
                result = self.route(prompt)
                self.assertEqual("BLOCKED", result["status"])
                self.assertEqual("spec-governance", result["selected_skill"])
        self.assertIsNotNone(spec.pending_decision(self.reload()))

    def test_factual_followup_preserves_question(self):
        self.question()
        result = self.route("companion 的功能是什麼？", "read-only")
        self.assertEqual("PASS", result["status"])
        self.assertEqual("explain-code-flow", result["selected_skill"])
        self.assertIsNotNone(spec.pending_decision(self.reload()))

    def test_question_cannot_be_replaced_or_silently_removed(self):
        self.question()
        text = self.reload()
        result = spec.reconcile_working_bundle(
            self.root,
            self.wid,
            spec._replace_pending_decision(text, None),
            {},
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertEqual(text, self.reload())
        self.assertEqual("BLOCKED", self.materialize()["verdict"])

    def test_stale_and_empty_answers_do_not_change_state(self):
        self.question()
        before = self.reload()
        self.assertEqual("BLOCKED", self.answer(version=999)["verdict"])
        self.assertEqual("BLOCKED", self.answer(answer="")["verdict"])
        self.assertEqual(before, self.reload())

    def test_answer_reconciles_once_and_materializes(self):
        self.question()
        self.assertEqual("PASS", self.answer()["verdict"])
        text = self.reload()
        self.assertIsNone(spec.pending_decision(text))
        result = spec.reconcile_working_bundle(
            self.root,
            self.wid,
            text,
            {},
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
            question_id="Q-tracking",
            question_version=2,
            answer="保留本機、排除 commit",
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertEqual("PASS", self.materialize()["verdict"])

    def test_task_mismatch_and_malformed_state_fail_closed(self):
        self.question()
        self.assertEqual(
            "invalid",
            spec.assess_turn_context(self.root, reference=self.wid, task_ref="task-B")[
                "state"
            ],
        )
        path = self.root / self.ref["snapshot_path"]
        path.write_text(
            self.reload().replace('"version": 2', '"version": "bad"'), encoding="utf-8"
        )
        self.assertEqual(
            "invalid", spec.assess_turn_context(self.root, reference=self.wid)["state"]
        )

    def test_conflict_survives_answer_and_blocks_confirmation(self):
        self.question()
        self.assertEqual("PASS", self.answer()["verdict"])
        text = self.reload().replace(
            "| REQ-001 | depends_on | DEC-001 |",
            "| REQ-001 | conflicts_with | DEC-001 |",
        )
        result = spec.reconcile_working_bundle(
            self.root,
            self.wid,
            text,
            {},
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertTrue(result["conflicts"])
        self.assertEqual("BLOCKED", self.materialize()["verdict"])

    def test_delivery_requires_explicit_authorization_and_current_verified_spec(self):
        self.question()
        self.answer()
        result = self.materialize()
        relative = result["canonical_spec"]["path"]
        path = self.root / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        for authorization in [
            "採用",
            "1",
            "",
            "Default",
            "不要開始執行",
            "「開始執行」",
        ]:
            result = delivery.verify_delivery_admission(
                self.root,
                relative,
                expected_hash=digest,
                authorization=authorization,
                working_reference=self.wid,
            )
            self.assertFalse(result["product_code_allowed"])
        result = delivery.verify_delivery_admission(
            self.root,
            relative,
            expected_hash=digest,
            authorization="開始執行",
            working_reference=self.wid,
        )
        self.assertTrue(result["product_code_allowed"], result)
        path.write_text(
            path.read_text(encoding="utf-8") + "\nChanged\n", encoding="utf-8"
        )
        result = delivery.verify_delivery_admission(
            self.root,
            relative,
            expected_hash=digest,
            authorization="開始執行",
            working_reference=self.wid,
        )
        self.assertFalse(result["product_code_allowed"])

    def test_tracking_phrase_is_modifying_even_without_pending_context(self):
        self.assertTrue(
            selection.classify_intent("保留本機、排除 commit")["requires_modification"]
        )

    def test_numeric_answer_must_match_user_answer_field(self):
        self.question()
        text = self.reload().replace(
            "## Acceptance Criteria",
            """### DISC-002: A different answer

- **Situation:** Awaiting a choice.
- **Question:** 保留哪些檔案？
- **Options and tradeoffs:** 保留追蹤 or 保留本機、排除 commit.
- **User answer:** not stated
- **Explicit rationale:** not stated
- **Resulting impact:** REQ-001, DEC-001, AC-001.

## Acceptance Criteria""",
        )
        result = spec.reconcile_working_bundle(
            self.root,
            self.wid,
            text,
            {},
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
            question_id="Q-tracking",
            question_version=2,
            answer="1",
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertIsNotNone(spec.pending_decision(self.reload()))

    def test_lowercase_heading_still_persists_question_without_journal_prose(self):
        text = self.reload().replace("## Revision History", "## revision history")
        spec.reconcile_working_bundle(
            self.root,
            self.wid,
            text,
            {},
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        self.reload()
        self.question()
        self.assertIsNotNone(spec.pending_decision(self.reload()))
        journal = (self.root / self.ref["journal_path"]).read_text(encoding="utf-8")
        self.assertNotIn("保留哪些檔案", journal)
        self.assertIn("Q-tracking@", journal)

    def test_contract_sections_after_revision_history_are_not_ignored(self):
        text = confirmed_spec()
        self.assertNotEqual(
            spec._contract_hash(text),
            spec._contract_hash(
                text + "\n## Additional contract\n\nNo retries permitted.\n"
            ),
        )

    def test_reopen_without_optional_identity_preserves_task(self):
        canonical = self.materialize()["canonical_spec"]
        result = spec.reopen_spec(
            self.root,
            Path(canonical["path"]),
            expected_revision=canonical["revision"],
            reason="Clarify existing scope",
        )
        self.assertEqual("PASS", result["verdict"])
        self.assertEqual("task-A", result["working_spec"]["task_ref"])
        self.assertNotEqual(
            "invalid", spec.assess_turn_context(self.root, task_ref="task-A")["state"]
        )

    def test_read_only_followups_keep_their_workflow(self):
        for pending in [False, True]:
            if pending:
                self.question()
            for prompt, expected in [
                ("code review", "code-review"),
                ("diagnose", "diagnosing-bugs"),
                ("驗證階梯", "verification-ladder"),
            ]:
                self.assertEqual(
                    expected, self.route(prompt, "read-only")["selected_skill"]
                )

    def test_same_revision_canonical_drift_is_rejected(self):
        self.question()
        self.answer()
        relative = self.materialize()["canonical_spec"]["path"]
        path = self.root / relative
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "Retry at most three times.", "Retry at most eight times."
            ),
            encoding="utf-8",
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result = delivery.verify_delivery_admission(
            self.root,
            relative,
            expected_hash=digest,
            authorization="開始執行",
            working_reference=self.wid,
        )
        self.assertFalse(result["product_code_allowed"])

    def test_composed_router_and_contract_reopen_lifecycle(self):
        (self.root / "main.py").write_text(
            "def main():\n    return 0\n", encoding="utf-8"
        )
        self.question()
        result = router.route(
            "1", self.root, task_ref="task-A", working_reference=self.wid
        )
        self.assertEqual("spec-governance", result["selected_skill"])
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("PASS", self.answer("1")["verdict"])
        canonical = self.materialize()["canonical_spec"]
        result = router.route(
            "開始執行", self.root, task_ref="task-A", working_reference=self.wid
        )
        self.assertEqual(canonical["path"], result["spec_context"]["selected_path"])
        self.assertEqual("spec-governance", result["selected_skill"])
        reopened = spec.reopen_spec(
            self.root,
            Path(canonical["path"]),
            expected_revision=canonical["revision"],
            reason="Investigate a possible change",
            task_ref="task-A",
        )
        self.assertEqual("PASS", reopened["verdict"])
        self.wid = reopened["working_spec"]["working_id"]
        unchanged = self.materialize()
        self.assertTrue(unchanged["authorization_retained"])
        canonical = unchanged["canonical_spec"]
        spec.reopen_spec(
            self.root,
            Path(canonical["path"]),
            expected_revision=canonical["revision"],
            reason="Change the retry limit",
            task_ref="task-A",
        )
        text = self.reload().replace(
            "Retry at most three times.", "Retry at most four times."
        )
        spec.reconcile_working_bundle(
            self.root,
            self.wid,
            text,
            {},
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        changed = self.materialize()
        self.assertTrue(changed["actual_contract_delta"])
        self.assertFalse(changed["authorization_retained"])
        self.assertFalse(changed["product_execution_authorized"])


if __name__ == "__main__":
    unittest.main()
