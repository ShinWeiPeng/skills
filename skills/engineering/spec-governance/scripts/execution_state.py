"""Project-local execution receipts; caller evidence is not host authentication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from spec_contract import _atomic_write, assess_turn_context, project_state_lock


def execution_binding(
    root: Path, spec_path: str, working_reference: str, task_ref: str
) -> dict:
    """Bind an execution epoch to the actual project, task and current SPEC files."""
    if any(
        not isinstance(value, str) or not value.strip()
        for value in (spec_path, task_ref, working_reference)
    ):
        raise ValueError("SPEC path, task and working reference must be nonempty text")
    root = root.resolve()
    canonical = (root / spec_path).resolve()
    if canonical.parent != root / "specs" or not canonical.is_file():
        raise ValueError("canonical SPEC must be directly under project specs")
    context = assess_turn_context(root, reference=working_reference, task_ref=task_ref)
    if context["state"] != "ready" or context.get("canonical_matches") is not True:
        raise ValueError("working SPEC is not ready and matched")
    working = context["working_spec"]
    if canonical.name != f"{working['spec_id']}-{working['change_set']}.md":
        raise ValueError("canonical SPEC differs from working identity")
    journal = root / working["journal_path"]
    return {
        "project_root": str(root),
        "task_ref": task_ref,
        "spec_path": canonical.relative_to(root).as_posix(),
        "spec_hash": hashlib.sha256(canonical.read_bytes()).hexdigest(),
        "working_id": working["working_id"],
        "snapshot_hash": working["snapshot_hash"],
        "journal_hash": hashlib.sha256(journal.read_bytes()).hexdigest(),
    }


def _state_path(root: Path, task_ref: str) -> Path:
    if not isinstance(task_ref, str) or not task_ref.strip():
        raise ValueError("task reference is required")
    directory = root.resolve() / "spec-governance"
    if directory.is_symlink() or directory.resolve() != directory:
        raise ValueError("governance directory must not be redirected")
    name = hashlib.sha256(task_ref.encode()).hexdigest()
    path = directory / f"EXECUTION-{name}.json"
    if path.is_symlink():
        raise ValueError("execution receipt must not be a symlink")
    return path


def read_execution_state(root: Path, task_ref: str) -> dict:
    """Absent means discussion only; malformed existing evidence fails closed."""
    path = _state_path(root, task_ref)
    if not path.exists():
        return {
            "_loaded_sha256": None,
            "schema_version": 1,
            "phase": "discussion",
            "used_event_ids": [],
            "receipt": None,
        }
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or value.get("phase") not in {"discussion", "executing", "suspended"}
        or not isinstance(value.get("used_event_ids"), list)
        or any(not isinstance(item, str) for item in value["used_event_ids"])
        or (value.get("receipt") is not None and not isinstance(value["receipt"], dict))
    ):
        raise ValueError("invalid execution state")
    for field in ("receipts", "recovery"):
        if field in value and (
            not isinstance(value[field], dict)
            or any(not isinstance(item, dict) for item in value[field].values())
        ):
            raise ValueError("invalid " + field + " state; preserve for investigation")
    if "recovery_history" in value and (
        not isinstance(value["recovery_history"], list)
        or any(not isinstance(item, dict) for item in value["recovery_history"])
    ):
        raise ValueError("invalid recovery history; preserve for investigation")
    value["_loaded_sha256"] = hashlib.sha256(raw).hexdigest()
    return value


def write_execution_state(root: Path, task_ref: str, value: dict) -> None:
    """Compare and commit state under a short per-task lock, preserving newer writes."""
    path = _state_path(root, task_ref)
    with project_state_lock(root, "execution:" + task_ref):
        actual = (
            hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        )
        if value.get("_loaded_sha256") != actual:
            raise ValueError("execution state changed; reread and retry")
        text = (
            json.dumps(
                {k: v for k, v in value.items() if k != "_loaded_sha256"},
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        _atomic_write(path, text)
        value["_loaded_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
