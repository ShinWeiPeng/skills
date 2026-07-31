from __future__ import annotations

import hashlib
import json
from typing import Any, Callable


SESSION_KEYS = {"schema_version", "run_id", "scenario", "phase", "evidence_mode", "max_duration_ms", "profile_sha256", "capture_mode", "steps"}
SESSION_STEP_KEYS = {"id", "order", "required", "instruction", "expected_observation", "evidence_required", "observation_code"}
RESPONSE_KEYS = {"schema_version", "run_id", "scenario", "profile_sha256", "capture_mode", "revision", "supersedes_sha256", "steps", "confirmation"}
RESPONSE_STEP_KEYS = {"step_id", "state", "actual_observation", "observer", "evidence", "blocked_reason", "remediation"}
EVIDENCE_KEYS = {"path"}
CONFIRMATION_KEYS = {"confirmed"}
REVIEW_KEYS = {"schema_version", "run_id", "scenario", "profile_sha256", "revision", "response_sha256", "supersedes_sha256", "review_status", "confirmation", "steps", "problems"}


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def profile_sha256(profile: dict[str, Any]) -> str:
    snapshot = {key: value for key, value in profile.items() if key != "_project_root"}
    return canonical_sha256(snapshot)


def _default_steps(profile: dict[str, Any], scenario: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    platform = profile["target"]["platform"]
    preparation = "Prepare the declared test build and start the target application." if platform in {"windows", "linux", "ios"} else f"Upload the declared test firmware for run {run_id}."
    steps: list[dict[str, Any]] = [
        {"id": "prepare-target", "instruction": preparation, "expected_observation": "The declared test build is present and the target is ready.", "required": True, "evidence_required": False, "observation_code": None},
        {"id": "start-capture", "instruction": "Start bounded raw evidence capture before reset or trigger.", "expected_observation": "Capture is active and bound to this run ID.", "required": True, "evidence_required": False, "observation_code": None},
        {"id": "begin-session", "instruction": f"Begin validation run {run_id} for scenario {scenario['id']}.", "expected_observation": "VAL_SESSION_BEGIN contains the same run and scenario.", "required": True, "evidence_required": False, "observation_code": None},
    ]
    for criterion in scenario.get("criteria", []):
        if criterion.get("type") == "observation":
            steps.append({"id": f"observe-{criterion['id']}", "instruction": f"Perform and observe step {criterion['step']} for {criterion['code']}.", "expected_observation": f"Record the physical outcome for observation code {criterion['code']}.", "required": True, "evidence_required": False, "observation_code": criterion["code"]})
    steps.append({"id": "preserve-evidence", "instruction": "End the session as complete and preserve the unedited evidence files.", "expected_observation": "VAL_SESSION_END is complete and the returned evidence files are unchanged.", "required": True, "evidence_required": True, "observation_code": None})
    return [{**step, "order": index} for index, step in enumerate(steps, 1)]


def build_session(profile: dict[str, Any], scenario: dict[str, Any], run_id: str, capture_mode: str = "gpt-guided") -> dict[str, Any]:
    configured = scenario.get("guided_steps")
    if configured:
        steps = [
            {
                "id": step["id"],
                "order": index,
                "required": step.get("required", True),
                "instruction": step["instruction"],
                "expected_observation": step["expected_observation"],
                "evidence_required": step.get("evidence_required", False),
                "observation_code": step.get("observation_code"),
            }
            for index, step in enumerate(configured, 1)
        ]
    else:
        steps = _default_steps(profile, scenario, run_id)
    return {"schema_version": "1.0", "run_id": run_id, "scenario": scenario["id"], "phase": scenario["phase"], "evidence_mode": scenario["evidence_mode"], "max_duration_ms": scenario["max_duration_ms"], "profile_sha256": profile_sha256(profile), "capture_mode": capture_mode, "steps": steps}


def build_response_template(session: dict[str, Any], capture_mode: str = "offline-user") -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": session["run_id"],
        "scenario": session["scenario"],
        "profile_sha256": session["profile_sha256"],
        "capture_mode": capture_mode,
        "revision": 1,
        "supersedes_sha256": None,
        "steps": [
            {"step_id": step["id"], "state": "pending", "actual_observation": "", "observer": "user", "evidence": [], "blocked_reason": "", "remediation": ""}
            for step in session["steps"]
        ],
        "confirmation": {"confirmed": False},
    }


def render_user_guide(session: dict[str, Any]) -> str:
    lines = [f"# Guided test: {session['scenario']}", "", f"Run ID: `{session['run_id']}`", f"Phase: `{session['phase']}`", f"Evidence mode: `{session['evidence_mode']}`", f"Maximum duration: `{session['max_duration_ms']} ms`", "", "Follow each form step in order. Record facts only; do not assign PASS or FAIL.", ""]
    for step in session["steps"]:
        required = "required" if step["required"] else "optional"
        lines.extend([f"## {step['order']}. {step['id']} ({required})", "", step["instruction"], "", f"Expected observable fact: {step['expected_observation']}", "", "- State: pending / completed / blocked", "- Actual observation:", "- Evidence file path(s):", "- If blocked, reason and remediation:", ""])
    lines.extend(["## Final confirmation", "", "After reviewing the generated summary table, set `confirmation.confirmed` to `true` in the response JSON. This confirms only the recorded facts; the runner owns PASS/FAIL/BLOCKED.", ""])
    return "\n".join(lines)


def validate_session(session: Any) -> list[str]:
    problems: list[str] = []
    if not isinstance(session, dict):
        return ["session must be an object"]
    if set(session) != SESSION_KEYS:
        problems.append("session fields do not match the guided-session schema")
    if session.get("schema_version") != "1.0" or not all(isinstance(session.get(key), str) and session.get(key) for key in ("run_id", "scenario", "phase", "evidence_mode", "profile_sha256", "capture_mode")) or type(session.get("max_duration_ms")) is not int or session.get("max_duration_ms", 0) <= 0:
        problems.append("session identity fields are invalid")
    steps = session.get("steps")
    if not isinstance(steps, list) or not steps:
        return problems + ["session steps must be a non-empty list"]
    ids: set[str] = set()
    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict) or set(step) != SESSION_STEP_KEYS:
            problems.append(f"session step {index} fields are invalid")
            continue
        step_id = step.get("id")
        if not isinstance(step_id, str) or not step_id or step_id in ids or step.get("order") != index:
            problems.append(f"session step {index} identity/order is invalid")
        if isinstance(step_id, str):
            ids.add(step_id)
        if type(step.get("required")) is not bool or type(step.get("evidence_required")) is not bool or not isinstance(step.get("instruction"), str) or not isinstance(step.get("expected_observation"), str):
            problems.append(f"session step {index} contract is invalid")
    return problems


def finalize_response(
    session: dict[str, Any],
    response: dict[str, Any],
    evidence_hasher: Callable[[str], dict[str, Any]],
    previous_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    problems = validate_session(session)
    if problems:
        return {"schema_version": "1.0", "run_id": session.get("run_id") if isinstance(session, dict) else None, "scenario": session.get("scenario") if isinstance(session, dict) else None, "profile_sha256": session.get("profile_sha256") if isinstance(session, dict) else None, "revision": response.get("revision") if isinstance(response, dict) else None, "response_sha256": canonical_sha256(response) if isinstance(response, dict) else None, "supersedes_sha256": response.get("supersedes_sha256") if isinstance(response, dict) else None, "review_status": "BLOCKED", "confirmation": {"confirmed": False}, "steps": [], "problems": problems}
    if not isinstance(response, dict):
        return {"review_status": "BLOCKED", "problems": problems + ["response must be an object"]}
    if set(response) != RESPONSE_KEYS:
        problems.append("response fields do not match the schema; verdict fields are forbidden")
    for key in ("run_id", "scenario", "profile_sha256"):
        if response.get(key) != session.get(key):
            problems.append(f"response {key} does not match session")
    if response.get("schema_version") != "1.0" or response.get("capture_mode") not in {"gpt-guided", "offline-user"}:
        problems.append("response schema_version or capture_mode is invalid")
    revision = response.get("revision")
    if type(revision) is not int or revision <= 0:
        problems.append("response revision must be a positive integer")
    if type(revision) is int and revision == 1:
        if response.get("supersedes_sha256") is not None or previous_response is not None:
            problems.append("revision 1 cannot supersede another response")
    elif type(revision) is int:
        if previous_response is None or previous_response.get("revision") != revision - 1 or response.get("supersedes_sha256") != canonical_sha256(previous_response):
            problems.append("revision chain is missing or invalid")
    confirmation = response.get("confirmation")
    confirmed = isinstance(confirmation, dict) and set(confirmation) == CONFIRMATION_KEYS and confirmation.get("confirmed") is True
    if not confirmed:
        problems.append("final confirmation is missing")
    response_steps = response.get("steps")
    expected_steps = session.get("steps", [])
    reviewed_steps: list[dict[str, Any]] = []
    if not isinstance(response_steps, list) or len(response_steps) != len(expected_steps):
        problems.append("response must contain every session step exactly once")
        response_steps = []
    seen: set[str] = set()
    for index, expected in enumerate(expected_steps):
        item = response_steps[index] if index < len(response_steps) else {}
        step_problems: list[str] = []
        if not isinstance(item, dict) or set(item) != RESPONSE_STEP_KEYS:
            step_problems.append("response step fields are invalid")
            item = {}
        step_id = item.get("step_id")
        if step_id != expected["id"] or (isinstance(step_id, str) and step_id in seen):
            step_problems.append("step is missing, duplicated, or out of order")
        if isinstance(step_id, str):
            seen.add(step_id)
        state = item.get("state")
        if state not in {"completed", "blocked"}:
            step_problems.append("state must be completed or blocked")
        if item.get("observer") != "user":
            step_problems.append("observer must be user")
        if state == "completed" and (not isinstance(item.get("actual_observation"), str) or not item.get("actual_observation").strip()):
            step_problems.append("completed step requires an actual observation")
        if state == "completed" and (item.get("blocked_reason") or item.get("remediation")):
            step_problems.append("completed step cannot retain blocked reason or remediation")
        if state == "blocked" and (not isinstance(item.get("blocked_reason"), str) or not item.get("blocked_reason").strip() or not isinstance(item.get("remediation"), str) or not item.get("remediation").strip()):
            step_problems.append("blocked step requires reason and remediation")
        evidence = item.get("evidence")
        hashed: list[dict[str, Any]] = []
        if not isinstance(evidence, list):
            step_problems.append("evidence must be a list")
        else:
            for ref in evidence:
                if not isinstance(ref, dict) or set(ref) != EVIDENCE_KEYS or not isinstance(ref.get("path"), str) or not ref["path"]:
                    step_problems.append("evidence reference must contain only a non-empty path")
                    continue
                try:
                    hashed.append(evidence_hasher(ref["path"]))
                except (OSError, ValueError) as exc:
                    step_problems.append(f"evidence cannot be verified: {exc}")
        if expected["evidence_required"] and not hashed:
            step_problems.append("required evidence is missing")
        problems.extend(f"step {expected['id']}: {problem}" for problem in step_problems)
        reviewed_steps.append({"step_id": expected["id"], "order": expected["order"], "required": expected["required"], "state": state, "actual_observation": item.get("actual_observation", ""), "observer": item.get("observer"), "evidence": hashed, "blocked_reason": item.get("blocked_reason", ""), "remediation": item.get("remediation", ""), "complete": not step_problems})
    if any(step["required"] and step["state"] == "blocked" for step in reviewed_steps):
        problems.append("one or more required guided steps are blocked")
    response_hash = canonical_sha256(response)
    return {"schema_version": "1.0", "run_id": session.get("run_id"), "scenario": session.get("scenario"), "profile_sha256": session.get("profile_sha256"), "revision": revision, "response_sha256": response_hash, "supersedes_sha256": response.get("supersedes_sha256"), "review_status": "READY" if not problems else "BLOCKED", "confirmation": {"confirmed": confirmed}, "steps": reviewed_steps, "problems": problems}


def render_review(review: dict[str, Any]) -> str:
    def cell(value: Any) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\r", " ").replace("\n", " ")

    lines = [f"# Guided test review: {review.get('scenario', '')}", "", f"Run ID: `{review.get('run_id', '')}`", "", f"Review status: **{review.get('review_status', 'BLOCKED')}**", "", "| # | Step | State | Actual observation | Evidence | Complete |", "|---:|---|---|---|---:|---|"]
    for step in review.get("steps", []):
        lines.append(f"| {step['order']} | {cell(step['step_id'])} | {cell(step['state'])} | {cell(step['actual_observation'])} | {len(step['evidence'])} | {'yes' if step['complete'] else 'no'} |")
    lines.extend(["", f"- [ {'x' if review.get('confirmation', {}).get('confirmed') else ' '} ] The user confirmed that the recorded facts are correct.", "", "This table is read-only evidence review. It is not a PASS/FAIL decision source.", ""])
    if review.get("problems"):
        lines.extend(["## Blocking problems", "", *[f"- {cell(problem)}" for problem in review["problems"]], ""])
    return "\n".join(lines)


def validate_review_bundle(
    session: dict[str, Any],
    responses: list[dict[str, Any]],
    supplied_review: dict[str, Any],
    evidence_hasher: Callable[[str], dict[str, Any]],
    current_profile_sha256: str,
    scenario_id: str,
) -> list[str]:
    problems = validate_session(session)
    if session.get("profile_sha256") != current_profile_sha256:
        problems.append("guided session profile does not match the current profile")
    if session.get("scenario") != scenario_id:
        problems.append("guided session scenario does not match evaluation scenario")
    if not responses:
        problems.append("at least one guided response revision is required")
        return problems
    previous = None
    computed_review: dict[str, Any] | None = None
    expected_step_ids = [step["id"] for step in session.get("steps", [])]
    for index, response in enumerate(responses, 1):
        if not isinstance(response, dict) or set(response) != RESPONSE_KEYS:
            problems.append(f"response revision {index} fields are invalid")
            previous = response if isinstance(response, dict) else None
            continue
        if response.get("schema_version") != "1.0":
            problems.append(f"response revision {index} schema version is invalid")
        if response.get("capture_mode") not in {"gpt-guided", "offline-user"}:
            problems.append(f"response revision {index} capture mode is invalid")
        if any(response.get(key) != session.get(key) for key in ("run_id", "scenario", "profile_sha256")):
            problems.append(f"response revision {index} identity does not match session")
        if response.get("revision") != index:
            problems.append(f"response revision {index} number is invalid")
        expected_predecessor = None if previous is None else canonical_sha256(previous)
        if response.get("supersedes_sha256") != expected_predecessor:
            problems.append(f"response revision {index} predecessor hash is invalid")
        raw_steps = response.get("steps")
        if not isinstance(raw_steps, list) or [step.get("step_id") if isinstance(step, dict) else None for step in raw_steps] != expected_step_ids or any(not isinstance(step, dict) or set(step) != RESPONSE_STEP_KEYS for step in raw_steps):
            problems.append(f"response revision {index} step schema/order is invalid")
        elif any(not isinstance(ref, dict) or set(ref) != EVIDENCE_KEYS for step in raw_steps for ref in (step.get("evidence") if isinstance(step.get("evidence"), list) else [{}])):
            problems.append(f"response revision {index} evidence schema is invalid")
        elif any(
            step.get("state") not in {"completed", "blocked"}
            or step.get("observer") != "user"
            or not isinstance(step.get("actual_observation"), str)
            or any(not isinstance(ref.get("path"), str) or not ref.get("path") for ref in step.get("evidence", []))
            for step in raw_steps
        ):
            problems.append(f"response revision {index} step values are invalid")
        confirmation = response.get("confirmation")
        if not isinstance(confirmation, dict) or set(confirmation) != CONFIRMATION_KEYS or type(confirmation.get("confirmed")) is not bool:
            problems.append(f"response revision {index} confirmation schema is invalid")
        previous = response
    if isinstance(responses[-1], dict):
        computed_review = finalize_response(session, responses[-1], evidence_hasher, responses[-2] if len(responses) > 1 else None)
        if computed_review.get("review_status") != "READY":
            problems.extend(computed_review.get("problems", []))
    if not isinstance(supplied_review, dict) or set(supplied_review) != REVIEW_KEYS:
        problems.append("supplied review fields are invalid")
    elif computed_review != supplied_review:
        problems.append("supplied review does not match the recomputed response review")
    if not isinstance(supplied_review, dict) or supplied_review.get("review_status") != "READY" or supplied_review.get("confirmation", {}).get("confirmed") is not True:
        problems.append("guided review is not confirmed and READY")
    return list(dict.fromkeys(problems))


class GuidedSessionInputPort:
    """Demand-owned contract for guided response commands."""


class GuidedSessionOutputPort:
    """Single guided-session output contract consumed by collection_domain."""
