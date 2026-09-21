#!/usr/bin/env python3
"""Persist, validate, materialize, resolve, and verify change-set specs."""

from __future__ import annotations

import argparse
import difflib
import errno
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from datetime import date, datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any


def check_spec_dependencies(root: Path, path: Path, visiting=None) -> list[str]:
    """Require every transitive prerequisite to be uniquely implemented."""
    visiting = set() if visiting is None else set(visiting)
    identity = path.name[:9]
    if identity in visiting:
        return [identity + ": dependency cycle"]
    visiting.add(identity)
    errors = []
    for row in _table(
        _sections(path.read_text(encoding="utf-8")).get("relationships", "")
    ):
        if _field(row, "Relation") != "depends_on":
            continue
        target = _field(row, "Target")
        if re.fullmatch(r"(?:REQ|DEC|AC)-\d{3}", target):
            continue
        if not re.fullmatch(r"SPEC-\d{4}", target):
            errors.append("invalid prerequisite: " + target)
            continue
        matches = list((root / "specs").glob(target + "-*.md"))
        if len(matches) != 1:
            errors.append(target + ": missing or ambiguous prerequisite")
            continue
        checked = validate_spec_text(
            matches[0].read_text(encoding="utf-8"),
            known_spec_ids=_repository_spec_ids(root),
        )
        if (
            checked["verdict"] != "PASS"
            or checked["canonical_spec"]["status"] != "implemented"
        ):
            errors.append(target + ": prerequisite is not implemented")
        errors.extend(check_spec_dependencies(root, matches[0], visiting))
    return errors


def assess_project_validation(
    project_root,
    spec=None,
    *,
    phase="planning",
    candidate_text=None,
    validation_assessor=None,
):
    """Demand-side validation seam; composition supplies the external adapter."""
    if validation_assessor is not None:
        return validation_assessor(
            project_root, spec, phase=phase, candidate_text=candidate_text
        )
    root = Path(project_root)
    try:
        markers = [
            root / "architecture/adoption.yaml",
            root / "architecture/manifest.yaml",
            root / "validation/verification-ladder.yaml",
            root / "validation/on-device.yaml",
        ]
        governed = any(p.exists() or p.is_symlink() for p in markers) or any(
            (root / "validation").glob("acceptance-*.json")
        )
    except OSError:
        governed = True
    if governed:
        return {
            "verdict": "BLOCKED",
            "required_gates": ["verification-ladder"],
            "errors": [
                "Project validation assessor is required. Use project_validation_workflow.py spec|managed|admission -- <existing CLI arguments>."
            ],
            "device_actions_authorized": False,
        }
    return {
        "verdict": "PASS",
        "required_gates": [],
        "errors": [],
        "reason": "Legacy host project declares no validation governance.",
    }


def assess_spec_evidence_update(
    project_root: Path, text: str, validation_assessor=None
) -> dict:
    """Treat prose PASS as a request for assessment, never as proof of acceptance."""
    metadata, _ = _metadata(text)
    acceptance = _table(_sections(text).get("acceptance criteria", ""))
    requested = metadata.get("status") == "implemented" or any(
        re.search(r"\bPASS\b", _field(row, "Evidence"), re.IGNORECASE)
        for row in acceptance
    )
    if not requested:
        return {"verdict": "PASS", "reason": "no acceptance claim recorded"}
    relative = f"specs/{metadata.get('spec_id')}-{metadata.get('change_set')}.md"
    return assess_project_validation(
        project_root,
        relative,
        phase="acceptance",
        candidate_text=text,
        validation_assessor=validation_assessor,
    )


SPEC_ID_RE = re.compile(r"^SPEC-(\d{4})$")
ITEM_ID_RE = re.compile(r"^(REQ|DEC|AC)-(\d{3})$")
DISCUSSION_ID_RE = re.compile(r"^DISC-(\d{3})$")
CANONICAL_PATH_RE = re.compile(
    r"(?P<path>specs[/\\]SPEC-\d{4}-[A-Za-z0-9][A-Za-z0-9_-]*\.md)",
    re.IGNORECASE,
)
REQUIRED_SECTIONS = {
    "problem",
    "solution",
    "user stories",
    "requirements",
    "decisions",
    "acceptance criteria",
    "relationships",
    "out of scope",
    "open decisions",
    "routing/gates",
    "revision history",
}
WORKING_REQUIRED_SECTIONS = REQUIRED_SECTIONS | {"discussion context"}
RELATIONS = {"depends_on", "refines", "conflicts_with", "supersedes"}
WORKING_ID_RE = re.compile(r"^WORKING-SPEC-[0-9a-f]{12}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?$")
LEGACY_WORKING_ID_RE = re.compile(r"^WSP-[0-9a-f]{12}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?$")
WORKING_ROOT = Path("spec-governance")
LEGACY_WORKING_ROOT = Path(".codex") / "spec-governance"
WORKING_SNAPSHOT_SUFFIX = ".md"
WORKING_JOURNAL_SUFFIX = ".journal.jsonl"
LEGACY_WORKING_SNAPSHOT = "working.md"
LEGACY_WORKING_JOURNAL = "journal.jsonl"
COMMIT_DISPOSITIONS = {"delete", "keep-local", "archive"}
REDACTION_MARKERS = {
    "credential": "[REDACTED: credential]",
    "personal": "[REDACTED: personal data]",
}


def _metadata(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not text.startswith("---"):
        return {}, ["missing YAML-style metadata fence"]
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not match:
        return {}, ["unterminated YAML-style metadata fence"]
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"invalid metadata line: {line}")
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip("\"'")
    return result, errors


def _sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1).strip().casefold()] = text[match.end() : end].strip()
    return sections


def pending_decision(text: str) -> dict[str, Any] | None:
    """Read the durable question; malformed state must never look like no question."""
    section = _sections(text).get("pending decision")
    if section is None:
        return None
    match = re.fullmatch(r"```json\s*\n(.*?)\n```", section, re.DOTALL)
    if not match:
        raise ValueError("invalid pending decision encoding")
    question = json.loads(match.group(1))
    if (
        not isinstance(question, dict)
        or set(question)
        not in (
            {"id", "version", "question", "options"},
            {"id", "version", "question", "options", "kind"},
        )
        or not isinstance(question["id"], str)
        or not re.fullmatch(r"Q-[A-Za-z0-9-]+", question["id"])
        or type(question["version"]) is not int
        or question["version"] < 1
        or not isinstance(question["question"], str)
        or not question["question"].strip()
        or not isinstance(question["options"], list)
        or (question.get("kind", "choice") not in ("choice", "open-text"))
        or (
            len(question["options"]) != 0
            if question.get("kind") == "open-text"
            else len(question["options"]) < 2
        )
        or any(
            not isinstance(item, str) or not item.strip()
            for item in question["options"]
        )
        or len(set(question["options"])) != len(question["options"])
    ):
        raise ValueError("invalid pending decision contract")
    return question


def question_surface_policy(
    host: dict[str, Any], surface: str, failed_surfaces: dict[str, str] | None = None
) -> dict[str, Any]:
    """Deny menu selection in Default before any question-tool invocation."""
    denied = {
        "verdict": "BLOCKED",
        "menu_allowed": False,
        "surface_allowed": False,
        "product_code_allowed": False,
        "evidence_trust": "caller-attested",
    }
    if not isinstance(host, dict) or not isinstance(surface, str):
        return denied
    if not all(
        isinstance(host.get(k), str) and host[k].strip()
        for k in ("mode_ref", "policy_ref")
    ):
        return denied
    mode = host.get("mode")
    if mode not in ("default", "plan"):
        return denied
    menu = surface in (
        "structured-menu",
        "request_user_input",
        "request_user_input_async",
    )
    failed = failed_surfaces if failed_surfaces is not None else {}
    if not isinstance(failed, dict):
        return denied
    menu_allowed = (
        mode == "plan"
        and host.get("menu_tool_allowed") is True
        and "structured-menu" not in failed
    )
    if ("structured-menu" if menu else surface) in failed:
        return denied
    allowed = (
        (menu and menu_allowed)
        or (surface == "numbered-text" and host.get("numbered_text_allowed") is True)
        or surface == "open-text"
    )
    return denied | {
        "verdict": "PASS" if allowed else "BLOCKED",
        "surface_allowed": allowed,
        "menu_allowed": menu_allowed,
    }


def _question_record(text: str) -> dict[str, Any]:
    raw = _sections(text).get("question record")
    if raw is None:
        return {"question_id": None, "history": [], "failed_surfaces": {}}
    match = re.fullmatch(r"```json\s*\n(.*?)\n```", raw, re.DOTALL)
    record = json.loads(match.group(1)) if match else None
    if (
        not isinstance(record, dict)
        or not isinstance(record.get("history"), list)
        or not isinstance(record.get("failed_surfaces"), dict)
        or not isinstance(record.get("question_id"), str)
        or not re.fullmatch(r"Q-[A-Za-z0-9-]+", record["question_id"])
        or any(
            k not in ("structured-menu", "numbered-text", "open-text")
            or not isinstance(v, str)
            or not v.strip()
            for k, v in record["failed_surfaces"].items()
        )
        or any(
            not isinstance(entry, dict)
            or not isinstance(entry.get("question"), dict)
            or entry.get("action")
            not in ("revise", "presentation-failed", "retry-requested")
            for entry in record["history"]
        )
    ):
        raise ValueError("invalid question presentation record")
    return record


def _question_update_snapshot(text: str, request: dict[str, Any], revision: int) -> str:
    pending = pending_decision(text)
    if (
        not pending
        or not isinstance(request, dict)
        or request.get("question_version") != pending["version"]
    ):
        raise ValueError("missing or stale question update")
    if not all(
        isinstance(request.get(k), str) and request[k].strip()
        for k in ("source_ref", "user_text")
    ):
        raise ValueError("question update requires original user feedback evidence")
    record = _question_record(text)
    if record.get("question_id") != pending["id"]:
        record["failed_surfaces"] = {}
    record["question_id"] = pending["id"]
    action = request.get("action")
    entry = {
        "action": action,
        "question": pending,
        "source_ref": request["source_ref"],
        "user_text": request["user_text"],
    }
    if action == "revise":
        if (
            request.get("kind", "choice") == "choice"
            and len(request.get("options") or []) < 3
        ):
            raise ValueError(
                "revised decision questions require at least three meaningful options"
            )
        revised = {
            "id": pending["id"],
            "version": revision + 1,
            "question": request.get("question"),
            "options": request.get("options"),
            "kind": request.get("kind", "choice"),
        }
        text = _replace_pending_decision(text, revised)
        pending_decision(text)
    elif action in ("presentation-failed", "retry-requested"):
        surface = request.get("surface")
        if surface not in (
            "structured-menu",
            "request_user_input_async",
            "request_user_input",
            "numbered-text",
            "open-text",
        ):
            raise ValueError("unknown failed surface")
        surface = (
            "structured-menu" if surface.startswith("request_user_input") else surface
        )
        entry["surface"] = surface
        if action == "presentation-failed":
            record["failed_surfaces"][surface] = request["source_ref"]
        else:
            record["failed_surfaces"].pop(surface, None)
    else:
        raise ValueError("unknown question update action")
    record["history"].append(entry)
    text = re.sub(r"(?ims)^## Question Record\s*\n.*?(?=^## |\Z)", "", text)
    section = (
        "## Question Record\n\n```json\n"
        + json.dumps(record, ensure_ascii=False, indent=2)
        + "\n```\n\n"
    )
    return re.sub(
        r"(?m)^## Revision History",
        lambda _: section + "## Revision History",
        text,
        count=1,
    )


def update_question(
    project_root: Path,
    working_id: str,
    request: dict[str, Any],
    *,
    expected_revision: int,
    expected_hash: str,
    validation_assessor=None,
) -> dict[str, Any]:
    """Record presentation feedback or explicitly version alternatives; never answer them."""
    resolved = resolve_working_bundle(project_root, reference=working_id)
    if resolved["state"] != "working":
        return {"verdict": "BLOCKED", "reason": resolved["reason"]}
    ref = resolved["working_spec"]
    if ref["status"] != "working":
        return {"verdict": "BLOCKED", "reason": "reopen before revising a question"}
    current = (project_root / ref["snapshot_path"]).read_text(encoding="utf-8")
    try:
        rendered = _question_update_snapshot(current, request, expected_revision)
    except (ValueError, TypeError, KeyError) as error:
        return {"verdict": "BLOCKED", "reason": str(error)}
    return reconcile_working_bundle(
        project_root,
        working_id,
        rendered,
        {},
        expected_revision=expected_revision,
        expected_hash=expected_hash,
        question_update=request,
        validation_assessor=validation_assessor,
    )


def _presentation_matches(
    question: dict[str, Any], evidence: Any, record: dict[str, Any]
) -> bool:
    if (
        not isinstance(evidence, dict)
        or not isinstance(record, dict)
        or not isinstance(record.get("failed_surfaces", {}), dict)
    ):
        return False
    surface = evidence.get("surface")
    if (
        question_surface_policy(
            evidence.get("host"), surface, record.get("failed_surfaces", {})
        )["verdict"]
        != "PASS"
    ):
        return False
    surface = (
        "structured-menu"
        if surface in ("request_user_input", "request_user_input_async")
        else surface
    )
    if surface in record.get("failed_surfaces", {}):
        return False
    if evidence.get("stage") not in ("prepared", "emitted"):
        return False
    if (
        not isinstance(evidence.get("source_ref"), str)
        or not evidence["source_ref"].strip()
    ):
        return False
    content = evidence.get("text")
    reply = evidence.get("reply_text")
    if not isinstance(content, str) or not isinstance(reply, str):
        return False
    expected = question["question"]
    options = question["options"]
    numbered_lines = re.findall(r"(?m)^\s*\d+[.)]\s+(.+)$", reply)
    if surface == "open-text":
        return (
            question.get("kind") == "open-text"
            and content == expected
            and reply.rstrip().endswith(expected)
            and not numbered_lines
        )
    if question.get("kind") == "open-text":
        return False
    expected += "\n\n" + "\n".join(
        f"{i}. {option}" for i, option in enumerate(options, 1)
    )
    if content != expected:
        return False
    if surface == "structured-menu" and not numbered_lines:
        # Options belong to the permitted Plan menu; the final reply repeats its question.
        return reply.rstrip().endswith(question["question"])
    return (
        evidence["host"].get("numbered_text_allowed") is True
        and numbered_lines == options
        and reply.rstrip().endswith(expected)
    )


def _replace_pending_decision(text: str, question: dict[str, Any] | None) -> str:
    text = re.sub(r"(?ims)^## Pending Decision\s*\n.*?(?=^## |\Z)", "", text)
    if question is not None:
        section = (
            "## Pending Decision\n\n```json\n"
            + json.dumps(question, ensure_ascii=False, indent=2)
            + "\n```\n\n"
        )
        text = re.sub(
            r"(?im)^## Revision History\s*$",
            lambda match: section + match.group(0),
            text,
            count=1,
        )
    return text


def assess_turn_context(
    project_root: Path, *, reference: str | None = None, task_ref: str | None = None
) -> dict[str, Any]:
    """Recover a question and open decisions from the existing authoritative pair."""
    resolved = resolve_working_bundle(
        project_root, reference=reference, task_ref=task_ref
    )
    if resolved["state"] == "absent":
        return {"state": "absent", "pending_question": None, "open_decisions": []}
    if resolved["state"] != "working":
        return {"state": "invalid", "reason": resolved["reason"]}
    working = resolved["working_spec"]
    if task_ref and working.get("task_ref") != task_ref:
        return {"state": "invalid", "reason": "working specification task mismatch"}
    text = (project_root / working["snapshot_path"]).read_text(encoding="utf-8")
    try:
        question = pending_decision(text)
        question_record = _question_record(text)
        if question and question_record.get("question_id") != question["id"]:
            question_record["failed_surfaces"] = {}
    except (ValueError, TypeError) as error:
        return {"state": "invalid", "reason": str(error)}
    consistency = _snapshot_consistency(text, text)
    canonical_path = (
        project_root / "specs" / f"{working['spec_id']}-{working['change_set']}.md"
    )
    canonical_matches = (
        _contract_hash(text)
        == _contract_hash(canonical_path.read_text(encoding="utf-8"))
        if canonical_path.is_file()
        else None
    )
    canonical_metadata = (
        _metadata(canonical_path.read_text(encoding="utf-8"))[0]
        if canonical_path.is_file()
        else {}
    )
    context = {
        "spec_presentation": {
            "spec_id": working["spec_id"],
            "title": next(
                (
                    line[2:].strip()
                    for line in text.splitlines()
                    if line.startswith("# ")
                ),
                "",
            ),
            "path": canonical_path.resolve().as_posix(),
            "revision": working["revision"],
            "snapshot_hash": working["snapshot_hash"],
        }
        if canonical_path.is_file()
        else None,
        "canonical_revision": canonical_metadata.get("revision"),
        "canonical_status": canonical_metadata.get("status"),
        "project_root": str(project_root.resolve()),
        "state": "pending" if question or consistency["open_decisions"] else "ready",
        "working_spec": working,
        "pending_question": question,
        "question_record": question_record,
        "presentation": {
            "markdown": question["question"]
            + ("\n\n" if question["options"] else "")
            + "\n".join(
                f"{index}. {option}"
                for index, option in enumerate(question["options"], 1)
            ),
            "response_deadline": None,
            "request_mode_change": False,
        }
        if question
        else None,
        "open_decisions": consistency["open_decisions"],
        "conflicts": consistency["conflicts"],
        "canonical_matches": canonical_matches,
    }
    context["continuation"] = assess_discussion_completion(
        context, {"working_spec": working, "project_root": context["project_root"]}
    )
    return context


def _spec_reply_matches(context: dict, observation: dict) -> bool:
    """Validate an emitted reply, not a panel-open or a caller's presented flag."""
    expected = context.get("spec_presentation")
    evidence = observation.get("spec_presentation")
    if not isinstance(expected, dict) or not isinstance(evidence, dict):
        return False
    if (
        evidence.get("stage") != "emitted"
        or not isinstance(evidence.get("source_ref"), str)
        or not evidence["source_ref"].strip()
    ):
        return False
    if any(
        evidence.get(key) != expected.get(key)
        for key in ("spec_id", "revision", "snapshot_hash")
    ):
        return False
    reply = evidence.get("reply_text")
    summary = evidence.get("summary")
    if (
        not isinstance(reply, str)
        or not isinstance(summary, str)
        or not summary.strip()
    ):
        return False
    # Code examples cannot establish an actually rendered clickable specification.
    visible = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1[^\n]*$", "", reply)
    visible = re.sub(r"(?s)<!--.*?-->", "", visible)
    visible = re.sub(r"(?m)^(?: {4}|\t).*?$", "", visible)
    visible = re.sub(
        r"(?is)<(div|pre|details|script|style)\b[^>]*>.*?</\1\s*>", "", visible
    )
    visible = re.sub(r"`[^`\n]*`", "", visible)
    if re.search(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*|/?)>", visible):
        return False
    links = [
        (label, angle or bare)
        for label, angle, bare in re.findall(
            r"(?<![!\\])\[([^]\n]+?)(?<!\\)\]\((?:<([^<>\n]+)>|([^\s<>()]+))\)", visible
        )
    ]
    if not any(
        expected.get("spec_id", "") in label
        and expected.get("title", "") in label
        and target == expected.get("path")
        for label, target in links
    ):
        return False
    if summary.strip() not in visible:
        return False
    revision = str(expected.get("revision"))
    status = context.get("canonical_status") or context.get("working_spec", {}).get(
        "status"
    )
    if not re.search(
        r"(?:revision|修訂)\s*[:：]?\s*" + re.escape(revision) + r"(?!\d)",
        visible,
        re.IGNORECASE,
    ) or not re.search(r"\b" + re.escape(str(status)) + r"\b", visible):
        return False
    execution = observation.get("execution")
    if (
        isinstance(execution, dict)
        and execution.get("verdict") == "PASS"
        and execution.get("product_code_allowed") is True
    ):
        binding = execution.get("binding")
        working = context["working_spec"]
        if not isinstance(binding, dict) or any(
            binding.get(k) != v
            for k, v in {
                "project_root": context["project_root"],
                "task_ref": working["task_ref"],
                "working_id": working["working_id"],
                "snapshot_hash": working["snapshot_hash"],
            }.items()
        ):
            return False
        return (
            evidence.get("status") == "executing"
            and "SPEC 已完成，已取得本次「開始執行」授權" in visible
            and "等待「開始執行」" not in visible
        )
    return (
        evidence.get("status") == "awaiting-authorization"
        and "SPEC 已完成，等待「開始執行」" in visible
        and "已取得本次「開始執行」授權" not in visible
    )


def assess_discussion_completion(
    context: dict[str, Any], observation: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Check observed presentation against one recovered discussion, never authorize writes."""
    result = {
        "verdict": "BLOCKED",
        "can_end_turn": False,
        "next_action": "recover-context",
        "product_code_allowed": False,
        "enforcement_scope": "observed-discussion-only",
    }
    if not isinstance(context, dict) or not isinstance(observation, dict):
        return result
    if observation.get("unreconciled_decision"):
        return result | {"next_action": "reconcile"}
    question_tools = observation.get("question_tools", [])
    if not isinstance(question_tools, list) or any(
        question_surface_policy(observation.get("host"), tool)["verdict"] != "PASS"
        for tool in question_tools
    ):
        return result | {"reason": "observed question tool forbidden by current mode"}
    # A recorded context failure may itself be the blocker requiring user input.
    blocker = observation.get("blocker")
    if (
        context.get("state") in ("invalid", "absent")
        and observation.get("context_error") == context
        and isinstance(blocker, dict)
        and all(
            isinstance(blocker.get(key), str) and blocker[key].strip()
            for key in ("detail", "required_input", "evidence_ref", "presentation_ref")
        )
    ):
        return result | {
            "verdict": "PASS",
            "can_end_turn": True,
            "next_action": "await-blocker-input",
        }
    if (
        not isinstance(context.get("project_root"), str)
        or observation.get("project_root") != context["project_root"]
    ):
        return result
    working = context.get("working_spec")
    if not isinstance(working, dict) or observation.get("working_spec") != working:
        return result
    if any(
        not isinstance(working.get(key), str) or not working[key].strip()
        for key in ("working_id", "task_ref", "snapshot_hash", "status")
    ):
        return result
    if type(working.get("revision")) is not int or working["revision"] < 1:
        return result
    if not isinstance(context.get("open_decisions"), list) or not isinstance(
        context.get("conflicts"), list
    ):
        return result

    def has_text(record: Any, keys: tuple[str, ...]) -> bool:
        return isinstance(record, dict) and all(
            isinstance(record.get(key), str) and record[key].strip() for key in keys
        )

    pause = observation.get("pause")
    pause_text = pause.get("user_text", "") if isinstance(pause, dict) else ""
    explicit_pause = (
        isinstance(pause_text, str)
        and bool(
            re.search(
                r"暫停討論|停止討論|先不討論|暫停全部|停止全部|暫停所有|停止所有|(?:pause|stop|end)\s+(?:the\s+)?(?:discussion|all\s+work)",
                pause_text,
                re.IGNORECASE,
            )
        )
        and not re.search(
            r"不要|別|not|don't|continue\s+discussion|繼續討論",
            pause_text,
            re.IGNORECASE,
        )
    )
    if (
        explicit_pause
        and has_text(pause, ("scope", "user_text", "source_ref"))
        and pause["scope"]
        in {
            "discussion",
            "all",
        }
    ):
        return result | {
            "verdict": "PASS",
            "can_end_turn": True,
            "next_action": "paused-by-user",
        }
    blocker = observation.get("blocker")
    if has_text(
        blocker, ("detail", "required_input", "evidence_ref", "presentation_ref")
    ):
        return result | {
            "verdict": "PASS",
            "can_end_turn": True,
            "next_action": "await-blocker-input",
        }
    if context.get("state") not in ("pending", "ready") or context.get("conflicts"):
        return result
    question = context.get("pending_question")
    if question is not None:
        if not isinstance(question, dict) or not has_text(question, ("id", "question")):
            return result
        if type(question.get("version")) is not int or question["version"] < 1:
            return result
        options = question.get("options")
        if (
            not isinstance(options, list)
            or (
                len(options) != 0
                if question.get("kind") == "open-text"
                else len(options) < 2
            )
            or any(not isinstance(x, str) or not x.strip() for x in options)
        ):
            return result
        if (
            observation.get("question_presented") == question
            and has_text(observation, ("presentation_ref",))
            and _presentation_matches(
                question,
                observation.get("presentation"),
                context.get("question_record", {}),
            )
        ):
            return result | {
                "verdict": "PASS",
                "can_end_turn": True,
                "next_action": "await-answer",
                "presentation_stage": observation["presentation"]["stage"],
                "delivery_verified": False,
            }
        return result | {"next_action": "present-pending-question"}
    if context.get("open_decisions"):
        return result | {"next_action": "ask-next-decision"}
    if (
        working.get("status") != "confirmed"
        or context.get("canonical_status") != "confirmed"
        or str(context.get("canonical_revision")) != str(working.get("revision"))
        or context.get("canonical_matches") is not True
    ):
        return result | {"next_action": "materialize"}
    if (
        observation.get("proposal_presented") is True
        and has_text(observation, ("presentation_ref",))
        and _spec_reply_matches(context, observation)
    ):
        return result | {
            "verdict": "PASS",
            "can_end_turn": True,
            "next_action": "continue-authorized-execution"
            if observation["spec_presentation"]["status"] == "executing"
            else "await-execution-authorization",
            "delivery_verified": True,
        }
    return result | {
        "next_action": "present-confirmed-proposal",
        "reason": "emit current SPEC ID, title, clickable link, summary and authorization status in the reply",
    }


def finish_discussion_turn(
    project_root: Path, *, reference: str, task_ref: str, observation: dict[str, Any]
) -> dict[str, Any]:
    """Reload project/task context before accepting a discussion turn's stopping point."""
    if not isinstance(observation, dict):
        return {
            "verdict": "BLOCKED",
            "can_end_turn": True,
            "sync_status": "unverifiable",
            "next_action": "report-save-gap-and-finish",
            "reason": "completion observation must be an object",
        }
    if not all(
        isinstance(value, str) and value.strip() for value in (reference, task_ref)
    ):
        return assess_discussion_completion({}, {})
    context = assess_turn_context(project_root, reference=reference, task_ref=task_ref)
    # The host-backed discussion state is owner-local; older contexts retain their
    # historical completion contract, never fabricated entry evidence.
    from discussion_state import discussion_request

    try:
        state = (
            discussion_request(
                project_root, {"operation": "resume", "task_ref": task_ref}
            )["state"]
            if task_ref
            else {"active_turn": None}
        )
        if state["active_turn"]:
            saved = discussion_request(
                project_root,
                {
                    "operation": "verify",
                    "task_ref": task_ref,
                    "turn_id": observation.get("turn_id", ""),
                    "reply_text": observation.get("reply_text", ""),
                },
            )
            if (
                saved["verdict"] != "PASS"
                or saved.get("original_turn") != state["active_turn"]
                or observation.get("working_spec") != context.get("working_spec")
            ):
                return {
                    "verdict": "BLOCKED",
                    "can_end_turn": True,
                    "discussion_sync": saved,
                    "next_action": "report-unsaved-discussion",
                    "product_code_allowed": False,
                }
            if (
                context.get("state") == "ready"
                and not context.get("conflicts")
                and not any(
                    key.startswith("REQ-")
                    for key in _snapshot_rows(
                        (
                            project_root / context["working_spec"]["snapshot_path"]
                        ).read_text(encoding="utf-8")
                    )
                )
                and not context.get("open_decisions")
            ):
                return {
                    "verdict": "PASS",
                    "can_end_turn": True,
                    "next_action": "discussion-saved",
                    "product_code_allowed": False,
                }
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {
            "verdict": "BLOCKED",
            "can_end_turn": True,
            "next_action": "report-unverifiable-discussion",
            "reason": str(error),
            "product_code_allowed": False,
        }
    return assess_discussion_completion(context, observation)


def record_question(
    project_root: Path,
    working_id: str,
    question_id: str,
    question_text: str,
    options: list[str],
    *,
    expected_revision: int,
    expected_hash: str,
    question_kind: str = "choice",
    validation_assessor=None,
) -> dict[str, Any]:
    """Persist options before presentation, without a deadline or mode dependency."""
    if question_kind == "choice" and len(options) < 3:
        return {
            "verdict": "BLOCKED",
            "reason": "new decision questions require at least three meaningful options",
        }
    if question_kind not in ("choice", "open-text"):
        return {"verdict": "BLOCKED", "reason": "unknown question kind"}
    resolved = resolve_working_bundle(project_root, reference=working_id)
    if resolved["state"] != "working":
        return {"verdict": "BLOCKED", "reason": resolved["reason"]}
    ref = resolved["working_spec"]
    if ref["status"] != "working":
        return {
            "verdict": "BLOCKED",
            "reason": "reopen the specification before a new question",
        }
    text = (project_root / ref["snapshot_path"]).read_text(encoding="utf-8")
    try:
        if pending_decision(text):
            return {
                "verdict": "BLOCKED",
                "reason": "recover the existing pending question first",
            }
        rendered = _replace_pending_decision(
            text,
            {
                "id": question_id,
                "version": expected_revision + 1,
                "question": question_text,
                "options": options,
                **({"kind": "open-text"} if question_kind == "open-text" else {}),
            },
        )
        pending_decision(rendered)
    except (ValueError, TypeError) as error:
        return {"verdict": "BLOCKED", "reason": str(error)}
    return reconcile_working_bundle(
        project_root,
        working_id,
        rendered,
        {},
        expected_revision=expected_revision,
        expected_hash=expected_hash,
        validation_assessor=validation_assessor,
    )


def _table(section: str) -> list[dict[str, str]]:
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in section.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if len(rows) < 2:
        return []
    headers = rows[0]
    data = (
        rows[2:]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1])
        else rows[1:]
    )
    return [dict(zip(headers, cells)) for cells in data if len(cells) == len(headers)]


def _field(row: dict[str, str], name: str) -> str:
    wanted = name.casefold()
    for key, value in row.items():
        if key.casefold() == wanted:
            return value.strip()
    return ""


def _open_decisions_are_empty(value: str) -> bool:
    normalized = re.sub(r"[\s.*_-]+", "", value).casefold()
    return normalized in {"none", "noopen decisions", "無", "無未決事項"}


def validate_spec_text(
    text: str,
    *,
    known_spec_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Return a strict structural and traceability assessment."""
    metadata, errors = _metadata(text)
    sections = _sections(text)
    missing_sections = sorted(REQUIRED_SECTIONS - set(sections))
    errors.extend(f"missing section: {name}" for name in missing_sections)

    required_metadata = {"spec_version", "spec_id", "revision", "status", "change_set"}
    errors.extend(
        f"missing metadata: {name}"
        for name in sorted(required_metadata - set(metadata))
    )
    if metadata.get("spec_version") != "1":
        errors.append("spec_version must be 1")
    if not SPEC_ID_RE.fullmatch(metadata.get("spec_id", "")):
        errors.append("spec_id must match SPEC-####")
    try:
        if int(metadata.get("revision", "0")) < 1:
            raise ValueError
    except ValueError:
        errors.append("revision must be a positive integer")
    status = metadata.get("status", "")
    if status not in {"working", "confirmed", "implemented"}:
        errors.append("status must be working, confirmed, or implemented")
    slug = metadata.get("change_set", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        errors.append("change_set must be a lowercase kebab-case slug")

    requirements = _table(sections.get("requirements", ""))
    decisions = _table(sections.get("decisions", ""))
    acceptance = _table(sections.get("acceptance criteria", ""))
    relationships = _table(sections.get("relationships", ""))
    rows_by_kind = {
        "REQ": requirements,
        "DEC": decisions,
        "AC": acceptance,
    }
    all_ids: list[str] = []
    for prefix, rows in rows_by_kind.items():
        for row in rows:
            item_id = _field(row, "ID")
            if not re.fullmatch(rf"{prefix}-\d{{3}}", item_id):
                errors.append(f"invalid {prefix} ID: {item_id or '<missing>'}")
            all_ids.append(item_id)
    duplicates = sorted({item_id for item_id in all_ids if all_ids.count(item_id) > 1})
    errors.extend(f"duplicate ID: {item_id}" for item_id in duplicates)
    known_ids = set(all_ids)

    req_ids = {_field(row, "ID") for row in requirements}
    covered: set[str] = set()
    uncovered_acceptance: list[str] = []
    for row in acceptance:
        ac_id = _field(row, "ID")
        refs = [
            value.strip()
            for value in re.split(r"[,; ]+", _field(row, "Requirements"))
            if value.strip()
        ]
        for ref in refs:
            if ref not in req_ids:
                errors.append(f"{ac_id} references unknown requirement {ref}")
            else:
                covered.add(ref)
        if not _field(row, "Validation Method"):
            uncovered_acceptance.append(ac_id)
    uncovered_requirements = sorted(req_ids - covered)
    errors.extend(
        f"{item_id} has no acceptance criterion" for item_id in uncovered_requirements
    )

    conflicts: list[dict[str, str]] = []
    for row in relationships:
        source = _field(row, "Source")
        relation = _field(row, "Relation")
        target = _field(row, "Target")
        if relation not in RELATIONS:
            errors.append(f"invalid relation: {relation or '<missing>'}")
        for ref in (source, target):
            if SPEC_ID_RE.fullmatch(ref):
                allowed_specs = set(known_spec_ids or ())
                allowed_specs.add(metadata.get("spec_id", ""))
                if ref not in allowed_specs:
                    errors.append(f"relationship references unknown spec {ref}")
            elif ref not in known_ids:
                errors.append(
                    f"relationship references unknown ID {ref or '<missing>'}"
                )
        if relation == "conflicts_with":
            conflicts.append({"source": source, "target": target})

    open_decisions = sections.get("open decisions", "")
    try:
        if pending_decision(text):
            errors.append("unanswered pending decision prevents canonical verification")
    except (ValueError, TypeError) as error:
        errors.append(str(error))
    if status in {"confirmed", "implemented"} and not _open_decisions_are_empty(
        open_decisions
    ):
        errors.append("confirmed and implemented specs must have zero open decisions")
    if status in {"confirmed", "implemented"} and conflicts:
        errors.append(
            "confirmed and implemented specs must have zero unresolved conflicts"
        )

    if status == "implemented":
        for row in acceptance:
            if not _field(row, "Evidence").casefold().startswith("pass"):
                uncovered_acceptance.append(_field(row, "ID"))
        gates = sections.get("routing/gates", "")
        if re.search(r"(?im)spec review:\s*pass\b", gates) is None:
            errors.append("implemented spec requires Spec review: PASS")
    uncovered_acceptance = sorted(set(filter(None, uncovered_acceptance)))
    errors.extend(
        f"{item_id} lacks required validation or PASS evidence"
        for item_id in uncovered_acceptance
    )

    verdict = "PASS" if not errors else "BLOCKED"
    reference = {
        "spec_id": metadata.get("spec_id"),
        "path": None,
        "revision": int(metadata["revision"])
        if metadata.get("revision", "").isdigit()
        else None,
        "status": status or None,
    }
    return {
        "verdict": verdict,
        "errors": errors,
        "canonical_spec": reference,
        "traceability": {
            "verdict": verdict,
            "uncovered_requirements": uncovered_requirements,
            "uncovered_acceptance": uncovered_acceptance,
            "scope_creep": [],
        },
    }


def _next_item_id(rows: list[dict[str, str]], prefix: str) -> str:
    numbers = [
        int(match.group(2))
        for row in rows
        if (match := ITEM_ID_RE.fullmatch(str(row.get("id", ""))))
        and match.group(1) == prefix
    ]
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def reconcile_working_spec(
    working_spec: dict[str, Any],
    new_content: dict[str, Any],
) -> dict[str, Any]:
    """Merge a discussion delta while preserving stable IDs across revisions."""
    result: dict[str, Any] = {
        key: [dict(row) for row in working_spec.get(key, [])]
        for key in ("requirements", "decisions", "acceptance_criteria")
    }
    added_ids: list[str] = []
    changed_ids: list[str] = []
    removed_ids: list[str] = []
    mapping = {
        "requirements": "REQ",
        "decisions": "DEC",
        "acceptance_criteria": "AC",
    }
    for key, prefix in mapping.items():
        existing_by_id = {str(row.get("id", "")): row for row in result[key]}
        existing_by_text = {
            str(row.get("text", "")).strip().casefold(): row for row in result[key]
        }
        for value in new_content.get(key, []):
            incoming = {"text": value} if isinstance(value, str) else dict(value)
            requested_id = str(incoming.pop("id", "")).strip()
            text = str(incoming.get("text", "")).strip()
            incoming["text"] = text
            if requested_id and requested_id in existing_by_id:
                current = existing_by_id[requested_id]
                updated = {**current, **incoming, "id": requested_id}
                if updated != current:
                    old_text = str(current.get("text", "")).strip().casefold()
                    current.clear()
                    current.update(updated)
                    existing_by_text.pop(old_text, None)
                    existing_by_text[text.casefold()] = current
                    if requested_id not in changed_ids:
                        changed_ids.append(requested_id)
                continue
            normalized = text.casefold()
            if normalized in existing_by_text:
                continue
            item_id = _next_item_id(result[key], prefix)
            row = {**incoming, "id": item_id}
            result[key].append(row)
            existing_by_id[item_id] = row
            existing_by_text[normalized] = row
            added_ids.append(item_id)

    requested_removals = list(dict.fromkeys(new_content.get("removed_ids", [])))
    for item_id in requested_removals:
        for key in mapping:
            retained = [row for row in result[key] if str(row.get("id", "")) != item_id]
            if len(retained) != len(result[key]):
                result[key] = retained
                removed_ids.append(item_id)
                if item_id in added_ids:
                    added_ids.remove(item_id)
                if item_id in changed_ids:
                    changed_ids.remove(item_id)
                break

    relationships = [dict(item) for item in working_spec.get("relationships", [])]
    for item in new_content.get("relationships", []):
        if item not in relationships:
            relationships.append(dict(item))
    resolved_relationships = {
        json.dumps(item, sort_keys=True)
        for item in new_content.get("resolved_relationships", [])
    }
    relationships = [
        item
        for item in relationships
        if json.dumps(item, sort_keys=True) not in resolved_relationships
        and item.get("source") not in removed_ids
        and item.get("target") not in removed_ids
    ]
    open_decisions = list(working_spec.get("open_decisions", []))
    for item in new_content.get("open_decisions", []):
        if item not in open_decisions:
            open_decisions.append(item)
    resolved_open = set(new_content.get("resolved_open_decisions", []))
    open_decisions = [item for item in open_decisions if item not in resolved_open]

    conflicts = [dict(item) for item in working_spec.get("conflicts", [])]
    for item in new_content.get("conflicts", []):
        if item not in conflicts:
            conflicts.append(dict(item))
    resolved_conflicts = {
        json.dumps(item, sort_keys=True)
        for item in new_content.get("resolved_conflicts", [])
    }
    conflicts = [
        item
        for item in conflicts
        if json.dumps(item, sort_keys=True) not in resolved_conflicts
    ]
    result["relationships"] = relationships
    result["open_decisions"] = open_decisions
    result["conflicts"] = conflicts
    return {
        "verdict": "BLOCKED" if open_decisions or conflicts else "PASS",
        "working_spec": result,
        "delta": {
            "added_ids": added_ids,
            "changed_ids": changed_ids,
            "removed_ids": removed_ids,
        },
        "relationships": relationships,
        "conflicts": conflicts,
        "open_decisions": open_decisions,
    }


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _snapshot_hash(text: str) -> str:
    """Hash the canonical body without recursively hashing its embedded audit."""
    return _sha256_text(_split_spec_audit(text)[0])


def _split_spec_audit(text: str) -> tuple[str, str]:
    start = text.find("\n<!-- spec-audit:start -->")
    if start < 0:
        return text, ""
    end = text.find("<!-- spec-audit:end -->", start)
    if end < 0:
        return text, ""
    end += len("<!-- spec-audit:end -->")
    if text[end : end + 1] == "\n":
        end += 1
    return text[:start] + text[end:], text[start:end]


def _normalized_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _acceptance_planning(
    project_root: Path, text: str, previous: str | None = None
) -> dict:
    metadata, _ = _metadata(text)
    path = project_root / "validation" / f"acceptance-{metadata.get('spec_id')}.json"

    def criteria(value):
        return {
            key: {k: v for k, v in row.items() if k.casefold() != "evidence"}
            for key, row in _snapshot_rows(value).items()
            if key.startswith("AC-")
        }

    current = criteria(text)
    prior = criteria(previous) if previous is not None else current
    if not (
        path.exists()
        or (project_root / "validation").is_dir()
        or (project_root / "architecture/manifest.yaml").is_file()
    ):
        return {
            "verdict": "PASS",
            "applicability": "legacy-unconfigured",
            "execution_ready": True,
            "saved_specification_independent": True,
        }
    try:
        document = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if not isinstance(document, dict):
            raise ValueError("acceptance document must be an object")
        mapping = document.get("acceptance", {})
        if not isinstance(mapping, dict) or any(
            not isinstance(value, dict) for value in mapping.values()
        ):
            raise ValueError("acceptance must be an object")
    except (OSError, ValueError, TypeError) as exc:
        return {"verdict": "BLOCKED", "path": str(path), "errors": [str(exc)]}
    missing = sorted(set(current) - set(mapping))
    removed = sorted(set(mapping) - set(current))
    changed = sorted(
        key for key in current.keys() & prior.keys() if current[key] != prior[key]
    )
    stale = sorted(
        key
        for key in current.keys() & mapping.keys()
        if mapping[key].get("criterion_sha256") is not None
        and mapping[key]["criterion_sha256"]
        != _sha256_text(_normalized_json(current[key]))
    )
    return {
        "verdict": "BLOCKED" if missing or removed or changed or stale else "PASS",
        "path": path.relative_to(project_root).as_posix(),
        "missing": missing,
        "removed": removed,
        "changed": changed,
        "stale": stale,
        "criterion_hashes": {
            key: _sha256_text(_normalized_json(value)) for key, value in current.items()
        },
        "execution_ready": not (missing or removed or changed or stale),
        "saved_specification_independent": True,
    }


def generated_acceptance(text: str, *, known_spec_ids=None) -> dict:
    """Rebuild definitions from SPEC; never infer selectors or execution evidence."""
    checked = validate_spec_text(text, known_spec_ids=known_spec_ids)
    if checked["verdict"] != "PASS":
        raise ValueError("invalid canonical specification")
    metadata, _ = _metadata(text)
    criteria = {
        key: {k: v for k, v in row.items() if k.casefold() != "evidence"}
        for key, row in _snapshot_rows(text).items()
        if key.startswith("AC-")
    }
    declared = _sections(text).get("acceptance mapping", "").strip()
    if declared.startswith("```json\n") and declared.endswith("```"):
        declared = declared[len("```json\n") : -3].strip()
    selectors = json.loads(declared) if declared else {}
    if not isinstance(selectors, dict) or set(selectors) - set(criteria):
        raise ValueError("Acceptance Mapping must refer only to current AC IDs")
    for key, value in selectors.items():
        if not isinstance(value, dict) or set(value) - {
            "evidence_claims",
            "contract_dimensions",
            "execution_changes",
            "rationale",
            "scenario_layers",
            "enablement_scenarios",
            "build_artifact",
        }:
            raise ValueError(key + ": unsupported selector fields")
    definitions = {
        key: {
            "definition": row,
            "criterion_sha256": _sha256_text(_normalized_json(row)),
            **selectors.get(key, {}),
        }
        for key, row in criteria.items()
    }
    return {
        "schema_version": 2,
        "spec_id": metadata["spec_id"],
        "source": {
            "revision": int(metadata["revision"]),
            "definitions_sha256": _sha256_text(_normalized_json(definitions)),
        },
        "acceptance": definitions,
    }


def acceptance_selector_gaps(acceptance: dict, matrix=None) -> list[str]:
    """Report every AC selection gap without treating a projection as evidence."""
    ladder = Path(__file__).resolve().parents[2] / "verification-ladder" / "scripts"
    if str(ladder) not in sys.path:
        sys.path.insert(0, str(ladder))
    from verification_ladder import TAXONOMY, UNIVERSAL_LAYERS, plan

    gaps = []
    for ac, item in acceptance.items():
        if not isinstance(item, dict):
            gaps.append(f"{ac}: selectors must be an object")
            continue
        requested = {}
        invalid = False
        for field, allowed in TAXONOMY.items():
            values = item.get(field, [])
            if not isinstance(values, list) or any(
                not isinstance(v, str) or v not in allowed for v in values
            ):
                gaps.append(f"{ac}: {field} must contain known selection values")
                invalid = True
            else:
                requested[field] = set(values)
        if not item.get("evidence_claims"):
            gaps.append(f"{ac}: evidence claims (evidence_claims) required")
            invalid = True
        rationale = item.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            gaps.append(f"{ac}: applicability rationale required")
            invalid = True
        if matrix is None and not invalid:
            selected_layers = set().union(
                *(UNIVERSAL_LAYERS[v] for values in requested.values() for v in values)
            )
            if selected_layers & {"pil", "hil", "system-soak"}:
                gaps.append(f"{ac}: device selections require a verification matrix")
        if matrix is not None and not invalid:
            selected = plan(matrix, requested)
            if selected["status"] != "PASS":
                gaps.extend(f"{ac}: {error}" for error in selected["errors"])
                continue
            layers = set(selected["required_layers"])
            if layers - set(matrix["layers"]):
                gaps.append(f"{ac}: required layer has no project contract")
            devices = layers & {"pil", "hil", "system-soak"}
            scenarios = item.get("scenario_layers", {})
            if (
                not isinstance(scenarios, dict)
                or set(scenarios) != devices
                or any(
                    not isinstance(v, list)
                    or not v
                    or any(not isinstance(s, str) or not s.strip() for s in v)
                    for v in scenarios.values()
                )
            ):
                gaps.append(f"{ac}: scenario_layers must cover selected device layers")
            if devices and (
                not isinstance(item.get("build_artifact"), str)
                or not item["build_artifact"].strip()
            ):
                gaps.append(f"{ac}: build_artifact required for device layers")
    return gaps


def acceptance_plan_completeness(project_root: Path, text: str) -> list[str]:
    """Read canonical selections before confirmation; preserve legacy host drafts."""
    matrix_path = project_root / "validation/verification-ladder.yaml"
    declared = "acceptance mapping" in _sections(text)
    if not matrix_path.is_file() and not declared:
        return []
    import yaml

    try:
        document = generated_acceptance(
            text,
            known_spec_ids=_repository_spec_ids(project_root)
            | {_metadata(text)[0].get("spec_id", "")},
        )
        matrix = None
        if matrix_path.is_file():
            matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
            if (
                not isinstance(matrix, dict)
                or not isinstance(matrix.get("layers"), dict)
                or not isinstance(matrix.get("rules"), list)
            ):
                return ["Acceptance planning: invalid verification matrix"]
        return acceptance_selector_gaps(document["acceptance"], matrix)
    except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError) as error:
        return ["Acceptance planning: " + str(error)]


def acceptance_generation_plan(project_root: Path, spec_path: str) -> dict:
    """Prepare a reconstructible projection for the ordinary managed apply entry."""
    root = project_root.resolve()
    path = (root / spec_path).resolve()
    if path.parent != root / "specs" or not path.is_file():
        return {"verdict": "BLOCKED", "reason": "canonical specification required"}
    try:
        document = generated_acceptance(
            path.read_text(encoding="utf-8"), known_spec_ids=_repository_spec_ids(root)
        )
        target = root / "validation" / ("acceptance-" + document["spec_id"] + ".json")
        if target.is_symlink():
            raise ValueError("redirected acceptance path")
        raw = target.read_bytes() if target.exists() else None
        content = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
        unresolved = [
            key
            for key, row in document["acceptance"].items()
            if not row.get("evidence_claims") or not row.get("rationale")
        ]
        planning_errors = list(
            dict.fromkeys(
                acceptance_selector_gaps(document["acceptance"])
                + acceptance_plan_completeness(root, path.read_text(encoding="utf-8"))
            )
        )
        return {
            "verdict": "PASS",
            "generation_verdict": "PASS",
            "planning_verdict": "BLOCKED" if planning_errors else "PASS",
            "planning_errors": planning_errors,
            "product_code_allowed": False,
            "acceptance_complete": False,
            "unresolved_selectors": unresolved,
            "patch": None
            if raw is not None and raw.decode("utf-8").replace("\r\n", "\n") == content
            else {
                "path": target.relative_to(root).as_posix(),
                "before_sha256": hashlib.sha256(raw).hexdigest()
                if raw is not None
                else None,
                "content": content,
            },
        }
    except (OSError, ValueError, TypeError, KeyError) as error:
        return {
            "verdict": "BLOCKED",
            "reason": str(error),
            "product_code_allowed": False,
        }


def acceptance_repair_plan(project_root: Path, spec_path: str) -> dict:
    """Derive an additive mapping only from explicitly declared contract data.

    Natural-language test selection remains a reviewed draft. This read-only
    operation grants no authority and never interprets prose as machine policy.
    """
    root = project_root.resolve()
    path = (root / spec_path).resolve()
    blocked = {
        "verdict": "BLOCKED",
        "product_code_allowed": False,
        "draft_required": True,
    }
    if path.parent != root / "specs" or not path.is_file():
        return blocked | {"reason": "canonical specification required"}
    text = path.read_text(encoding="utf-8")
    checked = validate_spec_text(text)
    if checked["verdict"] != "PASS":
        return blocked | {"reason": "invalid canonical specification"}
    planning = _acceptance_planning(root, text)
    if planning.get("errors") or any(
        planning.get(k) for k in ("stale", "removed", "changed")
    ):
        return blocked | {
            "reason": "repair cannot replace or remove existing criteria",
            "planning": planning,
        }
    declared = _sections(text).get("acceptance mapping", "").strip()
    if declared.startswith("```json\n") and declared.endswith("```"):
        declared = declared[len("```json\n") : -3].strip()
    try:
        approved = json.loads(declared)
    except (ValueError, TypeError):
        return blocked | {
            "reason": "missing explicit Acceptance Mapping data; retain a reviewed draft",
            "planning": planning,
        }
    if not isinstance(approved, dict):
        return blocked | {"reason": "Acceptance Mapping must be an AC-keyed object"}
    identity = checked["canonical_spec"]["spec_id"]
    relative = f"validation/acceptance-{identity}.json"
    target = root / relative
    raw = target.read_bytes() if target.exists() else None
    document = (
        json.loads(raw.decode("utf-8"))
        if raw is not None
        else {
            "schema_version": 1,
            "spec_id": identity,
            "acceptance": {},
        }
    )
    if (
        not isinstance(document, dict)
        or set(document) != {"schema_version", "spec_id", "acceptance"}
        or type(document["schema_version"]) is not int
        or document["schema_version"] != 1
        or document["spec_id"] != identity
        or not isinstance(document["acceptance"], dict)
    ):
        return blocked | {"reason": "existing mapping schema/identity is invalid"}
    hashes = planning.get("criterion_hashes", {})
    missing = sorted(set(hashes) - set(document["acceptance"]))
    if not missing:
        return {
            "verdict": "PASS",
            "product_code_allowed": False,
            "missing": [],
            "patch": None,
        }
    for key in missing:
        row = approved.get(key)
        if not isinstance(row, dict) or set(row) != {
            "evidence_claims",
            "contract_dimensions",
            "execution_changes",
            "rationale",
        }:
            return blocked | {"reason": key + ": explicit bounded mapping required"}
        if not isinstance(row["rationale"], str) or not row["rationale"].strip():
            return blocked | {"reason": key + ": mapping rationale required"}
        for field in ("evidence_claims", "contract_dimensions", "execution_changes"):
            values = row[field]
            if (
                not isinstance(values, list)
                or any(not isinstance(v, str) or not v.strip() for v in values)
                or len(set(values)) != len(values)
            ):
                return blocked | {"reason": key + ": invalid mapping dimensions"}
        if not row["evidence_claims"]:
            return blocked | {"reason": key + ": evidence claims required"}
        document["acceptance"][key] = row | {"criterion_sha256": hashes[key]}
    return {
        "verdict": "PASS",
        "product_code_allowed": False,
        "missing": missing,
        "patch": {
            "path": relative,
            "before_sha256": hashlib.sha256(raw).hexdigest()
            if raw is not None
            else None,
            "content": json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        },
    }


def _contract_completeness_gaps(project_root: Path, text: str) -> list[str]:
    gaps = list(
        validate_spec_text(text, known_spec_ids=_repository_spec_ids(project_root))[
            "errors"
        ]
    )
    sections = _sections(text)
    for name in ("problem", "solution", "out of scope"):
        if sections.get(name, "").strip().casefold() in {
            "",
            "none",
            "none.",
            "tbd",
            "pending",
        }:
            gaps.append("Define " + name + " before confirmation.")
    for key, row in _snapshot_rows(text).items():
        fields = (
            ("requirement",)
            if key.startswith("REQ-")
            else ("criterion", "validation method")
            if key.startswith("AC-")
            else ()
        )
        for field in fields:
            if row.get(field, "").strip().casefold() in {
                "",
                "none",
                "none.",
                "tbd",
                "pending",
            }:
                gaps.append(key + " has no meaningful " + field + ".")
    gaps.extend(acceptance_plan_completeness(project_root, text))
    return gaps


def _refresh_discussion_views(text: str, project_root: Path) -> str:
    """Maintain readable navigation and discoverable structural gaps in the SPEC."""
    body, audit = _split_spec_audit(text)
    if audit:
        audit_end = text.index(audit) + len(audit)
        trailing = text[audit_end:]
        if trailing.strip():
            body = (
                text[: text.index(audit)] + "\n## Discussion Additions\n\n" + trailing
            )
    for name in (
        "Current Specification",
        "Decision History",
        "Pending Discussion",
        "Completeness Gaps",
    ):
        body = re.sub(r"(?ms)^## " + re.escape(name) + r"\n.*?(?=^## |\Z)", "", body)
    confirmed = _replace_metadata(body, status="confirmed")
    gaps = _contract_completeness_gaps(project_root, confirmed)
    rows = _snapshot_rows(body)
    if not any(key.startswith("REQ-") for key in rows):
        gaps.append(
            "No adopted change requirements; pure discussion may end without confirmation."
        )
    if not any(key.startswith("AC-") for key in rows):
        gaps.append("No acceptance criteria for an adopted change.")
    open_decisions = _snapshot_consistency(body, body)["open_decisions"]
    body = body.rstrip() + (
        "\n\n## Current Specification\n\nSee Problem, Solution, Requirements and Acceptance Criteria above.\n"
        "\n## Decision History\n\nSee Decisions, Discussion Context and the sourced Discussion History below.\n"
        "\n## Pending Discussion\n\n"
        + ("\n".join("- " + item for item in open_decisions) or "None.")
        + "\n\n## Completeness Gaps\n\n"
        + ("\n".join("- " + str(item) for item in gaps) or "None.")
        + "\n"
    )
    return body + audit


def _atomic_write(path: Path, text: str, *, preserve_audit: bool = True) -> None:
    if (
        preserve_audit
        and path.suffix == ".md"
        and path.is_file()
        and "<!-- spec-audit:start -->" not in text
    ):
        existing = path.read_text(encoding="utf-8")
        if "\n<!-- spec-audit:start -->" in existing:
            text += (
                "\n<!-- spec-audit:start -->"
                + existing.split("\n<!-- spec-audit:start -->", 1)[1]
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _replace_metadata(text: str, **updates: str | int | None) -> str:
    metadata, errors = _metadata(text)
    if errors or not metadata:
        raise ValueError("working snapshot requires valid YAML-style metadata")
    rendered = text
    for key, value in updates.items():
        pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
        if value is None:
            rendered = re.sub(pattern + r"\n?", "", rendered, count=1)
        elif re.search(pattern, rendered):
            rendered = re.sub(pattern, f"{key}: {value}", rendered, count=1)
        else:
            closing = re.search(r"(?m)^---\s*$", rendered[4:])
            if closing is None:
                raise ValueError("working snapshot metadata fence is malformed")
            insert_at = closing.start() + 4
            rendered = rendered[:insert_at] + f"{key}: {value}\n" + rendered[insert_at:]
    return rendered


def _working_structure_errors(text: str) -> list[str]:
    metadata, errors = _metadata(text)
    sections = _sections(text)
    missing_sections = sorted(WORKING_REQUIRED_SECTIONS - set(sections))
    errors.extend(f"missing section: {name}" for name in missing_sections)
    if metadata.get("status") not in {"working", "confirmed"}:
        errors.append("working snapshot status must be working or confirmed")
    if not SPEC_ID_RE.fullmatch(metadata.get("spec_id", "")):
        errors.append("working snapshot spec_id must match SPEC-####")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", metadata.get("change_set", "")):
        errors.append("working snapshot change_set must be lowercase kebab-case")
    if not WORKING_ID_RE.fullmatch(metadata.get("working_id", "")):
        errors.append("working snapshot working_id is invalid")
    try:
        if int(metadata.get("revision", "0")) < 1:
            raise ValueError
    except ValueError:
        errors.append("working snapshot revision must be a positive integer")
    discussion_ids = [
        match.group(1)
        for match in re.finditer(
            r"(?m)^###\s+(DISC-\d{3})(?::\s+.+)?\s*$",
            sections.get("discussion context", ""),
        )
    ]
    if len(discussion_ids) != len(set(discussion_ids)):
        errors.append("discussion context IDs must be unique")
    for discussion_id in discussion_ids:
        if not DISCUSSION_ID_RE.fullmatch(discussion_id):
            errors.append(f"invalid discussion context ID {discussion_id}")
    for discussion_id, row in _discussion_rows(text).items():
        for label in (
            "Situation",
            "Question",
            "Options and tradeoffs",
            "User answer",
            "Explicit rationale",
            "Resulting impact",
        ):
            if (
                re.search(
                    rf"(?im)^-\s+\*\*{re.escape(label)}:\*\*\s*\S",
                    row["content"],
                )
                is None
            ):
                errors.append(f"{discussion_id} missing discussion field {label}")
        impact = re.search(
            r"(?im)^-\s+\*\*Resulting impact:\*\*\s*(.+)$",
            row["content"],
        )
        affected_ids = re.findall(
            r"\b(?:REQ|DEC|AC)-\d{3}\b", impact.group(1) if impact else ""
        )
        known_ids = set(_snapshot_rows(text))
        if not affected_ids:
            errors.append(
                f"{discussion_id} resulting impact must link an affected REQ/DEC/AC ID"
            )
        for affected_id in affected_ids:
            if affected_id not in known_ids:
                errors.append(
                    f"{discussion_id} links unknown affected ID {affected_id}"
                )
    forbidden_patterns = (
        (r"(?im)^#{1,6}\s+(?:full\s+)?transcript\b", "full transcript"),
        (r"(?i)<(?:thinking|reasoning)>", "hidden reasoning"),
        (
            r"(?i)\b(?:chain[ -]of[ -]thought|hidden reasoning|internal reasoning)\b",
            "hidden reasoning",
        ),
    )
    for pattern, label in forbidden_patterns:
        if re.search(pattern, text):
            errors.append(f"working snapshot contains forbidden {label}")
    if re.search(r"(?im)^\s*(?:user|human)\s*:", text) and re.search(
        r"(?im)^\s*(?:assistant|ai)\s*:", text
    ):
        errors.append("working snapshot contains forbidden full transcript")
    if _redact_sensitive_content(text) != text:
        errors.append("working snapshot contains unredacted sensitive data")
    return errors


def _redact_sensitive_content(text: str) -> str:
    """Redact bounded credential and personal-data patterns in a working snapshot."""
    text = re.sub(
        r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*\b",
        f"Bearer {REDACTION_MARKERS['credential']}",
        text,
    )
    text = re.sub(
        r"(?i)\b(password|passwd|api[_ -]?key|access[_ -]?token|client[_ -]?secret|private[_ -]?key|authorization|secret)\s*([:=])\s*(?!\[REDACTED:)[^\s`,;]+",
        lambda match: (
            f"{match.group(1)}{match.group(2)}{REDACTION_MARKERS['credential']}"
        ),
        text,
    )
    text = re.sub(
        r"(?is)-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----",
        REDACTION_MARKERS["credential"],
        text,
    )
    text = re.sub(
        r"\bsk-[A-Za-z0-9_-]{12,}\b",
        REDACTION_MARKERS["credential"],
        text,
    )
    text = re.sub(
        r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])",
        REDACTION_MARKERS["personal"],
        text,
    )
    text = re.sub(
        r"(?<![\w-])\+?(?:\d[\s().-]?){8,19}\d(?![\w-])",
        REDACTION_MARKERS["personal"],
        text,
    )
    return text


def _snapshot_rows(text: str) -> dict[str, dict[str, str]]:
    sections = _sections(text)
    rows: dict[str, dict[str, str]] = {}
    for section_name in ("requirements", "decisions", "acceptance criteria"):
        for row in _table(sections.get(section_name, "")):
            item_id = _field(row, "ID")
            if item_id:
                rows[item_id] = {
                    key.strip().casefold(): value.strip() for key, value in row.items()
                }
    return rows


def _discussion_rows(text: str) -> dict[str, dict[str, str]]:
    section = _sections(text).get("discussion context", "")
    matches = list(re.finditer(r"(?m)^###\s+(DISC-\d{3})(?::\s+(.+?))?\s*$", section))
    rows: dict[str, dict[str, str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        rows[match.group(1)] = {
            "title": (match.group(2) or "").strip(),
            "content": section[match.end() : end].strip(),
        }
    return rows


def _snapshot_consistency(
    previous_text: str,
    current_text: str,
) -> dict[str, Any]:
    previous_rows = {**_snapshot_rows(previous_text), **_discussion_rows(previous_text)}
    current_rows = {**_snapshot_rows(current_text), **_discussion_rows(current_text)}
    previous_ids = set(previous_rows)
    current_ids = set(current_rows)
    delta = {
        "added_ids": sorted(current_ids - previous_ids),
        "changed_ids": sorted(
            item_id
            for item_id in current_ids & previous_ids
            if current_rows[item_id] != previous_rows[item_id]
        ),
        "removed_ids": sorted(previous_ids - current_ids),
    }
    sections = _sections(current_text)
    relationships = [
        {
            "source": _field(row, "Source"),
            "relation": _field(row, "Relation"),
            "target": _field(row, "Target"),
        }
        for row in _table(sections.get("relationships", ""))
    ]
    conflicts = [
        {"source": row["source"], "target": row["target"]}
        for row in relationships
        if row["relation"] == "conflicts_with"
    ]
    open_section = sections.get("open decisions", "")
    if _open_decisions_are_empty(open_section):
        open_decisions: list[str] = []
    else:
        open_decisions = [
            re.sub(r"^\s*(?:[-*+]|\d+[.)])\s*", "", line).strip()
            for line in open_section.splitlines()
            if line.strip()
        ]
    try:
        question = pending_decision(current_text)
        if question:
            open_decisions.append(f"{question['id']}@{question['version']}")
    except (ValueError, TypeError) as error:
        open_decisions.append(str(error))
    return {
        "verdict": "BLOCKED" if conflicts or open_decisions else "PASS",
        "delta": delta,
        "relationships": relationships,
        "conflicts": conflicts,
        "open_decisions": open_decisions,
    }


def _confirmed_decision_replacement_errors(
    previous_text: str,
    current_text: str,
) -> list[str]:
    previous = {
        item_id: row
        for item_id, row in _snapshot_rows(previous_text).items()
        if item_id.startswith("DEC-")
    }
    current = {
        item_id: row
        for item_id, row in _snapshot_rows(current_text).items()
        if item_id.startswith("DEC-")
    }
    replaced = sorted(
        item_id
        for item_id, row in previous.items()
        if item_id not in current or current[item_id] != row
    )
    return [
        (
            f"{item_id} is confirmed history; preserve it and add a new DEC "
            "with an explicit supersedes relationship"
        )
        for item_id in replaced
    ]


def _working_paths(project_root: Path, working_id: str) -> tuple[Path, Path]:
    matches = []
    for path in (project_root / "specs").glob("SPEC-*.md"):
        metadata, _ = _metadata(path.read_text(encoding="utf-8"))
        if metadata.get("working_id") == working_id:
            matches.append(path)
    if len(matches) > 1:
        raise ValueError("duplicate canonical working identity")
    if matches:
        return matches[0], matches[0]
    root = project_root / WORKING_ROOT
    return (
        root / f"{working_id}{WORKING_SNAPSHOT_SUFFIX}",
        root / f"{working_id}{WORKING_JOURNAL_SUFFIX}",
    )


def _legacy_working_paths(project_root: Path, working_id: str) -> tuple[Path, Path]:
    bundle = project_root / LEGACY_WORKING_ROOT / working_id
    return bundle / LEGACY_WORKING_SNAPSHOT, bundle / LEGACY_WORKING_JOURNAL


def _journal_event_hash(event: dict[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_hash"}
    return hashlib.sha256(_normalized_json(payload).encode("utf-8")).hexdigest()


def _read_journal(path: Path) -> tuple[list[dict[str, Any]], str]:
    if not path.is_file():
        return [], "unavailable"
    events: list[dict[str, Any]] = []
    previous_hash: str | None = None
    try:
        raw = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            if "\n<!-- spec-audit:start -->" not in raw:
                return [], "unavailable"
            audit = raw.split("\n<!-- spec-audit:start -->", 1)[1]
            match = re.search(r"(?s)```jsonl\n(.*?)\n```", audit)
            if not match or not audit.rstrip().endswith("<!-- spec-audit:end -->"):
                return [], "unavailable"
            raw = match.group(1)
        for raw_line in raw.splitlines():
            if not raw_line.strip():
                continue
            event = json.loads(raw_line)
            if event.get("previous_event_hash") != previous_hash:
                return events, "unavailable"
            if event.get("event_hash") != _journal_event_hash(event):
                return events, "unavailable"
            events.append(event)
            previous_hash = event["event_hash"]
    except (OSError, ValueError, TypeError):
        return events, "unavailable"
    return events, "continuous" if events else "unavailable"


def _append_journal_event(
    path: Path,
    *,
    event_type: str,
    working_id: str,
    revision: int,
    previous_snapshot_hash: str | None,
    snapshot_hash: str,
    continuity: str,
    delta: dict[str, Any] | None = None,
    relationships: list[dict[str, Any]] | None = None,
    conflicts: list[dict[str, Any]] | None = None,
    open_decisions: list[str] | None = None,
    verdict: str = "BLOCKED",
    baseline_contract_hash: str | None = None,
) -> dict[str, Any]:
    journal_exists = path.is_file()
    events, journal_continuity = _read_journal(path)
    if journal_continuity != "continuous":
        events = []
        if event_type != "start" or (journal_exists and path.suffix != ".md"):
            continuity = "unavailable"
    elif events:
        continuity = events[-1].get("continuity", continuity)
    event: dict[str, Any] = {
        "event_version": 1,
        "event_type": event_type,
        "working_id": working_id,
        "epoch": events[-1]["epoch"] if events else uuid.uuid4().hex,
        "revision": revision,
        "previous_snapshot_hash": previous_snapshot_hash,
        "snapshot_hash": snapshot_hash,
        "previous_event_hash": events[-1]["event_hash"] if events else None,
        "continuity": continuity,
        "delta": delta
        or {
            "added_ids": [],
            "changed_ids": [],
            "removed_ids": [],
        },
        "affected_ids": sorted(
            set(
                (delta or {}).get("added_ids", [])
                + (delta or {}).get("changed_ids", [])
                + (delta or {}).get("removed_ids", [])
            )
        ),
        "relationships": relationships or [],
        "conflicts": conflicts or [],
        "open_decisions": open_decisions or [],
        "verdict": verdict,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    if baseline_contract_hash is not None:
        event["baseline_contract_hash"] = baseline_contract_hash
    event["event_hash"] = _journal_event_hash(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".md":
        body = _split_spec_audit(path.read_text(encoding="utf-8"))[0]
        history = []
        for item in events + [event]:
            discussion = item.get("delta", {}).get("discussion", {})
            summary = discussion.get("summary") or discussion.get("goal")
            if summary:
                history.append(
                    "- "
                    + str(discussion.get("source_ref", "unknown"))
                    + ": "
                    + str(summary).replace("\n", " ")
                )
        audit = (
            "\n<!-- spec-audit:start -->\n## Discussion History\n\n"
            + "\n".join(history)
            + "\n\n### Source and Revision Audit\n\n```jsonl\n"
            + "\n".join(_normalized_json(item) for item in events + [event])
            + "\n```\n<!-- spec-audit:end -->\n"
        )
        _atomic_write(path, body + audit)
    else:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(_normalized_json(event) + "\n")
    return event


def _contract_hash(text: str) -> str:
    text = _split_spec_audit(text)[0]
    for name in (
        "Current Specification",
        "Decision History",
        "Pending Discussion",
        "Completeness Gaps",
    ):
        text = re.sub(r"(?ms)^## " + re.escape(name) + r"\n.*?(?=^## |\Z)", "", text)
    rendered = _replace_metadata(
        text,
        revision=1,
        status="confirmed",
        working_id=None,
        task_ref=None,
        branch_ref=None,
    )
    sections = _sections(rendered)
    revision_history = sections.get("revision history")
    if revision_history is not None:
        heading = re.search(r"(?m)^##\s+Revision History\s*$", rendered)
        if heading:
            next_section = re.search(r"(?m)^##\s+", rendered[heading.end() :])
            tail = (
                rendered[heading.end() + next_section.start() :] if next_section else ""
            )
            rendered = rendered[: heading.end()] + "\n" + tail
    return _sha256_text(rendered.strip() + "\n")


def _working_reference(
    project_root: Path,
    snapshot_path: Path,
    journal_path: Path,
) -> dict[str, Any]:
    text = snapshot_path.read_text(encoding="utf-8")
    metadata, _ = _metadata(text)
    events, continuity = _read_journal(journal_path)
    snapshot_hash = _snapshot_hash(text)
    if (
        not events
        or events[-1].get("snapshot_hash") != snapshot_hash
        or events[-1].get("continuity") == "unavailable"
    ):
        continuity = "unavailable"
    planning = _acceptance_planning(project_root, text)
    pending_changes = set()
    for event in events:
        pending_changes.update(event.get("delta", {}).get("acceptance_changes", []))
    mapping_path = project_root / planning.get("path", "validation/missing.json")
    try:
        mapping = json.loads(mapping_path.read_text(encoding="utf-8")).get(
            "acceptance", {}
        )
    except (OSError, ValueError, TypeError, AttributeError):
        mapping = {}
    pending_changes = {
        key
        for key in pending_changes
        if key in planning.get("criterion_hashes", {})
        and (
            not isinstance(mapping.get(key), dict)
            or mapping[key].get("criterion_sha256") != planning["criterion_hashes"][key]
        )
    }
    if pending_changes:
        planning.update(
            verdict="BLOCKED", execution_ready=False, changed=sorted(pending_changes)
        )
    return {
        "working_id": metadata.get("working_id"),
        "snapshot_path": snapshot_path.relative_to(project_root).as_posix(),
        "journal_path": journal_path.relative_to(project_root).as_posix(),
        "revision": int(metadata["revision"]),
        "snapshot_hash": snapshot_hash,
        "continuity": continuity,
        "status": metadata.get("status"),
        "spec_id": metadata.get("spec_id"),
        "change_set": metadata.get("change_set"),
        "task_ref": metadata.get("task_ref") or None,
        "branch_ref": metadata.get("branch_ref") or None,
        "validation_planning": planning,
        "confirmed_history": metadata.get("status") == "confirmed"
        or any(
            event.get("event_type") in {"materialize", "reopen"} for event in events
        ),
    }


def _migrate_legacy_bundle(
    project_root: Path,
    legacy_snapshot: Path,
) -> dict[str, Any]:
    legacy_id = legacy_snapshot.parent.name
    snapshot_relative = legacy_snapshot.relative_to(project_root).as_posix()

    def failure(*errors: str) -> dict[str, Any]:
        return {
            "state": "invalid",
            "working_id": legacy_id,
            "logical_working_id": legacy_id.replace("WSP-", "WORKING-SPEC-", 1),
            "snapshot_path": snapshot_relative,
            "errors": [error for error in errors if error],
        }

    if not LEGACY_WORKING_ID_RE.fullmatch(legacy_id):
        return failure("legacy working ID is invalid")
    legacy_journal = legacy_snapshot.with_name(LEGACY_WORKING_JOURNAL)
    source_snapshot_bytes = legacy_snapshot.read_bytes()
    source_journal_bytes = (
        legacy_journal.read_bytes() if legacy_journal.is_file() else None
    )
    source_text = legacy_snapshot.read_text(encoding="utf-8")
    metadata, metadata_errors = _metadata(source_text)
    if metadata_errors or metadata.get("working_id") != legacy_id:
        return failure(
            *metadata_errors,
            "legacy snapshot ID does not match its bundle directory",
        )
    new_id = legacy_id.replace("WSP-", "WORKING-SPEC-", 1)
    destination_snapshot, destination_journal = _working_paths(project_root, new_id)
    if destination_snapshot.exists() or destination_journal.exists():
        return failure("legacy migration destination collision")
    rendered = _replace_metadata(source_text, working_id=new_id)
    if "discussion context" not in _sections(rendered):
        rendered = re.sub(
            r"(?m)^##\s+Acceptance Criteria\s*$",
            "## Discussion Context\n\nNone.\n\n## Acceptance Criteria",
            rendered,
            count=1,
        )
    errors = _working_structure_errors(rendered)
    if errors:
        return failure(*errors)
    events, continuity = _read_journal(legacy_journal)
    if legacy_journal.is_file() and continuity != "continuous":
        return failure("legacy journal chain is invalid")
    source_snapshot_hash = _snapshot_hash(source_text)
    if events and events[-1].get("snapshot_hash") != source_snapshot_hash:
        return failure("legacy journal snapshot hash is stale")
    rewritten_events: list[dict[str, Any]] = []
    previous_event_hash: str | None = None
    snapshot_hash = _snapshot_hash(rendered)
    for index, source_event in enumerate(events):
        event = {
            key: value for key, value in source_event.items() if key != "event_hash"
        }
        event["working_id"] = new_id
        event["previous_event_hash"] = previous_event_hash
        if index == len(events) - 1:
            event["snapshot_hash"] = snapshot_hash
        event["event_hash"] = _journal_event_hash(event)
        rewritten_events.append(event)
        previous_event_hash = event["event_hash"]
    journal_text = "".join(_normalized_json(event) + "\n" for event in rewritten_events)
    destination_snapshot.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    temporary_snapshot = destination_snapshot.with_name(
        f".{destination_snapshot.name}.{token}.tmp"
    )
    temporary_journal = destination_journal.with_name(
        f".{destination_journal.name}.{token}.tmp"
    )
    try:
        temporary_snapshot.write_text(rendered, encoding="utf-8", newline="\n")
        temporary_journal.write_text(journal_text, encoding="utf-8", newline="\n")
        migrated_events, migrated_continuity = _read_journal(temporary_journal)
        if (
            _working_structure_errors(temporary_snapshot.read_text(encoding="utf-8"))
            or (rewritten_events and migrated_continuity != "continuous")
            or (
                migrated_events
                and migrated_events[-1].get("snapshot_hash") != snapshot_hash
            )
        ):
            raise ValueError("migrated working specification verification failed")
        os.replace(temporary_journal, destination_journal)
        try:
            os.replace(temporary_snapshot, destination_snapshot)
        except OSError:
            destination_journal.unlink(missing_ok=True)
            raise
        if _working_structure_errors(
            destination_snapshot.read_text(encoding="utf-8")
        ) or _read_journal(destination_journal)[1] != (
            "continuous" if rewritten_events else "unavailable"
        ):
            raise ValueError("published working specification verification failed")
        legacy_snapshot.unlink()
        if legacy_journal.exists():
            legacy_journal.unlink()
        legacy_snapshot.parent.rmdir()
    except (OSError, ValueError) as error:
        destination_snapshot.unlink(missing_ok=True)
        destination_journal.unlink(missing_ok=True)
        legacy_snapshot.parent.mkdir(parents=True, exist_ok=True)
        legacy_snapshot.write_bytes(source_snapshot_bytes)
        if source_journal_bytes is not None:
            legacy_journal.write_bytes(source_journal_bytes)
        return failure(str(error))
    finally:
        temporary_snapshot.unlink(missing_ok=True)
        temporary_journal.unlink(missing_ok=True)
    return _working_reference(project_root, destination_snapshot, destination_journal)


def _migrate_flat_bundle(
    project_root: Path, working_id: str, notes: list[str] | None = None
) -> dict:
    """Validate and archive a legacy pair only after the canonical audit verifies."""
    if not WORKING_ID_RE.fullmatch(working_id):
        return {"verdict": "BLOCKED", "reason": "invalid working ID"}
    snapshot = project_root / WORKING_ROOT / (working_id + WORKING_SNAPSHOT_SUFFIX)
    journal = project_root / WORKING_ROOT / (working_id + WORKING_JOURNAL_SUFFIX)
    destination = None
    original = None
    moved = []
    wrote = False
    try:
        if not snapshot.exists() and not journal.exists():
            resolved = resolve_working_bundle(project_root, reference=working_id)
            if resolved["state"] == "working":
                return {
                    "verdict": "PASS",
                    "working_spec": resolved["working_spec"],
                    "migrated": False,
                }
        for path in (snapshot, journal):
            if not path.is_file() or path.is_symlink() or path.stat().st_nlink != 1:
                raise ValueError(
                    "legacy snapshot and journal must both be ordinary files"
                )
        text = snapshot.read_text(encoding="utf-8")
        errors = _working_structure_errors(text)
        ref = _working_reference(project_root, snapshot, journal)
        if (
            errors
            or ref["working_id"] != working_id
            or ref["continuity"] != "continuous"
        ):
            raise ValueError(
                "legacy identity, structure or source continuity is invalid"
            )
        if ref["status"] == "implemented":
            raise ValueError("implemented specifications are immutable")
        spec_id = (
            _next_spec_id(project_root)
            if ref["spec_id"] == "SPEC-0000"
            else ref["spec_id"]
        )
        destination = project_root / "specs" / f"{spec_id}-{ref['change_set']}.md"
        if destination.exists():
            if destination.is_symlink() or destination.stat().st_nlink != 1:
                raise ValueError("canonical destination is redirected or shared")
            original = destination.read_text(encoding="utf-8")
            metadata, _ = _metadata(original)
            if (
                metadata.get("status") == "implemented"
                or metadata.get("revision") != str(ref["revision"])
                or _contract_hash(original) != _contract_hash(text)
            ):
                raise ValueError(
                    "canonical and legacy versions conflict; reconcile before migration"
                )
        legacy_notes = []
        for relative in notes or []:
            path = project_root / relative
            if (
                not path.resolve().is_relative_to(project_root.resolve())
                or path.is_symlink()
            ):
                raise ValueError("legacy note must stay inside the project")
            content = path.read_text(encoding="utf-8")
            if _redact_sensitive_content(content) != content:
                raise ValueError("redact sensitive legacy notes before migration")
            legacy_notes.append(
                {"path": relative, "sha256": _sha256_text(content), "content": content}
            )
        events, _ = _read_journal(journal)
        rendered = _refresh_discussion_views(
            _replace_metadata(text, spec_id=spec_id), project_root
        )
        audit = (
            "\n<!-- spec-audit:start -->\n## Discussion History\n\n"
            "Legacy source events preserved below.\n\n### Source and Revision Audit\n\n```jsonl\n"
            + "\n".join(_normalized_json(event) for event in events)
            + "\n```\n<!-- spec-audit:end -->\n"
        )
        _atomic_write(destination, rendered + audit, preserve_audit=False)
        wrote = True
        _append_journal_event(
            destination,
            event_type="migration",
            working_id=working_id,
            revision=ref["revision"],
            previous_snapshot_hash=ref["snapshot_hash"],
            snapshot_hash=_snapshot_hash(rendered),
            continuity="continuous",
            verdict="PASS",
            delta={
                "added_ids": [],
                "changed_ids": [],
                "removed_ids": [],
                "legacy_snapshot": snapshot.relative_to(project_root).as_posix(),
                "legacy_journal": journal.relative_to(project_root).as_posix(),
                "legacy_notes": legacy_notes,
            },
        )
        migrated = _working_reference(project_root, destination, destination)
        if migrated["continuity"] != "continuous":
            raise ValueError("canonical migration verification failed")
        for path in (snapshot, journal):
            archive = path.with_name(path.name + ".migrated")
            if archive.exists():
                raise ValueError(
                    "legacy archive already exists; inspect interrupted migration"
                )
            path.rename(archive)
            moved.append((path, archive))
        return {
            "verdict": "PASS",
            "working_spec": migrated,
            "migrated": True,
            "authorization_retained": False,
            "repair_budget_changed": False,
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        for path, archive in reversed(moved):
            archive.rename(path)
        if wrote and destination is not None:
            if original is None:
                destination.unlink(missing_ok=True)
            else:
                _atomic_write(destination, original, preserve_audit=False)
        return {"verdict": "BLOCKED", "reason": str(exc), "originals_preserved": True}


def _working_candidates(project_root: Path) -> list[dict[str, Any]]:
    root = project_root / WORKING_ROOT
    candidates: list[dict[str, Any]] = []
    canonical_ids = set()
    for path in sorted((project_root / "specs").glob("SPEC-*.md")):
        text = path.read_text(encoding="utf-8")
        metadata, _ = _metadata(text)
        if not metadata.get("working_id") or metadata.get("status") == "implemented":
            continue
        canonical_ids.add(metadata["working_id"])
        errors = _working_structure_errors(text)
        if errors:
            candidates.append(
                {
                    "state": "invalid",
                    "working_id": metadata["working_id"],
                    "snapshot_path": path.relative_to(project_root).as_posix(),
                    "errors": errors,
                }
            )
        else:
            candidates.append(_working_reference(project_root, path, path))
    legacy_root = project_root / LEGACY_WORKING_ROOT
    if legacy_root.is_dir():
        for legacy_snapshot in sorted(legacy_root.glob(f"*/{LEGACY_WORKING_SNAPSHOT}")):
            migrated = _migrate_legacy_bundle(project_root, legacy_snapshot)
            if migrated.get("state") == "invalid":
                candidates.append(migrated)
    if not root.is_dir():
        return candidates
    blocked_logical_ids = {
        row.get("logical_working_id")
        for row in candidates
        if row.get("state") == "invalid"
    }
    for snapshot in sorted(root.glob(f"WORKING-SPEC-*{WORKING_SNAPSHOT_SUFFIX}")):
        if snapshot.name.endswith(WORKING_JOURNAL_SUFFIX):
            continue
        snapshot_text = snapshot.read_text(encoding="utf-8")
        errors = _working_structure_errors(snapshot_text)
        metadata, _ = _metadata(snapshot_text)
        expected_id = snapshot.name[: -len(WORKING_SNAPSHOT_SUFFIX)]
        if expected_id in canonical_ids:
            candidates.append(
                {
                    "state": "invalid",
                    "working_id": expected_id,
                    "snapshot_path": snapshot.relative_to(project_root).as_posix(),
                    "errors": [
                        "canonical and legacy working records coexist; verify migration before resuming"
                    ],
                }
            )
            continue
        if metadata.get("working_id") != expected_id:
            errors.append("working snapshot ID does not match its filename")
        journal = snapshot.with_name(f"{expected_id}{WORKING_JOURNAL_SUFFIX}")
        if expected_id in blocked_logical_ids:
            continue
        if errors:
            candidates.append(
                {
                    "state": "invalid",
                    "working_id": expected_id,
                    "snapshot_path": snapshot.relative_to(project_root).as_posix(),
                    "errors": errors,
                }
            )
        else:
            candidates.append(_working_reference(project_root, snapshot, journal))
    return candidates


def resolve_working_bundle(
    project_root: Path,
    *,
    reference: str | None = None,
    task_ref: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Resolve a working bundle explicitly, by task/branch evidence, then uniquely."""
    candidates = _working_candidates(project_root)
    invalid = [row for row in candidates if row.get("state") == "invalid"]
    valid = [row for row in candidates if row.get("state") != "invalid"]

    def result(
        state: str, matches: list[dict[str, Any]], reason: str
    ) -> dict[str, Any]:
        return {
            "state": state,
            "working_spec": matches[0] if len(matches) == 1 else None,
            "candidates": [
                row.get("snapshot_path") or row.get("working_id") for row in matches
            ],
            "reason": reason,
        }

    if reference:
        original = reference.replace("\\", "/").casefold()
        normalized = original
        if normalized.startswith("wsp-"):
            normalized = normalized.replace("wsp-", "working-spec-", 1)
        matches = [
            row
            for row in valid
            if str(row.get("working_id", "")).casefold() == normalized
            or str(row.get("snapshot_path", "")).casefold() == normalized
        ]
        invalid_matches = [
            row
            for row in invalid
            if str(row.get("working_id", "")).casefold() in {original, normalized}
            or str(row.get("logical_working_id", "")).casefold()
            in {original, normalized}
            or str(row.get("snapshot_path", "")).casefold() in {original, normalized}
        ]
        if invalid_matches:
            errors = sorted(
                {error for row in invalid_matches for error in row.get("errors", [])}
            )
            return result(
                "invalid",
                invalid_matches,
                "; ".join(errors) or "working specification is malformed",
            )
        return result(
            "working" if len(matches) == 1 else "invalid",
            matches,
            "explicit working reference"
            if matches
            else "explicit working reference does not exist",
        )
    if task_ref:
        matches = [row for row in valid if row.get("task_ref") == task_ref]
        if matches:
            return result(
                "working" if len(matches) == 1 else "ambiguous",
                matches,
                "task reference",
            )
    if branch:
        matches = [row for row in valid if row.get("branch_ref") == branch]
        if matches:
            return result(
                "working" if len(matches) == 1 else "ambiguous",
                matches,
                "branch reference",
            )
    if len(valid) == 1:
        return result("working", valid, "unique working fallback")
    if len(valid) > 1:
        return result(
            "ambiguous",
            valid,
            "multiple working specifications require an explicit reference",
        )
    if invalid:
        return result("invalid", invalid, "working specification is malformed")
    return result("absent", [], "no working specification exists")


@contextmanager
def project_state_lock(root: Path, key: str, timeout: float = 30.0):
    """Lock a stable inode briefly; the OS releases ownership on process exit."""
    directory = root.resolve() / "spec-governance"
    if directory.is_symlink() or directory.resolve() != directory:
        raise ValueError("governance directory must not be redirected")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (".state-" + hashlib.sha256(key.encode()).hexdigest() + ".lock")
    if path.is_symlink():
        raise ValueError("state lock must not be redirected")
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN}:
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"shared state remained locked for {timeout:g}s; holder unknown; preserve pending edits and reread before retrying"
                    )
                time.sleep(0.01)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _serialize_spec_creation(function):
    @wraps(function)
    def create(project_root, *args, **kwargs):
        with project_state_lock(project_root, "spec-id-allocation"):
            return function(project_root, *args, **kwargs)

    return create


@_serialize_spec_creation
def start_working_bundle(
    project_root: Path,
    slug: str,
    text: str,
    *,
    working_id: str | None = None,
    task_ref: str | None = None,
    branch: str | None = None,
    preserve_spec_identity: bool = False,
    baseline_contract_hash: str | None = None,
    baseline_file_hash: str | None = None,
) -> dict[str, Any]:
    """Create one authoritative Markdown snapshot and normalized journal epoch."""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        return {"verdict": "BLOCKED", "reason": "invalid change-set slug"}
    discovered = _working_candidates(project_root)
    invalid = [row for row in discovered if row.get("state") == "invalid"]
    if invalid:
        return {
            "verdict": "BLOCKED",
            "reason": "working specification discovery or migration failed",
            "errors": sorted(
                {error for row in invalid for error in row.get("errors", [])}
            ),
        }
    matching = [row for row in discovered if row.get("change_set") == slug]
    if len(matching) == 1:
        with project_state_lock(project_root, "spec:" + matching[0]["working_id"]):
            if preserve_spec_identity:
                ref = _working_reference(
                    project_root,
                    *_working_paths(project_root, matching[0]["working_id"]),
                )
                snapshot_path, journal_path = _working_paths(
                    project_root, ref["working_id"]
                )
                previous = snapshot_path.read_text(encoding="utf-8")
                if (
                    baseline_file_hash is not None
                    and _sha256_text(previous) != baseline_file_hash
                ):
                    return {
                        "verdict": "BLOCKED",
                        "reason": "SPEC changed during reopen; reread current file",
                        "pending_edits_preserved": True,
                    }
                metadata, errors = _metadata(text)
                if (
                    errors
                    or ref["status"] != "confirmed"
                    or ref["spec_id"] != metadata.get("spec_id")
                    or _contract_hash(previous) != baseline_contract_hash
                ):
                    return {
                        "verdict": "BLOCKED",
                        "reason": "existing working bundle does not match the reopen baseline",
                    }
                rendered = _replace_metadata(
                    text,
                    working_id=ref["working_id"],
                    task_ref=task_ref if task_ref is not None else ref.get("task_ref"),
                    branch_ref=branch if branch is not None else ref.get("branch_ref"),
                )
                errors = _working_structure_errors(rendered)
                if errors:
                    return {
                        "verdict": "BLOCKED",
                        "reason": "invalid reopened snapshot",
                        "errors": errors,
                    }
                _, continuity = _read_journal(journal_path)
                _atomic_write(snapshot_path, rendered)
                _append_journal_event(
                    journal_path,
                    event_type="reopen",
                    working_id=ref["working_id"],
                    revision=int(metadata["revision"]),
                    previous_snapshot_hash=_snapshot_hash(previous),
                    snapshot_hash=_snapshot_hash(rendered),
                    continuity=continuity,
                    baseline_contract_hash=baseline_contract_hash,
                )
                return {
                    "verdict": "PASS",
                    "working_spec": _working_reference(
                        project_root, snapshot_path, journal_path
                    ),
                    "created": False,
                }
            return {"verdict": "PASS", "working_spec": matching[0], "created": False}
    if len(matching) > 1:
        return {
            "verdict": "BLOCKED",
            "reason": "multiple working specifications match change set",
        }
    working_id = working_id or f"WORKING-SPEC-{uuid.uuid4().hex[:12]}-{slug}"
    if not WORKING_ID_RE.fullmatch(working_id):
        return {"verdict": "BLOCKED", "reason": "invalid working ID"}
    snapshot_path, journal_path = _working_paths(project_root, working_id)
    if snapshot_path.exists():
        reference = _working_reference(project_root, snapshot_path, journal_path)
        return {"verdict": "PASS", "working_spec": reference, "created": False}
    metadata, metadata_errors = _metadata(text)
    if metadata_errors:
        return {
            "verdict": "BLOCKED",
            "reason": "invalid working snapshot",
            "errors": metadata_errors,
        }
    spec_id = (
        metadata.get("spec_id")
        if preserve_spec_identity
        else _next_spec_id(project_root)
    )
    snapshot_path = project_root / "specs" / f"{spec_id}-{slug}.md"
    journal_path = snapshot_path
    if snapshot_path.exists() and not preserve_spec_identity:
        return {"verdict": "BLOCKED", "reason": "canonical destination already exists"}
    rendered = _redact_sensitive_content(
        _replace_metadata(
            text,
            spec_id=spec_id,
            revision=1 if not preserve_spec_identity else metadata.get("revision", "1"),
            status=metadata.get("status", "working")
            if preserve_spec_identity
            else "working",
            change_set=slug,
            working_id=working_id,
            task_ref=task_ref,
            branch_ref=branch,
        )
    )
    rendered = _refresh_discussion_views(rendered, project_root)
    errors = _working_structure_errors(rendered)
    if errors:
        return {
            "verdict": "BLOCKED",
            "reason": "invalid working snapshot",
            "errors": errors,
        }
    _atomic_write(snapshot_path, rendered)
    snapshot_hash = _snapshot_hash(rendered)
    initial_consistency = _snapshot_consistency(rendered, rendered)
    _append_journal_event(
        journal_path,
        event_type="start",
        working_id=working_id,
        revision=int(_metadata(rendered)[0]["revision"]),
        previous_snapshot_hash=None,
        snapshot_hash=snapshot_hash,
        continuity="continuous",
        relationships=initial_consistency["relationships"],
        conflicts=initial_consistency["conflicts"],
        open_decisions=initial_consistency["open_decisions"],
        verdict=initial_consistency["verdict"],
        baseline_contract_hash=baseline_contract_hash,
    )
    return {
        "verdict": "PASS",
        "working_spec": _working_reference(project_root, snapshot_path, journal_path),
        "created": True,
    }


def _merge_spec_edits(base: str, desired: str, current: str) -> str:
    """Integrate disjoint line edits; conflicts retain both original inputs."""
    lines = base.splitlines(keepends=True)

    def edits(value):
        changed = value.splitlines(keepends=True)
        return [
            (a, b, changed[c:d])
            for op, a, b, c, d in difflib.SequenceMatcher(
                None, lines, changed, autojunk=False
            ).get_opcodes()
            if op != "equal"
        ]

    ours, theirs = edits(desired), edits(current)
    combined = list(theirs)
    for edit in ours:
        if edit in theirs:
            continue
        a, b, _ = edit
        for c, d, _ in theirs:
            if (
                max(a, c) < min(b, d)
                or (a == b and c <= a <= d)
                or (c == d and a <= c <= b)
            ):
                raise ValueError(
                    "conflicting SPEC edits; preserve both changes and reconcile the decision"
                )
        combined.append(edit)
    for a, b, replacement in sorted(
        combined, key=lambda item: (item[0], item[1]), reverse=True
    ):
        lines[a:b] = replacement
    return "".join(lines)


def _serialize_spec_update(function):
    @wraps(function)
    def update(project_root, working_id, *args, **kwargs):
        try:
            resolved = resolve_working_bundle(project_root, reference=working_id)
            identity = (resolved.get("working_spec") or {}).get(
                "working_id", working_id
            )
            with project_state_lock(project_root, "spec:" + identity):
                return function(project_root, working_id, *args, **kwargs)
        except TimeoutError as error:
            return {
                "verdict": "BLOCKED",
                "reason": str(error),
                "pending_edits_preserved": True,
            }

    return update


@_serialize_spec_update
def reconcile_working_bundle(
    project_root: Path,
    working_id: str,
    next_snapshot: str,
    normalized_delta: dict[str, Any],
    *,
    expected_revision: int,
    expected_hash: str,
    question_id: str | None = None,
    question_version: int | None = None,
    answer: str | None = None,
    question_update: dict[str, Any] | None = None,
    validation_assessor=None,
    base_snapshot: str | None = None,
) -> dict[str, Any]:
    """Persist a complete next snapshot with optimistic revision/hash checks."""
    if not (
        WORKING_ID_RE.fullmatch(working_id)
        or LEGACY_WORKING_ID_RE.fullmatch(working_id)
    ):
        return {"verdict": "BLOCKED", "reason": "invalid working ID"}
    resolved = resolve_working_bundle(project_root, reference=working_id)
    if resolved["state"] != "working":
        return {"verdict": "BLOCKED", "reason": resolved["reason"]}
    reference = resolved["working_spec"]
    working_id = reference["working_id"]
    snapshot_path = project_root / reference["snapshot_path"]
    journal_path = project_root / reference["journal_path"]
    current = snapshot_path.read_text(encoding="utf-8")
    metadata, _ = _metadata(current)
    current_hash = _snapshot_hash(current)
    current_revision = int(metadata.get("revision", "0"))
    if (
        expected_revision != current_revision or expected_hash != current_hash
    ) and base_snapshot is not None:
        if (
            _snapshot_hash(base_snapshot) != expected_hash
            or int(_metadata(base_snapshot)[0].get("revision", 0)) != expected_revision
        ):
            return {
                "verdict": "BLOCKED",
                "reason": "unverified merge baseline",
                "pending_edits_preserved": True,
            }
        if (
            metadata.get("status") != "working"
            or question_update is not None
            or answer is not None
        ):
            return {
                "verdict": "BLOCKED",
                "reason": "reread current contract/question before merging",
                "pending_edits_preserved": True,
            }
        try:
            next_snapshot = _merge_spec_edits(base_snapshot, next_snapshot, current)
        except ValueError as error:
            return {
                "verdict": "BLOCKED",
                "reason": str(error),
                "pending_edits_preserved": True,
            }
        expected_revision, expected_hash = current_revision, current_hash
    if expected_revision != current_revision or expected_hash != current_hash:
        return {
            "pending_edits_preserved": True,
            "next_action": "reread-and-integrate",
            "verdict": "BLOCKED",
            "reason": "stale working specification",
            "working_spec": _working_reference(
                project_root, snapshot_path, journal_path
            ),
        }
    # The caller owns proposed body edits, never the current audit journal.
    # Audit-only appends deliberately retain the snapshot hash and revision.
    next_snapshot = _split_spec_audit(next_snapshot)[0] + _split_spec_audit(current)[1]
    try:
        pending = pending_decision(current)
        next_pending = pending_decision(next_snapshot)
        current_record = _question_record(current)
        next_record = _question_record(next_snapshot)
        if question_update is None and current_record != next_record:
            raise ValueError(
                "question history and failed surfaces require an explicit question update"
            )
    except (ValueError, TypeError) as error:
        return {"verdict": "BLOCKED", "reason": str(error)}
    answering = any(
        item is not None for item in (question_id, question_version, answer)
    )
    if not answering and question_update is None and next_snapshot == current:
        return {
            "verdict": "PASS",
            "working_spec": reference,
            "delta": {"added_ids": [], "changed_ids": [], "removed_ids": []},
            "changed": False,
            "open_decisions": _snapshot_consistency(current, current)["open_decisions"],
        }

    if question_update is not None:
        try:
            if answering or next_snapshot != _question_update_snapshot(
                current, question_update, current_revision
            ):
                raise ValueError("question update does not match preserved state")
        except (ValueError, TypeError, KeyError) as error:
            return {"verdict": "BLOCKED", "reason": str(error)}
    if answering:
        if (
            not pending
            or question_id != pending["id"]
            or question_version != pending["version"]
            or not isinstance(answer, str)
            or not answer.strip()
        ):
            return {
                "verdict": "BLOCKED",
                "reason": "missing, stale or duplicate explicit answer",
            }
        if (
            pending["options"]
            and re.fullmatch(r"\d+", answer.strip())
            and not 1 <= int(answer.strip()) <= len(pending["options"])
        ):
            return {
                "verdict": "BLOCKED",
                "reason": "numeric answer is outside current options",
            }
        # Require the supplied synthesis to retain the human answer in a new DISC record.
        before_disc = _discussion_rows(current)
        after_disc = _discussion_rows(next_snapshot)

        def records_answer(row: dict[str, str]) -> bool:
            field = re.search(
                r"(?ms)^-\s+\*\*User answer:\*\*\s*(.*?)(?=^-\s+\*\*|\Z)",
                row["content"],
            )
            return bool(
                field
                and field.group(1).strip().strip("`") == answer.strip()
                and pending["question"] in row["content"]
                and all(option in row["content"] for option in pending["options"])
            )

        if not any(
            records_answer(row)
            for key, row in after_disc.items()
            if key not in before_disc
        ):
            return {
                "verdict": "BLOCKED",
                "reason": "answer must be persisted in a new DISC record",
            }
        next_snapshot = _replace_pending_decision(next_snapshot, None)
    elif pending != next_pending and pending is not None and question_update is None:
        return {
            "verdict": "BLOCKED",
            "reason": "pending question requires an explicit versioned answer",
        }
    rendered = _redact_sensitive_content(
        _replace_metadata(
            next_snapshot,
            spec_id=metadata.get("spec_id"),
            revision=current_revision + 1,
            status="working",
            change_set=metadata.get("change_set"),
            working_id=working_id,
            task_ref=metadata.get("task_ref") or None,
            branch_ref=metadata.get("branch_ref") or None,
        )
    )
    rendered = _refresh_discussion_views(rendered, project_root)
    errors = _working_structure_errors(rendered)
    if errors:
        return {
            "verdict": "BLOCKED",
            "reason": "invalid next working snapshot",
            "errors": errors,
        }
    if metadata.get("spec_id") != "SPEC-0000":
        replacement_errors = _confirmed_decision_replacement_errors(current, rendered)
        if replacement_errors:
            return {
                "verdict": "BLOCKED",
                "reason": "confirmed decisions must be superseded, not rewritten",
                "errors": replacement_errors,
            }
    evidence = assess_spec_evidence_update(
        project_root, rendered, validation_assessor=validation_assessor
    )
    if evidence["verdict"] != "PASS":
        return {
            "verdict": evidence["verdict"],
            "reason": "acceptance evidence is insufficient",
            "validation": evidence,
        }
    consistency = _snapshot_consistency(current, rendered)
    delta = consistency["delta"]
    planning = _acceptance_planning(project_root, rendered, current)
    delta["acceptance_changes"] = planning.get("changed", [])
    relationships = consistency["relationships"]
    conflicts = consistency["conflicts"]
    open_decisions = consistency["open_decisions"]
    verdict = consistency["verdict"]
    _, continuity = _read_journal(journal_path)
    _atomic_write(snapshot_path, rendered)
    snapshot_hash = _snapshot_hash(rendered)
    _append_journal_event(
        journal_path,
        event_type="reconcile",
        working_id=working_id,
        revision=current_revision + 1,
        previous_snapshot_hash=current_hash,
        snapshot_hash=snapshot_hash,
        continuity=continuity,
        delta=delta,
        relationships=relationships,
        conflicts=conflicts,
        open_decisions=open_decisions,
        verdict=verdict,
    )
    return {
        "verdict": verdict,
        "working_spec": _working_reference(project_root, snapshot_path, journal_path),
        "delta": delta,
        "relationships": relationships,
        "conflicts": conflicts,
        "open_decisions": open_decisions,
    }


def _next_spec_id(project_root: Path) -> str:
    numbers: list[int] = []
    for path in (project_root / "specs").glob("SPEC-[0-9][0-9][0-9][0-9]-*.md"):
        match = re.match(r"SPEC-(\d{4})-", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return f"SPEC-{max(numbers, default=0) + 1:04d}"


def _repository_spec_inventory(project_root: Path) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    for path in (project_root / "specs").glob("SPEC-[0-9][0-9][0-9][0-9]-*.md"):
        metadata, _ = _metadata(path.read_text(encoding="utf-8"))
        if SPEC_ID_RE.fullmatch(metadata.get("spec_id", "")):
            result.setdefault(metadata["spec_id"], []).append(path)
    return result


def _repository_spec_ids(project_root: Path) -> set[str]:
    return set(_repository_spec_inventory(project_root))


def _canonical_identity_errors(
    project_root: Path,
    path: Path,
    text: str,
) -> list[str]:
    metadata, _ = _metadata(text)
    spec_id = metadata.get("spec_id", "")
    slug = metadata.get("change_set", "")
    errors: list[str] = []
    if path.parent.name.casefold() != "specs":
        errors.append("canonical spec must be directly under specs/")
    expected_name = f"{spec_id}-{slug}.md"
    if path.name != expected_name:
        errors.append(
            f"canonical filename {path.name} does not match metadata {expected_name}"
        )
    inventory = _repository_spec_inventory(project_root)
    if spec_id and len(inventory.get(spec_id, [])) > 1:
        errors.append(f"duplicate repository spec ID {spec_id}")
    return errors


def _apply_identity_errors(
    assessment: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    if errors:
        assessment["errors"].extend(errors)
        assessment["verdict"] = "BLOCKED"
        assessment["traceability"]["verdict"] = "BLOCKED"
    return assessment


def _append_revision_history(text: str, revision: int, change: str) -> str:
    lines = text.rstrip().splitlines()
    heading = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip().casefold() == "## revision history"
        ),
        None,
    )
    if heading is None:
        return text
    insert_at = len(lines)
    for index in range(heading + 1, len(lines)):
        if lines[index].startswith("## "):
            insert_at = index
            break
    while insert_at > heading + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(
        insert_at,
        f"| {revision} | {date.today().isoformat()} | {change} |",
    )
    return "\n".join(lines) + "\n"


def materialize_spec(
    project_root: Path,
    slug: str,
    text: str,
    *,
    authorized: bool | None = None,
    validation_assessor=None,
) -> dict[str, Any]:
    """Write one decision-complete canonical spec without product authorization."""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        return {
            "verdict": "BLOCKED",
            "reason": "invalid change-set slug",
            "canonical_spec": None,
        }
    spec_id = _next_spec_id(project_root)
    rendered = re.sub(
        r"(?m)^spec_id:\s*SPEC-\d{4}\s*$",
        f"spec_id: {spec_id}",
        text,
        count=1,
    )
    rendered_metadata, _ = _metadata(rendered)
    if rendered_metadata.get("status") != "confirmed":
        return {
            "verdict": "BLOCKED",
            "reason": "materialization requires status confirmed",
            "canonical_spec": None,
        }
    rendered = re.sub(
        r"(?m)^change_set:\s*.*$",
        f"change_set: {slug}",
        rendered,
        count=1,
    )
    assessment = validate_spec_text(
        rendered,
        known_spec_ids=_repository_spec_ids(project_root) | {spec_id},
    )
    if assessment["verdict"] != "PASS":
        return {
            "verdict": "BLOCKED",
            "reason": "canonical spec validation failed",
            "errors": assessment["errors"],
            "canonical_spec": None,
        }
    gaps = acceptance_plan_completeness(project_root, rendered)
    if gaps:
        return {
            "verdict": "BLOCKED",
            "reason": "acceptance plan incomplete",
            "errors": gaps,
        }
    specs_dir = project_root / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    relative = Path("specs") / f"{spec_id}-{slug}.md"
    destination = project_root / relative
    evidence = assess_spec_evidence_update(
        project_root, rendered, validation_assessor=validation_assessor
    )
    if evidence["verdict"] != "PASS":
        return {
            "verdict": evidence["verdict"],
            "reason": "acceptance evidence is insufficient",
            "validation": evidence,
        }
    _atomic_write(destination, rendered)
    reference = assessment["canonical_spec"]
    reference["path"] = relative.as_posix()
    return {
        "verdict": "PASS",
        "canonical_spec": reference,
        "product_execution_authorized": False,
    }


@_serialize_spec_update
def materialize_working_bundle(
    project_root: Path,
    working_id: str,
    *,
    expected_revision: int,
    expected_hash: str,
    validation_assessor=None,
) -> dict[str, Any]:
    """Confirm a decision-complete bundle, creating or updating its canonical spec."""
    if not (
        WORKING_ID_RE.fullmatch(working_id)
        or LEGACY_WORKING_ID_RE.fullmatch(working_id)
    ):
        return {"verdict": "BLOCKED", "reason": "invalid working ID"}
    resolved = resolve_working_bundle(project_root, reference=working_id)
    if resolved["state"] != "working":
        return {"verdict": "BLOCKED", "reason": resolved["reason"]}
    reference = resolved["working_spec"]
    working_id = reference["working_id"]
    snapshot_path = project_root / reference["snapshot_path"]
    journal_path = project_root / reference["journal_path"]
    current = snapshot_path.read_text(encoding="utf-8")
    metadata, _ = _metadata(current)
    current_hash = _snapshot_hash(current)
    current_revision = int(metadata.get("revision", "0"))
    if current_revision != expected_revision or current_hash != expected_hash:
        return {
            "verdict": "BLOCKED",
            "reason": "stale working specification",
            "working_spec": _working_reference(
                project_root, snapshot_path, journal_path
            ),
        }
    rendered = _replace_metadata(
        current,
        status="confirmed",
        working_id=None,
        task_ref=None,
        branch_ref=None,
    )
    spec_id = metadata.get("spec_id", "")
    slug = metadata.get("change_set", "")
    existing = spec_id != "SPEC-0000"
    if not existing:
        spec_id = _next_spec_id(project_root)
        rendered = _replace_metadata(rendered, spec_id=spec_id)
    assessment = validate_spec_text(
        rendered,
        known_spec_ids=_repository_spec_ids(project_root) | {spec_id},
    )
    if assessment["verdict"] != "PASS":
        return {
            "verdict": "BLOCKED",
            "reason": "working specification is not decision-complete",
            "errors": assessment["errors"],
        }
    gaps = acceptance_plan_completeness(project_root, rendered)
    if gaps:
        return {
            "verdict": "BLOCKED",
            "reason": "acceptance plan incomplete",
            "errors": gaps,
        }
    destination = project_root / "specs" / f"{spec_id}-{slug}.md"
    if existing and not destination.is_file():
        return {
            "verdict": "BLOCKED",
            "reason": "reopened canonical specification path is missing",
        }
    if existing:
        existing_metadata, _ = _metadata(destination.read_text(encoding="utf-8"))
        if existing_metadata.get("status") == "implemented":
            return {
                "verdict": "BLOCKED",
                "reason": "implemented specification cannot reopen",
            }
    events, _ = _read_journal(journal_path)
    baseline_hash = next(
        (
            event.get("baseline_contract_hash")
            for event in reversed(events)
            if event.get("baseline_contract_hash")
        ),
        None,
    )
    actual_delta = baseline_hash is not None and baseline_hash != _contract_hash(
        rendered
    )
    evidence = assess_spec_evidence_update(
        project_root, rendered, validation_assessor=validation_assessor
    )
    if evidence["verdict"] != "PASS":
        return {
            "verdict": evidence["verdict"],
            "reason": "acceptance evidence is insufficient",
            "validation": evidence,
        }
    working_rendered = _replace_metadata(
        rendered,
        working_id=working_id,
        task_ref=metadata.get("task_ref") or None,
        branch_ref=metadata.get("branch_ref") or None,
    )
    if destination != snapshot_path:
        _atomic_write(destination, rendered)
    _atomic_write(snapshot_path, working_rendered)
    final_hash = _snapshot_hash(working_rendered)
    _append_journal_event(
        journal_path,
        event_type="materialize",
        working_id=working_id,
        revision=current_revision,
        previous_snapshot_hash=current_hash,
        snapshot_hash=final_hash,
        continuity=_read_journal(journal_path)[1],
        verdict="PASS",
    )
    reference = assessment["canonical_spec"]
    reference["path"] = destination.relative_to(project_root).as_posix()
    return {
        "verdict": "PASS",
        "canonical_spec": reference,
        "working_spec": _working_reference(project_root, snapshot_path, journal_path),
        "actual_contract_delta": actual_delta,
        "authorization_retained": False,
        "product_execution_authorized": False,
    }


def reopen_spec(
    project_root: Path,
    spec_path: Path,
    *,
    expected_revision: int,
    reason: str,
    task_ref: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Reopen a confirmed unimplemented canonical spec before clarification."""
    path = spec_path if spec_path.is_absolute() else project_root / spec_path
    if not path.is_file():
        return {
            "verdict": "BLOCKED",
            "reason": "canonical specification does not exist",
        }
    try:
        relative = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return {
            "verdict": "BLOCKED",
            "reason": "canonical specification is outside the project",
        }
    if relative.parent.as_posix().casefold() != "specs":
        return {
            "verdict": "BLOCKED",
            "reason": "canonical specification must be directly under specs/",
        }
    text = path.read_text(encoding="utf-8")
    metadata, errors = _metadata(text)
    if errors:
        return {
            "verdict": "BLOCKED",
            "reason": "canonical metadata is invalid",
            "errors": errors,
        }
    if metadata.get("status") == "implemented":
        return {
            "verdict": "BLOCKED",
            "reason": "implemented specification cannot reopen",
        }
    if metadata.get("status") != "confirmed":
        return {
            "verdict": "BLOCKED",
            "reason": "only confirmed specifications can reopen",
        }
    identity_errors = _canonical_identity_errors(project_root, path, text)
    if identity_errors:
        return {
            "verdict": "BLOCKED",
            "reason": "canonical identity validation failed",
            "errors": identity_errors,
        }
    revision = int(metadata.get("revision", "0"))
    if revision != expected_revision:
        return {"verdict": "BLOCKED", "reason": "stale canonical specification"}
    baseline_hash = _contract_hash(text)
    reopened = _replace_metadata(text, revision=revision + 1, status="working")
    reopened = _append_revision_history(
        reopened,
        revision + 1,
        f"Reopened before clarification: {reason.strip()}",
    )
    if not metadata.get("working_id"):
        _atomic_write(path, reopened)
    result = start_working_bundle(
        project_root,
        metadata["change_set"],
        reopened,
        task_ref=task_ref,
        branch=branch,
        preserve_spec_identity=True,
        baseline_contract_hash=baseline_hash,
        baseline_file_hash=_sha256_text(text) if metadata.get("working_id") else None,
    )
    if result["verdict"] != "PASS":
        if (
            not metadata.get("working_id")
            and path.read_text(encoding="utf-8") == reopened
        ):
            _atomic_write(path, text)
        return result
    result["canonical_spec"] = {
        "spec_id": metadata["spec_id"],
        "path": path.relative_to(project_root).as_posix(),
        "revision": revision + 1,
        "status": "working",
    }
    result["authorization_suspended"] = True
    return result


def prepare_commit(
    project_root: Path,
    *,
    disposition: str | None = None,
    tracked_paths: list[str] | None = None,
    staged_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Inspect local working state and require an explicit retention disposition."""
    if disposition is not None and disposition not in COMMIT_DISPOSITIONS:
        return {
            "verdict": "BLOCKED",
            "reason": "invalid working bundle disposition",
            "options": sorted(COMMIT_DISPOSITIONS),
        }
    discovered = _working_candidates(project_root)
    invalid = [row for row in discovered if row.get("state") == "invalid"]
    if invalid:
        return {
            "verdict": "BLOCKED",
            "reason": "working specification discovery or migration failed",
            "errors": sorted(
                {error for row in invalid for error in row.get("errors", [])}
            ),
        }
    bundles = sorted(
        row["snapshot_path"] for row in discovered if row.get("snapshot_path")
    )
    if tracked_paths is None or staged_paths is None:
        try:
            tracked = subprocess.run(
                [
                    "git",
                    "-C",
                    str(project_root),
                    "ls-files",
                    "--",
                    WORKING_ROOT.as_posix(),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            staged = subprocess.run(
                [
                    "git",
                    "-C",
                    str(project_root),
                    "diff",
                    "--cached",
                    "--name-only",
                    "--",
                    WORKING_ROOT.as_posix(),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            tracked_paths = [line for line in tracked.stdout.splitlines() if line]
            staged_paths = [line for line in staged.stdout.splitlines() if line]
        except (OSError, subprocess.CalledProcessError) as error:
            return {
                "verdict": "BLOCKED",
                "reason": "Git working bundle evidence unavailable",
                "error": str(error),
            }
    if staged_paths:
        return {
            "verdict": "BLOCKED",
            "reason": "local working bundle is staged",
            "staged_paths": staged_paths,
            "tracked_paths": tracked_paths,
            "options": sorted(COMMIT_DISPOSITIONS),
        }
    if bundles and disposition is None:
        return {
            "verdict": "BLOCKED",
            "reason": "working bundle disposition required before commit",
            "bundles": bundles,
            "tracked_paths": tracked_paths,
            "options": sorted(COMMIT_DISPOSITIONS),
        }
    return {
        "verdict": "PASS",
        "disposition": disposition,
        "bundles": bundles,
        "tracked_paths": tracked_paths,
        "action_performed": False,
    }


def publish_tracker_snapshot(
    spec_path: Path,
    publisher: Callable[[Path, str], Any],
) -> dict[str, Any]:
    """Publish a snapshot without deleting or rewriting local canonical state."""
    snapshot = spec_path.read_text(encoding="utf-8")
    try:
        receipt = publisher(spec_path, snapshot)
    except Exception as error:  # external adapter boundary
        return {
            "verdict": "BLOCKED",
            "reason": "tracker publication pending",
            "error": str(error),
            "path": spec_path.as_posix(),
        }
    return {"verdict": "PASS", "receipt": receipt, "path": spec_path.as_posix()}


def _candidate_record(
    project_root: Path,
    path: Path,
    known_spec_ids: set[str],
) -> dict[str, Any]:
    relative = path.relative_to(project_root).as_posix()
    text = path.read_text(encoding="utf-8")
    assessment = validate_spec_text(
        text,
        known_spec_ids=known_spec_ids,
    )
    _apply_identity_errors(
        assessment,
        _canonical_identity_errors(project_root, path, text),
    )
    return {
        "path": relative,
        "assessment": assessment,
        "status": assessment["canonical_spec"]["status"],
        "slug": path.stem.split("-", 2)[-1].casefold(),
    }


def resolve_spec_context(
    project_root: Path,
    prompt: str,
    *,
    tracker_path: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Resolve active spec by explicit/tracker path, branch, then unique confirmed."""
    specs_dir = project_root / "specs"
    paths = [
        path
        for path in sorted(specs_dir.glob("SPEC-[0-9][0-9][0-9][0-9]-*.md"))
        if path.is_file()
    ]
    known_spec_ids = _repository_spec_ids(project_root)
    records = [_candidate_record(project_root, path, known_spec_ids) for path in paths]

    def response(
        state: str,
        selected: dict[str, Any] | None,
        candidates: list[dict[str, Any]],
        reason: str,
    ) -> dict[str, Any]:
        return {
            "state": state,
            "selected_path": selected["path"] if selected else None,
            "candidates": [record["path"] for record in candidates],
            "reason": reason,
        }

    explicit = CANONICAL_PATH_RE.search(prompt)
    if explicit:
        wanted = explicit.group("path").replace("\\", "/").casefold()
        selected = next(
            (row for row in records if row["path"].casefold() == wanted), None
        )
        if selected is None:
            return response(
                "invalid", None, records, "explicit canonical path does not exist"
            )
        if selected["assessment"]["verdict"] != "PASS":
            return response(
                "invalid", selected, [selected], "explicit canonical spec is invalid"
            )
        return response(
            selected["status"], selected, [selected], "explicit canonical path"
        )

    confirmed = [
        row
        for row in records
        if row["status"] == "confirmed" and row["assessment"]["verdict"] == "PASS"
    ]
    if tracker_path:
        wanted = tracker_path.replace("\\", "/").casefold()
        selected = next(
            (row for row in records if row["path"].casefold() == wanted), None
        )
        if selected is None:
            return response(
                "invalid", None, records, "tracker canonical path does not exist"
            )
        if selected["assessment"]["verdict"] != "PASS":
            return response(
                "invalid", selected, [selected], "tracker canonical spec is invalid"
            )
        return response(
            selected["status"], selected, [selected], "tracker canonical path"
        )
    if branch:
        normalized_branch = branch.casefold().replace("_", "-")
        matches = [row for row in confirmed if row["slug"] in normalized_branch]
        if len(matches) == 1:
            return response("confirmed", matches[0], matches, "branch name match")
        if len(matches) > 1:
            return response(
                "ambiguous", None, matches, "multiple branch-matched specifications"
            )
    if len(confirmed) == 1:
        return response(
            "confirmed", confirmed[0], confirmed, "unique confirmed specification"
        )
    if len(confirmed) > 1:
        return response(
            "ambiguous", None, confirmed, "multiple confirmed specifications"
        )
    invalid = [row for row in records if row["assessment"]["verdict"] != "PASS"]
    if invalid:
        return response(
            "invalid", None, invalid, "repository contains invalid specifications"
        )
    return response("none", None, [], "no active confirmed specification")


def verify_spec(
    text: str,
    *,
    known_spec_ids: set[str] | None = None,
    requested_changes: list[str] | None = None,
    scope_creep: list[str] | None = None,
) -> dict[str, Any]:
    """Verify a confirmed spec and block any un-reconciled request delta."""
    assessment = validate_spec_text(text, known_spec_ids=known_spec_ids)
    new_decisions = list(requested_changes or [])
    unauthorized_scope = list(scope_creep or [])
    if new_decisions:
        return {
            "verdict": "BLOCKED",
            "errors": ["new request content requires reconciliation"],
            "new_decisions": new_decisions,
            "canonical_spec": assessment["canonical_spec"],
            "traceability": assessment["traceability"],
        }
    if assessment["canonical_spec"]["status"] != "confirmed":
        assessment["errors"].append("active implementation spec must be confirmed")
        assessment["verdict"] = "BLOCKED"
        assessment["traceability"]["verdict"] = "BLOCKED"
    if unauthorized_scope:
        assessment["errors"].append(
            "implementation contains behavior outside canonical scope"
        )
        assessment["verdict"] = "BLOCKED"
        assessment["traceability"]["verdict"] = "BLOCKED"
        assessment["traceability"]["scope_creep"] = unauthorized_scope
    assessment["new_decisions"] = []
    return assessment


def verify_spec_path(
    spec_path: Path,
    *,
    requested_changes: list[str] | None = None,
    scope_creep: list[str] | None = None,
) -> dict[str, Any]:
    """Verify one canonical repository path with cross-spec identity context."""
    if spec_path.parent.name.casefold() != "specs":
        return {
            "verdict": "BLOCKED",
            "errors": ["canonical spec must be directly under specs/"],
            "new_decisions": [],
            "traceability": {
                "verdict": "BLOCKED",
                "uncovered_requirements": [],
                "uncovered_acceptance": [],
                "scope_creep": [],
            },
        }
    project_root = spec_path.parent.parent
    text = spec_path.read_text(encoding="utf-8")
    result = verify_spec(
        text,
        known_spec_ids=_repository_spec_ids(project_root),
        requested_changes=requested_changes,
        scope_creep=scope_creep,
    )
    result = _apply_identity_errors(
        result,
        _canonical_identity_errors(project_root, spec_path, text),
    )
    result["canonical_spec"]["path"] = (Path("specs") / spec_path.name).as_posix()
    return result


def mark_spec_implemented(
    spec_path: Path,
    evidence_by_ac: dict[str, str],
    *,
    spec_review_passed: bool,
    authorized: bool,
    validation_assessor=None,
) -> dict[str, Any]:
    """Record implementation evidence after the enclosing governed orchestration."""
    if not authorized:
        return {"verdict": "BLOCKED", "reason": "explicit authorization required"}
    if not spec_review_passed:
        return {"verdict": "BLOCKED", "reason": "Spec review has not passed"}
    if spec_path.parent.name.casefold() != "specs":
        return {
            "verdict": "BLOCKED",
            "reason": "canonical spec must be directly under specs/",
        }
    text = spec_path.read_text(encoding="utf-8")
    project_root = spec_path.parent.parent
    known_spec_ids = _repository_spec_ids(project_root)
    current = validate_spec_text(text, known_spec_ids=known_spec_ids)
    _apply_identity_errors(
        current,
        _canonical_identity_errors(project_root, spec_path, text),
    )
    if (
        current["verdict"] != "PASS"
        or current["canonical_spec"]["status"] != "confirmed"
    ):
        return {
            "verdict": "BLOCKED",
            "reason": "canonical spec is not confirmed and valid",
        }

    sections = _sections(text)
    acceptance = _table(sections.get("acceptance criteria", ""))
    ac_ids = {_field(row, "ID") for row in acceptance}
    if set(evidence_by_ac) != ac_ids or any(
        not evidence.casefold().startswith("pass")
        for evidence in evidence_by_ac.values()
    ):
        return {
            "verdict": "BLOCKED",
            "reason": "every AC requires actual PASS evidence",
        }

    lines = text.splitlines()
    in_acceptance = False
    for index, line in enumerate(lines):
        if line.casefold().startswith("## acceptance criteria"):
            in_acceptance = True
            continue
        if in_acceptance and line.startswith("## "):
            in_acceptance = False
        if not in_acceptance or not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and cells[0] in evidence_by_ac and len(cells) >= 5:
            cells[4] = evidence_by_ac[cells[0]]
            lines[index] = "| " + " | ".join(cells) + " |"

    rendered = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    rendered = re.sub(
        r"(?m)^status:\s*confirmed\s*$", "status: implemented", rendered, count=1
    )
    revision = int(current["canonical_spec"]["revision"])
    rendered = re.sub(
        r"(?m)^revision:\s*\d+\s*$",
        f"revision: {revision + 1}",
        rendered,
        count=1,
    )
    revision_heading = next(
        (
            index
            for index, line in enumerate(rendered.splitlines())
            if line.strip().casefold() == "## revision history"
        ),
        None,
    )
    if revision_heading is not None:
        rendered_lines = rendered.splitlines()
        insert_at = len(rendered_lines)
        for index in range(revision_heading + 1, len(rendered_lines)):
            if rendered_lines[index].startswith("## "):
                insert_at = index
                break
        while (
            insert_at > revision_heading + 1
            and not rendered_lines[insert_at - 1].strip()
        ):
            insert_at -= 1
        rendered_lines.insert(
            insert_at,
            f"| {revision + 1} | {date.today().isoformat()} | Recorded implementation PASS evidence. |",
        )
        rendered = "\n".join(rendered_lines) + "\n"
    rendered = re.sub(
        r"(?im)spec review:\s*(?:pending|blocked)\b",
        "Spec review: PASS",
        rendered,
        count=1,
    )
    if "spec review: pass" not in rendered.casefold():
        rendered = re.sub(
            r"(?im)^(## Routing/Gates[^\n]*\n)",
            r"\1Spec review: PASS\n",
            rendered,
            count=1,
        )
    final = validate_spec_text(rendered, known_spec_ids=known_spec_ids)
    if final["verdict"] != "PASS":
        return {
            "verdict": "BLOCKED",
            "reason": "implemented lifecycle validation failed",
            "errors": final["errors"],
        }
    evidence = assess_spec_evidence_update(
        project_root, rendered, validation_assessor=validation_assessor
    )
    if evidence["verdict"] != "PASS":
        return {
            "verdict": evidence["verdict"],
            "reason": "acceptance evidence is insufficient",
            "validation": evidence,
        }
    spec_path.write_text(rendered, encoding="utf-8", newline="\n")
    final["canonical_spec"]["path"] = (Path("specs") / spec_path.name).as_posix()
    return final


def main(validation_assessor=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--spec", type=Path, required=True)

    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    resolve_parser.add_argument("--prompt", default="")
    resolve_parser.add_argument("--tracker-path")
    resolve_parser.add_argument("--branch")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    start_parser.add_argument("--slug", required=True)
    start_parser.add_argument("--snapshot", type=Path, required=True)
    start_parser.add_argument("--working-id")
    start_parser.add_argument("--task-ref")
    start_parser.add_argument("--branch")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    status_parser.add_argument("--reference")
    status_parser.add_argument("--task-ref")
    status_parser.add_argument("--branch")

    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    migrate_parser.add_argument("--working-id", required=True)
    migrate_parser.add_argument("--note", action="append", default=[])

    reconcile_parser = subparsers.add_parser("reconcile")
    reconcile_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    reconcile_parser.add_argument("--working-id", required=True)
    reconcile_parser.add_argument("--snapshot", type=Path, required=True)
    reconcile_parser.add_argument("--base-snapshot", type=Path)
    reconcile_parser.add_argument("--delta", type=Path, required=True)
    reconcile_parser.add_argument("--expected-revision", type=int, required=True)
    reconcile_parser.add_argument("--expected-hash", required=True)
    reconcile_parser.add_argument("--question-id")
    reconcile_parser.add_argument("--question-version", type=int)
    reconcile_parser.add_argument("--answer")

    question_parser = subparsers.add_parser("question")
    question_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    question_parser.add_argument("--working-id", required=True)
    question_parser.add_argument("--question-id", required=True)
    question_parser.add_argument("--question", required=True)
    question_parser.add_argument("--option", action="append", default=[])
    question_parser.add_argument(
        "--kind", choices=("choice", "open-text"), default="choice"
    )
    question_parser.add_argument("--expected-revision", type=int, required=True)
    question_parser.add_argument("--expected-hash", required=True)

    policy_parser = subparsers.add_parser("question-policy")
    policy_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    policy_parser.add_argument("--reference", required=True)
    policy_parser.add_argument("--task-ref", required=True)
    policy_parser.add_argument("--host", type=Path, required=True)
    policy_parser.add_argument("--surface", required=True)
    update_parser = subparsers.add_parser("question-update")
    update_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    update_parser.add_argument("--working-id", required=True)
    update_parser.add_argument("--request", type=Path, required=True)
    update_parser.add_argument("--expected-revision", type=int, required=True)
    update_parser.add_argument("--expected-hash", required=True)

    finish_parser = subparsers.add_parser("finish-turn")
    finish_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    finish_parser.add_argument("--reference", required=True)
    finish_parser.add_argument("--task-ref", required=True)
    finish_parser.add_argument("--observation", type=Path, required=True)

    turn_parser = subparsers.add_parser("turn-context")
    turn_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    turn_parser.add_argument("--reference")
    turn_parser.add_argument("--task-ref")

    materialize_parser = subparsers.add_parser("materialize")
    materialize_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    materialize_parser.add_argument("--working-id", required=True)
    materialize_parser.add_argument("--expected-revision", type=int, required=True)
    materialize_parser.add_argument("--expected-hash", required=True)

    reopen_parser = subparsers.add_parser("reopen")
    reopen_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    reopen_parser.add_argument("--spec", type=Path, required=True)
    reopen_parser.add_argument("--expected-revision", type=int, required=True)
    reopen_parser.add_argument("--reason", required=True)
    reopen_parser.add_argument("--task-ref")
    reopen_parser.add_argument("--branch")

    commit_parser = subparsers.add_parser("prepare-commit")
    commit_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    commit_parser.add_argument(
        "--disposition",
        choices=sorted(COMMIT_DISPOSITIONS),
    )

    args = parser.parse_args()
    if args.command in ("question-policy", "question-update"):
        try:
            if args.command == "question-policy":
                context = assess_turn_context(
                    args.project_root, reference=args.reference, task_ref=args.task_ref
                )
                result = question_surface_policy(
                    json.loads(args.host.read_text(encoding="utf-8")),
                    args.surface,
                    context.get("question_record", {}).get("failed_surfaces", {}),
                )
                if context.get("state") != "pending":
                    result.update(
                        verdict="BLOCKED",
                        menu_allowed=False,
                        surface_allowed=False,
                        reason="persist and reload the current question before presentation",
                    )
            else:
                result = update_question(
                    args.project_root,
                    args.working_id,
                    json.loads(args.request.read_text(encoding="utf-8")),
                    expected_revision=args.expected_revision,
                    expected_hash=args.expected_hash,
                    validation_assessor=validation_assessor,
                )
        except (OSError, ValueError, TypeError) as error:
            result = {"verdict": "BLOCKED", "reason": str(error)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["verdict"] == "PASS" else 2
    if args.command == "finish-turn":
        try:
            result = finish_discussion_turn(
                args.project_root,
                reference=args.reference,
                task_ref=args.task_ref,
                observation=json.loads(args.observation.read_text(encoding="utf-8")),
            )
        except (OSError, ValueError, TypeError) as error:
            result = {
                "verdict": "BLOCKED",
                "can_end_turn": True,
                "reason": str(error),
                "sync_status": "unverifiable",
                "next_action": "report-save-gap-and-finish",
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["verdict"] == "PASS" else 2
    if args.command == "validate":
        project_root = (
            args.spec.parent.parent
            if args.spec.parent.name.casefold() == "specs"
            else args.spec.parent
        )
        result = validate_spec_text(
            args.spec.read_text(encoding="utf-8"),
            known_spec_ids=_repository_spec_ids(project_root),
        )
        _apply_identity_errors(
            result,
            _canonical_identity_errors(
                project_root,
                args.spec,
                args.spec.read_text(encoding="utf-8"),
            ),
        )
        result["canonical_spec"]["path"] = (
            (Path("specs") / args.spec.name).as_posix()
            if args.spec.parent.name.casefold() == "specs"
            else None
        )
    elif args.command == "resolve":
        result = resolve_spec_context(
            args.project_root,
            args.prompt,
            tracker_path=args.tracker_path,
            branch=args.branch,
        )
    elif args.command == "start":
        result = start_working_bundle(
            args.project_root,
            args.slug,
            args.snapshot.read_text(encoding="utf-8"),
            working_id=args.working_id,
            task_ref=args.task_ref,
            branch=args.branch,
        )
    elif args.command == "migrate":
        result = _migrate_flat_bundle(args.project_root, args.working_id, args.note)
    elif args.command == "status":
        result = resolve_working_bundle(
            args.project_root,
            reference=args.reference,
            task_ref=args.task_ref,
            branch=args.branch,
        )
    elif args.command == "reconcile":
        result = reconcile_working_bundle(
            args.project_root,
            args.working_id,
            args.snapshot.read_text(encoding="utf-8"),
            json.loads(args.delta.read_text(encoding="utf-8")),
            base_snapshot=args.base_snapshot.read_text(encoding="utf-8")
            if args.base_snapshot
            else None,
            expected_revision=args.expected_revision,
            expected_hash=args.expected_hash,
            question_id=args.question_id,
            question_version=args.question_version,
            answer=args.answer,
            validation_assessor=validation_assessor,
        )
    elif args.command == "question":
        result = record_question(
            args.project_root,
            args.working_id,
            args.question_id,
            args.question,
            args.option,
            expected_revision=args.expected_revision,
            expected_hash=args.expected_hash,
            question_kind=args.kind,
            validation_assessor=validation_assessor,
        )
    elif args.command == "turn-context":
        result = assess_turn_context(
            args.project_root,
            reference=args.reference,
            task_ref=args.task_ref,
        )
    elif args.command == "materialize":
        result = materialize_working_bundle(
            args.project_root,
            args.working_id,
            expected_revision=args.expected_revision,
            expected_hash=args.expected_hash,
            validation_assessor=validation_assessor,
        )
    elif args.command == "reopen":
        result = reopen_spec(
            args.project_root,
            args.spec,
            expected_revision=args.expected_revision,
            reason=args.reason,
            task_ref=args.task_ref,
            branch=args.branch,
        )
    else:
        result = prepare_commit(
            args.project_root,
            disposition=args.disposition,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return (
        0
        if result.get("verdict", "PASS") == "PASS"
        and result.get("state") not in {"ambiguous", "invalid"}
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
