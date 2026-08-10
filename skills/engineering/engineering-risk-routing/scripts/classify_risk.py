#!/usr/bin/env python3
"""Classify one engineering task using the governed hard-trigger table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RULES_PATH = Path(__file__).resolve().parents[1] / "references" / "routing-rules.json"


def load_rules(path: Path = RULES_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify(
    prompt: str,
    *,
    entry_skill: str | None = None,
    passed_gates: set[str] | None = None,
    available_skills: set[str] | None = None,
    governance_status: str = "supported",
    rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = rules or load_rules()
    normalized = prompt.casefold()
    passed = passed_gates or set()

    engineering_terms = {
        term.casefold()
        for item in config["classes"]
        for term in item["terms"]
    }
    note_matches = [
        term for term in config["out_of_scope"]["terms"] if term.casefold() in normalized
    ]
    engineering_matches = sorted(term for term in engineering_terms if term in normalized)
    if note_matches and not engineering_matches:
        return {
            "task_class": config["out_of_scope"]["task_class"],
            "matched_hard_triggers": note_matches,
            "risk_class": None,
            "required_gates": [],
            "next_skill": None,
            "status": "PASS",
            "return_to_flow": None,
            "blockers": [],
        }

    selected = None
    matches: list[str] = []
    for risk in config["precedence"]:
        candidate = next(
            (item for item in config["classes"] if item["risk_class"] == risk),
            None,
        )
        if candidate is None:
            continue
        candidate_matches = [
            term for term in candidate["terms"] if term.casefold() in normalized
        ]
        if candidate_matches:
            selected = candidate
            matches = candidate_matches
            break
    if selected is None:
        selected = config["default"]

    required = list(selected["required_gates"])
    blockers: list[str] = []
    if available_skills is not None:
        blockers.extend(
            f"missing capability: {gate}"
            for gate in required
            if gate not in available_skills
        )
    if (
        entry_skill in config["mutation_entries"]
        and selected["risk_class"] in {"R2", "R3"}
        and config["governance_gate"] not in passed
    ):
        blockers.append(
            f"unpassed gate before {entry_skill}: {config['governance_gate']}"
        )
    if governance_status == "missing" and selected["risk_class"] in {"R2", "R3"}:
        blockers.append("as-is architecture inventory and baseline required")

    return {
        "task_class": selected["task_class"],
        "matched_hard_triggers": matches,
        "risk_class": selected["risk_class"],
        "required_gates": required,
        "next_skill": selected["next_skill"],
        "status": "BLOCKED" if blockers else "PASS",
        "return_to_flow": selected["return_to_flow"],
        "blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--entry-skill")
    parser.add_argument("--passed-gate", action="append", default=[])
    parser.add_argument("--available-skill", action="append")
    parser.add_argument(
        "--governance-status",
        choices=("supported", "missing"),
        default="supported",
    )
    args = parser.parse_args()
    decision = classify(
        args.prompt,
        entry_skill=args.entry_skill,
        passed_gates=set(args.passed_gate),
        available_skills=(
            set(args.available_skill) if args.available_skill is not None else None
        ),
        governance_status=args.governance_status,
    )
    print(json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if decision["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
