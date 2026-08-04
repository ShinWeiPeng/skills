from __future__ import annotations

import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PLUGIN_ROOT / "skills"
ARCHITECTURE_ROOT = PLUGIN_ROOT / "architecture"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


class SharedFlowCostContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = read(
            SKILLS_ROOT
            / "govern-modular-event-architecture"
            / "references"
            / "flow-cost-review.md"
        )

    def test_contract_defines_four_ordered_dimensions(self) -> None:
        for heading in (
            "Functional admission",
            "Execution cost and real-time feasibility",
            "Maintainability and extensibility",
            "Model assurance",
        ):
            self.assertIn(heading, self.reference)

    def test_contract_defines_assurance_verdicts_and_evidence(self) -> None:
        for token in (
            "`estimated`",
            "`calibrated`",
            "`validated`",
            "`BLOCKED`",
            "prediction error",
            "scenario coverage",
            "uncovered risks",
            "reserve source",
            "evidence reference",
            "production-equivalent",
        ):
            self.assertIn(token, self.reference)

    def test_existing_and_greenfield_flows_have_distinct_entry_rules(self) -> None:
        reference = collapse_whitespace(self.reference)
        self.assertIn("Existing project", reference)
        self.assertIn("as-is Flow", reference)
        self.assertIn("Greenfield", reference)
        self.assertIn("portable estimate", reference)
        self.assertIn("at least two structurally different candidates", reference)
        self.assertIn("external compatibility", reference)
        self.assertIn("internal orchestration", reference)

    def test_fail_closed_regression_fixtures_are_normative(self) -> None:
        for fixture in (
            "STACK-UNIT-AMBIGUITY",
            "HIDDEN-REENTRY",
            "SCENARIO-GAP",
            "BUILD-MISMATCH",
            "PREDICTION-OVERRUN",
            "MISSING-RESERVE-SOURCE",
            "AVERAGE-ONLY-REALTIME",
            "BEST-EFFORT-RISK",
        ):
            row = next(
                (
                    line
                    for line in self.reference.splitlines()
                    if line.startswith(f"| `{fixture}` ")
                ),
                "",
            )
            self.assertTrue(row, fixture)
            self.assertIn("`BLOCKED`", row)

    def test_stack_and_realtime_evidence_are_not_average_only(self) -> None:
        reference = collapse_whitespace(self.reference).casefold()
        for token in (
            "ABI",
            "RTOS",
            "LTO",
            "API units",
            "callback re-entry",
            "indirect calls",
            "large locals",
            "TLS",
            "high-water",
            "canary",
            "WCET",
            "release jitter",
            "blocking",
            "interrupt interference",
            "average-only",
        ):
            self.assertIn(token.casefold(), reference)

    def test_evolution_uses_change_scenarios_and_pareto_comparison(self) -> None:
        for token in (
            "source",
            "subscriber",
            "adapter",
            "processing stage",
            "platform variant",
            "locality",
            "leverage",
            "constraint filtering",
            "Pareto",
        ):
            self.assertIn(token, self.reference)


class SkillIntegrationContractTests(unittest.TestCase):
    def test_three_skills_route_through_the_shared_contract(self) -> None:
        expected = {
            "improve-codebase-architecture": "flow-cost-review.md",
            "clarify-improvement-proposals": "flow-cost-review.md",
            "govern-modular-event-architecture": "flow-cost-review.md",
        }
        for skill, reference in expected.items():
            text = read(SKILLS_ROOT / skill / "SKILL.md")
            self.assertIn(reference, text, skill)

    def test_architecture_report_requires_execution_and_evolution_evidence(self) -> None:
        report = collapse_whitespace(
            read(SKILLS_ROOT / "improve-codebase-architecture" / "HTML-REPORT.md")
        )
        for token in (
            "critical path",
            "model status",
            "confidence basis",
            "predicted",
            "observed",
            "scenario coverage",
            "resource headroom",
            "change-scenario",
            "Pareto",
        ):
            self.assertIn(token, report)

    def test_manifest_and_algorithm_inventory_describe_flow_review(self) -> None:
        manifest = read(ARCHITECTURE_ROOT / "manifest.yaml")
        inventory = read(ARCHITECTURE_ROOT / "algorithms" / "README.md")
        self.assertIn("governed-change-set-lifecycle.review-flow-cost", manifest)
        self.assertIn("Flow cost review", inventory)
        self.assertIn("ALG-0005", inventory)

    def test_agents_metadata_mentions_flow_cost_evidence(self) -> None:
        for skill in (
            "improve-codebase-architecture",
            "clarify-improvement-proposals",
            "govern-modular-event-architecture",
        ):
            metadata = read(SKILLS_ROOT / skill / "agents" / "openai.yaml")
            self.assertIn("flow", metadata.casefold(), skill)
            self.assertIn("evidence", metadata.casefold(), skill)


if __name__ == "__main__":
    unittest.main()
