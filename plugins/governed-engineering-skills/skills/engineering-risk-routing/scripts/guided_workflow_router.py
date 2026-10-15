#!/usr/bin/env python3
"""Compose repository, intent, risk, and capability evidence into one handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILLS_ROOT = Path(__file__).resolve().parents[2]
DELIVERY_SCRIPTS_ROOT = SKILLS_ROOT / "implement" / "scripts"
if str(DELIVERY_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(DELIVERY_SCRIPTS_ROOT))

from classify_risk import classify
from project_state import assess_project_state
from project_validation_adapter import assess_project_validation
from repository_evidence import GitFilesystemRepositoryEvidenceAdapter
from spec_delivery import (
    assess_delivery_compatibility,
    assess_delivery_spec_context,
    assess_delivery_turn_context,
    manage_delivery_discussion,
    resolve_delivery_project,
)
from workflow_selection import classify_intent, select_workflow


def discover_available_skills(skills_root: Path = SKILLS_ROOT) -> set[str]:
    """Return the fresh-task inventory represented by this plugin package."""
    roots = [skills_root]
    if (
        skills_root.name == "engineering"
        and (skills_root.parent / "productivity").is_dir()
    ):
        roots.append(skills_root.parent / "productivity")
    return {
        path.parent.name
        for root in roots
        for path in root.glob("*/SKILL.md")
        if path.is_file()
    }


def detect_branch(project_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    branch = result.stdout.strip()
    return branch or None


def format_route_output(result: dict[str, Any], *, force_json: bool = False) -> str:
    """Render one PASS summary line or expanded exceptional evidence."""
    compatibility = result.get("compatibility", {})
    if (
        force_json
        or result["status"] != "PASS"
        or (compatibility and not compatibility.get("reused"))
        or compatibility.get("verdict") == "BLOCKED"
    ):
        return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    project = result["project_state"]
    spec = result["spec_context"]
    gates = ",".join(result["required_gates"]) or "none"
    return (
        f"PASS: selected={result['selected_skill']}; "
        f"implementation={project['implementation']}; "
        f"stateful_context={project['stateful_context']}; "
        f"spec_context={spec['state']}; "
        f"gates={gates}; resume={result['resume_target'] or 'none'}"
    )


def route(
    prompt: str,
    project_root: Path,
    *,
    explicit_skill: str | None = None,
    available_skills: set[str] | None = None,
    passed_gates: set[str] | None = None,
    completed_stages: set[str] | None = None,
    wayfinder_evidence: dict[str, Any] | None = None,
    tracker_available: bool = True,
    has_unresolved_decision: bool = False,
    tracker_spec_path: str | None = None,
    branch: str | None = None,
    resume_confirmed_spec: bool = False,
    working_reference: str | None = None,
    task_ref: str | None = None,
    turn_kind: str = "auto",
    turn_ref: str | None = None,
    source_ref: str | None = None,
) -> dict[str, Any]:
    if task_ref:
        project_root = resolve_delivery_project(project_root, task_ref)
    capabilities = (
        discover_available_skills() if available_skills is None else available_skills
    )
    artifacts = GitFilesystemRepositoryEvidenceAdapter().collect(project_root)
    project = assess_project_state(artifacts)
    turn_context = assess_delivery_turn_context(
        project_root,
        reference=working_reference,
        task_ref=task_ref,
    )
    discussion = {
        "verdict": "BLOCKED",
        "reason": "task/turn/source references required for discussion entry",
    }
    if task_ref and turn_ref and source_ref:
        try:
            discussion = manage_delivery_discussion(
                project_root,
                {
                    "operation": "enter",
                    "task_ref": task_ref,
                    "turn_id": turn_ref,
                    "prompt": prompt,
                    "source_ref": source_ref,
                    "engineering": True,
                    "working_reference": working_reference,
                },
            )
            checked = manage_delivery_discussion(
                project_root,
                {"operation": "status", "task_ref": task_ref, "turn_id": turn_ref},
            )
            discussion = checked
            turn_context = assess_delivery_turn_context(
                project_root, reference=working_reference, task_ref=task_ref
            )
        except (OSError, ValueError, KeyError, TypeError) as error:
            discussion = {"verdict": "BLOCKED", "reason": str(error)}
    elif task_ref:
        # Reload an actual host-created obligation; a selected-skill flag is insufficient.
        try:
            saved = manage_delivery_discussion(
                project_root, {"operation": "resume", "task_ref": task_ref}
            )["state"]
            if saved["active_turn"]:
                discussion = manage_delivery_discussion(
                    project_root,
                    {
                        "operation": "status",
                        "task_ref": task_ref,
                        "turn_id": saved["active_turn"],
                    },
                )
        except (OSError, ValueError, KeyError, TypeError) as error:
            discussion = {"verdict": "BLOCKED", "reason": str(error)}
    active_working = turn_context.get("working_spec")
    if (
        active_working
        and not tracker_spec_path
        and active_working["spec_id"] != "SPEC-0000"
        and (working_reference or active_working.get("confirmed_history") is True)
    ):
        tracker_spec_path = (
            f"specs/{active_working['spec_id']}-{active_working['change_set']}.md"
        )
    spec_context = assess_delivery_spec_context(
        project_root,
        prompt,
        tracker_path=tracker_spec_path,
        branch=branch if branch is not None else detect_branch(project_root),
    )
    intent = classify_intent(prompt, explicit_skill=explicit_skill)
    risk = classify(
        prompt,
        entry_skill=explicit_skill or "ask-matt",
        passed_gates=passed_gates,
        available_skills=capabilities,
    )
    validation = assess_project_validation(
        project_root, spec_context.get("selected_path")
    )
    if available_skills is None:
        capabilities = capabilities | {
            name
            for name, evidence in validation.get("capabilities", {}).items()
            if evidence.get("callable") is True
            and evidence.get("evidence") == "validated-cli-result"
        }
    risk["required_gates"] = list(
        dict.fromkeys(risk["required_gates"] + validation["required_gates"])
    )
    missing = set(validation["required_gates"]) - capabilities
    result = select_workflow(
        intent,
        project,
        risk,
        available_skills=capabilities,
        completed_stages=completed_stages,
        wayfinder_evidence=wayfinder_evidence,
        tracker_available=tracker_available,
        has_unresolved_decision=has_unresolved_decision,
        spec_context=spec_context,
        resume_confirmed_spec=resume_confirmed_spec,
        turn_context=turn_context,
        turn_kind=turn_kind,
    )
    if task_ref and active_working and spec_context.get("selected_path"):
        result["compatibility"] = assess_delivery_compatibility(
            project_root,
            spec_context["selected_path"],
            active_working["working_id"],
            task_ref,
            persist=True,
            validation_assessor=assess_project_validation,
        )
        # Inventory never suppresses the original validation/authorization gates.
        # Unknown state still permits diagnosis and discussion.
        if result["compatibility"]["verdict"] != "PASS":
            result["product_code_allowed"] = False
            result["compatibility_recovery"] = {
                "required": True,
                "next_action": "diagnose-compatibility",
                "discussion_allowed": True,
            }
            # Routing into diagnosis is valid even when execution is blocked.
            # The renderer exposes this BLOCKED inventory instead of hiding it.
    result["discussion_owner"] = "grilling"
    result["discussion_entry"] = discussion
    result["supporting_skill"] = result.get("selected_skill")
    if discussion["verdict"] != "PASS":
        # Routing to investigation/discussion is not permission to mutate products.
        # Preserve the supporting route and its own validation failures.
        result["discussion_recovery"] = {
            "required": True,
            "reason": discussion.get(
                "reason", "Save or repair the current discussion."
            ),
            "resume_target": "spec-governance",
            "discussion_allowed": True,
        }
        result["product_code_allowed"] = False
    result["project_validation"] = validation
    result["capability_resolution"] = {
        "explicit_limit": available_skills is not None,
        "available": sorted(capabilities),
        "checks": validation.get("capabilities", {}),
    }
    if (validation["verdict"] != "PASS" or missing) and spec_context.get(
        "state"
    ) != "working":
        result.update(
            status="BLOCKED",
            reason="; ".join(
                validation.get("errors", [])
                + [f"missing capability: {v}" for v in sorted(missing)]
            ),
            product_code_allowed=False,
        )
        if result.get("selected_skill") != "spec-governance":
            result.update(
                selected_skill="verification-ladder", next_action="verification-ladder"
            )
    return result


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--turn-ref")
    parser.add_argument("--source-ref")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--explicit-skill")
    parser.add_argument("--available-skill", action="append")
    parser.add_argument("--passed-gate", action="append", default=[])
    parser.add_argument("--completed-stage", action="append", default=[])
    parser.add_argument("--decision-ticket-candidate", action="count", default=0)
    parser.add_argument("--blocking-dependency", action="count", default=0)
    parser.add_argument("--fog-area", action="count", default=0)
    parser.add_argument("--tracker-unavailable", action="store_true")
    parser.add_argument("--tracker-spec-path")
    parser.add_argument("--unresolved-decision", action="store_true")
    parser.add_argument(
        "--resume-confirmed-spec",
        action="store_true",
        help=(
            "Resume the selected confirmed spec without another interview; "
            "requires explicit no-new-decision evidence."
        ),
    )
    parser.add_argument("--branch")
    parser.add_argument("--working-reference")
    parser.add_argument("--task-ref")
    parser.add_argument(
        "--turn-kind",
        choices=["auto", "read-only", "decision-answer", "change-request"],
        default="auto",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Always emit the complete GuidedRouteDecision JSON.",
    )
    args = parser.parse_args()
    result = route(
        args.prompt,
        args.project_root,
        explicit_skill=args.explicit_skill,
        available_skills=(
            set(args.available_skill) if args.available_skill is not None else None
        ),
        passed_gates=set(args.passed_gate),
        completed_stages=set(args.completed_stage),
        wayfinder_evidence={
            "decision_ticket_candidates": args.decision_ticket_candidate,
            "blocking_dependencies": args.blocking_dependency,
            "fog_areas": args.fog_area,
        },
        tracker_available=not args.tracker_unavailable,
        has_unresolved_decision=args.unresolved_decision,
        tracker_spec_path=args.tracker_spec_path,
        branch=args.branch,
        resume_confirmed_spec=args.resume_confirmed_spec,
        working_reference=args.working_reference,
        task_ref=args.task_ref,
        turn_kind=args.turn_kind,
        turn_ref=args.turn_ref,
        source_ref=args.source_ref,
    )
    print(format_route_output(result, force_json=args.json))
    return 0 if result["status"] in {"PASS", "DEGRADED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
