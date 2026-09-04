import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "verification_ladder.py"


def layer_contract(next_layers=None):
    return {
        "scope": "Bounded verification scope.",
        "inputs": ["confirmed project contract"],
        "metrics": ["contract verdict"],
        "thresholds": {
            "pass": "Every selected assertion passes.",
            "fail": "A complete observation violates an assertion.",
            "blocked": "Required evidence is incomplete.",
        },
        "evidence": "JSON result artifact",
        "stop_condition": "Stop at PASS, FAIL, or BLOCKED.",
        "next_layers": next_layers or [],
    }


def base_matrix():
    return {
        "schema_version": "1.0",
        "architecture_manifest": "architecture/manifest.yaml",
        "on_device_profile": "validation/on-device.yaml",
        "layers": {
            "module-contract": layer_contract(["sil", "adapter-contract", "pil"]),
            "sil": layer_contract(["pil", "hil"]),
            "adapter-contract": layer_contract(["hil"]),
            "pil": layer_contract(["hil"]),
            "hil": layer_contract(["system-soak"]),
            "system-soak": layer_contract(),
        },
        "rules": [
            {
                "id": "processing-semantics",
                "architecture_refs": ["processing"],
                "contract_dimensions": ["state-transition"],
                "execution_changes": [],
                "evidence_claims": ["host-semantics"],
                "layers": ["module-contract", "sil"],
                "on_device_scenarios": [],
                "execution_profiles": [],
            },
            {
                "id": "production-deadline",
                "architecture_refs": ["processing-flow", "target-a"],
                "contract_dimensions": ["latency-resource"],
                "execution_changes": ["core-mapping", "competing-workload"],
                "evidence_claims": ["production-timing"],
                "layers": ["pil", "hil"],
                "on_device_scenarios": ["pil-cost", "hil-timing"],
                "execution_profiles": ["target-a"],
            },
        ],
    }


class VerificationLadderCliTests(unittest.TestCase):
    def run_authority(self, claim, *passed_layers):
        completed = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "assess-evidence",
                "--claim",
                claim,
                *[
                    argument
                    for layer in passed_layers
                    for argument in ("--passed-layer", layer)
                ],
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        return completed, json.loads(completed.stdout)

    def run_cli(
        self,
        matrix,
        *arguments,
        architecture=None,
        on_device=None,
        include_on_device=True,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix_path = root / "validation" / "verification-ladder.yaml"
            architecture_path = root / "architecture" / "manifest.yaml"
            on_device_path = root / "validation" / "on-device.yaml"
            matrix_path.parent.mkdir(parents=True)
            architecture_path.parent.mkdir(parents=True)
            matrix_path.write_text(yaml.safe_dump(matrix), encoding="utf-8")
            architecture_path.write_text(
                yaml.safe_dump(
                    architecture
                    or {
                        "modules": [{"id": "processing"}],
                        "flows": [{"id": "processing-flow"}],
                        "execution_profiles": [{"id": "target-a"}],
                    }
                ),
                encoding="utf-8",
            )
            on_device_path.write_text(
                yaml.safe_dump(
                    on_device
                    or {
                        "version": "1.1",
                        "architecture": {"execution_profile": "target-a"},
                        "scenarios": [
                            {"id": "pil-cost"},
                            {"id": "hil-timing"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            command = [
                sys.executable,
                str(CLI),
                *arguments,
                "--matrix",
                str(matrix_path),
                "--architecture",
                str(architecture_path),
            ]
            if include_on_device:
                command.extend(("--on-device", str(on_device_path)))
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
            return completed, json.loads(completed.stdout)

    def test_plan_combines_project_rules_and_universal_authority(self):
        completed, result = self.run_cli(
            base_matrix(),
            "plan",
            "--contract-dimension",
            "state-transition",
            "--evidence-claim",
            "production-timing",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(
            ["module-contract", "sil", "pil", "hil"],
            result["required_layers"],
        )
        self.assertEqual(
            ["processing-semantics", "production-deadline"],
            result["activated_rules"],
        )

    def test_production_timing_cannot_be_passed_by_pil(self):
        blocked, blocked_result = self.run_authority("production-timing", "pil")
        passed, passed_result = self.run_authority("production-timing", "hil")

        self.assertEqual(2, blocked.returncode)
        self.assertEqual("BLOCKED", blocked_result["status"])
        self.assertEqual("hil", blocked_result["required_authority"])
        self.assertEqual(0, passed.returncode, passed.stderr)
        self.assertEqual("PASS", passed_result["status"])

    def test_duplicate_architecture_identity_is_blocked(self):
        architecture = {
            "modules": [{"id": "processing"}],
            "flows": [{"id": "processing-flow"}],
            "execution_profiles": [{"id": "target-a"}, {"id": "target-a"}],
        }

        completed, result = self.run_cli(
            base_matrix(),
            "plan",
            "--evidence-claim",
            "production-timing",
            architecture=architecture,
        )

        self.assertEqual(2, completed.returncode)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("duplicate architecture id 'target-a'", result["errors"])

    def test_host_only_project_does_not_require_device_profile(self):
        matrix = base_matrix()
        matrix.pop("on_device_profile")
        matrix["rules"] = [matrix["rules"][0]]

        completed, result = self.run_cli(
            matrix,
            "plan",
            "--contract-dimension",
            "state-transition",
            include_on_device=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(["module-contract", "sil"], result["required_layers"])

    def test_declared_on_device_profile_must_match_the_supplied_profile(self):
        matrix = base_matrix()
        matrix["on_device_profile"] = "validation/different-device.yaml"

        completed, result = self.run_cli(
            matrix,
            "plan",
            "--evidence-claim",
            "production-timing",
        )

        self.assertEqual(2, completed.returncode)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn(
            "on_device_profile does not resolve to the supplied profile",
            result["errors"],
        )

    def test_validate_reports_resolved_contract_without_selecting_layers(self):
        completed, result = self.run_cli(base_matrix(), "validate")

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(2, result["rule_count"])
        self.assertEqual(6, result["layer_contract_count"])

    def test_unknown_matrix_field_is_blocked(self):
        matrix = base_matrix()
        matrix["platform"] = "esp32"

        completed, result = self.run_cli(matrix, "validate")

        self.assertEqual(2, completed.returncode)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("unknown matrix field 'platform'", result["errors"])

    def test_unknown_nested_fields_and_invalid_na_are_blocked(self):
        matrix = base_matrix()
        matrix["layers"]["sil"]["platform"] = "host"
        matrix["rules"][0]["priority"] = "high"
        matrix["not_applicable"] = [
            {"layer": "pil", "rationale": "No target claim.", "owner": "team"},
            {"layer": "pil", "rationale": "Duplicate declaration."},
        ]

        completed, result = self.run_cli(matrix, "validate")

        self.assertEqual(2, completed.returncode)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("unknown layers.sil field 'platform'", result["errors"])
        self.assertIn("unknown rules[0] field 'priority'", result["errors"])
        self.assertIn("unknown not_applicable[0] field 'owner'", result["errors"])
        self.assertIn("duplicate not_applicable layer 'pil'", result["errors"])

    def test_duplicate_on_device_ids_are_blocked(self):
        profile = {
            "version": "1.1",
            "architecture": {"execution_profile": "target-a"},
            "scenarios": [
                {"id": "pil-cost"},
                {"id": "pil-cost"},
                {"id": "hil-timing"},
            ],
        }

        completed, result = self.run_cli(base_matrix(), "validate", on_device=profile)

        self.assertEqual(2, completed.returncode)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("duplicate on-device scenario id 'pil-cost'", result["errors"])

    def test_stale_reference_and_unmapped_claim_are_blocked(self):
        stale = base_matrix()
        stale["rules"][0]["architecture_refs"] = ["renamed-processing"]
        stale_run, stale_result = self.run_cli(stale, "validate")
        unmapped_run, unmapped_result = self.run_cli(
            base_matrix(), "plan", "--evidence-claim", "system-stability"
        )

        self.assertEqual(2, stale_run.returncode)
        self.assertTrue(
            any(
                "unresolved id 'renamed-processing'" in error
                for error in stale_result["errors"]
            )
        )
        self.assertEqual(2, unmapped_run.returncode)
        self.assertIn(
            "trigger 'system-stability' is not mapped by any project rule",
            unmapped_result["errors"],
        )

    def test_taxonomy_is_portable_across_project_platform_bindings(self):
        matrix = base_matrix()
        matrix["rules"][1]["architecture_refs"] = ["processing-flow", "linux-rt"]
        matrix["rules"][1]["execution_profiles"] = ["linux-rt"]
        matrix["rules"][1]["on_device_scenarios"] = ["linux-cost", "linux-hil"]
        architecture = {
            "modules": [{"id": "processing"}],
            "flows": [{"id": "processing-flow"}],
            "execution_profiles": [{"id": "linux-rt"}],
        }
        on_device = {
            "version": "1.1",
            "architecture": {"execution_profile": "linux-rt"},
            "scenarios": [{"id": "linux-cost"}, {"id": "linux-hil"}],
        }

        completed, result = self.run_cli(
            matrix,
            "plan",
            "--evidence-claim",
            "production-timing",
            architecture=architecture,
            on_device=on_device,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(["pil", "hil"], result["required_layers"])


class VerificationLadderSkillContractTests(unittest.TestCase):
    def test_skill_preserves_layer_ownership_and_production_code_sil(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        normalized = text.casefold()
        for required in (
            "Run the production functional implementation on the host",
            "A simplified duplicate Processing model is not SIL",
            "same suite",
            "PIL cannot alone pass production latency or deadline claims",
            "invoke `$validate-on-device`",
            "never assume ESP32",
            "do not force the complete ladder",
        ):
            self.assertIn(required.casefold(), normalized)

    def test_schema_is_machine_readable_and_declares_project_owned_fields(self):
        schema = json.loads(
            (ROOT / "references" / "verification-ladder.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("1.0", schema["properties"]["schema_version"]["const"])
        self.assertIn("architecture_manifest", schema["required"])
        self.assertIn("not_applicable", schema["properties"])


if __name__ == "__main__":
    unittest.main()
