#!/usr/bin/env python3
"""Validate, materialize, resolve, and verify canonical change-set specs."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Callable


SPEC_ID_RE = re.compile(r"^SPEC-(\d{4})$")
ITEM_ID_RE = re.compile(r"^(REQ|DEC|AC)-(\d{3})$")
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
RELATIONS = {"depends_on", "refines", "conflicts_with", "supersedes"}


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


def materialize_spec(
    project_root: Path,
    slug: str,
    text: str,
    *,
    authorized: bool,
) -> dict[str, Any]:
    """Write one validated canonical spec only after explicit authorization."""
    if not authorized:
        return {
            "verdict": "BLOCKED",
            "reason": "explicit authorization required",
            "canonical_spec": None,
        }
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
    destination.write_text(rendered, encoding="utf-8", newline="\n")
    reference = assessment["canonical_spec"]
    reference["path"] = relative.as_posix()
    return {"verdict": "PASS", "canonical_spec": reference}


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
    else:
        result = resolve_spec_context(
            args.project_root,
            args.prompt,
            tracker_path=args.tracker_path,
            branch=args.branch,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("verdict", "PASS") == "PASS" and result.get("state") not in {"ambiguous", "invalid"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
