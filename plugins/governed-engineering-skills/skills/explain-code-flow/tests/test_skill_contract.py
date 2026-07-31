"""Contract tests for the explain-code-flow skill instructions."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
METADATA = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")


class ExplainCodeFlowContractTests(unittest.TestCase):
    def test_only_schema_2_0_2_has_formal_support(self) -> None:
        matrix = SKILL.split("### Enforce the capability matrix", 1)[1].split(
            "### Route a blocked request through governance", 1
        )[0]
        data_rows = [
            line
            for line in matrix.splitlines()
            if line.startswith("| ")
            and not line.startswith("| Standard ")
            and not line.startswith("|---")
        ]

        self.assertEqual(2, len(data_rows))
        self.assertTrue(
            data_rows[0].startswith(
                "| `2.1.0` | `2.1.0` | Supported | Supported after"
            )
        )
        self.assertTrue(data_rows[1].startswith("| Any other pair, including `1.x` |"))

    def test_governance_owns_formal_view_translation(self) -> None:
        self.assertIn(
            "Read the validated generated System or Parent view as the formal architecture input.",
            SKILL,
        )
        self.assertIn(
            "Do not reinterpret the complete manifest schema or independently regenerate a competing formal view",
            SKILL,
        )
        self.assertIn(
            "it owns manifest validation, generated-view comparison, baseline reconciliation, adoption readiness, and applicable language analyzers",
            SKILL,
        )
        self.assertIn(
            "Let the governance checker and renderer own the expected-page inventory",
            SKILL,
        )

    def test_local_explanation_is_not_blocked_by_schema_gate(self) -> None:
        self.assertIn(
            "Apply this gate only to Level 0 System requests and Level 1 Parent requests.",
            SKILL,
        )
        self.assertIn(
            "Do not apply it to a Flow, module, symbol, function, method, or code-region request.",
            SKILL,
        )
        self.assertIn(
            "For a Flow, module, symbol, function, method, or code-region request, continue with static analysis even when the gate would fail.",
            SKILL,
        )

    def test_capability_and_project_validity_are_distinct(self) -> None:
        self.assertIn("Distinguish capability from project validity:", SKILL)
        self.assertIn(
            "it is not evidence that the project itself is invalid", SKILL
        )
        self.assertIn(
            "lacks complete evidence is `BLOCKED` for formal System/Parent guidance",
            SKILL,
        )

    def test_coverage_separates_inspection_from_analyzer_verdict(self) -> None:
        self.assertIn("Inspection coverage", SKILL)
        self.assertIn("Analyzer verdict", SKILL)
        self.assertIn("Never translate `已檢視` into analyzer `PASS`", SKILL)

    def test_schema_2_0_2_evidence_is_exposed(self) -> None:
        for required in (
            "production, generated-production, development, derived-documentation, and build-output",
            "Type ownership, State ownership, and cross-module Boundary Mapping",
            "For schema 2.1.0, include the inherited execution contract",
            "schema 2.1.0 inherited workload",
            "C/C++ consistency requires complete AST evidence",
        ):
            with self.subTest(required=required):
                self.assertIn(required, SKILL)

    def test_ui_metadata_still_invokes_the_updated_skill(self) -> None:
        self.assertIn('display_name: "迭代式程式資料流與架構導讀"', METADATA)
        self.assertIn("$explain-code-flow", METADATA)
        self.assertIn("所有程式理解問題", METADATA)
        self.assertIn("Schema 2.1.0 正式視圖", METADATA)
        self.assertIn("原始碼與 AST 證據", METADATA)
        self.assertIn("allow_implicit_invocation: true", METADATA)

    def test_every_code_understanding_request_is_in_scope(self) -> None:
        frontmatter = SKILL.split("---", 2)[1]
        for required in (
            "Use for every code-understanding request",
            "what code does",
            "how data reaches a driver or other sink",
            "where state changes",
            "why a branch exists",
        ):
            with self.subTest(required=required):
                self.assertIn(required, frontmatter)

    def test_routing_is_deterministic_and_level_specific(self) -> None:
        routing = SKILL.split("## Route every code-understanding request", 1)[1].split(
            "## Apply the formal-governance gate", 1
        )[0]
        expected_cases = {
            "講解專案內多關節路徑規劃到實際 driver 輸出": "Level 1 Flow",
            "MJ_SetupTrajectory() 做什麼？": "Level 2 Module or symbol",
            "第 120–145 行的 branch 為什麼 early return？": "Level 3 Code region",
        }
        for prompt, expected_level in expected_cases.items():
            with self.subTest(prompt=prompt):
                row = next(line for line in routing.splitlines() if prompt in line)
                self.assertIn(expected_level, row)
        self.assertIn("cross-module path from A to B", routing)

    def test_specialized_workflows_keep_primary_ownership(self) -> None:
        routing = SKILL.split("## Route every code-understanding request", 1)[1].split(
            "## Distinguish the two level systems", 1
        )[0]
        self.assertIn("implementation or TDD workflow lead", routing)
        self.assertIn("`$diagnosing-bugs` lead", routing)
        self.assertIn("`$code-review` lead", routing)
        self.assertIn("this skill is supporting only", routing)

    def test_attachments_cannot_replace_code_flow_guidance(self) -> None:
        self.assertIn(
            "Do not let an attached presentation, document, spreadsheet, diagram, or note replace the code-understanding deliverable.",
            SKILL,
        )
        self.assertIn(
            "A code-understanding response is not replaced by an artifact-editing plan or general summary",
            SKILL,
        )

    def test_level_1_flow_final_self_check_is_complete(self) -> None:
        checks = SKILL.split(
            "## Validate the response contract before returning", 1
        )[1].split("## Save only on explicit request", 1)[0]
        for required in (
            "project-to-Parent-to-Flow breadcrumb",
            "owner, description, trigger, source data meaning, and entrypoint",
            "Mermaid sequence diagram",
            "#｜Module｜Action｜Receives｜Emits｜State changes｜Side effects｜程式錨點",
            "success result and committed state",
            "every evidenced error branch and handling outcome",
            "timing and task/thread/interrupt/queue/callback boundaries",
            "inherited execution evidence when declared",
            "implementation links and core function roles",
            "evidence-backed risks and uncertainties",
            "compact navigation block",
        ):
            with self.subTest(required=required):
                self.assertIn(required, checks)

    def test_existing_output_api_is_preserved(self) -> None:
        headings = (
            "## 1. 專案定位",
            "## 2. 架構地圖",
            "## 3. 開發者閱讀導覽",
            "## 4. 完整資料流索引",
            "## 5. 開發任務索引",
            "## 6. Coverage ledger",
            "## 7. 架構與資料流風險",
            "## 8. 下一層導讀選項",
        )
        positions = [SKILL.index(heading) for heading in headings]

        self.assertEqual(sorted(positions), positions)
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertEqual(1, SKILL.splitlines().count(heading))
        self.assertIn(
            "`**正式架構脈絡：可用** — Standard/Schema: <validated pair>`",
            SKILL,
        )
        self.assertIn(
            "`**正式架構脈絡：受限** — <missing, legacy, unsupported, invalid, or stale reason>`",
            SKILL,
        )
        self.assertIn("### 精簡導覽", SKILL)


if __name__ == "__main__":
    unittest.main()
