import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(
    0,
    str(
        (
            next(
                p
                for p in Path(__file__).resolve().parents
                if (p / "CLAUDE.md").is_file()
            )
            / "skills/engineering/verification-ladder"
        )
        / "scripts"
    ),
)
import project_validation as validation
from run_storage import allocate_run, finalize_run, source_snapshot
from test_verification_ladder import base_matrix

SOURCE_SKILLS = (
    next(p for p in Path(__file__).resolve().parents if (p / "CLAUDE.md").is_file())
    / "skills/engineering"
)
TEST_TEMP_ROOT = SOURCE_SKILLS.parent.parent / ".test-tmp" / "project-validation"
TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SOURCE_SKILLS / "engineering-risk-routing/scripts"))
sys.path.insert(0, str(SOURCE_SKILLS / "spec-governance/scripts"))
from guided_workflow_router import route
import spec_contract as lifecycle
from managed_delivery import execute_request
from spec_contract import assess_spec_evidence_update
from project_validation_adapter import assess_project_validation

SPEC = """---
spec_version: 1
spec_id: SPEC-0001
revision: 1
status: confirmed
change_set: sensor
---
# Sensor acceptance
## Problem
Confirm sensor timing.
## Solution
Use production device evidence.
## User Stories
- Operator observes actual sample rate.
## Requirements
| ID | Requirement |
|---|---|
| REQ-001 | Physical sample timing is correct. |
## Decisions
| ID | Decision |
|---|---|
| DEC-001 | Use production profile. |
## Discussion Context
### DISC-001: Timing
- **Situation:** Physical timing needs validation.
- **Question:** What evidence is required?
- **Options and tradeoffs:** Real hardware proves timing; fake hardware does not.
- **User answer:** Use the production device.
- **Explicit rationale:** Timing depends on real peripherals.
- **Resulting impact:** REQ-001, DEC-001, AC-001.
## Acceptance Criteria
| ID | Requirements | Criterion | Validation Method | Evidence |
|---|---|---|---|---|
| AC-001 | REQ-001 | Timing is correct. | Device scenario. | Pending |
## Relationships
None.
## Out of Scope
Other sensors.
## Open Decisions
None.
## Routing/Gates
Spec review: pending
## Revision History
| Revision | Date | Change |
|---|---|---|
| 1 | 2026-09-16 | Initial. |
"""


def write(root, path, data):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        data if isinstance(data, str) else json.dumps(data), encoding="utf-8"
    )


def run_metadata(root):
    return {
        "target": {"module": "processing"},
        "scenario": "fixture",
        "tool": {"name": "test-fixture", "version": "1"},
        "command": ["unittest-fixture"],
        "source": source_snapshot(root),
        "inputs": {},
        "spec": "SPEC-0001",
        "acceptance": ["AC-001"],
    }


def publish_evidence(root, value):
    import shutil

    bundle = copy.deepcopy(value)
    metadata = run_metadata(root)
    planned = validation.assess_project(root, "specs/SPEC-0001-sensor.md")
    metadata["inputs"] = {
        "plan": bundle["plan_sha256"],
        **{
            p: r["sha256"]
            for p, r in planned["documents"].items()
            if r["state"] == "present"
        },
    }
    metadata["acceptance"] = sorted({r["ac"] for r in bundle["results"]})
    metadata["scenarios"] = sorted(
        {r["scenario"] for r in bundle["results"] if r.get("scenario")}
    )
    run = allocate_run(root, "validation", metadata=metadata)
    for row in bundle["results"]:
        for artifact in row.get("artifacts", []):
            old = artifact["path"]
            source = root / old
            destination = run / "reports" / Path(old).name
            destination.parent.mkdir(exist_ok=True)
            if source.is_file():
                shutil.copyfile(source, destination)
            artifact["path"] = destination.relative_to(root).as_posix()
            for field in ("runner_result", "release_report"):
                if row.get(field) == old:
                    row[field] = artifact["path"]
    write(root, (run / "evidence.json").relative_to(root).as_posix(), bundle)
    outcomes = {row.get("verdict") for row in bundle["results"]}
    finalize_run(
        root,
        run,
        "FAIL"
        if "FAIL" in outcomes
        else "BLOCKED"
        if "BLOCKED" in outcomes
        else "PASS",
    )
    selected = json.loads(
        (root / "validation/run-references-SPEC-0001.json").read_text()
    )
    selected["evidence_manifests"] = [
        (run / "manifest.json").relative_to(root).as_posix()
    ]
    write(root, "validation/run-references-SPEC-0001.json", selected)


def fixture(root):
    write(
        root,
        "architecture/adoption.yaml",
        {
            "runtime_validation": {
                "applicability": "required",
                "rationale": "Production timing",
            }
        },
    )
    write(
        root,
        "architecture/manifest.yaml",
        {
            "modules": [{"id": "processing"}],
            "flows": [{"id": "processing-flow"}],
            "execution_profiles": [{"id": "target-a"}],
        },
    )
    write(root, "validation/verification-ladder.yaml", base_matrix())
    write(
        root,
        "validation/on-device.yaml",
        {
            "architecture": {"execution_profile": "target-a"},
            "scenarios": [
                {"id": "pil-cost", "phase": "acceptance", "prerequisites": ["setup"]},
                {"id": "hil-timing", "phase": "acceptance", "prerequisites": ["setup"]},
                {"id": "setup", "phase": "enablement"},
            ],
        },
    )
    write(root, "specs/SPEC-0001-sensor.md", SPEC)
    write(
        root,
        "validation/acceptance-SPEC-0001.json",
        {
            "schema_version": 1,
            "spec_id": "SPEC-0001",
            "acceptance": {
                "AC-001": {
                    "evidence_claims": ["production-timing"],
                    "rationale": "Real peripheral scheduling",
                    "scenario_layers": {"pil": ["pil-cost"], "hil": ["hil-timing"]},
                    "build_artifact": "build/firmware.bin",
                    "enablement_scenarios": ["setup"],
                }
            },
        },
    )
    write(root, "build/firmware.bin", "production build")
    (root / "spec-governance").mkdir()
    write(
        root,
        "validation/layout.yaml",
        {
            "schema_version": 1,
            "entries": [
                {"include": ["architecture/**"], "role": "metadata"},
                {"include": ["validation/**"], "role": "validation-definition"},
                {"include": ["specs/**"], "role": "specification"},
                {"include": ["spec-governance/**"], "role": "governance-state"},
                {
                    "include": ["build/**"],
                    "role": "generated",
                    "provenance": "test-authored build input",
                },
                {
                    "include": ["tests/modules/processing/support/**"],
                    "role": "fixture",
                    "owner": "processing",
                    "provenance": "test-authored expected evidence input",
                },
                {"include": ["artifacts/validation/**"], "role": "run-output"},
            ],
            "required_analyzers": [],
            "references": [],
            "output_bindings": [],
            "external_resources": [],
        },
    )


def save_plan(root):
    assessment = validation.assess_project(root, "specs/SPEC-0001-sensor.md")
    if assessment["verdict"] != "PASS":
        raise AssertionError(assessment)
    run = allocate_run(root, "validation", metadata=run_metadata(root))
    write(
        root,
        (run / "plan.snapshot.json").relative_to(root).as_posix(),
        assessment["plan"],
    )
    finalize_run(root, run, "PASS")
    write(
        root,
        "validation/run-references-SPEC-0001.json",
        {
            "schema_version": 1,
            "plan_manifest": (run / "manifest.json").relative_to(root).as_posix(),
            "evidence_manifests": [],
        },
    )
    return assessment


def evidence(root, planned):
    result = {"schema_version": 1, "plan_sha256": planned["plan_sha256"], "results": []}
    for layer, scenario, purpose in [
        ("hil", "setup", "enablement"),
        ("pil", "pil-cost", "acceptance"),
        ("hil", "hil-timing", "acceptance"),
    ]:
        runner_path = f"tests/modules/processing/support/{scenario}.json"
        write(
            root,
            runner_path,
            {
                "scenario": scenario,
                "phase": purpose,
                "verdict": "PASS",
                "profile_sha256": planned["plan"]["binding"]["device_profile_sha256"],
            },
        )
        result["results"].append(
            {
                "ac": "AC-001",
                "layer": layer,
                "scenario": scenario,
                "purpose": purpose,
                "verdict": "PASS",
                "complete": True,
                "execution_profile": "target-a",
                "build_sha256": hashlib.sha256(
                    (root / "build/firmware.bin").read_bytes()
                ).hexdigest(),
                "runner_result": runner_path,
                "artifacts": [
                    {
                        "path": runner_path,
                        "sha256": hashlib.sha256(
                            (root / runner_path).read_bytes()
                        ).hexdigest(),
                    }
                ],
            }
        )
    publish_evidence(root, result)
    return result


def fail_row(root, row):
    row["verdict"] = "FAIL"
    path = row["runner_result"]
    runner = json.loads((root / path).read_text())
    runner["verdict"] = "FAIL"
    write(root, path, runner)
    row["artifacts"][0]["sha256"] = hashlib.sha256(
        (root / path).read_bytes()
    ).hexdigest()


class ProjectValidationTests(unittest.TestCase):
    def test_source_change_invalidates_terminal_acceptance(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            planned = save_plan(root)
            evidence(root, planned)
            self.assertEqual(
                validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                )["verdict"],
                "PASS",
            )
            write(root, "build/extra_source.py", "changed = True")
            result = validation.assess_project(
                root, "specs/SPEC-0001-sensor.md", phase="acceptance"
            )
            self.assertEqual(result["verdict"], "BLOCKED")
            self.assertIn("source snapshot", " ".join(result["errors"]))

    def test_validly_hashed_metadata_must_match_bundle(self):
        from unittest.mock import patch
        import run_storage

        for field in ("plan", "configuration", "acceptance", "scenarios"):
            with (
                self.subTest(field=field),
                tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory,
            ):
                root = Path(directory)
                fixture(root)
                planned = save_plan(root)
                bundle = evidence(root, planned)
                original = allocate_run

                def allocate(*args, **kwargs):
                    metadata = kwargs["metadata"]
                    if field == "plan":
                        metadata["inputs"]["plan"] = "0" * 64
                    elif field == "configuration":
                        metadata["inputs"].pop("validation/layout.yaml")
                    elif field == "acceptance":
                        metadata["acceptance"] = ["AC-999"]
                    else:
                        metadata["scenarios"] = ["unrelated"]
                    return original(*args, **kwargs)

                with patch(__name__ + ".allocate_run", side_effect=allocate):
                    publish_evidence(root, bundle)
                result = validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                )
                self.assertEqual(result["verdict"], "BLOCKED")
                self.assertIn("metadata", " ".join(result["errors"]))

    def test_required_policy_cannot_disappear_without_matrix(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            (root / "architecture").mkdir()
            (root / "architecture/adoption.yaml").write_text(
                yaml.safe_dump(
                    {
                        "runtime_validation": {
                            "applicability": "required",
                            "rationale": "Physical acceptance",
                        }
                    }
                ),
                encoding="utf-8",
            )
            result = validation.assess_project(root)
            self.assertEqual(result["verdict"], "BLOCKED")
            self.assertIn("verification-ladder", result["required_gates"])
            self.assertTrue(any("matrix" in error for error in result["errors"]))

    def test_planning_allows_work_but_acceptance_requires_hil(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            planned = save_plan(root)
            enabled = evidence(root, planned)
            enabled["results"] = enabled["results"][:1]
            publish_evidence(root, enabled)
            self.assertEqual(planned["required_layers"], ["pil", "hil"])
            self.assertEqual(
                validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="enablement"
                )["verdict"],
                "PASS",
            )
            self.assertEqual(
                validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                )["verdict"],
                "BLOCKED",
            )
            evidence(root, planned)
            self.assertEqual(
                validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                )["verdict"],
                "PASS",
            )

    def test_host_build_smoke_partial_wrong_profile_and_stale_artifacts_do_not_pass(
        self,
    ):
        cases = [
            "host",
            "smoke",
            "partial",
            "profile",
            "build",
            "artifact",
            "incomplete",
            "duplicate",
            "stale-plan",
        ]
        for case in cases:
            with (
                self.subTest(case=case),
                tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory,
            ):
                root = Path(directory)
                fixture(root)
                bundle = evidence(root, save_plan(root))
                row = bundle["results"][-1]
                if case == "host":
                    row["layer"] = "module-contract"
                if case == "smoke":
                    row["purpose"] = "smoke"
                if case == "partial":
                    bundle["results"].pop()
                if case == "profile":
                    row["execution_profile"] = "different"
                if case == "build":
                    write(root, "build/firmware.bin", "new build")
                if case == "artifact":
                    write(
                        root,
                        "tests/modules/processing/support/hil-timing.json",
                        "changed",
                    )
                if case == "incomplete":
                    row["complete"] = False
                if case == "duplicate":
                    bundle["results"].append(copy.deepcopy(row))
                if case == "stale-plan":
                    bundle["plan_sha256"] = "0" * 64
                publish_evidence(root, bundle)
                self.assertEqual(
                    validation.assess_project(
                        root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                    )["verdict"],
                    "BLOCKED",
                )

    def test_complete_violation_remains_fail_even_when_other_layer_missing(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            bundle = evidence(root, save_plan(root))
            bundle["results"] = [bundle["results"][-1]]
            fail_row(root, bundle["results"][0])
            publish_evidence(root, bundle)
            self.assertEqual(
                validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                )["verdict"],
                "FAIL",
            )

    def test_reload_detects_policy_and_spec_changes_without_mutation(self):
        for relative in [
            "architecture/adoption.yaml",
            "architecture/manifest.yaml",
            "validation/on-device.yaml",
            "specs/SPEC-0001-sensor.md",
        ]:
            with (
                self.subTest(path=relative),
                tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory,
            ):
                root = Path(directory)
                fixture(root)
                baseline = save_plan(root)
                evidence(root, baseline)
                self.assertEqual(
                    save_plan(root)["plan_sha256"], baseline["plan_sha256"]
                )
                path = root / relative
                path.write_text(
                    path.read_text(encoding="utf-8") + "\n", encoding="utf-8"
                )
                result = validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                )
                self.assertEqual(result["verdict"], "BLOCKED")
                self.assertTrue(any("stale" in x for x in result["errors"]))

    def test_explicit_host_only_mapping_avoids_device_layers(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            mapping = {
                "schema_version": 1,
                "spec_id": "SPEC-0001",
                "acceptance": {
                    "AC-001": {
                        "evidence_claims": ["host-semantics"],
                        "rationale": "This change checks configuration selection only; no physical claim.",
                    }
                },
            }
            write(root, "validation/acceptance-SPEC-0001.json", mapping)
            result = validation.assess_project(root, "specs/SPEC-0001-sensor.md")
            self.assertEqual(result["verdict"], "PASS")
            self.assertEqual(result["required_layers"], ["module-contract", "sil"])
            self.assertNotIn("validate-on-device", result["required_gates"])
            text = (root / "specs/SPEC-0001-sensor.md").read_text(encoding="utf-8")
            _, _, rows = validation.spec_contract(text)
            names = ["id", "requirements", "criterion", "validation method", "evidence"]
            criterion = {
                name: value
                for name, value in zip(names, rows["AC-001"], strict=True)
                if name != "evidence"
            }
            mapping["acceptance"]["AC-001"]["criterion_sha256"] = validation.digest(
                criterion
            )
            write(root, "validation/acceptance-SPEC-0001.json", mapping)
            self.assertEqual(
                "PASS",
                validation.assess_project(root, "specs/SPEC-0001-sensor.md")["verdict"],
            )
            mapping["acceptance"]["AC-001"]["criterion_sha256"] = "0" * 64
            write(root, "validation/acceptance-SPEC-0001.json", mapping)
            self.assertEqual(
                "BLOCKED",
                validation.assess_project(root, "specs/SPEC-0001-sensor.md")["verdict"],
            )

    def test_unknown_claim_and_missing_ac_mapping_block(self):
        for case in ["unknown", "missing"]:
            with (
                self.subTest(case=case),
                tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory,
            ):
                root = Path(directory)
                fixture(root)
                path = root / "validation/acceptance-SPEC-0001.json"
                mapping = json.loads(path.read_text())
                if case == "unknown":
                    mapping["acceptance"]["AC-001"]["evidence_claims"] = [
                        "unrecognized"
                    ]
                else:
                    mapping["acceptance"] = {}
                write(root, str(path.relative_to(root)), mapping)
                self.assertEqual(
                    validation.assess_project(root, "specs/SPEC-0001-sensor.md")[
                        "verdict"
                    ],
                    "BLOCKED",
                )

    def test_short_commands_keep_project_gates(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            write(root, "app.py", "print('firmware fixture')")
            for prompt in ["開始執行", "繼續", "重新載入技能"]:
                result = route(
                    prompt,
                    root,
                    tracker_spec_path="specs/SPEC-0001-sensor.md",
                    turn_kind="read-only",
                )
                self.assertIn("verification-ladder", result["required_gates"])
                self.assertIn("validate-on-device", result["required_gates"])

    def test_confirmed_evidence_only_update_cannot_bypass_assessment(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            planned = save_plan(root)
            candidate = SPEC.replace("| Pending |", "| PASS host tests |")
            self.assertEqual(
                assess_spec_evidence_update(
                    root, candidate, validation_assessor=assess_project_validation
                )["verdict"],
                "BLOCKED",
            )
            evidence(root, planned)
            self.assertEqual(
                assess_spec_evidence_update(
                    root, candidate, validation_assessor=assess_project_validation
                )["verdict"],
                "PASS",
            )
            changed = candidate.replace(
                "Physical sample timing is correct.",
                "Different production requirement.",
            )
            self.assertEqual(
                assess_spec_evidence_update(
                    root, changed, validation_assessor=assess_project_validation
                )["verdict"],
                "BLOCKED",
            )

    def test_release_is_separate_from_runtime_acceptance(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            evidence(root, save_plan(root))
            self.assertEqual(
                validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                )["verdict"],
                "PASS",
            )
            self.assertEqual(
                validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="release"
                )["verdict"],
                "BLOCKED",
            )

    def test_enablement_does_not_wait_for_final_hil_and_fail_precedence_is_order_independent(
        self,
    ):
        for reverse in [False, True]:
            with (
                self.subTest(reverse=reverse),
                tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory,
            ):
                root = Path(directory)
                fixture(root)
                bundle = evidence(root, save_plan(root))
                fail_row(root, bundle["results"][-1])
                bad = copy.deepcopy(bundle["results"][1])
                bad["artifacts"][0]["sha256"] = "0" * 64
                bundle["results"].append(bad)
                if reverse:
                    bundle["results"].reverse()
                publish_evidence(root, bundle)
                self.assertEqual(
                    validation.assess_project(
                        root, "specs/SPEC-0001-sensor.md", phase="enablement"
                    )["verdict"],
                    "PASS",
                )
                self.assertEqual(
                    validation.assess_project(
                        root, "specs/SPEC-0001-sensor.md", phase="acceptance"
                    )["verdict"],
                    "FAIL",
                )

    def test_governed_direct_library_without_injection_fails_closed(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            evidence(root, save_plan(root))
            self.assertEqual(
                assess_spec_evidence_update(
                    root, SPEC.replace("| Pending |", "| PASS host |")
                )["verdict"],
                "BLOCKED",
            )
            (root / "architecture/adoption.yaml").write_text(
                "invalid:", encoding="utf-8"
            )
            self.assertEqual(
                lifecycle.assess_project_validation(root)["verdict"], "BLOCKED"
            )

    def test_lifecycle_and_managed_completion_reject_host_only_pass(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            started = lifecycle.start_working_bundle(
                root, "sensor", SPEC, task_ref="test", preserve_spec_identity=True
            )
            self.assertEqual(started["verdict"], "PASS", started)
            w = started["working_spec"]
            materialized = lifecycle.materialize_working_bundle(
                root,
                w["working_id"],
                expected_revision=w["revision"],
                expected_hash=w["snapshot_hash"],
                validation_assessor=assess_project_validation,
            )
            self.assertEqual(materialized["verdict"], "PASS", materialized)
            w = materialized["working_spec"]
            planned = save_plan(root)
            bundle = evidence(root, planned)
            full_bundle = copy.deepcopy(bundle)
            bundle["results"] = bundle["results"][:1]
            publish_evidence(root, bundle)
            canonical = root / "specs/SPEC-0001-sensor.md"
            baseline = canonical.read_bytes()
            base = {
                "task_ref": "test",
                "spec": "specs/SPEC-0001-sensor.md",
                "working_reference": w["working_id"],
            }
            auth = execute_request(
                root,
                base
                | {
                    "operation": "authorize",
                    "instruction": "開始執行",
                    "source_event_id": "fixture-user",
                    "expected_hash": hashlib.sha256(baseline).hexdigest(),
                },
                validation_assessor=assess_project_validation,
            )
            self.assertEqual(auth["verdict"], "PASS", auth)
            self.assertEqual(
                execute_request(
                    root,
                    base | {"operation": "complete"},
                    validation_assessor=assess_project_validation,
                )["verdict"],
                "BLOCKED",
            )
            # The actual state-changing API must block before writing anything.
            implemented = lifecycle.mark_spec_implemented(
                canonical,
                {"AC-001": "PASS host tests"},
                spec_review_passed=True,
                authorized=True,
                validation_assessor=assess_project_validation,
            )
            self.assertEqual(implemented["verdict"], "BLOCKED", implemented)
            self.assertEqual(canonical.read_bytes(), baseline)
            snapshot = root / w["snapshot_path"]
            before = snapshot.read_bytes()
            update = lifecycle.reconcile_working_bundle(
                root,
                w["working_id"],
                before.decode().replace("| Pending |", "| PASS host tests |"),
                {
                    "added_ids": [],
                    "changed_ids": ["AC-001"],
                    "removed_ids": [],
                    "conflicts": [],
                    "open_decisions": [],
                },
                expected_revision=w["revision"],
                expected_hash=w["snapshot_hash"],
                validation_assessor=assess_project_validation,
            )
            self.assertEqual(update["verdict"], "BLOCKED", update)
            self.assertEqual(snapshot.read_bytes(), before)
            # Direct materialization with unsupported PASS is also rejected.
            direct = lifecycle.materialize_spec(
                root,
                "other",
                SPEC.replace("sensor", "other").replace(
                    "| Pending |", "| PASS host tests |"
                ),
                validation_assessor=assess_project_validation,
            )
            self.assertEqual(direct["verdict"], "BLOCKED", direct)
            publish_evidence(root, full_bundle)
            self.assertEqual(
                execute_request(
                    root,
                    base | {"operation": "complete"},
                    validation_assessor=assess_project_validation,
                )["verdict"],
                "PASS",
            )
            request = root / "spec-governance/request.json"
            request.write_text(
                json.dumps(base | {"operation": "complete"}), encoding="utf-8"
            )
            cli = SOURCE_SKILLS / "implement/scripts/project_validation_workflow.py"
            run = subprocess.run(
                [
                    sys.executable,
                    str(cli),
                    "managed",
                    "--",
                    "--project-root",
                    str(root),
                    "--request",
                    str(request),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            direct_cli = SOURCE_SKILLS / "implement/scripts/managed_delivery.py"
            run = subprocess.run(
                [
                    sys.executable,
                    str(direct_cli),
                    "--project-root",
                    str(root),
                    "--request",
                    str(request),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(run.returncode, 0)
            implemented = lifecycle.mark_spec_implemented(
                canonical,
                {"AC-001": "PASS validated device bundle"},
                spec_review_passed=True,
                authorized=True,
                validation_assessor=assess_project_validation,
            )
            self.assertEqual(implemented["verdict"], "PASS", implemented)

    def test_mapping_schema_and_runtime_agree_on_invalid_version(self):

        schema = json.loads(
            (
                SOURCE_SKILLS
                / "verification-ladder/references/project-validation.schema.json"
            ).read_text()
        )
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            path = root / "validation/acceptance-SPEC-0001.json"
            mapping = json.loads(path.read_text())
            self.assertEqual(
                schema["required"], ["schema_version", "spec_id", "acceptance"]
            )
            self.assertEqual(schema["properties"]["schema_version"], {"const": 1})
            mapping["schema_version"] = True
            write(root, str(path.relative_to(root)), mapping)
            self.assertEqual(
                validation.assess_project(root, "specs/SPEC-0001-sensor.md")["verdict"],
                "BLOCKED",
            )

    def test_release_wraps_real_acceptance_runner_instead_of_nonexistent_release_phase(
        self,
    ):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            planned = save_plan(root)
            bundle = evidence(root, planned)
            row = copy.deepcopy(bundle["results"][-1])
            row["purpose"] = "release"
            row["release_report"] = "tests/modules/processing/support/release.json"
            report = {
                "gate": "Release Acceptance",
                "verdict": "PASS",
                "plan_sha256": planned["plan_sha256"],
                "build_sha256": row["build_sha256"],
                "checks": {
                    k: "PASS"
                    for k in [
                        "test_only_wiring_absent",
                        "release_build",
                        "regression",
                        "architecture",
                        "analyzer",
                        "size",
                        "safety",
                    ]
                },
            }
            write(root, row["release_report"], report)
            row["artifacts"].append(
                {
                    "path": row["release_report"],
                    "sha256": hashlib.sha256(
                        (root / row["release_report"]).read_bytes()
                    ).hexdigest(),
                }
            )
            bundle["results"].append(row)
            publish_evidence(root, bundle)
            self.assertEqual(
                validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="release"
                )["verdict"],
                "PASS",
            )
            report["checks"]["test_only_wiring_absent"] = "FAIL"
            report["verdict"] = row["verdict"] = "FAIL"
            write(root, row["release_report"], report)
            row["artifacts"][-1]["sha256"] = hashlib.sha256(
                (root / row["release_report"]).read_bytes()
            ).hexdigest()
            publish_evidence(root, bundle)
            self.assertEqual(
                validation.assess_project(
                    root, "specs/SPEC-0001-sensor.md", phase="release"
                )["verdict"],
                "FAIL",
            )

    def test_implemented_transition_records_review_when_placeholder_was_absent(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            fixture(root)
            path = root / "specs/SPEC-0001-sensor.md"
            write(
                root,
                str(path.relative_to(root)),
                SPEC.replace("Spec review: pending", "Require code review."),
            )
            evidence(root, save_plan(root))
            result = lifecycle.mark_spec_implemented(
                path,
                {"AC-001": "PASS validated bundle"},
                spec_review_passed=True,
                authorized=True,
                validation_assessor=assess_project_validation,
            )
            self.assertEqual(result["verdict"], "PASS", result)
            self.assertIn("Spec review: PASS", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
