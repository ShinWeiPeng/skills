import json
import sys
import subprocess
import hashlib
import tempfile
import unittest
from pathlib import Path

from test_project_validation import (
    fixture,
    save_plan,
    write,
    publish_evidence,
    validation,
    TEST_TEMP_ROOT,
)
from test_verification_ladder import base_matrix
from verification_ladder import plan, assess_evidence


class ModuleSilTests(unittest.TestCase):
    def test_host_module_semantics_select_sil_when_project_rule_omits_it(self):
        matrix = base_matrix()
        matrix["rules"][0]["layers"] = ["module-contract"]
        result = plan(
            matrix,
            {
                "contract_dimensions": set(),
                "execution_changes": set(),
                "evidence_claims": {"host-semantics"},
            },
        )
        self.assertEqual(["module-contract", "sil"], result["required_layers"])
        self.assertEqual("NOT_RUN", result["execution_status"])
        self.assertTrue(
            any("harness" in gap for gap in result["execution_requirements"])
        )

    def test_host_module_semantics_cannot_exclude_sil_as_no_separate_integration(self):
        matrix = base_matrix()
        matrix["not_applicable"] = [
            {"layer": "sil", "rationale": "No separate simulated integration claim."}
        ]
        result = plan(
            matrix,
            {
                "contract_dimensions": set(),
                "execution_changes": set(),
                "evidence_claims": {"host-semantics"},
            },
        )
        self.assertEqual("BLOCKED", result["status"])

    def test_module_contract_label_alone_does_not_prove_sil_execution(self):
        self.assertEqual(
            "BLOCKED", assess_evidence("host-semantics", {"module-contract"})["status"]
        )

    def test_acceptance_rejects_sil_without_executed_public_module_report(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            write(
                root,
                "validation/acceptance-SPEC-0001.json",
                {
                    "schema_version": 1,
                    "spec_id": "SPEC-0001",
                    "acceptance": {
                        "AC-001": {
                            "evidence_claims": ["host-semantics"],
                            "rationale": "Formal production module on the host.",
                        }
                    },
                },
            )
            planned = save_plan(root)
            log = "tests/modules/processing/support/host.txt"
            write(root, log, "PASS")
            import hashlib

            artifact = {
                "path": log,
                "sha256": hashlib.sha256((root / log).read_bytes()).hexdigest(),
            }
            bundle = {
                "schema_version": 1,
                "plan_sha256": planned["plan_sha256"],
                "results": [
                    {
                        "ac": "AC-001",
                        "layer": layer,
                        "scenario": None,
                        "purpose": "acceptance",
                        "verdict": "PASS",
                        "complete": True,
                        "artifacts": [dict(artifact)],
                    }
                    for layer in ("module-contract", "sil")
                ],
            }
            publish_evidence(root, bundle)
            result = validation.assess_project(
                root, "specs/SPEC-0001-sensor.md", phase="acceptance"
            )
            self.assertEqual("BLOCKED", result["verdict"])
            self.assertTrue(any("SIL" in error for error in result["errors"]), result)

    def test_executed_module_report_and_stale_or_incomplete_evidence(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            write(
                root,
                "validation/acceptance-SPEC-0001.json",
                {
                    "schema_version": 1,
                    "spec_id": "SPEC-0001",
                    "acceptance": {
                        "AC-001": {
                            "evidence_claims": ["host-semantics"],
                            "rationale": "Formal production module on host.",
                        }
                    },
                },
            )
            production_path = "src/verification_ladder.py"
            write(
                root,
                "architecture/manifest.yaml",
                {
                    "modules": [{"id": "processing", "paths": [production_path]}],
                    "flows": [{"id": "processing-flow"}],
                    "execution_profiles": [{"id": "target-a"}],
                },
            )
            layout = json.loads((root / "validation/layout.yaml").read_text())
            layout["entries"].append(
                {
                    "include": ["src/**"],
                    "role": "development-tool",
                    "provenance": "Production module fixture for public execution evidence.",
                }
            )
            write(root, "validation/layout.yaml", layout)
            production = (
                Path(validation.__file__)
                .with_name("verification_ladder.py")
                .read_bytes()
            )
            (root / production_path).parent.mkdir(parents=True, exist_ok=True)
            (root / production_path).write_bytes(production)
            planned = save_plan(root)
            command = [
                sys.executable,
                str(root / production_path),
                "assess-evidence",
                "--claim",
                "host-semantics",
                "--passed-layer",
                "sil",
            ]
            run = subprocess.run(
                command, capture_output=True, text=True, encoding="utf-8", timeout=30
            )
            self.assertEqual(0, run.returncode, run.stderr)
            self.assertEqual("PASS", json.loads(run.stdout)["status"])
            log = "tests/modules/processing/support/host.txt"
            report_path = "tests/modules/processing/support/sil.json"
            write(root, log, run.stdout + run.stderr)
            module = {
                "id": "processing",
                "public_interfaces": ["assess_evidence"],
                "cases": ["host-semantics with executed SIL"],
                "production_sources": [
                    {
                        "path": production_path,
                        "sha256": hashlib.sha256(production).hexdigest(),
                    }
                ],
                "external_dependencies": [],
            }
            report = {
                "layer": "sil",
                "ac": "AC-001",
                "plan_sha256": planned["plan_sha256"],
                "verdict": "PASS",
                "complete": True,
                "command": command,
                "exit_code": run.returncode,
                "modules": [module],
            }

            def assess(report):
                write(root, report_path, report)
                artifacts = [
                    {
                        "path": path,
                        "sha256": hashlib.sha256(
                            (root / path).read_bytes()
                        ).hexdigest(),
                    }
                    for path in (log, report_path)
                ]
                rows = [
                    {
                        "ac": "AC-001",
                        "layer": layer,
                        "scenario": None,
                        "purpose": "acceptance",
                        "verdict": "PASS",
                        "complete": True,
                        "artifacts": [dict(a) for a in artifacts],
                        **({"runner_result": report_path} if layer == "sil" else {}),
                    }
                    for layer in ("module-contract", "sil")
                ]
                publish_evidence(
                    root,
                    {
                        "schema_version": 1,
                        "plan_sha256": planned["plan_sha256"],
                        "results": rows,
                    },
                )
                return validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                )

            self.assertEqual("PASS", assess(report)["verdict"])
            for field, value in (
                ("public_interfaces", []),
                ("public_interfaces", [" "]),
                ("cases", [" "]),
                ("cases", []),
                ("id", "unmapped"),
                ("production_sources", []),
            ):
                with self.subTest(field=field):
                    broken = json.loads(json.dumps(report))
                    broken["modules"][0][field] = value
                    result = assess(broken)
                    self.assertEqual("BLOCKED", result["verdict"], result)
            for path in ("tests/modules/processing/support/model.py", "src/other.py"):
                with self.subTest(source=path):
                    write(root, path, production.decode())
                    broken = json.loads(json.dumps(report))
                    broken["modules"][0]["production_sources"][0]["path"] = path
                    result = assess(broken)
                    self.assertEqual("BLOCKED", result["verdict"], result)
                    self.assertTrue(
                        any("owned" in error for error in result["errors"]), result
                    )
            broken = dict(report, exit_code=1)
            self.assertEqual("BLOCKED", assess(broken)["verdict"])
            (root / production_path).write_bytes(production + b"\n# changed source\n")
            result = assess(report)
            self.assertEqual("BLOCKED", result["verdict"], result)
            self.assertTrue(any("stale" in error for error in result["errors"]), result)
