import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ValidationWorkflowSkillTests(unittest.TestCase):
    def test_four_gates_and_evidence_rules_are_explicit(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Validation Enablement",
            "Per-change Development Validation",
            "Final Runtime Acceptance",
            "Release Acceptance",
            "never invent a universal 30-second acceptance window",
            "calculable sampling plan",
            "structured logs cannot pass supported-OS scheduler/resource criteria",
            "all four gates are `PASS`",
            "Treat ordinary Gate 1 checks as host-side development tests",
            "Fake child Ports",
            "Fake dependency Ports",
            "demand-owned reusable contract suite",
            "Do not plan flash, Serial/TCP capture",
            "A smoke result can support Gate 1 but cannot satisfy Gate 2",
        ):
            self.assertIn(phrase, text)

    def test_product_algorithm_decisions_are_required(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        metadata = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        for phrase in (
            "Screen every product feature",
            "Algorithm Design Record",
            "specific `not applicable` reason",
            "risk-required",
            "Algorithm impact",
            "quantitative acceptance thresholds",
        ):
            self.assertIn(phrase, text)
        self.assertIn("screen product features for algorithm decisions", metadata)


if __name__ == "__main__":
    unittest.main()
