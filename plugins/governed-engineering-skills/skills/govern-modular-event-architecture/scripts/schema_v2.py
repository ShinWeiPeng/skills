"""Schema 2.0 type-governed architecture and execution validation."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from check_architecture import (
    BANNED_AI_APPROVERS,
    DESCRIPTION_SCHEMA_VERSION,
    DESCRIPTION_STANDARD_VERSION,
    SCHEMA_VERSION,
    STANDARD_VERSION,
    Diagnostic,
    ManifestError,
    _diag,
    _is_nonempty_string,
    load_yaml,
)
from schema_description import (
    ID_PATTERN,
    PROTECTED_RULES,
    validate_description_manifest,
)
from type_catalog import validate_type_catalog
from state_catalog import validate_state_catalog
from boundary_catalog import validate_boundary_catalog
from source_sets import validate_manifest_source_paths, validate_source_sets


TIMING_CLASSES = {"hard-real-time", "soft-real-time", "best-effort"}
PROFILE_STATUSES = {"legacy-review", "proposed", "accepted", "superseded"}
UNIT_KINDS = {"interrupt", "event-loop", "dedicated-task", "worker-pool", "async-executor", "process"}
OVERLOAD_POLICIES = {"reject", "backpressure", "drop", "coalesce", "degrade", "fail-safe"}
OPTIMIZATION_TIERS = {"tier-0", "tier-1", "tier-2"}
REQUIRED_TIER1_FIELDS = {
    "working_set",
    "memory_traffic",
    "branch_predictability",
    "simd_dependencies",
    "parallelism",
    "blocking_bounds",
}
REQUIRED_ACCEPTED_TARGET_FIELDS = {"platform", "cpu", "runtime", "compiler"}


def _list(value: Any, diagnostics: list[Diagnostic], rule: str, location: str) -> list[Any]:
    if not isinstance(value, list):
        _diag(diagnostics, rule, location, "must be a list", configuration=True)
        return []
    return value


def _mapping(value: Any, diagnostics: list[Diagnostic], rule: str, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _diag(diagnostics, rule, location, "must be a mapping", configuration=True)
        return {}
    return value


def _nonempty_list(value: Any, diagnostics: list[Diagnostic], rule: str, location: str) -> list[Any]:
    parsed = _list(value, diagnostics, rule, location)
    if not parsed:
        _diag(diagnostics, rule, location, "must not be empty", configuration=True)
    return parsed


def _index(
    values: list[Any],
    diagnostics: list[Diagnostic],
    rule: str,
    location: str,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(values):
        item_location = f"{location}[{index}]"
        item = _mapping(raw, diagnostics, rule, item_location)
        identifier = item.get("id")
        if not _is_nonempty_string(identifier) or not ID_PATTERN.fullmatch(str(identifier)):
            _diag(diagnostics, rule, f"{item_location}.id", "must be a stable lowercase identifier", configuration=True)
            continue
        if str(identifier) in result:
            _diag(diagnostics, rule, f"{item_location}.id", f"duplicate ID {identifier!r}", configuration=True)
            continue
        result[str(identifier)] = item
    return result


def _refs(
    values: Any,
    known: dict[str, Any],
    diagnostics: list[Diagnostic],
    rule: str,
    location: str,
    *,
    required: bool = False,
) -> list[str]:
    parsed = _list(values, diagnostics, rule, location)
    if required and not parsed:
        _diag(diagnostics, rule, location, "must not be empty", configuration=True)
    result: list[str] = []
    for index, value in enumerate(parsed):
        if not _is_nonempty_string(value):
            _diag(diagnostics, rule, f"{location}[{index}]", "must be a non-empty ID", configuration=True)
        elif str(value) not in known:
            _diag(diagnostics, rule, f"{location}[{index}]", f"unknown reference {value!r}")
        else:
            result.append(str(value))
    return result


def _has_metric(workload: dict[str, Any], metric: str) -> bool:
    return any(isinstance(item, dict) and item.get("metric") == metric for item in workload.get("budgets", []))


def _valid_human_approval(approval: Any) -> bool:
    if not isinstance(approval, dict):
        return False
    words = set(re.findall(r"[a-z]+", str(approval.get("approved_by", "")).lower()))
    return (
        _is_nonempty_string(approval.get("approved_by"))
        and _is_nonempty_string(approval.get("approval_date"))
        and _is_nonempty_string(approval.get("approval_reference"))
        and not words.intersection(BANNED_AI_APPROVERS)
    )


def _apply_governance(
    diagnostics: list[Diagnostic],
    data: dict[str, Any],
    manifest_path: Path,
    baseline_path: Path | None,
    previous_baseline_path: Path | None,
) -> None:
    valid_exceptions: list[dict[str, Any]] = []
    for raw in data.get("adr_exceptions", []):
        if not isinstance(raw, dict) or raw.get("status") != "accepted":
            continue
        words = set(re.findall(r"[a-z]+", str(raw.get("approved_by", "")).lower()))
        adr_path = manifest_path.parent / str(raw.get("adr", ""))
        if (
            _is_nonempty_string(raw.get("rule_id"))
            and _is_nonempty_string(raw.get("scope"))
            and _is_nonempty_string(raw.get("approval_reference"))
            and not words.intersection(BANNED_AI_APPROVERS)
            and adr_path.is_file()
        ):
            valid_exceptions.append(raw)

    baseline_entries: set[tuple[str, str]] = set()
    if baseline_path is not None:
        try:
            baseline = load_yaml(baseline_path)
            if baseline.get("schema_version") != SCHEMA_VERSION:
                _diag(diagnostics, "BAS001", str(baseline_path), "baseline schema version mismatch", configuration=True)
            entries = baseline.get("violations")
            if not isinstance(entries, list):
                _diag(diagnostics, "BAS002", str(baseline_path), "violations must be a list", configuration=True)
            else:
                for entry in entries:
                    if isinstance(entry, dict) and _is_nonempty_string(entry.get("rule_id")) and _is_nonempty_string(entry.get("location")):
                        baseline_entries.add((str(entry["rule_id"]), str(entry["location"])))
                    else:
                        _diag(diagnostics, "BAS003", str(baseline_path), "invalid baseline entry", configuration=True)
        except ManifestError as exc:
            _diag(diagnostics, "BAS000", str(baseline_path), str(exc), configuration=True)

    if previous_baseline_path is not None:
        try:
            previous = load_yaml(previous_baseline_path)
            previous_entries = {
                (str(item["rule_id"]), str(item["location"]))
                for item in previous.get("violations", [])
                if isinstance(item, dict) and "rule_id" in item and "location" in item
            }
            for rule_id, location in sorted(baseline_entries.difference(previous_entries)):
                _diag(diagnostics, "BAS004", f"{rule_id}:{location}", "baseline growth is forbidden")
        except ManifestError as exc:
            _diag(diagnostics, "BAS000", str(previous_baseline_path), str(exc), configuration=True)

    for diagnostic in diagnostics:
        if diagnostic.configuration or diagnostic.rule_id in PROTECTED_RULES or diagnostic.disposition != "active":
            continue
        if (diagnostic.rule_id, diagnostic.location) in baseline_entries:
            diagnostic.disposition = "baseline"
            continue
        for exception in valid_exceptions:
            if diagnostic.rule_id == exception["rule_id"] and diagnostic.location.startswith(str(exception["scope"])):
                diagnostic.disposition = f"adr:{exception['adr']}"
                break


def validate_manifest_v2(
    data: dict[str, Any],
    manifest_path: Path,
    baseline_path: Path | None = None,
    previous_baseline_path: Path | None = None,
    *,
    check_docs: bool = False,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if data.get("standard_version") != STANDARD_VERSION:
        _diag(diagnostics, "VER001", "standard_version", f"must equal {STANDARD_VERSION!r}", configuration=True)
    if data.get("schema_version") != SCHEMA_VERSION:
        _diag(diagnostics, "VER001", "schema_version", f"must equal {SCHEMA_VERSION!r}", configuration=True)

    projected = copy.deepcopy(data)
    projected["standard_version"] = DESCRIPTION_STANDARD_VERSION
    projected["schema_version"] = DESCRIPTION_SCHEMA_VERSION
    for field in (
        "workloads",
        "execution_profiles",
        "execution_units",
        "execution_mappings",
        "execution_channels",
        "data_access_profiles",
        "microarchitecture_profiles",
        "platform_variants",
    ):
        projected.pop(field, None)
    projected.pop("types", None)
    projected.pop("type_exclusions", None)
    projected.pop("state_objects", None)
    projected.pop("boundary_mappings", None)
    projected.pop("source_sets", None)
    diagnostics.extend(
        validate_description_manifest(projected, manifest_path, check_docs=False)
    )
    diagnostics.extend(validate_type_catalog(data, manifest_path))
    diagnostics.extend(validate_state_catalog(data, manifest_path))
    diagnostics.extend(validate_boundary_catalog(data, manifest_path))
    diagnostics.extend(validate_source_sets(data))
    diagnostics.extend(validate_manifest_source_paths(data))

    flows = {
        str(item.get("id")): item
        for item in data.get("flows", [])
        if isinstance(item, dict) and _is_nonempty_string(item.get("id"))
    }
    step_ids: dict[str, tuple[str, dict[str, Any]]] = {}
    for flow_id, flow in flows.items():
        for index, step in enumerate(flow.get("steps", [])):
            location = f"{flow_id}.steps[{index}]"
            step_id = step.get("id") if isinstance(step, dict) else None
            if not _is_nonempty_string(step_id) or not ID_PATTERN.fullmatch(str(step_id)):
                _diag(diagnostics, "EXE001", f"{location}.id", "schema 2.0 requires a stable step ID", configuration=True)
            elif str(step_id) in step_ids:
                _diag(diagnostics, "EXE002", f"{location}.id", f"duplicate flow step ID {step_id!r}", configuration=True)
            else:
                step_ids[str(step_id)] = (flow_id, step)

    workloads = _index(_list(data.get("workloads"), diagnostics, "EXE003", "workloads"), diagnostics, "EXE003", "workloads")
    profiles = _index(_list(data.get("execution_profiles"), diagnostics, "EXE004", "execution_profiles"), diagnostics, "EXE004", "execution_profiles")
    units = _index(_list(data.get("execution_units"), diagnostics, "EXE005", "execution_units"), diagnostics, "EXE005", "execution_units")
    mappings = _index(_list(data.get("execution_mappings"), diagnostics, "EXE006", "execution_mappings"), diagnostics, "EXE006", "execution_mappings")
    channels = _index(_list(data.get("execution_channels"), diagnostics, "EXE007", "execution_channels"), diagnostics, "EXE007", "execution_channels")
    data_profiles = _index(_list(data.get("data_access_profiles"), diagnostics, "PERF001", "data_access_profiles"), diagnostics, "PERF001", "data_access_profiles")
    micro_profiles = _index(_list(data.get("microarchitecture_profiles"), diagnostics, "PERF002", "microarchitecture_profiles"), diagnostics, "PERF002", "microarchitecture_profiles")
    variants = _index(_list(data.get("platform_variants"), diagnostics, "EXE008", "platform_variants"), diagnostics, "EXE008", "platform_variants")

    for workload_id, workload in workloads.items():
        flow_id = workload.get("flow")
        if flow_id not in flows:
            _diag(diagnostics, "EXE010", f"{workload_id}.flow", f"unknown Flow {flow_id!r}")
        referenced_steps = _refs(workload.get("steps"), step_ids, diagnostics, "EXE011", f"{workload_id}.steps", required=True)
        for step_id in referenced_steps:
            if flow_id in flows and step_ids[step_id][0] != flow_id:
                _diag(diagnostics, "EXE012", f"{workload_id}.steps", f"step {step_id!r} belongs to another Flow")
        timing_class = workload.get("timing_class")
        if timing_class not in TIMING_CLASSES:
            _diag(diagnostics, "EXE013", f"{workload_id}.timing_class", f"must be one of {sorted(TIMING_CLASSES)}", configuration=True)
        _mapping(workload.get("activation"), diagnostics, "EXE014", f"{workload_id}.activation")
        _mapping(workload.get("data"), diagnostics, "EXE015", f"{workload_id}.data")
        budgets = _list(workload.get("budgets"), diagnostics, "PERF003", f"{workload_id}.budgets")
        for index, raw in enumerate(budgets):
            budget = _mapping(raw, diagnostics, "PERF003", f"{workload_id}.budgets[{index}]")
            for key in ("metric", "operator", "threshold", "unit", "method"):
                if not _is_nonempty_string(budget.get(key)) and not (key == "threshold" and isinstance(budget.get(key), (int, float))):
                    _diag(diagnostics, "PERF003", f"{workload_id}.budgets[{index}].{key}", "is required", configuration=True)
        if timing_class == "hard-real-time":
            if not _has_metric(workload, "deadline") or not _has_metric(workload, "deadline-miss-count"):
                _diag(diagnostics, "PERF004", workload_id, "hard-real-time workload requires deadline and deadline-miss-count budgets")
            analysis = _mapping(workload.get("tier1_analysis"), diagnostics, "PERF005", f"{workload_id}.tier1_analysis")
            for field in sorted(REQUIRED_TIER1_FIELDS):
                if not _is_nonempty_string(analysis.get(field)):
                    _diag(diagnostics, "PERF005", f"{workload_id}.tier1_analysis.{field}", "hard-real-time analysis is required")
        if timing_class == "soft-real-time":
            has_percentile = any(
                isinstance(item, dict) and item.get("method") == "percentile"
                for item in workload.get("budgets", [])
            )
            if not has_percentile or not _has_metric(workload, "deadline-miss-rate"):
                _diag(diagnostics, "PERF006", workload_id, "soft-real-time workload requires percentile and deadline-miss-rate budgets")

    covered_flows = {str(item.get("flow")) for item in workloads.values()}
    for flow_id in flows:
        if flow_id not in covered_flows:
            _diag(diagnostics, "EXE016", flow_id, "schema 1.2 requires at least one workload for every Flow")

    for profile_id, profile in profiles.items():
        status = profile.get("status")
        if status not in PROFILE_STATUSES:
            _diag(diagnostics, "EXE020", f"{profile_id}.status", f"must be one of {sorted(PROFILE_STATUSES)}", configuration=True)
        target = _mapping(profile.get("target"), diagnostics, "EXE021", f"{profile_id}.target")
        if status == "accepted":
            for field in REQUIRED_ACCEPTED_TARGET_FIELDS:
                if not _is_nonempty_string(target.get(field)) or "TODO" in str(target.get(field)).upper():
                    _diag(diagnostics, "EXE022", f"{profile_id}.target.{field}", "accepted profile requires a confirmed value")
            if not isinstance(target.get("cache_topology"), dict) or not target.get("cache_topology"):
                _diag(diagnostics, "EXE023", f"{profile_id}.target.cache_topology", "accepted profile requires confirmed cache topology")
            if not isinstance(target.get("scheduler_capabilities"), list) or not target.get("scheduler_capabilities"):
                _diag(diagnostics, "EXE024", f"{profile_id}.target.scheduler_capabilities", "accepted profile requires scheduler capabilities")
            if not _valid_human_approval(profile.get("approval")):
                _diag(diagnostics, "EXE025", f"{profile_id}.approval", "accepted profile requires non-AI human approval metadata")

    for unit_id, unit in units.items():
        profile_id = unit.get("profile")
        if profile_id not in profiles:
            _diag(diagnostics, "EXE030", f"{unit_id}.profile", f"unknown execution profile {profile_id!r}")
        if unit.get("kind") not in UNIT_KINDS:
            _diag(diagnostics, "EXE031", f"{unit_id}.kind", f"must be one of {sorted(UNIT_KINDS)}", configuration=True)
        if not isinstance(unit.get("concurrency"), int) or unit.get("concurrency", 0) <= 0:
            _diag(diagnostics, "EXE032", f"{unit_id}.concurrency", "must be a positive integer", configuration=True)
        for field in ("priority", "affinity", "resources", "blocking", "allocation"):
            if field not in unit:
                _diag(diagnostics, "EXE033", f"{unit_id}.{field}", "must be declared explicitly", configuration=True)

    for mapping_id, mapping in mappings.items():
        profile_id = mapping.get("profile")
        workload_id = mapping.get("workload")
        if profile_id not in profiles:
            _diag(diagnostics, "EXE040", f"{mapping_id}.profile", f"unknown execution profile {profile_id!r}")
        if workload_id not in workloads:
            _diag(diagnostics, "EXE041", f"{mapping_id}.workload", f"unknown workload {workload_id!r}")
        mapped_units = _refs(mapping.get("units"), units, diagnostics, "EXE042", f"{mapping_id}.units", required=True)
        mapped_steps = _refs(mapping.get("steps"), step_ids, diagnostics, "EXE043", f"{mapping_id}.steps", required=True)
        if workload_id in workloads:
            allowed_steps = set(workloads[workload_id].get("steps", []))
            for step_id in mapped_steps:
                if step_id not in allowed_steps:
                    _diag(diagnostics, "EXE044", f"{mapping_id}.steps", f"step {step_id!r} is outside workload {workload_id!r}")
        for unit_id in mapped_units:
            if profile_id in profiles and units[unit_id].get("profile") != profile_id:
                _diag(diagnostics, "EXE045", f"{mapping_id}.units", f"unit {unit_id!r} belongs to another profile")
        for field in ("serialization", "reentrant", "activation", "wcet"):
            if field not in mapping:
                _diag(diagnostics, "EXE046", f"{mapping_id}.{field}", "must be declared explicitly", configuration=True)

    ports = {str(item.get("id")): item for item in data.get("ports", []) if isinstance(item, dict)}
    events = {str(item.get("id")): item for item in data.get("events", []) if isinstance(item, dict)}
    contract_refs = {**ports, **events}
    for channel_id, channel in channels.items():
        profile_id = channel.get("profile")
        if profile_id not in profiles:
            _diag(diagnostics, "EXE050", f"{channel_id}.profile", f"unknown execution profile {profile_id!r}")
        for field in ("from_unit", "to_unit"):
            unit_id = channel.get(field)
            if unit_id not in units:
                _diag(diagnostics, "EXE051", f"{channel_id}.{field}", f"unknown unit {unit_id!r}")
            elif profile_id in profiles and units[unit_id].get("profile") != profile_id:
                _diag(diagnostics, "EXE052", f"{channel_id}.{field}", "unit belongs to another profile")
        _refs(channel.get("contract_refs"), contract_refs, diagnostics, "EXE053", f"{channel_id}.contract_refs", required=True)
        if not isinstance(channel.get("capacity"), int) or channel.get("capacity", -1) < 0:
            _diag(diagnostics, "EXE054", f"{channel_id}.capacity", "must be a non-negative integer", configuration=True)
        for field in ("ordering", "copy_policy", "timeout_ms"):
            if field not in channel:
                _diag(diagnostics, "EXE055", f"{channel_id}.{field}", "must be declared explicitly", configuration=True)
        if not isinstance(channel.get("timeout_ms"), (int, float)) or isinstance(channel.get("timeout_ms"), bool) or channel.get("timeout_ms", -1) < 0:
            _diag(diagnostics, "EXE057", f"{channel_id}.timeout_ms", "must be a non-negative number", configuration=True)
        if channel.get("overload") not in OVERLOAD_POLICIES:
            _diag(diagnostics, "EXE056", f"{channel_id}.overload", f"must be one of {sorted(OVERLOAD_POLICIES)}")

    for data_id, profile in data_profiles.items():
        if profile.get("profile") not in profiles:
            _diag(diagnostics, "PERF010", f"{data_id}.profile", "unknown execution profile")
        if profile.get("workload") not in workloads:
            _diag(diagnostics, "PERF011", f"{data_id}.workload", "unknown workload")
        if profile.get("tier") not in OPTIMIZATION_TIERS:
            _diag(diagnostics, "PERF012", f"{data_id}.tier", f"must be one of {sorted(OPTIMIZATION_TIERS)}")
        for field in (
            "element_size_bytes",
            "layout",
            "active_working_set_bytes",
            "stride_bytes",
            "reuse",
            "alignment_bytes",
            "sharing",
            "cache_target",
            "candidates",
        ):
            if field not in profile:
                _diag(diagnostics, "PERF013", f"{data_id}.{field}", "must be declared explicitly", configuration=True)
        for field in ("element_size_bytes", "active_working_set_bytes", "stride_bytes", "alignment_bytes"):
            if not isinstance(profile.get(field), int) or isinstance(profile.get(field), bool) or profile.get(field, 0) <= 0:
                _diag(diagnostics, "PERF015", f"{data_id}.{field}", "must be a positive integer", configuration=True)
        if not isinstance(profile.get("candidates"), list) or not profile.get("candidates"):
            _diag(diagnostics, "PERF016", f"{data_id}.candidates", "must be a non-empty list", configuration=True)
        if profile.get("tier") == "tier-2" and (not profile.get("portable_baseline") or not profile.get("benchmark")):
            _diag(diagnostics, "PERF014", data_id, "tier-2 data optimization requires portable_baseline and benchmark")

    for micro_id, profile in micro_profiles.items():
        if profile.get("profile") not in profiles:
            _diag(diagnostics, "PERF020", f"{micro_id}.profile", "unknown execution profile")
        if profile.get("workload") not in workloads:
            _diag(diagnostics, "PERF021", f"{micro_id}.workload", "unknown workload")
        if profile.get("tier") not in OPTIMIZATION_TIERS:
            _diag(diagnostics, "PERF022", f"{micro_id}.tier", f"must be one of {sorted(OPTIMIZATION_TIERS)}")
        for field in ("branches", "simd_eligibility", "compiler", "compiler_flags", "vectorization_report", "pgo", "lto"):
            if field not in profile:
                _diag(diagnostics, "PERF023", f"{micro_id}.{field}", "must be declared explicitly", configuration=True)
        if profile.get("tier") == "tier-2" and (not profile.get("portable_baseline") or not profile.get("benchmark")):
            _diag(diagnostics, "PERF024", micro_id, "tier-2 microarchitecture optimization requires portable_baseline and benchmark")

    for variant_id, variant in variants.items():
        profile_id = variant.get("profile")
        if profile_id not in profiles:
            _diag(diagnostics, "EXE060", f"{variant_id}.profile", "unknown execution profile")
        _refs(variant.get("units"), units, diagnostics, "EXE061", f"{variant_id}.units")
        _refs(variant.get("data_access_profiles"), data_profiles, diagnostics, "EXE062", f"{variant_id}.data_access_profiles")
        _refs(variant.get("microarchitecture_profiles"), micro_profiles, diagnostics, "EXE063", f"{variant_id}.microarchitecture_profiles")
        if not isinstance(variant.get("parameters"), dict):
            _diag(diagnostics, "EXE064", f"{variant_id}.parameters", "must be a mapping", configuration=True)
        if variant.get("release") is True and (profile_id not in profiles or profiles[profile_id].get("status") != "accepted"):
            _diag(diagnostics, "EXE065", variant_id, "release variant must reference an accepted execution profile")

    if check_docs:
        from render_architecture import compare_documents

        for rule_id, location, message in compare_documents(data, manifest_path):
            _diag(diagnostics, rule_id, location, message)

    _apply_governance(diagnostics, data, manifest_path, baseline_path, previous_baseline_path)
    return diagnostics
