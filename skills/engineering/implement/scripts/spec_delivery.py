#!/usr/bin/env python3
"""Delivery-owned adapter for canonical specification context."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SKILLS_ROOT = Path(__file__).resolve().parents[2]
SPEC_SCRIPTS_ROOT = SKILLS_ROOT / "spec-governance" / "scripts"
if str(SPEC_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SPEC_SCRIPTS_ROOT))

from discussion_state import discussion_request
from spec_contract import (
    assess_project_validation,
    assess_turn_context,
    check_spec_dependencies,
    resolve_spec_context,
    validate_spec_text,
)


def manage_delivery_discussion(project_root: Path, request: dict) -> dict:
    """Delegate task discussion state to its sole specification owner."""
    return discussion_request(project_root, request)


def assess_delivery_spec_context(
    project_root: Path,
    prompt: str,
    *,
    tracker_path: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Project the canonical child result into the delivery workflow contract."""
    return resolve_spec_context(
        project_root,
        prompt,
        tracker_path=tracker_path,
        branch=branch,
    )


def assess_delivery_turn_context(
    project_root: Path,
    *,
    reference: str | None = None,
    task_ref: str | None = None,
) -> dict[str, Any]:
    """Project persisted decision context without transferring mutation authority."""
    return assess_turn_context(project_root, reference=reference, task_ref=task_ref)


def verify_delivery_admission(
    project_root: Path,
    spec_path: str,
    *,
    expected_hash: str,
    authorization: str,
    working_reference: str | None = None,
    task_ref: str | None = None,
    validation_assessor=None,
) -> dict[str, Any]:
    """Check current canonical content, pending work and the final human instruction."""
    blocked = {"verdict": "BLOCKED", "product_code_allowed": False}
    root = project_root.resolve()
    path = (root / spec_path).resolve()
    if path.parent != root / "specs" or not path.is_file():
        return blocked | {
            "reason": "canonical path must be a file directly under project specs"
        }
    relative = path.relative_to(root).as_posix()
    instruction = authorization.strip().replace("\\", "/")
    legacy_instruction = re.fullmatch(
        r"開始執行(?:\s+" + re.escape(relative) + r")?",
        instruction,
    )
    explicit = re.fullmatch(
        r"開始執行\s*SPEC-(\d{4}(?:/(?:SPEC-)?\d{4})*)", instruction
    )
    ids = (
        ["SPEC-" + item.removeprefix("SPEC-") for item in explicit.group(1).split("/")]
        if explicit
        else []
    )
    scoped_instruction = (
        bool(ids)
        and len(ids) == len(set(ids))
        and path.name[:9] in ids
        and all(len(list((root / "specs").glob(item + "-*.md"))) == 1 for item in ids)
    )
    if not (legacy_instruction or scoped_instruction):
        return blocked | {
            "reason": "explicit execution authorization required for this specification"
        }
    current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if current_hash != expected_hash:
        return blocked | {"reason": "verified specification hash is stale"}
    context = assess_delivery_spec_context(root, relative)
    if context["state"] != "confirmed" or context.get("selected_path") != relative:
        return blocked | {"reason": context["reason"]}
    turn = assess_delivery_turn_context(
        root, reference=working_reference, task_ref=task_ref
    )
    if turn["state"] not in {"absent", "ready"} or turn.get("conflicts"):
        return blocked | {
            "reason": "pending or invalid working specification",
            "turn_context": turn,
        }
    working = turn.get("working_spec")
    if working and working.get("continuity") != "continuous":
        return blocked | {"reason": "working specification audit continuity is invalid"}
    if working and working.get("validation_planning", {}).get("verdict") == "BLOCKED":
        return blocked | {
            "reason": "acceptance mapping requires reconciliation",
            "validation_planning": working["validation_planning"],
        }
    canonical = validate_spec_text(path.read_text(encoding="utf-8"))["canonical_spec"]
    if working and (
        working["spec_id"] != canonical["spec_id"]
        or working["status"] != "confirmed"
        or working["revision"] != canonical["revision"]
        or f"{working['spec_id']}-{working['change_set']}.md" != path.name
        or turn.get("canonical_matches") is not True
    ):
        return blocked | {
            "reason": "working and canonical specification identity/status mismatch"
        }
    dependencies = check_spec_dependencies(root, path)
    if dependencies:
        return blocked | {
            "reason": "prerequisite SPEC is not complete",
            "dependencies": dependencies,
            "unaffected_branches_suspended": False,
        }
    validation = assess_project_validation(
        root, relative, phase="enablement", validation_assessor=validation_assessor
    )
    if validation["verdict"] != "PASS":
        return blocked | {
            "reason": "project validation planning/enablement incomplete",
            "validation": validation,
        }
    return {
        "validation": validation,
        "verdict": "PASS",
        "product_code_allowed": True,
        "spec_path": relative,
        "spec_hash": current_hash,
        "enforcement_scope": "governed-delivery-only",
    }


def run_spec_cli(validation_assessor=None):
    """Coordinate the child specification CLI with a composition-provided port."""
    from spec_contract import main as spec_main

    return spec_main(validation_assessor=validation_assessor)


def main(validation_assessor=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", required=True)
    parser.add_argument("--expected-hash", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--working-reference")
    parser.add_argument("--task-ref")
    args = parser.parse_args()
    result = verify_delivery_admission(
        args.project_root,
        args.spec,
        expected_hash=args.expected_hash,
        authorization=args.authorization,
        working_reference=args.working_reference,
        task_ref=args.task_ref,
        validation_assessor=validation_assessor,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
