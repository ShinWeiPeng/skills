from __future__ import annotations

import json
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_on_device import main
from vod.guided import build_response_template, build_session, canonical_sha256, finalize_response, profile_sha256, render_review, render_user_guide, validate_review_bundle
from vod.providers import hash_evidence_reference


def guided_profile() -> dict:
    return {
        "version": "1.0",
        "target": {"platform": "bare-metal", "provider": "structured-log", "fallback": "structured-log"},
        "transport": {"type": "import", "timeout_seconds": 30, "max_bytes": 4096},
        "actions": {},
        "scenarios": [
            {
                "id": "smoke",
                "phase": "smoke",
                "evidence_mode": "flow",
                "max_duration_ms": 30000,
                "completion": {"trigger_criteria": ["ready"], "required_criteria": ["ready"], "session_end_reason": "complete"},
                "prerequisites": [],
                "architecture_refs": [],
                "guided_steps": [
                    {"id": "power", "instruction": "Power the target.", "expected_observation": "Target powers on.", "required": True},
                    {"id": "capture", "instruction": "Preserve the raw log.", "expected_observation": "Raw log exists.", "required": True, "evidence_required": True},
                ],
                "criteria": [{"id": "ready", "type": "event_sequence", "events": ["ready"]}],
            }
        ],
    }


class GuidedContractTests(unittest.TestCase):
    def _ready(self, root: Path) -> tuple[dict, dict, dict]:
        profile = guided_profile()
        profile["_project_root"] = str(root)
        session = build_session(profile, profile["scenarios"][0], "R1")
        response = build_response_template(session, "gpt-guided")
        evidence = root / "raw.log"
        evidence.write_text("evidence", encoding="utf-8")
        for step in response["steps"]:
            step["state"] = "completed"
            step["actual_observation"] = f"observed {step['step_id']}"
        response["steps"][1]["evidence"] = [{"path": "raw.log"}]
        response["confirmation"]["confirmed"] = True
        review = finalize_response(session, response, lambda path: hash_evidence_reference(root, path, 4096))
        return session, response, review

    def test_ready_response_renders_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            session, _, review = self._ready(Path(temp))
            self.assertEqual("READY", review["review_status"])
            self.assertEqual(render_review(review), render_review(review))
            self.assertIn("do not assign PASS or FAIL", render_user_guide(session))

    def test_response_cannot_supply_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session, response, _ = self._ready(root)
            response["verdict"] = "PASS"
            review = finalize_response(session, response, lambda path: hash_evidence_reference(root, path, 4096))
            self.assertEqual("BLOCKED", review["review_status"])
            self.assertTrue(any("verdict fields" in item for item in review["problems"]))

    def test_required_blocked_step_is_immediately_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session, response, _ = self._ready(root)
            response["steps"][0].update({"state": "blocked", "actual_observation": "", "blocked_reason": "no power", "remediation": "connect power"})
            review = finalize_response(session, response, lambda path: hash_evidence_reference(root, path, 4096))
            self.assertEqual("BLOCKED", review["review_status"])
            self.assertTrue(any("required guided steps" in item for item in review["problems"]))

    def test_missing_unconfirmed_and_mismatched_identity_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session, response, _ = self._ready(root)
            response["steps"].pop()
            response["confirmation"]["confirmed"] = False
            response["run_id"] = "stale-run"
            review = finalize_response(session, response, lambda path: hash_evidence_reference(root, path, 4096))
            self.assertEqual("BLOCKED", review["review_status"])
            self.assertTrue(any("run_id" in item for item in review["problems"]))
            self.assertTrue(any("confirmation" in item for item in review["problems"]))
            self.assertTrue(any("every session step" in item for item in review["problems"]))

    def test_revision_chain_and_tampered_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session, first, first_review = self._ready(root)
            second = json.loads(json.dumps(first))
            second["revision"] = 2
            second["supersedes_sha256"] = canonical_sha256(first)
            second["steps"][0]["actual_observation"] = "corrected observation"
            second_review = finalize_response(session, second, lambda path: hash_evidence_reference(root, path, 4096), first)
            self.assertEqual("READY", second_review["review_status"])
            problems = validate_review_bundle(session, [first, second], second_review, lambda path: hash_evidence_reference(root, path, 4096), session["profile_sha256"], "smoke")
            self.assertEqual([], problems)
            tampered = json.loads(json.dumps(second_review))
            tampered["review_status"] = "BLOCKED"
            self.assertTrue(validate_review_bundle(session, [first, second], tampered, lambda path: hash_evidence_reference(root, path, 4096), session["profile_sha256"], "smoke"))
            self.assertEqual("READY", first_review["review_status"])

    def test_blocked_revision_can_be_corrected_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session, first, _ = self._ready(root)
            first["steps"][0].update({"state": "blocked", "actual_observation": "", "blocked_reason": "no power", "remediation": "connect power"})
            first_review = finalize_response(session, first, lambda path: hash_evidence_reference(root, path, 4096))
            self.assertEqual("BLOCKED", first_review["review_status"])
            second = json.loads(json.dumps(first))
            second["revision"] = 2
            second["supersedes_sha256"] = canonical_sha256(first)
            second["steps"][0].update({"state": "completed", "actual_observation": "power restored", "blocked_reason": "", "remediation": ""})
            second_review = finalize_response(session, second, lambda path: hash_evidence_reference(root, path, 4096), first)
            self.assertEqual([], validate_review_bundle(session, [first, second], second_review, lambda path: hash_evidence_reference(root, path, 4096), session["profile_sha256"], "smoke"))

    def test_completed_revision_cannot_retain_stale_blocked_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session, response, _ = self._ready(root)
            response["steps"][0]["blocked_reason"] = "stale reason"
            review = finalize_response(session, response, lambda path: hash_evidence_reference(root, path, 4096))
            self.assertEqual("BLOCKED", review["review_status"])
            self.assertTrue(any("cannot retain" in item for item in review["problems"]))

    def test_gpt_and_offline_responses_have_same_fact_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session, gpt_response, gpt_review = self._ready(root)
            offline = json.loads(json.dumps(gpt_response))
            offline["capture_mode"] = "offline-user"
            offline_review = finalize_response(session, offline, lambda path: hash_evidence_reference(root, path, 4096))
            self.assertEqual("READY", offline_review["review_status"])
            self.assertEqual(gpt_review["steps"], offline_review["steps"])

    def test_evidence_path_and_size_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root.parent / "outside-guided-evidence.txt"
            outside.write_text("x", encoding="utf-8")
            try:
                with self.assertRaises(ValueError):
                    hash_evidence_reference(root, str(outside), 10)
                large = root / "large.bin"
                large.write_bytes(b"x" * 11)
                with self.assertRaises(ValueError):
                    hash_evidence_reference(root, "large.bin", 10)
            finally:
                outside.unlink(missing_ok=True)


class GuidedCliTests(unittest.TestCase):
    def test_blocked_step_stops_finalize_and_preserves_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            validation = project / "validation"
            validation.mkdir(parents=True)
            profile_path = validation / "on-device.yaml"
            profile_path.write_text(yaml.safe_dump(guided_profile(), sort_keys=False), encoding="utf-8")
            artifacts = project / "guided"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["prepare-guided-session", "--profile", str(profile_path), "--scenario", "smoke", "--output", str(artifacts)]))
            response_path = artifacts / "response.template.json"
            response = json.loads(response_path.read_text(encoding="utf-8"))
            response["steps"][0]["state"] = "blocked"
            response["steps"][0]["blocked_reason"] = "device cannot be powered"
            response["confirmation"]["confirmed"] = True
            response_path.write_text(json.dumps(response, indent=2), encoding="utf-8")
            review_dir = project / "blocked-review"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(2, main(["finalize-guided-session", "--profile", str(profile_path), "--session", str(artifacts / "session.json"), "--response", str(response_path), "--output", str(review_dir)]))
            review = json.loads((review_dir / "review.json").read_text(encoding="utf-8"))
            self.assertEqual("BLOCKED", review["review_status"])
            self.assertTrue((review_dir / "review.md").exists())

    def test_prepare_finalize_evaluate_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            validation = project / "validation"
            validation.mkdir(parents=True)
            profile_path = validation / "on-device.yaml"
            profile_path.write_text(yaml.safe_dump(guided_profile(), sort_keys=False), encoding="utf-8")
            artifacts = project / "guided"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["prepare-guided-session", "--profile", str(profile_path), "--scenario", "smoke", "--output", str(artifacts)]))
            session = json.loads((artifacts / "session.json").read_text(encoding="utf-8"))
            response_path = artifacts / "response.template.json"
            response = json.loads(response_path.read_text(encoding="utf-8"))
            raw = project / "raw.log"
            raw.write_text("\n".join([f"VAL_SESSION_BEGIN run={session['run_id']} scenario=smoke observer=user t_ms=0 seq=1", "VAL_EVENT name=ready t_ms=10 seq=2", f"VAL_SESSION_END run={session['run_id']} reason=complete records=3 dropped=0 duration_ms=10 t_ms=10 seq=3"]), encoding="utf-8")
            for step in response["steps"]:
                step["state"] = "completed"
                step["actual_observation"] = "completed as instructed"
            response["steps"][1]["evidence"] = [{"path": "raw.log"}]
            response["confirmation"]["confirmed"] = True
            response_path.write_text(json.dumps(response, indent=2), encoding="utf-8")
            review_dir = project / "review-r1"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["finalize-guided-session", "--profile", str(profile_path), "--session", str(artifacts / "session.json"), "--response", str(response_path), "--output", str(review_dir)]))
            (review_dir / "review.md").write_text("manually edited display only", encoding="utf-8")
            evidence_dir = project / "evidence"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["evaluate", "--profile", str(profile_path), "--scenario", "smoke", "--raw-log", str(raw), "--output", str(evidence_dir), "--guided-session", str(artifacts / "session.json"), "--guided-review", str(review_dir / "review.json"), "--guided-response", str(response_path)]))
            result = json.loads((evidence_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual("PASS", result["verdict"])
            self.assertTrue(result["guided_review_confirmed"])
            self.assertFalse(result["upload_verified_by_gpt"])
            self.assertTrue((evidence_dir / "guided" / "response.r1.json.sha256").exists())


if __name__ == "__main__":
    unittest.main()
