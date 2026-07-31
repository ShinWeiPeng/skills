from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import re
from typing import Any, Protocol


VALIDATION_GATES = (
    "Validation Enablement",
    "Per-change Development Validation",
    "Final Runtime Acceptance",
    "Release Acceptance",
)


class Verdict(IntEnum):
    PASS = 0
    BLOCKED = 1
    FAIL = 2

    @property
    def label(self) -> str:
        return self.name


@dataclass
class CriterionResult:
    criterion_id: str
    verdict: Verdict
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)


class VerdictInputPort(Protocol):
    def submit(self, results: list[CriterionResult]) -> Verdict: ...


class VerdictOutputPort(Protocol):
    def publish(self, verdict: Verdict, results: list[CriterionResult]) -> None: ...


def overall(results: list[CriterionResult]) -> Verdict:
    if not results:
        return Verdict.BLOCKED
    return max((item.verdict for item in results), default=Verdict.BLOCKED)


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and bool(item.strip()) for item in value)


def _development_gate_result(
    document: dict[str, Any],
    smoke_results: dict[str, Verdict],
    external_contract_refs: set[str],
) -> tuple[CriterionResult, list[str]]:
    problems: list[str] = []
    group_results: list[CriterionResult] = []
    if document.get("schema_version") != "1.0":
        problems.append("development gate schema_version must be '1.0'")
    if document.get("gate") != VALIDATION_GATES[1]:
        problems.append("development gate identifier is invalid")
    if not isinstance(document.get("source_revision"), str) or not document["source_revision"].strip():
        problems.append("development gate source_revision is required")
    groups = document.get("change_groups")
    if not isinstance(groups, list) or not groups:
        problems.append("development gate requires at least one change group")
        groups = []
    seen_group_ids: set[str] = set()
    for group_index, group in enumerate(groups):
        prefix = f"change_groups[{group_index}]"
        group_problems: list[str] = []
        check_verdicts: list[Verdict] = []
        if not isinstance(group, dict):
            problems.append(f"{prefix} must be a mapping")
            group_results.append(CriterionResult(prefix, Verdict.BLOCKED, "change group is invalid"))
            continue
        group_id = group.get("id")
        if not isinstance(group_id, str) or not group_id.strip():
            group_problems.append(f"{prefix}.id is required")
            group_id = prefix
        elif group_id in seen_group_ids:
            group_problems.append(f"{prefix}.id is duplicated")
        else:
            seen_group_ids.add(group_id)
        architecture_refs = group.get("architecture_refs")
        if not _nonempty_strings(architecture_refs):
            group_problems.append(f"{prefix}.architecture_refs must contain non-empty identifiers")
            architecture_refs = []
        risks = group.get("risks")
        if not _nonempty_strings(risks):
            group_problems.append(f"{prefix}.risks must contain non-empty risks")
        checks = group.get("checks")
        if not isinstance(checks, list) or not checks:
            group_problems.append(f"{prefix}.checks must contain at least one check")
            checks = []
        seen_check_ids: set[str] = set()
        check_kinds: set[str] = set()
        for check_index, check in enumerate(checks):
            check_prefix = f"{prefix}.checks[{check_index}]"
            check_problems: list[str] = []
            if not isinstance(check, dict):
                group_problems.append(f"{check_prefix} must be a mapping")
                check_verdicts.append(Verdict.BLOCKED)
                continue
            check_id = check.get("id")
            if not isinstance(check_id, str) or not check_id.strip():
                check_problems.append(f"{check_prefix}.id is required")
            elif check_id in seen_check_ids:
                check_problems.append(f"{check_prefix}.id is duplicated")
            else:
                seen_check_ids.add(check_id)
            kind = check.get("kind")
            if not isinstance(kind, str) or not kind.strip():
                check_problems.append(f"{check_prefix}.kind is required")
            else:
                check_kinds.add(kind)
            if not isinstance(check.get("test_boundary"), str) or not check["test_boundary"].strip():
                check_problems.append(f"{check_prefix}.test_boundary is required")
            command = check.get("command")
            if not isinstance(command, dict):
                check_problems.append(f"{check_prefix}.command must be a mapping")
            else:
                if not isinstance(command.get("executable"), str) or not command["executable"].strip():
                    check_problems.append(f"{check_prefix}.command.executable is required")
                if not isinstance(command.get("args"), list) or not all(isinstance(item, str) for item in command.get("args", [])):
                    check_problems.append(f"{check_prefix}.command.args must be a string list")
                if "cwd" in command and (not isinstance(command["cwd"], str) or not command["cwd"].strip()):
                    check_problems.append(f"{check_prefix}.command.cwd must be a non-empty string")
            exit_code = check.get("exit_code")
            if not isinstance(exit_code, int) or isinstance(exit_code, bool):
                check_problems.append(f"{check_prefix}.exit_code must be an integer")
            verdict_name = check.get("verdict")
            if verdict_name not in Verdict.__members__:
                check_problems.append(f"{check_prefix}.verdict is invalid")
                check_verdict = Verdict.BLOCKED
            else:
                check_verdict = Verdict[verdict_name]
                if check_verdict == Verdict.PASS and exit_code != 0:
                    check_problems.append(f"{check_prefix} cannot PASS with a nonzero exit_code")
            evidence = check.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                check_problems.append(f"{check_prefix}.evidence must contain hashed artifacts")
            else:
                for evidence_index, artifact in enumerate(evidence):
                    artifact_prefix = f"{check_prefix}.evidence[{evidence_index}]"
                    if not isinstance(artifact, dict):
                        check_problems.append(f"{artifact_prefix} must be a mapping")
                        continue
                    if not isinstance(artifact.get("path"), str) or not artifact["path"].strip():
                        check_problems.append(f"{artifact_prefix}.path is required")
                    digest = artifact.get("sha256")
                    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
                        check_problems.append(f"{artifact_prefix}.sha256 must be a 64-digit hexadecimal digest")
            if check_problems:
                group_problems.extend(check_problems)
                check_verdict = max(check_verdict, Verdict.BLOCKED)
            check_verdicts.append(check_verdict)
        if set(architecture_refs) & external_contract_refs and "port-contract" not in check_kinds:
            group_problems.append(f"{prefix} changes an external Port/Adapter but has no port-contract check")
        smoke = group.get("on_device_smoke")
        if not isinstance(smoke, dict) or not isinstance(smoke.get("required"), bool):
            group_problems.append(f"{prefix}.on_device_smoke.required must be boolean")
        else:
            if not isinstance(smoke.get("reason"), str) or not smoke["reason"].strip():
                group_problems.append(f"{prefix}.on_device_smoke.reason is required")
            if smoke["required"]:
                scenario = smoke.get("scenario")
                if not isinstance(scenario, str) or not scenario.strip():
                    group_problems.append(f"{prefix}.on_device_smoke.scenario is required")
                elif scenario not in smoke_results:
                    group_problems.append(f"{prefix} requires smoke scenario {scenario!r}, but no matching result was supplied")
                    check_verdicts.append(Verdict.BLOCKED)
                else:
                    check_verdicts.append(smoke_results[scenario])
        group_verdict = max(check_verdicts, default=Verdict.BLOCKED)
        if group_problems:
            problems.extend(group_problems)
            group_verdict = max(group_verdict, Verdict.BLOCKED)
        group_results.append(
            CriterionResult(str(group_id), group_verdict, "change group evidence recomputed", {"checks": len(checks), "problems": group_problems})
        )
    recomputed = overall(group_results)
    declared = document.get("verdict")
    if declared not in Verdict.__members__:
        problems.append("development gate verdict is invalid")
    elif Verdict[declared] != recomputed:
        problems.append(f"development gate declared verdict {declared} does not match recomputed verdict {recomputed.label}")
    effective = max(recomputed, Verdict.BLOCKED) if problems else recomputed
    return (
        CriterionResult(
            VALIDATION_GATES[1],
            effective,
            "development gate evidence recomputed",
            {
                "source_revision": document.get("source_revision"),
                "change_groups": [
                    {"id": item.criterion_id, "verdict": item.verdict.label, **item.evidence} for item in group_results
                ],
            },
        ),
        problems,
    )


def overall_gates(
    documents: list[dict[str, Any]],
    profile_sha256: str,
    expected_enablement: set[str],
    expected_acceptance: set[str],
    expected_smoke: set[str] | None = None,
    external_contract_refs: set[str] | None = None,
) -> tuple[Verdict, dict[str, Any]]:
    """Combine runtime and external gate documents without letting smoke satisfy acceptance."""
    phase_gate = {"enablement": VALIDATION_GATES[0], "acceptance": VALIDATION_GATES[2]}
    grouped: dict[str, list[dict[str, Any]]] = {gate: [] for gate in VALIDATION_GATES}
    invalid: list[str] = []
    expected_smoke = expected_smoke or set()
    external_contract_refs = external_contract_refs or set()
    smoke_results: dict[str, Verdict] = {}
    smoke_indexes: set[int] = set()
    for index, document in enumerate(documents):
        if not isinstance(document, dict) or document.get("phase") != "smoke":
            continue
        smoke_indexes.add(index)
        if document.get("profile_sha256") != profile_sha256:
            invalid.append(f"result[{index}] is not bound to the current profile")
            continue
        scenario = document.get("scenario")
        if not isinstance(scenario, str) or not scenario or scenario not in expected_smoke:
            invalid.append(f"result[{index}] is not a declared smoke scenario")
            continue
        if document.get("verdict") not in Verdict.__members__:
            invalid.append(f"result[{index}] has an invalid verdict")
            continue
        verdict = Verdict[document["verdict"]]
        smoke_results[scenario] = max(smoke_results.get(scenario, Verdict.PASS), verdict)
    for index, document in enumerate(documents):
        if index in smoke_indexes:
            continue
        if not isinstance(document, dict) or document.get("profile_sha256") != profile_sha256:
            invalid.append(f"result[{index}] is not bound to the current profile")
            continue
        gate = document.get("gate") or phase_gate.get(document.get("phase"))
        if gate not in grouped:
            invalid.append(f"result[{index}] does not identify a recognized validation gate")
            continue
        if gate == VALIDATION_GATES[0] and document.get("scenario") not in expected_enablement:
            invalid.append(f"result[{index}] is not a declared enablement scenario")
            continue
        if gate == VALIDATION_GATES[2] and document.get("scenario") not in expected_acceptance:
            invalid.append(f"result[{index}] is not a declared acceptance scenario")
            continue
        if gate != VALIDATION_GATES[1] and document.get("verdict") not in Verdict.__members__:
            invalid.append(f"result[{index}] has an invalid verdict")
            continue
        if gate == VALIDATION_GATES[3] and not document.get("evidence"):
            invalid.append(f"result[{index}] requires non-empty evidence references")
            continue
        grouped[gate].append(document)
    missing_scenarios = {
        VALIDATION_GATES[0]: sorted(expected_enablement - {item.get("scenario") for item in grouped[VALIDATION_GATES[0]]}),
        VALIDATION_GATES[2]: sorted(expected_acceptance - {item.get("scenario") for item in grouped[VALIDATION_GATES[2]]}),
    }
    gate_results: list[CriterionResult] = []
    for gate in VALIDATION_GATES:
        items = grouped[gate]
        missing = missing_scenarios.get(gate, [])
        if not items or missing:
            gate_results.append(CriterionResult(gate, Verdict.BLOCKED, "required gate evidence is missing", {"missing_scenarios": missing}))
            continue
        if gate == VALIDATION_GATES[1]:
            development_results: list[CriterionResult] = []
            for item in items:
                result, problems = _development_gate_result(item, smoke_results, external_contract_refs)
                development_results.append(result)
                invalid.extend(problems)
            verdict = overall(development_results)
            gate_results.append(
                CriterionResult(
                    gate,
                    verdict,
                    "structured change-group evidence recomputed",
                    {"documents": len(items), "results": [item.evidence for item in development_results]},
                )
            )
        else:
            verdict = max(Verdict[item["verdict"]] for item in items)
            gate_results.append(CriterionResult(gate, verdict, "gate evidence combined", {"documents": len(items)}))
    if invalid:
        gate_results.append(CriterionResult("gate-input", Verdict.BLOCKED, "; ".join(invalid)))
    verdict = overall(gate_results)
    return verdict, {
        "verdict": verdict.label,
        "gates": [{"gate": item.criterion_id, "verdict": item.verdict.label, "reason": item.reason, "evidence": item.evidence} for item in gate_results],
        "invalid": invalid,
    }
