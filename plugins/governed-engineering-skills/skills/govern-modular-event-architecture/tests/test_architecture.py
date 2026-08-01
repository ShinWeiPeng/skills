from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from bootstrap_project import bootstrap
from ast_analyzer import _parse_arguments
from c_analyzer import _discover_named_types, analyze
from check_architecture import exit_code, validate_manifest
from fanout_reference import publish_all
from render_architecture import compare_documents, render_documents


def module(
    module_id: str,
    level: str,
    role: str,
    path: str,
    parent: str | None,
    depends_on: list[str],
) -> dict:
    symbol = f"{module_id}_port"
    return {
        "id": module_id,
        "level": level,
        "role": role,
        "implementation_status": "planned",
        "paths": [path],
        "parent": parent,
        "depends_on": depends_on,
        "implements_ports": [],
        "public_headers": [f"{path}/*.h"],
        "description": {
            "purpose": f"Provide the {module_id} responsibility.",
            "input_ports": [],
            "output_ports": [],
            "emitted_events": [],
            "owned_state": [],
            "side_effects": [],
            "errors": [],
            "invariants": [],
        },
        "entrypoints": [
            {
                "path": f"{path}/{module_id}.c",
                "symbol": f"{module_id}_init",
                "kind": "initializer",
            }
        ],
        "public_symbols": [
            {
                "path": f"{path}/{module_id}.h",
                "symbol": symbol,
                "kind": "port",
            }
        ],
    }


def valid_manifest(*, c_ast: bool = False) -> dict:
    app = module("app", "L0", "composition", "src/app", None, ["feature", "adapter"])
    feature = module("feature", "L1", "domain", "src/feature", "app", [])
    adapter = module("adapter", "L3+", "adapter", "src/adapter", None, ["feature"])
    adapter["implements_ports"] = ["feature.io"]
    feature["description"]["input_ports"] = ["feature.command"]
    feature["description"]["output_ports"] = ["feature.io"]
    feature["description"]["emitted_events"] = ["feature.completed"]
    manifest = {
        "standard_version": "2.1.0",
        "schema_version": "2.1.0",
        "project": {"name": "fixture", "documentation_language": "en"},
        "modules": [app, feature, adapter],
        "composition_roots": [
            {
                "id": "fixture-release",
                "module": "app",
                "path": "src/app/app.c",
                "symbol": "app_init",
                "purpose": "Compose the fixture release application.",
                "source_set": "formal-program",
                "kind": "release",
            }
        ],
        "source_sets": [
            {
                "id": "formal-program",
                "classification": "production",
                "include": ["src/**"],
                "exclude": ["src/generated/**"],
                "purpose": "Govern maintained product sources.",
                "provenance": "Human-maintained project source.",
            },
            {
                "id": "generated-adapter",
                "classification": "generated-production",
                "include": ["src/generated/**"],
                "exclude": [],
                "purpose": "Compile generator-owned adapter sources without catalog migration.",
                "provenance": "Fixture generator output.",
                "generator": "fixture-generator",
                "owner": "adapter",
            },
            {
                "id": "development",
                "classification": "development",
                "include": ["tests/**", ".codex/**"],
                "exclude": [],
                "purpose": "Keep development and GPT evidence outside formal sources.",
                "provenance": "Developer and GPT tooling.",
            },
            {
                "id": "derived-docs",
                "classification": "derived-documentation",
                "include": ["architecture/generated/**"],
                "exclude": [],
                "purpose": "Keep deterministic description views outside formal sources.",
                "provenance": "Architecture renderer.",
            },
            {
                "id": "build-output",
                "classification": "build-output",
                "include": ["build/**", "Debug/**", "Release/**"],
                "exclude": [],
                "purpose": "Exclude compiler and linker outputs.",
                "provenance": "Build toolchain.",
            },
        ],
        "ports": [
            {
                "id": "feature.command",
                "owner": "feature",
                "direction": "input",
                "kind": "command",
                "contract": "src/feature/feature.h",
                "implemented_by": [],
                "description": {
                    "purpose": "Submit one feature command.",
                    "data": "Typed command data.",
                    "timing": "sync",
                    "immediate_rejections": [],
                },
                "symbols": ["feature_port"],
            },
            {
                "id": "feature.io",
                "owner": "feature",
                "direction": "output",
                "kind": "dependency",
                "contract": "src/feature/feature.h",
                "implemented_by": ["adapter"],
                "description": {
                    "purpose": "Access external I/O through a demand-owned contract.",
                    "data": "Logical input and output values.",
                    "timing": "sync",
                    "immediate_rejections": [],
                },
                "symbols": ["feature_port"],
            },
            {
                "id": "feature.events",
                "owner": "feature",
                "direction": "output",
                "kind": "event",
                "contract": "src/feature/feature.h",
                "implemented_by": [],
                "description": {
                    "purpose": "Publish completed feature work.",
                    "data": "Feature completion payload.",
                    "timing": "async",
                    "immediate_rejections": [],
                },
                "symbols": ["feature_port"],
            },
        ],
        "events": [
            {
                "id": "feature.completed",
                "owner": "feature",
                "output_port": "feature.events",
                "delivery": "at-most-once",
                "envelope": [
                    "event_type",
                    "source",
                    "correlation_id",
                    "stream_id",
                    "sequence",
                    "payload",
                ],
                "lifecycle": [
                    "received",
                    "validated",
                    "processing",
                    "succeeded",
                    "failed",
                ],
                "description": {
                    "purpose": "Report successful feature completion.",
                    "emitted_when": "State has committed.",
                    "payload_fields": [
                        {"name": "value", "type": "integer", "meaning": "Fixture value."}
                    ],
                    "intended_consumers": ["app"],
                },
            }
        ],
        "types": [],
        "type_exclusions": [],
        "state_objects": [],
        "boundary_mappings": [],
        "flows": [
            {
                "id": "feature-flow",
                "owner": "feature",
                "description": "Process one feature command.",
                "trigger": {
                    "kind": "command",
                    "ref": "feature.command",
                    "description": "A caller submits a command.",
                },
                "steps": [
                    {
                        "id": "feature-flow.step-1",
                        "order": 1,
                        "module": "feature",
                        "action": "Validate and process the command.",
                        "receives": ["feature.command"],
                        "emits": ["feature.completed"],
                        "state_changes": [],
                        "side_effects": [],
                    }
                ],
                "success": {
                    "result": "The feature reports completion.",
                    "events": ["feature.completed"],
                },
                "errors": [],
            }
        ],
        "adr_exceptions": [],
        "c_analyzer": {
            "ast": {
                "status": "required" if c_ast else "not-applicable",
                "rationale": (
                    "C fixture requires complete AST enforcement."
                    if c_ast
                    else "This planned manifest has no governed C translation units."
                ),
                **(
                    {
                        "compilation_database": "compile_commands.json",
                        "target_triple": "native",
                    }
                    if c_ast
                    else {}
                ),
            },
            "functional_boundary": {
                "status": "configured",
                "rationale": "The fixture has an L3+ adapter.",
                "forbidden_includes": ["stm32f10x.h"],
                "forbidden_symbols": ["GPIO_SetBits"],
            },
            "forbidden_public_includes": ["stm32f10x.h"],
            "forbidden_public_symbols": ["GPIO_TypeDef"],
            "forbidden_source_symbols": [],
        },
        "python_analyzer": {
            "status": "not-applicable",
            "rationale": "The fixture contains governed C source only.",
        },
        "workloads": [
            {
                "id": "feature-workload",
                "flow": "feature-flow",
                "steps": ["feature-flow.step-1"],
                "timing_class": "best-effort",
                "activation": {"kind": "command"},
                "data": {"volume": "one command"},
                "budgets": [],
            }
        ],
        "execution_profiles": [
            {
                "id": "fixture-profile",
                "status": "legacy-review",
                "assurance_scope": ["functional-compatibility"],
                "target": {
                    "platform": "test",
                    "cpu": "test",
                    "runtime": "native",
                    "compiler": "test",
                    "cache_topology": {},
                    "scheduler_capabilities": [],
                },
            }
        ],
        "execution_units": [
            {
                "id": "fixture-process",
                "profile": "fixture-profile",
                "kind": "process",
                "priority": "default",
                "affinity": [],
                "concurrency": 1,
                "resources": {"memory": "bounded"},
                "blocking": "none",
                "allocation": "static",
            }
        ],
        "execution_mappings": [
            {
                "id": "fixture-map",
                "profile": "fixture-profile",
                "workload": "feature-workload",
                "steps": ["feature-flow.step-1"],
                "units": ["fixture-process"],
                "serialization": "one invocation",
                "reentrant": False,
                "activation": "command",
                "wcet": "not established",
            }
        ],
        "execution_channels": [],
        "data_access_profiles": [],
        "microarchitecture_profiles": [],
        "platform_variants": [
            {
                "id": "fixture-variant",
                "profile": "fixture-profile",
                "units": ["fixture-process"],
                "data_access_profiles": [],
                "microarchitecture_profiles": [],
                "parameters": {},
                "release": False,
            }
        ],
        "realtime_scheduling_studies": [],
        "validation_profiles": [
            {
                "id": "fixture-host-validation",
                "applicability": "not-applicable",
                "rationale": "The fixture has no runtime acceptance claim.",
            }
        ],
    }
    return manifest


def realtime_design_manifest() -> dict:
    manifest = valid_manifest()
    manifest["project"]["documentation_language"] = "zh-TW"
    manifest["workloads"][0].update(
        {
            "timing_class": "hard-real-time",
            "activation": {"kind": "periodic", "period_ns": 10_000_000},
            "budgets": [
                {
                    "metric": "deadline",
                    "operator": "<=",
                    "threshold": 10_000_000,
                    "unit": "ns",
                    "method": "RTA",
                },
                {
                    "metric": "deadline-miss-count",
                    "operator": "==",
                    "threshold": 0,
                    "unit": "count",
                    "method": "runtime-evidence",
                },
            ],
            "tier1_analysis": {
                "working_set": "Bounded fixture state.",
                "memory_traffic": "Bounded fixture transfers.",
                "branch_predictability": "Deterministic fixture paths.",
                "simd_dependencies": "None.",
                "parallelism": "Partitioned tasks.",
                "blocking_bounds": "Priority-ceiling bound.",
            },
        }
    )

    def candidate(profile_id: str) -> dict:
        return {
            "id": profile_id,
            "status": "proposed",
            "assurance_scope": ["functional-compatibility", "real-time"],
            "execution_model": "bare-metal",
            "analysis_phase": "provisional",
            "target": {
                "platform": "fixture-board",
                "cpu": "fixture-cpu",
                "runtime": "fixture-rtos",
                "compiler": "fixture-compiler",
                "cache_topology": {"kind": "fixture"},
                "scheduler_capabilities": ["fixed-priority", "core-affinity"],
            },
            "scheduler": {
                "model": "partitioned-fixed-priority",
                "priority_assignment": "rate-monotonic",
                "preemption": "fully-preemptive",
                "migration": "forbidden",
                "core_count": 2,
                "priority_higher_value_wins": True,
                "timer_resolution_ns": 1_000,
                "resource_access_protocol": "priority-ceiling",
            },
            "overheads": {
                "context_switch_ns": 10_000,
                "dispatch_ns": 5_000,
                "preemption_ns": 10_000,
                "timer_interrupt_ns": 5_000,
            },
        }

    def unit(
        unit_id: str,
        profile_id: str,
        mapping_id: str,
        *,
        core: int,
        period_ns: int,
        budget_ns: int,
        priority: int,
    ) -> dict:
        return {
            "id": unit_id,
            "profile": profile_id,
            "kind": "dedicated-task",
            "priority": priority,
            "affinity": [core],
            "concurrency": 1,
            "resources": {"stack": "bounded"},
            "blocking": "priority-ceiling",
            "allocation": "static",
            "realtime_task": {
                "core": core,
                "activation": {"kind": "periodic", "period_ns": period_ns},
                "relative_deadline_ns": period_ns,
                "release_jitter_ns": 0,
                "blocking_ns": 0,
                "demand_components": [
                    {"mapping": mapping_id, "budget_ns": budget_ns}
                ],
            },
        }

    def mapping(
        mapping_id: str, profile_id: str, unit_id: str, wcet: str
    ) -> dict:
        return {
            "id": mapping_id,
            "profile": profile_id,
            "workload": "feature-workload",
            "steps": ["feature-flow.step-1"],
            "units": [unit_id],
            "serialization": "one job",
            "reentrant": False,
            "activation": "periodic",
            "wcet": wcet,
        }

    manifest["execution_profiles"] = [candidate("candidate-a"), candidate("candidate-b")]
    manifest["execution_units"] = [
        unit(
            "candidate-a-task",
            "candidate-a",
            "candidate-a-map",
            core=0,
            period_ns=10_000_000,
            budget_ns=1_000_000,
            priority=1,
        ),
        unit(
            "candidate-b-fast",
            "candidate-b",
            "candidate-b-fast-map",
            core=0,
            period_ns=5_000_000,
            budget_ns=400_000,
            priority=1,
        ),
        unit(
            "candidate-b-slow",
            "candidate-b",
            "candidate-b-slow-map",
            core=1,
            period_ns=10_000_000,
            budget_ns=500_000,
            priority=1,
        ),
    ]
    manifest["execution_mappings"] = [
        mapping("candidate-a-map", "candidate-a", "candidate-a-task", "1 ms"),
        mapping("candidate-b-fast-map", "candidate-b", "candidate-b-fast", "0.4 ms"),
        mapping("candidate-b-slow-map", "candidate-b", "candidate-b-slow", "0.5 ms"),
    ]
    manifest["execution_channels"] = [
        {
            "id": "candidate-b-handoff",
            "profile": "candidate-b",
            "from_unit": "candidate-b-fast",
            "to_unit": "candidate-b-slow",
            "contract_refs": ["feature.completed"],
            "capacity": 1,
            "ordering": "FIFO",
            "copy_policy": "copy",
            "timeout_ms": 0,
            "overload": "fail-safe",
            "realtime_timing": {
                "cross_core": True,
                "notification_latency_ns": 50_000,
                "release_jitter_ns": 20_000,
                "copy_cost_ns": 20_000,
                "cpu_cost_accounting": [
                    {"unit": "candidate-b-fast", "cost_ns": 10_000},
                    {"unit": "candidate-b-slow", "cost_ns": 10_000},
                ],
            },
        }
    ]
    manifest["platform_variants"] = []
    manifest["realtime_scheduling_studies"] = [
        {
            "id": "feature-task-study",
            "analysis_method": "rate-monotonic-rta",
            "objective": "Select a schedulable task count, rate, and core allocation.",
            "requirements": [
                "Meet the feature Flow deadline.",
                "Account for RTOS and cross-core overhead.",
            ],
            "assumptions": [
                "Tasks use partitioned fixed-priority scheduling.",
                "Provisional WCET values are conservative budgets.",
            ],
            "analysis_phase": "provisional",
            "workload_refs": ["feature-workload"],
            "flow_refs": ["feature-flow"],
            "candidate_profiles": ["candidate-a", "candidate-b"],
            "selected_profile": "candidate-a",
            "candidate_outcomes": {"candidate-b": "pass"},
            "rejection_reasons": {},
            "selection_rationale": "Candidate A uses fewer tasks and avoids cross-core transfer while meeting RTA.",
            "selection_approval": {
                "approved_by": "Fixture Owner",
                "approval_date": "2026-07-30",
                "approval_reference": "fixture-review-1",
            },
            "flow_chains": [
                {
                    "id": "candidate-a-flow",
                    "profile": "candidate-a",
                    "flow": "feature-flow",
                    "ordered_units": ["candidate-a-task"],
                    "ordered_channels": [],
                    "deadline_ns": 10_000_000,
                },
                {
                    "id": "candidate-b-flow",
                    "profile": "candidate-b",
                    "flow": "feature-flow",
                    "ordered_units": ["candidate-b-fast", "candidate-b-slow"],
                    "ordered_channels": ["candidate-b-handoff"],
                    "deadline_ns": 10_000_000,
                },
            ],
        }
    ]
    return manifest


def type_entry(
    owner: str,
    path: str,
    symbol: str,
    kind: str,
    semantic_kind: str,
    visibility: str,
    fields: list[dict] | None = None,
) -> dict:
    return {
        "id": symbol.lower().replace("_", "-"),
        "owner": owner,
        "language": "c",
        "declaration": {"path": path, "symbol": symbol, "kind": kind},
        "visibility": visibility,
        "semantic_kind": semantic_kind,
        "description": f"Govern {symbol}.",
        "lifetime": "Static firmware lifetime.",
        "mutability": "immutable",
        "mutation_authority": [],
        "consumers": [owner],
        "references": [],
        "fields": fields or [],
    }


def state_entry(
    owner: str,
    path: str,
    symbol: str,
    declared_type: str,
    *,
    type_ref: str | None = None,
    storage: str = "file-static",
) -> dict:
    result = {
        "id": symbol.lower().replace("_", "-"),
        "owner": owner,
        "language": "c",
        "declaration": {
            "path": path,
            "symbol": symbol,
            "storage": storage,
        },
        "type": declared_type,
        "visibility": "private",
        "lifetime": "Process lifetime.",
        "mutability": "owner-mutable",
        "read_authority": [owner],
        "write_authority": [owner],
    }
    if type_ref is not None:
        result["type_ref"] = type_ref
    return result


class SchemaV2Tests(unittest.TestCase):
    def test_valid_v2_keeps_all_inherited_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "architecture" / "manifest.yaml"
            diagnostics = validate_manifest(valid_manifest(), path)
        self.assertEqual(0, exit_code(diagnostics), diagnostics)

    def test_schema_1x_is_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["schema_version"] = "1.2.0"
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertEqual(2, exit_code(diagnostics))
        self.assertTrue(any(item.rule_id == "VER002" for item in diagnostics))

    def test_schema_2_0_1_is_not_silently_reinterpreted(self) -> None:
        manifest = valid_manifest()
        manifest["standard_version"] = "2.0.1"
        manifest["schema_version"] = "2.0.1"
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertEqual(2, exit_code(diagnostics))
        self.assertTrue(any(item.rule_id == "VER002" for item in diagnostics))

    def test_schema_2_0_2_is_rejected_after_realtime_contract_upgrade(self) -> None:
        manifest = valid_manifest()
        manifest["standard_version"] = "2.0.2"
        manifest["schema_version"] = "2.0.2"
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertEqual(2, exit_code(diagnostics))
        self.assertTrue(any(item.rule_id == "VER002" for item in diagnostics))

    def test_hard_realtime_bare_metal_profile_triggers_and_passes_study(self) -> None:
        diagnostics = validate_manifest(
            realtime_design_manifest(), Path("architecture/manifest.yaml")
        )
        self.assertEqual(0, exit_code(diagnostics), diagnostics)

    def test_best_effort_rtos_profile_does_not_require_study(self) -> None:
        manifest = valid_manifest()
        manifest["execution_profiles"][0]["execution_model"] = "rtos"
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertEqual(0, exit_code(diagnostics), diagnostics)
        self.assertFalse(
            any(item.rule_id.startswith("SCHED") for item in diagnostics),
            diagnostics,
        )

    def test_realtime_profile_requires_explicit_execution_environment(self) -> None:
        manifest = realtime_design_manifest()
        manifest["execution_profiles"][0].pop("execution_model")
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(
            any(item.rule_id == "SCHED005" for item in diagnostics),
            diagnostics,
        )

    def test_realtime_study_requires_distinct_candidates_and_human_selection(self) -> None:
        manifest = realtime_design_manifest()
        study = manifest["realtime_scheduling_studies"][0]
        study["candidate_profiles"] = ["candidate-a", "candidate-a"]
        study["selected_profile"] = "candidate-a"
        study["selection_approval"]["approved_by"] = "Codex"
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        rules = {item.rule_id for item in diagnostics}
        self.assertIn("SCHED041", rules)
        self.assertIn("SCHED046", rules)

    def test_selected_hard_realtime_candidate_must_pass_rta(self) -> None:
        manifest = realtime_design_manifest()
        manifest["execution_units"][0]["realtime_task"]["relative_deadline_ns"] = 100_000
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        rules = {item.rule_id for item in diagnostics}
        self.assertIn("SCHED061", rules)
        self.assertIn("SCHED062", rules)
        self.assertEqual(1, exit_code(diagnostics))

    def test_selected_hard_realtime_deadline_miss_cannot_be_baselined(self) -> None:
        manifest = realtime_design_manifest()
        manifest["execution_units"][0]["realtime_task"]["relative_deadline_ns"] = 100_000
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "architecture" / "manifest.yaml"
            manifest_path.parent.mkdir()
            baseline_path = root / "architecture" / "baseline.yaml"
            baseline_path.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "2.1.0",
                        "violations": [
                            {"rule_id": "SCHED061", "location": "candidate-a"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            diagnostics = validate_manifest(
                manifest, manifest_path, baseline_path=baseline_path
            )
        misses = [item for item in diagnostics if item.rule_id == "SCHED061"]
        self.assertTrue(misses)
        self.assertTrue(all(item.disposition == "active" for item in misses))

    def test_final_accepted_realtime_profile_requires_runtime_evidence(self) -> None:
        manifest = realtime_design_manifest()
        profile = manifest["execution_profiles"][0]
        profile["status"] = "accepted"
        profile["analysis_phase"] = "final"
        profile["approval"] = {
            "approved_by": "Fixture Owner",
            "approval_date": "2026-07-30",
            "approval_reference": "fixture-final-review",
        }
        study = manifest["realtime_scheduling_studies"][0]
        study["analysis_phase"] = "final"
        study["final_approval"] = copy.deepcopy(profile["approval"])
        for unit in manifest["execution_units"]:
            if unit["profile"] != "candidate-a":
                continue
            for component in unit["realtime_task"]["demand_components"]:
                component.update(
                    {
                        "final_ns": component["budget_ns"],
                        "basis": "measured",
                        "evidence_path": "validation/wcet.json",
                        "evidence_sha256": "a" * 64,
                    }
                )
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "SCHED013" for item in diagnostics))

    def test_unsupported_scheduling_method_is_blocked(self) -> None:
        for method in (
            "earliest-deadline-first",
            "cyclic-executive",
            "unknown-method",
        ):
            with self.subTest(method=method):
                manifest = realtime_design_manifest()
                manifest["realtime_scheduling_studies"][0][
                    "analysis_method"
                ] = method
                diagnostics = validate_manifest(
                    manifest, Path("architecture/manifest.yaml")
                )
                rules = {item.rule_id for item in diagnostics}
                self.assertIn("SCHED060", rules)
                self.assertIn("SCHED062", rules)
                self.assertEqual(2, exit_code(diagnostics))

    def test_soft_rta_risk_requires_plan_and_human_risk_acceptance(self) -> None:
        manifest = realtime_design_manifest()
        workload = manifest["workloads"][0]
        workload["timing_class"] = "soft-real-time"
        workload["budgets"] = [
            {
                "metric": "latency-p99",
                "operator": "<=",
                "threshold": 10_000_000,
                "unit": "ns",
                "method": "percentile",
            },
            {
                "metric": "deadline-miss-rate",
                "operator": "<=",
                "threshold": 0.001,
                "unit": "ratio",
                "method": "runtime-evidence",
            },
        ]
        manifest["execution_units"][0]["realtime_task"][
            "relative_deadline_ns"
        ] = 100_000

        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        rules = {item.rule_id for item in diagnostics}
        self.assertIn("SCHED063", rules)
        self.assertNotIn("SCHED061", rules)
        self.assertNotIn("SCHED062", rules)

        manifest["realtime_scheduling_studies"][0]["soft_acceptance_plans"] = [
            {
                "workload": "feature-workload",
                "validation_plan_path": "validation/soft-slo-plan.md",
                "evidence_format": "JSON percentile and miss-rate summary",
                "risk_approval": {
                    "approved_by": "Fixture Owner",
                    "approval_date": "2026-07-30",
                    "approval_reference": "fixture-soft-risk-review",
                },
            }
        ]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertEqual(0, exit_code(diagnostics), diagnostics)

    def test_final_soft_profile_requires_bound_passing_slo_evidence(self) -> None:
        manifest = realtime_design_manifest()
        workload = manifest["workloads"][0]
        workload["timing_class"] = "soft-real-time"
        workload["budgets"] = [
            {
                "metric": "latency-p99",
                "operator": "<=",
                "threshold": 10_000_000,
                "unit": "ns",
                "method": "percentile",
            },
            {
                "metric": "deadline-miss-rate",
                "operator": "<=",
                "threshold": 0.001,
                "unit": "ratio",
                "method": "runtime-evidence",
            },
        ]
        approval = {
            "approved_by": "Fixture Owner",
            "approval_date": "2026-07-30",
            "approval_reference": "fixture-final-review",
        }
        for profile in manifest["execution_profiles"]:
            profile["analysis_phase"] = "final"
        selected = manifest["execution_profiles"][0]
        selected["status"] = "accepted"
        selected["approval"] = copy.deepcopy(approval)
        selected["runtime_evidence"] = [
            {
                "path": "validation/runtime-summary.json",
                "sha256": "a" * 64,
                "profile_id": "candidate-a",
                "manifest_sha256": "b" * 64,
            }
        ]
        for unit in manifest["execution_units"]:
            for component in unit["realtime_task"]["demand_components"]:
                component.update(
                    {
                        "final_ns": component["budget_ns"],
                        "basis": "measured",
                        "evidence_path": "validation/wcet.json",
                        "evidence_sha256": "c" * 64,
                    }
                )
        study = manifest["realtime_scheduling_studies"][0]
        study["analysis_phase"] = "final"
        study["final_approval"] = copy.deepcopy(approval)
        study["soft_acceptance_plans"] = [
            {
                "workload": "feature-workload",
                "validation_plan_path": "validation/soft-slo-plan.md",
                "evidence_format": "JSON percentile and miss-rate summary",
                "risk_approval": {
                    "approved_by": "Fixture Owner",
                    "approval_date": "2026-07-30",
                    "approval_reference": "fixture-soft-risk-review",
                },
            }
        ]

        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(
            any(item.rule_id == "SCHED064" for item in diagnostics),
            diagnostics,
        )

        study["soft_slo_results"] = [
            {
                "workload": "feature-workload",
                "verdict": "pass",
                "evidence_path": "validation/soft-slo-result.json",
                "evidence_sha256": "d" * 64,
                "profile_id": "candidate-a",
                "manifest_sha256": "b" * 64,
            }
        ]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertEqual(0, exit_code(diagnostics), diagnostics)

    def test_obsolete_rtos_specific_fields_are_configuration_blocked(self) -> None:
        manifest = realtime_design_manifest()
        manifest["rtos_design_studies"] = manifest.pop(
            "realtime_scheduling_studies"
        )
        manifest["execution_profiles"][0]["overheads"]["timer_isr_ns"] = 1
        manifest["execution_units"][0]["rtos"] = {}
        manifest["execution_units"][0]["rtos_isr"] = {}
        manifest["execution_channels"][0]["rtos_timing"] = {}
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        obsolete = [item for item in diagnostics if item.rule_id == "SCHED000"]
        self.assertTrue(obsolete, diagnostics)
        self.assertTrue(all(item.configuration for item in obsolete))
        locations = {item.location for item in obsolete}
        self.assertTrue(
            {
                "rtos_design_studies",
                "candidate-a.overheads.timer_isr_ns",
                "candidate-a-task.rtos",
                "candidate-a-task.rtos_isr",
                "candidate-b-handoff.rtos_timing",
            }.issubset(locations),
            locations,
        )

    def test_every_realtime_workload_profile_pair_has_exactly_one_study(self) -> None:
        manifest = realtime_design_manifest()
        manifest["realtime_scheduling_studies"] = []
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(
            any(item.rule_id == "SCHED070" for item in diagnostics),
            diagnostics,
        )

        manifest = realtime_design_manifest()
        duplicate = copy.deepcopy(manifest["realtime_scheduling_studies"][0])
        duplicate["id"] = "duplicate-feature-task-study"
        manifest["realtime_scheduling_studies"].append(duplicate)
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(
            any(item.rule_id == "SCHED070" for item in diagnostics),
            diagnostics,
        )

    def test_source_set_overlap_and_nonproduction_declaration_are_blocking(self) -> None:
        manifest = valid_manifest()
        manifest["source_sets"].append(
            {
                "id": "overlap",
                "classification": "development",
                "include": ["src/feature/**"],
                "exclude": [],
                "purpose": "Create an intentional overlap.",
                "provenance": "Fixture.",
            }
        )
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "SRC004" for item in diagnostics))

        manifest = valid_manifest()
        manifest["types"] = [
            type_entry(
                "feature", "tests/generated.h", "GeneratedTestType", "struct",
                "domain-value", "module-public",
                [{"name": "value", "type": "int", "role": "domain-value", "meaning": "Test value."}],
            )
        ]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "SRC005" for item in diagnostics))

    def test_source_set_unclassified_absolute_and_traversal_are_blocked(self) -> None:
        manifest = valid_manifest()
        manifest["source_sets"][0]["include"] = ["formal/**"]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "SRC004" for item in diagnostics))

        for invalid in ("C:/absolute/**", "../escape/**"):
            manifest = valid_manifest()
            manifest["source_sets"][0]["include"].append(invalid)
            diagnostics = validate_manifest(
                manifest, Path("architecture/manifest.yaml")
            )
            self.assertTrue(any(item.rule_id == "SRC002" for item in diagnostics))

    def test_v1_core_dependency_rule_remains(self) -> None:
        manifest = valid_manifest()
        manifest["modules"][1]["depends_on"] = ["adapter"]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "DEP002" for item in diagnostics))

    def test_v1_1_description_rule_remains(self) -> None:
        manifest = valid_manifest()
        manifest["modules"][1]["description"]["purpose"] = ""
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "DESC006" for item in diagnostics))

    def test_v1_2_execution_rule_remains(self) -> None:
        manifest = valid_manifest()
        del manifest["flows"][0]["steps"][0]["id"]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "EXE001" for item in diagnostics))

    def test_functional_public_type_rejects_adapter_field(self) -> None:
        manifest = valid_manifest()
        manifest["types"] = [
            type_entry(
                "feature",
                "src/feature/feature.h",
                "IoEndpointDescriptor",
                "struct",
                "descriptor",
                "cross-module",
                [
                    {
                        "name": "logical_role",
                        "type": "unsigned char",
                        "role": "domain-identity",
                        "meaning": "Logical signal role.",
                    },
                    {
                        "name": "adapter_channel",
                        "type": "unsigned short",
                        "role": "adapter-binding",
                        "meaning": "Physical channel index.",
                    },
                ],
            )
        ]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "TYP004" for item in diagnostics))

    def test_runtime_state_must_be_private_and_owner_mutated(self) -> None:
        manifest = valid_manifest()
        entry = type_entry(
            "feature",
            "src/feature/feature.h",
            "FeatureRuntime",
            "struct",
            "runtime-state",
            "cross-module",
        )
        entry["mutability"] = "owner-mutable"
        entry["mutation_authority"] = ["adapter"]
        manifest["types"] = [entry]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        rules = {item.rule_id for item in diagnostics}
        self.assertIn("TYP004", rules)
        self.assertIn("TYP005", rules)

    def test_type_exclusion_requires_l3_owner(self) -> None:
        manifest = valid_manifest()
        manifest["type_exclusions"] = [
            {
                "path": "src/feature/generated/**",
                "owner": "feature",
                "classification": "generated",
                "source": "fixture generator",
                "reason": "Generated declarations.",
            }
        ]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "TYP007" for item in diagnostics))

    def test_planned_illegal_type_reference_is_blocking(self) -> None:
        manifest = valid_manifest()
        parent_contract = type_entry(
            "app",
            "src/app/app.h",
            "ParentContract",
            "struct",
            "command",
            "cross-module",
        )
        child_contract = type_entry(
            "feature",
            "src/feature/feature.h",
            "ChildContract",
            "struct",
            "command",
            "cross-module",
        )
        child_contract["references"] = [parent_contract["id"]]
        manifest["types"] = [parent_contract, child_contract]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "TYP006" for item in diagnostics))

    def test_unresolved_parent_mapping_is_blocking(self) -> None:
        manifest = valid_manifest()
        consumer = module(
            "consumer", "L1", "domain", "src/consumer", "app", []
        )
        manifest["modules"].append(consumer)
        producer_contract = type_entry(
            "feature",
            "src/feature/feature.h",
            "FeatureResult",
            "struct",
            "event-payload",
            "cross-module",
        )
        consumer_contract = type_entry(
            "consumer",
            "src/consumer/consumer.h",
            "ConsumerCommand",
            "struct",
            "command",
            "cross-module",
        )
        manifest["types"] = [producer_contract, consumer_contract]
        manifest["boundary_mappings"] = [
            {
                "id": "feature-to-consumer",
                "interaction": "Transfer a result to a sibling command.",
                "producer": "feature",
                "consumer": "consumer",
                "parent": "app",
                "producer_contract": producer_contract["id"],
                "consumer_contract": consumer_contract["id"],
                "mapping_owner": None,
                "state_objects": [],
                "allowed_edges": [],
                "forbidden_edges": [
                    "feature->consumer",
                    "consumer->feature",
                ],
            }
        ]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertTrue(any(item.rule_id == "BND004" for item in diagnostics))

    def test_legal_direct_contract_reuse_does_not_require_second_dto(self) -> None:
        manifest = valid_manifest()
        producer_contract = type_entry(
            "feature",
            "src/feature/feature.h",
            "FeatureResult",
            "struct",
            "event-payload",
            "cross-module",
        )
        producer_contract["consumers"] = ["feature", "app"]
        manifest["types"] = [producer_contract]
        manifest["boundary_mappings"] = [
            {
                "id": "feature-to-parent",
                "interaction": "Deliver a child result directly to its parent.",
                "producer": "feature",
                "consumer": "app",
                "parent": "app",
                "producer_contract": producer_contract["id"],
                "consumer_contract": producer_contract["id"],
                "mapping_owner": None,
                "state_objects": [],
                "allowed_edges": ["app->feature"],
                "forbidden_edges": ["feature->app"],
            }
        ]
        diagnostics = validate_manifest(manifest, Path("architecture/manifest.yaml"))
        self.assertEqual(0, exit_code(diagnostics), diagnostics)

    def test_renderer_contains_type_catalog(self) -> None:
        manifest = valid_manifest()
        manifest["types"] = [
            type_entry(
                "feature",
                "src/feature/feature.h",
                "SignalId",
                "alias",
                "domain-identity",
                "cross-module",
            )
        ]
        manifest["types"][0]["target"] = "unsigned short"
        documents = render_documents(manifest)
        self.assertIn("Type Catalog", documents[Path("generated/system.md")])
        self.assertIn("SignalId", documents[Path("generated/system.md")])
        self.assertIn("State Ownership", documents[Path("generated/system.md")])
        self.assertIn("Cross-module Mapping", documents[Path("generated/system.md")])


class CAnalyzerV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from libclang_toolchain_adapter import EspressifLibclangToolchainAdapter

        cls.provider_evidence = EspressifLibclangToolchainAdapter().verify(
            SKILL_ROOT / "assets" / "project" / "toolchain-lock.yaml"
        )

    def setUp(self) -> None:
        patcher = mock.patch(
            "libclang_toolchain_adapter.EspressifLibclangToolchainAdapter.verify",
            return_value=self.provider_evidence,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_windows_quoted_include_with_spaces_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "main.cpp"
            source.write_text("int main_value;\n", encoding="utf-8")
            entry = {
                "command": (
                    f'clang++ "-I{root / "Library With Spaces" / "src"}" '
                    f'-c "{source}"'
                ),
                "file": str(source),
                "_source": source,
            }
            arguments = _parse_arguments(entry, "native")
        self.assertIn(
            f"-I{root / 'Library With Spaces' / 'src'}",
            arguments,
        )

    def write_fixture(self, root: Path) -> None:
        commands = []
        for name in ("app", "feature", "adapter"):
            directory = root / "src" / name
            directory.mkdir(parents=True)
            (directory / f"{name}.c").write_text(
                f'#include "{name}.h"\nvoid {name}_init(void) {{}}\n',
                encoding="utf-8",
            )
            (directory / f"{name}.h").write_text(
                f"void {name}_port(void);\n",
                encoding="utf-8",
            )
            commands.append(
                {
                    "directory": str(root),
                    "file": f"src/{name}/{name}.c",
                    "arguments": [
                        "clang",
                        "-std=c11",
                        f"-I{directory}",
                        "-c",
                        f"src/{name}/{name}.c",
                    ],
                }
            )
        (root / "compile_commands.json").write_text(
            json.dumps(commands, indent=2),
            encoding="utf-8",
        )

    def add_translation_unit(self, root: Path, module_name: str) -> None:
        commands = json.loads(
            (root / "compile_commands.json").read_text(encoding="utf-8")
        )
        commands.append(
            {
                "directory": str(root),
                "file": f"src/{module_name}/{module_name}.c",
                "arguments": [
                    "clang",
                    "-std=c11",
                    f"-I{root / 'src' / module_name}",
                    "-c",
                    f"src/{module_name}/{module_name}.c",
                ],
            }
        )
        (root / "compile_commands.json").write_text(
            json.dumps(commands, indent=2),
            encoding="utf-8",
        )

    def add_generated_od(self, root: Path, manifest: dict) -> None:
        generated = root / "src" / "adapter" / "generated"
        generated.mkdir(parents=True)
        (generated / "od.c").write_text(
            "int od_generated_state;\n",
            encoding="utf-8",
        )
        manifest["source_sets"][0]["exclude"].append(
            "src/adapter/generated/**"
        )
        manifest["source_sets"][1]["include"] = [
            "src/adapter/generated/**"
        ]
        commands = json.loads(
            (root / "compile_commands.json").read_text(encoding="utf-8")
        )
        commands.append(
            {
                "directory": str(root),
                "file": "src/adapter/generated/od.c",
                "arguments": [
                    "clang", "-std=c11", "-c",
                    "src/adapter/generated/od.c",
                ],
            }
        )
        (root / "compile_commands.json").write_text(
            json.dumps(commands, indent=2),
            encoding="utf-8",
        )

    def test_generated_state_is_catalog_only_and_non_owner_access_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            manifest = valid_manifest(c_ast=True)
            self.add_generated_od(root, manifest)
            diagnostics, mode = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
            self.assertEqual("libclang-ast", mode)
            self.assertTrue(any(item.rule_id == "CSTATE007" for item in diagnostics))
            self.assertFalse(
                any(
                    item.rule_id == "CSTATE001"
                    and "od_generated_state" in item.location
                    for item in diagnostics
                )
            )

            (root / "src" / "feature" / "feature.c").write_text(
                '#include "feature.h"\n'
                "extern int od_generated_state;\n"
                "void feature_init(void) { (void)od_generated_state; }\n",
                encoding="utf-8",
            )
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
            self.assertTrue(
                any(item.rule_id == "CSTATE003" for item in diagnostics),
                diagnostics,
            )

    def test_development_source_in_production_database_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            tests = root / "tests"
            tests.mkdir()
            (tests / "probe.c").write_text("int probe(void) { return 0; }\n", encoding="utf-8")
            commands = json.loads(
                (root / "compile_commands.json").read_text(encoding="utf-8")
            )
            commands.append(
                {
                    "directory": str(root),
                    "file": "tests/probe.c",
                    "arguments": ["clang", "-std=c11", "-c", "tests/probe.c"],
                }
            )
            (root / "compile_commands.json").write_text(
                json.dumps(commands, indent=2), encoding="utf-8"
            )
            diagnostics, _ = analyze(
                valid_manifest(c_ast=True),
                root / "architecture" / "manifest.yaml",
                root,
            )
            self.assertTrue(any(item.rule_id == "SRC006" for item in diagnostics))

    def test_build_output_declarations_are_not_product_catalog_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            build = root / "build"
            build.mkdir()
            (build / "generated.h").write_text(
                "typedef struct { int value; } BuildArtifact;\n",
                encoding="utf-8",
            )
            feature_source = root / "src" / "feature" / "feature.c"
            feature_source.write_text(
                '#include "feature.h"\n'
                '#include "../../build/generated.h"\n'
                "void feature_init(void) {}\n",
                encoding="utf-8",
            )
            diagnostics, _ = analyze(
                valid_manifest(c_ast=True),
                root / "architecture" / "manifest.yaml",
                root,
            )
            self.assertFalse(
                any(
                    item.rule_id.startswith("CTYPE")
                    and "BuildArtifact" in item.location
                    for item in diagnostics
                ),
                diagnostics,
            )

    def test_wrong_manifest_cannot_hide_hardware_use(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            feature_header = root / "src" / "feature" / "feature.h"
            feature_header.write_text(
                "typedef struct {\n"
                "  unsigned char logical_role;\n"
                "  unsigned short adapter_channel;\n"
                "} IoEndpointDescriptor;\n"
                "void feature_port(void);\n",
                encoding="utf-8",
            )
            (root / "src" / "feature" / "feature.c").write_text(
                '#include "feature.h"\n'
                "void feature_init(void) { GPIO_SetBits(0, 1); }\n",
                encoding="utf-8",
            )
            manifest = valid_manifest(c_ast=True)
            manifest["types"] = [
                type_entry(
                    "feature",
                    "src/feature/feature.h",
                    "IoEndpointDescriptor",
                    "struct",
                    "descriptor",
                    "cross-module",
                    [
                        {
                            "name": "logical_role",
                            "type": "unsigned char",
                            "role": "domain-value",
                            "meaning": "Logical role.",
                        },
                        {
                            "name": "adapter_channel",
                            "type": "unsigned short",
                            "role": "domain-value",
                            "meaning": "Incorrectly claimed domain value.",
                        },
                    ],
                )
            ]
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        self.assertTrue(any(item.rule_id == "CFUN002" for item in diagnostics))

    def test_unregistered_runtime_state_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.c").write_text(
                '#include "feature.h"\n'
                "static int g_runtime;\n"
                "void feature_init(void) { g_runtime = 1; }\n",
                encoding="utf-8",
            )
            diagnostics, _ = analyze(
                valid_manifest(c_ast=True),
                root / "architecture" / "manifest.yaml",
                root,
            )
        self.assertTrue(
            any(item.rule_id == "CSTATE001" for item in diagnostics), diagnostics
        )

    def test_state_definition_shape_must_match_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.c").write_text(
                '#include "feature.h"\n'
                "static int g_runtime;\n"
                "void feature_init(void) { g_runtime = 1; }\n",
                encoding="utf-8",
            )
            manifest = valid_manifest(c_ast=True)
            manifest["state_objects"] = [
                state_entry(
                    "feature",
                    "src/feature/feature.c",
                    "g_runtime",
                    "long",
                    storage="external-linkage",
                )
            ]
            manifest["state_objects"][0]["visibility"] = "module-public"
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        self.assertTrue(any(item.rule_id == "CSTATE002" for item in diagnostics))

    def test_unauthorized_read_and_private_extern_leak_are_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.h").write_text(
                "extern int g_runtime;\nvoid feature_port(void);\n",
                encoding="utf-8",
            )
            (root / "src" / "feature" / "feature.c").write_text(
                '#include "feature.h"\n'
                "int g_runtime;\n"
                "void feature_init(void) { g_runtime = 1; }\n",
                encoding="utf-8",
            )
            (root / "src" / "app" / "app.c").write_text(
                '#include "app.h"\n'
                '#include "../feature/feature.h"\n'
                "#define READ_RUNTIME() (g_runtime)\n"
                "void app_init(void) { g_runtime = 2; int observed = READ_RUNTIME(); (void)observed; }\n",
                encoding="utf-8",
            )
            manifest = valid_manifest(c_ast=True)
            runtime = state_entry(
                "feature",
                "src/feature/feature.c",
                "g_runtime",
                "int",
                storage="external-linkage",
            )
            runtime["visibility"] = "private"
            manifest["state_objects"] = [runtime]
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        rules = {item.rule_id for item in diagnostics}
        self.assertIn("CSTATE003", rules, diagnostics)
        self.assertIn("CSTATE004", rules, diagnostics)
        self.assertIn("CSTATE005", rules, diagnostics)

    def test_getter_cannot_launder_private_state_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.h").write_text(
                "typedef struct FeatureRuntime FeatureRuntime;\n"
                "FeatureRuntime *feature_runtime(void);\n"
                "void feature_port(void);\n",
                encoding="utf-8",
            )
            (root / "src" / "feature" / "feature.c").write_text(
                '#include "feature.h"\n'
                "struct FeatureRuntime { int value; };\n"
                "static FeatureRuntime g_runtime;\n"
                "FeatureRuntime *feature_runtime(void) { return &g_runtime; }\n"
                "void feature_init(void) {}\n",
                encoding="utf-8",
            )
            manifest = valid_manifest(c_ast=True)
            alias = type_entry(
                "feature",
                "src/feature/feature.h",
                "FeatureRuntime",
                "alias",
                "port",
                "cross-module",
            )
            alias["target"] = "struct FeatureRuntime"
            alias["id"] = "feature-runtime-handle"
            runtime_type = type_entry(
                "feature",
                "src/feature/feature.c",
                "FeatureRuntime",
                "struct",
                "runtime-state",
                "private",
                [
                    {
                        "name": "value",
                        "type": "int",
                        "role": "runtime-state",
                        "meaning": "Owner-private runtime value.",
                    }
                ],
            )
            runtime_type["mutability"] = "owner-mutable"
            runtime_type["mutation_authority"] = ["feature"]
            runtime_type["id"] = "feature-runtime-record"
            manifest["types"] = [alias, runtime_type]
            manifest["state_objects"] = [
                state_entry(
                    "feature",
                    "src/feature/feature.c",
                    "g_runtime",
                    "FeatureRuntime",
                    type_ref=runtime_type["id"],
                )
            ]
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        self.assertTrue(
            any(item.rule_id == "CSTATE005" for item in diagnostics), diagnostics
        )

    def test_child_reference_to_parent_type_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "app" / "app.h").write_text(
                "typedef struct { int value; } AppContract;\n"
                "void app_port(void);\n",
                encoding="utf-8",
            )
            (root / "src" / "feature" / "feature.h").write_text(
                '#include "../app/app.h"\n'
                "void feature_accept(AppContract value);\n"
                "void feature_port(void);\n",
                encoding="utf-8",
            )
            contract = type_entry(
                "app",
                "src/app/app.h",
                "AppContract",
                "struct",
                "command",
                "cross-module",
                [
                    {
                        "name": "value",
                        "type": "int",
                        "role": "domain-value",
                        "meaning": "Parent-owned value.",
                    }
                ],
            )
            manifest = valid_manifest(c_ast=True)
            manifest["types"] = [contract]
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        self.assertTrue(any(item.rule_id == "CTYPE005" for item in diagnostics))

    def test_missing_ast_declaration_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            manifest = valid_manifest(c_ast=True)
            manifest["c_analyzer"]["ast"] = {
                "status": "not-applicable",
                "rationale": "Incorrectly disabled.",
            }
            diagnostics, mode = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        self.assertNotEqual("libclang-ast", mode)
        self.assertTrue(any(item.rule_id == "CAST001" for item in diagnostics))
        self.assertEqual(2, exit_code(diagnostics))

    def test_non_owner_private_runtime_dereference_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.h").write_text(
                "typedef struct FeatureRuntime { int value; } FeatureRuntime;\n"
                "void feature_port(void);\n",
                encoding="utf-8",
            )
            (root / "src" / "app" / "app.c").write_text(
                '#include "app.h"\n'
                '#include "../feature/feature.h"\n'
                "void app_read(FeatureRuntime *runtime) { int value = runtime->value; (void)value; }\n"
                "void app_init(void) {}\n",
                encoding="utf-8",
            )
            runtime_type = type_entry(
                "feature",
                "src/feature/feature.h",
                "FeatureRuntime",
                "struct",
                "runtime-state",
                "private",
                [
                    {
                        "name": "value",
                        "type": "int",
                        "role": "runtime-state",
                        "meaning": "Owner-private runtime value.",
                    }
                ],
            )
            runtime_type["mutability"] = "owner-mutable"
            runtime_type["mutation_authority"] = ["feature"]
            manifest = valid_manifest(c_ast=True)
            manifest["types"] = [runtime_type]
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        rules = {item.rule_id for item in diagnostics}
        self.assertIn("CSTATE005", rules, diagnostics)
        self.assertIn("CSTATE006", rules, diagnostics)

    def test_legal_opaque_handle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.h").write_text(
                "typedef struct FeatureHandle FeatureHandle;\n"
                "FeatureHandle *feature_open(void);\n"
                "int feature_read(const FeatureHandle *handle);\n"
                "void feature_port(void);\n",
                encoding="utf-8",
            )
            (root / "src" / "feature" / "feature.c").write_text(
                '#include "feature.h"\n'
                "struct FeatureHandle { int value; };\n"
                "FeatureHandle *feature_open(void) { return (FeatureHandle *)0; }\n"
                "int feature_read(const FeatureHandle *handle) { return handle ? handle->value : 0; }\n"
                "void feature_init(void) {}\n",
                encoding="utf-8",
            )
            (root / "src" / "app" / "app.c").write_text(
                '#include "app.h"\n'
                '#include "../feature/feature.h"\n'
                "void app_init(void) { FeatureHandle *handle = feature_open(); (void)feature_read(handle); }\n",
                encoding="utf-8",
            )
            handle_alias = type_entry(
                "feature",
                "src/feature/feature.h",
                "FeatureHandle",
                "alias",
                "port",
                "cross-module",
            )
            handle_alias["id"] = "feature-handle"
            handle_alias["target"] = "struct FeatureHandle"
            handle_alias["consumers"] = ["feature", "app"]
            handle_record = type_entry(
                "feature",
                "src/feature/feature.c",
                "FeatureHandle",
                "struct",
                "private-helper",
                "private",
                [
                    {
                        "name": "value",
                        "type": "int",
                        "role": "runtime-state",
                        "meaning": "Private handle representation.",
                    }
                ],
            )
            handle_record["id"] = "feature-handle-record"
            manifest = valid_manifest(c_ast=True)
            manifest["types"] = [handle_alias, handle_record]
            diagnostics, mode = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        active_must = [
            item
            for item in diagnostics
            if item.severity == "MUST" and item.disposition == "active"
        ]
        self.assertEqual("libclang-ast", mode)
        self.assertEqual([], active_must, active_must)

    def test_legal_parent_mapping_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            consumer_dir = root / "src" / "consumer"
            consumer_dir.mkdir()
            (consumer_dir / "consumer.h").write_text(
                "typedef struct { int target; } ConsumerCommand;\n"
                "void consumer_accept(ConsumerCommand command);\n"
                "void consumer_port(void);\n",
                encoding="utf-8",
            )
            (consumer_dir / "consumer.c").write_text(
                '#include "consumer.h"\n'
                "void consumer_accept(ConsumerCommand command) { (void)command; }\n"
                "void consumer_init(void) {}\n",
                encoding="utf-8",
            )
            self.add_translation_unit(root, "consumer")
            (root / "src" / "feature" / "feature.h").write_text(
                "typedef struct { int value; } FeatureResult;\n"
                "FeatureResult feature_result(void);\n"
                "void feature_port(void);\n",
                encoding="utf-8",
            )
            (root / "src" / "feature" / "feature.c").write_text(
                '#include "feature.h"\n'
                "FeatureResult feature_result(void) { FeatureResult result = {1}; return result; }\n"
                "void feature_init(void) {}\n",
                encoding="utf-8",
            )
            (root / "src" / "app" / "app.c").write_text(
                '#include "app.h"\n'
                '#include "../feature/feature.h"\n'
                '#include "../consumer/consumer.h"\n'
                "void app_init(void) {\n"
                "  FeatureResult result = feature_result();\n"
                "  ConsumerCommand command = { result.value };\n"
                "  consumer_accept(command);\n"
                "}\n",
                encoding="utf-8",
            )
            manifest = valid_manifest(c_ast=True)
            consumer_module = module(
                "consumer", "L1", "domain", "src/consumer", "app", []
            )
            manifest["modules"].append(consumer_module)
            manifest["modules"][0]["depends_on"].append("consumer")
            producer_contract = type_entry(
                "feature",
                "src/feature/feature.h",
                "FeatureResult",
                "struct",
                "event-payload",
                "cross-module",
                [
                    {
                        "name": "value",
                        "type": "int",
                        "role": "domain-value",
                        "meaning": "Producer result.",
                    }
                ],
            )
            producer_contract["consumers"] = ["feature", "app"]
            consumer_contract = type_entry(
                "consumer",
                "src/consumer/consumer.h",
                "ConsumerCommand",
                "struct",
                "command",
                "cross-module",
                [
                    {
                        "name": "target",
                        "type": "int",
                        "role": "domain-value",
                        "meaning": "Consumer target.",
                    }
                ],
            )
            consumer_contract["consumers"] = ["consumer", "app"]
            manifest["types"] = [producer_contract, consumer_contract]
            manifest["boundary_mappings"] = [
                {
                    "id": "feature-to-consumer",
                    "interaction": "Map a producer result to a consumer command.",
                    "producer": "feature",
                    "consumer": "consumer",
                    "parent": "app",
                    "producer_contract": producer_contract["id"],
                    "consumer_contract": consumer_contract["id"],
                    "mapping_owner": "app",
                    "state_objects": [],
                    "allowed_edges": ["app->feature", "app->consumer"],
                    "forbidden_edges": [
                        "feature->consumer",
                        "consumer->feature",
                    ],
                }
            ]
            diagnostics, mode = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        active_must = [
            item
            for item in diagnostics
            if item.severity == "MUST" and item.disposition == "active"
        ]
        self.assertEqual("libclang-ast", mode)
        self.assertEqual([], active_must, active_must)

    def test_split_domain_and_private_binding_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.h").write_text(
                "typedef unsigned short IoEndpointId;\nvoid feature_port(void);\n",
                encoding="utf-8",
            )
            (root / "src" / "adapter" / "adapter.h").write_text(
                '#include "../feature/feature.h"\n'
                "typedef struct {\n"
                "  IoEndpointId logical_id;\n"
                "  unsigned short channel;\n"
                "} IoEndpointBinding;\n"
                "void adapter_port(void);\n",
                encoding="utf-8",
            )
            manifest = valid_manifest(c_ast=True)
            domain_type = type_entry(
                "feature",
                "src/feature/feature.h",
                "IoEndpointId",
                "alias",
                "domain-identity",
                "cross-module",
            )
            domain_type["target"] = "unsigned short"
            domain_type["consumers"] = ["feature", "adapter"]
            binding = type_entry(
                "adapter",
                "src/adapter/adapter.h",
                "IoEndpointBinding",
                "struct",
                "adapter-binding",
                "private",
                [
                    {
                        "name": "logical_id",
                        "type": "IoEndpointId",
                        "role": "domain-identity",
                        "meaning": "Demand-owned endpoint identity.",
                    },
                    {
                        "name": "channel",
                        "type": "unsigned short",
                        "role": "adapter-binding",
                        "meaning": "Physical adapter channel.",
                    },
                ],
            )
            manifest["types"] = [domain_type, binding]
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        active_must = [
            item
            for item in diagnostics
            if item.severity == "MUST" and item.disposition == "active"
        ]
        self.assertEqual([], active_must, active_must)

    def test_missing_named_type_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.h").write_text(
                "typedef unsigned short SignalId;\nvoid feature_port(void);\n",
                encoding="utf-8",
            )
            diagnostics, _ = analyze(
                valid_manifest(c_ast=True), root / "architecture" / "manifest.yaml", root
            )
        self.assertTrue(any(item.rule_id == "CTYPE001" for item in diagnostics))

    def test_discovery_covers_enum_union_alias_and_function_pointer(self) -> None:
        declarations = _discover_named_types(
            "enum Mode { MODE_A, MODE_B };\n"
            "typedef union { unsigned short word; unsigned char byte; } Value;\n"
            "typedef struct Tagged { int value; } TaggedAlias;\n"
            "class Box { int value; };\n"
            "typedef unsigned short SignalId;\n"
            "typedef int (*Handler)(SignalId value);\n",
            "types.h",
        )
        found = {(item["symbol"], item["kind"]) for item in declarations}
        self.assertIn(("Mode", "enum"), found)
        self.assertIn(("Value", "union"), found)
        self.assertIn(("SignalId", "alias"), found)
        self.assertIn(("Handler", "function-pointer"), found)
        self.assertIn(("Tagged", "struct"), found)
        self.assertIn(("TaggedAlias", "alias"), found)
        self.assertIn(("Box", "class"), found)

    def test_stale_catalog_and_field_shape_are_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.h").write_text(
                "typedef struct { unsigned short value; } SignalValue;\n"
                "void feature_port(void);\n",
                encoding="utf-8",
            )
            wrong_shape = type_entry(
                "feature",
                "src/feature/feature.h",
                "SignalValue",
                "struct",
                "domain-value",
                "cross-module",
                [
                    {
                        "name": "value",
                        "type": "unsigned char",
                        "role": "domain-value",
                        "meaning": "Incorrect catalog width.",
                    }
                ],
            )
            stale = type_entry(
                "feature",
                "src/feature/feature.h",
                "MissingType",
                "struct",
                "domain-value",
                "cross-module",
            )
            manifest = valid_manifest(c_ast=True)
            manifest["types"] = [wrong_shape, stale]
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        rules = {item.rule_id for item in diagnostics}
        self.assertIn("CTYPE002", rules)
        self.assertIn("CTYPE003", rules)

    def test_excluded_vendor_type_cannot_leak_to_functional_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            vendor = root / "src" / "adapter" / "vendor"
            vendor.mkdir()
            (vendor / "vendor.h").write_text(
                "typedef struct { int value; } VendorHandle;\n",
                encoding="utf-8",
            )
            (root / "src" / "feature" / "feature.h").write_text(
                '#include "../adapter/vendor/vendor.h"\n'
                "extern VendorHandle *feature_handle;\n"
                "void feature_port(void);\n",
                encoding="utf-8",
            )
            manifest = valid_manifest(c_ast=True)
            manifest["type_exclusions"] = [
                {
                    "path": "src/adapter/vendor/**",
                    "owner": "adapter",
                    "classification": "vendor",
                    "source": "Fixture vendor package.",
                    "reason": "Adapter-private external declaration.",
                }
            ]
            diagnostics, _ = analyze(
                manifest, root / "architecture" / "manifest.yaml", root
            )
        self.assertTrue(any(item.rule_id == "CTYPE004" for item in diagnostics))

    def test_functional_external_include_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            (root / "src" / "feature" / "feature.c").write_text(
                "#include <stm32f10x.h>\nvoid feature_init(void) {}\n",
                encoding="utf-8",
            )
            diagnostics, _ = analyze(
                valid_manifest(c_ast=True), root / "architecture" / "manifest.yaml", root
            )
        self.assertTrue(any(item.rule_id == "CFUN001" for item in diagnostics))


class ToolingTests(unittest.TestCase):
    def test_realtime_study_markdown_is_human_readable_and_deterministic(self) -> None:
        manifest = realtime_design_manifest()
        documents = render_documents(manifest)
        path = Path("generated/realtime-study-feature-task-study.md")
        self.assertIn(path, documents)
        report = documents[path]
        for expected in (
            "候選方案比較",
            "排程器相容性",
            "每核心 RM 排序",
            "ISR 干擾模型",
            "Task RTA",
            "WCET 上界證據",
            "Queue／Notification 與跨核心成本",
            "端到端 Flow",
            "Runtime 證據綁定",
            "design-budget",
            "方案核准人",
            "100 Hz",
            "candidate-a",
            "candidate-b",
        ):
            self.assertIn(expected, report)
        self.assertIn(
            "generated/realtime-study-feature-task-study.md",
            documents[Path("ARCHITECTURE.md")],
        )
        self.assertIn(
            "realtime-study-feature-task-study.md",
            documents[Path("generated/execution-candidate-a.md")],
        )
        self.assertEqual(documents, render_documents(copy.deepcopy(manifest)))

    def test_soft_realtime_report_contains_risk_and_slo_plan(self) -> None:
        manifest = realtime_design_manifest()
        manifest["workloads"][0]["timing_class"] = "soft-real-time"
        manifest["workloads"][0]["budgets"] = [
            {
                "metric": "latency-p99",
                "operator": "<=",
                "threshold": 10_000_000,
                "unit": "ns",
                "method": "percentile",
            },
            {
                "metric": "deadline-miss-rate",
                "operator": "<=",
                "threshold": 0.001,
                "unit": "ratio",
                "method": "runtime-evidence",
            },
        ]
        manifest["execution_units"][0]["realtime_task"][
            "relative_deadline_ns"
        ] = 100_000
        manifest["realtime_scheduling_studies"][0]["soft_acceptance_plans"] = [
            {
                "workload": "feature-workload",
                "validation_plan_path": "validation/soft-slo-plan.md",
                "evidence_format": "JSON percentile and miss-rate summary",
                "risk_approval": {
                    "approved_by": "Fixture Owner",
                    "approval_date": "2026-07-30",
                    "approval_reference": "fixture-soft-risk-review",
                },
            }
        ]
        report = render_documents(manifest)[
            Path("generated/realtime-study-feature-task-study.md")
        ]
        for expected in (
            "`soft-real-time`",
            "`rate-monotonic-rta`",
            "排程器相容性",
            "`SOFT_RISK`",
            "Soft SLO 驗證計畫",
            "validation/soft-slo-plan.md",
            "fixture-soft-risk-review",
        ):
            self.assertIn(expected, report)

    def test_realtime_study_markdown_participates_in_stale_checks(self) -> None:
        manifest = realtime_design_manifest()
        with tempfile.TemporaryDirectory() as directory:
            architecture = Path(directory) / "architecture"
            architecture.mkdir()
            manifest_path = architecture / "manifest.yaml"
            manifest_path.write_text(
                yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
            )
            documents = render_documents(manifest)
            for relative, content in documents.items():
                destination = architecture / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
            report_path = (
                architecture
                / "generated"
                / "realtime-study-feature-task-study.md"
            )
            report_path.write_text(
                report_path.read_text(encoding="utf-8") + "\nmanual edit\n",
                encoding="utf-8",
            )
            diagnostics = compare_documents(manifest, manifest_path)
        self.assertTrue(
            any(
                rule == "DOC002"
                and location == "generated/realtime-study-feature-task-study.md"
                for rule, location, _ in diagnostics
            )
        )

    def test_realtime_study_markdown_missing_and_obsolete_files_are_detected(self) -> None:
        manifest = realtime_design_manifest()
        with tempfile.TemporaryDirectory() as directory:
            architecture = Path(directory) / "architecture"
            architecture.mkdir()
            manifest_path = architecture / "manifest.yaml"
            manifest_path.write_text(
                yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
            )
            documents = render_documents(manifest)
            for relative, content in documents.items():
                destination = architecture / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
            expected_report = (
                architecture
                / "generated"
                / "realtime-study-feature-task-study.md"
            )
            expected_report.unlink()
            obsolete_report = (
                architecture / "generated" / "realtime-study-obsolete.md"
            )
            obsolete_report.write_text(
                "<!-- GENERATED BY govern-modular-event-architecture; DO NOT EDIT -->\n",
                encoding="utf-8",
            )
            diagnostics = compare_documents(manifest, manifest_path)
        self.assertIn(
            (
                "DOC001",
                "generated/realtime-study-feature-task-study.md",
                "generated architecture document is missing",
            ),
            diagnostics,
        )
        self.assertIn(
            (
                "DOC003",
                "generated/realtime-study-obsolete.md",
                "obsolete generated architecture document exists",
            ),
            diagnostics,
        )

    def test_bootstrap_installs_only_schema_v2_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "spec.yaml"
            spec.write_text(
                yaml.safe_dump(valid_manifest(), sort_keys=False),
                encoding="utf-8",
            )
            project = root / "project"
            written = bootstrap(project, spec)
            names = {path.name for path in written}
            self.assertIn("schema_v2.py", names)
            self.assertIn("realtime_analysis.py", names)
            self.assertIn("type_catalog.py", names)
            self.assertIn("state_catalog.py", names)
            self.assertIn("source_sets.py", names)
            self.assertIn("boundary_catalog.py", names)
            self.assertIn("ast_analyzer.py", names)
            self.assertIn("architecture_cli.py", names)
            self.assertIn("python_analyzer.py", names)
            self.assertIn("governance_adoption.py", names)
            self.assertIn("adoption.yaml", names)
            self.assertIn("baseline.yaml", names)
            self.assertIn("adoption-readiness.md", names)
            self.assertIn("adoption-readiness.json", names)
            self.assertIn("requirements.txt", names)
            self.assertNotIn("toolchain-lock.yaml", names)
            self.assertIn("libclang_toolchain_adapter.py", names)
            self.assertIn("libclang_toolchain_contract.py", names)
            self.assertIn(
                "clang==20.1.5",
                (project / "tools" / "architecture" / "requirements.txt").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertNotIn("migrate_manifest.py", names)
            self.assertFalse((project / "src").exists())
            self.assertFalse(
                (project / "tools" / "architecture" / "schema_v1_2.py").exists()
            )
            manifest_path = project / "architecture" / "manifest.yaml"
            checker = subprocess.run(
                [
                    sys.executable,
                    str(project / "tools" / "architecture" / "architecture_cli.py"),
                    "gate",
                    "--phase",
                    "design",
                    "--manifest",
                    str(manifest_path),
                ],
                cwd=project,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, checker.returncode, checker.stdout + checker.stderr)
            old_command = subprocess.run(
                [
                    sys.executable,
                    str(project / "tools" / "architecture" / "c_analyzer.py"),
                    "--help",
                ],
                cwd=project,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, old_command.returncode)
            self.assertIn("architecture_cli.py", old_command.stderr)

    def test_bootstrap_c_project_installs_toolchain_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "spec.yaml"
            spec.write_text(
                yaml.safe_dump(valid_manifest(c_ast=True), sort_keys=False),
                encoding="utf-8",
            )
            project = root / "project"
            written = bootstrap(project, spec)
            self.assertIn("toolchain-lock.yaml", {path.name for path in written})
            lock = yaml.safe_load(
                (project / "architecture" / "toolchain-lock.yaml").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                "20.1.1_20250829",
                lock["libclang_provider"]["version"],
            )

    def test_bootstrap_realtime_project_uses_single_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "spec.yaml"
            spec.write_text(
                yaml.safe_dump(realtime_design_manifest(), sort_keys=False),
                encoding="utf-8",
            )
            project = root / "project"
            bootstrap(project, spec)
            report = (
                project
                / "architecture"
                / "generated"
                / "realtime-study-feature-task-study.md"
            )
            self.assertTrue(report.is_file())
            for command in (
                [
                    sys.executable,
                    str(project / "tools" / "architecture" / "architecture_cli.py"),
                    "gate",
                    "--phase",
                    "design",
                    "--manifest",
                    str(project / "architecture" / "manifest.yaml"),
                ],
            ):
                result = subprocess.run(
                    command,
                    cwd=project,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(
                    0, result.returncode, result.stdout + result.stderr
                )

    def test_generated_views_match_skill_manifest(self) -> None:
        manifest_path = SKILL_ROOT / "architecture" / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual([], compare_documents(manifest, manifest_path))

    def test_fanout_continues_after_failure(self) -> None:
        calls: list[str] = []

        def first(_: object) -> None:
            calls.append("first")
            raise RuntimeError("failed")

        def second(_: object) -> None:
            calls.append("second")

        failures = publish_all(object(), [first, second])
        self.assertEqual(["first", "second"], calls)
        self.assertEqual(1, len(failures))


if __name__ == "__main__":
    unittest.main()
