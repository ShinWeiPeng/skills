from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from architecture_cli import run_gate
from governance_adoption import (
    apply_baseline,
    compare_adoption_documents,
    render_adoption_documents,
    validate_adoption,
    write_adoption_documents,
)
from python_analyzer import analyze_python
from test_architecture import valid_manifest


def adoption() -> dict:
    return {
        "schema_version": "2.1.0",
        "project_stage": "existing",
        "applicable_analyzers": ["python"],
        "runtime_validation": {
            "applicability": "not-applicable",
            "rationale": "The governed project is host-side static tooling without target runtime claims.",
        },
        "tool_host_evidence": {
            "operating_systems": ["windows", "linux"],
            "python_versions": ["3.11", "3.12", "3.13"],
        },
    }


class GovernanceCliTests(unittest.TestCase):
    def test_schema_requires_composition_root_and_assurance_scope(self) -> None:
        from check_architecture import validate_manifest

        manifest = valid_manifest()
        manifest["composition_roots"] = []
        manifest["execution_profiles"][0].pop("assurance_scope")
        diagnostics = validate_manifest(
            manifest, Path("architecture/manifest.yaml"), check_docs=False
        )
        rules = {item.rule_id for item in diagnostics}
        self.assertIn("CMP001", rules)
        self.assertIn("EXE027", rules)

    def test_single_cli_design_gate_and_legacy_commands(self) -> None:
        manifest = valid_manifest()
        manifest["composition_roots"] = [
            {
                "id": "release-cli",
                "module": "app",
                "path": "src/app/app.c",
                "symbol": "app_init",
                "purpose": "Compose the release application.",
                "source_set": "formal-program",
                "kind": "release",
            }
        ]
        manifest["execution_profiles"][0]["assurance_scope"] = [
            "functional-compatibility"
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            architecture = root / "architecture"
            architecture.mkdir()
            manifest_path = architecture / "manifest.yaml"
            manifest_path.write_text(
                yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
            )
            code, evidence = run_gate(
                phase="design",
                manifest_path=manifest_path,
                adoption_path=None,
                baseline_path=None,
                previous_baseline_path=None,
            )
            self.assertEqual(0, code, evidence)
            for legacy in (
                "check_architecture.py",
                "render_architecture.py",
                "c_analyzer.py",
                "bootstrap_project.py",
            ):
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / legacy), "--help"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(0, result.returncode, legacy)
                self.assertIn("architecture_cli.py", result.stderr)

    def test_baseline_requires_human_approval_and_release_zero(self) -> None:
        diagnostics = [
            {
                "rule_id": "PYTYPE001",
                "severity": "MUST",
                "location": "src/example.py:Thing",
                "message": "uncataloged production type",
                "configuration": False,
                "disposition": "active",
            }
        ]
        approved = {
            "schema_version": "2.1.0",
            "violations": [
                {
                    "rule_id": "PYTYPE001",
                    "location": "src/example.py:Thing",
                    "rationale": "Owner approved a bounded migration.",
                    "approved_by": "Repository owner",
                    "approval_date": "2026-07-31",
                    "approval_reference": "review-42",
                    "captured_revision": "abc123",
                    "review_by": "2026-08-31",
                    "removal_condition": "Catalog Thing and verify Python AST.",
                }
            ],
        }
        development = copy.deepcopy(diagnostics)
        baseline_diagnostics = apply_baseline(
            development,
            approved,
            None,
            phase="development",
            expected_schema_version="2.1.0",
        )
        self.assertEqual([], baseline_diagnostics)
        self.assertEqual("baseline", development[0]["disposition"])

        release = copy.deepcopy(diagnostics)
        release_diagnostics = apply_baseline(
            release,
            approved,
            None,
            phase="release",
            expected_schema_version="2.1.0",
        )
        self.assertTrue(
            any(item["rule_id"] == "BAS006" for item in release_diagnostics)
        )
        self.assertEqual("active", release[0]["disposition"])

        unapproved = copy.deepcopy(approved)
        unapproved["violations"][0]["approved_by"] = "Codex"
        invalid = apply_baseline(
            copy.deepcopy(diagnostics),
            unapproved,
            None,
            phase="development",
            expected_schema_version="2.1.0",
        )
        self.assertTrue(any(item["rule_id"] == "BAS003" for item in invalid))

        stale = apply_baseline(
            [],
            approved,
            None,
            phase="development",
            expected_schema_version="2.1.0",
        )
        self.assertTrue(any(item["rule_id"] == "BAS005" for item in stale))

        growth = apply_baseline(
            copy.deepcopy(diagnostics),
            approved,
            {"schema_version": "2.1.0", "violations": []},
            phase="development",
            expected_schema_version="2.1.0",
        )
        self.assertTrue(any(item["rule_id"] == "BAS004" for item in growth))

    def test_adoption_contract_separates_tool_host_from_execution_target(self) -> None:
        manifest = valid_manifest()
        manifest["composition_roots"] = []
        diagnostics = validate_adoption(manifest, adoption())
        rules = {item["rule_id"] for item in diagnostics}
        self.assertIn("CMP001", rules)
        self.assertNotIn("EXE_HOST001", rules)

        invalid = adoption()
        invalid["runtime_validation"] = {"applicability": "not-applicable"}
        diagnostics = validate_adoption(valid_manifest(), invalid)
        self.assertTrue(
            any(item["rule_id"] == "VAL001" for item in diagnostics)
        )
        performance_manifest = valid_manifest()
        performance_manifest["execution_profiles"][0]["assurance_scope"] = [
            "performance"
        ]
        diagnostics = validate_adoption(performance_manifest, adoption())
        self.assertTrue(any(item["rule_id"] == "VAL002" for item in diagnostics))

    def test_python_analyzer_catalogs_types_state_symbols_and_composition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src"
            source.mkdir()
            (source / "app.py").write_text(
                "class Request:\n"
                "    pass\n\n"
                "runtime_cache = {}\n\n"
                "def compose() -> None:\n"
                "    pass\n",
                encoding="utf-8",
            )
            manifest = {
                "source_sets": [
                    {
                        "id": "formal",
                        "classification": "production",
                        "include": ["src/**"],
                        "exclude": [],
                    }
                ],
                "modules": [
                    {
                        "id": "app",
                        "level": "L0",
                        "role": "composition",
                        "paths": ["src/app.py"],
                        "depends_on": [],
                        "entrypoints": [
                            {
                                "path": "src/app.py",
                                "symbol": "compose",
                                "kind": "function",
                            }
                        ],
                        "public_symbols": [],
                    }
                ],
                "composition_roots": [
                    {
                        "id": "release",
                        "module": "app",
                        "path": "src/app.py",
                        "symbol": "compose",
                        "purpose": "Compose the app.",
                        "source_set": "formal",
                        "kind": "release",
                    }
                ],
                "types": [],
                "state_objects": [],
                "python_analyzer": {
                    "status": "required",
                    "rationale": "Production Python requires AST evidence.",
                },
            }
            diagnostics, evidence = analyze_python(manifest, root)
            rules = {item["rule_id"] for item in diagnostics}
            self.assertEqual("python-ast", evidence["mode"])
            self.assertIn("PYTYPE001", rules)
            self.assertIn("PYSTATE001", rules)

            manifest["types"] = [
                {
                    "id": "request",
                    "owner": "app",
                    "language": "python",
                    "declaration": {
                        "path": "src/app.py",
                        "symbol": "Request",
                        "kind": "class",
                    },
                }
            ]
            manifest["state_objects"] = [
                {
                    "id": "runtime-cache",
                    "owner": "app",
                    "language": "python",
                    "declaration": {
                        "path": "src/app.py",
                        "symbol": "runtime_cache",
                        "storage": "file-static",
                    },
                }
            ]
            diagnostics, evidence = analyze_python(manifest, root)
            self.assertEqual([], diagnostics)
            self.assertEqual(["src/app.py"], evidence["analyzed_files"])

    def test_unsupported_production_code_language_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src"
            source.mkdir()
            (source / "main.js").write_text("export function compose() {}\n", encoding="utf-8")
            manifest = {
                "source_sets": [
                    {
                        "id": "formal",
                        "classification": "production",
                        "include": ["src/**"],
                        "exclude": [],
                    }
                ],
                "modules": [
                    {
                        "id": "app",
                        "level": "L0",
                        "role": "composition",
                        "paths": ["src"],
                        "depends_on": [],
                        "entrypoints": [],
                        "public_symbols": [],
                    }
                ],
                "composition_roots": [],
                "types": [],
                "state_objects": [],
                "python_analyzer": {
                    "status": "not-applicable",
                    "rationale": "No Python.",
                },
            }
            diagnostics, evidence = analyze_python(manifest, root)
            self.assertEqual("not-run", evidence["mode"])
            self.assertTrue(
                any(item["rule_id"] == "SRCAN001" for item in diagnostics)
            )

    def test_adoption_markdown_and_json_are_deterministic_and_stale_checked(self) -> None:
        manifest = valid_manifest()
        evidence = {
            "phase": "development",
            "gate_result": "PASS",
            "readiness_status": "VERIFIED",
            "exit_code": 0,
            "analyzers": {
                "python": {
                    "mode": "python-ast",
                    "analyzed_files": ["src/app.py"],
                    "type_count": 1,
                    "state_count": 0,
                }
            },
            "diagnostics": [],
        }
        expected = render_adoption_documents(
            manifest, adoption(), {"schema_version": "2.1.0", "violations": []}, evidence
        )
        self.assertIn(Path("generated/adoption-readiness.md"), expected)
        self.assertIn(Path("generated/adoption-readiness.json"), expected)
        self.assertIn("VERIFIED", expected[Path("generated/adoption-readiness.md")])
        self.assertEqual(
            expected,
            render_adoption_documents(
                copy.deepcopy(manifest),
                copy.deepcopy(adoption()),
                {"schema_version": "2.1.0", "violations": []},
                copy.deepcopy(evidence),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            architecture = Path(directory) / "architecture"
            architecture.mkdir()
            manifest_path = architecture / "manifest.yaml"
            write_adoption_documents(
                manifest_path, manifest, adoption(), {"violations": []}, evidence
            )
            self.assertEqual(
                [],
                compare_adoption_documents(
                    manifest_path, manifest, adoption(), {"violations": []}, evidence
                ),
            )
            report = architecture / "generated" / "adoption-readiness.md"
            report.write_text(report.read_text(encoding="utf-8") + "manual\n", encoding="utf-8")
            self.assertTrue(
                any(
                    item["rule_id"] == "DOC002"
                    for item in compare_adoption_documents(
                        manifest_path,
                        manifest,
                        adoption(),
                        {"violations": []},
                        evidence,
                    )
                )
            )
            obsolete = architecture / "generated" / "adoption-readiness-old.json"
            obsolete.write_text(
                json.dumps({"_generated": "GENERATED BY govern-modular-event-architecture; DO NOT EDIT"}),
                encoding="utf-8",
            )
            self.assertTrue(
                any(
                    item["rule_id"] == "DOC003"
                    for item in compare_adoption_documents(
                        manifest_path,
                        manifest,
                        adoption(),
                        {"violations": []},
                        evidence,
                    )
                )
            )


if __name__ == "__main__":
    unittest.main()
