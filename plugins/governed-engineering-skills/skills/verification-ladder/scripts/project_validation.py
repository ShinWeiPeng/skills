"""Bind project policy, AC plans and evidence to the existing verification ladder.

JSON artifacts are caller-supplied evidence, not authenticated device observations.
All public assessments reread the bounded project documents; no device is opened.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml
from run_storage import allocate_run, finalize_run, validate_run, source_snapshot
from verification_ladder import (
    LAYER_ORDER,
    TAXONOMY,
    assess_evidence,
    plan,
    validate_matrix,
    validate_paths,
)

DEVICE_LAYERS = {"pil", "hil", "system-soak"}
DOCUMENTS = (
    "architecture/adoption.yaml",
    "architecture/manifest.yaml",
    "validation/verification-ladder.yaml",
    "validation/on-device.yaml",
    "validation/layout.yaml",
)
MAX_BYTES = 1048576


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def project_path(root, relative):
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or ":" in relative
    ):
        raise ValueError("expected a portable project-relative path")
    path = Path(relative)
    if path.is_absolute() or any(p in {".", ".."} for p in relative.split("/")):
        raise ValueError("path must stay within project")
    target = root / path
    for item in (target, *target.parents):
        if item == root:
            break
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ValueError("redirected validation path")
    if not target.resolve().is_relative_to(root):
        raise ValueError("validation path escaped project")
    return target


def read_document(root, relative, records, required=False):
    path = project_path(root, relative)
    if not path.exists():
        records[relative] = {"state": "missing", "sha256": None}
        if required:
            raise ValueError(f"missing required document: {relative}")
        return {}
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError(f"invalid or oversized document: {relative}")
    raw = path.read_bytes()
    records[relative] = {"state": "present", "sha256": hashlib.sha256(raw).hexdigest()}
    try:
        data = (
            json.loads(raw)
            if path.suffix == ".json"
            else yaml.safe_load(raw.decode("utf-8-sig"))
        )
    except (ValueError, yaml.YAMLError) as exc:
        records[relative]["state"] = "invalid"
        raise ValueError(f"invalid document: {relative}: {exc}") from exc
    if not isinstance(data, dict):
        records[relative]["state"] = "invalid"
        raise ValueError(f"document must be an object: {relative}")
    return data


def spec_contract(text):
    identity = re.search(r"(?m)^spec_id:\s*(SPEC-\d{4})\s*$", text)
    revision = re.search(r"(?m)^revision:\s*(\d+)\s*$", text)
    if not identity or not revision:
        raise ValueError("invalid SPEC identity/revision")
    section = re.search(r"(?ms)^## Acceptance Criteria\s*\n(.*?)(?=^## |\Z)", text)
    rows = {}
    if section:
        for line in section.group(1).splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and re.fullmatch(r"AC-\d+", cells[0]):
                if len(cells) != 5 or cells[0] in rows:
                    raise ValueError("malformed or duplicate acceptance row")
                rows[cells[0]] = cells
    if not rows:
        raise ValueError("SPEC has no acceptance criteria")
    return identity.group(1), int(revision.group(1)), rows


def skill_identity():
    # Bind the actual selected package's code, rule table and instructions.
    scripts = Path(__file__).resolve().parent
    skills = scripts.parents[1]
    files = [
        scripts / "project_validation.py",
        scripts / "verification_ladder.py",
        scripts / "run_storage.py",
        scripts.parent / "SKILL.md",
        skills / "engineering-risk-routing/references/routing-rules.json",
    ]
    files.extend(
        skills / relative
        for relative in (
            "engineering-risk-routing/scripts/guided_workflow_router.py",
            "govern-modular-event-architecture/scripts/validation_layout.py",
            "spec-governance/scripts/spec_contract.py",
            "implement/scripts/spec_delivery.py",
            "implement/scripts/managed_delivery.py",
            "implement/scripts/project_validation_adapter.py",
            "implement/scripts/project_validation_workflow.py",
        )
    )
    hashes = {
        str(p.relative_to(skills)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files
    }
    version = "source-checkout"
    candidates = [
        skills.parent / ".codex-plugin/plugin.json",
        skills.parent.parent
        / "plugins/governed-engineering-skills/.codex-plugin/plugin.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            version = json.loads(candidate.read_text(encoding="utf-8"))["version"]
            break
    return {"version": version, "sha256": digest(hashes)}


def _strings(value, name):
    if (
        not isinstance(value, list)
        or any(not isinstance(v, str) or not v for v in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError(f"{name} must be unique non-empty strings")
    return value


def assess_project(root, spec=None, *, phase="planning", candidate_text=None):
    """Read fresh facts and return planning/enablement/acceptance independently."""
    root = Path(root).resolve()
    result = {
        "verdict": "BLOCKED",
        "required_gates": [],
        "required_layers": [],
        "errors": [],
        "documents": {},
        "phase": phase,
        "device_actions_authorized": False,
    }
    try:
        _assess(root, spec, phase, candidate_text, result)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        result["errors"].append(str(exc))
    if result["errors"] and result["verdict"] != "FAIL":
        result["verdict"] = "BLOCKED"
    return result


def _assess(root, spec, phase, candidate_text, result):
    if phase not in {"planning", "enablement", "acceptance", "release"}:
        raise ValueError("unknown validation phase")
    records = result["documents"]
    docs = {p: read_document(root, p, records) for p in DOCUMENTS}
    policy = docs[DOCUMENTS[0]].get("runtime_validation")
    if policy is not None and (
        not isinstance(policy, dict)
        or policy.get("applicability") not in {"required", "not-applicable"}
        or not str(policy.get("rationale", "")).strip()
    ):
        raise ValueError("runtime_validation requires applicability and rationale")
    required = bool(policy and policy["applicability"] == "required")
    matrix = docs[DOCUMENTS[2]]
    active = required or bool(matrix) or bool(docs[DOCUMENTS[3]])
    result["applicability"] = policy["applicability"] if policy else "undeclared"
    result["skill"] = skill_identity()
    if active:
        result["required_gates"] = ["verification-ladder"]
    if required and not matrix:
        raise ValueError("required runtime policy has no verification matrix")
    if active and not matrix:
        raise ValueError("device context has no verification matrix")
    if matrix:
        errors = validate_matrix(matrix, docs[DOCUMENTS[1]], docs[DOCUMENTS[3]])
        errors += validate_paths(
            matrix,
            root / DOCUMENTS[2],
            root / DOCUMENTS[1],
            root / DOCUMENTS[3] if matrix.get("on_device_profile") else None,
        )
        if errors:
            raise ValueError("; ".join(errors))
    if not spec:
        if active:
            raise ValueError("resolve the current SPEC before validation planning")
        result["verdict"] = "PASS"
        result["reason"] = (
            "No project runtime obligation declared; not a device exemption."
        )
        return
    path = project_path(root, spec)
    if path.parent != root / "specs" or path.stat().st_size > MAX_BYTES:
        raise ValueError("expected canonical SPEC directly under specs/")
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    spec_id, revision, rows = spec_contract(text)
    if not path.name.startswith(spec_id + "-"):
        raise ValueError("SPEC filename/identity mismatch")
    # A scope mapping is required when project validation is governed. Ordinary
    # legacy host projects retain behavior, without asserting device acceptance.
    mapping_path = f"validation/acceptance-{spec_id}.json"
    mapping = read_document(root, mapping_path, records, required=active)
    if not active and not mapping:
        result["verdict"] = "PASS"
        result["reason"] = (
            "Legacy ungoverned host context; no hardware acceptance asserted."
        )
        return
    result["required_gates"] = ["verification-ladder"]
    if not matrix:
        raise ValueError("AC claims require a verification matrix")
    if (
        set(mapping) != {"schema_version", "spec_id", "acceptance"}
        or type(mapping["schema_version"]) is not int
        or mapping["schema_version"] != 1
        or mapping["spec_id"] != spec_id
        or not isinstance(mapping["acceptance"], dict)
        or set(mapping["acceptance"]) != set(rows)
    ):
        raise ValueError("acceptance mapping must cover exactly this SPEC's AC IDs")
    plans = {}
    scenario_by_id = {s["id"]: s for s in docs[DOCUMENTS[3]].get("scenarios", [])}
    for ac, item in mapping["acceptance"].items():
        if not isinstance(item, dict) or set(item) - {
            *TAXONOMY,
            "rationale",
            "scenario_layers",
            "build_artifact",
            "enablement_scenarios",
            "criterion_sha256",
        }:
            raise ValueError(f"{ac}: unknown acceptance mapping fields")
        if "criterion_sha256" in item:
            section = re.search(
                r"(?ms)^## Acceptance Criteria\s*\n(.*?)(?=^## |\Z)", text
            )
            header = next(
                line
                for line in section.group(1).splitlines()
                if line.strip().startswith("|")
            )
            names = [
                cell.strip().casefold() for cell in header.strip().strip("|").split("|")
            ]
            criterion = {
                name: value
                for name, value in zip(names, rows[ac], strict=True)
                if name != "evidence"
            }
            if item["criterion_sha256"] != digest(criterion):
                raise ValueError(f"{ac}: acceptance criterion signature is stale")
        requested = {k: set(_strings(item.get(k, []), f"{ac}.{k}")) for k in TAXONOMY}
        if (
            not requested["evidence_claims"]
            or not str(item.get("rationale", "")).strip()
        ):
            raise ValueError(
                f"{ac}: evidence claims and applicability rationale required"
            )
        selected = plan(matrix, requested)
        if selected["status"] != "PASS":
            raise ValueError(f"{ac}: " + "; ".join(selected["errors"]))
        layers = selected["required_layers"]
        device = set(layers) & DEVICE_LAYERS
        if any(layer not in matrix["layers"] for layer in layers):
            raise ValueError(f"{ac}: required layer has no project contract")
        rules = [r for r in matrix["rules"] if r["id"] in selected["activated_rules"]]
        profiles = sorted({p for rule in rules for p in rule["execution_profiles"]})
        scenarios = sorted({s for rule in rules for s in rule["on_device_scenarios"]})
        assignments = item.get("scenario_layers", {})
        prerequisites = item.get("enablement_scenarios", [])
        if not isinstance(assignments, dict) or set(assignments) != device:
            raise ValueError(
                f"{ac}: scenario_layers must name exactly selected device layers"
            )
        for layer, values in assignments.items():
            if not _strings(values, layer):
                raise ValueError(f"{ac}: each device layer needs a scenario")
        if set(s for values in assignments.values() for s in values) != set(scenarios):
            raise ValueError(f"{ac}: scenario coverage differs from activated rules")
        if device and len(profiles) != 1:
            raise ValueError(f"{ac}: exactly one production execution profile required")
        for prerequisite in _strings(prerequisites, "enablement_scenarios"):
            if (
                prerequisite not in scenario_by_id
                or scenario_by_id[prerequisite].get("phase") != "enablement"
            ):
                raise ValueError(f"{ac}: invalid enablement scenario")
        if device and any(
            scenario_by_id[s].get("phase") != "acceptance"
            or not scenario_by_id[s].get("prerequisites")
            for s in scenarios
        ):
            raise ValueError(
                f"{ac}: device scenarios require acceptance phase and enablement prerequisites"
            )
        expected_prerequisites = {
            p for s in scenarios for p in scenario_by_id[s].get("prerequisites", [])
        }
        if set(prerequisites) != expected_prerequisites:
            raise ValueError(f"{ac}: enablement prerequisites differ from profile")
        build = item.get("build_artifact")
        if device and not build:
            raise ValueError(f"{ac}: build artifact path required")
        if build:
            project_path(root, build)
        plans[ac] = {
            "claims": sorted(requested["evidence_claims"]),
            "contract": rows[ac][:4],
            "rules": selected["activated_rules"],
            "layers": layers,
            "scenario_layers": assignments,
            "execution_profiles": profiles,
            "enablement_scenarios": prerequisites,
            "build_artifact": build,
            "rationale": item["rationale"],
        }
    layers = set(layer for item in plans.values() for layer in item["layers"])
    result["required_layers"] = [layer for layer in LAYER_ORDER if layer in layers]
    if layers & DEVICE_LAYERS:
        result["required_gates"].append("validate-on-device")
    binding = {
        "project_root": str(root),
        "spec": spec,
        "spec_id": spec_id,
        "revision": revision,
        "spec_sha256": hashlib.sha256(raw).hexdigest(),
        "documents": records.copy(),
        "skill": result["skill"],
        "device_profile_sha256": digest(
            {k: v for k, v in docs[DOCUMENTS[3]].items() if k != "_project_root"}
        ),
    }
    current_plan = {"schema_version": 1, "binding": binding, "acceptance": plans}
    result["plan"] = current_plan
    result["plan_sha256"] = digest(current_plan)
    result["verdict"] = "PASS"
    if phase == "planning":
        return
    references = read_document(
        root, f"validation/run-references-{spec_id}.json", {}, required=True
    )
    plan_reference = references.get("plan_manifest")
    if not isinstance(plan_reference, str):
        raise ValueError("explicit plan_manifest reference required")
    plan_run = validate_run(root, plan_reference)
    if plan_run["outcome"] != "PASS" or plan_run["metadata"].get("spec") != spec_id:
        raise ValueError("plan run identity/outcome mismatch")
    stored_path = str(Path(plan_reference).parent / "plan.snapshot.json").replace(
        "\\", "/"
    )
    stored = read_document(root, stored_path, {}, required=True)
    if stored != current_plan:
        raise ValueError(
            "validation plan is stale; regenerate from current project/SPEC"
        )
    if candidate_text is not None:
        candidate_id, _, candidate_rows = spec_contract(candidate_text)
        if candidate_id != spec_id or {k: v[:4] for k, v in candidate_rows.items()} != {
            k: v[:4] for k, v in rows.items()
        }:
            raise ValueError(
                "acceptance contract changed; replan before evidence update"
            )

        # Requirements and other contract sections must not change during a PASS update.
        def semantic(value):
            value = value.replace("\r\n", "\n")
            value = re.sub(
                r"(?im)^Spec review:[ \t]*(?:pending|pass|blocked)[ \t]*\n",
                "",
                value,
            )
            value = re.sub(
                r"(?m)^(revision|status|working_id|task_ref|branch_ref):.*\n", "", value
            )
            value = re.sub(
                r"(?ms)^## (?:Acceptance Criteria|Revision History|Implementation Evidence).*?(?=^## |\Z)",
                "",
                value,
            )
            return value.strip()

        if semantic(text) != semantic(candidate_text):
            raise ValueError(
                "SPEC contract changed; old evidence cannot approve new requirements"
            )
    if phase == "enablement" and not any(
        item["enablement_scenarios"] for item in plans.values()
    ):
        return
    evidence_references = references.get("evidence_manifests")
    if (
        not isinstance(evidence_references, list)
        or not evidence_references
        or len(set(evidence_references)) != len(evidence_references)
    ):
        raise ValueError("explicit unique evidence_manifests required")
    bundles = []
    for reference in evidence_references:
        evidence_run = validate_run(root, reference)
        if evidence_run["metadata"].get("spec") != spec_id:
            raise ValueError("evidence SPEC identity mismatch")
        evidence_path = str(Path(reference).parent / "evidence.json").replace("\\", "/")
        candidate = read_document(root, evidence_path, {}, required=True)
        if (
            candidate.get("plan_sha256") != result["plan_sha256"]
            or candidate.get("schema_version") != 1
        ):
            raise ValueError("evidence run references a different plan")
        if not isinstance(candidate.get("results"), list):
            raise ValueError("invalid run evidence results")
        metadata = evidence_run["metadata"]
        if metadata["inputs"].get("plan") != result["plan_sha256"]:
            raise ValueError("run metadata plan digest mismatch")
        expected_inputs = {
            p: record["sha256"]
            for p, record in records.items()
            if record["state"] == "present"
        }
        if any(
            metadata["inputs"].get(p) != value for p, value in expected_inputs.items()
        ):
            raise ValueError("run metadata configuration digest mismatch")
        covered = {
            row.get("ac") for row in candidate["results"] if isinstance(row, dict)
        }
        scenarios = {
            row.get("scenario")
            for row in candidate["results"]
            if isinstance(row, dict) and row.get("scenario") is not None
        }
        if set(metadata.get("acceptance", [])) != covered:
            raise ValueError("run metadata acceptance coverage mismatch")
        if (
            set(metadata.get("scenarios", [metadata["scenario"]])) != scenarios
            and scenarios
        ):
            raise ValueError("run metadata scenario coverage mismatch")
        if phase in {"acceptance", "release"} and metadata["source"] != source_snapshot(
            root
        ):
            raise ValueError("evidence source snapshot is stale")
        row_outcomes = {
            row.get("verdict") for row in candidate["results"] if isinstance(row, dict)
        }
        expected_outcome = (
            "FAIL"
            if "FAIL" in row_outcomes
            else "BLOCKED"
            if "BLOCKED" in row_outcomes
            else "PASS"
        )
        if evidence_run["outcome"] != expected_outcome:
            raise ValueError("terminal outcome is inconsistent with evidence rows")
        prefix = Path(reference).parent.as_posix() + "/"
        for row in candidate["results"]:
            for artifact in row.get("artifacts", []):
                if not artifact.get("path", "").startswith(prefix):
                    raise ValueError(
                        "evidence artifact must belong to its finalized run"
                    )
        bundles.append(candidate)
    bundle = {
        "schema_version": 1,
        "plan_sha256": result["plan_sha256"],
        "results": [row for candidate in bundles for row in candidate["results"]],
    }
    if (
        type(bundle.get("schema_version")) is not int
        or bundle.get("schema_version") != 1
        or bundle.get("plan_sha256") != result["plan_sha256"]
        or not isinstance(bundle.get("results"), list)
    ):
        raise ValueError("evidence bundle is missing or bound to a stale plan")
    _evaluate(root, result, bundle, phase)


def artifact_hash(path):
    """Stream large raw traces instead of loading entire captures into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _evidence_row(root, result, row):
    if not isinstance(row, dict):
        raise ValueError("invalid evidence result")
    key = (row.get("ac"), row.get("layer"), row.get("scenario"), row.get("purpose"))
    ac, layer, scenario, purpose = key
    item = result["plan"]["acceptance"].get(ac)
    if (
        item is None
        or layer not in item["layers"]
        or purpose not in {"acceptance", "enablement", "release"}
    ):
        raise ValueError("unknown AC, layer or evidence purpose")
    allowed = (
        item["enablement_scenarios"]
        if purpose == "enablement"
        else item["scenario_layers"].get(layer, [None])
    )
    if scenario not in allowed:
        raise ValueError("unknown or unmapped evidence scenario")
    if row.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}:
        raise ValueError("unknown evidence verdict")
    if row.get("complete") is not True or not row.get("artifacts"):
        raise ValueError(f"incomplete evidence: {key}")
    artifacts = row["artifacts"]
    if not isinstance(artifacts, list):
        raise ValueError("artifacts must be a list")
    for artifact in artifacts:
        target = project_path(root, artifact["path"])
        if not target.is_file() or artifact_hash(target) != artifact.get("sha256"):
            raise ValueError("missing or stale evidence artifact")
    if layer in DEVICE_LAYERS:
        build = project_path(root, item["build_artifact"])
        if (
            row.get("execution_profile") not in item["execution_profiles"]
            or not build.is_file()
            or row.get("build_sha256") != artifact_hash(build)
        ):
            raise ValueError("device build/profile evidence mismatch")
        runner_path = row.get("runner_result")
        if runner_path not in [a["path"] for a in artifacts]:
            raise ValueError("device evidence must include a hashed runner_result")
        runner = read_document(root, runner_path, {}, required=True)
        binding = result["plan"]["binding"]
        if (
            runner.get("scenario") != scenario
            or runner.get("phase")
            != ("acceptance" if purpose == "release" else purpose)
            or runner.get("verdict")
            != ("PASS" if purpose == "release" else row["verdict"])
            or runner.get("profile_sha256") != binding["device_profile_sha256"]
        ):
            raise ValueError("runner result scenario/phase/verdict/profile mismatch")
    if purpose == "release":
        report_path = row.get("release_report")
        if report_path not in [a["path"] for a in artifacts]:
            raise ValueError("release requires a separate hashed release_report")
        report = read_document(root, report_path, {}, required=True)
        checks = report.get("checks", {})
        required_checks = {
            "test_only_wiring_absent",
            "release_build",
            "regression",
            "architecture",
            "analyzer",
            "size",
            "safety",
        }
        if (
            report.get("gate") != "Release Acceptance"
            or report.get("verdict") != row["verdict"]
            or report.get("plan_sha256") != result["plan_sha256"]
            or not isinstance(checks, dict)
            or set(checks) != required_checks
            or any(v not in {"PASS", "FAIL", "BLOCKED"} for v in checks.values())
        ):
            raise ValueError(
                "release report is incomplete or not bound to the current plan"
            )
        verdict = (
            "FAIL"
            if "FAIL" in checks.values()
            else "BLOCKED"
            if "BLOCKED" in checks.values()
            else "PASS"
        )
        if report["verdict"] != verdict:
            raise ValueError("release report verdict disagrees with its checks")
        if layer in DEVICE_LAYERS and report.get("build_sha256") != row.get(
            "build_sha256"
        ):
            raise ValueError("release report build does not match the validated build")
    return key, row["verdict"]


def _evaluate(root, result, bundle, phase):
    seen = set()
    valid = set()
    failed = False
    for row in bundle["results"]:
        # Later phases must not prevent already-enabled implementation progress.
        if isinstance(row, dict):
            if phase == "enablement" and row.get("purpose") in {
                "acceptance",
                "release",
            }:
                continue
            if phase == "acceptance" and row.get("purpose") == "release":
                continue
        try:
            key, verdict = _evidence_row(root, result, row)
            if verdict == "FAIL":
                failed = True
            if key in seen:
                valid.discard(key)
                raise ValueError("duplicate evidence result")
            seen.add(key)
            if verdict == "PASS":
                valid.add(key)
            elif verdict == "BLOCKED":
                result["errors"].append(f"blocked evidence: {key}")
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            result["errors"].append(str(exc))
    for ac, item in result["plan"]["acceptance"].items():
        for prerequisite in item["enablement_scenarios"]:
            if not any(
                k[0] == ac and k[2:] == (prerequisite, "enablement") for k in valid
            ):
                result["errors"].append(f"{ac}: missing enablement {prerequisite}")
        if phase == "enablement":
            continue
        for layer in item["layers"]:
            for scenario in item["scenario_layers"].get(layer, [None]):
                if (ac, layer, scenario, "acceptance") not in valid:
                    result["errors"].append(
                        f"{ac}: missing acceptance {layer}/{scenario}"
                    )
        passed = {k[1] for k in valid if k[0] == ac and k[3] == "acceptance"}
        for claim in item["claims"]:
            result["errors"].extend(assess_evidence(claim, passed).get("errors", []))
        if phase == "release" and not any(
            k[0] == ac and k[3] == "release" for k in valid
        ):
            result["errors"].append(f"{ac}: separate release acceptance missing")
    result["verdict"] = "FAIL" if failed else "BLOCKED" if result["errors"] else "PASS"
    result["evidence_trust"] = (
        "caller-supplied-artifacts-not-authenticated-observations"
    )


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--spec")
    parser.add_argument(
        "--phase",
        choices=["planning", "enablement", "acceptance", "release"],
        default="planning",
    )
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--candidate-stdin", action="store_true")
    args = parser.parse_args()
    result = assess_project(
        args.project_root,
        args.spec,
        phase=args.phase,
        candidate_text=sys.stdin.read() if args.candidate_stdin else None,
    )
    if args.write_plan:
        if (
            args.phase != "planning"
            or result["verdict"] != "PASS"
            or "plan" not in result
        ):
            result.update(
                verdict="BLOCKED", errors=["only a valid planning result can be saved"]
            )
        else:
            root = args.project_root.resolve()
            spec_id = result["plan"]["binding"]["spec_id"]
            try:
                layout = read_document(
                    root, "validation/layout.yaml", {}, required=True
                )
                bindings = [
                    b
                    for b in layout.get("output_bindings", [])
                    if b.get("writer") == "project_validation"
                    and b.get("root") == "artifacts/validation"
                ]
                if len(bindings) != 1:
                    raise ValueError(
                        "declare exactly one project_validation output target"
                    )
                metadata = {
                    "target": bindings[0].get("target"),
                    "scenario": "validation-planning",
                    "tool": {"name": "project_validation", "version": "1"},
                    "command": [
                        "project_validation.py",
                        "--write-plan",
                        "--spec",
                        args.spec,
                    ],
                    "source": source_snapshot(root),
                    "inputs": {"plan": result["plan_sha256"]},
                    "spec": spec_id,
                    "acceptance": sorted(result["plan"]["acceptance"]),
                }
                run = allocate_run(root, "validation", metadata=metadata)
                (run / "plan.snapshot.json").write_text(
                    json.dumps(result["plan"], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                finalize_run(root, run, "PASS")
                reference = (run / "manifest.json").relative_to(root).as_posix()
                selection = project_path(
                    root, f"validation/run-references-{spec_id}.json"
                )
                # This is an authored selection, not a mutable evidence identity.
                # Explicit --write-plan selects the newly returned fixed run.
                selection.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "plan_manifest": reference,
                            "evidence_manifests": [],
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                result["plan_manifest"] = reference
            except (OSError, ValueError) as exc:
                result.update(verdict="BLOCKED", errors=[str(exc)])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
