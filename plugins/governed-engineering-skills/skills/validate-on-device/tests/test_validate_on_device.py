from __future__ import annotations

import json
import hashlib
import re
import socket
import sys
import tempfile
import threading
import unittest
import copy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vod.evidence import evaluate, write_bundle
from vod.guided import profile_sha256
from vod.execution import run_action
from vod.model import Verdict, overall_gates
from vod.profile import redact, required_samples, validate_architecture_references, validate_local_override, validate_profile
from vod.providers import capture_tcp, probe
from validate_on_device import _external_contract_refs


def profile() -> dict:
    return {
        "version": "1.0",
        "target": {"platform": "windows", "provider": "structured-log", "fallback": "structured-log"},
        "transport": {"type": "import", "timeout_seconds": 30, "max_bytes": 100000},
        "actions": {
            "flash": {"executable": "missing-tool", "args": ["upload"], "risk": "flash", "timeout_seconds": 10}
        },
        "scenarios": [
            {
                "id": "boot",
                "phase": "enablement",
                "evidence_mode": "mixed",
                "max_duration_ms": 30000,
                "completion": {
                    "trigger_criteria": ["trigger"],
                    "required_criteria": ["flow", "latency"],
                    "session_end_reason": "complete",
                },
                "prerequisites": [],
                "architecture_refs": ["FLOW-BOOT-001"],
                "forbidden_patterns": ["WATCHDOG"],
                "criteria": [
                    {"id": "trigger", "type": "event_sequence", "events": ["started"]},
                    {"id": "flow", "type": "event_sequence", "events": ["started", "ready"]},
                    {
                        "id": "latency",
                        "type": "statistic",
                        "metric": "latency_us",
                        "method": "percentile",
                        "percentile": 0.95,
                        "operator": "<=",
                        "threshold": 50,
                        "sample_plan": {"basis": "external-standard", "reference": "TEST-SAMPLE-100", "min_samples": 100},
                        "max_duration_ms": 30000,
                        "confidence": 0.95,
                        "timing": True,
                        "instrumentation_budget": {
                            "update_cycles_max": 100,
                            "snapshot_us": 500,
                            "log_bytes": 1000,
                            "allocation_count": 0,
                            "isr_log_writes": 0,
                            "critical_section_us": 10,
                        },
                        "clock": {"source": "cycle_counter", "hz": 240000000, "resolution_ns": 4},
                    },
                ],
            }
        ],
    }


def good_log() -> str:
    return "\n".join(
        [
            "VAL_SESSION_BEGIN run=R1 scenario=boot observer=user t_ms=0 seq=1",
            "VAL_EVENT name=started t_ms=1 seq=2",
            "VAL_EVENT name=ready t_ms=2 seq=3",
            "VAL_STATS metric=latency_us window_start_ms=0 n=100 min=10 max=60 sum=3000 sum_sq=100000 errors=0 unit=us t_ms=100 seq=4",
            "VAL_BUCKET metric=latency_us le=25 count=20 t_ms=100 seq=5",
            "VAL_BUCKET metric=latency_us le=50 count=80 t_ms=100 seq=6",
            "VAL_STATS_META metric=latency_us update_cycles_max=80 snapshot_us=200 log_bytes=400 allocation_count=0 isr_log_writes=0 critical_section_us=5 clock=cycle_counter clock_hz=240000000 resolution_ns=4 saturated=0 t_ms=100 seq=7",
            "VAL_STATS_END metric=latency_us n=100 dropped=0 elapsed_ms=100 t_ms=100 seq=8",
            "VAL_SESSION_END run=R1 reason=complete records=9 dropped=0 duration_ms=100 t_ms=100 seq=9",
        ]
    )


def warmup_log() -> str:
    lines = good_log().splitlines()
    lines.insert(1, "VAL_PHASE name=warmup state=begin t_ms=0 seq=0")
    lines.insert(2, "VAL_PHASE name=warmup state=end t_ms=1 seq=0")
    lines = [re.sub(r"seq=\d+", f"seq={index}", line) for index, line in enumerate(lines, 1)]
    lines[-1] = re.sub(r"records=\d+", f"records={len(lines)}", lines[-1])
    return "\n".join(lines).replace("VAL_STATS metric=latency_us window_start_ms=0", "VAL_STATS metric=latency_us phase=steady window_start_ms=1").replace("elapsed_ms=100", "elapsed_ms=99")


class ProfileTests(unittest.TestCase):
    def test_skill_allows_implicit_invocation(self) -> None:
        metadata = yaml.safe_load((ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
        self.assertIs(metadata["policy"]["allow_implicit_invocation"], True)

    def test_valid_profile(self) -> None:
        self.assertEqual([], validate_profile(profile()))

    def test_optional_user_facing_metadata_is_backward_compatible_and_strict(self) -> None:
        value = profile()
        value["scenarios"][0]["title"] = "Boot readiness"
        value["scenarios"][0]["purpose"] = "Verify that the target reaches its ready state."
        value["scenarios"][0]["criteria"][0]["label"] = "Boot trigger"
        value["scenarios"][0]["criteria"][0]["description"] = "Observe the start event."
        self.assertEqual([], validate_profile(value))

        for path, invalid in (
            (("title",), ""),
            (("purpose",), 7),
            (("criteria", 0, "label"), "  "),
            (("criteria", 0, "description"), None),
        ):
            invalid_value = profile()
            target = invalid_value["scenarios"][0]
            if path[0] == "criteria":
                target["criteria"][path[1]][path[2]] = invalid
                expected = path[2]
            else:
                target[path[0]] = invalid
                expected = path[0]
            self.assertTrue(any(expected in item for item in validate_profile(invalid_value)), path)

    def test_user_facing_reporting_contract_is_documented(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = (ROOT / "references" / "user-facing-reporting.md").read_text(encoding="utf-8")
        self.assertIn("references/user-facing-reporting.md", skill)
        for heading in ("測試目的", "測試項目結果", "第一個差異", "問題分類", "證據"):
            self.assertIn(heading, reference)
        for verdict in ("PASS", "FAIL", "BLOCKED"):
            self.assertIn(f"`{verdict}`", reference)
        self.assertIn("Mermaid", reference)
        self.assertIn("（由測試契約推導）", reference)
        self.assertIn("Never ask the user to assign or change a verdict.", reference)
        self.assertIn("do not omit, merge, rename", reference)
        self.assertIn("must not use Mermaid", reference)
        self.assertIn("all required headings are present exactly once and in order", reference)

    def test_four_phase_scenario_contract_is_required(self) -> None:
        for field in ("phase", "evidence_mode", "max_duration_ms", "completion"):
            value = profile()
            del value["scenarios"][0][field]
            self.assertTrue(any(field in item for item in validate_profile(value)), field)

    def test_calculated_and_external_sample_plans(self) -> None:
        self.assertEqual(100, required_samples({"basis": "external-standard", "reference": "STD", "min_samples": 100}))
        self.assertEqual(97, required_samples({"basis": "calculated", "model": "proportion", "confidence": 0.95, "absolute_error": 0.1, "expected_proportion": 0.5}))
        self.assertEqual(385, required_samples({"basis": "calculated", "model": "mean", "confidence": 0.95, "absolute_error": 0.1, "estimated_stddev": 1.0}))
        self.assertEqual(738, required_samples({"basis": "calculated", "model": "distribution", "confidence": 0.95, "absolute_error": 0.05}))

    def test_guided_step_schema_is_strict(self) -> None:
        value = profile()
        value["scenarios"][0]["guided_steps"] = [{"id": "observe", "instruction": "Observe it.", "expected_observation": "It is visible.", "verdict": "PASS"}]
        self.assertTrue(any("guided_steps" in item for item in validate_profile(value)))

    def test_guided_step_ids_are_unique(self) -> None:
        value = profile()
        step = {"id": "observe", "instruction": "Observe it.", "expected_observation": "It is visible."}
        value["scenarios"][0]["guided_steps"] = [step, dict(step)]
        self.assertTrue(any("duplicate" in item for item in validate_profile(value)))

    def test_literal_secret_is_rejected(self) -> None:
        value = profile()
        value["token"] = "plaintext"
        self.assertTrue(any("tracked secrets" in item for item in validate_profile(value)))

    def test_timing_budget_is_required(self) -> None:
        value = profile()
        del value["scenarios"][0]["criteria"][2]["instrumentation_budget"]
        self.assertTrue(any("instrumentation_budget" in item for item in validate_profile(value)))

    def test_unknown_operator_and_method_are_rejected(self) -> None:
        value = profile()
        value["scenarios"][0]["criteria"][2]["operator"] = "approximately"
        value["scenarios"][0]["criteria"][2]["method"] = "magic"
        errors = validate_profile(value)
        self.assertTrue(any("operator" in item for item in errors))
        self.assertTrue(any("method" in item for item in errors))

    def test_trace_action_requires_cleanup(self) -> None:
        value = profile()
        value["actions"]["trace-start"] = {"executable": "wpr", "args": ["-start", "profile.wprp"], "risk": "trace"}
        value["scenarios"][0]["actions"] = ["trace-start"]
        self.assertTrue(any("cleanup_actions" in item for item in validate_profile(value)))

    def test_local_override_cannot_change_risk_or_criteria(self) -> None:
        value = profile()
        local = {"actions": {"flash": {"risk": "passive"}}, "scenarios": []}
        errors = validate_local_override(local, value)
        self.assertTrue(any("only executable" in item for item in errors))
        self.assertTrue(any("scenarios" in item for item in errors))

    def test_native_metric_rejects_removed_fallback_contract(self) -> None:
        value = profile()
        value["scenarios"][0]["criteria"].append(
            {"id": "native", "type": "native_metric", "metric": "scheduler.delay", "max_alignment_error_ns": 10, "fallback_metric": "latency_us"}
        )
        self.assertTrue(any("fallback_metric" in item for item in validate_profile(value)))

    def test_supported_os_native_resource_requires_native_provider(self) -> None:
        value = profile()
        value["scenarios"][0]["criteria"].append(
            {"id": "native", "type": "native_metric", "metric": "scheduler.delay", "operator": "<=", "threshold": 10, "max_alignment_error_ns": 10, "sample_plan": {"basis": "external-standard", "reference": "STD", "min_samples": 10}, "max_duration_ms": 1000, "native_unit": "us", "native_semantics": {"start_event": "ready", "end_event": "running", "clock": "qpc"}}
        )
        self.assertTrue(any("etw-wpr" in item for item in validate_profile(value)))


class GateSummaryTests(unittest.TestCase):
    @staticmethod
    def development_result(digest: str, *, verdict: str = "PASS", check_kind: str = "unit", smoke: dict | None = None) -> dict:
        return {
            "schema_version": "1.0",
            "gate": "Per-change Development Validation",
            "profile_sha256": digest,
            "source_revision": "worktree-001",
            "change_groups": [
                {
                    "id": "control-clock",
                    "architecture_refs": ["control_domain", "control.clock"],
                    "risks": ["timeout-calculation"],
                    "checks": [
                        {
                            "id": "control-unit",
                            "kind": check_kind,
                            "test_boundary": "FakeClockPort",
                            "command": {"executable": "test-runner", "args": ["control"]},
                            "exit_code": 0,
                            "verdict": "PASS",
                            "evidence": [{"path": "tests.json", "sha256": "b" * 64}],
                        }
                    ],
                    "on_device_smoke": smoke or {"required": False, "reason": "No runtime boundary changed."},
                }
            ],
            "verdict": verdict,
        }

    def test_all_four_gates_are_required_and_smoke_cannot_substitute(self) -> None:
        digest = "a" * 64
        documents = [
            {"scenario": "enable", "phase": "enablement", "verdict": "PASS", "profile_sha256": digest},
            self.development_result(digest),
            {"scenario": "accept", "phase": "acceptance", "verdict": "PASS", "profile_sha256": digest},
            {"gate": "Release Acceptance", "verdict": "PASS", "profile_sha256": digest, "evidence": ["release.json"]},
        ]
        verdict, result = overall_gates(documents, digest, {"enable"}, {"accept"})
        self.assertEqual(Verdict.PASS, verdict, result)
        verdict, _ = overall_gates(documents[:-1], digest, {"enable"}, {"accept"})
        self.assertEqual(Verdict.BLOCKED, verdict)
        smoke = {"scenario": "smoke", "phase": "smoke", "verdict": "PASS", "profile_sha256": digest}
        verdict, _ = overall_gates([*documents[:2], smoke, documents[-1]], digest, {"enable"}, {"accept"}, {"smoke"})
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_structured_development_gate_is_recomputed(self) -> None:
        digest = "a" * 64
        document = self.development_result(digest)
        verdict, result = overall_gates([document], digest, set(), set())
        development = next(item for item in result["gates"] if item["gate"] == "Per-change Development Validation")
        self.assertEqual("PASS", development["verdict"], result)
        self.assertEqual(Verdict.BLOCKED, verdict, "the other three gates remain required")

    def test_empty_change_groups_block_development_gate(self) -> None:
        digest = "a" * 64
        document = self.development_result(digest, verdict="BLOCKED")
        document["change_groups"] = []
        _, result = overall_gates([document], digest, set(), set())
        self.assertTrue(any("at least one change group" in item for item in result["invalid"]), result)

    def test_missing_risk_or_evidence_hash_blocks_development_gate(self) -> None:
        digest = "a" * 64
        document = self.development_result(digest, verdict="BLOCKED")
        document["change_groups"][0]["risks"] = []
        del document["change_groups"][0]["checks"][0]["evidence"][0]["sha256"]
        _, result = overall_gates([document], digest, set(), set())
        self.assertTrue(any("risks" in item for item in result["invalid"]), result)
        self.assertTrue(any("sha256" in item for item in result["invalid"]), result)

    def test_external_port_change_requires_contract_check(self) -> None:
        digest = "a" * 64
        document = self.development_result(digest, verdict="BLOCKED")
        _, result = overall_gates([document], digest, set(), set(), external_contract_refs={"control.clock"})
        self.assertTrue(any("port-contract" in item for item in result["invalid"]), result)
        document = self.development_result(digest, check_kind="port-contract")
        _, result = overall_gates([document], digest, set(), set(), external_contract_refs={"control.clock"})
        development = next(item for item in result["gates"] if item["gate"] == "Per-change Development Validation")
        self.assertEqual("PASS", development["verdict"], result)

    def test_required_smoke_must_have_matching_profile_bound_result(self) -> None:
        digest = "a" * 64
        smoke_policy = {"required": True, "reason": "Timer adapter changed.", "scenario": "timer-smoke"}
        document = self.development_result(digest, verdict="BLOCKED", smoke=smoke_policy)
        _, missing = overall_gates([document], digest, set(), set(), {"timer-smoke"})
        self.assertTrue(any("no matching result" in item for item in missing["invalid"]), missing)
        document["verdict"] = "PASS"
        smoke = {"scenario": "timer-smoke", "phase": "smoke", "verdict": "PASS", "profile_sha256": digest}
        _, supplied = overall_gates([document, smoke], digest, set(), set(), {"timer-smoke"})
        development = next(item for item in supplied["gates"] if item["gate"] == "Per-change Development Validation")
        self.assertEqual("PASS", development["verdict"], supplied)

    def test_declared_development_verdict_must_match_recomputed_result(self) -> None:
        digest = "a" * 64
        document = self.development_result(digest, verdict="FAIL")
        _, result = overall_gates([document], digest, set(), set())
        self.assertTrue(any("does not match recomputed verdict" in item for item in result["invalid"]), result)

    def test_external_contract_refs_come_from_governed_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "architecture" / "manifest.yaml"
            manifest.parent.mkdir()
            manifest.write_text(
                yaml.safe_dump(
                    {
                        "modules": [
                            {"id": "timer_adapter", "level": "L3+", "role": "adapter"},
                            {"id": "clock_domain", "level": "L1", "role": "domain"},
                        ],
                        "ports": [
                            {"id": "clock.port", "implemented_by": ["timer_adapter"]},
                            {"id": "clock.input", "implemented_by": []},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            value = {"_project_root": str(root), "architecture": {"manifest": "architecture/manifest.yaml"}}
            self.assertEqual({"timer_adapter", "clock.port"}, _external_contract_refs(value))

    def test_secret_reference_is_allowed(self) -> None:
        value = profile()
        value["external_refs"] = {"credential": {"ref": "windows-credential-manager:device"}}
        self.assertEqual([], validate_profile(value))

    def test_architecture_reference_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "architecture" / "manifest.yaml"
            manifest.parent.mkdir()
            manifest.write_text(yaml.safe_dump({"modules": [{"id": "known"}], "ports": [], "events": [], "flows": []}), encoding="utf-8")
            value = profile()
            value["architecture"] = {"manifest": "architecture/manifest.yaml"}
            self.assertTrue(any("unknown architecture reference" in item for item in validate_architecture_references(value, root)))

    def test_profile_v1_1_binds_accepted_execution_profile_and_extended_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "architecture" / "manifest.yaml"
            manifest.parent.mkdir()
            manifest.write_text(
                yaml.safe_dump(
                    {
                        "modules": [],
                        "ports": [],
                        "events": [],
                        "flows": [{"id": "FLOW-BOOT-001"}],
                        "workloads": [{"id": "boot-workload"}],
                        "execution_profiles": [
                            {
                                "id": "windows-release",
                                "status": "accepted",
                                "target": {"platform": "windows"},
                            }
                        ],
                        "execution_units": [{"id": "boot-thread"}],
                        "execution_channels": [{"id": "boot-channel"}],
                        "data_access_profiles": [{"id": "boot-data"}],
                        "microarchitecture_profiles": [{"id": "boot-micro"}],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            value = profile()
            value["version"] = "1.1"
            value["architecture"] = {
                "manifest": "architecture/manifest.yaml",
                "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
                "execution_profile": "windows-release",
            }
            value["scenarios"][0]["architecture_refs"] = [
                "FLOW-BOOT-001",
                "boot-workload",
                "boot-thread",
                "boot-channel",
                "boot-data",
                "boot-micro",
            ]
            self.assertEqual([], validate_profile(value))
            self.assertEqual([], validate_architecture_references(value, root))

    def test_profile_v1_1_rejects_stale_manifest_hash_and_proposed_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "architecture" / "manifest.yaml"
            manifest.parent.mkdir()
            manifest.write_text(
                yaml.safe_dump(
                    {
                        "modules": [],
                        "ports": [],
                        "events": [],
                        "flows": [{"id": "FLOW-BOOT-001"}],
                        "execution_profiles": [
                            {"id": "candidate", "status": "proposed", "target": {"platform": "windows"}}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            value = profile()
            value["version"] = "1.1"
            value["architecture"] = {
                "manifest": "architecture/manifest.yaml",
                "manifest_sha256": "0" * 64,
                "execution_profile": "candidate",
            }
            errors = validate_architecture_references(value, root)
            self.assertTrue(any("does not match" in item for item in errors), errors)
            self.assertTrue(any("accepted profile" in item for item in errors), errors)


class EvidenceTests(unittest.TestCase):
    def test_complete_event_and_statistical_evidence_passes(self) -> None:
        _, results, verdict = evaluate(profile(), "boot", good_log())
        self.assertEqual(Verdict.PASS, verdict, [(item.criterion_id, item.reason) for item in results])

    def test_sequence_gap_is_blocked(self) -> None:
        text = good_log().replace("seq=3", "seq=30", 1)
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_forbidden_pattern_fails(self) -> None:
        _, _, verdict = evaluate(profile(), "boot", good_log() + "\nWATCHDOG fired")
        self.assertEqual(Verdict.FAIL, verdict)

    def test_instrumentation_over_budget_blocks(self) -> None:
        text = good_log().replace("update_cycles_max=80", "update_cycles_max=101")
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_insufficient_samples_blocks(self) -> None:
        text = good_log().replace("n=100", "n=99")
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_statistical_window_duration_is_enforced(self) -> None:
        text = good_log().replace("elapsed_ms=100", "elapsed_ms=30001")
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_nonmonotonic_timestamp_blocks(self) -> None:
        text = good_log().replace("name=ready t_ms=2", "name=ready t_ms=0")
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_records_outside_session_are_blocked(self) -> None:
        text = good_log().replace("records=9", "records=10") + "\nVAL_EVENT name=late t_ms=101 seq=10"
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_duplicate_key_and_nonfinite_number_are_blocked(self) -> None:
        duplicate = good_log().replace("dropped=0 duration_ms", "dropped=5 dropped=0 duration_ms")
        nonfinite = good_log().replace("max=60", "max=-inf")
        self.assertEqual(Verdict.BLOCKED, evaluate(profile(), "boot", duplicate)[2])
        self.assertEqual(Verdict.BLOCKED, evaluate(profile(), "boot", nonfinite)[2])

    def test_missing_required_aggregate_field_blocks(self) -> None:
        text = good_log().replace("sum=3000 ", "")
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_missing_event_in_incomplete_window_is_blocked(self) -> None:
        text = good_log().replace("VAL_EVENT name=ready t_ms=2 seq=3\n", "")
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_complete_trigger_with_missing_required_flow_fails(self) -> None:
        text = good_log().replace("name=ready", "name=not_ready")
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.FAIL, verdict)

    def test_missing_trigger_is_blocked(self) -> None:
        text = good_log().replace("name=started", "name=not_started")
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_histogram_count_mismatch_blocks(self) -> None:
        text = good_log().replace("le=50 count=80", "le=50 count=79")
        _, _, verdict = evaluate(profile(), "boot", text)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_required_warmup_must_be_complete(self) -> None:
        value = profile()
        value["scenarios"][0]["warmup_required"] = True
        _, _, missing_verdict = evaluate(value, "boot", good_log())
        _, results, complete_verdict = evaluate(value, "boot", warmup_log())
        self.assertEqual(Verdict.BLOCKED, missing_verdict)
        self.assertEqual(Verdict.PASS, complete_verdict, [(item.criterion_id, item.reason) for item in results])

    def test_bundle_records_user_upload_limitation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "input.log"
            raw.write_text(good_log(), encoding="utf-8")
            result = write_bundle(root / "evidence", profile(), "boot", raw, probe(profile()), expected_run_id="R1")
            self.assertEqual("PASS", result["verdict"])
            self.assertFalse(result["upload_verified_by_gpt"])
            self.assertTrue((root / "evidence" / "raw.sha256").exists())
            self.assertTrue((root / "evidence" / "capability.json").exists())
            self.assertTrue((root / "evidence" / "permission-decisions.json").exists())

    def test_acceptance_requires_matching_enablement_pass_bundle(self) -> None:
        value = profile()
        acceptance = copy.deepcopy(value["scenarios"][0])
        acceptance.update({"id": "accept", "phase": "acceptance", "prerequisites": ["boot"]})
        value["scenarios"].append(acceptance)
        raw_text = good_log().replace("scenario=boot", "scenario=accept")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "input.log"
            raw.write_text(raw_text, encoding="utf-8")
            blocked = write_bundle(root / "blocked", value, "accept", raw, probe(value), expected_run_id="R1")
            self.assertEqual("BLOCKED", blocked["verdict"])
            bad_hash = [{"scenario": "boot", "phase": "enablement", "verdict": "PASS", "profile_sha256": "stale"}]
            blocked = write_bundle(root / "stale", value, "accept", raw, probe(value), expected_run_id="R1", prerequisite_results=bad_hash)
            self.assertEqual("BLOCKED", blocked["verdict"])
            prerequisite = [{"scenario": "boot", "phase": "enablement", "verdict": "PASS", "profile_sha256": profile_sha256(value)}]
            passed = write_bundle(root / "passed", value, "accept", raw, probe(value), expected_run_id="R1", prerequisite_results=prerequisite)
            self.assertEqual("PASS", passed["verdict"])

    def test_oversized_import_is_blocked_without_copying_raw(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "input.log"
            raw.write_text("x" * 101, encoding="utf-8")
            value = profile()
            value["transport"]["max_bytes"] = 100
            result = write_bundle(root / "evidence", value, "boot", raw, probe(value), expected_run_id="R1")
            self.assertEqual("BLOCKED", result["verdict"])
            self.assertFalse((root / "evidence" / "raw.log").exists())

    def test_redaction_removes_secret_literals(self) -> None:
        self.assertEqual("<redacted>", redact({"token": "abc"})["token"])

    def test_native_metric_is_correlated_and_evaluated(self) -> None:
        value = profile()
        value["target"]["provider"] = "etw-wpr"
        value["scenarios"][0]["criteria"].append(
            {"id": "ready-latency", "type": "native_metric", "metric": "scheduler.ready_latency_us", "field": "max", "operator": "<=", "threshold": 50, "max_alignment_error_ns": 1000, "sample_plan": {"basis": "external-standard", "reference": "TEST-SAMPLE-100", "min_samples": 100}, "max_duration_ms": 30000, "native_unit": "us", "native_semantics": {"start_event": "thread_ready", "end_event": "thread_running", "clock": "qpc"}}
        )
        native = {"provider": "etw-wpr", "run_id": "R1", "lost_events": 0, "source_trace_sha256": "a" * 64, "correlation": {"marker": "R1", "alignment_error_ns": 100}, "window": {"complete": True, "n": 100, "duration_ms": 1000}, "metrics": {"scheduler.ready_latency_us": {"max": 42, "n": 100, "unit": "us", "start_event": "thread_ready", "end_event": "thread_running", "clock": "qpc"}}}
        _, _, verdict = evaluate(value, "boot", good_log(), native, "a" * 64)
        self.assertEqual(Verdict.PASS, verdict)

    def test_native_loss_blocks(self) -> None:
        value = profile()
        value["target"]["provider"] = "etw-wpr"
        native = {"provider": "etw-wpr", "run_id": "R1", "lost_events": 1, "source_trace_sha256": "a" * 64, "correlation": {"marker": "R1", "alignment_error_ns": 100}, "window": {"complete": True, "n": 100, "duration_ms": 1000}, "metrics": {}}
        _, _, verdict = evaluate(value, "boot", good_log(), native)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_native_source_hash_must_be_computed_from_supplied_trace(self) -> None:
        value = profile()
        value["target"]["provider"] = "etw-wpr"
        value["scenarios"][0]["criteria"].append(
            {"id": "ready-latency", "type": "native_metric", "metric": "scheduler.ready_latency_us", "field": "max", "operator": "<=", "threshold": 50, "max_alignment_error_ns": 1000, "sample_plan": {"basis": "external-standard", "reference": "TEST-SAMPLE-100", "min_samples": 100}, "max_duration_ms": 30000, "native_unit": "us", "native_semantics": {"start_event": "thread_ready", "end_event": "thread_running", "clock": "qpc"}}
        )
        native = {"provider": "etw-wpr", "run_id": "R1", "lost_events": 0, "source_trace_sha256": "a" * 64, "correlation": {"marker": "R1", "alignment_error_ns": 100}, "window": {"complete": True, "n": 100, "duration_ms": 1000}, "metrics": {"scheduler.ready_latency_us": {"max": 42, "n": 100, "unit": "us", "start_event": "thread_ready", "end_event": "thread_running", "clock": "qpc"}}}
        _, _, verdict = evaluate(value, "boot", good_log(), native)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_native_alignment_budget_is_enforced(self) -> None:
        value = profile()
        value["target"]["provider"] = "etw-wpr"
        value["scenarios"][0]["criteria"].append(
            {"id": "ready-latency", "type": "native_metric", "metric": "scheduler.ready_latency_us", "field": "max", "operator": "<=", "threshold": 50, "max_alignment_error_ns": 1000, "sample_plan": {"basis": "external-standard", "reference": "TEST-SAMPLE-100", "min_samples": 100}, "max_duration_ms": 30000, "native_unit": "us", "native_semantics": {"start_event": "thread_ready", "end_event": "thread_running", "clock": "qpc"}}
        )
        native = {"provider": "etw-wpr", "run_id": "R1", "lost_events": 0, "source_trace_sha256": "a" * 64, "correlation": {"marker": "R1", "alignment_error_ns": 1001}, "window": {"complete": True, "n": 100, "duration_ms": 1000}, "metrics": {"scheduler.ready_latency_us": {"max": 42}}}
        _, _, verdict = evaluate(value, "boot", good_log(), native)
        self.assertEqual(Verdict.BLOCKED, verdict)

    def test_native_metric_cannot_use_structured_log_fallback(self) -> None:
        value = profile()
        value["target"]["provider"] = "etw-wpr"
        value["scenarios"][0]["criteria"].append(
            {"id": "ready-latency", "type": "native_metric", "metric": "scheduler.ready_latency_us", "field": "max", "operator": "<=", "threshold": 70, "max_alignment_error_ns": 1000, "sample_plan": {"basis": "external-standard", "reference": "TEST-SAMPLE-100", "min_samples": 100}, "max_duration_ms": 30000, "native_unit": "us", "native_semantics": {"start_event": "thread_ready", "end_event": "thread_running", "clock": "qpc"}}
        )
        semantic_log = good_log().replace("unit=us", "unit=us start_event=thread_ready end_event=thread_running clock=cycle_counter", 1)
        _, results, verdict = evaluate(value, "boot", semantic_log)
        self.assertEqual(Verdict.BLOCKED, verdict)


class ProviderAndPermissionTests(unittest.TestCase):
    def test_structured_log_provider_is_available(self) -> None:
        self.assertEqual("PASS", probe(profile())["status"])

    def test_native_provider_can_fallback(self) -> None:
        value = profile()
        value["target"]["provider"] = "instruments-xctest"
        result = probe(value)
        self.assertEqual("structured-log", result["actual_provider"])
        self.assertIsNotNone(result["fallback_reason"])

    def test_flash_requires_approval_before_tool_lookup(self) -> None:
        result = run_action(profile(), "flash", set())
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual("flash", result["risk"])

    def test_action_output_is_bounded(self) -> None:
        value = profile()
        value["_project_root"] = str(ROOT)
        value["actions"]["noisy"] = {"executable": sys.executable, "args": ["-c", "print('x' * 100)"], "risk": "passive", "timeout_seconds": 10, "max_output_bytes": 10}
        result = run_action(value, "noisy", set())
        self.assertEqual("BLOCKED", result["status"])
        self.assertEqual(">10", result["output_bytes"])

    def test_tcp_client_capture_is_bounded(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]

            def send() -> None:
                conn, _ = server.accept()
                with conn:
                    conn.sendall(good_log().encode("utf-8"))

            thread = threading.Thread(target=send)
            thread.start()
            value = profile()
            value["transport"] = {"type": "tcp-client", "host": "127.0.0.1", "port": port, "timeout_seconds": 2, "max_bytes": 100000}
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "capture.log"
                result = capture_tcp(value, value["scenarios"][0], output)
                self.assertEqual("PASS", result["status"])
                self.assertIn(b"VAL_SESSION_END", output.read_bytes())
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
