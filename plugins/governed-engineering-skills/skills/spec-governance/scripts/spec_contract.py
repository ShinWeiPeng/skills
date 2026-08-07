#!/usr/bin/env python3
"""Persist, validate, materialize, resolve, and verify change-set specs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable


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


def _table(section: str) -> list[dict[str, str]]:
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in section.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if len(rows) < 2:
        return []
    headers = rows[0]
    data = rows[2:] if all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]) else rows[1:]
    return [
        dict(zip(headers, cells))
        for cells in data
        if len(cells) == len(headers)
    ]


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
        f"{item_id} has no acceptance criterion"
        for item_id in uncovered_requirements
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
                errors.append(f"relationship references unknown ID {ref or '<missing>'}")
        if relation == "conflicts_with":
            conflicts.append({"source": source, "target": target})

    open_decisions = sections.get("open decisions", "")
    if status in {"confirmed", "implemented"} and not _open_decisions_are_empty(open_decisions):
        errors.append("confirmed and implemented specs must have zero open decisions")
    if status in {"confirmed", "implemented"} and conflicts:
        errors.append("confirmed and implemented specs must have zero unresolved conflicts")

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
        "revision": int(metadata["revision"]) if metadata.get("revision", "").isdigit() else None,
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
            str(row.get("text", "")).strip().casefold(): row
            for row in result[key]
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
            retained = [
                row for row in result[key] if str(row.get("id", "")) != item_id
            ]
            if len(retained) != len(result[key]):
                result[key] = retained
                removed_ids.append(item_id)
                if item_id in added_ids:
                    added_ids.remove(item_id)
                if item_id in changed_ids:
                    changed_ids.remove(item_id)
                break

    relationships = [
        dict(item) for item in working_spec.get("relationships", [])
    ]
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


def _normalized_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _atomic_write(path: Path, text: str) -> None:
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
            if re.search(
                rf"(?im)^-\s+\*\*{re.escape(label)}:\*\*\s*\S",
                row["content"],
            ) is None:
                errors.append(f"{discussion_id} missing discussion field {label}")
        impact = re.search(
            r"(?im)^-\s+\*\*Resulting impact:\*\*\s*(.+)$",
            row["content"],
        )
        affected_ids = re.findall(r"\b(?:REQ|DEC|AC)-\d{3}\b", impact.group(1) if impact else "")
        known_ids = set(_snapshot_rows(text))
        if not affected_ids:
            errors.append(f"{discussion_id} resulting impact must link an affected REQ/DEC/AC ID")
        for affected_id in affected_ids:
            if affected_id not in known_ids:
                errors.append(f"{discussion_id} links unknown affected ID {affected_id}")
    forbidden_patterns = (
        (r"(?im)^#{1,6}\s+(?:full\s+)?transcript\b", "full transcript"),
        (r"(?i)<(?:thinking|reasoning)>", "hidden reasoning"),
        (r"(?i)\b(?:chain[ -]of[ -]thought|hidden reasoning|internal reasoning)\b", "hidden reasoning"),
    )
    for pattern, label in forbidden_patterns:
        if re.search(pattern, text):
            errors.append(f"working snapshot contains forbidden {label}")
    if (
        re.search(r"(?im)^\s*(?:user|human)\s*:", text)
        and re.search(r"(?im)^\s*(?:assistant|ai)\s*:", text)
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
        lambda match: f"{match.group(1)}{match.group(2)}{REDACTION_MARKERS['credential']}",
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
        r"(?<!\w)\+?(?:\d[\s().-]?){8,19}\d(?!\w)",
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
                    key.strip().casefold(): value.strip()
                    for key, value in row.items()
                }
    return rows


def _discussion_rows(text: str) -> dict[str, dict[str, str]]:
    section = _sections(text).get("discussion context", "")
    matches = list(
        re.finditer(r"(?m)^###\s+(DISC-\d{3})(?::\s+(.+?))?\s*$", section)
    )
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
        for raw_line in path.read_text(encoding="utf-8").splitlines():
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
        if event_type != "start" or journal_exists:
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
        "delta": delta or {
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
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(_normalized_json(event) + "\n")
    return event


def _contract_hash(text: str) -> str:
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
            rendered = rendered[: heading.end()] + "\n"
    return _sha256_text(rendered.strip() + "\n")


def _working_reference(
    project_root: Path,
    snapshot_path: Path,
    journal_path: Path,
) -> dict[str, Any]:
    text = snapshot_path.read_text(encoding="utf-8")
    metadata, _ = _metadata(text)
    events, continuity = _read_journal(journal_path)
    snapshot_hash = _sha256_text(text)
    if not events or events[-1].get("snapshot_hash") != snapshot_hash:
        continuity = "unavailable"
    elif events[-1].get("continuity") == "unavailable":
        continuity = "unavailable"
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
    source_journal_bytes = legacy_journal.read_bytes() if legacy_journal.is_file() else None
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
    source_snapshot_hash = _sha256_text(source_text)
    if events and events[-1].get("snapshot_hash") != source_snapshot_hash:
        return failure("legacy journal snapshot hash is stale")
    rewritten_events: list[dict[str, Any]] = []
    previous_event_hash: str | None = None
    snapshot_hash = _sha256_text(rendered)
    for index, source_event in enumerate(events):
        event = {
            key: value
            for key, value in source_event.items()
            if key != "event_hash"
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
    temporary_snapshot = destination_snapshot.with_name(f".{destination_snapshot.name}.{token}.tmp")
    temporary_journal = destination_journal.with_name(f".{destination_journal.name}.{token}.tmp")
    try:
        temporary_snapshot.write_text(rendered, encoding="utf-8", newline="\n")
        temporary_journal.write_text(journal_text, encoding="utf-8", newline="\n")
        migrated_events, migrated_continuity = _read_journal(temporary_journal)
        if (
            _working_structure_errors(temporary_snapshot.read_text(encoding="utf-8"))
            or (rewritten_events and migrated_continuity != "continuous")
            or (migrated_events and migrated_events[-1].get("snapshot_hash") != snapshot_hash)
        ):
            raise ValueError("migrated working specification verification failed")
        os.replace(temporary_journal, destination_journal)
        try:
            os.replace(temporary_snapshot, destination_snapshot)
        except OSError:
            destination_journal.unlink(missing_ok=True)
            raise
        if (
            _working_structure_errors(destination_snapshot.read_text(encoding="utf-8"))
            or _read_journal(destination_journal)[1] != ("continuous" if rewritten_events else "unavailable")
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


def _working_candidates(project_root: Path) -> list[dict[str, Any]]:
    root = project_root / WORKING_ROOT
    candidates: list[dict[str, Any]] = []
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

    def result(state: str, matches: list[dict[str, Any]], reason: str) -> dict[str, Any]:
        return {
            "state": state,
            "working_spec": matches[0] if len(matches) == 1 else None,
            "candidates": [
                row.get("snapshot_path") or row.get("working_id")
                for row in matches
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
        if not matches:
            invalid_matches = [
                row
                for row in invalid
                if str(row.get("working_id", "")).casefold() in {original, normalized}
                or str(row.get("logical_working_id", "")).casefold() in {original, normalized}
                or str(row.get("snapshot_path", "")).casefold() in {original, normalized}
            ]
            if invalid_matches:
                errors = sorted(
                    {
                        error
                        for row in invalid_matches
                        for error in row.get("errors", [])
                    }
                )
                return result(
                    "invalid",
                    invalid_matches,
                    "; ".join(errors) or "working specification is malformed",
                )
        return result(
            "working" if len(matches) == 1 else "invalid",
            matches,
            "explicit working reference" if matches else "explicit working reference does not exist",
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
        return result("ambiguous", valid, "multiple working specifications require an explicit reference")
    if invalid:
        return result("invalid", invalid, "working specification is malformed")
    return result("absent", [], "no working specification exists")


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
            "errors": sorted({error for row in invalid for error in row.get("errors", [])}),
        }
    matching = [row for row in discovered if row.get("change_set") == slug]
    if len(matching) == 1:
        return {"verdict": "PASS", "working_spec": matching[0], "created": False}
    if len(matching) > 1:
        return {"verdict": "BLOCKED", "reason": "multiple working specifications match change set"}
    working_id = working_id or f"WORKING-SPEC-{uuid.uuid4().hex[:12]}-{slug}"
    if not WORKING_ID_RE.fullmatch(working_id):
        return {"verdict": "BLOCKED", "reason": "invalid working ID"}
    snapshot_path, journal_path = _working_paths(project_root, working_id)
    if snapshot_path.exists():
        reference = _working_reference(project_root, snapshot_path, journal_path)
        return {"verdict": "PASS", "working_spec": reference, "created": False}
    metadata, metadata_errors = _metadata(text)
    if metadata_errors:
        return {"verdict": "BLOCKED", "reason": "invalid working snapshot", "errors": metadata_errors}
    rendered = _redact_sensitive_content(_replace_metadata(
        text,
        spec_id=metadata.get("spec_id", "SPEC-0000") if preserve_spec_identity else "SPEC-0000",
        revision=1 if not preserve_spec_identity else metadata.get("revision", "1"),
        status="working",
        change_set=slug,
        working_id=working_id,
        task_ref=task_ref,
        branch_ref=branch,
    ))
    errors = _working_structure_errors(rendered)
    if errors:
        return {"verdict": "BLOCKED", "reason": "invalid working snapshot", "errors": errors}
    _atomic_write(snapshot_path, rendered)
    snapshot_hash = _sha256_text(rendered)
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


def reconcile_working_bundle(
    project_root: Path,
    working_id: str,
    next_snapshot: str,
    normalized_delta: dict[str, Any],
    *,
    expected_revision: int,
    expected_hash: str,
) -> dict[str, Any]:
    """Persist a complete next snapshot with optimistic revision/hash checks."""
    if not (WORKING_ID_RE.fullmatch(working_id) or LEGACY_WORKING_ID_RE.fullmatch(working_id)):
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
    current_hash = _sha256_text(current)
    current_revision = int(metadata.get("revision", "0"))
    if expected_revision != current_revision or expected_hash != current_hash:
        return {
            "verdict": "BLOCKED",
            "reason": "stale working specification",
            "working_spec": _working_reference(project_root, snapshot_path, journal_path),
        }
    rendered = _redact_sensitive_content(_replace_metadata(
        next_snapshot,
        spec_id=metadata.get("spec_id"),
        revision=current_revision + 1,
        status="working",
        change_set=metadata.get("change_set"),
        working_id=working_id,
        task_ref=metadata.get("task_ref") or None,
        branch_ref=metadata.get("branch_ref") or None,
    ))
    errors = _working_structure_errors(rendered)
    if errors:
        return {"verdict": "BLOCKED", "reason": "invalid next working snapshot", "errors": errors}
    if metadata.get("spec_id") != "SPEC-0000":
        replacement_errors = _confirmed_decision_replacement_errors(current, rendered)
        if replacement_errors:
            return {
                "verdict": "BLOCKED",
                "reason": "confirmed decisions must be superseded, not rewritten",
                "errors": replacement_errors,
            }
    consistency = _snapshot_consistency(current, rendered)
    delta = consistency["delta"]
    relationships = consistency["relationships"]
    conflicts = consistency["conflicts"]
    open_decisions = consistency["open_decisions"]
    verdict = consistency["verdict"]
    _, continuity = _read_journal(journal_path)
    _atomic_write(snapshot_path, rendered)
    snapshot_hash = _sha256_text(rendered)
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
) -> dict[str, Any]:
    """Write one decision-complete canonical spec without product authorization."""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        return {"verdict": "BLOCKED", "reason": "invalid change-set slug", "canonical_spec": None}
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
    specs_dir = project_root / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    relative = Path("specs") / f"{spec_id}-{slug}.md"
    destination = project_root / relative
    _atomic_write(destination, rendered)
    reference = assessment["canonical_spec"]
    reference["path"] = relative.as_posix()
    return {
        "verdict": "PASS",
        "canonical_spec": reference,
        "product_execution_authorized": False,
    }


def materialize_working_bundle(
    project_root: Path,
    working_id: str,
    *,
    expected_revision: int,
    expected_hash: str,
) -> dict[str, Any]:
    """Confirm a decision-complete bundle, creating or updating its canonical spec."""
    if not (WORKING_ID_RE.fullmatch(working_id) or LEGACY_WORKING_ID_RE.fullmatch(working_id)):
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
    current_hash = _sha256_text(current)
    current_revision = int(metadata.get("revision", "0"))
    if current_revision != expected_revision or current_hash != expected_hash:
        return {
            "verdict": "BLOCKED",
            "reason": "stale working specification",
            "working_spec": _working_reference(project_root, snapshot_path, journal_path),
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
    destination = project_root / "specs" / f"{spec_id}-{slug}.md"
    if existing and not destination.is_file():
        return {
            "verdict": "BLOCKED",
            "reason": "reopened canonical specification path is missing",
        }
    if existing:
        existing_metadata, _ = _metadata(destination.read_text(encoding="utf-8"))
        if existing_metadata.get("status") == "implemented":
            return {"verdict": "BLOCKED", "reason": "implemented specification cannot reopen"}
    events, _ = _read_journal(journal_path)
    baseline_hash = next(
        (
            event.get("baseline_contract_hash")
            for event in events
            if event.get("baseline_contract_hash")
        ),
        None,
    )
    actual_delta = baseline_hash is not None and baseline_hash != _contract_hash(rendered)
    _atomic_write(destination, rendered)
    working_rendered = _replace_metadata(
        rendered,
        working_id=working_id,
        task_ref=metadata.get("task_ref") or None,
        branch_ref=metadata.get("branch_ref") or None,
    )
    _atomic_write(snapshot_path, working_rendered)
    final_hash = _sha256_text(working_rendered)
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
        "authorization_retained": bool(existing and not actual_delta),
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
        return {"verdict": "BLOCKED", "reason": "canonical specification does not exist"}
    try:
        relative = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return {"verdict": "BLOCKED", "reason": "canonical specification is outside the project"}
    if relative.parent.as_posix().casefold() != "specs":
        return {"verdict": "BLOCKED", "reason": "canonical specification must be directly under specs/"}
    text = path.read_text(encoding="utf-8")
    metadata, errors = _metadata(text)
    if errors:
        return {"verdict": "BLOCKED", "reason": "canonical metadata is invalid", "errors": errors}
    if metadata.get("status") == "implemented":
        return {"verdict": "BLOCKED", "reason": "implemented specification cannot reopen"}
    if metadata.get("status") != "confirmed":
        return {"verdict": "BLOCKED", "reason": "only confirmed specifications can reopen"}
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
    _atomic_write(path, reopened)
    result = start_working_bundle(
        project_root,
        metadata["change_set"],
        reopened,
        task_ref=task_ref,
        branch=branch,
        preserve_spec_identity=True,
        baseline_contract_hash=baseline_hash,
    )
    if result["verdict"] != "PASS":
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
            "errors": sorted({error for row in invalid for error in row.get("errors", [])}),
        }
    bundles = sorted(
        row["snapshot_path"] for row in discovered if row.get("snapshot_path")
    )
    if tracked_paths is None or staged_paths is None:
        try:
            tracked = subprocess.run(
                ["git", "-C", str(project_root), "ls-files", "--", WORKING_ROOT.as_posix()],
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
    records = [
        _candidate_record(project_root, path, known_spec_ids)
        for path in paths
    ]

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
        selected = next((row for row in records if row["path"].casefold() == wanted), None)
        if selected is None:
            return response("invalid", None, records, "explicit canonical path does not exist")
        if selected["assessment"]["verdict"] != "PASS":
            return response("invalid", selected, [selected], "explicit canonical spec is invalid")
        return response(selected["status"], selected, [selected], "explicit canonical path")

    confirmed = [
        row
        for row in records
        if row["status"] == "confirmed" and row["assessment"]["verdict"] == "PASS"
    ]
    if tracker_path:
        wanted = tracker_path.replace("\\", "/").casefold()
        selected = next((row for row in records if row["path"].casefold() == wanted), None)
        if selected is None:
            return response("invalid", None, records, "tracker canonical path does not exist")
        if selected["assessment"]["verdict"] != "PASS":
            return response("invalid", selected, [selected], "tracker canonical spec is invalid")
        return response(selected["status"], selected, [selected], "tracker canonical path")
    if branch:
        normalized_branch = branch.casefold().replace("_", "-")
        matches = [row for row in confirmed if row["slug"] in normalized_branch]
        if len(matches) == 1:
            return response("confirmed", matches[0], matches, "branch name match")
        if len(matches) > 1:
            return response("ambiguous", None, matches, "multiple branch-matched specifications")
    if len(confirmed) == 1:
        return response("confirmed", confirmed[0], confirmed, "unique confirmed specification")
    if len(confirmed) > 1:
        return response("ambiguous", None, confirmed, "multiple confirmed specifications")
    invalid = [row for row in records if row["assessment"]["verdict"] != "PASS"]
    if invalid:
        return response("invalid", None, invalid, "repository contains invalid specifications")
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
        assessment["errors"].append("implementation contains behavior outside canonical scope")
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
) -> dict[str, Any]:
    """Record implementation evidence after the enclosing governed orchestration."""
    if not authorized:
        return {"verdict": "BLOCKED", "reason": "explicit authorization required"}
    if not spec_review_passed:
        return {"verdict": "BLOCKED", "reason": "Spec review has not passed"}
    if spec_path.parent.name.casefold() != "specs":
        return {"verdict": "BLOCKED", "reason": "canonical spec must be directly under specs/"}
    text = spec_path.read_text(encoding="utf-8")
    project_root = spec_path.parent.parent
    known_spec_ids = _repository_spec_ids(project_root)
    current = validate_spec_text(text, known_spec_ids=known_spec_ids)
    _apply_identity_errors(
        current,
        _canonical_identity_errors(project_root, spec_path, text),
    )
    if current["verdict"] != "PASS" or current["canonical_spec"]["status"] != "confirmed":
        return {"verdict": "BLOCKED", "reason": "canonical spec is not confirmed and valid"}

    sections = _sections(text)
    acceptance = _table(sections.get("acceptance criteria", ""))
    ac_ids = {_field(row, "ID") for row in acceptance}
    if set(evidence_by_ac) != ac_ids or any(
        not evidence.casefold().startswith("pass")
        for evidence in evidence_by_ac.values()
    ):
        return {"verdict": "BLOCKED", "reason": "every AC requires actual PASS evidence"}

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
    rendered = re.sub(r"(?m)^status:\s*confirmed\s*$", "status: implemented", rendered, count=1)
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
        while insert_at > revision_heading + 1 and not rendered_lines[insert_at - 1].strip():
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
    final = validate_spec_text(rendered, known_spec_ids=known_spec_ids)
    if final["verdict"] != "PASS":
        return {
            "verdict": "BLOCKED",
            "reason": "implemented lifecycle validation failed",
            "errors": final["errors"],
        }
    spec_path.write_text(rendered, encoding="utf-8", newline="\n")
    final["canonical_spec"]["path"] = (Path("specs") / spec_path.name).as_posix()
    return final


def main() -> int:
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

    reconcile_parser = subparsers.add_parser("reconcile")
    reconcile_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    reconcile_parser.add_argument("--working-id", required=True)
    reconcile_parser.add_argument("--snapshot", type=Path, required=True)
    reconcile_parser.add_argument("--delta", type=Path, required=True)
    reconcile_parser.add_argument("--expected-revision", type=int, required=True)
    reconcile_parser.add_argument("--expected-hash", required=True)

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
            expected_revision=args.expected_revision,
            expected_hash=args.expected_hash,
        )
    elif args.command == "materialize":
        result = materialize_working_bundle(
            args.project_root,
            args.working_id,
            expected_revision=args.expected_revision,
            expected_hash=args.expected_hash,
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
    return 0 if result.get("verdict", "PASS") == "PASS" and result.get("state") not in {"ambiguous", "invalid"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
