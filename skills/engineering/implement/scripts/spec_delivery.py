#!/usr/bin/env python3
"""Delivery-owned adapter for canonical specification context."""

from __future__ import annotations

import sys
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SKILLS_ROOT = Path(__file__).resolve().parents[2]
SPEC_SCRIPTS_ROOT = SKILLS_ROOT / "spec-governance" / "scripts"
if str(SPEC_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SPEC_SCRIPTS_ROOT))

from spec_contract import resolve_spec_context, assess_turn_context, validate_spec_text


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
    if not re.fullmatch(
        r"開始執行(?:\s+" + re.escape(relative) + r")?",
        authorization.strip().replace("\\", "/"),
    ):
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
    return {
        "verdict": "PASS",
        "product_code_allowed": True,
        "spec_path": relative,
        "spec_hash": current_hash,
        "enforcement_scope": "governed-delivery-only",
    }


def main() -> int:
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
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
