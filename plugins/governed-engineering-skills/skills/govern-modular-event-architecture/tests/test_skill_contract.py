from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_single_cli_and_honest_legacy_policy(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "architecture_cli.py",
            "only public governance CLI",
            "Default to remediation",
            "Release requires a zero-entry temporary baseline",
            "An empty baseline is not completion evidence",
            "tool-host OS/Python compatibility metadata",
        ):
            self.assertIn(phrase, text)

    def test_skill_routes_realtime_workloads_to_scheduler_compatible_gate(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = (ROOT / "references" / "realtime-scheduling-analysis.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "references/realtime-scheduling-analysis.md",
            "every hard/soft real-time workload",
            "at least two structurally different scheduling candidates",
            "generated human-readable Markdown study report",
            "human selection of a provisional-PASS candidate",
        ):
            self.assertIn(phrase, text)
        for phrase in (
            "Timing class triggers the scheduling study",
            "partitioned, fully preemptive, fixed-priority",
            "level-i busy period",
            "realtime-study-<study-id>.md",
            "`SOFT_RISK`",
            "RTOS use alone does not",
            "`$validate-on-device`",
        ):
            self.assertIn(phrase, reference)


if __name__ == "__main__":
    unittest.main()
