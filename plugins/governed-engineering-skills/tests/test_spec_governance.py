from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEST_TEMP_ROOT = PLUGIN_ROOT / ".tmp" / "test-spec-governance"
TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TEST_TEMP_ROOT)
MODULE_PATH = (
    PLUGIN_ROOT
    / "skills"
    / "spec-governance"
    / "scripts"
    / "spec_contract.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("spec_contract", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SPEC_CONTRACT = load_module()


def confirmed_spec(
    *,
    spec_id: str = "SPEC-0001",
    slug: str = "payment-retry",
    status: str = "confirmed",
    evidence: str = "pending",
    review: str = "pending",
) -> str:
    return f"""---
spec_version: 1
spec_id: {spec_id}
revision: 1
status: {status}
change_set: {slug}
---

# Payment retry

## Problem

Retries are inconsistent.

## Solution

Use one bounded retry policy.

## User Stories

- As an operator, I can observe retry exhaustion.

## Requirements

| ID | Requirement |
|---|---|
| REQ-001 | Retry at most three times. |

## Decisions

| ID | Decision |
|---|---|
| DEC-001 | Use exponential backoff. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | A fourth attempt is never made. | `test_retry_limit` | {evidence} |

## Relationships

| Source | Relation | Target |
|---|---|---|
| REQ-001 | depends_on | DEC-001 |

## Out of Scope

- Changing payment providers.

## Open Decisions

None.

## Routing/Gates

- TDD
- Code review
- Spec review: {review}

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-02 | Initial confirmed contract. |
"""


class CanonicalSpecValidationTests(unittest.TestCase):
    def test_confirmed_spec_passes_with_requirement_coverage(self) -> None:
        result = SPEC_CONTRACT.validate_spec_text(confirmed_spec())

        self.assertEqual("PASS", result["verdict"])
        self.assertEqual([], result["errors"])
        self.assertEqual([], result["traceability"]["uncovered_requirements"])

    def test_missing_acceptance_coverage_blocks_confirmation(self) -> None:
        text = confirmed_spec().replace("REQ-001 | A fourth", "REQ-999 | A fourth")

        result = SPEC_CONTRACT.validate_spec_text(text)

        self.assertEqual("BLOCKED", result["verdict"])
        self.assertIn("REQ-001", result["traceability"]["uncovered_requirements"])
        self.assertTrue(any("REQ-999" in error for error in result["errors"]))

    def test_open_decision_and_invalid_relation_block_confirmation(self) -> None:
        text = confirmed_spec().replace(
            "None.\n\n## Routing/Gates",
            "- Choose jitter strategy.\n\n## Routing/Gates",
        ).replace(
            "| REQ-001 | depends_on | DEC-001 |",
            "| REQ-001 | depends_on | DEC-999 |",
        )

        result = SPEC_CONTRACT.validate_spec_text(text)

        self.assertEqual("BLOCKED", result["verdict"])
        self.assertTrue(any("open decisions" in error.casefold() for error in result["errors"]))
        self.assertTrue(any("DEC-999" in error for error in result["errors"]))

    def test_dangling_cross_spec_reference_blocks_without_repository_evidence(self) -> None:
        text = confirmed_spec().replace(
            "| REQ-001 | depends_on | DEC-001 |",
            "| REQ-001 | refines | SPEC-9999 |",
        )

        result = SPEC_CONTRACT.validate_spec_text(text)

        self.assertEqual("BLOCKED", result["verdict"])
        self.assertTrue(any("SPEC-9999" in error for error in result["errors"]))

    def test_implemented_requires_pass_evidence_and_spec_review(self) -> None:
        blocked = SPEC_CONTRACT.validate_spec_text(
            confirmed_spec(status="implemented")
        )
        passed = SPEC_CONTRACT.validate_spec_text(
            confirmed_spec(
                status="implemented",
                evidence="PASS: tests.test_retry_limit",
                review="PASS",
            )
        )

        self.assertEqual("BLOCKED", blocked["verdict"])
        self.assertEqual("PASS", passed["verdict"])


class CanonicalSpecLifecycleTests(unittest.TestCase):
    def test_reconcile_reuses_stable_ids_and_reports_delta(self) -> None:
        working = {
            "requirements": [{"id": "REQ-001", "text": "Retry at most three times."}],
            "decisions": [],
            "acceptance_criteria": [],
        }

        result = SPEC_CONTRACT.reconcile_working_spec(
            working,
            {
                "requirements": [
                    "Retry at most three times.",
                    "Record retry exhaustion.",
                ],
                "decisions": ["Use exponential backoff."],
            },
        )

        self.assertEqual("REQ-001", result["working_spec"]["requirements"][0]["id"])
        self.assertEqual("REQ-002", result["working_spec"]["requirements"][1]["id"])
        self.assertEqual("DEC-001", result["working_spec"]["decisions"][0]["id"])
        self.assertEqual(["REQ-002", "DEC-001"], result["delta"]["added_ids"])

    def test_reconcile_updates_existing_item_without_replacing_its_id(self) -> None:
        result = SPEC_CONTRACT.reconcile_working_spec(
            {
                "requirements": [
                    {"id": "REQ-001", "text": "Retry failed payments."},
                ],
                "decisions": [],
                "acceptance_criteria": [],
            },
            {
                "requirements": [
                    {
                        "id": "REQ-001",
                        "text": "Retry failed payments at most three times.",
                    },
                ],
            },
        )

        self.assertEqual(
            [
                {
                    "id": "REQ-001",
                    "text": "Retry failed payments at most three times.",
                },
            ],
            result["working_spec"]["requirements"],
        )
        self.assertEqual(["REQ-001"], result["delta"]["changed_ids"])
        self.assertEqual([], result["delta"]["added_ids"])

    def test_reconcile_reports_removed_ids_and_drops_their_relationships(self) -> None:
        result = SPEC_CONTRACT.reconcile_working_spec(
            {
                "requirements": [
                    {"id": "REQ-001", "text": "Retry failed payments."},
                    {"id": "REQ-002", "text": "Record retry exhaustion."},
                ],
                "decisions": [],
                "acceptance_criteria": [],
                "relationships": [
                    {
                        "source": "REQ-001",
                        "relation": "depends_on",
                        "target": "REQ-002",
                    },
                ],
            },
            {"removed_ids": ["REQ-002"]},
        )

        self.assertEqual(
            [{"id": "REQ-001", "text": "Retry failed payments."}],
            result["working_spec"]["requirements"],
        )
        self.assertEqual(["REQ-002"], result["delta"]["removed_ids"])
        self.assertEqual([], result["relationships"])

    def test_reconcile_preserves_relationships_across_rounds(self) -> None:
        existing = {
            "source": "REQ-001",
            "relation": "depends_on",
            "target": "DEC-001",
        }
        added = {
            "source": "AC-001",
            "relation": "depends_on",
            "target": "REQ-001",
        }
        result = SPEC_CONTRACT.reconcile_working_spec(
            {
                "requirements": [
                    {"id": "REQ-001", "text": "Retry failed payments."},
                ],
                "decisions": [
                    {"id": "DEC-001", "text": "Use exponential backoff."},
                ],
                "acceptance_criteria": [
                    {"id": "AC-001", "text": "A fourth attempt is never made."},
                ],
                "relationships": [existing],
            },
            {"relationships": [added]},
        )

        self.assertEqual([existing, added], result["relationships"])
        self.assertEqual([existing, added], result["working_spec"]["relationships"])

    def test_reconcile_retains_unresolved_state_and_conflicts_block(self) -> None:
        first = SPEC_CONTRACT.reconcile_working_spec(
            {
                "requirements": [],
                "decisions": [],
                "acceptance_criteria": [],
            },
            {
                "open_decisions": ["Choose retry owner."],
                "conflicts": [{"source": "REQ-001", "target": "DEC-001"}],
            },
        )
        second = SPEC_CONTRACT.reconcile_working_spec(
            first["working_spec"],
            {"requirements": ["Retry at most three times."]},
        )

        self.assertEqual("BLOCKED", first["verdict"])
        self.assertEqual("BLOCKED", second["verdict"])
        self.assertEqual(["Choose retry owner."], second["open_decisions"])
        self.assertEqual(first["conflicts"], second["conflicts"])

    def test_materialization_does_not_require_product_authorization_and_uses_next_number(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            specs = root / "specs"
            specs.mkdir()
            (specs / "SPEC-0007-existing.md").write_text(
                confirmed_spec(spec_id="SPEC-0007", slug="existing"),
                encoding="utf-8",
            )

            created = SPEC_CONTRACT.materialize_spec(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000"),
                authorized=False,
            )

            self.assertEqual("PASS", created["verdict"])
            self.assertEqual("SPEC-0008", created["canonical_spec"]["spec_id"])
            self.assertTrue((root / created["canonical_spec"]["path"]).is_file())
            self.assertFalse(created["product_execution_authorized"])

    def test_materialization_rejects_working_and_implemented_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for status in ("working", "implemented"):
                result = SPEC_CONTRACT.materialize_spec(
                    root,
                    f"{status}-change",
                    confirmed_spec(
                        spec_id="SPEC-0000",
                        slug=f"{status}-change",
                        status=status,
                        evidence="PASS: test" if status == "implemented" else "pending",
                        review="PASS" if status == "implemented" else "pending",
                    ),
                )
                self.assertEqual("BLOCKED", result["verdict"])
            self.assertFalse((root / "specs").exists())

    def test_working_bundle_persists_snapshot_and_normalized_hash_linked_journal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = SPEC_CONTRACT.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000", status="working"),
                task_ref="task-123",
                branch="feature/payment-retry",
            )

            reference = started["working_spec"]
            self.assertEqual("PASS", started["verdict"])
            self.assertEqual("continuous", reference["continuity"])
            self.assertTrue((root / reference["snapshot_path"]).is_file())
            journal_path = root / reference["journal_path"]
            first_event = json.loads(journal_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual("start", first_event["event_type"])
            self.assertEqual(reference["snapshot_hash"], first_event["snapshot_hash"])
            self.assertIn("event_hash", first_event)

            next_snapshot = confirmed_spec(
                spec_id="SPEC-0000",
                status="working",
            ).replace(
                "Retry at most three times.",
                "Retry failed payments at most three times.",
            )
            reconciled = SPEC_CONTRACT.reconcile_working_bundle(
                root,
                reference["working_id"],
                next_snapshot,
                {
                    "changed_ids": ["REQ-001"],
                    "relationships": [
                        {
                            "source": "REQ-001",
                            "relation": "depends_on",
                            "target": "DEC-001",
                        }
                    ],
                    "conflicts": [],
                    "open_decisions": [],
                    "raw_answer": "this must never reach the journal",
                },
                expected_revision=reference["revision"],
                expected_hash=reference["snapshot_hash"],
            )

            self.assertEqual("PASS", reconciled["verdict"])
            self.assertEqual(2, reconciled["working_spec"]["revision"])
            journal = journal_path.read_text(encoding="utf-8")
            self.assertNotIn("this must never reach the journal", journal)
            events = [json.loads(line) for line in journal.splitlines()]
            self.assertEqual(events[0]["event_hash"], events[1]["previous_event_hash"])
            self.assertEqual(["REQ-001"], events[1]["affected_ids"])

    def test_stale_working_writer_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = SPEC_CONTRACT.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000", status="working"),
            )
            reference = started["working_spec"]
            snapshot_path = root / reference["snapshot_path"]
            before = snapshot_path.read_text(encoding="utf-8")

            result = SPEC_CONTRACT.reconcile_working_bundle(
                root,
                reference["working_id"],
                before,
                {},
                expected_revision=99,
                expected_hash="stale",
            )

            self.assertEqual("BLOCKED", result["verdict"])
            self.assertEqual("stale working specification", result["reason"])
            self.assertEqual(before, snapshot_path.read_text(encoding="utf-8"))

    def test_working_resolution_is_explicit_then_task_then_branch_then_unique(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = SPEC_CONTRACT.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000", status="working"),
                working_id="WSP-aaaaaaaaaaaa-payment-retry",
                task_ref="task-payment",
                branch="feature/payment",
            )["working_spec"]
            second = SPEC_CONTRACT.start_working_bundle(
                root,
                "invoice-export",
                confirmed_spec(
                    spec_id="SPEC-0000",
                    slug="invoice-export",
                    status="working",
                ),
                working_id="WSP-bbbbbbbbbbbb-invoice-export",
                task_ref="task-invoice",
                branch="feature/invoice",
            )["working_spec"]

            ambiguous = SPEC_CONTRACT.resolve_working_bundle(root)
            explicit = SPEC_CONTRACT.resolve_working_bundle(
                root,
                reference=first["snapshot_path"],
                task_ref="task-invoice",
                branch="feature/invoice",
            )
            by_task = SPEC_CONTRACT.resolve_working_bundle(
                root,
                task_ref="task-invoice",
                branch="feature/payment",
            )
            by_branch = SPEC_CONTRACT.resolve_working_bundle(
                root,
                branch="feature/payment",
            )

            self.assertEqual("ambiguous", ambiguous["state"])
            self.assertEqual(first["working_id"], explicit["working_spec"]["working_id"])
            self.assertEqual(second["working_id"], by_task["working_spec"]["working_id"])
            self.assertEqual(first["working_id"], by_branch["working_spec"]["working_id"])

    def test_invalid_journal_chain_marks_continuity_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = SPEC_CONTRACT.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000", status="working"),
            )["working_spec"]
            journal_path = root / reference["journal_path"]
            event = json.loads(journal_path.read_text(encoding="utf-8"))
            event["snapshot_hash"] = "0" * 64
            journal_path.write_text(json.dumps(event) + "\n", encoding="utf-8")

            resolved = SPEC_CONTRACT.resolve_working_bundle(
                root,
                reference=reference["working_id"],
            )

            self.assertEqual("working", resolved["state"])
            self.assertEqual(
                "unavailable",
                resolved["working_spec"]["continuity"],
            )

    def test_reconcile_derives_blocking_state_from_authoritative_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = SPEC_CONTRACT.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000", status="working"),
            )["working_spec"]
            next_snapshot = (
                (root / reference["snapshot_path"])
                .read_text(encoding="utf-8")
                .replace(
                    "None.\n\n## Routing/Gates",
                    "- Choose retry owner.\n\n## Routing/Gates",
                )
            )

            result = SPEC_CONTRACT.reconcile_working_bundle(
                root,
                reference["working_id"],
                next_snapshot,
                {
                    "conflicts": [],
                    "open_decisions": [],
                },
                expected_revision=reference["revision"],
                expected_hash=reference["snapshot_hash"],
            )

            self.assertEqual("BLOCKED", result["verdict"])
            self.assertEqual(["Choose retry owner."], result["open_decisions"])

    def test_missing_journal_starts_unavailable_continuity_epoch_from_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = SPEC_CONTRACT.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000", status="working"),
            )
            reference = started["working_spec"]
            (root / reference["journal_path"]).unlink()
            next_snapshot = (
                (root / reference["snapshot_path"])
                .read_text(encoding="utf-8")
                .replace(
                    "None.\n\n## Routing/Gates",
                    "- Choose retry owner.\n\n## Routing/Gates",
                )
            )

            result = SPEC_CONTRACT.reconcile_working_bundle(
                root,
                reference["working_id"],
                next_snapshot,
                {"open_decisions": ["Choose retry owner."]},
                expected_revision=reference["revision"],
                expected_hash=reference["snapshot_hash"],
            )

            self.assertEqual("BLOCKED", result["verdict"])
            self.assertEqual("unavailable", result["working_spec"]["continuity"])
            event = json.loads(
                (root / reference["journal_path"]).read_text(encoding="utf-8")
            )
            self.assertEqual("unavailable", event["continuity"])
            self.assertIsNone(event["previous_event_hash"])

    def test_decision_complete_bundle_materializes_before_product_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = SPEC_CONTRACT.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000", status="working"),
            )
            reference = started["working_spec"]

            result = SPEC_CONTRACT.materialize_working_bundle(
                root,
                reference["working_id"],
                expected_revision=reference["revision"],
                expected_hash=reference["snapshot_hash"],
            )

            self.assertEqual("PASS", result["verdict"])
            self.assertTrue((root / result["canonical_spec"]["path"]).is_file())
            self.assertFalse(result["product_execution_authorized"])

    def test_confirmed_spec_reopens_same_identity_and_no_delta_retains_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "specs" / "SPEC-0001-payment-retry.md"
            path.parent.mkdir()
            path.write_text(confirmed_spec(), encoding="utf-8")

            reopened = SPEC_CONTRACT.reopen_spec(
                root,
                Path("specs/SPEC-0001-payment-retry.md"),
                expected_revision=1,
                reason="Check whether retry ownership changed.",
            )
            reference = reopened["working_spec"]
            self.assertIn("status: working", path.read_text(encoding="utf-8"))
            reconfirmed = SPEC_CONTRACT.materialize_working_bundle(
                root,
                reference["working_id"],
                expected_revision=reference["revision"],
                expected_hash=reference["snapshot_hash"],
            )

            self.assertEqual("SPEC-0001", reopened["canonical_spec"]["spec_id"])
            self.assertEqual("PASS", reconfirmed["verdict"])
            self.assertTrue(reconfirmed["authorization_retained"])
            self.assertFalse(reconfirmed["actual_contract_delta"])
            self.assertIn("status: confirmed", path.read_text(encoding="utf-8"))

    def test_reopened_contract_delta_invalidates_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "specs" / "SPEC-0001-payment-retry.md"
            path.parent.mkdir()
            path.write_text(confirmed_spec(), encoding="utf-8")
            reopened = SPEC_CONTRACT.reopen_spec(
                root,
                path,
                expected_revision=1,
                reason="Retry limit might change.",
            )
            reference = reopened["working_spec"]
            changed = (root / reference["snapshot_path"]).read_text(encoding="utf-8").replace(
                "Retry at most three times.",
                "Retry at most four times.",
            ).replace(
                "A fourth attempt is never made.",
                "A fifth attempt is never made.",
            )
            reconciled = SPEC_CONTRACT.reconcile_working_bundle(
                root,
                reference["working_id"],
                changed,
                {"changed_ids": ["REQ-001", "AC-001"]},
                expected_revision=reference["revision"],
                expected_hash=reference["snapshot_hash"],
            )
            reconfirmed = SPEC_CONTRACT.materialize_working_bundle(
                root,
                reference["working_id"],
                expected_revision=reconciled["working_spec"]["revision"],
                expected_hash=reconciled["working_spec"]["snapshot_hash"],
            )

            self.assertEqual("PASS", reconfirmed["verdict"])
            self.assertTrue(reconfirmed["actual_contract_delta"])
            self.assertFalse(reconfirmed["authorization_retained"])

    def test_reopened_confirmed_decision_must_be_preserved_and_superseded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "specs" / "SPEC-0001-payment-retry.md"
            path.parent.mkdir()
            path.write_text(confirmed_spec(), encoding="utf-8")
            reference = SPEC_CONTRACT.reopen_spec(
                root,
                path,
                expected_revision=1,
                reason="Backoff policy may change.",
            )["working_spec"]
            current = (root / reference["snapshot_path"]).read_text(encoding="utf-8")
            rewritten = current.replace(
                "Use exponential backoff.",
                "Use linear backoff.",
            )

            blocked = SPEC_CONTRACT.reconcile_working_bundle(
                root,
                reference["working_id"],
                rewritten,
                {},
                expected_revision=reference["revision"],
                expected_hash=reference["snapshot_hash"],
            )
            preserved = current.replace(
                "| DEC-001 | Use exponential backoff. |",
                "| DEC-001 | Use exponential backoff. |\n"
                "| DEC-002 | Use linear backoff. |",
            ).replace(
                "| REQ-001 | depends_on | DEC-001 |",
                "| REQ-001 | depends_on | DEC-001 |\n"
                "| DEC-002 | supersedes | DEC-001 |",
            )
            passed = SPEC_CONTRACT.reconcile_working_bundle(
                root,
                reference["working_id"],
                preserved,
                {},
                expected_revision=reference["revision"],
                expected_hash=reference["snapshot_hash"],
            )

            self.assertEqual("BLOCKED", blocked["verdict"])
            self.assertIn("superseded", blocked["reason"])
            self.assertEqual("PASS", passed["verdict"])
            self.assertEqual(["DEC-002"], passed["delta"]["added_ids"])
            self.assertIn(
                {
                    "source": "DEC-002",
                    "relation": "supersedes",
                    "target": "DEC-001",
                },
                passed["relationships"],
            )

    def test_implemented_spec_cannot_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "specs" / "SPEC-0001-payment-retry.md"
            path.parent.mkdir()
            path.write_text(
                confirmed_spec(
                    status="implemented",
                    evidence="PASS: test_retry_limit",
                    review="PASS",
                ),
                encoding="utf-8",
            )

            result = SPEC_CONTRACT.reopen_spec(
                root,
                path,
                expected_revision=1,
                reason="Try to change a closed contract.",
            )

            self.assertEqual("BLOCKED", result["verdict"])
            self.assertIn("cannot reopen", result["reason"])

    def test_commit_preparation_requires_disposition_and_never_performs_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            SPEC_CONTRACT.start_working_bundle(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000", status="working"),
            )

            blocked = SPEC_CONTRACT.prepare_commit(
                root,
                tracked_paths=[],
                staged_paths=[],
            )
            passed = SPEC_CONTRACT.prepare_commit(
                root,
                disposition="keep-local",
                tracked_paths=[],
                staged_paths=[],
            )

            self.assertEqual("BLOCKED", blocked["verdict"])
            self.assertCountEqual(["archive", "delete", "keep-local"], blocked["options"])
            self.assertEqual("PASS", passed["verdict"])
            self.assertFalse(passed["action_performed"])

    def test_commit_preparation_blocks_staged_local_bundle_even_with_disposition(self) -> None:
        result = SPEC_CONTRACT.prepare_commit(
            Path("."),
            disposition="keep-local",
            tracked_paths=[".codex/spec-governance/WSP-x/working.md"],
            staged_paths=[".codex/spec-governance/WSP-x/working.md"],
        )

        self.assertEqual("BLOCKED", result["verdict"])
        self.assertEqual("local working bundle is staged", result["reason"])

    def test_tracker_failure_preserves_local_canonical_spec(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "specs" / "SPEC-0001-payment-retry.md"
            path.parent.mkdir()
            path.write_text(confirmed_spec(), encoding="utf-8")

            result = SPEC_CONTRACT.publish_tracker_snapshot(
                path,
                lambda _path, _snapshot: (_ for _ in ()).throw(RuntimeError("offline")),
            )

            self.assertEqual("BLOCKED", result["verdict"])
            self.assertEqual("tracker publication pending", result["reason"])
            self.assertTrue(path.is_file())

    def test_review_pass_marks_spec_implemented_with_actual_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "specs" / "SPEC-0001-payment-retry.md"
            path.parent.mkdir()
            path.write_text(confirmed_spec(), encoding="utf-8")

            blocked = SPEC_CONTRACT.mark_spec_implemented(
                path,
                {"AC-001": "PASS: tests.test_retry_limit"},
                spec_review_passed=False,
                authorized=True,
            )
            passed = SPEC_CONTRACT.mark_spec_implemented(
                path,
                {"AC-001": "PASS: tests.test_retry_limit"},
                spec_review_passed=True,
                authorized=True,
            )

            self.assertEqual("BLOCKED", blocked["verdict"])
            self.assertEqual("PASS", passed["verdict"])
            self.assertEqual("implemented", passed["canonical_spec"]["status"])
            self.assertEqual("specs/SPEC-0001-payment-retry.md", passed["canonical_spec"]["path"])
            self.assertIn("status: implemented", path.read_text(encoding="utf-8"))
            self.assertIn(
                f"| 2 | {date.today().isoformat()} | Recorded implementation PASS evidence. |",
                path.read_text(encoding="utf-8"),
            )


class SpecContextResolutionTests(unittest.TestCase):
    def write_spec(
        self,
        root: Path,
        spec_id: str,
        slug: str,
        *,
        status: str = "confirmed",
    ) -> Path:
        path = root / "specs" / f"{spec_id}-{slug}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(
            confirmed_spec(spec_id=spec_id, slug=slug, status=status),
            encoding="utf-8",
        )
        return path

    def test_unique_confirmed_spec_is_selected_but_implemented_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = self.write_spec(root, "SPEC-0001", "payment-retry")
            self.write_spec(
                root,
                "SPEC-0002",
                "old-change",
                status="implemented",
            )

            result = SPEC_CONTRACT.resolve_spec_context(root, "")

            self.assertEqual("confirmed", result["state"])
            self.assertEqual(selected.relative_to(root).as_posix(), result["selected_path"])

    def test_explicit_path_wins_and_multiple_fallback_candidates_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self.write_spec(root, "SPEC-0001", "payment-retry")
            second = self.write_spec(root, "SPEC-0002", "invoice-export")

            ambiguous = SPEC_CONTRACT.resolve_spec_context(root, "")
            explicit = SPEC_CONTRACT.resolve_spec_context(
                root,
                f"請實作 {first.relative_to(root).as_posix()}",
            )

            self.assertEqual("ambiguous", ambiguous["state"])
            self.assertCountEqual(
                [
                    first.relative_to(root).as_posix(),
                    second.relative_to(root).as_posix(),
                ],
                ambiguous["candidates"],
            )
            self.assertEqual(first.relative_to(root).as_posix(), explicit["selected_path"])

    def test_user_explicit_path_precedes_tracker_path_and_tracker_precedes_branch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            explicit_path = self.write_spec(root, "SPEC-0001", "payment-retry")
            tracker_path = self.write_spec(root, "SPEC-0002", "invoice-export")
            branch_path = self.write_spec(root, "SPEC-0003", "audit-log")

            explicit = SPEC_CONTRACT.resolve_spec_context(
                root,
                f"Use {explicit_path.relative_to(root).as_posix()}",
                tracker_path=tracker_path.relative_to(root).as_posix(),
                branch="feature/audit-log",
            )
            tracker = SPEC_CONTRACT.resolve_spec_context(
                root,
                "",
                tracker_path=tracker_path.relative_to(root).as_posix(),
                branch="feature/audit-log",
            )

            self.assertEqual(explicit_path.relative_to(root).as_posix(), explicit["selected_path"])
            self.assertEqual(tracker_path.relative_to(root).as_posix(), tracker["selected_path"])

    def test_branch_match_precedes_unique_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_spec(root, "SPEC-0001", "payment-retry")
            selected = self.write_spec(root, "SPEC-0002", "invoice-export")

            result = SPEC_CONTRACT.resolve_spec_context(
                root,
                "",
                branch="feature/invoice-export",
            )

            self.assertEqual(selected.relative_to(root).as_posix(), result["selected_path"])

    def test_verify_confirmed_spec_passes_without_new_delta_and_blocks_with_one(self) -> None:
        passed = SPEC_CONTRACT.verify_spec(confirmed_spec())
        blocked = SPEC_CONTRACT.verify_spec(
            confirmed_spec(),
            requested_changes=["Add a fourth retry mode."],
        )

        self.assertEqual("PASS", passed["verdict"])
        self.assertEqual("BLOCKED", blocked["verdict"])
        self.assertEqual(["Add a fourth retry mode."], blocked["new_decisions"])

    def test_path_aware_verify_accepts_existing_cross_spec_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_spec(root, "SPEC-0001", "base-policy")
            refining = self.write_spec(root, "SPEC-0002", "payment-retry")
            refining.write_text(
                confirmed_spec(spec_id="SPEC-0002").replace(
                    "| REQ-001 | depends_on | DEC-001 |",
                    "| REQ-001 | refines | SPEC-0001 |",
                ),
                encoding="utf-8",
            )

            result = SPEC_CONTRACT.verify_spec_path(refining)
            blocked = SPEC_CONTRACT.verify_spec_path(
                refining,
                requested_changes=["Choose a new retry owner."],
            )

            self.assertEqual("PASS", result["verdict"])
            self.assertEqual(
                "specs/SPEC-0002-payment-retry.md",
                result["canonical_spec"]["path"],
            )
            self.assertEqual("BLOCKED", blocked["verdict"])
            self.assertEqual(
                "specs/SPEC-0002-payment-retry.md",
                blocked["canonical_spec"]["path"],
            )

    def test_filename_metadata_mismatch_and_duplicate_spec_ids_are_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mismatched = root / "specs" / "SPEC-0001-wrong-name.md"
            mismatched.parent.mkdir()
            mismatched.write_text(
                confirmed_spec(spec_id="SPEC-0002", slug="actual-name"),
                encoding="utf-8",
            )
            duplicate = root / "specs" / "SPEC-0003-duplicate.md"
            duplicate.write_text(
                confirmed_spec(spec_id="SPEC-0002", slug="duplicate"),
                encoding="utf-8",
            )

            result = SPEC_CONTRACT.resolve_spec_context(root, "")

            self.assertEqual("invalid", result["state"])
            self.assertCountEqual(
                [
                    mismatched.relative_to(root).as_posix(),
                    duplicate.relative_to(root).as_posix(),
                ],
                result["candidates"],
            )

    def test_scope_creep_blocks_traceability(self) -> None:
        result = SPEC_CONTRACT.verify_spec(
            confirmed_spec(),
            scope_creep=["Added an unrequested provider switch."],
        )

        self.assertEqual("BLOCKED", result["verdict"])
        self.assertEqual(
            ["Added an unrequested provider switch."],
            result["traceability"]["scope_creep"],
        )


if __name__ == "__main__":
    unittest.main()
