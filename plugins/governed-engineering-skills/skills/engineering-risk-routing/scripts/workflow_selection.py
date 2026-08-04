#!/usr/bin/env python3
"""Classify engineering intent and select the authoritative workflow handoff."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


RULES_PATH = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "intent-rules.json"
)


def load_intent_rules(path: Path = RULES_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _term_matches(term: str, normalized_prompt: str) -> bool:
    normalized_term = term.casefold()
    if normalized_term.isascii():
        return re.search(
            rf"(?<!\w){re.escape(normalized_term)}(?!\w)",
            normalized_prompt,
        ) is not None
    return normalized_term in normalized_prompt


def _mixed_modification_matches(
    normalized_prompt: str,
    modification_matches: list[str],
    config: dict[str, Any],
) -> bool:
    def token_pattern(token: str) -> str:
        escaped = re.escape(token.casefold())
        if token.isascii() and token.replace("-", "").isalnum():
            return rf"(?<!\w){escaped}(?!\w)"
        return escaped

    connector = "(?:" + "|".join(
        token_pattern(item) for item in config["mixed_action_connectors"]
    ) + ")"
    for term in modification_matches:
        normalized_term = term.casefold()
        term_pattern = token_pattern(normalized_term)
        if re.search(
            rf"{connector}\s*(?:please\s+)?{term_pattern}",
            normalized_prompt,
        ):
            return True
    return False


def classify_intent(
    prompt: str,
    *,
    explicit_skill: str | None = None,
    rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = rules or load_intent_rules()
    normalized = prompt.casefold()
    modification_matches = [
        term
        for term in config["modification_terms"]
        if _term_matches(term, normalized)
    ]
    inferred_intent = "indeterminate"
    inferred_matches: list[str] = []
    for intent in config["precedence"]:
        candidate = next(
            item for item in config["intents"] if item["intent"] == intent
        )
        matches = [
            term
            for term in candidate["terms"]
            if _term_matches(term, normalized)
        ]
        if matches:
            inferred_intent = intent
            inferred_matches = matches
            break

    if explicit_skill:
        if explicit_skill in config["read_only_explicit_skills"]:
            if inferred_intent in {"review", "code-understanding"}:
                requires_modification = _mixed_modification_matches(
                    normalized,
                    modification_matches,
                    config,
                )
            else:
                requires_modification = bool(modification_matches)
        else:
            requires_modification = (
                bool(modification_matches)
                or explicit_skill in config["modifying_explicit_skills"]
            )
        return {
            "intent": "explicit-skill",
            "explicit_skill": explicit_skill,
            "matched_terms": [explicit_skill],
            "requires_modification": requires_modification,
        }

    if inferred_intent != "indeterminate":
        requires_modification = bool(modification_matches)
        if inferred_intent in {"review", "code-understanding"}:
            requires_modification = _mixed_modification_matches(
                normalized,
                modification_matches,
                config,
            )
        return {
            "intent": inferred_intent,
            "explicit_skill": None,
            "matched_terms": inferred_matches,
            "requires_modification": requires_modification,
        }

    return {
        "intent": "indeterminate",
        "explicit_skill": None,
        "matched_terms": [],
        "requires_modification": bool(modification_matches),
    }


def select_workflow(
    intent_assessment: dict[str, Any],
    project_state: dict[str, Any],
    risk_decision: dict[str, Any],
    *,
    available_skills: set[str] | None = None,
    completed_stages: set[str] | None = None,
    wayfinder_evidence: dict[str, Any] | None = None,
    tracker_available: bool = True,
    has_unresolved_decision: bool = False,
    spec_context: dict[str, Any] | None = None,
    resume_confirmed_spec: bool = False,
) -> dict[str, Any]:
    """Select the authoritative workflow handoff after ordered assessments."""
    completed = completed_stages or set()
    intent = intent_assessment["intent"]
    modifies = bool(intent_assessment["requires_modification"])
    implementation = project_state["implementation"]
    context = project_state["stateful_context"]
    resolved_spec = spec_context or {
        "state": "none",
        "selected_path": None,
        "candidates": [],
        "reason": "no active canonical specification",
    }
    spec_state = resolved_spec["state"]
    grilling_complete = bool(
        completed & {"grilling", "grill-me", "grill-with-docs"}
    ) or (
        resume_confirmed_spec
        and spec_state == "confirmed"
        and "spec-verified" in completed
    )

    def decision(
        selected_skill: str | None,
        *,
        status: str = "PASS",
        reason: str,
        resume_target: str | None = None,
        fallback: str | None = None,
    ) -> dict[str, Any]:
        return {
            "selected_skill": selected_skill,
            "project_state": project_state,
            "intent_assessment": intent_assessment,
            "spec_context": resolved_spec,
            "required_gates": list(risk_decision.get("required_gates", [])),
            "status": status,
            "fallback": fallback,
            "reason": reason,
            "resume_target": resume_target,
        }

    def capability_checked(
        preferred: str,
        *,
        reason: str,
        resume_target: str | None = None,
    ) -> dict[str, Any]:
        if available_skills is None or preferred in available_skills:
            return decision(
                preferred,
                reason=reason,
                resume_target=resume_target,
            )
        if preferred == "grill-me" and "grilling" in available_skills:
            return decision(
                "grilling",
                status="DEGRADED",
                reason=(
                    "grill-me is unavailable; using its grilling primitive "
                    "without asking the user to invoke a skill."
                ),
                resume_target=resume_target,
                fallback="grill-me",
            )
        return decision(
            None,
            status="BLOCKED",
            reason=f"Required capability is unavailable: {preferred}.",
            resume_target=resume_target,
            fallback=preferred,
        )

    if has_unresolved_decision:
        return capability_checked(
            "grilling",
            reason="A new discretionary decision must be resolved before execution.",
            resume_target="resume-execution",
        )

    if intent == "indeterminate":
        return decision(
            "grilling",
            status="BLOCKED",
            reason="Intent could not be classified by the ordered hard rules.",
            resume_target="intent-decision",
        )

    if modifies and resume_confirmed_spec and spec_state != "confirmed":
        return capability_checked(
            "spec-governance",
            reason=(
                "Confirmed-spec resume evidence requires exactly one valid "
                "confirmed canonical specification."
            ),
            resume_target="spec-context-decision",
        ) | {"status": "BLOCKED"}

    if modifies and spec_state in {"ambiguous", "invalid"}:
        return capability_checked(
            "spec-governance",
            reason=resolved_spec["reason"],
            resume_target=(
                "spec-context-decision"
                if spec_state == "ambiguous"
                else "spec-repair"
            ),
        ) | {"status": "BLOCKED"}

    if "indeterminate" in {implementation, context}:
        return decision(
            "grilling",
            status="BLOCKED",
            reason="Repository evidence is insufficient for a reliable route.",
            resume_target="project-state-decision",
        )

    if intent == "diagnosis" and "diagnosis" not in completed:
        return capability_checked(
            "diagnosing-bugs",
            reason="Establish the root cause using read-only diagnosis first.",
            resume_target="grilling" if modifies else None,
        )

    explicit_skill = intent_assessment.get("explicit_skill")
    post_spec_target = explicit_skill
    if intent == "review":
        post_spec_target = "code-review"
    elif intent == "code-understanding":
        post_spec_target = "explain-code-flow"
    elif not post_spec_target:
        post_spec_target = (
            "to-spec"
            if implementation == "absent"
            else risk_decision.get("next_skill")
        )

    if (
        modifies
        and resume_confirmed_spec
        and spec_state == "confirmed"
        and "spec-verified" not in completed
    ):
        return capability_checked(
            "spec-governance",
            reason="The confirmed canonical spec must verify before execution resumes.",
            resume_target=post_spec_target,
        )

    if modifies and not grilling_complete:
        if implementation == "absent" and context == "absent":
            preferred = "grill-me"
            resume_target = "to-spec"
        elif implementation == "absent" and context == "present":
            preferred = "grill-with-docs"
            resume_target = "to-spec"
        else:
            preferred = "grilling"
            resume_target = explicit_skill or risk_decision.get("next_skill")
        return capability_checked(
            preferred,
            reason="The modifying change set must complete grilling first.",
            resume_target=resume_target,
        )

    if modifies and "spec-verified" not in completed:
        return capability_checked(
            "spec-governance",
            reason="The decision-complete working spec must be materialized and verified.",
            resume_target=post_spec_target,
        )

    if risk_decision.get("status", "PASS") == "BLOCKED":
        blockers = risk_decision.get("blockers", [])
        return decision(
            None,
            status="BLOCKED",
            reason="Risk gates are blocked: " + "; ".join(blockers),
            resume_target=risk_decision.get("return_to_flow"),
            fallback=risk_decision.get("next_skill"),
        )

    if intent == "explicit-skill" and not modifies:
        return capability_checked(
            intent_assessment["explicit_skill"],
            reason="The explicit read-only skill remains the authoritative entry.",
        )

    if intent == "review" and not modifies:
        return capability_checked(
            "code-review",
            reason="The request is a read-only code review.",
        )

    if intent == "code-understanding" and not modifies:
        return capability_checked(
            "explain-code-flow",
            reason="The request is read-only code understanding.",
        )

    if modifies:
        signals = wayfinder_evidence or {}

        def signal_count(key: str) -> int:
            value = signals.get(key, 0)
            return len(value) if isinstance(value, (list, tuple, set)) else int(value)

        needs_wayfinder = (
            signal_count("decision_ticket_candidates") >= 2
            and signal_count("blocking_dependencies") >= 1
            and signal_count("fog_areas") >= 1
        )
        if needs_wayfinder:
            if not tracker_available:
                return decision(
                    None,
                    status="BLOCKED",
                    reason="Wayfinder requires an available tracker capability.",
                    resume_target="to-spec",
                    fallback="wayfinder",
                )
            return capability_checked(
                "wayfinder",
                reason="All three wayfinder escalation signals are present.",
                resume_target="to-spec",
            )

        next_skill = intent_assessment.get("explicit_skill")
        if intent == "review":
            next_skill = "code-review"
        elif intent == "code-understanding":
            next_skill = "explain-code-flow"
        if not next_skill:
            next_skill = (
                "to-spec"
                if implementation == "absent"
                else risk_decision.get("next_skill")
            )
        if not next_skill:
            return decision(
                None,
                status="BLOCKED",
                reason="No post-grilling implementation handoff is available.",
            )
        resume_target = risk_decision.get("return_to_flow")
        if intent in {"review", "code-understanding"}:
            resume_target = risk_decision.get("next_skill")
        return capability_checked(
            next_skill,
            reason="The change set is decision-complete and may continue.",
            resume_target=resume_target,
        )

    return decision(
        None,
        status="BLOCKED",
        reason="No governed workflow rule matched the assessments.",
    )
