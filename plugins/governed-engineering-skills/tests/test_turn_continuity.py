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


def host_evidence(mode="default", numbered=True):
    return {
        "mode": mode,
        "mode_ref": "fixture-host-turn",
        "policy_ref": "fixture-host-policy",
        "numbered_text_allowed": numbered,
        "menu_tool_allowed": True,
    }


def presentation_evidence(q, stage="prepared", host=None):
    content = q["question"] + (
        ("\n\n" + "\n".join(f"{i}. {v}" for i, v in enumerate(q["options"], 1)))
        if q["options"]
        else ""
    )
    return {
        "host": host or host_evidence(),
        "surface": "open-text" if q.get("kind") == "open-text" else "numbered-text",
        "stage": stage,
        "text": content,
        "reply_text": content,
        "source_ref": "fixture-rendered-reply",
    }


def with_presentation(events):
    """Add explicit rendered reply observations to pre-existing lifecycle fixtures."""
    result = []
    for event in events:
        event = dict(event)
        if event["kind"] == "turn_start":
            event["host"] = host_evidence()
        if event["kind"] == "question" and isinstance(event.get("question"), dict):
            event["presentation"] = presentation_evidence(event["question"])
            result.extend(
                [
                    event,
                    {
                        "kind": "reply",
                        "text": event["presentation"]["text"],
                        "source_ref": "fixture-reply",
                    },
                ]
            )
        else:
            result.append(event)
    return result


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
- **Question:** {question["question"]}
- **Options and tradeoffs:** {" or ".join(question["options"]) or "Open text; no authored choices."}
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
        self.assertFalse(unchanged["authorization_retained"])
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


class DiscussionCompletionTests(unittest.TestCase):
    setUp = TurnContinuityTests.setUp
    reload = TurnContinuityTests.reload
    question = TurnContinuityTests.question
    answer = TurnContinuityTests.answer
    materialize = TurnContinuityTests.materialize

    def context(self):
        return spec.assess_turn_context(
            self.root, reference=self.wid, task_ref="task-A"
        )

    def observed(self, **extra):
        if (
            isinstance(extra.get("question_presented"), dict)
            and "presentation" not in extra
        ):
            extra["presentation"] = presentation_evidence(extra["question_presented"])
        return {
            "working_spec": self.context()["working_spec"],
            "project_root": str(self.root.resolve()),
            **extra,
        }

    def finish(self, **extra):
        return spec.assess_discussion_completion(self.context(), self.observed(**extra))

    def test_saved_question_requires_actual_matching_presentation(self):
        self.question()
        self.assertFalse(self.finish(reason="waiting-for-user")["can_end_turn"])
        q = self.context()["pending_question"]
        self.assertTrue(
            self.finish(question_presented=q, presentation_ref="message-1")[
                "can_end_turn"
            ]
        )
        for bad in (
            {**q, "version": 999},
            {**q, "question": "Different question"},
            {**q, "options": ["Other", "Unknown"]},
        ):
            self.assertFalse(
                self.finish(question_presented=bad, presentation_ref="message-1")[
                    "can_end_turn"
                ]
            )
        stale = self.observed(question_presented=q, presentation_ref="message-1")
        stale["working_spec"] = {**stale["working_spec"], "snapshot_hash": "wrong"}
        self.assertFalse(
            spec.assess_discussion_completion(self.context(), stale)["can_end_turn"]
        )

    def spec_reply(self):
        self.reload()
        ctx = self.context()
        path = (
            self.root / "specs" / f"{self.ref['spec_id']}-{self.ref['change_set']}.md"
        )
        text = path.read_text(encoding="utf-8")
        title = next(line[2:] for line in text.splitlines() if line.startswith("# "))
        summary = "Preserve accepted requirements and require explicit execution."
        return {
            "spec_id": self.ref["spec_id"],
            "revision": self.ref["revision"],
            "snapshot_hash": ctx["working_spec"]["snapshot_hash"],
            "summary": summary,
            "status": "awaiting-authorization",
            "source_ref": "fixture-visible-reply",
            "stage": "emitted",
            "reply_text": f"[{self.ref['spec_id']}: {title}](<{path.as_posix()}>)\n\n{summary}\n\nSPEC 已完成，等待「開始執行」。",
        }

    def test_completed_spec_requires_visible_current_link_summary_and_status(self):
        self.materialize()
        good = self.spec_reply()
        self.assertFalse(
            self.finish(proposal_presented=True, presentation_ref="panel-only")[
                "can_end_turn"
            ]
        )
        for changes in (
            {"reply_text": "SPEC 已完成"},
            {"reply_text": good["reply_text"].replace("](", "\\](")},
            {"reply_text": "<section hidden>" + good["reply_text"] + "</section>"},
            {"reply_text": good["reply_text"].replace("[", "\\[")},
            {"reply_text": "<!--" + good["reply_text"] + "-->"},
            {
                "reply_text": "\n".join(
                    "    " + line for line in good["reply_text"].splitlines()
                )
            },
            {"reply_text": "<div hidden>" + good["reply_text"] + "</div>"},
            {"reply_text": good["reply_text"].replace("[", "").replace("]", "")},
            {"reply_text": good["reply_text"].replace(good["summary"], "")},
            {
                "reply_text": good["reply_text"].replace(
                    "SPEC 已完成，等待「開始執行」。", ""
                )
            },
            {"revision": 999},
            {"snapshot_hash": "old"},
            {"stage": "prepared"},
            {"source_ref": ""},
            {"status": "executing"},
        ):
            with self.subTest(changes=changes):
                self.assertFalse(
                    self.finish(
                        proposal_presented=True,
                        presentation_ref="reply",
                        spec_presentation=good | changes,
                    )["can_end_turn"]
                )
        self.assertTrue(
            self.finish(
                proposal_presented=True,
                presentation_ref="reply",
                spec_presentation=good,
            )["can_end_turn"]
        )

    def test_spec_link_with_space_requires_angle_destination(self):
        self.materialize()
        evidence = self.spec_reply()
        context = self.context()
        original = context["spec_presentation"]["path"]
        spaced = original.replace("/specs/", "/space in path/specs/")
        context["spec_presentation"]["path"] = spaced
        evidence["reply_text"] = evidence["reply_text"].replace(original, spaced)
        observation = self.observed(
            proposal_presented=True,
            presentation_ref="reply",
            spec_presentation=evidence,
        )
        self.assertTrue(
            spec.assess_discussion_completion(context, observation)["can_end_turn"]
        )
        evidence["reply_text"] = (
            evidence["reply_text"].replace("(<", "(").replace(">)", ")")
        )
        self.assertFalse(
            spec.assess_discussion_completion(context, observation)["can_end_turn"]
        )

    def test_visible_spec_can_report_current_authorization_without_reasking(self):
        from managed_delivery import execute_request

        self.materialize()
        evidence = self.spec_reply()
        base = {
            "task_ref": "task-A",
            "working_reference": self.wid,
            "spec": f"specs/{self.ref['spec_id']}-{self.ref['change_set']}.md",
        }
        result = execute_request(
            self.root,
            base
            | {
                "operation": "authorize",
                "instruction": "開始執行",
                "source_event_id": "synthetic-fixture-start",
                "expected_hash": hashlib.sha256(
                    (self.root / base["spec"]).read_bytes()
                ).hexdigest(),
            },
        )
        self.assertEqual("PASS", result["verdict"])
        status = execute_request(self.root, base | {"operation": "status"})
        evidence["status"] = "executing"
        evidence["reply_text"] = evidence["reply_text"].replace(
            "等待「開始執行」", "已取得本次「開始執行」授權"
        )
        assessment = self.finish(
            proposal_presented=True,
            presentation_ref="reply",
            spec_presentation=evidence,
            execution=status,
        )
        self.assertTrue(assessment["can_end_turn"])
        self.assertEqual("continue-authorized-execution", assessment["next_action"])
        self.assertFalse(assessment["product_code_allowed"])
        status["binding"]["task_ref"] = "another-task"
        self.assertFalse(
            self.finish(
                proposal_presented=True,
                presentation_ref="reply",
                spec_presentation=evidence,
                execution=status,
            )["can_end_turn"]
        )

    def test_completed_decisions_require_materialized_presented_proposal(self):
        self.assertEqual("materialize", self.finish()["next_action"])
        self.materialize()
        self.assertFalse(self.finish()["can_end_turn"])
        r = self.finish(
            proposal_presented=True,
            presentation_ref="message-2",
            spec_presentation=self.spec_reply(),
        )
        self.assertEqual("await-execution-authorization", r["next_action"])
        self.assertTrue(r["can_end_turn"])
        self.assertFalse(r["product_code_allowed"])

    def test_mixed_answer_and_next_question_resume_same_turn(self):
        from managed_delivery import audit_trace

        self.question()
        initial = self.context()
        self.assertEqual(
            "PASS",
            self.answer("2，但不用比較沒有高通的結果。是否對高通資料 training？")[
                "verdict"
            ],
        )
        text = (
            self.reload()
            .replace(
                "## Open Decisions\n\nNone.",
                "## Open Decisions\n\n- Where should filtering run?",
            )
            .replace(
                "Retry at most three times.",
                "Train only high-pass Accel; omit unfiltered comparison.",
            )
        )
        r = spec.reconcile_working_bundle(
            self.root,
            self.wid,
            text,
            {},
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        self.assertEqual("BLOCKED", r["verdict"])
        self.assertIn(
            "Train only high-pass Accel; omit unfiltered comparison.", self.reload()
        )
        updated = self.context()
        self.assertFalse(self.finish()["can_end_turn"])
        self.assertEqual("ask-next-decision", self.finish()["next_action"])
        prefix = [
            {"kind": "turn_start", "context": initial},
            {"kind": "decision"},
            {"kind": "requirement"},
            {"kind": "read"},
        ]
        self.assertEqual(
            "FAIL",
            audit_trace(
                with_presentation(prefix + [{"kind": "turn_end", "reason": "answered"}])
            )["verdict"],
        )
        saved = prefix + [{"kind": "spec_saved", "verdict": "PASS", "context": updated}]
        self.assertEqual(
            "FAIL",
            audit_trace(
                with_presentation(saved + [{"kind": "turn_end", "reason": "waiting"}])
            )["verdict"],
        )
        self.reload()
        r = spec.record_question(
            self.root,
            self.wid,
            "Q-filter",
            "Where should filtering run?",
            ["In this project", "Before import"],
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        self.assertEqual("BLOCKED", r["verdict"])
        context = self.context()
        trace = saved + [
            {"kind": "context", "context": context},
            {
                "kind": "question",
                "question": context["pending_question"],
                "presentation_ref": "reply-next",
            },
            {"kind": "turn_end"},
        ]
        self.assertEqual("PASS", audit_trace(with_presentation(trace))["verdict"])
        self.assertFalse((self.root / "program.py").exists())

    def test_pause_requires_explicit_discussion_scope_and_observed_message(self):
        self.question()
        for observation in (
            {"reason": "paused"},
            {
                "pause": {
                    "scope": "product",
                    "user_text": "stop implementation",
                    "source_ref": "user-1",
                }
            },
            {"pause": {"scope": "discussion"}},
        ):
            self.assertFalse(self.finish(**observation)["can_end_turn"])
        self.assertTrue(
            self.finish(
                pause={
                    "scope": "discussion",
                    "user_text": "暫停討論",
                    "source_ref": "user-2",
                }
            )["can_end_turn"]
        )

    def test_factual_followup_and_timeout_preserve_same_question(self):
        from managed_delivery import audit_trace

        self.question()
        context = self.context()
        q = context["pending_question"]
        trace = [
            {"kind": "turn_start", "context": context},
            {"kind": "read"},
            {"kind": "timeout"},
            {"kind": "question", "question": q, "presentation_ref": "reply"},
            {"kind": "turn_end"},
        ]
        self.assertEqual("PASS", audit_trace(with_presentation(trace))["verdict"])
        self.assertEqual(q, self.context()["pending_question"])
        self.assertEqual(
            "FAIL",
            audit_trace(
                trace
                + [{"kind": "turn_start", "context": context}, {"kind": "turn_end"}]
            )["verdict"],
        )

    def test_project_task_binding_and_malformed_observation(self):
        self.question()
        self.assertEqual(
            "BLOCKED",
            spec.finish_discussion_turn(
                self.root, reference=self.wid, task_ref="wrong", observation={}
            )["verdict"],
        )
        for value in (None, [], "waiting", {"pause": []}):
            self.assertFalse(
                spec.assess_discussion_completion(self.context(), value)["can_end_turn"]
            )

    def test_blocker_requires_evidence_and_visible_request(self):
        self.question()
        self.assertFalse(self.finish(blocker={"reason": "unknown"})["can_end_turn"])
        b = {
            "detail": "Repository data cannot be read",
            "required_input": "Provide the missing dataset path",
            "evidence_ref": "tool-error-1",
            "presentation_ref": "reply-1",
        }
        self.assertTrue(self.finish(blocker=b)["can_end_turn"])

    def test_audit_does_not_reset_question_count_or_leak_admission(self):
        from managed_delivery import audit_trace

        self.question()
        c = self.context()
        q = {
            "kind": "question",
            "question": c["pending_question"],
            "presentation_ref": "reply",
        }
        trace = [
            {"kind": "turn_start", "context": c},
            q,
            {"kind": "context", "context": c},
            q,
            {"kind": "turn_end"},
        ]
        self.assertEqual("FAIL", audit_trace(with_presentation(trace))["verdict"])
        first = [
            {"kind": "turn_start", "context": c},
            {"kind": "admission", "verdict": "PASS", "product_code_allowed": True},
            q,
            {"kind": "turn_end"},
        ]
        other = {**c, "working_spec": {**c["working_spec"], "task_ref": "task-B"}}
        trace = first + [
            {"kind": "turn_start", "context": other},
            {"kind": "managed_write", "verdict": "PASS"},
            q,
            {"kind": "turn_end"},
        ]
        self.assertEqual("FAIL", audit_trace(with_presentation(trace))["verdict"])

    def test_malformed_trace_fails_without_throwing(self):
        from managed_delivery import audit_trace

        self.question()
        for bad in (
            None,
            {},
            {"working_spec": None},
            {"working_spec": {}},
            {"state": [], "working_spec": {}},
            {"state": {}, "working_spec": {}},
        ):
            trace = [
                {"kind": "turn_start", "context": bad},
                {"kind": "context", "context": self.context()},
                {"kind": "turn_end"},
            ]
            self.assertEqual("FAIL", audit_trace(with_presentation(trace))["verdict"])
        self.assertFalse(
            self.finish(
                pause={
                    "scope": "discussion",
                    "user_text": "Stop product implementation only; continue discussion",
                    "source_ref": "user",
                }
            )["can_end_turn"]
        )

    def test_context_revision_revokes_audited_admission(self):
        from managed_delivery import audit_trace

        self.question()
        c = self.context()
        changed = {
            **c,
            "working_spec": {
                **c["working_spec"],
                "revision": c["working_spec"]["revision"] + 1,
            },
        }
        trace = [
            {"kind": "turn_start", "context": c},
            {"kind": "admission", "verdict": "PASS", "product_code_allowed": True},
            {"kind": "context", "context": changed},
            {"kind": "managed_write", "verdict": "PASS"},
            {
                "kind": "question",
                "question": c["pending_question"],
                "presentation_ref": "reply",
            },
            {"kind": "turn_end"},
        ]
        self.assertEqual("FAIL", audit_trace(with_presentation(trace))["verdict"])
        self.assertFalse(self.finish(project_root="some-other-project")["can_end_turn"])

    def test_finish_turn_cli_uses_recovered_context(self):
        self.question()
        q = self.context()["pending_question"]
        observation = self.observed(
            question_presented=q, presentation_ref="prepared-reply"
        )
        path = self.root / "observation.json"
        path.write_text(json.dumps(observation), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                str(PLUGIN / "spec-governance/scripts/spec_contract.py"),
                "finish-turn",
                "--project-root",
                str(self.root),
                "--reference",
                self.wid,
                "--task-ref",
                "task-A",
                "--observation",
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("await-answer", json.loads(result.stdout)["next_action"])

    def test_missing_context_can_report_concrete_evidenced_blocker(self):
        context = {"state": "invalid", "reason": "working specification task mismatch"}
        blocker = {
            "detail": context["reason"],
            "required_input": "Identify the intended task",
            "evidence_ref": "context-tool-result",
            "presentation_ref": "reply",
        }
        self.assertFalse(
            spec.assess_discussion_completion(context, {"blocker": blocker})[
                "can_end_turn"
            ]
        )
        self.assertTrue(
            spec.assess_discussion_completion(
                context, {"context_error": context, "blocker": blocker}
            )["can_end_turn"]
        )

    def test_audited_recovery_blocker_requires_matching_context_error(self):
        from managed_delivery import audit_trace

        c = {"state": "invalid", "reason": "missing journal"}
        b = {
            "detail": "missing journal",
            "required_input": "Identify the recoverable specification",
            "evidence_ref": "tool",
            "presentation_ref": "reply",
        }
        trace = [
            {"kind": "turn_start", "context": c},
            {"kind": "blocker", "blocker": b, "context_error": c},
            {"kind": "turn_end"},
        ]
        self.assertEqual("PASS", audit_trace(with_presentation(trace))["verdict"])
        trace[1]["context_error"] = {"state": "invalid", "reason": "unrelated"}
        self.assertEqual("FAIL", audit_trace(with_presentation(trace))["verdict"])

    def test_canonical_metadata_drift_cannot_present_stale_proposal(self):
        result = self.materialize()
        path = self.root / result["canonical_spec"]["path"]
        before = path.read_text(encoding="utf-8")
        for old, new in (
            ("revision: 1", "revision: 2"),
            ("status: confirmed", "status: implemented"),
        ):
            path.write_text(before.replace(old, new), encoding="utf-8")
            self.assertFalse(
                self.finish(proposal_presented=True, presentation_ref="reply")[
                    "can_end_turn"
                ]
            )


class QuestionPresentationTests(unittest.TestCase):
    setUp = TurnContinuityTests.setUp
    reload = TurnContinuityTests.reload
    question = TurnContinuityTests.question
    answer = TurnContinuityTests.answer

    def host(self, mode="default", numbered=True):
        return {
            "mode": mode,
            "mode_ref": "host-turn-1",
            "policy_ref": "host-rules-1",
            "numbered_text_allowed": numbered,
            "menu_tool_allowed": True,
        }

    def test_default_denies_menus_even_if_tools_available(self):
        for surface in (
            "request_user_input_async",
            "request_user_input",
            "structured-menu",
        ):
            for numbered in (True, False):
                r = spec.question_surface_policy(self.host(numbered=numbered), surface)
                self.assertEqual("BLOCKED", r["verdict"])
                self.assertFalse(r["menu_allowed"])
        self.assertEqual(
            "PASS",
            spec.question_surface_policy(self.host("plan"), "structured-menu")[
                "verdict"
            ],
        )
        self.assertEqual(
            "BLOCKED",
            spec.question_surface_policy(self.host("unknown"), "structured-menu")[
                "verdict"
            ],
        )
        self.assertEqual(
            "PASS",
            spec.question_surface_policy(self.host(numbered=False), "open-text")[
                "verdict"
            ],
        )

    def test_open_question_roundtrip_and_freeform_answer(self):
        r = spec.record_question(
            self.root,
            self.wid,
            "Q-tracking",
            "保留哪些檔案？",
            [],
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
            question_kind="open-text",
        )
        self.assertEqual("BLOCKED", r["verdict"])
        self.reload()
        q = spec.pending_decision(self.reload())
        self.assertEqual([], q["options"])
        self.assertEqual("open-text", q["kind"])
        self.assertEqual("PASS", self.answer("只保留本機紀錄")["verdict"])

    def test_revise_options_requires_versioned_history(self):
        self.question()
        q = spec.pending_decision(self.reload())
        r = spec.update_question(
            self.root,
            self.wid,
            {
                "action": "revise",
                "question_version": q["version"],
                "question": q["question"],
                "options": q["options"] + ["新增第三種保留方式"],
                "source_ref": "user-turn-2",
                "user_text": "提供其他方案",
            },
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        self.assertEqual("BLOCKED", r["verdict"])
        new = spec.pending_decision(self.reload())
        self.assertGreater(new["version"], q["version"])
        self.assertEqual(3, len(new["options"]))
        self.assertEqual("BLOCKED", self.answer("3", version=q["version"])["verdict"])
        self.assertIn("Question Record", self.reload())
        self.assertEqual("BLOCKED", self.answer("4")["verdict"])
        self.assertEqual("PASS", self.answer("3")["verdict"])

    def test_failed_surface_survives_reload_without_becoming_answer(self):
        self.question()
        q = spec.pending_decision(self.reload())
        r = spec.update_question(
            self.root,
            self.wid,
            {
                "action": "presentation-failed",
                "question_version": q["version"],
                "surface": "structured-menu",
                "source_ref": "user-turn-2",
                "user_text": "沒看到",
            },
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        self.assertEqual("BLOCKED", r["verdict"])
        self.assertEqual(q, spec.pending_decision(self.reload()))
        c = spec.assess_turn_context(self.root, reference=self.wid, task_ref="task-A")
        self.assertIn("structured-menu", c["question_record"]["failed_surfaces"])

    def test_accepted_or_prepared_file_cannot_prove_emitted_question(self):
        self.question()
        c = spec.assess_turn_context(self.root, reference=self.wid, task_ref="task-A")
        obs = {
            "project_root": str(self.root.resolve()),
            "working_spec": c["working_spec"],
            "question_presented": c["pending_question"],
            "presentation_ref": "draft.md",
            "presentation": {
                "host": self.host(),
                "surface": "numbered-text",
                "stage": "emitted",
                "text": "選項已送出",
                "source_ref": "reply-1",
            },
        }
        self.assertFalse(spec.assess_discussion_completion(c, obs)["can_end_turn"])

    def test_failed_plan_menu_denied_until_explicit_retry(self):
        self.question()

        def update(action):
            q = spec.pending_decision(self.reload())
            spec.update_question(
                self.root,
                self.wid,
                {
                    "action": action,
                    "question_version": q["version"],
                    "surface": "request_user_input_async",
                    "source_ref": "user-turn",
                    "user_text": "retry"
                    if action == "retry-requested"
                    else "cannot see",
                },
                expected_revision=self.ref["revision"],
                expected_hash=self.ref["snapshot_hash"],
            )
            return spec.assess_turn_context(
                self.root, reference=self.wid, task_ref="task-A"
            )

        c = update("presentation-failed")
        for surface in (
            "request_user_input_async",
            "request_user_input",
            "structured-menu",
        ):
            self.assertEqual(
                "BLOCKED",
                spec.question_surface_policy(
                    self.host("plan"), surface, c["question_record"]["failed_surfaces"]
                )["verdict"],
            )
        c = update("retry-requested")
        self.assertEqual(
            "PASS",
            spec.question_surface_policy(
                self.host("plan"),
                "structured-menu",
                c["question_record"]["failed_surfaces"],
            )["verdict"],
        )
        self.assertFalse(
            spec.question_surface_policy(
                self.host(), "structured-menu", c["question_record"]["failed_surfaces"]
            )["menu_allowed"]
        )

    def test_choice_to_open_transition_preserves_history_and_identity(self):
        self.question()
        q = spec.pending_decision(self.reload())
        spec.update_question(
            self.root,
            self.wid,
            {
                "action": "revise",
                "question_version": q["version"],
                "kind": "open-text",
                "question": "你希望如何保留檔案？",
                "options": [],
                "source_ref": "host-policy-and-user-turn",
                "user_text": "沒看到",
            },
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        c = spec.assess_turn_context(self.root, reference=self.wid, task_ref="task-A")
        self.assertEqual(q["id"], c["pending_question"]["id"])
        self.assertEqual(q, c["question_record"]["history"][-1]["question"])
        self.assertEqual("open-text", c["pending_question"]["kind"])
        self.assertEqual("BLOCKED", self.answer("1", version=q["version"])["verdict"])
        self.assertEqual("PASS", self.answer("本機保存")["verdict"])

    def test_trace_rejects_actual_menu_even_if_text_is_valid(self):
        from managed_delivery import audit_trace

        self.question()
        c = spec.assess_turn_context(self.root, reference=self.wid, task_ref="task-A")
        trace = with_presentation(
            [
                {"kind": "turn_start", "context": c},
                {
                    "kind": "question",
                    "question": c["pending_question"],
                    "presentation_ref": "reply",
                },
                {"kind": "turn_end"},
            ]
        )
        self.assertEqual("PASS", audit_trace(trace)["verdict"])
        for tool in ("request_user_input_async", "request_user_input"):
            self.assertEqual(
                "FAIL",
                audit_trace(
                    trace[:1]
                    + [{"kind": "question_tool", "tool": tool, "accepted": True}]
                    + trace[1:]
                )["verdict"],
            )
        self.assertEqual(
            "FAIL", audit_trace([e for e in trace if e["kind"] != "reply"])["verdict"]
        )
        changed = [dict(e) for e in trace]
        next(e for e in changed if e["kind"] == "reply")["text"] = "選項已送出"
        self.assertEqual("FAIL", audit_trace(changed)["verdict"])
        self.assertEqual(
            "FAIL",
            audit_trace(
                trace[:1] + [{"kind": "mode_change", "mode": "plan"}] + trace[1:]
            )["verdict"],
        )

    def test_reconcile_cannot_erase_failure_history(self):
        import re

        self.question()
        q = spec.pending_decision(self.reload())
        spec.update_question(
            self.root,
            self.wid,
            {
                "action": "presentation-failed",
                "question_version": q["version"],
                "surface": "structured-menu",
                "source_ref": "user-2",
                "user_text": "cannot see",
            },
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        original = self.reload()
        erased = re.sub(r"(?ms)^## Question Record.*?(?=^## |\Z)", "", original)
        r = spec.reconcile_working_bundle(
            self.root,
            self.wid,
            erased,
            {},
            expected_revision=self.ref["revision"],
            expected_hash=self.ref["snapshot_hash"],
        )
        self.assertEqual("BLOCKED", r["verdict"])
        self.assertEqual(original, self.reload())

    def test_malformed_question_record_trace_is_fail_closed(self):
        from managed_delivery import audit_trace

        for record in (None, [], "invalid", {"failed_surfaces": []}):
            self.assertEqual(
                "FAIL",
                audit_trace(
                    [
                        {
                            "kind": "turn_start",
                            "context": {"working_spec": {}, "question_record": record},
                        },
                        {"kind": "question_tool", "tool": "request_user_input_async"},
                        {"kind": "turn_end"},
                    ]
                )["verdict"],
            )

    def test_final_reply_cannot_add_an_unsaved_third_option(self):
        from managed_delivery import audit_trace

        self.question()
        c = spec.assess_turn_context(self.root, reference=self.wid, task_ref="task-A")
        evidence = presentation_evidence(c["pending_question"])
        obs = {
            "project_root": c["project_root"],
            "working_spec": c["working_spec"],
            "question_presented": c["pending_question"],
            "presentation_ref": "reply",
            "presentation": evidence,
        }
        self.assertTrue(spec.assess_discussion_completion(c, obs)["can_end_turn"])
        for reply in (
            evidence["text"] + "\n3. unsaved alternative",
            "3. unsaved alternative\n" + evidence["text"],
        ):
            bad = {**evidence, "reply_text": reply}
            self.assertFalse(
                spec.assess_discussion_completion(c, {**obs, "presentation": bad})[
                    "can_end_turn"
                ]
            )
            trace = [
                {"kind": "turn_start", "context": c, "host": evidence["host"]},
                {
                    "kind": "question",
                    "question": c["pending_question"],
                    "presentation_ref": "reply",
                    "presentation": evidence,
                },
                {"kind": "reply", "text": reply, "source_ref": "actual-reply"},
                {"kind": "turn_end"},
            ]
            self.assertEqual("FAIL", audit_trace(trace)["verdict"])
        for record in (None, [], {"failed_surfaces": []}):
            self.assertFalse(
                spec.assess_discussion_completion(
                    {**c, "question_record": record}, obs
                )["can_end_turn"]
            )
        self.assertFalse(
            spec.assess_discussion_completion(
                c,
                {
                    **obs,
                    "host": self.host(),
                    "question_tools": ["request_user_input_async"],
                },
            )["can_end_turn"]
        )

    def test_plan_audit_requires_allowed_host_and_emitted_reply(self):
        from managed_delivery import audit_trace

        self.question()
        c = spec.assess_turn_context(self.root, reference=self.wid, task_ref="task-A")
        host = self.host("plan")
        ev = {
            **presentation_evidence(c["pending_question"], host=host),
            "surface": "structured-menu",
        }
        trace = [
            {"kind": "turn_start", "context": c, "host": host},
            {
                "kind": "question_tool",
                "tool": "request_user_input_async",
                "accepted": True,
            },
            {
                "kind": "question",
                "question": c["pending_question"],
                "presentation_ref": "reply",
                "presentation": ev,
            },
            {"kind": "reply", "text": ev["text"], "source_ref": "reply"},
            {"kind": "turn_end"},
        ]
        self.assertEqual("PASS", audit_trace(trace)["verdict"])
        host["menu_tool_allowed"] = False
        self.assertEqual("FAIL", audit_trace(trace)["verdict"])

    def test_open_question_cli_and_policy_use_current_persisted_state(self):
        cli = str(PLUGIN / "spec-governance/scripts/spec_contract.py")

        def run(*args):
            result = subprocess.run(
                [sys.executable, "-X", "utf8", cli, *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            return result.returncode, json.loads(result.stdout)

        host = self.root / "host.json"
        host.write_text(json.dumps(self.host(numbered=False)), encoding="utf-8")
        common = [
            "--project-root",
            str(self.root),
            "--reference",
            self.wid,
            "--task-ref",
            "task-A",
            "--host",
            str(host),
        ]
        self.assertEqual(
            2, run("question-policy", *common, "--surface", "open-text")[0]
        )
        code, _ = run(
            "question",
            "--project-root",
            str(self.root),
            "--working-id",
            self.wid,
            "--question-id",
            "Q-open",
            "--question",
            "How should this behave?",
            "--kind",
            "open-text",
            "--expected-revision",
            str(self.ref["revision"]),
            "--expected-hash",
            self.ref["snapshot_hash"],
        )
        self.assertEqual(2, code)  # Saved, still awaiting its answer.
        self.assertEqual("open-text", spec.pending_decision(self.reload())["kind"])
        self.assertEqual(
            0, run("question-policy", *common, "--surface", "open-text")[0]
        )
        for surface in (
            "numbered-text",
            "request_user_input_async",
            "request_user_input",
        ):
            code, output = run("question-policy", *common, "--surface", surface)
            self.assertEqual(2, code)
            self.assertFalse(output["menu_allowed"])

    def test_plan_menu_does_not_force_forbidden_textual_options(self):
        self.question()
        c = spec.assess_turn_context(self.root, reference=self.wid, task_ref="task-A")
        evidence = {
            **presentation_evidence(
                c["pending_question"], host=self.host("plan", numbered=False)
            ),
            "surface": "structured-menu",
        }
        observation = {
            "project_root": c["project_root"],
            "working_spec": c["working_spec"],
            "question_presented": c["pending_question"],
            "presentation_ref": "menu-and-reply",
            "presentation": evidence,
        }
        self.assertFalse(
            spec.assess_discussion_completion(c, observation)["can_end_turn"]
        )
        evidence["reply_text"] = c["pending_question"]["question"]
        self.assertTrue(
            spec.assess_discussion_completion(c, observation)["can_end_turn"]
        )
        evidence["host"]["mode"] = "default"
        self.assertFalse(
            spec.assess_discussion_completion(c, observation)["can_end_turn"]
        )
