#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

from vod.evidence import write_bundle
from vod.model import overall_gates
from vod.execution import run_action
from vod.guided import build_response_template, build_session, finalize_response, profile_sha256, render_review, render_user_guide, validate_review_bundle
from vod.profile import load_profile, load_yaml, validate_profile
from vod.providers import capture_serial, capture_tcp, hash_evidence_reference, probe, read_bounded_json, write_json, write_json_exclusive, write_text_exclusive


def _paths(args: argparse.Namespace) -> tuple[dict, list[str]]:
    return load_profile(args.profile.resolve(), args.local.resolve() if args.local else None)


def _emit(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def _external_contract_refs(profile: dict) -> set[str]:
    architecture = profile.get("architecture")
    if not isinstance(architecture, dict) or not architecture.get("manifest"):
        return set()
    project_root = Path(profile["_project_root"]).resolve()
    manifest_path = (project_root / str(architecture["manifest"])).resolve()
    manifest = load_yaml(manifest_path)
    adapter_ids = {
        item["id"]
        for item in manifest.get("modules", [])
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and item.get("level") == "L3+"
        and item.get("role") == "adapter"
    }
    external_refs = set(adapter_ids)
    for port in manifest.get("ports", []):
        if not isinstance(port, dict) or not isinstance(port.get("id"), str):
            continue
        implemented_by = port.get("implemented_by", [])
        if isinstance(implemented_by, list) and adapter_ids.intersection(implemented_by):
            external_refs.add(port["id"])
    return external_refs


def _run_cleanups(profile: dict, scenario: dict, approvals: set[str], enabled: bool) -> list[dict]:
    if not enabled:
        return []
    results = []
    for name in reversed(scenario.get("cleanup_actions", [])):
        try:
            result = run_action(profile, name, approvals)
        except Exception as exc:
            result = {"status": "BLOCKED", "reason": f"cleanup raised {type(exc).__name__}: {exc}"}
        results.append({"action": name, **result})
    return results


def _guided_output_paths(output: Path) -> tuple[Path, Path, Path]:
    if output.suffix.lower() == ".json":
        prefix = "" if output.name == "session.json" else output.stem + "."
        return output, output.with_name(prefix + "response.template.json"), output.with_name(prefix + "user-guide.md")
    return output / "session.json", output / "response.template.json", output / "user-guide.md"


def _guided_evaluation_context(args: argparse.Namespace, profile: dict, scenario_id: str) -> tuple[str | None, dict[str, object] | None, list[str]]:
    expected_run_id = args.expected_run_id
    if not args.guided_session:
        if args.guided_review or args.guided_response:
            return expected_run_id, None, ["guided review/responses require --guided-session"]
        return expected_run_id, None, []
    max_bytes = int(profile.get("transport", {}).get("max_bytes", 1048576))
    try:
        session = read_bounded_json(args.guided_session, max_bytes)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return expected_run_id, None, [f"guided session cannot be read: {exc}"]
    expected_run_id = session.get("run_id")
    artifacts: dict[str, object] = {"session": args.guided_session, "responses": [], "review": args.guided_review}
    if args.guided_review:
        try:
            responses = [read_bounded_json(path, max_bytes) for path in args.guided_response]
            review = read_bounded_json(args.guided_review, max_bytes)
            root = Path(profile["_project_root"])
            problems = validate_review_bundle(session, responses, review, lambda path: hash_evidence_reference(root, path, max_bytes), profile_sha256(profile), scenario_id)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return expected_run_id, None, [f"guided review cannot be verified: {exc}"]
        artifacts["responses"] = list(args.guided_response)
        review_markdown = args.guided_review.with_suffix(".md")
        artifacts["review_markdown"] = review_markdown if review_markdown.exists() else None
        artifact_paths = [args.guided_session, *args.guided_response, args.guided_review, *([review_markdown] if review_markdown.exists() else [])]
        artifacts["expected_sha256"] = {str(path.resolve()): hash_evidence_reference(root, str(path), max_bytes)["sha256"] for path in artifact_paths}
        return expected_run_id, artifacts, problems
    return expected_run_id, artifacts, ["guided session requires --guided-review and at least one --guided-response for user-confirmed evaluation"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate bounded on-device and native-platform evidence.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate-profile", "probe", "prepare-guided-session", "finalize-guided-session", "capture", "run-action", "evaluate", "run", "summarize-gates"):
        command = sub.add_parser(name)
        command.add_argument("--profile", required=True, type=Path)
        command.add_argument("--local", type=Path)
        if name == "prepare-guided-session":
            command.add_argument("--scenario", required=True)
            command.add_argument("--output", required=True, type=Path)
            command.add_argument("--capture-mode", choices=("gpt-guided", "offline-user"), default="gpt-guided")
        elif name == "finalize-guided-session":
            command.add_argument("--session", required=True, type=Path)
            command.add_argument("--response", required=True, type=Path)
            command.add_argument("--previous-response", type=Path)
            command.add_argument("--output", required=True, type=Path)
        elif name == "capture":
            command.add_argument("--scenario", required=True)
            command.add_argument("--output", required=True, type=Path)
            command.add_argument("--approve-risk", action="append", default=[])
        elif name == "run-action":
            command.add_argument("--action", required=True)
            command.add_argument("--approve-risk", action="append", default=[])
        elif name == "summarize-gates":
            command.add_argument("--result", required=True, type=Path, action="append")
            command.add_argument("--output", required=True, type=Path)
        elif name in {"evaluate", "run"}:
            command.add_argument("--scenario", required=True)
            command.add_argument("--raw-log", type=Path)
            command.add_argument("--output", required=True, type=Path)
            command.add_argument("--native-evidence", type=Path)
            command.add_argument("--native-source-trace", type=Path)
            command.add_argument("--guided-session", type=Path)
            command.add_argument("--guided-review", type=Path)
            command.add_argument("--guided-response", type=Path, action="append", default=[])
            command.add_argument("--expected-run-id")
            command.add_argument("--upload-actor", choices=("user", "gpt"), default="user")
            command.add_argument("--prerequisite-result", type=Path, action="append", default=[])
            if name == "run":
                command.add_argument("--approve-risk", action="append", default=[])
    args = parser.parse_args(argv)
    profile, errors = _paths(args)
    if errors:
        _emit({"status": "BLOCKED", "errors": errors})
        return 2
    if args.command == "validate-profile":
        _emit({"status": "PASS", "errors": validate_profile(profile, tracked=False)})
        return 0
    provider = probe(profile)
    if args.command == "probe":
        _emit(provider)
        return 0 if provider["status"] == "PASS" else 2
    if args.command == "summarize-gates":
        max_bytes = int(profile.get("transport", {}).get("max_bytes", 1048576))
        try:
            documents = [read_bounded_json(path, max_bytes) for path in args.result]
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            _emit({"status": "BLOCKED", "reason": f"gate result cannot be read: {exc}"})
            return 2
        expected_enablement = {item["id"] for item in profile["scenarios"] if item["phase"] == "enablement"}
        expected_smoke = {item["id"] for item in profile["scenarios"] if item["phase"] == "smoke"}
        expected_acceptance = {item["id"] for item in profile["scenarios"] if item["phase"] == "acceptance"}
        verdict, result = overall_gates(
            documents,
            profile_sha256(profile),
            expected_enablement,
            expected_acceptance,
            expected_smoke,
            _external_contract_refs(profile),
        )
        result["profile_sha256"] = profile_sha256(profile)
        write_json(args.output, result)
        _emit(result)
        return 0 if verdict.name == "PASS" else (1 if verdict.name == "FAIL" else 2)
    if args.command == "prepare-guided-session":
        scenario = next((item for item in profile["scenarios"] if item["id"] == args.scenario), None)
        if scenario is None:
            _emit({"status": "BLOCKED", "reason": "unknown scenario"})
            return 2
        session = build_session(profile, scenario, secrets.token_hex(8), args.capture_mode)
        response = build_response_template(session, "offline-user" if args.capture_mode == "offline-user" else "gpt-guided")
        session_path, response_path, guide_path = _guided_output_paths(args.output)
        try:
            write_json_exclusive(session_path, session)
            write_json_exclusive(response_path, response)
            write_text_exclusive(guide_path, render_user_guide(session))
        except FileExistsError as exc:
            _emit({"status": "BLOCKED", "reason": f"guided artifact already exists: {exc.filename}"})
            return 2
        result = {"status": "PASS", "run_id": session["run_id"], "session": str(session_path), "response_template": str(response_path), "user_guide": str(guide_path), "provider": provider}
        _emit(result)
        return 0
    if args.command == "finalize-guided-session":
        max_bytes = int(profile.get("transport", {}).get("max_bytes", 1048576))
        try:
            session = read_bounded_json(args.session, max_bytes)
            response = read_bounded_json(args.response, max_bytes)
            previous = read_bounded_json(args.previous_response, max_bytes) if args.previous_response else None
            root = Path(profile["_project_root"])
            review = finalize_response(session, response, lambda path: hash_evidence_reference(root, path, max_bytes), previous)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            _emit({"status": "BLOCKED", "reason": str(exc)})
            return 2
        if session.get("profile_sha256") != profile_sha256(profile):
            review.setdefault("problems", []).append("session profile snapshot does not match the current profile")
            review["review_status"] = "BLOCKED"
        try:
            write_json_exclusive(args.output / "review.json", review)
            write_text_exclusive(args.output / "review.md", render_review(review))
        except FileExistsError as exc:
            _emit({"status": "BLOCKED", "reason": f"review artifact already exists: {exc.filename}"})
            return 2
        _emit(review)
        return 0 if review["review_status"] == "READY" else 2
    if args.command == "capture":
        scenario = next((item for item in profile["scenarios"] if item["id"] == args.scenario), None)
        if scenario is None:
            _emit({"status": "BLOCKED", "reason": "unknown scenario"})
            return 2
        transport = profile.get("transport", {}).get("type")
        if transport == "serial":
            result = capture_serial(profile, scenario, args.output, set(args.approve_risk))
        elif transport in {"tcp-client", "tcp-server"}:
            result = capture_tcp(profile, scenario, args.output)
        else:
            result = {"status": "BLOCKED", "reason": f"transport {transport!r} requires guided native/import collection"}
        _emit(result)
        return 0 if result["status"] == "PASS" else 2
    if args.command == "run-action":
        result = run_action(profile, args.action, set(args.approve_risk))
        _emit(result)
        return 0 if result["status"] == "PASS" else (1 if result["status"] == "FAIL" else 2)
    if args.command == "run":
        scenario = next((item for item in profile["scenarios"] if item["id"] == args.scenario), None)
        if scenario is None:
            _emit({"status": "BLOCKED", "reason": "unknown scenario"})
            return 2
        action_results = []
        cleanup_results = []
        cleanup_needed = False
        approvals = set(args.approve_risk)
        for action_name in scenario.get("actions", []):
            try:
                action_result = run_action(profile, action_name, approvals)
            except Exception as exc:
                action_result = {"status": "BLOCKED", "reason": f"action raised {type(exc).__name__}: {exc}", "spawned": True}
            cleanup_needed = cleanup_needed or action_result.get("spawned", False)
            action_results.append({"action": action_name, **action_result})
            if action_result["status"] != "PASS":
                if (
                    action_result["status"] == "BLOCKED"
                    and action_result.get("risk") == "trace"
                    and profile.get("target", {}).get("fallback") == "structured-log"
                ):
                    cleanup_results = _run_cleanups(profile, scenario, approvals, cleanup_needed)
                    cleanup_needed = False
                    cleanup_failed = next((item for item in cleanup_results if item["status"] != "PASS"), None)
                    if cleanup_failed is not None:
                        args.output.mkdir(parents=True, exist_ok=True)
                        write_json(args.output / "actions.json", {"actions": action_results, "cleanups": cleanup_results})
                        _emit({"status": "BLOCKED", "reason": "trace cleanup failed before fallback", "cleanups": cleanup_results})
                        return 2
                    provider = dict(provider)
                    provider["actual_provider"] = "structured-log"
                    provider["fallback_reason"] = action_result.get("reason", "native trace action was blocked")
                    provider["status"] = "PASS"
                    break
                cleanup_results = _run_cleanups(profile, scenario, approvals, cleanup_needed)
                args.output.mkdir(parents=True, exist_ok=True)
                write_json(args.output / "actions.json", {"actions": action_results, "cleanups": cleanup_results})
                _emit({"status": action_result["status"], "actions": action_results, "cleanups": cleanup_results})
                return 1 if action_result["status"] == "FAIL" else 2
        raw_path = args.raw_log
        if raw_path is None:
            raw_path = args.output / "captured.log"
            transport = profile.get("transport", {}).get("type")
            try:
                if transport == "serial":
                    capture_result = capture_serial(profile, scenario, raw_path, set(args.approve_risk))
                elif transport in {"tcp-client", "tcp-server"}:
                    capture_result = capture_tcp(profile, scenario, raw_path)
                else:
                    capture_result = {"status": "BLOCKED", "reason": "this transport requires --raw-log from a guided/import collection"}
            except BaseException:
                cleanup_results.extend(_run_cleanups(profile, scenario, approvals, cleanup_needed))
                args.output.mkdir(parents=True, exist_ok=True)
                write_json(args.output / "actions.json", {"actions": action_results, "cleanups": cleanup_results, "capture": {"status": "BLOCKED", "reason": "capture raised or was cancelled"}})
                raise
            if capture_result["status"] != "PASS":
                cleanup_results.extend(_run_cleanups(profile, scenario, approvals, cleanup_needed))
                args.output.mkdir(parents=True, exist_ok=True)
                write_json(args.output / "actions.json", {"actions": action_results, "capture": capture_result, "cleanups": cleanup_results})
                _emit(capture_result)
                return 2
        cleanup_results.extend(_run_cleanups(profile, scenario, approvals, cleanup_needed))
        cleanup_failed = next((item for item in cleanup_results if item["status"] != "PASS"), None)
        if cleanup_failed is not None:
            args.output.mkdir(parents=True, exist_ok=True)
            write_json(args.output / "actions.json", {"actions": action_results, "cleanups": cleanup_results})
            _emit({"status": "BLOCKED", "reason": "required cleanup did not complete", "cleanups": cleanup_results})
            return 2
        expected_run_id, guided_artifacts, guided_problems = _guided_evaluation_context(args, profile, args.scenario)
        if guided_problems:
            _emit({"status": "BLOCKED", "reason": "guided review validation failed", "problems": guided_problems})
            return 2
        if args.upload_actor == "user" and not expected_run_id:
            _emit({"status": "BLOCKED", "reason": "user-uploaded evidence requires --guided-session or --expected-run-id to prevent replay"})
            return 2
        prerequisite_results = []
        for path in args.prerequisite_result:
            prerequisite_results.append(read_bounded_json(path, int(profile.get("transport", {}).get("max_bytes", 1048576))))
        result = write_bundle(args.output, profile, args.scenario, raw_path, provider, args.upload_actor, args.native_evidence, approvals, args.native_source_trace, expected_run_id, guided_artifacts, prerequisite_results)
        write_json(args.output / "actions.json", {"actions": action_results, "cleanups": cleanup_results})
        _emit(result)
        return 0 if result["verdict"] == "PASS" else (1 if result["verdict"] == "FAIL" else 2)
    if args.raw_log is None:
        _emit({"status": "BLOCKED", "reason": "--raw-log is required for evaluate"})
        return 2
    expected_run_id, guided_artifacts, guided_problems = _guided_evaluation_context(args, profile, args.scenario)
    if guided_problems:
        _emit({"status": "BLOCKED", "reason": "guided review validation failed", "problems": guided_problems})
        return 2
    if args.upload_actor == "user" and not expected_run_id:
        _emit({"status": "BLOCKED", "reason": "user-uploaded evidence requires --guided-session or --expected-run-id to prevent replay"})
        return 2
    prerequisite_results = []
    for path in args.prerequisite_result:
        prerequisite_results.append(read_bounded_json(path, int(profile.get("transport", {}).get("max_bytes", 1048576))))
    result = write_bundle(args.output, profile, args.scenario, args.raw_log, provider, args.upload_actor, args.native_evidence, native_source_path=args.native_source_trace, expected_run_id=expected_run_id, guided_artifacts=guided_artifacts, prerequisite_results=prerequisite_results)
    _emit(result)
    return 0 if result["verdict"] == "PASS" else (1 if result["verdict"] == "FAIL" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
