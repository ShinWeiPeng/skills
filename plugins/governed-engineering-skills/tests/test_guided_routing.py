from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = (
    PLUGIN_ROOT / "skills" / "engineering-risk-routing" / "scripts"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROJECT_STATE = load_module(
    "project_state",
    SCRIPTS_ROOT / "project_state.py",
)
REPOSITORY_EVIDENCE = load_module(
    "repository_evidence",
    SCRIPTS_ROOT / "repository_evidence.py",
)
WORKFLOW_SELECTION = load_module(
    "workflow_selection",
    SCRIPTS_ROOT / "workflow_selection.py",
)

CONFIRMED_SPEC_TEXT = """---
spec_version: 1
spec_id: SPEC-0001
revision: 1
status: confirmed
change_set: payment-retry
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
| DEC-001 | Use bounded retry. |

## Acceptance Criteria

| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | A fourth attempt is rejected. | `test_retry_limit` | pending |

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
- Spec review: pending

## Revision History

| Revision | Date | Change |
|---|---|---|
| 1 | 2026-08-03 | Initial confirmed contract. |
"""


class ProjectStateAssessmentTests(unittest.TestCase):
    def test_empty_repository_is_absent_on_both_axes(self) -> None:
        result = PROJECT_STATE.assess_project_state([])

        self.assertEqual("absent", result["implementation"])
        self.assertEqual("absent", result["stateful_context"])
        self.assertEqual([], result["evidence"])

    def test_source_file_marks_implementation_present(self) -> None:
        result = PROJECT_STATE.assess_project_state(
            [{"path": "src/app.py", "tracking": "tracked"}]
        )

        self.assertEqual("present", result["implementation"])
        self.assertEqual("absent", result["stateful_context"])
        self.assertEqual(
            "implementation",
            result["evidence"][0]["classification"],
        )

    def test_context_document_marks_stateful_context_present(self) -> None:
        result = PROJECT_STATE.assess_project_state(
            [{"path": "CONTEXT.md", "tracking": "tracked", "size_bytes": 20}]
        )

        self.assertEqual("absent", result["implementation"])
        self.assertEqual("present", result["stateful_context"])
        self.assertEqual(
            "stateful-context",
            result["evidence"][0]["classification"],
        )

    def test_empty_formal_context_is_indeterminate_not_present(self) -> None:
        result = PROJECT_STATE.assess_project_state(
            [{"path": "CONTEXT.md", "tracking": "tracked", "size_bytes": 0}]
        )

        self.assertEqual("absent", result["implementation"])
        self.assertEqual("indeterminate", result["stateful_context"])
        self.assertEqual("ambiguous", result["evidence"][0]["classification"])

    def test_readme_only_is_indeterminate_on_both_axes(self) -> None:
        result = PROJECT_STATE.assess_project_state(
            [{"path": "README.md", "tracking": "tracked"}]
        )

        self.assertEqual("indeterminate", result["implementation"])
        self.assertEqual("indeterminate", result["stateful_context"])
        self.assertEqual("ambiguous", result["evidence"][0]["classification"])

    def test_empty_source_placeholder_is_indeterminate_implementation(self) -> None:
        result = PROJECT_STATE.assess_project_state(
            [
                {
                    "path": "src/app.py",
                    "tracking": "tracked",
                    "size_bytes": 0,
                }
            ]
        )

        self.assertEqual("indeterminate", result["implementation"])
        self.assertEqual("absent", result["stateful_context"])
        self.assertEqual("ambiguous", result["evidence"][0]["classification"])

    def test_source_and_docs_are_present_on_both_axes(self) -> None:
        result = PROJECT_STATE.assess_project_state(
            [
                {
                    "path": "src/app.py",
                    "tracking": "tracked",
                    "size_bytes": 10,
                },
                {
                    "path": "CONTEXT.md",
                    "tracking": "tracked",
                    "size_bytes": 20,
                },
            ]
        )

        self.assertEqual("present", result["implementation"])
        self.assertEqual("present", result["stateful_context"])

    def test_weak_artifacts_do_not_pollute_strong_source_evidence(self) -> None:
        result = PROJECT_STATE.assess_project_state(
            [
                {"path": "src/app.py", "tracking": "tracked"},
                {"path": "README.md", "tracking": "tracked"},
            ]
        )

        self.assertEqual("present", result["implementation"])
        self.assertEqual("absent", result["stateful_context"])

    def test_weak_artifacts_do_not_pollute_formal_context_evidence(self) -> None:
        result = PROJECT_STATE.assess_project_state(
            [
                {"path": "specs/app.md", "tracking": "tracked"},
                {"path": "README.md", "tracking": "tracked"},
            ]
        )

        self.assertEqual("absent", result["implementation"])
        self.assertEqual("present", result["stateful_context"])

    def test_excluded_evidence_does_not_change_either_axis(self) -> None:
        result = PROJECT_STATE.assess_project_state(
            [
                {
                    "path": "generated/app.py",
                    "tracking": "tracked",
                    "size_bytes": 0,
                    "exclusion_reason": (
                        "excluded repository path component: generated"
                    ),
                }
            ]
        )

        self.assertEqual("absent", result["implementation"])
        self.assertEqual("absent", result["stateful_context"])
        self.assertEqual("excluded", result["evidence"][0]["classification"])


class RepositoryEvidenceAdapterTests(unittest.TestCase):
    def test_collects_tracked_and_untracked_but_not_ignored_artifacts(self) -> None:
        build_root = PLUGIN_ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build_root) as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            (root / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
            (root / "tracked.py").write_text("tracked = True\n", encoding="utf-8")
            (root / "untracked.py").write_text("untracked = True\n", encoding="utf-8")
            (root / "ignored.tmp").write_text("ignored\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", ".gitignore", "tracked.py"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            result = (
                REPOSITORY_EVIDENCE.GitFilesystemRepositoryEvidenceAdapter()
                .collect(root)
            )

        self.assertEqual(
            [
                (".gitignore", "tracked", True),
                ("tracked.py", "tracked", False),
                ("untracked.py", "untracked", False),
            ],
            [
                (
                    row["path"],
                    row["tracking"],
                    row["exclusion_reason"] is not None,
                )
                for row in result
            ],
        )
        included = [
            row for row in result if row["exclusion_reason"] is None
        ]
        self.assertEqual(
            [
                ("tracked.py", "tracked"),
                ("untracked.py", "untracked"),
            ],
            [(row["path"], row["tracking"]) for row in included],
        )
        self.assertTrue(all(row["size_bytes"] > 0 for row in included))

    def test_ignored_artifacts_only_are_equivalent_to_empty_repository(self) -> None:
        build_root = PLUGIN_ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build_root) as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            (root / ".gitignore").write_text("*.py\n", encoding="utf-8")
            (root / "generated.py").write_text("value = 1\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", ".gitignore"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            evidence = (
                REPOSITORY_EVIDENCE.GitFilesystemRepositoryEvidenceAdapter()
                .collect(root)
            )

        self.assertEqual(1, len(evidence))
        self.assertEqual(".gitignore", evidence[0]["path"])
        self.assertIsNotNone(evidence[0]["exclusion_reason"])
        self.assertEqual(
            ("absent", "absent"),
            (
                PROJECT_STATE.assess_project_state(evidence)["implementation"],
                PROJECT_STATE.assess_project_state(evidence)["stateful_context"],
            ),
        )

    def test_symbolic_link_is_excluded_without_reading_target_metadata(
        self,
    ) -> None:
        with (
            mock.patch.object(Path, "is_symlink", return_value=True),
            mock.patch.object(
                Path,
                "stat",
                side_effect=AssertionError("symlink target metadata was read"),
            ),
        ):
            row = (
                REPOSITORY_EVIDENCE.GitFilesystemRepositoryEvidenceAdapter
                ._artifact_row(Path.cwd(), "outside.py", "tracked")
            )

        self.assertEqual(0, row["size_bytes"])
        self.assertIn("symbolic links", row["exclusion_reason"])


class IntentAssessmentTests(unittest.TestCase):
    def test_thesis_trace_greenfield_wording_is_modifying(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "我想做一個自己用的投資工具"
        )

        self.assertEqual("implementation-design", result["intent"])
        self.assertTrue(result["requires_modification"])
        self.assertIn("做", result["matched_terms"])

    def test_new_feature_is_modifying_implementation_design(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "在月報頁面新增匯出 CSV 按鈕"
        )

        self.assertEqual("implementation-design", result["intent"])
        self.assertTrue(result["requires_modification"])
        self.assertIn("新增", result["matched_terms"])

    def test_review_and_fix_is_modifying_not_read_only_review(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "Review this change and fix any bugs"
        )

        self.assertEqual("review", result["intent"])
        self.assertTrue(result["requires_modification"])

    def test_english_terms_do_not_match_inside_unrelated_words(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "Explain how the address formatter works"
        )

        self.assertEqual("indeterminate", result["intent"])
        self.assertFalse(result["requires_modification"])

    def test_review_with_fix_remains_a_modifying_change_set(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "review this payment flow and fix the retry bug"
        )

        self.assertEqual("review", result["intent"])
        self.assertTrue(result["requires_modification"])

    def test_reviewing_a_change_remains_read_only(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent("review this change")

        self.assertEqual("review", result["intent"])
        self.assertFalse(result["requires_modification"])

    def test_reviewing_a_fix_remains_read_only(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent("review this fix")

        self.assertEqual("review", result["intent"])
        self.assertFalse(result["requires_modification"])

    def test_explaining_how_update_works_remains_read_only(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "how does update work"
        )

        self.assertEqual("code-understanding", result["intent"])
        self.assertFalse(result["requires_modification"])

    def test_semicolon_separated_review_and_fix_is_mixed(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "review this; fix the bug"
        )

        self.assertEqual("review", result["intent"])
        self.assertTrue(result["requires_modification"])

    def test_chinese_comma_separated_review_and_fix_is_mixed(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "檢視程式碼，修正錯誤"
        )

        self.assertEqual("review", result["intent"])
        self.assertTrue(result["requires_modification"])

    def test_chinese_code_understanding_with_do_word_remains_read_only(
        self,
    ) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "解釋這段程式碼在做什麼"
        )

        self.assertEqual("code-understanding", result["intent"])
        self.assertFalse(result["requires_modification"])

    def test_chinese_code_understanding_then_modify_is_mixed(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "解釋這段流程，然後修改錯誤處理"
        )

        self.assertEqual("code-understanding", result["intent"])
        self.assertTrue(result["requires_modification"])

    def test_explicit_conflict_resolution_is_modifying(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "resolve the current conflict",
            explicit_skill="resolving-merge-conflicts",
        )

        self.assertEqual("explicit-skill", result["intent"])
        self.assertTrue(result["requires_modification"])

    def test_explicit_code_review_cannot_hide_direct_fix_intent(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "fix this login bug",
            explicit_skill="code-review",
        )

        self.assertEqual("explicit-skill", result["intent"])
        self.assertTrue(result["requires_modification"])

    def test_explicit_code_review_of_a_change_remains_read_only(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "review this change",
            explicit_skill="code-review",
        )

        self.assertEqual("explicit-skill", result["intent"])
        self.assertFalse(result["requires_modification"])

    def test_explicit_code_explanation_cannot_hide_update_intent(self) -> None:
        result = WORKFLOW_SELECTION.classify_intent(
            "update the payment retry logic",
            explicit_skill="explain-code-flow",
        )

        self.assertEqual("explicit-skill", result["intent"])
        self.assertTrue(result["requires_modification"])


class GuidedWorkflowSelectionTests(unittest.TestCase):
    RISK = {
        "required_gates": ["tdd", "code-review"],
        "next_skill": "tdd",
        "return_to_flow": "code-review",
    }
    SKILLS = {
        "code-review",
        "diagnosing-bugs",
        "explain-code-flow",
        "grill-me",
        "grill-with-docs",
        "grilling",
        "spec-governance",
        "tdd",
        "to-spec",
        "wayfinder",
    }

    def test_greenfield_modification_starts_with_grill_me(self) -> None:
        intent = WORKFLOW_SELECTION.classify_intent(
            "建立一個自己使用的投資工具"
        )
        project_state = PROJECT_STATE.assess_project_state([])

        result = WORKFLOW_SELECTION.select_workflow(
            intent,
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
        )

        self.assertEqual("PASS", result["status"])
        self.assertEqual("grill-me", result["selected_skill"])
        self.assertEqual("to-spec", result["resume_target"])

    def test_doc_only_modification_starts_with_grill_with_docs(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("依照規格建立付款服務"),
            PROJECT_STATE.assess_project_state(
                [{"path": "specs/payment.md", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
        )

        self.assertEqual("PASS", result["status"])
        self.assertEqual("grill-with-docs", result["selected_skill"])
        self.assertEqual("to-spec", result["resume_target"])

    def test_doc_only_confirmed_spec_without_resume_still_grills_with_docs(
        self,
    ) -> None:
        spec_context = {
            "state": "confirmed",
            "selected_path": "specs/SPEC-0001-payment-retry.md",
            "candidates": ["specs/SPEC-0001-payment-retry.md"],
            "reason": "unique confirmed specification",
        }

        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("新增不同的付款部署規格"),
            PROJECT_STATE.assess_project_state(
                [
                    {
                        "path": spec_context["selected_path"],
                        "tracking": "tracked",
                        "size_bytes": 100,
                    }
                ]
            ),
            self.RISK,
            available_skills=self.SKILLS,
            spec_context=spec_context,
        )

        self.assertEqual("PASS", result["status"])
        self.assertEqual("grill-with-docs", result["selected_skill"])
        self.assertEqual("to-spec", result["resume_target"])

    def test_existing_implementation_modification_starts_with_grilling(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("修改付款重試規則"),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/payment.py", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
        )

        self.assertEqual("grilling", result["selected_skill"])
        self.assertEqual("tdd", result["resume_target"])

    def test_bug_diagnosis_is_read_only_before_fix_grilling(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("修正登入偶發失敗的 bug"),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/login.py", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
        )

        self.assertEqual("diagnosing-bugs", result["selected_skill"])
        self.assertEqual("grilling", result["resume_target"])

    def test_review_and_code_understanding_keep_read_only_routes(self) -> None:
        project_state = PROJECT_STATE.assess_project_state(
            [{"path": "src/app.py", "tracking": "tracked"}]
        )

        review = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("review 這次變更"),
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
        )
        explanation = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("解釋資料如何流到 PostgreSQL"),
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
        )

        self.assertEqual("code-review", review["selected_skill"])
        self.assertEqual("explain-code-flow", explanation["selected_skill"])

    def test_mixed_review_and_fix_grills_before_review(self) -> None:
        intent = WORKFLOW_SELECTION.classify_intent(
            "review this payment flow and fix the retry bug"
        )
        project_state = PROJECT_STATE.assess_project_state(
            [{"path": "src/payment.py", "tracking": "tracked"}]
        )

        before_grilling = WORKFLOW_SELECTION.select_workflow(
            intent,
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
        )
        after_grilling = WORKFLOW_SELECTION.select_workflow(
            intent,
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
            completed_stages={"grilling"},
        )
        after_spec_verification = WORKFLOW_SELECTION.select_workflow(
            intent,
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
            completed_stages={"grilling", "spec-verified"},
        )

        self.assertEqual("grilling", before_grilling["selected_skill"])
        self.assertEqual("spec-governance", after_grilling["selected_skill"])
        self.assertEqual("code-review", after_grilling["resume_target"])
        self.assertEqual(
            "code-review",
            after_spec_verification["selected_skill"],
        )
        self.assertEqual("tdd", after_spec_verification["resume_target"])

    def test_explicit_tdd_cannot_skip_change_set_grilling(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent(
                "新增匯出功能",
                explicit_skill="tdd",
            ),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/export.py", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
        )

        self.assertEqual("grilling", result["selected_skill"])
        self.assertEqual("tdd", result["resume_target"])

    def test_indeterminate_project_state_blocks_guessing_and_asks_one_question(
        self,
    ) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("新增匯出功能"),
            PROJECT_STATE.assess_project_state(
                [{"path": "README.md", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
        )

        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("grilling", result["selected_skill"])
        self.assertEqual("project-state-decision", result["resume_target"])

    def test_missing_grill_me_degrades_to_grilling_primitive(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("建立新的投資工具"),
            PROJECT_STATE.assess_project_state([]),
            self.RISK,
            available_skills=self.SKILLS - {"grill-me"},
        )

        self.assertEqual("DEGRADED", result["status"])
        self.assertEqual("grilling", result["selected_skill"])
        self.assertEqual("grill-me", result["fallback"])

    def test_wayfinder_requires_all_three_complexity_signals(self) -> None:
        intent = WORKFLOW_SELECTION.classify_intent("建立新的投資工具")
        project_state = PROJECT_STATE.assess_project_state([])

        selected = WORKFLOW_SELECTION.select_workflow(
            intent,
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
            completed_stages={"grilling", "spec-verified"},
            wayfinder_evidence={
                "decision_ticket_candidates": 2,
                "blocking_dependencies": 1,
                "fog_areas": 1,
            },
        )
        not_selected = WORKFLOW_SELECTION.select_workflow(
            intent,
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
            completed_stages={"grilling", "spec-verified"},
            wayfinder_evidence={
                "decision_ticket_candidates": 2,
                "blocking_dependencies": 1,
                "fog_areas": 0,
            },
        )

        self.assertEqual("wayfinder", selected["selected_skill"])
        self.assertEqual("to-spec", not_selected["selected_skill"])

        for missing in (
            "decision_ticket_candidates",
            "blocking_dependencies",
            "fog_areas",
        ):
            evidence = {
                "decision_ticket_candidates": 2,
                "blocking_dependencies": 1,
                "fog_areas": 1,
            }
            evidence[missing] = 0
            result = WORKFLOW_SELECTION.select_workflow(
                intent,
                project_state,
                self.RISK,
                available_skills=self.SKILLS,
                completed_stages={"grilling", "spec-verified"},
                wayfinder_evidence=evidence,
            )
            self.assertNotEqual("wayfinder", result["selected_skill"])

    def test_greenfield_wrapper_completion_does_not_repeat_grilling(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("建立新的投資工具"),
            PROJECT_STATE.assess_project_state([]),
            self.RISK,
            available_skills=self.SKILLS,
            completed_stages={"grill-me"},
        )

        self.assertEqual("spec-governance", result["selected_skill"])
        self.assertNotEqual("grill-me", result["selected_skill"])

    def test_confirmed_spec_verifies_then_resumes_tdd_without_grilling(self) -> None:
        spec_context = {
            "state": "confirmed",
            "selected_path": "specs/SPEC-0001-payment-retry.md",
            "candidates": ["specs/SPEC-0001-payment-retry.md"],
            "reason": "unique confirmed specification",
        }
        project_state = PROJECT_STATE.assess_project_state(
            [
                {"path": "src/payment.py", "tracking": "tracked", "size_bytes": 10},
                {
                    "path": spec_context["selected_path"],
                    "tracking": "tracked",
                    "size_bytes": 100,
                },
            ]
        )

        verify = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("修改付款重試規則"),
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
            spec_context=spec_context,
            resume_confirmed_spec=True,
        )
        resume = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("修改付款重試規則"),
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
            spec_context=spec_context,
            completed_stages={"spec-verified"},
            resume_confirmed_spec=True,
        )

        self.assertEqual("spec-governance", verify["selected_skill"])
        self.assertEqual("tdd", verify["resume_target"])
        self.assertEqual("tdd", resume["selected_skill"])
        self.assertNotIn(resume["selected_skill"], {"grilling", "grill-with-docs"})

    def test_resume_requires_exactly_one_valid_confirmed_spec(self) -> None:
        contexts = {
            "none": None,
            "ambiguous": {
                "state": "ambiguous",
                "selected_path": None,
                "candidates": ["specs/SPEC-0001-a.md", "specs/SPEC-0002-b.md"],
                "reason": "multiple confirmed specifications",
            },
            "invalid": {
                "state": "invalid",
                "selected_path": None,
                "candidates": ["specs/SPEC-0001-invalid.md"],
                "reason": "repository contains invalid specifications",
            },
            "implemented": {
                "state": "implemented",
                "selected_path": "specs/SPEC-0001-payment-retry.md",
                "candidates": ["specs/SPEC-0001-payment-retry.md"],
                "reason": "explicit canonical path",
            },
        }

        for state, spec_context in contexts.items():
            with self.subTest(state=state):
                result = WORKFLOW_SELECTION.select_workflow(
                    WORKFLOW_SELECTION.classify_intent(
                        "修改付款規格並繼續既有 change set"
                    ),
                    PROJECT_STATE.assess_project_state(
                        [
                            {
                                "path": "CONTEXT.md",
                                "tracking": "tracked",
                                "size_bytes": 100,
                            }
                        ]
                    ),
                    self.RISK,
                    available_skills=self.SKILLS,
                    spec_context=spec_context,
                    resume_confirmed_spec=True,
                )

                self.assertEqual("BLOCKED", result["status"])
                self.assertEqual("spec-governance", result["selected_skill"])
                self.assertEqual("spec-context-decision", result["resume_target"])

    def test_ambiguous_spec_context_blocks_without_guessing(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("修改付款重試規則"),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/payment.py", "tracking": "tracked", "size_bytes": 10}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
            spec_context={
                "state": "ambiguous",
                "selected_path": None,
                "candidates": [
                    "specs/SPEC-0001-a.md",
                    "specs/SPEC-0002-b.md",
                ],
                "reason": "multiple confirmed specifications",
            },
        )

        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("spec-governance", result["selected_skill"])
        self.assertEqual("spec-context-decision", result["resume_target"])

    def test_missing_wayfinder_capability_is_blocked(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("建立新的投資工具"),
            PROJECT_STATE.assess_project_state([]),
            self.RISK,
            available_skills=self.SKILLS - {"wayfinder"},
            completed_stages={"grilling", "spec-verified"},
            wayfinder_evidence={
                "decision_ticket_candidates": 2,
                "blocking_dependencies": 1,
                "fog_areas": 1,
            },
        )

        self.assertEqual("BLOCKED", result["status"])
        self.assertIsNone(result["selected_skill"])
        self.assertEqual("wayfinder", result["fallback"])

    def test_missing_tracker_capability_is_blocked(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("建立新的投資工具"),
            PROJECT_STATE.assess_project_state([]),
            self.RISK,
            available_skills=self.SKILLS,
            completed_stages={"grilling", "spec-verified"},
            wayfinder_evidence={
                "decision_ticket_candidates": 2,
                "blocking_dependencies": 1,
                "fog_areas": 1,
            },
            tracker_available=False,
        )

        self.assertEqual("BLOCKED", result["status"])
        self.assertIsNone(result["selected_skill"])
        self.assertEqual("wayfinder", result["fallback"])

    def test_new_execution_decision_returns_to_grilling(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("修改付款規則"),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/payment.py", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
            completed_stages={"grilling", "spec-verified"},
            has_unresolved_decision=True,
        )

        self.assertEqual("grilling", result["selected_skill"])
        self.assertEqual("spec-governance", result["resume_target"])
        self.assertEqual(
            "A repository-modifying design or specification decision must be "
            "resolved before the active workflow continues.",
            result["reason"],
        )

    def test_read_only_odr_flow_hands_off_before_design_choice(self) -> None:
        project_state = PROJECT_STATE.assess_project_state(
            [{"path": "src/sample_pairer.py", "tracking": "tracked"}]
        )
        explanation = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent(
                "解釋 ODR 資料流與 sample_pairer 怎麼運作"
            ),
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
        )
        before_design_question = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent(
                "比較 Boot 固定與滑動視窗的設計選項"
            ),
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
            has_unresolved_decision=True,
        )
        numeric_answer = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("1"),
            project_state,
            self.RISK,
            available_skills=self.SKILLS,
            has_unresolved_decision=True,
        )

        self.assertEqual("explain-code-flow", explanation["selected_skill"])
        self.assertEqual("grilling", before_design_question["selected_skill"])
        self.assertEqual("grilling", numeric_answer["selected_skill"])
        self.assertEqual(
            "spec-governance", before_design_question["resume_target"]
        )
        self.assertEqual("spec-governance", numeric_answer["resume_target"])

    def test_decision_complete_clears_signal_and_restores_normal_routing(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent(
                "解釋 GetFIFOData 的 Sequence 怎麼流到 sample_pairer"
            ),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/sample_pairer.py", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
            has_unresolved_decision=False,
        )

        self.assertEqual("explain-code-flow", result["selected_skill"])
        self.assertNotEqual("spec-governance", result["resume_target"])

    def test_factual_odr_follow_up_remains_code_understanding(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent(
                "解釋 GetFIFOData 的 Sequence 怎麼流到 sample_pairer"
            ),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/sample_pairer.py", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
        )

        self.assertEqual("explain-code-flow", result["selected_skill"])

    def test_modification_grills_before_reporting_blocked_risk_gate(self) -> None:
        risk = {
            **self.RISK,
            "status": "BLOCKED",
            "blockers": ["missing capability: govern-modular-event-architecture"],
        }
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("新增付款服務"),
            PROJECT_STATE.assess_project_state([]),
            risk,
            available_skills=self.SKILLS,
        )

        self.assertEqual("PASS", result["status"])
        self.assertEqual("grill-me", result["selected_skill"])

        after_grilling = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("新增付款服務"),
            PROJECT_STATE.assess_project_state([]),
            risk,
            available_skills=self.SKILLS,
            completed_stages={"grilling"},
        )
        self.assertEqual("PASS", after_grilling["status"])
        self.assertEqual("spec-governance", after_grilling["selected_skill"])

        after_verification = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("新增付款服務"),
            PROJECT_STATE.assess_project_state([]),
            risk,
            available_skills=self.SKILLS,
            completed_stages={"grilling", "spec-verified"},
        )
        self.assertEqual("BLOCKED", after_verification["status"])
        self.assertIsNone(after_verification["selected_skill"])

    def test_blocked_risk_gate_prevents_read_only_handoff(self) -> None:
        risk = {
            **self.RISK,
            "status": "BLOCKED",
            "blockers": ["missing capability: govern-modular-event-architecture"],
        }
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent("review the architecture"),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/app.py", "tracking": "tracked"}]
            ),
            risk,
            available_skills=self.SKILLS,
        )

        self.assertEqual("BLOCKED", result["status"])
        self.assertIsNone(result["selected_skill"])

    def test_explicit_read_only_skill_keeps_its_entry(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent(
                "檢視目前的變更",
                explicit_skill="code-review",
            ),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/app.py", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS,
        )

        self.assertEqual("PASS", result["status"])
        self.assertEqual("code-review", result["selected_skill"])

    def test_missing_explicit_read_only_skill_is_blocked(self) -> None:
        result = WORKFLOW_SELECTION.select_workflow(
            WORKFLOW_SELECTION.classify_intent(
                "檢視目前的變更",
                explicit_skill="code-review",
            ),
            PROJECT_STATE.assess_project_state(
                [{"path": "src/app.py", "tracking": "tracked"}]
            ),
            self.RISK,
            available_skills=self.SKILLS - {"code-review"},
        )

        self.assertEqual("BLOCKED", result["status"])
        self.assertIsNone(result["selected_skill"])


class GuidedRoutingContractTests(unittest.TestCase):
    def test_automatic_route_skills_allow_implicit_invocation(self) -> None:
        for skill in (
            "ask-matt",
            "grill-me",
            "grill-with-docs",
            "wayfinder",
        ):
            metadata = (
                PLUGIN_ROOT / "skills" / skill / "agents" / "openai.yaml"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "allow_implicit_invocation: true",
                metadata,
                msg=skill,
            )

    def test_resume_documentation_requires_explicit_evidence(self) -> None:
        ask_matt = (PLUGIN_ROOT / "skills" / "ask-matt" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        risk_routing = (
            PLUGIN_ROOT / "skills" / "engineering-risk-routing" / "SKILL.md"
        ).read_text(encoding="utf-8")
        grill_with_docs = (
            PLUGIN_ROOT / "skills" / "grill-with-docs" / "SKILL.md"
        ).read_text(encoding="utf-8")
        algorithm = (
            PLUGIN_ROOT
            / "architecture"
            / "algorithms"
            / "ALG-0003-ordered-workflow-selection.md"
        ).read_text(encoding="utf-8")
        canonical_spec_adr = (
            PLUGIN_ROOT
            / "architecture"
            / "decisions"
            / "ADR-0011-canonical-change-set-specification.md"
        ).read_text(encoding="utf-8")
        manifest = (PLUGIN_ROOT / "architecture" / "manifest.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("resume_confirmed_spec=true", ask_matt)
        self.assertIn("--resume-confirmed-spec", risk_routing)
        self.assertIn("explicit resume evidence", grill_with_docs)
        self.assertIn("resume_confirmed_spec", algorithm)
        self.assertIn("explicit resume evidence", canonical_spec_adr)
        self.assertIn("explicit resume evidence", manifest)
        self.assertNotIn(
            "verified rather than re-interviewed unless",
            manifest,
        )

    def test_schema_declares_all_public_contracts(self) -> None:
        schema = json.loads(
            (
                PLUGIN_ROOT
                / "skills"
                / "engineering-risk-routing"
                / "references"
                / "guided-routing-contract.schema.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(
            {
                "RepositoryArtifact",
                "RepositoryEvidence",
                "ProjectStateAssessment",
                "IntentAssessment",
                "SpecContextAssessment",
                "WorkflowSelectionOptions",
                "GuidedRouteDecision",
            },
            set(schema["$defs"]),
        )
        options = schema["$defs"]["WorkflowSelectionOptions"]
        self.assertEqual([], options["required"])
        self.assertFalse(options["properties"]["has_unresolved_decision"]["default"])
        self.assertIn(
            "--unresolved-decision",
            options["properties"]["has_unresolved_decision"]["description"],
        )
        unresolved_description = options["properties"][
            "has_unresolved_decision"
        ]["description"]
        self.assertIn("true if and only if", unresolved_description)
        self.assertIn("short or numeric answers", unresolved_description)
        self.assertIn("no open decisions remain", unresolved_description)
        self.assertIn("resume_target spec-governance", unresolved_description)
        self.assertFalse(options["properties"]["resume_confirmed_spec"]["default"])
        decision = schema["$defs"]["GuidedRouteDecision"]
        self.assertIn("DEGRADED", decision["properties"]["status"]["enum"])
        self.assertIn("project_state", decision["required"])
        artifact = schema["$defs"]["RepositoryArtifact"]
        self.assertIn("exclusion_reason", artifact["required"])
        intent_rules = json.loads(
            (
                PLUGIN_ROOT
                / "skills"
                / "engineering-risk-routing"
                / "references"
                / "intent-rules.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("mixed_action_connectors", intent_rules)

    def test_cli_routes_an_empty_repository_to_grill_me(self) -> None:
        build_root = PLUGIN_ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build_root) as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_ROOT / "guided_workflow_router.py"),
                    "--prompt",
                    "建立一個自己使用的投資工具",
                    "--project-root",
                    str(root),
                    "--json",
                ],
                cwd=PLUGIN_ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        result = json.loads(completed.stdout)
        self.assertEqual("grill-me", result["selected_skill"])
        self.assertEqual("absent", result["project_state"]["implementation"])
        self.assertEqual("absent", result["project_state"]["stateful_context"])

    def test_cli_unresolved_decision_routes_to_grilling_then_spec_governance(
        self,
    ) -> None:
        build_root = PLUGIN_ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build_root) as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_ROOT / "guided_workflow_router.py"),
                    "--prompt",
                    "1",
                    "--project-root",
                    str(root),
                    "--unresolved-decision",
                    "--json",
                ],
                cwd=PLUGIN_ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        result = json.loads(completed.stdout)
        self.assertEqual("grilling", result["selected_skill"])
        self.assertEqual("spec-governance", result["resume_target"])
        self.assertIn("design or specification decision", result["reason"])

    def test_cli_requires_explicit_flag_to_resume_a_confirmed_spec(self) -> None:
        build_root = PLUGIN_ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build_root) as directory:
            root = Path(directory)
            specs_dir = root / "specs"
            specs_dir.mkdir()
            (specs_dir / "SPEC-0001-payment-retry.md").write_text(
                CONFIRMED_SPEC_TEXT,
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "init"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "add", "specs/SPEC-0001-payment-retry.md"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            base_command = [
                sys.executable,
                str(SCRIPTS_ROOT / "guided_workflow_router.py"),
                "--project-root",
                str(root),
                "--json",
            ]
            default_route = subprocess.run(
                [
                    *base_command,
                    "--prompt",
                    "新增另一個付款部署規格",
                ],
                cwd=PLUGIN_ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            resume_route = subprocess.run(
                [
                    *base_command,
                    "--prompt",
                    "修改並繼續既有付款 change set",
                    "--resume-confirmed-spec",
                ],
                cwd=PLUGIN_ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(
            "grill-with-docs",
            json.loads(default_route.stdout)["selected_skill"],
        )
        self.assertEqual(
            "spec-governance",
            json.loads(resume_route.stdout)["selected_skill"],
        )

    def test_cli_pass_output_is_one_summary_line(self) -> None:
        build_root = PLUGIN_ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build_root) as directory:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_ROOT / "guided_workflow_router.py"),
                    "--prompt",
                    "建立一個自己使用的投資工具",
                    "--project-root",
                    directory,
                ],
                cwd=PLUGIN_ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(1, len(completed.stdout.strip().splitlines()))
        self.assertIn("PASS", completed.stdout)
        self.assertIn("grill-me", completed.stdout)

    def test_cli_degraded_output_expands_evidence(self) -> None:
        build_root = PLUGIN_ROOT / "build"
        build_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build_root) as directory:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_ROOT / "guided_workflow_router.py"),
                    "--prompt",
                    "建立一個自己使用的投資工具",
                    "--project-root",
                    directory,
                    "--available-skill",
                    "grilling",
                    "--available-skill",
                    "tdd",
                    "--available-skill",
                    "code-review",
                ],
                cwd=PLUGIN_ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertGreater(len(completed.stdout.strip().splitlines()), 1)
        self.assertIn('"status": "DEGRADED"', completed.stdout)
        self.assertIn('"evidence"', completed.stdout)


if __name__ == "__main__":
    unittest.main()
