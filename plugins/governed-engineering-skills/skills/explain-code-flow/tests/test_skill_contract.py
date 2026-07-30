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
                "| `2.0.2` | `2.0.2` | Supported | Supported after"
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
        self.assertIn("deterministic renderer with `--check`", SKILL)
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
            "retains valid formal governance; label implementation consistency incomplete",
            SKILL,
        )

    def test_schema_2_0_2_evidence_is_exposed(self) -> None:
        for required in (
            "production, generated-production, development, derived-documentation, and build-output",
            "Type ownership, State ownership, and cross-module Boundary Mapping",
            "For schema 2.0.2, include the inherited execution contract",
            "schema 2.0.2 inherited workload",
            "C/C++ consistency requires complete AST evidence",
        ):
            with self.subTest(required=required):
                self.assertIn(required, SKILL)

    def test_ui_metadata_still_invokes_the_updated_skill(self) -> None:
        self.assertIn('display_name: "迭代式程式資料流與架構導讀"', METADATA)
        self.assertIn("$explain-code-flow", METADATA)
        self.assertIn("Schema 2.0.2 正式視圖", METADATA)
        self.assertIn("原始碼與 AST 證據", METADATA)
        self.assertIn("allow_implicit_invocation: true", METADATA)

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
