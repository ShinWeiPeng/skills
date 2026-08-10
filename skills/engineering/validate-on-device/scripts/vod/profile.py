from __future__ import annotations

import copy
import hashlib
import math
import re
from pathlib import Path
from statistics import NormalDist
from typing import Any

import yaml


PLATFORMS = {"windows", "linux", "ios", "bare-metal", "custom"}
PROVIDERS = {"etw-wpr", "perf-ftrace", "instruments-xctest", "structured-log"}
RISKS = {"passive", "build", "trace", "serial-open-reset", "flash", "reset", "actuate", "irreversible"}
CRITERIA = {"event_sequence", "hard_limit", "statistic", "native_metric", "observation"}
OPERATORS = {"<", "<=", ">", ">=", "=="}
STATISTIC_METHODS = {"field", "mean", "mean_upper_ci", "percentile", "wilson_upper"}
SECRET_WORDS = ("password", "token", "secret", "credential")
ROOT_KEYS = {"version", "target", "architecture", "transport", "actions", "scenarios", "bindings", "external_refs", "_project_root"}
ARCHITECTURE_KEYS = {"manifest", "manifest_sha256", "execution_profile"}
TARGET_KEYS = {"platform", "provider", "fallback", "native_max_bytes"}
TRANSPORT_KEYS = {"type", "binding", "baud", "dtr", "rts", "timeout_seconds", "max_bytes", "host", "port"}
ACTION_KEYS = {"executable", "args", "cwd", "risk", "timeout_seconds", "max_output_bytes", "bounded_artifact", "max_artifact_bytes", "idempotent", "trace_role"}
SCENARIO_KEYS = {"id", "title", "purpose", "phase", "evidence_mode", "max_duration_ms", "completion", "prerequisites", "architecture_refs", "forbidden_patterns", "criteria", "warmup_required", "actions", "cleanup_actions", "guided_steps"}
GUIDED_STEP_KEYS = {"id", "instruction", "expected_observation", "required", "evidence_required", "observation_code"}
COMPLETION_KEYS = {"trigger_criteria", "required_criteria", "session_end_reason"}
SAMPLE_PLAN_KEYS = {"basis", "model", "confidence", "absolute_error", "expected_proportion", "estimated_stddev", "reference", "min_samples"}
CRITERION_KEYS = {"id", "label", "description", "type", "events", "metric", "method", "percentile", "operator", "threshold", "max", "max_duration_ms", "confidence", "timing", "instrumentation_budget", "clock", "field", "code", "step", "result", "max_alignment_error_ns", "native_unit", "native_semantics", "sample_plan"}


class ProfileError(ValueError):
    pass


def _number(value: Any, *, positive: bool = False) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and (value > 0 if positive else value >= 0)


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def required_samples(plan: dict[str, Any]) -> int:
    """Return the deterministic minimum sample count declared by a sample plan."""
    if plan.get("basis") == "external-standard":
        return int(plan["min_samples"])
    confidence = float(plan["confidence"])
    error = float(plan["absolute_error"])
    model = plan["model"]
    if model == "distribution":
        return max(1, math.ceil(math.log(2.0 / (1.0 - confidence)) / (2.0 * error * error)))
    z = NormalDist().inv_cdf((1.0 + confidence) / 2.0)
    if model == "proportion":
        proportion = float(plan["expected_proportion"])
        return max(1, math.ceil(z * z * proportion * (1.0 - proportion) / (error * error)))
    if model == "mean":
        stddev = float(plan["estimated_stddev"])
        return max(1, math.ceil((z * stddev / error) ** 2))
    raise ValueError(f"unsupported sample-plan model {model!r}")


def _validate_sample_plan(plan: Any, path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return [f"{path}.sample_plan is required"]
    for key in set(plan) - SAMPLE_PLAN_KEYS:
        errors.append(f"unknown {path}.sample_plan field {key!r}")
    basis = plan.get("basis")
    if basis == "external-standard":
        if not isinstance(plan.get("reference"), str) or not plan.get("reference"):
            errors.append(f"{path}.sample_plan.reference is required")
        if type(plan.get("min_samples")) is not int or plan.get("min_samples", 0) <= 0:
            errors.append(f"{path}.sample_plan.min_samples must be positive")
        return errors
    if basis != "calculated":
        errors.append(f"{path}.sample_plan.basis must be calculated or external-standard")
        return errors
    if plan.get("model") not in {"proportion", "mean", "distribution"}:
        errors.append(f"{path}.sample_plan.model must be proportion, mean, or distribution")
    confidence = plan.get("confidence")
    if not _number(confidence, positive=True) or not 0.5 < confidence < 1:
        errors.append(f"{path}.sample_plan.confidence must be between 0.5 and 1")
    if not _number(plan.get("absolute_error"), positive=True):
        errors.append(f"{path}.sample_plan.absolute_error must be positive")
    if plan.get("model") == "proportion" and (not _number(plan.get("expected_proportion")) or plan.get("expected_proportion", 2) > 1):
        errors.append(f"{path}.sample_plan.expected_proportion must be between zero and one")
    if plan.get("model") == "mean" and not _number(plan.get("estimated_stddev"), positive=True):
        errors.append(f"{path}.sample_plan.estimated_stddev must be positive")
    return errors


def validate_local_override(local: dict[str, Any], tracked: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in local:
        if key not in {"bindings", "actions"}:
            errors.append(f"local override may not change {key!r}; only bindings and action executable paths are allowed")
    actions = local.get("actions", {})
    bindings = local.get("bindings", {})
    allowed_binding_keys = {"port", "host", "device", "udid", "process", "pid"}
    if bindings and not isinstance(bindings, dict):
        errors.append("local bindings must be a mapping")
    elif isinstance(bindings, dict):
        for name, binding in bindings.items():
            if not isinstance(binding, dict) or set(binding) - allowed_binding_keys:
                errors.append(f"local bindings.{name} may contain only endpoint identity fields {sorted(allowed_binding_keys)}")
    if actions and not isinstance(actions, dict):
        errors.append("local actions must be a mapping")
    elif isinstance(actions, dict):
        for name, override in actions.items():
            if name not in tracked.get("actions", {}):
                errors.append(f"local actions.{name} is not declared in the tracked profile")
            if not isinstance(override, dict) or set(override) - {"executable"}:
                errors.append(f"local actions.{name} may override only executable")
    return errors


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProfileError(f"{path}: root must be a mapping")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _find_literal_secrets(value: Any, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else str(key)
            if any(word in str(key).lower() for word in SECRET_WORDS) and child not in (None, ""):
                if not (isinstance(child, dict) and set(child) == {"ref"}):
                    errors.append(f"{here}: tracked secrets must use {{ref: ...}}")
            errors.extend(_find_literal_secrets(child, here))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_find_literal_secrets(child, f"{path}[{index}]"))
    return errors


def validate_profile(profile: dict[str, Any], *, tracked: bool = True) -> list[str]:
    errors: list[str] = []
    for key in set(profile) - ROOT_KEYS:
        errors.append(f"unknown profile field {key!r}")
    version = str(profile.get("version"))
    if version not in {"1.0", "1.1"}:
        errors.append("version must be '1.0' or '1.1'")
    architecture = profile.get("architecture")
    if architecture is not None:
        if not isinstance(architecture, dict):
            errors.append("architecture must be a mapping")
        else:
            for key in set(architecture) - ARCHITECTURE_KEYS:
                errors.append(f"unknown architecture field {key!r}")
            if not isinstance(architecture.get("manifest"), str) or not architecture.get("manifest"):
                errors.append("architecture.manifest is required")
            if version == "1.1":
                if not isinstance(architecture.get("manifest_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", architecture.get("manifest_sha256", "")):
                    errors.append("architecture.manifest_sha256 must be 64 lowercase hex characters")
                if not isinstance(architecture.get("execution_profile"), str) or not architecture.get("execution_profile"):
                    errors.append("architecture.execution_profile is required for version 1.1")
    target = profile.get("target")
    if not isinstance(target, dict):
        errors.append("target must be a mapping")
        target = {}
    for key in set(target) - TARGET_KEYS:
        errors.append(f"unknown target field {key!r}")
    if target.get("platform") not in PLATFORMS:
        errors.append(f"target.platform must be one of {sorted(PLATFORMS)}")
    if target.get("provider") not in PROVIDERS:
        errors.append(f"target.provider must be one of {sorted(PROVIDERS)}")
    fallback = target.get("fallback")
    if fallback not in (None, "structured-log"):
        errors.append("target.fallback must be structured-log or omitted")
    if not isinstance(target.get("native_max_bytes", 4294967296), int) or target.get("native_max_bytes", 4294967296) <= 0:
        errors.append("target.native_max_bytes must be a positive integer")

    transport = profile.get("transport", {})
    if isinstance(transport, dict):
        for key in set(transport) - TRANSPORT_KEYS:
            errors.append(f"unknown transport field {key!r}")
    if transport and transport.get("type") not in {"serial", "tcp-client", "tcp-server", "native", "import"}:
        errors.append("transport.type is unsupported")
    if transport:
        timeout = transport.get("timeout_seconds", 30)
        max_bytes = transport.get("max_bytes", 1048576)
        if not _number(timeout, positive=True):
            errors.append("transport.timeout_seconds must be positive")
        if not isinstance(max_bytes, int) or max_bytes <= 0:
            errors.append("transport.max_bytes must be a positive integer")

    actions = profile.get("actions", {})
    if not isinstance(actions, dict):
        errors.append("actions must be a mapping")
        actions = {}
    for name, action in actions.items():
        if not isinstance(action, dict):
            errors.append(f"actions.{name} must be a mapping")
            continue
        for key in set(action) - ACTION_KEYS:
            errors.append(f"unknown actions.{name} field {key!r}")
        if not isinstance(action.get("executable"), str) or not action.get("executable"):
            errors.append(f"actions.{name}.executable is required")
        if not isinstance(action.get("args", []), list) or not all(isinstance(x, str) for x in action.get("args", [])):
            errors.append(f"actions.{name}.args must be a string list")
        if action.get("risk", "passive") not in RISKS:
            errors.append(f"actions.{name}.risk is invalid")
        if action.get("risk", "passive") == "trace":
            if action.get("trace_role") not in {"record", "stop", "export", "cleanup"}:
                errors.append(f"actions.{name}.trace_role is required for trace risk")
            if action.get("trace_role") == "record" and not action.get("bounded_artifact"):
                errors.append(f"actions.{name} trace record requires bounded_artifact")
        if not _number(action.get("timeout_seconds", 300), positive=True):
            errors.append(f"actions.{name}.timeout_seconds must be positive")
        if not isinstance(action.get("max_output_bytes", 1048576), int) or action.get("max_output_bytes", 1048576) <= 0:
            errors.append(f"actions.{name}.max_output_bytes must be a positive integer")
        if action.get("bounded_artifact") is not None and (not isinstance(action.get("bounded_artifact"), str) or not action.get("bounded_artifact") or not isinstance(action.get("max_artifact_bytes"), int) or action.get("max_artifact_bytes", 0) <= 0):
            errors.append(f"actions.{name}.bounded_artifact requires a path and positive max_artifact_bytes")

    scenarios = profile.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios must be a non-empty list")
        scenarios = []
    seen: set[str] = set()
    for index, scenario in enumerate(scenarios):
        prefix = f"scenarios[{index}]"
        if not isinstance(scenario, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        for key in set(scenario) - SCENARIO_KEYS:
            errors.append(f"unknown {prefix} field {key!r}")
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id:
            errors.append(f"{prefix}.id is required")
        elif scenario_id in seen:
            errors.append(f"{prefix}.id is duplicated")
        else:
            seen.add(scenario_id)
        for key in ("title", "purpose"):
            if key in scenario and (not isinstance(scenario[key], str) or not scenario[key].strip()):
                errors.append(f"{prefix}.{key} must be a non-empty string")
        if scenario.get("phase") not in {"enablement", "smoke", "acceptance"}:
            errors.append(f"{prefix}.phase must be enablement, smoke, or acceptance")
        evidence_mode = scenario.get("evidence_mode")
        if evidence_mode not in {"flow", "statistical", "mixed"}:
            errors.append(f"{prefix}.evidence_mode must be flow, statistical, or mixed")
        if not _number(scenario.get("max_duration_ms"), positive=True):
            errors.append(f"{prefix}.max_duration_ms must be positive")
        completion = scenario.get("completion")
        if not isinstance(completion, dict):
            errors.append(f"{prefix}.completion is required")
            completion = {}
        else:
            for key in set(completion) - COMPLETION_KEYS:
                errors.append(f"unknown {prefix}.completion field {key!r}")
        for key in ("trigger_criteria", "required_criteria"):
            if not isinstance(completion.get(key), list) or not completion.get(key) or not all(isinstance(item, str) and item for item in completion.get(key, [])):
                errors.append(f"{prefix}.completion.{key} must be a non-empty criterion ID list")
        if not isinstance(completion.get("session_end_reason"), str) or not completion.get("session_end_reason"):
            errors.append(f"{prefix}.completion.session_end_reason is required")
        prerequisites = scenario.get("prerequisites", [])
        if not isinstance(prerequisites, list) or not all(isinstance(item, str) and item for item in prerequisites):
            errors.append(f"{prefix}.prerequisites must be a scenario ID list")
        if not isinstance(scenario.get("warmup_required", False), bool):
            errors.append(f"{prefix}.warmup_required must be boolean")
        guided_steps = scenario.get("guided_steps", [])
        if not isinstance(guided_steps, list):
            errors.append(f"{prefix}.guided_steps must be a list")
        else:
            guided_ids: set[str] = set()
            for step_index, step in enumerate(guided_steps):
                spath = f"{prefix}.guided_steps[{step_index}]"
                if not isinstance(step, dict) or set(step) - GUIDED_STEP_KEYS:
                    errors.append(f"{spath} contains unknown fields or is not a mapping")
                    continue
                step_id = step.get("id")
                if not isinstance(step_id, str) or not step_id:
                    errors.append(f"{spath}.id must be non-empty")
                elif step_id in guided_ids:
                    errors.append(f"{spath}.id is duplicated")
                guided_ids.add(step_id)
                for key in ("instruction", "expected_observation"):
                    if not isinstance(step.get(key), str) or not step.get(key):
                        errors.append(f"{spath}.{key} is required")
                for key in ("required", "evidence_required"):
                    if key in step and type(step[key]) is not bool:
                        errors.append(f"{spath}.{key} must be boolean")
        criteria = scenario.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            errors.append(f"{prefix}.criteria must be a non-empty list")
            continue
        criterion_ids = [criterion.get("id") for criterion in criteria if isinstance(criterion, dict)]
        if len(criterion_ids) != len(set(criterion_ids)):
            errors.append(f"{prefix}.criteria IDs must be unique")
        for key in ("trigger_criteria", "required_criteria"):
            for criterion_id in completion.get(key, []) if isinstance(completion.get(key), list) else []:
                if criterion_id not in criterion_ids:
                    errors.append(f"{prefix}.completion.{key} references unknown criterion {criterion_id!r}")
        flow_ids = {c.get("id") for c in criteria if isinstance(c, dict) and c.get("type") in {"event_sequence", "observation"}}
        statistical_ids = {c.get("id") for c in criteria if isinstance(c, dict) and c.get("type") in {"statistic", "native_metric"}}
        required_ids = set(completion.get("required_criteria", []))
        if evidence_mode in {"flow", "mixed"} and not required_ids.intersection(flow_ids):
            errors.append(f"{prefix}.completion requires at least one flow criterion")
        if evidence_mode in {"statistical", "mixed"} and not required_ids.intersection(statistical_ids):
            errors.append(f"{prefix}.completion requires at least one statistical criterion")
        scenario_actions = scenario.get("actions", [])
        cleanup_actions = scenario.get("cleanup_actions", [])
        if not isinstance(scenario_actions, list) or not all(isinstance(name, str) and name in actions for name in scenario_actions):
            errors.append(f"{prefix}.actions must reference declared actions")
            scenario_actions = []
        if not isinstance(cleanup_actions, list) or not all(isinstance(name, str) and name in actions for name in cleanup_actions):
            errors.append(f"{prefix}.cleanup_actions must reference declared actions")
            cleanup_actions = []
        for name in cleanup_actions:
            cleanup = actions[name]
            if cleanup.get("idempotent") is not True or cleanup.get("risk", "passive") not in {"passive", "trace"} or (cleanup.get("risk") == "trace" and cleanup.get("trace_role") not in {"stop", "cleanup"}):
                errors.append(f"actions.{name} cleanup must declare idempotent: true and use passive or trace risk")
        if any(actions[name].get("risk") == "trace" for name in scenario_actions) and not cleanup_actions:
            errors.append(f"{prefix}.cleanup_actions is required for trace actions")
        if scenario.get("warmup_required", False):
            statistical_metrics = {c.get("metric") for c in criteria if isinstance(c, dict) and c.get("type") == "statistic"}
            hard_limit_metrics = {c.get("metric") for c in criteria if isinstance(c, dict) and c.get("type") == "hard_limit"}
            for reused in sorted((statistical_metrics & hard_limit_metrics) - {None}):
                errors.append(f"{prefix}: warmup statistic and hard_limit must use distinct metrics, not {reused!r}")
        for c_index, criterion in enumerate(criteria):
            cpath = f"{prefix}.criteria[{c_index}]"
            if not isinstance(criterion, dict):
                errors.append(f"{cpath} must be a mapping")
                continue
            for key in set(criterion) - CRITERION_KEYS:
                errors.append(f"unknown {cpath} field {key!r}")
            if not criterion.get("id"):
                errors.append(f"{cpath}.id is required")
            for key in ("label", "description"):
                if key in criterion and (not isinstance(criterion[key], str) or not criterion[key].strip()):
                    errors.append(f"{cpath}.{key} must be a non-empty string")
            if criterion.get("type") not in CRITERIA:
                errors.append(f"{cpath}.type is invalid")
            if criterion.get("type") == "event_sequence" and not criterion.get("events"):
                errors.append(f"{cpath}.events is required")
            if criterion.get("type") == "observation":
                if not isinstance(criterion.get("code"), str) or not criterion.get("code"):
                    errors.append(f"{cpath}.code is required")
                if not isinstance(criterion.get("step"), int) or isinstance(criterion.get("step"), bool):
                    errors.append(f"{cpath}.step must be an integer")
            if criterion.get("type") in {"hard_limit", "statistic", "native_metric"} and not criterion.get("metric"):
                errors.append(f"{cpath}.metric is required")
            if criterion.get("type") in {"hard_limit", "statistic", "native_metric"}:
                if criterion.get("operator", "<=") not in OPERATORS:
                    errors.append(f"{cpath}.operator must be one of {sorted(OPERATORS)}")
                if not _finite_number(criterion.get("threshold", criterion.get("max"))):
                    errors.append(f"{cpath}.threshold must be numeric")
            if criterion.get("type") == "statistic":
                if criterion.get("method", "field") not in STATISTIC_METHODS:
                    errors.append(f"{cpath}.method must be one of {sorted(STATISTIC_METHODS)}")
                if criterion.get("method") == "percentile" and (not _number(criterion.get("percentile"), positive=True) or criterion.get("percentile", 0) > 1):
                    errors.append(f"{cpath}.percentile must be between zero and one")
                errors.extend(_validate_sample_plan(criterion.get("sample_plan"), cpath))
                if not _number(criterion.get("max_duration_ms"), positive=True):
                    errors.append(f"{cpath}.max_duration_ms must be positive")
                confidence = criterion.get("confidence", 0.95)
                if not _number(confidence, positive=True) or not 0.5 < confidence < 1:
                    errors.append(f"{cpath}.confidence must be between 0.5 and 1")
                if criterion.get("timing", False) and not isinstance(criterion.get("instrumentation_budget"), dict):
                    errors.append(f"{cpath}.instrumentation_budget is required for timing statistics")
                if criterion.get("timing", False):
                    budget = criterion.get("instrumentation_budget", {})
                    for key in ("update_cycles_max", "snapshot_us", "log_bytes", "allocation_count", "isr_log_writes", "critical_section_us"):
                        if not _number(budget.get(key)):
                            errors.append(f"{cpath}.instrumentation_budget.{key} must be a non-negative number")
                    clock = criterion.get("clock")
                    if not isinstance(clock, dict) or not isinstance(clock.get("source"), str) or not clock.get("source"):
                        errors.append(f"{cpath}.clock.source is required for timing statistics")
                    else:
                        if not _number(clock.get("hz"), positive=True):
                            errors.append(f"{cpath}.clock.hz must be positive")
                        if not _number(clock.get("resolution_ns"), positive=True):
                            errors.append(f"{cpath}.clock.resolution_ns must be positive")
            if criterion.get("type") == "native_metric":
                if not _number(criterion.get("max_alignment_error_ns")):
                    errors.append(f"{cpath}.max_alignment_error_ns must be a non-negative number")
                errors.extend(_validate_sample_plan(criterion.get("sample_plan"), cpath))
                if not _number(criterion.get("max_duration_ms"), positive=True):
                    errors.append(f"{cpath}.max_duration_ms must be positive")
                semantics = criterion.get("native_semantics")
                if not isinstance(semantics, dict) or not all(semantics.get(key) for key in ("start_event", "end_event", "clock")):
                    errors.append(f"{cpath}.native_semantics must define start_event, end_event, and clock")
                if not isinstance(criterion.get("native_unit"), str) or not criterion.get("native_unit"):
                    errors.append(f"{cpath}.native_unit is required")
    scenario_by_id = {scenario.get("id"): scenario for scenario in scenarios if isinstance(scenario, dict)}
    has_native_resource = any(
        isinstance(criterion, dict) and criterion.get("type") == "native_metric"
        for scenario in scenarios if isinstance(scenario, dict)
        for criterion in scenario.get("criteria", [])
    )
    required_native = {"windows": "etw-wpr", "linux": "perf-ftrace", "ios": "instruments-xctest"}
    platform = target.get("platform")
    if has_native_resource and platform in required_native and target.get("provider") != required_native[platform]:
        errors.append(f"target.provider must be {required_native[platform]!r} for {platform} native resource criteria")
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            continue
        for prerequisite in scenario.get("prerequisites", []):
            target_scenario = scenario_by_id.get(prerequisite)
            if target_scenario is None:
                errors.append(f"scenarios[{index}].prerequisites references unknown scenario {prerequisite!r}")
            elif target_scenario.get("phase") != "enablement":
                errors.append(f"scenarios[{index}].prerequisites must reference enablement scenarios")
        if scenario.get("phase") == "acceptance" and not scenario.get("prerequisites"):
            errors.append(f"scenarios[{index}].prerequisites requires at least one enablement scenario for acceptance")
    errors.extend(_find_literal_secrets(profile))
    return errors


def validate_architecture_references(profile: dict[str, Any], project_root: Path) -> list[str]:
    architecture = profile.get("architecture")
    if not isinstance(architecture, dict) or not architecture.get("manifest"):
        return []
    project_root = project_root.resolve()
    manifest_path = (project_root / str(architecture["manifest"])).resolve()
    if not manifest_path.is_relative_to(project_root):
        return ["architecture.manifest escapes the project root"]
    if not manifest_path.exists():
        return [f"architecture manifest does not exist: {manifest_path}"]
    manifest = load_yaml(manifest_path)
    errors: list[str] = []
    if str(profile.get("version")) == "1.1":
        actual_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        if architecture.get("manifest_sha256") != actual_hash:
            errors.append("architecture.manifest_sha256 does not match the selected manifest")
        profile_id = architecture.get("execution_profile")
        execution_profiles = {
            str(item.get("id")): item
            for item in manifest.get("execution_profiles", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        selected = execution_profiles.get(str(profile_id))
        if selected is None:
            errors.append(f"architecture.execution_profile references unknown profile {profile_id!r}")
        elif selected.get("status") != "accepted":
            errors.append("architecture.execution_profile must reference an accepted profile")
        else:
            execution_platform = selected.get("target", {}).get("validation_platform", selected.get("target", {}).get("platform"))
            selected_platform = profile.get("target", {}).get("platform")
            if execution_platform != selected_platform:
                errors.append(
                    "architecture.execution_profile platform does not match target.platform "
                    f"({execution_platform!r} != {selected_platform!r})"
                )
    known: set[str] = set()
    for collection in (
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
    ):
        for item in manifest.get(collection, []):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                known.add(item["id"])
    for scenario in profile.get("scenarios", []):
        refs = scenario.get("architecture_refs", []) if isinstance(scenario, dict) else []
        if not refs:
            errors.append(f"scenario {scenario.get('id', '<unknown>')}: architecture_refs is required for a governed project")
        for ref in refs:
            if ref not in known:
                errors.append(f"scenario {scenario.get('id', '<unknown>')}: unknown architecture reference {ref!r}")
    return errors


def load_profile(profile_path: Path, local_path: Path | None = None) -> tuple[dict[str, Any], list[str]]:
    tracked = load_yaml(profile_path)
    errors = validate_profile(tracked, tracked=True)
    if errors:
        return tracked, errors
    if local_path and local_path.exists():
        local = load_yaml(local_path)
        local_errors = validate_local_override(local, tracked)
        if local_errors:
            return tracked, local_errors
        merged = deep_merge(tracked, local)
    else:
        merged = tracked
    project_root = profile_path.resolve().parent.parent
    merged["_project_root"] = str(project_root)
    merged_errors = validate_profile(merged, tracked=False)
    merged_errors.extend(validate_architecture_references(merged, project_root))
    return merged, merged_errors


def redact(value: Any, key: str = "") -> Any:
    if any(word in key.lower() for word in SECRET_WORDS):
        return "<redacted>"
    if isinstance(value, dict):
        return {item_key: redact(item, str(item_key)) for item_key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return copy.deepcopy(value)
