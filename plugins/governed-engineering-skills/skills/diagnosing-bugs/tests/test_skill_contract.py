"""Contract tests for the diagnosing-bugs skill instructions."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
PACKET = (ROOT / "references" / "debug-model-packet.md").read_text(
    encoding="utf-8"
)
DOCS = (
    ROOT.parents[3] / "docs" / "engineering" / "diagnosing-bugs.md"
).read_text(encoding="utf-8")


class DiagnosingBugsContractTests(unittest.TestCase):
    def test_model_alignment_follows_reproduction_and_precedes_hypotheses(self) -> None:
        phase_2 = SKILL.index("## Phase 2 — Reproduce + minimise")
        phase_2_5 = SKILL.index("## Phase 2.5 — Align a shared computation model")
        phase_3 = SKILL.index("## Phase 3 — Hypothesise")

        self.assertLess(phase_2, phase_2_5)
        self.assertLess(phase_2_5, phase_3)

    def test_existing_red_capable_gate_is_preserved(self) -> None:
        phase_1 = SKILL.split("## Phase 1 — Build a feedback loop", 1)[1].split(
            "## Phase 2 — Reproduce + minimise", 1
        )[0]
        self.assertIn("one command", phase_1)
        self.assertIn("already run at least once", phase_1)
        self.assertIn("Red-capable", phase_1)
        self.assertIn("No red-capable command, no Phase 2", phase_1)

    def test_risk_triggers_and_stateless_skip_are_explicit(self) -> None:
        alignment = SKILL.split(
            "## Phase 2.5 — Align a shared computation model", 1
        )[1].split("## Phase 3 — Hypothesise", 1)[0]
        for required in (
            "multiple counters",
            "state machines",
            "event ordering",
            "multi-stage transformations",
            "simple stateless condition",
            "state the reason explicitly",
        ):
            with self.subTest(required=required):
                self.assertIn(required, alignment)

    def test_understanding_gate_blocks_premature_diagnosis(self) -> None:
        alignment = SKILL.split(
            "### Understanding gate", 1
        )[1].split("## Phase 3 — Hypothesise", 1)[0]
        for required in (
            "stop and ask the user to confirm",
            "does not ask the user to agree with a root cause or fix",
            "Do not generate ranked hypotheses",
            "declare a root cause",
            "compare repairs",
            "repeat the gate",
            "`BLOCKED`",
        ):
            with self.subTest(required=required):
                self.assertIn(required, alignment)

    def test_packet_requires_complete_computation_model(self) -> None:
        for required in (
            "Confirmed（已確認）",
            "Inference（推論）",
            "To verify（待確認）",
            "Mermaid flowchart",
            "Mermaid sequence diagram",
            "Counter and state contracts",
            "Conservation or reconciliation",
            "Minimal worked trace",
            "First semantic divergence",
            "Understanding gate",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PACKET)

    def test_counter_contract_and_trace_are_precise(self) -> None:
        for required in (
            "Unit and scope",
            "Increment/update condition",
            "Does not change when",
            "Clear/reset condition",
            "Threshold and epoch",
            "What it proves",
            "What it cannot prove",
            "Counter delta",
            "Pending/state after",
            "Offset/lock/epoch after",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PACKET)

    def test_diagram_never_replaces_arithmetic(self) -> None:
        self.assertIn(
            "does **not** replace exact counter arithmetic", PACKET
        )
        self.assertIn(
            "Never infer per-event order from periodic or aggregated snapshots",
            PACKET,
        )

    def test_flowchart_marks_error_path_and_evidence_status(self) -> None:
        decision_flow = PACKET.split("## 2. Decision flow", 1)[1].split(
            "## 3. Event sequence", 1
        )[0]
        for required in (
            "observed error path",
            "evaluated value on each decision edge",
            "`FIRST DIVERGENCE`",
            "final observable symptom",
            "evidence ID",
            "red stroke or error class",
            "textual label",
            "`INFERRED ERROR PATH`",
            "Do not render an inferred path as a confirmed observation",
        ):
            with self.subTest(required=required):
                self.assertIn(required, decision_flow)

        self.assertIn("classDef error", decision_flow)
        self.assertIn("classDef divergence", decision_flow)
        self.assertIn("linkStyle", decision_flow)

    def test_later_claims_remain_tied_to_model_and_evidence(self) -> None:
        self.assertIn(
            "link back to a flow node, counter/state contract, trace row, and evidence item",
            PACKET,
        )
        self.assertIn(
            "predict which counters, states, and outputs will change", PACKET
        )
        self.assertIn("`PASS`, `FAIL`, or `BLOCKED`", PACKET)

    def test_promoted_docs_explain_the_packet_and_gate(self) -> None:
        for required in (
            "Debug Model Packet",
            "counter/state contracts",
            "conservation equations",
            "minimal event-by-event trace",
            "The understanding gate is risk-based",
            "before root-cause ranking",
            "observed error path",
            "`FIRST DIVERGENCE`",
            "`INFERRED ERROR PATH`",
        ):
            with self.subTest(required=required):
                self.assertIn(required, DOCS)


if __name__ == "__main__":
    unittest.main()
