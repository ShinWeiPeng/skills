from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
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

    def test_materialization_requires_authorization_and_uses_next_number(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            specs = root / "specs"
            specs.mkdir()
            (specs / "SPEC-0007-existing.md").write_text(
                confirmed_spec(spec_id="SPEC-0007", slug="existing"),
                encoding="utf-8",
            )

            blocked = SPEC_CONTRACT.materialize_spec(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000"),
                authorized=False,
            )
            self.assertEqual("BLOCKED", blocked["verdict"])
            self.assertFalse((specs / "SPEC-0008-payment-retry.md").exists())

            created = SPEC_CONTRACT.materialize_spec(
                root,
                "payment-retry",
                confirmed_spec(spec_id="SPEC-0000"),
                authorized=True,
            )

            self.assertEqual("SPEC-0008", created["canonical_spec"]["spec_id"])
            self.assertTrue((root / created["canonical_spec"]["path"]).is_file())

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
                    authorized=True,
                )
                self.assertEqual("BLOCKED", result["verdict"])
            self.assertFalse((root / "specs").exists())

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
                "| 2 | 2026-08-02 | Recorded implementation PASS evidence. |",
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
