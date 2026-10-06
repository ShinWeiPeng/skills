from __future__ import annotations
import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "CLAUDE.md").is_file())
PLUGIN = ROOT / "dist/governed-engineering-skills/skills"
sys.path[:0] = [
    str(PLUGIN / "govern-modular-event-architecture/scripts"),
    str(PLUGIN / "spec-governance/scripts"),
]
from os_design_contract import (
    validate_os_designs,
    GROUPS,
    CATEGORIES,
    SCHEDULE_FIELDS,
    CHANNEL_FIELDS,
)
from document_bundle import render_design, parse_design
from design_sources import source_documents, generate_manifest, source_versions
from coding_rule_contract import catalog


def quantity(value=1, unit="ms"):
    return {
        "value": value,
        "unit": unit,
        "basis": "declared budget",
        "source_refs": ["REQ-1"],
    }


def fixture():
    facts = {
        k: {
            "status": "known",
            "reason": "target fact",
            "value": "supported",
            "basis": "platform docs",
            "source_refs": ["vendor-manual"],
        }
        for k in (
            "os",
            "cpu",
            "cores",
            "usable_ram",
            "capabilities",
            "call_limits",
            "scheduler",
        )
    }
    facts["os"]["value"] = "test RTOS 1.0"
    facts["cpu"]["value"] = "test CPU"
    facts["cores"] |= {"value": 1, "unit": "count"}
    facts["usable_ram"] |= {"value": 64, "unit": "KiB"}
    groups = {
        k: {
            "status": "applicable",
            "reason": "confirmed method",
            "details": {f: "specified contract" for f in v},
        }
        for k, v in GROUPS.items()
    }
    groups["units"]["details"]["items"] = [
        {
            "id": "task1",
            "kind": "Task",
            "responsibility": "process samples",
            "module_refs": [{"id": "m1", "version": 1}],
            "call_environment": "task",
        }
    ]
    scheduling = {f: "specified contract" for f in SCHEDULE_FIELDS} | {
        "unit_ref": "task1"
    }
    groups["scheduling"]["details"] = {"items": [scheduling]}
    channel = {f: "specified contract" for f in CHANNEL_FIELDS} | {
        "id": "q1",
        "senders": ["task1"],
        "receivers": ["task1"],
    }
    groups["channels"]["details"] = {"items": [channel]}
    for key in ("deadline", "execution_budget", "wait_budget"):
        scheduling[key] = quantity()
    scheduling["frequency_burst"] = {
        "frequency": quantity(100, "Hz"),
        "burst": quantity(1, "count"),
    }
    groups["channels"]["details"]["items"][0]["capacity"] = quantity(8, "count")
    resources = groups["resources"]["details"]
    resources["total_simultaneous"] = quantity(1024, "B")
    resources["os_overhead"] = quantity(128, "B")
    resources["capacities"] = [
        {
            "id": "stack1",
            "kind": "stack",
            "quantity": 1024,
            "unit": "B",
            "owner": "task1",
            "basis": "estimate",
            "source_refs": ["budget-1"],
        }
    ]
    evidence = {
        p: {
            "status": "pending",
            "method": "target test",
            "refs": [],
            "environment": "target",
        }
        for p in ("design", "implementation", "acceptance")
    }
    evidence["design"] = {
        "status": "pass",
        "method": "design review",
        "refs": ["review-1"],
        "environment": "review",
    }
    return {
        "modules": [{"id": "m1"}],
        "flows": [],
        "platform_design": {"id": "p1", "version": 1, "data": facts},
        "execution_design": {
            "id": "x1",
            "version": 1,
            "data": {
                "platform_ref": {"id": "p1", "version": 1},
                "design_refs": [{"id": "m1", "version": 1}],
                "applicability": {
                    k: {"status": "applicable", "reason": "required"}
                    for k in CATEGORIES
                },
                "groups": groups,
                "evidence": evidence,
            },
        },
    }


class OsGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = fixture()
        for path, text in source_documents(self.manifest).items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        self.versions = source_versions(self.root)

    def check(self, phase="design"):
        return validate_os_designs(self.manifest, phase, self.versions)

    def test_design_pass_does_not_require_unproduced_runtime_results(self):
        self.assertEqual([], self.check())
        self.assertTrue(self.check("development"))
        self.assertTrue(self.check("release"))

    def test_completion_requires_phase_evidence(self):
        evidence = self.manifest["execution_design"]["data"]["evidence"]
        for phase in ("implementation", "acceptance"):
            evidence[phase] = {
                "status": "pass",
                "method": "recorded target tests",
                "refs": ["run-1"],
                "environment": "target RTOS build",
            }
        self.assertEqual([], self.check("release"))

    def test_fixed_table_and_yaml_round_trip(self):
        self.assertEqual(self.manifest, generate_manifest(self.root)[0])
        platform = (self.root / "architecture/designs/platform/platform.md").read_text(
            encoding="utf-8"
        )
        execution = (
            self.root / "architecture/designs/execution/execution.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## Platform Facts", platform)
        self.assertIn("## Execution Units", execution)
        self.assertIn("## Resource Inventory", execution)
        self.assertNotIn("capacities:", execution)
        self.assertNotIn("\n  cores:", platform)

    def test_duplicate_table_and_yaml_owner_rejected(self):
        path = self.root / "architecture/designs/platform/platform.md"
        text = path.read_text(encoding="utf-8")
        bad = text.replace("value:\n", "value:\n  cores: hidden\n", 1)
        with self.assertRaisesRegex(ValueError, "duplicate platform"):
            parse_design(bad, str(path))

    def test_wrong_reference_version_and_unknown_id_fail(self):
        refs = self.manifest["execution_design"]["data"]["design_refs"]
        for ref in ({"id": "missing", "version": 1}, {"id": "m1", "version": 2}):
            refs[:] = [ref]
            self.assertTrue(self.check())

    def test_unit_reference_must_resolve_to_module(self):
        self.manifest["execution_design"]["data"]["groups"]["units"]["details"][
            "items"
        ][0]["module_refs"] = [{"id": "p1", "version": 1}]
        self.assertTrue(self.check())

    def test_quantities_require_type_units_and_basis(self):
        scheduling = self.manifest["execution_design"]["data"]["groups"]["scheduling"][
            "details"
        ]["items"][0]
        for bad in (
            "10",
            {"value": 10},
            quantity(1, "B"),
            quantity(float("nan")),
            quantity(True),
        ):
            scheduling["deadline"] = bad
            self.assertTrue(self.check())

    def test_platform_capacity_is_numeric_with_supported_unit(self):
        for bad in ("one", True, -1, 1.5):
            self.manifest["platform_design"]["data"]["cores"]["value"] = bad
            self.assertTrue(self.check())

    def test_unknown_is_distinct_from_not_applicable(self):
        row = self.manifest["execution_design"]["data"]["applicability"]["resources"]
        row["status"] = "unknown"
        self.assertTrue(self.check())
        row["status"] = "not-applicable"
        self.assertEqual([], self.check())

    def test_resource_and_channel_capacity_limits_are_typed(self):
        groups = self.manifest["execution_design"]["data"]["groups"]
        groups["channels"]["details"]["items"][0]["capacity"] = quantity(1, "Hz")
        self.assertTrue(self.check())
        groups["channels"]["details"]["items"][0]["capacity"] = quantity(8, "count")
        groups["resources"]["details"]["capacities"][0]["unit"] = "Hz"
        self.assertTrue(self.check())

    def test_independent_task_and_channel_contracts(self):
        groups = self.manifest["execution_design"]["data"]["groups"]
        units = groups["units"]["details"]["items"]
        units.append(copy.deepcopy(units[0]) | {"id": "task2"})
        schedules = groups["scheduling"]["details"]["items"]
        schedules.append(
            copy.deepcopy(schedules[0])
            | {"unit_ref": "task2", "deadline": quantity(10)}
        )
        channels = groups["channels"]["details"]["items"]
        channels.append(
            copy.deepcopy(channels[0])
            | {"id": "q2", "capacity": quantity(32, "count"), "receivers": ["task2"]}
        )
        self.assertEqual([], self.check())
        files = source_documents(self.manifest)
        for path, text in files.items():
            (self.root / path).write_text(text, encoding="utf-8")
        self.assertEqual(self.manifest, generate_manifest(self.root)[0])
        channels[1]["id"] = "q1"
        self.assertTrue(self.check())
        channels[1]["id"] = "q2"
        schedules[1]["unit_ref"] = "missing"
        self.assertTrue(self.check())

    def test_bare_metal_without_applicable_os_rules_does_not_require_fake_os_data(self):
        self.assertEqual(
            [], validate_os_designs({"modules": [], "flows": []}, "development")
        )

    def test_seven_rules_and_four_column_contract(self):
        selected = catalog()
        self.assertEqual(2, selected["version"])
        self.assertEqual(7, len([i for i in selected["ids"] if i.startswith("OS-")]))


if __name__ == "__main__":
    unittest.main()
