"""Managed single-file delivery with local receipt admission, not host interception."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "spec-governance/scripts"))

from execution_state import (
    execution_binding,
    read_execution_state,
    write_execution_state,
)
from spec_contract import assess_discussion_completion, question_surface_policy
from spec_delivery import verify_delivery_admission


def _blocked(reason: str) -> dict:
    return {
        "verdict": "BLOCKED",
        "product_code_allowed": False,
        "spec_discussion_allowed": True,
        "reason": reason,
        "enforcement_scope": "managed-entrypoint-only",
    }


def _admit(root: Path, request: dict, state: dict) -> dict:
    receipt = state.get("receipt")
    if state["phase"] != "executing" or not isinstance(receipt, dict):
        raise ValueError("execution is not authorized or is suspended")
    if not isinstance(receipt.get("instruction"), str):
        raise TypeError("receipt execution instruction is invalid")
    binding = execution_binding(
        root, request["spec"], request["working_reference"], request["task_ref"]
    )
    if receipt.get("binding") != binding:
        raise ValueError("execution receipt is stale or belongs to another contract")
    result = verify_delivery_admission(
        root,
        request["spec"],
        expected_hash=binding["spec_hash"],
        authorization=receipt["instruction"],
        working_reference=request["working_reference"],
        task_ref=request["task_ref"],
    )
    if not result["product_code_allowed"]:
        raise ValueError(result.get("reason", "admission denied"))
    return binding


def _target(root: Path, relative: str) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or ":" in relative
    ):
        raise ValueError("target must be a portable relative path")
    path = Path(relative)
    if any(
        not part
        or part != part.rstrip(" .")
        or re.fullmatch(r"(?i)(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part)
        for part in relative.split("/")
    ):
        raise ValueError("target contains nonportable or Windows-normalized components")
    if path.is_absolute() or any(part in {".", ".."} for part in relative.split("/")):
        raise ValueError("target must stay within project")
    if any(
        part.casefold() in {".git", ".codex", ".agents", "spec-governance", "specs"}
        for part in path.parts
    ):
        raise ValueError(
            "managed product patches cannot alter governance control paths"
        )
    target = root / path
    for parent in [target, *target.parents]:
        if parent == root:
            break
        if parent.is_symlink() or (
            hasattr(parent, "is_junction") and parent.is_junction()
        ):
            raise ValueError("redirected targets are not supported")
    if not target.resolve().is_relative_to(root) or not target.parent.is_dir():
        raise ValueError("target parent must already exist within project")
    if target.exists() and (not target.is_file() or target.stat().st_nlink != 1):
        raise ValueError("target must be an ordinary unshared file")
    return target


def _current_hash(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def _apply(root: Path, request: dict, state: dict) -> dict:
    _admit(root, request, state)
    patch = request["patch"]
    if not isinstance(patch, dict) or set(patch) != {
        "path",
        "before_sha256",
        "content",
    }:
        raise ValueError("patch requires path, before_sha256 and content only")
    target = _target(root, patch["path"])
    if not isinstance(patch["content"], str):
        raise TypeError("patch content must be UTF-8 text")
    content = patch["content"].encode("utf-8")
    if len(content) > 1048576:
        raise ValueError("single-file patch exceeds 1 MiB")
    before = _current_hash(target)
    if patch["before_sha256"] != before:
        raise ValueError("target hash differs from reviewed patch")
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=".governed-patch-", dir=target.parent)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        if target.exists():
            os.chmod(temporary, target.stat().st_mode)
        _admit(root, request, read_execution_state(root, request["task_ref"]))
        if _target(root, patch["path"]) != target or _current_hash(target) != before:
            raise ValueError("target changed during admission")
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    return {
        "verdict": "PASS",
        "product_code_allowed": True,
        "path": patch["path"],
        "before_sha256": before,
        "after_sha256": hashlib.sha256(content).hexdigest(),
        "enforcement_scope": "managed-entrypoint-only",
    }


def execute_request(root: Path, request: dict) -> dict:
    """Authorize, suspend, query or apply one reviewed replacement; deny on missing evidence."""
    root = root.resolve()
    lock = root / "spec-governance" / ".managed-delivery.lock"
    acquired = False
    try:
        if not isinstance(request, dict):
            raise TypeError("request must be an object")
        task = request["task_ref"]
        state = read_execution_state(root, task)
        lock.parent.mkdir(exist_ok=True)
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        acquired = True
        state = read_execution_state(root, task)
        operation = request["operation"]
        if operation == "suspend":
            state.update(phase="suspended", receipt=None)
            write_execution_state(root, task, state)
            return {
                "verdict": "PASS",
                "phase": "suspended",
                "product_code_allowed": False,
                "spec_discussion_allowed": True,
            }
        if operation == "authorize":
            if not isinstance(request.get("instruction"), str):
                raise TypeError("execution instruction must be text")
            event = request["source_event_id"]
            if not isinstance(event, str) or not event.strip() or len(event) > 256:
                raise ValueError("source event ID is required")
            if event in state["used_event_ids"]:
                raise ValueError(
                    "source event was already used; require fresh user authorization"
                )
            binding = execution_binding(
                root, request["spec"], request["working_reference"], task
            )
            if request["expected_hash"] != binding["spec_hash"]:
                raise ValueError("reviewed specification hash is stale")
            admission = verify_delivery_admission(
                root,
                request["spec"],
                expected_hash=request["expected_hash"],
                authorization=request["instruction"],
                working_reference=request["working_reference"],
                task_ref=task,
            )
            if not admission["product_code_allowed"]:
                raise ValueError(admission.get("reason", "admission denied"))
            state["used_event_ids"].append(event)
            state.update(
                phase="executing",
                receipt={
                    "binding": binding,
                    "instruction": request["instruction"],
                    "source_event_id": event,
                },
            )
            write_execution_state(root, task, state)
            return admission | {
                "phase": "executing",
                "source_event_id": event,
                "evidence_trust": "caller-attested-not-host-authenticated",
            }
        if operation == "status":
            _admit(root, request, state)
            return {
                "verdict": "PASS",
                "phase": "executing",
                "product_code_allowed": True,
                "spec_discussion_allowed": True,
            }
        if operation == "apply":
            return _apply(root, request, state)
        raise ValueError("unknown managed operation")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return _blocked(str(exc))
    finally:
        if acquired:
            lock.unlink(missing_ok=True)


def audit_trace(events: list[dict]) -> dict:
    """Audit normalized observed tool events; missing evidence never proves compliance."""
    authorized = False
    pending_spec = False
    turn = None
    context = None
    observed = {}
    question_count = 0
    host = None
    violations = []
    if not isinstance(events, list) or any(
        not isinstance(event, dict) for event in events
    ):
        return {
            "verdict": "FAIL",
            "violations": [{"index": 0, "reason": "invalid trace"}],
            "enforcement_scope": "observed-trace-only",
        }
    for index, event in enumerate(events):
        kind = event.get("kind")
        if not isinstance(kind, str):
            violations.append({"index": index, "reason": "trace kind must be text"})
            continue
        if kind == "mode_change" and turn is not None:
            # Only a new host turn can establish an already-active Plan mode.
            host = None
            observed = {}
            continue
        if kind == "question_tool":
            record = (
                context.get("question_record", {})
                if isinstance(context, dict)
                else None
            )
            failed = (
                record.get("failed_surfaces", {}) if isinstance(record, dict) else None
            )
            if not isinstance(failed, dict):
                violations.append(
                    {"index": index, "reason": "invalid question failure evidence"}
                )
                continue
            if (
                turn is None
                or question_surface_policy(host, event.get("tool"), failed)["verdict"]
                != "PASS"
            ):
                violations.append(
                    {
                        "index": index,
                        "reason": "question tool forbidden by current mode",
                    }
                )
            continue
        if kind == "reply":
            if turn is None or not isinstance(observed.get("presentation"), dict):
                violations.append(
                    {"index": index, "reason": "reply missing question evidence"}
                )
            else:
                observed["presentation"] = {
                    **observed["presentation"],
                    "reply_text": event.get("text"),
                    "stage": "emitted",
                    "source_ref": event.get("source_ref"),
                }
            continue
        if kind == "turn_start":
            if turn is not None:
                violations.append(
                    {"index": index, "reason": "previous turn has no completion"}
                )
            turn = index
            authorized = False
            question_count = 0
            host = event.get("host")
            context = event.get("context")
            observed = {}
            if not isinstance(context, dict) or (
                not isinstance(context.get("working_spec"), dict)
                and context.get("state") not in ("invalid", "absent")
            ):
                violations.append(
                    {"index": index, "reason": "missing persisted turn context"}
                )
            continue
        if (
            kind
            in {
                "context",
                "discussion_pause",
                "blocker",
                "proposal_presented",
                "turn_end",
            }
            and turn is None
        ):
            violations.append(
                {"index": index, "reason": "discussion evidence outside a turn"}
            )
            continue
        if kind == "context" or (
            kind == "spec_saved" and turn is not None and event.get("verdict") == "PASS"
        ):
            fresh = event.get("context")
            if not isinstance(fresh, dict) or not isinstance(
                fresh.get("working_spec"), dict
            ):
                violations.append(
                    {"index": index, "reason": "missing reloaded context"}
                )
            elif not isinstance(context, dict) or not isinstance(
                context.get("working_spec"), dict
            ):
                violations.append(
                    {"index": index, "reason": "invalid original turn context"}
                )
            elif fresh.get("project_root") != context.get("project_root") or any(
                fresh["working_spec"].get(key) != context["working_spec"].get(key)
                for key in ("working_id", "task_ref")
            ):
                violations.append(
                    {"index": index, "reason": "cross-discussion context"}
                )
            else:
                context = fresh
                authorized = False
                observed = {}
            if kind == "context":
                continue
        if kind == "discussion_pause":
            observed["pause"] = event.get("pause")
            continue
        if kind == "blocker":
            observed["blocker"] = event.get("blocker")
            observed["context_error"] = event.get("context_error")
            continue
        if kind == "proposal_presented":
            observed.update(
                proposal_presented=True, presentation_ref=event.get("presentation_ref")
            )
            continue
        if kind == "turn_end":
            if "question_presented" in observed and (
                not isinstance(observed.get("presentation"), dict)
                or observed["presentation"].get("stage") != "emitted"
            ):
                violations.append(
                    {"index": index, "reason": "no observed emitted question reply"}
                )
            assessment = assess_discussion_completion(
                context,
                {
                    **observed,
                    "working_spec": context.get("working_spec")
                    if isinstance(context, dict)
                    else None,
                    "project_root": context.get("project_root")
                    if isinstance(context, dict)
                    else None,
                    "unreconciled_decision": pending_spec,
                },
            )
            if not assessment["can_end_turn"]:
                violations.append(
                    {
                        "index": index,
                        "reason": "premature discussion completion",
                        "next_action": assessment["next_action"],
                    }
                )
            turn = None
            context = None
            observed = {}
            continue
        if kind == "question" and turn is not None:
            question_count += 1
            if question_count > 1:
                violations.append(
                    {
                        "index": index,
                        "reason": "multiple decision questions in one turn",
                    }
                )
            presentation = event.get("presentation")
            if not isinstance(presentation, dict) or presentation.get("host") != host:
                violations.append(
                    {
                        "index": index,
                        "reason": "missing or mismatched host presentation evidence",
                    }
                )
            if isinstance(presentation, dict):
                presentation = {**presentation, "stage": "prepared"}
            observed.update(
                presentation=presentation,
                question_presented=event.get("question"),
                presentation_ref=event.get("presentation_ref"),
            )
        if kind in {"requirement", "decision"}:
            authorized = False
            pending_spec = True
        elif kind == "pause":
            authorized = False
        elif kind == "spec_saved":
            authorized = False
            if event.get("verdict") == "PASS":
                pending_spec = False
        elif kind == "admission":
            authorized = (
                event.get("product_code_allowed") is True
                and event.get("verdict") == "PASS"
                and not pending_spec
            )
        elif kind == "direct_write":
            violations.append(
                {"index": index, "reason": "direct tool bypasses managed entrypoint"}
            )
        elif kind == "managed_write":
            if not authorized or event.get("verdict") != "PASS":
                violations.append(
                    {
                        "index": index,
                        "reason": "write without current observed admission",
                    }
                )
        elif kind == "gate_and_write":
            violations.append(
                {
                    "index": index,
                    "reason": "dependent write composed before gate result observed",
                }
            )
        elif kind == "question" and pending_spec:
            violations.append(
                {
                    "index": index,
                    "reason": "question before discussion decision was persisted",
                }
            )
        elif kind not in {"read", "question", "timeout", "mode_change"}:
            violations.append({"index": index, "reason": "unknown trace event"})
    if turn is not None:
        violations.append(
            {"index": len(events), "reason": "missing observed turn completion"}
        )
    if pending_spec:
        violations.append(
            {"index": len(events), "reason": "discussion decision not persisted"}
        )
    if not events:
        violations.append({"index": 0, "reason": "no observed evidence"})
    return {
        "verdict": "FAIL" if violations else "PASS",
        "violations": violations,
        "enforcement_scope": "observed-trace-only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--request", type=Path)
    parser.add_argument("--audit-trace", type=Path)
    args = parser.parse_args()
    try:
        if bool(args.request) == bool(args.audit_trace):
            raise ValueError("supply exactly one request or audit trace")
        if args.audit_trace:
            result = audit_trace(
                json.loads(args.audit_trace.read_text(encoding="utf-8"))
            )
        else:
            result = execute_request(
                args.project_root, json.loads(args.request.read_text(encoding="utf-8"))
            )
    except (OSError, ValueError, TypeError) as exc:
        result = _blocked(str(exc))
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
