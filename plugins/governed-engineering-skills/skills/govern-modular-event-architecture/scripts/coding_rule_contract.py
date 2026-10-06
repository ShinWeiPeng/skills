"""Check the selected rule catalog and recorded applicability without guessing facts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def catalog(rules=None):
    rules = rules or os.environ.get("GOVERNED_CODING_RULES")
    rules = (
        Path(rules)
        if rules
        else Path(__file__).resolve().parents[2] / "coding-standards/rules"
    )
    files = sorted(rules.glob("*.md"))
    if not files:
        raise ValueError("shared coding rule catalog is unavailable")
    metadata = json.loads(
        (rules.parent / "references/catalog.json").read_text(encoding="utf-8")
    )
    if (
        not isinstance(metadata, dict)
        or set(metadata) != {"version"}
        or type(metadata["version"]) is not int
        or metadata["version"] < 1
    ):
        raise ValueError("invalid shared rule catalog version")
    digest = hashlib.sha256()
    ids = set()
    for path in files:
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        digest.update(path.name.encode() + b"\0" + text.encode() + b"\0")
        rows = [line for line in text.splitlines() if line.startswith("|")]
        if len(rows) < 3 or [x.strip() for x in rows[0].strip("|").split("|")] != [
            "Rule ID",
            "Strength",
            "Applicable conditions",
            "Program requirement",
        ]:
            raise ValueError(f"invalid rule table: {path.name}")
        for row in rows[2:]:
            values = [x.strip() for x in row.strip("|").split("|")]
            if (
                len(values) != 4
                or not all(values)
                or values[1] not in {"MUST", "SHOULD", "MAY"}
                or values[0] in ids
            ):
                raise ValueError(f"invalid or duplicate rule: {path.name}")
            ids.add(values[0])
    return {
        "version": metadata["version"],
        "sha256": digest.hexdigest(),
        "ids": sorted(ids),
    }


def validate_rule_binding(manifest, rules=None):
    binding = manifest.get("coding_rules")
    if binding is None and "implementation_design" not in manifest:
        return []  # Historical schema support; adoption is required by the Skill.
    errors = []

    def issue(message):
        errors.append(
            {
                "rule_id": "CODING001",
                "severity": "MUST",
                "location": "coding_rules",
                "message": message,
                "configuration": True,
                "disposition": "active",
            }
        )

    try:
        current = catalog(rules)
    except (OSError, ValueError) as exc:
        issue(str(exc))
        return errors
    if not isinstance(binding, dict) or set(binding) != {
        "version",
        "sha256",
        "applicability",
    }:
        issue("expected version, sha256 and applicability for the shared catalog")
        return errors
    if (
        type(binding["version"]) is not int
        or binding["version"] != current["version"]
        or binding["sha256"] != current["sha256"]
    ):
        issue(
            "rule catalog changed; reconcile applicability and design before implementation or review"
        )
    rows = binding["applicability"]
    if not isinstance(rows, dict) or set(rows) != set(current["ids"]):
        issue("applicability must cover the current rule IDs exactly")
        return errors
    for identity, row in rows.items():
        if (
            not isinstance(row, dict)
            or set(row) != {"status", "reason"}
            or not isinstance(row.get("status"), str)
            or row["status"] not in {"applicable", "not-applicable"}
            or not isinstance(row.get("reason"), str)
            or not row["reason"].strip()
        ):
            issue(
                f"{identity}: unresolved applicability or missing project/path rationale"
            )
    return errors
