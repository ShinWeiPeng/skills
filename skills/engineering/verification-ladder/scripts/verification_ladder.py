#!/usr/bin/env python3
"""Validate and evaluate a project verification ladder matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = "1.0"
LAYER_ORDER = (
    "module-contract",
    "sil",
    "adapter-contract",
    "pil",
    "hil",
    "system-soak",
)
TAXONOMY = {
    "contract_dimensions": {
        "input-output-units",
        "state-transition",
        "call-order",
        "error-reset",
        "batch-capacity",
        "throughput-backlog",
        "latency-resource",
        "external-port",
    },
    "execution_changes": {
        "target-code",
        "core-mapping",
        "scheduler",
        "interrupt",
        "peripheral-traffic",
        "synchronization",
        "competing-workload",
        "physical-hardware",
        "transport-protocol",
        "logging",
    },
    "evidence_claims": {
        "host-semantics",
        "adapter-conformance",
        "controlled-target-cost",
        "production-timing",
        "physical-integration",
        "system-stability",
        "hard-real-time",
        "soft-real-time",
    },
}
UNIVERSAL_LAYERS = {
    "input-output-units": {"module-contract"},
    "state-transition": {"module-contract"},
    "call-order": {"module-contract"},
    "error-reset": {"module-contract"},
    "batch-capacity": {"module-contract"},
    "throughput-backlog": {"module-contract"},
    "latency-resource": {"module-contract"},
    "external-port": {"module-contract", "adapter-contract"},
    "target-code": {"pil"},
    "core-mapping": {"hil"},
    "scheduler": {"hil"},
    "interrupt": {"hil"},
    "peripheral-traffic": {"hil"},
    "synchronization": {"hil"},
    "competing-workload": {"hil"},
    "physical-hardware": {"hil"},
    "transport-protocol": {"hil"},
    "logging": {"hil"},
    "host-semantics": {"module-contract"},
    "adapter-conformance": {"adapter-contract"},
    "controlled-target-cost": {"pil"},
    "production-timing": {"hil"},
    "physical-integration": {"hil"},
    "system-stability": {"system-soak"},
    "hard-real-time": {"pil", "hil"},
    "soft-real-time": {"pil", "hil"},
}
EVIDENCE_AUTHORITY = {
    "host-semantics": "module-contract",
    "adapter-conformance": "adapter-contract",
    "controlled-target-cost": "pil",
    "production-timing": "hil",
    "physical-integration": "hil",
    "system-stability": "system-soak",
    "hard-real-time": "hil",
    "soft-real-time": "hil",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return value


def _document_ids(document: dict[str, Any]) -> set[str]:
    keys = (
        "modules",
        "ports",
        "events",
        "flows",
        "workloads",
        "execution_profiles",
        "execution_units",
        "execution_channels",
        "data_access_profiles",
        "microarchitecture_profiles",
        "platform_variants",
    )
    return {
        item["id"]
        for key in keys
        for item in document.get(key, [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _duplicate_document_ids(document: dict[str, Any]) -> set[str]:
    keys = (
        "modules",
        "ports",
        "events",
        "flows",
        "workloads",
        "execution_profiles",
        "execution_units",
        "execution_channels",
        "data_access_profiles",
        "microarchitecture_profiles",
        "platform_variants",
    )
    seen: set[str] = set()
    duplicates: set[str] = set()
    for key in keys:
        for item in document.get(key, []):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            identity = item["id"]
            if identity in seen:
                duplicates.add(identity)
            seen.add(identity)
    return duplicates


def _on_device_ids(
    document: dict[str, Any], errors: list[str]
) -> tuple[set[str], set[str]]:
    scenarios: set[str] = set()
    for item in document.get("scenarios", []):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        scenario = item["id"]
        if scenario in scenarios:
            errors.append(f"duplicate on-device scenario id {scenario!r}")
        scenarios.add(scenario)
    architecture = document.get("architecture", {})
    profile = (
        architecture.get("execution_profile")
        if isinstance(architecture, dict)
        else None
    )
    return scenarios, {profile} if isinstance(profile, str) and profile else set()


def _list_of_strings(value: Any, path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        errors.append(f"{path} must be a list of non-empty strings")
        return []
    return value


def _validate_layer(name: str, value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"layers.{name} must be a mapping")
        return
    allowed_fields = {
        "scope",
        "inputs",
        "metrics",
        "thresholds",
        "evidence",
        "stop_condition",
        "next_layers",
    }
    errors.extend(
        f"unknown layers.{name} field {field!r}"
        for field in sorted(set(value) - allowed_fields)
    )
    for field in ("scope", "evidence", "stop_condition"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            errors.append(f"layers.{name}.{field} is required")
    for field in ("inputs", "metrics", "next_layers"):
        _list_of_strings(value.get(field), f"layers.{name}.{field}", errors)
    thresholds = value.get("thresholds")
    if not isinstance(thresholds, dict):
        errors.append(f"layers.{name}.thresholds must be a mapping")
    else:
        errors.extend(
            f"unknown layers.{name}.thresholds field {field!r}"
            for field in sorted(set(thresholds) - {"pass", "fail", "blocked"})
        )
        for verdict in ("pass", "fail", "blocked"):
            if (
                not isinstance(thresholds.get(verdict), str)
                or not thresholds[verdict].strip()
            ):
                errors.append(f"layers.{name}.thresholds.{verdict} is required")


def validate_matrix(
    matrix: dict[str, Any], architecture: dict[str, Any], on_device: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    allowed_root_fields = {
        "schema_version",
        "architecture_manifest",
        "on_device_profile",
        "layers",
        "rules",
        "not_applicable",
    }
    errors.extend(
        f"unknown matrix field {field!r}"
        for field in sorted(set(matrix) - allowed_root_fields)
    )
    if str(matrix.get("schema_version")) != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    architecture_ids = _document_ids(architecture)
    errors.extend(
        f"duplicate architecture id {identity!r}"
        for identity in sorted(_duplicate_document_ids(architecture))
    )
    scenario_ids, profile_ids = _on_device_ids(on_device, errors)
    layers = matrix.get("layers")
    if not isinstance(layers, dict):
        errors.append("layers must be a mapping")
        layers = {}
    for name, value in layers.items():
        if name not in LAYER_ORDER:
            errors.append(f"unknown layer {name!r}")
        _validate_layer(name, value, errors)
    rules = matrix.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty list")
        return errors
    seen: set[str] = set()
    allowed_rule_fields = {
        "id",
        "architecture_refs",
        "contract_dimensions",
        "execution_changes",
        "evidence_claims",
        "layers",
        "on_device_scenarios",
        "execution_profiles",
    }
    for index, rule in enumerate(rules):
        path = f"rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{path} must be a mapping")
            continue
        errors.extend(
            f"unknown {path} field {field!r}"
            for field in sorted(set(rule) - allowed_rule_fields)
        )
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not rule_id:
            errors.append(f"{path}.id is required")
        elif rule_id in seen:
            errors.append(f"duplicate rule id {rule_id!r}")
        else:
            seen.add(rule_id)
        refs = _list_of_strings(
            rule.get("architecture_refs"), f"{path}.architecture_refs", errors
        )
        for ref in refs:
            if ref not in architecture_ids:
                errors.append(
                    f"{path}.architecture_refs contains unresolved id {ref!r}"
                )
        for field, allowed in TAXONOMY.items():
            values = _list_of_strings(rule.get(field), f"{path}.{field}", errors)
            for value in values:
                if value not in allowed:
                    errors.append(f"{path}.{field} contains unknown value {value!r}")
        selected = _list_of_strings(rule.get("layers"), f"{path}.layers", errors)
        for layer in selected:
            if layer not in layers:
                errors.append(f"{path}.layers references undefined layer {layer!r}")
        scenarios = _list_of_strings(
            rule.get("on_device_scenarios"), f"{path}.on_device_scenarios", errors
        )
        for scenario in scenarios:
            if scenario not in scenario_ids:
                errors.append(
                    f"{path}.on_device_scenarios contains unresolved id {scenario!r}"
                )
        profiles = _list_of_strings(
            rule.get("execution_profiles"), f"{path}.execution_profiles", errors
        )
        for profile in profiles:
            if profile not in profile_ids or profile not in architecture_ids:
                errors.append(
                    f"{path}.execution_profiles contains unresolved id {profile!r}"
                )
        if set(selected) & {"pil", "hil", "system-soak"}:
            if not matrix.get("on_device_profile"):
                errors.append(
                    f"{path} selects a device layer without on_device_profile"
                )
            if not scenarios:
                errors.append(f"{path} selects a device layer without a scenario")
            if not profiles:
                errors.append(
                    f"{path} selects a device layer without an execution profile"
                )

    not_applicable = matrix.get("not_applicable", [])
    if not isinstance(not_applicable, list):
        errors.append("not_applicable must be a list")
    else:
        seen_na: set[str] = set()
        for index, item in enumerate(not_applicable):
            path = f"not_applicable[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be a mapping")
                continue
            errors.extend(
                f"unknown {path} field {field!r}"
                for field in sorted(set(item) - {"layer", "rationale"})
            )
            layer = item.get("layer")
            if layer not in LAYER_ORDER:
                errors.append(f"{path}.layer must name a known layer")
            elif layer in seen_na:
                errors.append(f"duplicate not_applicable layer {layer!r}")
            else:
                seen_na.add(layer)
            rationale = item.get("rationale")
            if not isinstance(rationale, str) or not rationale.strip():
                errors.append(f"{path}.rationale is required")
            if layer in layers:
                errors.append(f"{path}.layer {layer!r} is also defined in layers")
    return errors


def validate_paths(
    matrix: dict[str, Any],
    matrix_path: Path,
    architecture_path: Path,
    on_device_path: Path | None,
) -> list[str]:
    errors: list[str] = []
    resolved_matrix = matrix_path.resolve()
    if (
        resolved_matrix.name != "verification-ladder.yaml"
        or resolved_matrix.parent.name != "validation"
    ):
        errors.append("matrix must be stored at validation/verification-ladder.yaml")
    project_root = resolved_matrix.parent.parent
    declared_architecture = matrix.get("architecture_manifest")
    if not isinstance(declared_architecture, str) or not declared_architecture:
        errors.append("architecture_manifest is required")
    elif (
        project_root / declared_architecture
    ).resolve() != architecture_path.resolve():
        errors.append("architecture_manifest does not resolve to the supplied manifest")
    declared_on_device = matrix.get("on_device_profile")
    if declared_on_device is None and on_device_path is not None:
        errors.append(
            "on_device_profile is required when an on-device profile is supplied"
        )
    elif declared_on_device is not None:
        if not isinstance(declared_on_device, str) or not declared_on_device:
            errors.append("on_device_profile must be a non-empty project-relative path")
        elif (
            on_device_path is None
            or (project_root / declared_on_device).resolve() != on_device_path.resolve()
        ):
            errors.append("on_device_profile does not resolve to the supplied profile")
    return errors


def _requested(args: argparse.Namespace) -> dict[str, set[str]]:
    return {
        "contract_dimensions": set(args.contract_dimension),
        "execution_changes": set(args.execution_change),
        "evidence_claims": set(args.evidence_claim),
    }


def plan(matrix: dict[str, Any], requested: dict[str, set[str]]) -> dict[str, Any]:
    problems: list[str] = []
    all_requested: set[str] = set()
    for field, values in requested.items():
        unknown = values - TAXONOMY[field]
        problems.extend(f"unknown {field} value {value!r}" for value in sorted(unknown))
        all_requested.update(values)
    activated: list[dict[str, Any]] = []
    mapped: set[str] = set()
    for rule in matrix["rules"]:
        matches = {
            value
            for field, values in requested.items()
            for value in values
            if value in rule[field]
        }
        if matches:
            activated.append(rule)
            mapped.update(matches)
    problems.extend(
        f"trigger {value!r} is not mapped by any project rule"
        for value in sorted(all_requested - mapped)
    )
    if problems:
        return {"status": "BLOCKED", "errors": problems}
    layers = {
        layer for value in all_requested for layer in UNIVERSAL_LAYERS.get(value, set())
    }
    for rule in activated:
        layers.update(rule["layers"])
    return {
        "status": "PASS",
        "required_layers": [layer for layer in LAYER_ORDER if layer in layers],
        "activated_rules": [rule["id"] for rule in activated],
    }


def assess_evidence(claim: str, passed_layers: set[str]) -> dict[str, Any]:
    authority = EVIDENCE_AUTHORITY.get(claim)
    if authority is None:
        return {"status": "BLOCKED", "errors": [f"unknown evidence claim {claim!r}"]}
    unknown = passed_layers - set(LAYER_ORDER)
    if unknown:
        return {
            "status": "BLOCKED",
            "required_authority": authority,
            "errors": [f"unknown passed layer {value!r}" for value in sorted(unknown)],
        }
    if authority not in passed_layers:
        return {
            "status": "BLOCKED",
            "claim": claim,
            "required_authority": authority,
            "supporting_layers": [
                layer for layer in LAYER_ORDER if layer in passed_layers
            ],
            "errors": [f"claim {claim!r} requires PASS evidence from {authority!r}"],
        }
    return {"status": "PASS", "claim": claim, "required_authority": authority}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    plan_parser = subparsers.add_parser("plan")
    for command_parser in (validate_parser, plan_parser):
        command_parser.add_argument("--matrix", required=True, type=Path)
        command_parser.add_argument("--architecture", required=True, type=Path)
        command_parser.add_argument("--on-device", type=Path)
    plan_parser.add_argument("--contract-dimension", action="append", default=[])
    plan_parser.add_argument("--execution-change", action="append", default=[])
    plan_parser.add_argument("--evidence-claim", action="append", default=[])
    evidence_parser = subparsers.add_parser("assess-evidence")
    evidence_parser.add_argument("--claim", required=True)
    evidence_parser.add_argument("--passed-layer", action="append", default=[])
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "assess-evidence":
        result = assess_evidence(args.claim, set(args.passed_layer))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "PASS" else 2
    try:
        matrix = _load_yaml(args.matrix)
        architecture = _load_yaml(args.architecture)
        on_device = _load_yaml(args.on_device) if args.on_device else {}
    except ValueError as exc:
        print(json.dumps({"status": "BLOCKED", "errors": [str(exc)]}, indent=2))
        return 2
    errors = validate_paths(matrix, args.matrix, args.architecture, args.on_device)
    errors.extend(validate_matrix(matrix, architecture, on_device))
    if errors:
        result = {"status": "BLOCKED", "errors": errors}
    elif args.command == "validate":
        result = {
            "status": "PASS",
            "rule_count": len(matrix["rules"]),
            "layer_contract_count": len(matrix["layers"]),
        }
    else:
        result = plan(matrix, _requested(args))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
