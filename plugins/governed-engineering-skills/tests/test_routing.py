from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER_PATH = PLUGIN_ROOT / "skills" / "engineering-risk-routing" / "scripts" / "classify_risk.py"
SPEC = importlib.util.spec_from_file_location("classify_risk", CLASSIFIER_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
classify = MODULE.classify


class RoutingFixtures(unittest.TestCase):
    def assert_contract(self, result: dict) -> None:
        schema_path = (
            PLUGIN_ROOT
            / "skills"
            / "engineering-risk-routing"
            / "references"
            / "routing-contract.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        contract = schema["$defs"]["RoutingDecision"]
        self.assertEqual(set(contract["required"]) | {"blockers"}, set(result))
        self.assertIn(result["status"], contract["properties"]["status"]["enum"])
        self.assertIn(result["risk_class"], contract["properties"]["risk_class"]["enum"])

    def test_read_only_code_flow_is_r0(self) -> None:
        result = classify("請唯讀導讀這段程式的資料流")
        self.assertEqual("R0", result["risk_class"])
        self.assertEqual(["explain-code-flow"], result["required_gates"])

    def test_standard_reversible_feature_is_r1(self) -> None:
        result = classify("Add a reversible formatter option with unit tests")
        self.assertEqual("R1", result["risk_class"])
        self.assertNotIn("validate-on-device", result["required_gates"])

    def test_module_or_type_ownership_is_r2(self) -> None:
        result = classify("Split this module and fix type ownership")
        self.assertEqual("R2", result["risk_class"])
        self.assertIn("govern-modular-event-architecture", result["required_gates"])

    def test_firmware_and_timing_are_r3(self) -> None:
        result = classify("Change CAN firmware ISR timing")
        self.assertEqual("R3", result["risk_class"])
        self.assertIn("validate-on-device", result["required_gates"])

    def test_direct_implement_is_blocked_before_governance(self) -> None:
        result = classify("Refactor module architecture", entry_skill="implement", passed_gates=set())
        self.assertEqual("BLOCKED", result["status"])

    def test_direct_implement_resumes_after_governance(self) -> None:
        result = classify(
            "Refactor module architecture",
            entry_skill="implement",
            passed_gates={"govern-modular-event-architecture"},
        )
        self.assertEqual("PASS", result["status"])

    def test_unit_test_does_not_trigger_device_validation(self) -> None:
        result = classify("Add an ordinary unit test for the parser")
        self.assertEqual("R1", result["risk_class"])
        self.assertNotIn("validate-on-device", result["required_gates"])

    def test_highest_risk_wins(self) -> None:
        result = classify("Explain then refactor the firmware module ISR")
        self.assertEqual("R3", result["risk_class"])

    def test_missing_required_capability_fails_closed(self) -> None:
        result = classify(
            "Change firmware timing",
            available_skills={
                "clarify-improvement-proposals",
                "govern-modular-event-architecture",
            },
        )
        self.assertEqual("BLOCKED", result["status"])
        self.assertTrue(any("validate-on-device" in item for item in result["blockers"]))

    def test_missing_legacy_governance_requires_as_is_baseline(self) -> None:
        result = classify(
            "Refactor this module architecture",
            governance_status="missing",
        )
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn(
            "as-is architecture inventory and baseline required",
            result["blockers"],
        )
        self.assertEqual("govern-modular-event-architecture", result["required_gates"][1])

    def test_learning_note_is_outside_engineering_router(self) -> None:
        result = classify("把今天內容整理成 HackMD 學習筆記")
        self.assertEqual("out_of_scope", result["task_class"])
        self.assertIsNone(result["risk_class"])
        self.assertIsNone(result["next_skill"])

    def test_all_decisions_match_public_contract_shape(self) -> None:
        for prompt in (
            "Explain code flow",
            "Add a unit test",
            "Refactor module architecture",
            "Change firmware ISR timing",
            "建立 HackMD 學習筆記",
        ):
            with self.subTest(prompt=prompt):
                self.assert_contract(classify(prompt))


if __name__ == "__main__":
    unittest.main()
