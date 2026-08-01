#!/usr/bin/env python3
"""Compose repository, intent, risk, and capability evidence into one handoff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from classify_risk import classify
from project_state import assess_project_state
from repository_evidence import GitFilesystemRepositoryEvidenceAdapter
from workflow_selection import classify_intent, select_workflow


SKILLS_ROOT = Path(__file__).resolve().parents[2]


def discover_available_skills(skills_root: Path = SKILLS_ROOT) -> set[str]:
    """Return the fresh-task inventory represented by this plugin package."""
    return {
        path.parent.name
        for path in skills_root.glob("*/SKILL.md")
        if path.is_file()
    }


def format_route_output(result: dict[str, Any], *, force_json: bool = False) -> str:
    """Render one PASS summary line or expanded exceptional evidence."""
    if force_json or result["status"] != "PASS":
        return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    project = result["project_state"]
    gates = ",".join(result["required_gates"]) or "none"
    return (
        f"PASS: selected={result['selected_skill']}; "
        f"implementation={project['implementation']}; "
        f"stateful_context={project['stateful_context']}; "
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
) -> dict[str, Any]:
    capabilities = (
        discover_available_skills()
        if available_skills is None
        else available_skills
    )
    artifacts = GitFilesystemRepositoryEvidenceAdapter().collect(project_root)
    project = assess_project_state(artifacts)
    intent = classify_intent(prompt, explicit_skill=explicit_skill)
    risk = classify(
        prompt,
        entry_skill=explicit_skill or "ask-matt",
        passed_gates=passed_gates,
        available_skills=capabilities,
    )
    return select_workflow(
        intent,
        project,
        risk,
        available_skills=capabilities,
        completed_stages=completed_stages,
        wayfinder_evidence=wayfinder_evidence,
        tracker_available=tracker_available,
        has_unresolved_decision=has_unresolved_decision,
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--explicit-skill")
    parser.add_argument("--available-skill", action="append")
    parser.add_argument("--passed-gate", action="append", default=[])
    parser.add_argument("--completed-stage", action="append", default=[])
    parser.add_argument("--decision-ticket-candidate", action="count", default=0)
    parser.add_argument("--blocking-dependency", action="count", default=0)
    parser.add_argument("--fog-area", action="count", default=0)
    parser.add_argument("--tracker-unavailable", action="store_true")
    parser.add_argument("--unresolved-decision", action="store_true")
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
    )
    print(format_route_output(result, force_json=args.json))
    return 0 if result["status"] in {"PASS", "DEGRADED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
