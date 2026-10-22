"""SPEC-0029 explicit discussion-owner contracts."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "CLAUDE.md").is_file())
sys.path.insert(0, str(ROOT / "skills/engineering/spec-governance/scripts"))
sys.path.insert(0, str(ROOT / "skills/engineering/implement/scripts"))
sys.path.insert(0, str(ROOT / "skills/engineering/engineering-risk-routing/scripts"))
from discussion_state import discussion_request
from spec_contract import (
    assess_turn_context,
    finish_discussion_turn,
    reconcile_working_bundle,
)
from test_spec_governance import confirmed_spec


class DiscussionEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = {"task_ref": "task-a", "turn_id": "turn-1"}

    def call(self, operation, **values):
        return discussion_request(
            self.root, {**self.base, "operation": operation, **values}
        )

    def enter(self, prompt="提出量測方案", **values):
        return self.call(
            "enter",
            prompt=prompt,
            source_ref="fixture-user-1",
            engineering=True,
            **values,
        )

    def save(self, reply="實際答覆", **values):
        status = self.call("status")
        if status.get("item_coverage") in {"legacy-unregistered", "unreviewed"}:
            self.call(
                "observe",
                items=[],
                source_refs=status.get("source_refs", ["fixture-user-1"]),
            )
        binding = self.call("status")["binding"]
        return self.call(
            "record",
            summary="Saved actual goal and known facts; no adoption.",
            source_ref="fixture-reply-1",
            reply_text=reply,
            binding=binding,
            **values,
        )

    def test_identified_decisions_need_individual_contract_bindings(self):
        from test_spec_governance import confirmed_spec

        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        text = confirmed_spec(status="working").replace(
            "| DEC-001 | Use exponential backoff. |",
            "| DEC-001 | Use exponential backoff. | fixture-user-1 |\n| DEC-002 | Keep the retry limit visible. | fixture-user-1 |",
        )
        text = text.replace("| ID | Decision |", "| ID | Decision | Source |").replace(
            "|---|---|\n| DEC-001", "|---|---|---|\n| DEC-001"
        )
        result = reconcile_working_bundle(
            self.root,
            ref["working_id"],
            text,
            {},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", result["verdict"], result)
        items = [
            {
                "id": "A",
                "kind": "accepted",
                "source_ref": "fixture-user-1",
                "text": "Use backoff.",
            },
            {
                "id": "B",
                "kind": "accepted",
                "source_ref": "fixture-user-1",
                "text": "Show retry limit.",
            },
        ]
        self.call("observe", items=items, source_refs=["fixture-user-1"])
        with self.assertRaisesRegex(ValueError, "every identified item"):
            self.save(item_bindings={"A": ["DEC-001"]})
        self.assertEqual("BLOCKED", self.call("status")["verdict"])
        with self.assertRaisesRegex(ValueError, "distinct"):
            self.save(item_bindings={"A": ["DEC-001"], "B": ["DEC-001"]})
        saved = self.save(item_bindings={"A": ["DEC-001"], "B": ["DEC-002"]})
        self.assertEqual("PASS", self.call("status")["verdict"])
        self.assertEqual("working", saved["spec_presentation"]["status"])
        self.call("observe", items=items, source_refs=["fixture-user-1"])
        self.assertEqual("PASS", self.call("status")["verdict"])
        again = self.save(item_bindings={"A": ["DEC-001"], "B": ["DEC-002"]})
        self.assertTrue(again["replayed"])
        self.assertEqual(saved["event_hash"], again["event_hash"])

    def test_explicit_host_root_binding_uses_one_spec_store(self):
        project = self.root / "project"
        project.mkdir()
        self.call("bind-project", project_root=str(project))
        self.enter()
        self.assertFalse((self.root / "specs").exists())
        self.assertEqual(1, len(list((project / "specs").glob("SPEC-*.md"))))
        from guided_workflow_router import route

        routed = route(
            "提出量測方案",
            self.root,
            task_ref="task-a",
            turn_ref="turn-1",
            source_ref="fixture-user-1",
        )
        self.assertEqual("SPEC-0001", routed["turn_context"]["working_spec"]["spec_id"])
        self.save()
        self.assertEqual("PASS", self.call("stop", reply_text="saved")["verdict"])
        other = self.root / "other"
        other.mkdir()
        with self.assertRaisesRegex(ValueError, "already bound"):
            self.call("bind-project", project_root=str(other))
        self.assertFalse((other / "specs").exists())

    def test_new_turn_requires_explicit_item_review(self):
        self.enter()
        with self.assertRaisesRegex(ValueError, "identify"):
            self.call(
                "record",
                binding=self.call("status")["binding"],
                summary="A summary alone does not classify all identified decisions.",
                source_ref="fixture-reply",
                reply_text="saved",
            )
        self.assertEqual("BLOCKED", self.call("status")["verdict"])
        self.save()
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_ambiguous_parent_retains_source_until_explicit_binding(self):
        for name in ("one", "two"):
            (self.root / name / ".git").mkdir(parents=True)
        entered = self.enter()
        self.assertEqual("BLOCKED", entered["verdict"])
        self.assertTrue(entered["mapping_gap"])
        self.assertFalse((self.root / "specs").exists())
        restored = self.call("resume")["state"]
        self.assertEqual("fixture-user-1", restored["turns"]["turn-1"]["source_ref"])
        bound = self.call("bind-project", project_root=str(self.root / "two"))
        self.assertEqual("fixture-user-1", bound["pending_sources"][0]["source_ref"])
        self.enter()
        self.assertEqual(1, len(list((self.root / "two/specs").glob("SPEC-*.md"))))
        self.assertFalse((self.root / "one/specs").exists())

    def test_unsaved_identified_items_carry_into_the_next_turn(self):
        self.enter()
        self.call(
            "observe",
            items=[
                {
                    "id": "fact-A",
                    "kind": "fact",
                    "source_ref": "fixture-user-1",
                    "text": "The current hook has no real host proof.",
                }
            ],
            source_refs=["fixture-user-1"],
        )
        self.base["turn_id"] = "turn-2"
        self.call(
            "enter",
            engineering=True,
            prompt="Continue the same discussion",
            source_ref="fixture-user-2",
        )
        pending = self.call("status")
        self.assertEqual(["fact-A"], pending["pending_items"])
        self.assertEqual(["fixture-user-1", "fixture-user-2"], pending["source_refs"])
        self.save(item_bindings={"fact-A": []})
        self.assertEqual("PASS", self.call("status")["verdict"])
        self.assertEqual(1, len(list((self.root / "specs").glob("SPEC-*.md"))))

    def test_continuing_discussion_has_no_three_turn_limit(self):
        for count in (1, 5, 17):
            with self.subTest(turns=count), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                first_path = None
                for number in range(count):
                    base = {"task_ref": "long-discussion", "turn_id": f"turn-{number}"}
                    source = f"source-{number}"
                    discussion_request(
                        root,
                        base
                        | {
                            "operation": "enter",
                            "engineering": True,
                            "prompt": f"Discuss fact {number}",
                            "source_ref": source,
                        },
                    )
                    status = discussion_request(root, base | {"operation": "status"})
                    discussion_request(
                        root,
                        base
                        | {
                            "operation": "observe",
                            "items": [],
                            "source_refs": [source],
                        },
                    )
                    record = base | {
                        "operation": "record",
                        "binding": status["binding"],
                        "summary": f"Recorded fact {number}",
                        "reply_text": f"Fact {number}",
                        "source_ref": source,
                        "item_bindings": {},
                    }
                    saved = discussion_request(root, record)
                    self.assertEqual("working", saved["spec_presentation"]["status"])
                    first_path = first_path or saved["spec_presentation"]["path"]
                    self.assertEqual(first_path, saved["spec_presentation"]["path"])
                    self.assertTrue(discussion_request(root, record)["replayed"])
                self.assertEqual(1, len(list((root / "specs").glob("SPEC-*.md"))))

    def test_accepted_candidate_cannot_bypass_identified_item_mapping(self):
        self.enter()
        self.call("observe", items=[], source_refs=["fixture-user-1"])
        with self.assertRaisesRegex(ValueError, "accepted candidate"):
            self.save(
                candidates=[
                    {
                        "id": "candidate-A",
                        "status": "accepted",
                        "source_ref": "proposal-A",
                        "reason": "The user selected this option",
                        "impact": "A new adopted decision",
                        "user_source_ref": "fixture-user-1",
                        "reconciliation_ref": "DEC-001",
                    }
                ]
            )

    def test_nonengineering_interlude_preserves_pending_engineering_items(self):
        self.enter()
        self.call(
            "observe",
            items=[
                {
                    "id": "A",
                    "kind": "fact",
                    "source_ref": "fixture-user-1",
                    "text": "Unrecorded fact",
                }
            ],
            source_refs=["fixture-user-1"],
        )
        self.base["turn_id"] = "turn-2"
        self.call("enter", prompt="Hello", source_ref="source-2")
        self.call("classify", kind="non-engineering", reason="A greeting")
        self.assertEqual("BLOCKED", self.call("status")["verdict"])
        self.assertEqual(
            "BLOCKED",
            self.call("stop", reply_text="Pending engineering work")["verdict"],
        )
        final = self.call("stop", reply_text="Pending engineering work")
        self.assertTrue(final["continue"])
        self.assertNotEqual(True, final.get("saved"))
        self.base["turn_id"] = "turn-3"
        self.call(
            "enter", prompt="Continue the work", source_ref="source-3", engineering=True
        )
        status = self.call("status")
        self.assertIn("A", status["pending_items"])
        self.assertIn("fixture-user-1", status["source_refs"])
        self.save(item_bindings={"A": []})
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_binding_transfers_unknown_prompt_before_classification(self):
        project = self.root / "child"
        project.mkdir()
        self.call("enter", prompt="Discuss architecture", source_ref="fixture-user-1")
        self.call("bind-project", project_root=str(project))
        restored = self.call("resume")["state"]
        self.assertEqual("fixture-user-1", restored["turns"]["turn-1"]["source_ref"])
        self.call(
            "classify", kind="engineering", reason="Explicit engineering discussion"
        )
        self.save()
        self.assertFalse((self.root / "specs").exists())
        self.assertEqual(1, len(list((project / "specs").glob("SPEC-*.md"))))

    def test_accepted_item_cannot_reference_another_sources_decision(self):
        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        text = (
            confirmed_spec(status="working")
            .replace("| ID | Decision |", "| ID | Decision | Source |")
            .replace("|---|---|\n| DEC-001", "|---|---|---|\n| DEC-001")
            .replace(
                "| DEC-001 | Use exponential backoff. |",
                "| DEC-001 | Use exponential backoff. | other-source |",
            )
        )
        self.assertEqual(
            "PASS",
            reconcile_working_bundle(
                self.root,
                ref["working_id"],
                text,
                {},
                expected_revision=ref["revision"],
                expected_hash=ref["snapshot_hash"],
            )["verdict"],
        )
        self.call(
            "observe",
            items=[
                {
                    "id": "A",
                    "kind": "accepted",
                    "source_ref": "fixture-user-1",
                    "text": "A different decision",
                }
            ],
            source_refs=["fixture-user-1"],
        )
        with self.assertRaisesRegex(ValueError, "source"):
            self.save(item_bindings={"A": ["DEC-001"]})

    def test_binding_preserves_active_nonengineering_turn_and_unknown_history(self):
        project = self.root / "child"
        project.mkdir()
        self.call(
            "enter", prompt="Unclassified earlier discussion", source_ref="source-1"
        )
        self.base["turn_id"] = "turn-2"
        self.call("enter", prompt="Hello", source_ref="source-2")
        self.call("classify", kind="non-engineering", reason="A greeting")
        self.call("bind-project", project_root=str(project))
        state = self.call("resume")["state"]
        self.assertEqual("turn-2", state["active_turn"])
        self.assertEqual("source-1", state["turns"]["turn-1"]["source_ref"])
        self.assertEqual("non-engineering", state["turns"]["turn-2"]["kind"])
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_single_file_views_and_noop_reconcile(self):
        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        self.assertEqual(ref["snapshot_path"], ref["journal_path"])
        text = (self.root / ref["snapshot_path"]).read_text(encoding="utf-8")
        for heading in (
            "Current Specification",
            "Decision History",
            "Pending Discussion",
            "Completeness Gaps",
        ):
            self.assertIn("## " + heading, text)
        result = reconcile_working_bundle(
            self.root,
            ref["working_id"],
            text,
            {},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual(ref["revision"], result["working_spec"]["revision"])
        self.assertFalse(list((self.root / "spec-governance").glob("WORKING*")))

    def test_implemented_history_does_not_block_new_discussion(self):
        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        path = self.root / ref["snapshot_path"]
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "status: working", "status: implemented", 1
            ),
            encoding="utf-8",
        )
        historical = path.read_bytes()
        self.base = {"task_ref": "task-b", "turn_id": "turn-2"}
        self.assertEqual("PASS", self.enter()["verdict"])
        self.assertEqual(historical, path.read_bytes())

    def test_legacy_migration_preserves_events_and_budget(self):
        import spec_contract as contract

        self.enter()
        self.call("stop", reply_text="missing")
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        canonical = self.root / ref["snapshot_path"]
        text = canonical.read_text(encoding="utf-8")
        events, continuity = contract._read_journal(canonical)
        self.assertEqual("continuous", continuity)
        legacy = self.root / "spec-governance" / (ref["working_id"] + ".md")
        journal = legacy.with_suffix(".journal.jsonl")
        legacy.write_text(
            text.split("\n<!-- spec-audit:start -->")[0], encoding="utf-8"
        )
        journal.write_text(
            "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n",
            encoding="utf-8",
        )
        # A duplicate canonical/legacy identity must not silently select either copy.
        self.assertEqual(
            "invalid",
            contract.resolve_working_bundle(self.root, reference=ref["working_id"])[
                "state"
            ],
        )
        result = contract._migrate_flat_bundle(self.root, ref["working_id"])
        self.assertEqual("PASS", result["verdict"], result)
        migrated, _ = contract._read_journal(canonical)
        self.assertEqual(events, migrated[:-1])
        self.assertFalse(legacy.exists())
        self.assertTrue(legacy.with_name(legacy.name + ".migrated").exists())
        self.assertTrue(self.call("status")["repair_used"])

    def test_migration_conflict_keeps_originals(self):
        import spec_contract as contract

        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        canonical = self.root / ref["snapshot_path"]
        text = canonical.read_text(encoding="utf-8")
        events, _ = contract._read_journal(canonical)
        legacy = self.root / "spec-governance" / (ref["working_id"] + ".md")
        journal = legacy.with_suffix(".journal.jsonl")
        legacy.write_text(
            text.split("\n<!-- spec-audit:start -->")[0], encoding="utf-8"
        )
        journal.write_text(
            "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
        )
        canonical.write_text(
            text.replace("revision: 1", "revision: 9"), encoding="utf-8"
        )
        before = [path.read_bytes() for path in (canonical, legacy, journal)]
        self.assertEqual(
            "BLOCKED",
            contract._migrate_flat_bundle(self.root, ref["working_id"])["verdict"],
        )
        self.assertEqual(
            before, [path.read_bytes() for path in (canonical, legacy, journal)]
        )

    def test_malformed_acceptance_mapping_does_not_lose_saved_discussion(self):
        import spec_contract as contract

        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        directory = self.root / "validation"
        directory.mkdir()
        (directory / ("acceptance-" + ref["spec_id"] + ".json")).write_text(
            '{"acceptance":{"AC-001":null}}', encoding="utf-8"
        )
        self.save()
        current = contract.resolve_working_bundle(
            self.root, reference=ref["working_id"]
        )["working_spec"]
        self.assertEqual("BLOCKED", current["validation_planning"]["verdict"])
        self.assertEqual("PASS", self.call("stop", reply_text="實際答覆")["verdict"])

    def test_layout_callability_is_separate_from_failed_check(self):
        from unittest.mock import patch

        from project_validation_adapter import assess_project_validation

        (self.root / "architecture").mkdir()
        (self.root / "architecture/manifest.yaml").write_text(
            "schema_version: 2", encoding="utf-8"
        )
        for verdict, code in (("PASS", 0), ("FAIL", 1), ("BLOCKED", 2)):
            with self.subTest(verdict=verdict):
                results = [
                    subprocess.CompletedProcess(
                        [], 0, json.dumps({"verdict": "PASS", "required_gates": []}), ""
                    ),
                    subprocess.CompletedProcess(
                        [],
                        code,
                        json.dumps({"verdict": verdict, "diagnostics": []}),
                        "",
                    ),
                ]
                with patch(
                    "project_validation_adapter.subprocess.run", side_effect=results
                ) as run:
                    result = assess_project_validation(self.root, phase="acceptance")
                self.assertEqual(2, run.call_count)
                self.assertTrue(
                    result["capabilities"]["test-validation-layout"]["callable"]
                )
                self.assertEqual(verdict, result["verdict"])

    def test_validation_faults_remain_distinct(self):
        from unittest.mock import patch

        from project_validation_adapter import assess_project_validation

        cases = [
            (subprocess.CompletedProcess([], 0, "bad", ""), "malformed-output"),
            (
                subprocess.CompletedProcess([], 2, '{"verdict":"PASS"}', ""),
                "exit-code-mismatch",
            ),
            (
                subprocess.CompletedProcess([], 1, "", "ModuleNotFoundError: missing"),
                "dependency-load-failure",
            ),
            (subprocess.TimeoutExpired("fixture", 30), "timeout"),
        ]
        for value, category in cases:
            with self.subTest(category=category):
                kw = (
                    {"side_effect": value}
                    if isinstance(value, Exception)
                    else {"return_value": value}
                )
                with patch("project_validation_adapter.subprocess.run", **kw):
                    result = assess_project_validation(self.root)
                self.assertEqual("BLOCKED", result["verdict"])
                self.assertEqual(category, result["diagnoses"][0]["category"])

    def test_acceptance_delta_survives_reload_until_mapping_rebound(self):
        import spec_contract as contract
        from test_spec_governance import confirmed_spec

        (self.root / "validation").mkdir()
        started = contract.start_working_bundle(
            self.root,
            "payment-retry",
            confirmed_spec(status="working"),
            task_ref="mapping",
        )
        ref = started["working_spec"]
        path = self.root / ref["snapshot_path"]
        mapping = self.root / "validation" / ("acceptance-" + ref["spec_id"] + ".json")
        mapping.write_text('{"acceptance":{"AC-001":{}}}', encoding="utf-8")
        current = path.read_text(encoding="utf-8")
        changed = current.replace(
            "A fourth attempt is never made.",
            "A fourth attempt is denied and recorded.",
        )
        result = contract.reconcile_working_bundle(
            self.root,
            ref["working_id"],
            changed,
            {},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", result["verdict"], result)
        planning = contract.resolve_working_bundle(
            self.root, reference=ref["working_id"]
        )["working_spec"]["validation_planning"]
        self.assertEqual(["AC-001"], planning["changed"])
        self.assertEqual("BLOCKED", planning["verdict"])
        mapping.write_text(
            json.dumps(
                {
                    "acceptance": {
                        "AC-001": {
                            "criterion_sha256": planning["criterion_hashes"]["AC-001"]
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            "PASS",
            contract.resolve_working_bundle(self.root, reference=ref["working_id"])[
                "working_spec"
            ]["validation_planning"]["verdict"],
        )

    def test_complete_adopted_contract_confirms_in_same_file_with_sourced_review(self):
        import spec_contract as contract
        from test_spec_governance import confirmed_spec

        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        text = confirmed_spec(status="working")
        result = contract.reconcile_working_bundle(
            self.root,
            ref["working_id"],
            text,
            {},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", result["verdict"], result)
        review = {
            name: {
                "source_ref": "fixture-reviewed-spec",
                "evidence": "Reviewed explicit "
                + name
                + " against the adopted retry contract",
            }
            for name in ("goal", "scope", "behavior", "exceptions", "acceptance")
        }
        saved = self.save(completeness_review=review)
        self.assertIsNone(saved["confirmation"])
        self.assertEqual(
            "working",
            self.call("status")["binding"]["status"]
            if "status" in self.call("status")["binding"]
            else contract.resolve_working_bundle(
                self.root, reference=ref["working_id"]
            )["working_spec"]["status"],
        )
        unknown = self.save(
            completeness_review=review,
            user_confirmed=True,
            confirmation_source_ref="unobserved-user",
        )
        self.assertIsNone(unknown["confirmation"])
        saved = self.save(
            completeness_review=review,
            user_confirmed=True,
            confirmation_source_ref="fixture-user-1",
        )
        self.assertEqual("PASS", saved["confirmation"]["verdict"])
        after = saved["confirmation"]["working_spec"]
        self.assertEqual(ref["snapshot_path"], after["snapshot_path"])
        self.assertEqual(ref["spec_id"], after["spec_id"])
        self.assertEqual("confirmed", after["status"])
        self.assertFalse(saved["product_code_allowed"])

    def test_blank_contract_cannot_confirm_even_with_review(self):
        import spec_contract as contract
        from test_spec_governance import confirmed_spec

        text = (
            confirmed_spec()
            .replace("Retries are inconsistent.", "")
            .replace("Use one bounded retry policy.", "")
            .replace("Retry at most three times.", "")
            .replace("A fourth attempt is never made.", "")
        )
        gaps = contract._contract_completeness_gaps(self.root, text)
        self.assertTrue(any("problem" in gap for gap in gaps), gaps)
        self.assertTrue(any("REQ-001" in gap for gap in gaps), gaps)
        self.assertTrue(any("AC-001" in gap for gap in gaps), gaps)

    def test_top_level_nonobject_mapping_remains_planning_block(self):
        import spec_contract as contract

        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        directory = self.root / "validation"
        directory.mkdir()
        for value in ("[]", "null"):
            (directory / ("acceptance-" + ref["spec_id"] + ".json")).write_text(
                value, encoding="utf-8"
            )
            self.save()
            loaded = contract.resolve_working_bundle(
                self.root, reference=ref["working_id"]
            )
            self.assertEqual(
                "BLOCKED", loaded["working_spec"]["validation_planning"]["verdict"]
            )

    def test_entry_precedes_answer_and_has_no_formal_spec(self):
        self.enter()
        context = assess_turn_context(self.root, task_ref="task-a")
        self.assertEqual("ready", context["state"])
        self.assertEqual("SPEC-0001", context["working_spec"]["spec_id"])
        self.assertIn(
            "提出量測方案",
            (self.root / context["working_spec"]["snapshot_path"]).read_text(
                encoding="utf-8"
            ),
        )
        self.assertEqual(
            "working",
            assess_turn_context(self.root, task_ref="task-a")["working_spec"]["status"],
        )
        self.assertEqual("BLOCKED", self.call("status")["verdict"])
        self.save()
        self.assertEqual("PASS", self.call("stop", reply_text="實際答覆")["verdict"])

    def test_same_working_pair_across_mixed_and_short_answers(self):
        first = self.enter()["working_id"]
        for index, prompt in enumerate(["1", "採用 1，另問現況", "只解釋原因"]):
            self.base["turn_id"] = str(index + 2)
            self.assertEqual(first, self.enter(prompt)["working_id"])
        self.assertEqual(1, len(list((self.root / "specs").glob("SPEC*.md"))))

    def test_nonengineering_does_not_create_working_spec(self):
        self.call("enter", prompt="寫一首詩", source_ref="fixture-user")
        self.call(
            "classify", kind="non-engineering", reason="Standalone creative writing"
        )
        self.assertEqual("PASS", self.call("stop", reply_text="詩")["verdict"])
        self.assertEqual([], list((self.root / "spec-governance").glob("WORKING*.md")))

    def test_unknown_is_not_silently_exempt(self):
        self.call(
            "enter",
            prompt="Investigate this unexplained behavior",
            source_ref="fixture-user",
        )
        self.assertEqual("block", self.call("stop")["decision"])

    def test_one_repair_survives_continuation_restart_and_general_recovery(self):
        self.enter()
        repair = self.call("stop", reply_text="missing")
        self.assertEqual("block", repair["decision"])
        self.base["turn_id"] = "continuation-2"
        self.call("enter", prompt=repair["reason"], source_ref="host-continuation")
        self.call("resume")  # fresh process loads the same persisted state
        for _ in range(3):
            result = self.call("stop", reply_text="still missing")
            self.assertTrue(result["continue"])
            self.assertNotIn("decision", result)
        self.save("direct recovery remains available")
        self.assertEqual("PASS", self.call("status")["verdict"])
        self.assertTrue(self.call("status")["repair_used"])

    def test_duplicate_prompt_cannot_reset_consumed_budget(self):
        self.enter()
        self.call("stop")
        self.enter()
        self.assertTrue(self.call("stop")["continue"])

    def test_wrong_task_stale_binding_and_missing_journal_fail(self):
        self.enter()
        binding = self.call("status")["binding"]
        binding["snapshot_hash"] = "wrong"
        with self.assertRaises(ValueError):
            self.call(
                "record",
                summary="x",
                source_ref="source",
                reply_text="reply",
                binding=binding,
            )
        with self.assertRaises(ValueError):
            discussion_request(
                self.root, {**self.base, "task_ref": "other", "operation": "status"}
            )
        self.save()
        path = next((self.root / "specs").glob("SPEC*.md"))
        path.write_text(
            path.read_text(encoding="utf-8").split("\n<!-- spec-audit:start -->")[0],
            encoding="utf-8",
        )
        self.assertFalse(self.call("stop")["verdict"] == "PASS")

    def test_candidate_deferral_does_not_adopt_or_block_completion(self):
        self.enter()
        self.save(
            candidates=[
                {
                    "id": "candidate-1",
                    "status": "deferred",
                    "source_ref": "assistant-1",
                    "user_source_ref": "user-2",
                    "reason": "Optional optimization",
                    "impact": "Additional code scope",
                }
            ]
        )
        self.assertEqual("PASS", self.call("stop", reply_text="實際答覆")["verdict"])
        self.assertEqual(
            "working",
            assess_turn_context(self.root, task_ref="task-a")["working_spec"]["status"],
        )

    def test_reply_wording_is_audit_only(self):
        self.enter()
        self.save("prepared text")
        self.assertEqual(
            "PASS", self.call("stop", reply_text="different actual reply")["verdict"]
        )

    def test_single_continuation_can_save_successfully(self):
        self.enter()
        repair = self.call("stop")
        self.base["turn_id"] = "continuation"
        self.call("enter", prompt=repair["reason"], source_ref="host-continuation")
        self.save("saved")
        self.assertEqual("PASS", self.call("stop", reply_text="saved")["verdict"])
        self.assertTrue(self.call("status")["repair_used"])

    def test_candidate_fields_are_redacted(self):
        self.enter()
        self.save(
            candidates=[
                {
                    "id": "c1",
                    "status": "candidate",
                    "source_ref": "assistant",
                    "reason": "api_key=fixture-secret",
                    "impact": "Optional",
                }
            ]
        )
        for path in (self.root / "spec-governance").glob("*"):
            if path.suffix != ".lock":
                self.assertNotIn("fixture-secret", path.read_text(encoding="utf-8"))

    def test_saved_current_revision_restores_entry_admission(self):
        self.enter()
        context = assess_turn_context(self.root, task_ref="task-a")
        ref = context["working_spec"]
        text = (self.root / ref["snapshot_path"]).read_text(encoding="utf-8")
        reconcile_working_bundle(
            self.root,
            ref["working_id"],
            text.replace("Engineering discussion", "Engineering facts"),
            {"added_ids": [], "changed_ids": [], "removed_ids": []},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertFalse(self.call("status")["entry_saved"])
        self.save()
        self.assertTrue(self.call("status")["entry_saved"])
        context = assess_turn_context(self.root, task_ref="task-a")
        result = finish_discussion_turn(
            self.root,
            reference=ref["working_id"],
            task_ref="task-a",
            observation={
                "turn_id": "turn-1",
                "reply_text": "實際答覆",
                "working_spec": context["working_spec"],
            },
        )
        self.assertEqual("PASS", result["verdict"])

    def test_killed_process_releases_lock_without_resetting_repair(self):
        self.enter()
        self.call("stop")
        code = "import sys,os;sys.path.insert(0,sys.argv[1]);import discussion_state as d;from pathlib import Path;d._operate=lambda *a:os._exit(3);d.discussion_request(Path(sys.argv[2]),{'operation':'resume','task_ref':'task-a'})"
        run = subprocess.run(
            [
                sys.executable,
                "-c",
                code,
                str(ROOT / "skills/engineering/spec-governance/scripts"),
                str(self.root),
            ],
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(3, run.returncode, run.stderr)
        self.assertTrue(self.call("status")["repair_used"])
        self.assertTrue(self.call("stop")["continue"])

    def test_steered_input_same_turn_is_saved_without_budget_reset(self):
        self.enter()
        self.call("stop")
        self.enter("增加限制：不能修改硬體")
        files = "".join(
            p.read_text(encoding="utf-8")
            for p in (self.root / "spec-governance").glob("*.json*")
        )
        self.assertIn("增加限制", files)
        self.assertTrue(self.call("status")["repair_used"])

    def test_invalid_save_after_retry_does_not_poison_valid_save(self):
        self.enter()
        self.call("stop")
        self.save("reply A")
        with self.assertRaises(ValueError):
            self.call(
                "record", binding={}, summary="bad", reply_text="bad", source_ref="bad"
            )
        self.assertEqual("PASS", self.call("verify", reply_text="reply B")["verdict"])

    def test_failed_unknown_turn_can_be_classified_after_exhaustion(self):
        self.call("enter", prompt="hello", source_ref="fixture-user")
        self.call("stop")
        self.call("stop")
        self.call("classify", kind="non-engineering", reason="greeting")
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_previous_turn_cannot_finish_unsaved_current_turn(self):
        self.enter()
        self.save("reply A")
        previous = self.base["turn_id"]
        self.base["turn_id"] = "turn-2"
        self.enter("請繼續說明")
        context = assess_turn_context(self.root, task_ref="task-a")
        result = finish_discussion_turn(
            self.root,
            reference=context["working_spec"]["working_id"],
            task_ref="task-a",
            observation={
                "turn_id": previous,
                "reply_text": "reply A",
                "working_spec": context["working_spec"],
            },
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertTrue(result["can_end_turn"])
        self.assertFalse(result["product_code_allowed"])

    def test_candidate_cannot_store_unbounded_nested_fields(self):
        self.enter()
        with self.assertRaisesRegex(ValueError, "unsupported candidate fields"):
            self.save(
                candidates=[
                    {
                        "id": "C1",
                        "status": "candidate",
                        "source_ref": "fixture",
                        "reason": "reason",
                        "impact": "impact",
                        "metadata": {"password": "fixture-secret"},
                    }
                ]
            )
        files = "".join(
            p.read_text(encoding="utf-8")
            for p in (self.root / "spec-governance").glob("*.json*")
        )
        self.assertNotIn("fixture-secret", files)

    def test_changed_spec_can_be_rechecked_after_exhaustion(self):
        self.enter()
        self.call("stop")
        self.call("stop")
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        text = (self.root / ref["snapshot_path"]).read_text(encoding="utf-8")
        result = reconcile_working_bundle(
            self.root,
            ref["working_id"],
            text.replace("Engineering discussion", "Repaired discussion"),
            {},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", result["verdict"])
        self.assertEqual("block", self.call("stop")["decision"])
        self.assertNotIn("decision", self.call("stop"))
        self.save()
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_new_turn_id_alone_does_not_repeat_automatic_repair(self):
        self.enter()
        self.call("stop")
        self.base["turn_id"] = "replayed-under-another-id"
        self.enter()
        result = self.call("stop")
        self.assertNotIn("decision", result)
        self.assertTrue(result["continue"])
        self.save()
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_v1_failed_state_migrates_without_erasing_history(self):
        self.enter()
        self.call("stop")
        self.call("stop")
        path = next((self.root / "spec-governance").glob("DISCUSSION-*.json"))
        state = json.loads(path.read_text(encoding="utf-8"))
        state["schema_version"] = 1
        state["turns"]["turn-1"].pop("repair_keys", None)
        path.write_text(json.dumps(state), encoding="utf-8")
        self.assertNotIn("decision", self.call("stop"))
        self.save()
        current = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(2, current["schema_version"])
        self.assertTrue(current["turns"]["turn-1"]["legacy_repair"]["repair_failed"])
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_product_authority_is_independent_of_historical_repair_failure(self):
        import hashlib

        import spec_contract as contract
        from managed_delivery import execute_request
        from test_spec_governance import confirmed_spec

        started = contract.start_working_bundle(
            self.root,
            "payment-retry",
            confirmed_spec(status="working"),
            task_ref="task-a",
        )
        ref = started["working_spec"]
        confirmed = contract.materialize_working_bundle(
            self.root,
            ref["working_id"],
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        ref = confirmed["working_spec"]
        self.enter(working_reference=ref["working_id"])
        self.call("stop")
        self.call("stop")
        self.save()
        base = {
            "task_ref": "task-a",
            "spec": ref["snapshot_path"],
            "working_reference": ref["working_id"],
        }
        target = self.root / "product.txt"
        target.write_text("before", encoding="utf-8")
        patch = {
            **base,
            "operation": "apply",
            "patch": {
                "path": "product.txt",
                "before_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "content": "after",
            },
        }
        self.assertEqual("BLOCKED", execute_request(self.root, patch)["verdict"])
        authorized = execute_request(
            self.root,
            {
                **base,
                "operation": "authorize",
                "instruction": "開始執行",
                "source_event_id": "fixture-explicit-authorization",
                "expected_hash": hashlib.sha256(
                    (self.root / ref["snapshot_path"]).read_bytes()
                ).hexdigest(),
            },
        )
        self.assertEqual("PASS", authorized["verdict"], authorized)
        state_path = next((self.root / "spec-governance").glob("DISCUSSION-*.json"))
        original_state = state_path.read_text(encoding="utf-8")
        incomplete = json.loads(original_state)
        incomplete["turns"]["turn-1"]["saved"] = None
        state_path.write_text(json.dumps(incomplete), encoding="utf-8")
        pending = self.call("status")
        self.assertTrue(pending["entry_saved"])
        self.assertEqual("BLOCKED", pending["verdict"])
        self.assertEqual("BLOCKED", execute_request(self.root, patch)["verdict"])
        self.assertEqual("before", target.read_text(encoding="utf-8"))
        state_path.write_text(original_state, encoding="utf-8")
        self.assertEqual("PASS", execute_request(self.root, patch)["verdict"])
        self.assertEqual("after", target.read_text(encoding="utf-8"))
        # A sourced audit append preserves the authorized contract and receipt.
        self.save("additional sourced observation")
        patch["patch"]["before_sha256"] = hashlib.sha256(
            target.read_bytes()
        ).hexdigest()
        patch["patch"]["content"] = "continued"
        continued = execute_request(self.root, patch)
        self.assertEqual("PASS", continued["verdict"], continued)
        self.assertEqual("continued", target.read_text(encoding="utf-8"))

    def test_router_keeps_read_only_support_when_persistence_is_unavailable(self):
        from unittest.mock import patch

        sys.path.insert(
            0, str(ROOT / "skills/engineering/engineering-risk-routing/scripts")
        )
        import guided_workflow_router as router

        (self.root / "app.py").write_text('print("hello")', encoding="utf-8")
        with patch.object(
            router,
            "manage_delivery_discussion",
            side_effect=ValueError("fixture store unavailable"),
        ):
            result = router.route(
                "Explain this code",
                self.root,
                explicit_skill="explain-code-flow",
                task_ref="task-a",
                turn_ref="turn-1",
                source_ref="fixture-input",
                turn_kind="read-only",
            )
        self.assertTrue(result["discussion_recovery"]["discussion_allowed"])
        self.assertEqual(result["supporting_skill"], result["selected_skill"])
        self.assertFalse(result["product_code_allowed"])

    def test_missing_v2_repair_history_is_not_reset(self):
        self.enter()
        self.call("stop")
        path = next((self.root / "spec-governance").glob("DISCUSSION-*.json"))
        state = json.loads(path.read_text(encoding="utf-8"))
        state["turns"]["turn-1"].pop("repair_keys")
        bad = json.dumps(state)
        path.write_text(bad, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "repair input history"):
            self.call("stop")
        self.assertEqual(bad, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


class RetiredHookTests(unittest.TestCase):
    def test_legacy_health_is_readonly_and_no_longer_requires_host_firing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = discussion_request(
                root, {"operation": "hook-health", "task_ref": "legacy-task"}
            )
            self.assertTrue(result["retired"])
            self.assertEqual([], result["supported"]["adapter_events"])
            self.assertEqual("not-applicable", result["fired"])
            with self.assertRaisesRegex(ValueError, "retired"):
                discussion_request(
                    root,
                    {"operation": "record-hook-observation", "task_ref": "legacy-task"},
                )
