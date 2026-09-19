"""Durable discussion obligations owned by spec governance, independent of execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from spec_contract import (
    REQUIRED_SECTIONS,
    _append_journal_event,
    _atomic_write,
    _migrate_flat_bundle,
    _read_journal,
    _redact_sensitive_content,
    _replace_metadata,
    _contract_completeness_gaps,
    _snapshot_rows,
    assess_turn_context,
    materialize_working_bundle,
    resolve_working_bundle,
    start_working_bundle,
)

MAX_TEXT = 32768


def _text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT:
        raise ValueError(f"{name} must be nonempty bounded text")
    return value


def _hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _paths(root, task):
    _text(task, "task_ref")
    root = root.resolve(strict=True)
    directory = root / "spec-governance"
    if directory.is_symlink() or directory.resolve() != directory:
        raise ValueError("discussion store must not be redirected")
    directory.mkdir(exist_ok=True)
    path = directory / f"DISCUSSION-{_hash(task)}.json"
    if path.is_symlink() or (path.exists() and path.stat().st_nlink != 1):
        raise ValueError("discussion state must be an ordinary unshared file")
    return path, path.with_suffix(".lock")


def _load(path, task):
    if not path.exists():
        return {"schema_version": 2, "task_ref": task, "active_turn": None, "turns": {}}
    state = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(state, dict)
        or state.get("schema_version") not in {1, 2}
        or state.get("task_ref") != task
        or not isinstance(state.get("turns"), dict)
    ):
        raise ValueError("invalid discussion state; do not reset the repair allowance")
    legacy = state["schema_version"] == 1
    for row in state["turns"].values():
        if (
            not isinstance(row, dict)
            or type(row.get("repair_used")) is not bool
            or not isinstance(row.get("aliases"), list)
            or row.get("kind") not in {"unknown", "engineering", "non-engineering"}
            or not isinstance(row.get("prompt"), str)
            or not isinstance(row.get("turn_id"), str)
            or any(not isinstance(alias, str) for alias in row["aliases"])
        ):
            raise ValueError("invalid persisted turn obligation")
        if legacy:
            row["legacy_repair"] = {
                "repair_used": row["repair_used"],
                "repair_failed": row.get("repair_failed", False),
            }
            row["repair_keys"] = (
                [_repair_input(path.parent.parent, task, row)]
                if row["repair_used"]
                else []
            )
        if not isinstance(row.get("repair_keys"), list) or any(
            not isinstance(key, str) for key in row["repair_keys"]
        ):
            raise ValueError("invalid repair input history")
        if row["repair_used"] and not row["repair_keys"]:
            raise ValueError("consumed repair has no input history")
    state["schema_version"] = 2
    if (
        state.get("active_turn") is not None
        and state["active_turn"] not in state["turns"]
    ):
        raise ValueError("active discussion turn is missing")
    return state


def _working(root, task, row):
    context = assess_turn_context(root, reference=row.get("working_id"), task_ref=task)
    working = context.get("working_spec")
    if (
        not working
        or working.get("task_ref") != task
        or working.get("continuity") != "continuous"
    ):
        raise ValueError("matching continuous working pair is unavailable")
    return working


def _append(root, working, record):
    path = root / working["journal_path"]
    if path.is_symlink() or path.stat().st_nlink != 1:
        raise ValueError("journal must be an ordinary unshared file")
    return _append_journal_event(
        path,
        event_type="discussion",
        working_id=working["working_id"],
        revision=working["revision"],
        previous_snapshot_hash=working["snapshot_hash"],
        snapshot_hash=working["snapshot_hash"],
        continuity="continuous",
        verdict="PASS",
        delta={
            "added_ids": [],
            "changed_ids": [],
            "removed_ids": [],
            "discussion": record,
        },
    )


def _enter_engineering(root, task, row):
    resolved = resolve_working_bundle(
        root, reference=row.get("working_id"), task_ref=task
    )
    if (
        not row.get("working_id")
        and resolved["state"] == "working"
        and resolved["working_spec"].get("task_ref") != task
    ):
        resolved = {"state": "absent"}
    if resolved["state"] == "absent":
        slug = "discussion-" + _hash(task)[:12]
        sections = {name: "None." for name in REQUIRED_SECTIONS}
        sections["problem"] = _redact_sensitive_content(row["prompt"])
        sections["solution"] = "Discussion only. No adopted change contract yet."
        sections["discussion context"] = "Entry source: " + row["source_ref"]
        text = (
            "---\nspec_version: 1\nspec_id: SPEC-0000\nrevision: 1\n"
            "status: working\nchange_set: "
            + slug
            + "\n---\n# Engineering discussion\n\n"
        )
        text += (
            "\n\n".join(
                "## " + name.title() + "\n" + content
                for name, content in sorted(sections.items())
            )
            + "\n"
        )
        result = start_working_bundle(root, slug, text, task_ref=task)
        if result["verdict"] != "PASS":
            raise ValueError(str(result))
        row["working_id"] = result["working_spec"]["working_id"]
    elif resolved["state"] == "working":
        row["working_id"] = resolved["working_spec"]["working_id"]
    else:
        raise ValueError(resolved.get("reason", "ambiguous working pair"))
    working = _working(root, task, row)
    if working["snapshot_path"] != working["journal_path"]:
        migrated = _migrate_flat_bundle(root, working["working_id"])
        if migrated["verdict"] != "PASS":
            raise ValueError(
                "legacy discussion migration requires repair: " + str(migrated)
            )
        working = migrated["working_spec"]
    _append(
        root,
        working,
        {
            "kind": "entry",
            "task_ref": task,
            "turn_id": row["turn_id"],
            "source_ref": row["source_ref"],
            "goal": _redact_sensitive_content(row["prompt"]),
            "historical_entry_evidence": "not-inferred",
        },
    )
    row["kind"] = "engineering"
    row["entry"] = {k: working[k] for k in ("working_id", "revision", "snapshot_hash")}
    return working


def _binding(root, task, row):
    working = _working(root, task, row)
    return {k: working[k] for k in ("working_id", "revision", "snapshot_hash")}


def _saved(root, task, row, reply=None):
    if row["kind"] == "non-engineering":
        return True
    saved = row.get("saved")
    if row["kind"] != "engineering" or not isinstance(saved, dict):
        return False
    if saved.get("task_ref") != task or saved.get("turn_id") != row["turn_id"]:
        return False
    if saved["binding"] != _binding(root, task, row):
        return False
    working = _working(root, task, row)
    events, continuity = _read_journal(root / working["journal_path"])
    if continuity != "continuous" or not any(
        e.get("event_hash") == saved["event_hash"]
        and e.get("delta", {}).get("discussion")
        == {k: v for k, v in saved.items() if k != "event_hash"}
        for e in events
    ):
        return False
    # Reply wording is audit evidence, not a requirement-synchronization gate.
    return True


def _repair_input(root, task, row):
    try:
        binding = _binding(root, task, row) if row["kind"] == "engineering" else None
    except (OSError, ValueError):
        binding = None
    return _hash(
        json.dumps(
            {
                "binding": binding,
                "prompts": row.get("prompt_hashes", [_hash(row["prompt"])]),
                "kind": row["kind"],
                "owner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            },
            sort_keys=True,
        )
    )


def _operate(root, state, request):
    task = state["task_ref"]
    operation = request["operation"]
    if operation == "resume":
        return {
            "verdict": "PASS",
            "state": state,
            "historical_entry_evidence": "not-inferred",
        }
    turn = _text(request.get("turn_id"), "turn_id")
    active = state["turns"].get(state["active_turn"])
    if operation == "enter":
        prompt = _text(request.get("prompt"), "prompt")
        if active and active.get("repair_prompt") == prompt:
            if turn not in active["aliases"]:
                active["aliases"].append(turn)
            return {
                "verdict": "PASS",
                "original_turn": active["turn_id"],
                "repair_used": True,
            }
        existing = [r for r in state["turns"].values() if turn in r["aliases"]]
        if existing:
            row = existing[0]
            redacted = _redact_sensitive_content(prompt)
            seen = row.setdefault("prompt_hashes", [_hash(row["prompt"])])
            if _hash(redacted) not in seen:
                update = {
                    "kind": "entry-update",
                    "task_ref": task,
                    "turn_id": row["turn_id"],
                    "source_ref": _text(request.get("source_ref"), "source_ref"),
                    "goal": redacted,
                }
                row.setdefault("additional_prompts", []).append(update)
                seen.append(_hash(redacted))
                row["saved"] = None
                if row["kind"] == "engineering":
                    _append(root, _working(root, task, row), update)
            if request.get("engineering") is True and existing[0]["kind"] == "unknown":
                _enter_engineering(root, task, existing[0])
            return {
                "verdict": "PASS",
                "original_turn": existing[0]["turn_id"],
                "replayed": True,
            }
        row = {
            "turn_id": turn,
            "aliases": [turn],
            "source_ref": _text(request.get("source_ref"), "source_ref"),
            "prompt": _redact_sensitive_content(prompt),
            "kind": "unknown",
            "repair_used": False,
            "repair_keys": [],
            "saved": None,
        }
        if request.get("working_reference"):
            row["working_id"] = _text(request["working_reference"], "working_reference")
        state["turns"][turn] = row
        state["active_turn"] = turn
        if request.get("engineering") is True:
            _enter_engineering(root, task, row)
        return {
            "verdict": "PASS",
            "original_turn": turn,
            "kind": row["kind"],
            "working_id": row.get("working_id"),
        }
    matches = [r for r in state["turns"].values() if turn in r["aliases"]]
    if len(matches) != 1:
        raise ValueError(
            "missing or ambiguous original-turn obligation; resume cannot reset it"
        )
    row = matches[0]
    if row["turn_id"] != state["active_turn"]:
        raise ValueError("only the active original turn can admit dependent operations")
    if operation == "classify":
        kind = request.get("kind")
        if kind not in {"engineering", "non-engineering"}:
            raise ValueError("explicit engineering classification is required")
        _text(request.get("reason"), "reason")
        if kind == "engineering" and row["kind"] != kind:
            _enter_engineering(root, task, row)
        elif kind == "non-engineering":
            if row["kind"] == "engineering":
                raise ValueError("an established engineering turn cannot be exempted")
            row["kind"] = kind
            row["classification_reason"] = request["reason"]
        return {
            "verdict": "PASS",
            "kind": row["kind"],
            "working_id": row.get("working_id"),
        }
    if operation == "record":
        if row["kind"] != "engineering":
            raise ValueError("classify the engineering discussion before saving")
        working = _working(root, task, row)
        if request.get("binding") != _binding(root, task, row):
            raise ValueError("stale or mismatched working binding")
        summary = _redact_sensitive_content(_text(request.get("summary"), "summary"))
        source = _text(request.get("source_ref"), "source_ref")
        reply = _text(request.get("reply_text"), "reply_text")
        candidates = request.get("candidates", [])
        if not isinstance(candidates, list):
            raise ValueError("candidates must be a list")
        for candidate in candidates:
            if not isinstance(candidate, dict) or candidate.get("status") not in {
                "candidate",
                "accepted",
                "rejected",
                "deferred",
            }:
                raise ValueError("invalid candidate state")
            allowed = {
                "id",
                "status",
                "source_ref",
                "reason",
                "impact",
                "user_source_ref",
                "reconciliation_ref",
            }
            if set(candidate) - allowed:
                raise ValueError(
                    "unsupported candidate fields; save only bounded contract fields"
                )
            for field in candidate:
                _text(candidate[field], "candidate." + field)
            for field in ("id", "source_ref", "reason", "impact"):
                _text(candidate.get(field), "candidate." + field)
            if candidate["status"] != "candidate":
                _text(candidate.get("user_source_ref"), "candidate.user_source_ref")
            if candidate["status"] == "accepted":
                _text(
                    candidate.get("reconciliation_ref"), "candidate.reconciliation_ref"
                )
        candidates = [
            {
                key: _redact_sensitive_content(value)
                if isinstance(value, str)
                else value
                for key, value in candidate.items()
            }
            for candidate in candidates
        ]
        source = _redact_sensitive_content(source)
        completeness = request.get("completeness_review")
        if completeness is not None:
            if not isinstance(completeness, dict) or set(completeness) != {
                "goal",
                "scope",
                "behavior",
                "exceptions",
                "acceptance",
            }:
                raise ValueError(
                    "completeness review requires all five contract dimensions"
                )
            normalized_review = {}
            for dimension, evidence in completeness.items():
                if not isinstance(evidence, dict) or set(evidence) != {
                    "source_ref",
                    "evidence",
                }:
                    raise ValueError(
                        "completeness review requires source_ref and evidence"
                    )
                normalized_review[dimension] = {
                    key: _redact_sensitive_content(_text(value, "completeness." + key))
                    for key, value in evidence.items()
                }
            completeness = normalized_review
        confirmation = None
        if (
            working["snapshot_path"] == working["journal_path"]
            and working["status"] == "working"
        ):
            text = (root / working["snapshot_path"]).read_text(encoding="utf-8")
            adopted = any(key.startswith("REQ-") for key in _snapshot_rows(text))
            accepted = any(key.startswith("AC-") for key in _snapshot_rows(text))
            review = completeness or {}
            reviewed = isinstance(review, dict) and all(
                isinstance(review.get(field), dict)
                and isinstance(review[field].get("source_ref"), str)
                and bool(review[field]["source_ref"].strip())
                and isinstance(review[field].get("evidence"), str)
                and bool(review[field]["evidence"].strip())
                for field in ("goal", "scope", "behavior", "exceptions", "acceptance")
            )
            if (
                adopted
                and accepted
                and reviewed
                and not _contract_completeness_gaps(
                    root, _replace_metadata(text, status="confirmed")
                )
            ):
                confirmation = materialize_working_bundle(
                    root,
                    working["working_id"],
                    expected_revision=working["revision"],
                    expected_hash=working["snapshot_hash"],
                )
                if confirmation["verdict"] != "PASS":
                    raise ValueError(
                        "completed contract could not be confirmed: "
                        + str(confirmation)
                    )
                working = confirmation["working_spec"]
        record = {
            "completeness_review": completeness,
            "kind": "saved",
            "task_ref": task,
            "turn_id": row["turn_id"],
            "source_ref": source,
            "summary": summary,
            "candidates": candidates,
            "reply_sha256": _hash(reply),
            "reply_stage": "prepared-until-host-stop",
            "binding": {
                k: working[k] for k in ("working_id", "revision", "snapshot_hash")
            },
        }
        event = _append(root, working, record)
        row["saved"] = {**record, "event_hash": event["event_hash"]}
        return {
            "verdict": "PASS",
            "binding": record["binding"],
            "event_hash": event["event_hash"],
            "product_code_allowed": False,
            "confirmation": confirmation,
        }
    if operation in {"status", "verify"}:
        try:
            saved = _saved(
                root,
                task,
                row,
                request.get("reply_text") if operation == "verify" else None,
            )
            binding = (
                _binding(root, task, row) if row["kind"] == "engineering" else None
            )
        except ValueError as exc:
            return {
                "verdict": "BLOCKED",
                "reason": str(exc),
                "sync_status": "unverifiable",
                "discussion_allowed": True,
                "repair_used": row["repair_used"],
            }
        return {
            "verdict": "PASS" if saved else "BLOCKED",
            "sync_status": "synced" if saved else "pending",
            "discussion_allowed": True,
            "binding": binding,
            "kind": row["kind"],
            "entry_saved": binding is not None
            and (row.get("entry") == binding or saved),
            "original_turn": row["turn_id"],
            "repair_used": row["repair_used"],
        }
    if operation == "stop":
        try:
            saved = _saved(root, task, row, request.get("reply_text", ""))
        except (OSError, ValueError):
            saved = False
        if saved:
            return {
                "verdict": "PASS",
                "continue": True,
                "saved": True,
                "original_turn": row["turn_id"],
            }
        # The key excludes turn IDs, reply wording and audit-only appends.
        # A changed actual SPEC/runtime may be rechecked; replay is not repair.
        repair_key = _repair_input(root, task, row)
        keys = row.setdefault("repair_keys", [])
        consumed = any(
            repair_key in prior.get("repair_keys", [])
            for prior in state["turns"].values()
        )
        if consumed or request.get("stop_hook_active") is True:
            if repair_key not in keys:
                keys.append(repair_key)
            row["repair_failed"] = True  # history only; never bars record/classify
            return {
                "verdict": "BLOCKED",
                "sync_status": "pending",
                "continue": True,
                "discussion_allowed": True,
                "auto_repair_allowed": False,
                "reason": "Discussion remains unsaved for turn "
                + row["turn_id"]
                + ". Automatic replay stopped; report the missing scope. Discussion, saving and rechecking remain available.",
            }
        keys.append(repair_key)
        row["repair_used"] = True  # retained as historical evidence
        row["repair_prompt"] = (
            "[discussion-repair:"
            + uuid4().hex
            + "] Save the actual discussion for original turn "
            + row["turn_id"]
            + " using spec-governance discussion_state.py. Classify engineering if unresolved; "
            "save sourced summary with current binding; final reply wording is audit only. Do not invent decisions, adopt candidates, "
            "authorize implementation or repeat unchanged failures. If this fails report unsaved scope and finish normally; saving and repair remain available."
        )
        return {
            "verdict": "BLOCKED",
            "decision": "block",
            "reason": row["repair_prompt"],
        }
    raise ValueError("unsupported discussion operation")


def discussion_request(root: Path, request: dict) -> dict:
    """Serialize all task operations; durable repair consumption precedes continuation."""
    root = root.resolve(strict=True)
    path, lock = _paths(root, request["task_ref"])
    if lock.is_symlink() or (lock.exists() and lock.stat().st_nlink != 1):
        raise ValueError("discussion lock must not be redirected or shared")
    # Kernel locks are released on process termination; a leftover file is harmless.
    with lock.open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = _load(path, request["task_ref"])
        try:
            result = _operate(root, state, request)
        except (OSError, ValueError, KeyError, TypeError):
            row = state["turns"].get(state["active_turn"], {})
            if row.get("repair_used") and request.get("operation") in {
                "record",
                "classify",
            }:
                row["repair_failed"] = True
                _atomic_write(
                    path, json.dumps(state, ensure_ascii=False, indent=2) + "\n"
                )
            raise
        _atomic_write(path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        with path.open("r+b") as persisted:
            os.fsync(persisted.fileno())
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = discussion_request(
            args.project_root, json.loads(args.request.read_text(encoding="utf-8-sig"))
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {
            "verdict": "BLOCKED",
            "reason": str(exc),
            "product_code_allowed": False,
        }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
