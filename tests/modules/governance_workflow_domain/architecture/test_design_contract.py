import copy
import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "CLAUDE.md").is_file())
sys.path.insert(
    0, str(ROOT / "skills/engineering/govern-modular-event-architecture/scripts")
)
from design_contract import (
    MODULE_FIELDS,
    INTERFACE_FIELDS,
    FLOW_FIELDS,
    validate_designs,
    render_designs,
)
from coding_rule_contract import catalog, validate_rule_binding


def example():
    def record(fields):
        result = {
            "status": "planned",
            "module_ref": "sensor",
            "evidence_refs": [],
            "groups": {
                field: {
                    "applicability": "applicable",
                    "value": "Bounded synchronous sensor processing",
                    "refs": {"modules": ["sensor"]},
                }
                for field in fields
            },
        }
        if fields == INTERFACE_FIELDS:
            result["groups"]["parameters"]["value"] = [
                {
                    "name": "sample",
                    "type": "immutable Sample",
                    "meaning": "One calibrated IMU sample",
                    "passing": "borrowed reference during call",
                    "nullability": "non-null",
                }
            ]
            result["groups"]["access_lifetime"]["value"] = (
                "Read-only borrow ends before synchronous return; caller prevents concurrent mutation."
            )
            result["groups"]["completion_result"]["value"] = (
                "Return means local processing completed, not transport or remote completion."
            )
        if fields == FLOW_FIELDS:
            result["groups"]["steps"]["value"] = [
                {
                    "id": "process",
                    "producer": "sensor",
                    "consumer": "sensor",
                    "interface_ref": "sensor.process",
                    "interaction": "synchronous call",
                    "completion": "returned processed result",
                    "handoff": "immutable sample borrowed only during call",
                    "failure": "reject invalid range; retain previous module state and report event",
                }
            ]
        if fields == MODULE_FIELDS:
            result["groups"]["error_lifecycle"]["value"] = {
                "transitions_applicability": "not-applicable",
                "transitions_reason": "Stateless calibration; failures return without retaining state and submit the declared abnormal event.",
            }
            result["groups"]["responsibility"]["value"] = (
                "Validate and process one IMU sample; transport and subscription fan-out belong to the parent."
            )
            result["groups"]["implementation_method"]["value"] = (
                "Apply the configured calibration synchronously; no internal queue, retained input reference or transport buffer."
            )
        return result

    return {
        "modules": [{"id": "sensor"}],
        "flows": [{"id": "sample"}],
        "implementation_design": {
            "version": 1,
            "modules": {"sensor": record(MODULE_FIELDS)},
            "interfaces": {"sensor.process": record(INTERFACE_FIELDS)},
            "flows": {"sample": record(FLOW_FIELDS)},
        },
    }


class DesignContractTests(unittest.TestCase):
    def test_complete_design_has_deterministic_generated_view(self):
        m = example()
        self.assertEqual([], validate_designs(m))
        self.assertEqual(render_designs(m), render_designs(copy.deepcopy(m)))
        self.assertIn("sensor.process", render_designs(m))

    def test_missing_owner_coverage_unknown_and_unproven_verification_fail(self):
        for change in (
            lambda d: d["modules"].clear(),
            lambda d: d["interfaces"]["sensor.process"].update(module_ref="absent"),
            lambda d: d["modules"]["sensor"]["groups"].pop("resource_timing"),
            lambda d: d["modules"]["sensor"].update(status="verified"),
            lambda d: d["modules"]["sensor"]["groups"]["responsibility"].update(
                applicability="unknown", reason="target unavailable"
            ),
            lambda d: d["modules"]["sensor"]["groups"]["responsibility"].update(
                refs={"modules": ["absent"]}
            ),
            lambda d: d["flows"]["sample"]["groups"]["steps"]["value"][0].pop(
                "completion"
            ),
            lambda d: d["flows"]["sample"]["groups"]["steps"]["value"][0].update(
                interface_ref="absent"
            ),
            lambda d: d["interfaces"]["sensor.process"]["groups"]["parameters"][
                "value"
            ][0].pop("passing"),
        ):
            m = example()
            change(m["implementation_design"])
            self.assertTrue(validate_designs(m))
            self.assertIsNone(render_designs(m))

    def test_legacy_absence_does_not_claim_design_verification(self):
        self.assertEqual([], validate_designs({}))
        self.assertIsNone(render_designs({}))

    def test_state_transition_fields_and_references(self):
        m = example()
        m["state_objects"] = [{"id": "sensor.runtime"}]
        value = {
            "transitions": [
                {
                    "state_object_ref": "sensor.runtime",
                    "from_state": "ready",
                    "to_state": "fault",
                    "trigger": "invalid sensor input",
                    "guard": "range validation failed",
                    "effects": "stop invalid processing; commit fault; submit abnormal event",
                }
            ]
        }
        m["implementation_design"]["modules"]["sensor"]["groups"]["error_lifecycle"][
            "value"
        ] = value
        self.assertEqual([], validate_designs(m))
        value["transitions"][0]["state_object_ref"] = "missing"
        self.assertTrue(validate_designs(m))
        value["transitions"][0]["state_object_ref"] = "sensor.runtime"
        value["transitions"][0].pop("guard")
        self.assertTrue(validate_designs(m))

    def test_malformed_yaml_values_return_diagnostics_instead_of_crashing(self):
        from datetime import date

        self.assertTrue(validate_designs({"implementation_design": None}))
        self.assertIsNone(render_designs({"implementation_design": None}))
        m = example()
        m["implementation_design"]["modules"]["sensor"]["groups"]["responsibility"][
            "value"
        ] = date(2026, 10, 2)
        self.assertTrue(validate_designs(m))
        self.assertIsNone(render_designs(m))
        for field in ("module_ref", "status"):
            m = example()
            m["implementation_design"]["modules"]["sensor"][field] = ["bad"]
            self.assertTrue(validate_designs(m))
        m = example()
        m["implementation_design"]["modules"]["sensor"]["groups"]["responsibility"][
            "applicability"
        ] = {}
        self.assertTrue(validate_designs(m))
        m["modules"] = None
        self.assertTrue(validate_designs(m))

    def test_selected_catalog_requires_current_digest_and_complete_applicability(self):
        current = catalog()
        m = example()
        self.assertTrue(validate_rule_binding(m))
        m["coding_rules"] = {k: current[k] for k in ("version", "sha256")}
        m["coding_rules"]["applicability"] = {
            rule: {
                "status": "applicable",
                "reason": "Module under review uses this contract",
            }
            for rule in current["ids"]
        }
        self.assertEqual([], validate_rule_binding(m))
        m["coding_rules"]["sha256"] = "0" * 64
        self.assertTrue(validate_rule_binding(m))
        m["coding_rules"]["sha256"] = current["sha256"]
        m["coding_rules"]["applicability"].pop(current["ids"][0])
        self.assertTrue(validate_rule_binding(m))


if __name__ == "__main__":
    unittest.main()
