"""Managed single-file delivery with local receipt admission, not host interception."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "spec-governance/scripts"))

from discussion_state import discussion_request
from execution_state import (
    execution_binding,
    read_execution_state,
    write_execution_state,
)
from spec_contract import (
    assess_discussion_completion,
    project_state_lock,
    question_surface_policy,
)
from spec_delivery import assess_project_validation, verify_delivery_admission


def _blocked(reason: str) -> dict:
    return {
        "verdict": "BLOCKED",
        "product_code_allowed": False,
        "spec_discussion_allowed": True,
        "reason": reason,
        "enforcement_scope": "managed-entrypoint-only",
    }


def _admit(root: Path, request: dict, state: dict, validation_assessor=None) -> dict:
    discussion = discussion_request(
        root, {"operation": "resume", "task_ref": request["task_ref"]}
    )["state"]
    if discussion["active_turn"]:
        entry = discussion_request(
            root,
            {
                "operation": "status",
                "task_ref": request["task_ref"],
                "turn_id": discussion["active_turn"],
            },
        )
        if not entry.get("entry_saved") or entry["verdict"] != "PASS":
            raise ValueError(
                "matching discussion is not synchronized; save or repair the current SPEC"
            )
    receipt = state.get("receipts", {}).get(request["spec"], state.get("receipt"))
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
        validation_assessor=validation_assessor,
    )
    if not result["product_code_allowed"]:
        repairable = (
            request.get("operation") == "recover"
            and request.get("deterministic") is True
            and result.get("reason")
            in {
                "acceptance mapping requires reconciliation",
                "project validation planning/enablement incomplete",
            }
        )
        if not repairable:
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
        part.casefold() in {".git", ".codex", ".agents"} for part in path.parts
    ) or path.parts[0].casefold() in {"spec-governance", "specs"}:
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


def _merge_patch(base: str, desired: str, current: str) -> str:
    """Integrate disjoint line edits; overlapping edits require a reviewed patch."""
    base_lines = base.splitlines(keepends=True)

    def edits(text):
        lines = text.splitlines(keepends=True)
        return [
            (i, j, lines[x:y])
            for op, i, j, x, y in difflib.SequenceMatcher(
                None, base_lines, lines, autojunk=False
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
                    "overlapping file edits; reread and resolve affected write"
                )
        combined.append(edit)
    for a, b, replacement in sorted(
        combined, key=lambda item: (item[0], item[1]), reverse=True
    ):
        base_lines[a:b] = replacement
    return "".join(base_lines)


def _apply(
    root: Path,
    request: dict,
    state: dict,
    validation_assessor=None,
    candidate_validator=None,
) -> dict:
    patch = request["patch"]
    required = {"path", "before_sha256", "content"}
    if (
        not isinstance(patch, dict)
        or not required <= patch.keys()
        or set(patch) - required - {"before_content"}
    ):
        raise ValueError(
            "patch requires path, before_sha256, content and optional before_content"
        )
    if (
        not isinstance(patch["content"], str)
        or len(patch["content"].encode()) > 1048576
    ):
        raise ValueError("patch content must be UTF-8 text at most 1 MiB")
    base = patch.get("before_content")
    if base is not None and (
        not isinstance(base, str)
        or hashlib.sha256(base.encode()).hexdigest() != patch["before_sha256"]
    ):
        raise ValueError("before_content must match the reviewed base hash")
    for retry in range(3):
        _admit(
            root,
            request,
            read_execution_state(root, request["task_ref"]),
            validation_assessor,
        )
        target = _target(root, patch["path"])
        raw = target.read_bytes() if target.exists() else None
        before = hashlib.sha256(raw).hexdigest() if raw is not None else None
        content = patch["content"]
        if before != patch["before_sha256"]:
            if base is None or raw is None:
                raise ValueError(
                    "target hash differs from reviewed patch; reread and integrate"
                )
            content = _merge_patch(base, content, raw.decode("utf-8"))
        encoded = content.encode("utf-8")
        if len(encoded) > 1048576:
            raise ValueError("merged patch exceeds 1 MiB")
        merged = before != patch["before_sha256"]
        if merged:
            candidate = {
                "path": patch["path"],
                "before_sha256": before,
                "content": content,
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }
            if candidate_validator is None:
                return _blocked(
                    "merged content requires candidate validation before commit"
                ) | {
                    "reviewable_candidate": candidate,
                    "unaffected_branches_suspended": False,
                }
            validation = candidate_validator(root, dict(candidate))
            if (
                not isinstance(validation, dict)
                or validation.get("verdict") != "PASS"
                or validation.get("sha256") != candidate["sha256"]
            ):
                return _blocked("merged candidate validation failed or is stale") | {
                    "reviewable_candidate": candidate,
                    "candidate_validation": validation,
                    "unaffected_branches_suspended": False,
                }
        # Validate the current admission after integration and before committing.
        fresh = read_execution_state(root, request["task_ref"])
        binding = _admit(root, request, fresh, validation_assessor)
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(
                prefix=".governed-patch-", dir=target.parent
            )
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
            if target.exists():
                os.chmod(temporary, target.stat().st_mode)
            with (
                project_state_lock(root, "product-commit"),
                project_state_lock(root, "execution:" + request["task_ref"]),
            ):
                if (
                    _target(root, patch["path"]) != target
                    or _current_hash(target) != before
                ):
                    continue
                if (
                    read_execution_state(root, request["task_ref"]) != fresh
                    or execution_binding(
                        root,
                        request["spec"],
                        request["working_reference"],
                        request["task_ref"],
                    )
                    != binding
                ):
                    raise ValueError("authorization changed during admission")
                os.replace(temporary, target)
                temporary = None
            return {
                "verdict": "PASS",
                "product_code_allowed": True,
                "path": patch["path"],
                "before_sha256": before,
                "after_sha256": hashlib.sha256(encoded).hexdigest(),
                "integration_retries": retry,
                "merged": before != patch["before_sha256"],
                "enforcement_scope": "managed-entrypoint-only",
            }
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)
    return _blocked("file kept changing; pause affected write and reread") | {
        "unaffected_branches_suspended": False
    }


def _recover(
    root: Path,
    request: dict,
    state: dict,
    validation_assessor=None,
    candidate_validator=None,
) -> dict:
    """Keep bounded repair state beside the existing receipt, never grant authority."""
    binding = execution_binding(
        root, request["spec"], request["working_reference"], request["task_ref"]
    )
    diagnosis = request["diagnosis"]
    fields = {
        "category",
        "source",
        "evidence",
        "affected_scope",
        "repair_suggestion",
        "authorization",
        "recheck_command",
        "success_condition",
        "resume_target",
    }
    if not isinstance(diagnosis, dict) or fields - diagnosis.keys():
        raise ValueError("recovery requires a complete structured diagnosis")
    branch = request.get("branch")
    if not isinstance(branch, str) or not branch.strip():
        raise ValueError("recovery branch is required")
    recoveries = state.setdefault("recovery", {})
    if not isinstance(recoveries, dict):
        raise TypeError("invalid legacy recovery state; preserve it for investigation")
    previous = recoveries.get(branch)
    if previous and previous.get("binding") != binding:
        _admit(root, request, state, validation_assessor=validation_assessor)
        state.setdefault("recovery_history", []).append(
            {"branch": branch, "cycle": previous}
        )
        previous = None
    row = previous or {
        "binding": binding,
        "started_at": time.time(),
        "attempts": [],
        "diagnosis": diagnosis,
        "resume_target": diagnosis["resume_target"],
    }
    recoveries[branch] = row
    row["diagnosis"] = diagnosis
    patch = request.get("patch")
    recheck_phase = diagnosis.get("phase", "enablement")
    if recheck_phase not in {"planning", "enablement", "acceptance", "release"}:
        raise ValueError("unknown diagnosis recheck phase")
    known_check = diagnosis["source"] in {
        "test-validation-layout",
        "verification-ladder",
    }
    known_check = known_check and diagnosis["success_condition"] in {
        "layout verdict PASS",
        "project validation enablement PASS",
        "valid CLI result and passing required check",
    }
    if not known_check:
        row.update(
            status="investigate", next_action="resolve-diagnosis-specific-recheck"
        )
        write_execution_state(root, request["task_ref"], state)
        return _blocked(
            "no executable recheck is bound to this diagnosed condition"
        ) | {"recovery": row}
    if request.get("deterministic") is not True:
        row.update(status="needs-decision", next_action="resolve-ambiguous-repair")
        write_execution_state(root, request["task_ref"], state)
        return _blocked("repair method or acceptance threshold is not unambiguous") | {
            "recovery": row
        }
    try:
        _admit(root, request, state, validation_assessor=validation_assessor)
    except (ValueError, TypeError, KeyError) as exc:
        row.update(
            status="prepared", next_action="verify-existing-authority", repair=patch
        )
        write_execution_state(root, request["task_ref"], state)
        return _blocked(str(exc)) | {"recovery": row, "reviewable_repair": patch}
    inputs = {}
    policy_inputs = {
        path.relative_to(root).as_posix()
        for directory in (root / "validation", root / "architecture")
        if directory.is_dir()
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in {".json", ".yaml", ".yml"}
    }
    for relative in sorted(set(request.get("inputs", [])) | policy_inputs):
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("recovery input must be an existing project file")
        inputs[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "binding": binding,
                "inputs": inputs,
                "patch": patch,
                "check": diagnosis["source"],
                "phase": recheck_phase,
                "success_condition": diagnosis["success_condition"],
                "recheck_command": diagnosis["recheck_command"],
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    attempts = row["attempts"]
    repeated = any(item["fingerprint"] == fingerprint for item in attempts)
    if (
        row.get("status") == "resolved"
        and attempts
        and attempts[-1]["fingerprint"] == fingerprint
    ):
        return {
            "verdict": "PASS",
            "product_code_allowed": False,
            "spec_discussion_allowed": True,
            "recovery": row,
            "replayed": True,
        }
    if attempts and not repeated:
        row["started_at"] = time.time()
        row["cycle_start"] = len(attempts)
    transient = diagnosis["category"] in {"timeout", "process-launch-failure"} and bool(
        request.get("transient_reason")
    )
    if (
        len(attempts) - row.get("cycle_start", 0) >= 3
        or time.time() - row["started_at"] >= 120
        or (repeated and not transient)
    ):
        row.update(status="blocked", next_action="collect-new-evidence-or-repair")
        write_execution_state(root, request["task_ref"], state)
        return _blocked("recovery budget exhausted or identical failed inputs") | {
            "recovery": row
        }
    attempt = {
        "fingerprint": fingerprint,
        "inputs": inputs,
        "started_at": time.time(),
        "status": "started",
        "transient_reason": request.get("transient_reason"),
    }
    attempts.append(attempt)
    # Reserve before effects: process restart cannot silently repeat an interrupted repair.
    write_execution_state(root, request["task_ref"], state)
    try:
        if patch is not None:
            attempt["repair"] = _apply(
                root,
                request | {"patch": patch},
                state,
                validation_assessor,
                candidate_validator,
            )
            if attempt["repair"]["verdict"] != "PASS":
                raise ValueError(
                    "repair patch was not committed: "
                    + attempt["repair"].get("reason", "blocked")
                )
        checked = assess_project_validation(
            root,
            request["spec"],
            phase=recheck_phase,
            validation_assessor=validation_assessor,
        )
        attempt["recheck"] = checked
        required = (
            checked.get("layout")
            if diagnosis["source"] == "test-validation-layout"
            else checked
        )
        success = isinstance(required, dict) and required.get("verdict") == "PASS"
        success = success and time.time() - row["started_at"] < 120
        attempt["status"] = "PASS" if success else "BLOCKED"
        row.update(
            status="resolved" if success else "blocked",
            next_action=row["resume_target"] if success else "investigate-recheck",
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        attempt.update(status="BLOCKED", error=str(exc))
        row.update(status="blocked", next_action="investigate-recheck")
    write_execution_state(root, request["task_ref"], state)
    return {
        "verdict": "PASS" if row["status"] == "resolved" else "BLOCKED",
        "product_code_allowed": False,
        "spec_discussion_allowed": True,
        "recovery": row,
        "unaffected_branches_suspended": False,
    }


def execute_request(
    root: Path, request: dict, validation_assessor=None, candidate_validator=None
) -> dict:
    """Authorize, suspend, query or apply one reviewed replacement; deny on missing evidence."""
    root = root.resolve()
    try:
        if not isinstance(request, dict):
            raise TypeError("request must be an object")
        task = request["task_ref"]
        state = read_execution_state(root, task)
        operation = request["operation"]
        if operation == "recover":
            return _recover(
                root, request, state, validation_assessor, candidate_validator
            )
        if operation == "suspend":
            state.update(phase="suspended", receipt=None, receipts={})
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
                validation_assessor=validation_assessor,
            )
            if not admission["product_code_allowed"]:
                raise ValueError(admission.get("reason", "admission denied"))
            receipts = {
                request["spec"]: {
                    "binding": binding,
                    "instruction": request["instruction"],
                    "source_event_id": event,
                }
            }
            explicit_batch = re.fullmatch(
                r"開始執行\s*SPEC-(\d{4}(?:/(?:SPEC-)?\d{4})+)",
                request["instruction"].strip().replace("\\", "/"),
            )
            if explicit_batch and request.get("scope") is None:
                raise ValueError(
                    "combined execution instruction requires all reviewed SPEC bindings"
                )
            if request.get("scope") is not None:
                scope = request["scope"]
                explicit = re.fullmatch(
                    r"開始執行\s*SPEC-(\d{4}(?:/(?:SPEC-)?\d{4})*)",
                    request["instruction"].strip().replace("\\", "/"),
                )
                if not explicit or not isinstance(scope, list) or not scope:
                    raise ValueError(
                        "batch scope requires explicit SPEC IDs and reviewed bindings"
                    )
                ids = [
                    "SPEC-" + item.removeprefix("SPEC-")
                    for item in explicit.group(1).split("/")
                ]
                if len(scope) != len(ids) or {
                    Path(item["spec"]).name[:9] for item in scope
                } != set(ids):
                    raise ValueError(
                        "batch scope differs from the original execution instruction"
                    )
                for item in scope:
                    scoped = execution_binding(
                        root, item["spec"], item["working_reference"], task
                    )
                    checked = verify_delivery_admission(
                        root,
                        item["spec"],
                        expected_hash=item["expected_hash"],
                        authorization=request["instruction"],
                        working_reference=item["working_reference"],
                        task_ref=task,
                        validation_assessor=validation_assessor,
                    )
                    if (
                        not checked["product_code_allowed"]
                        or scoped["spec_hash"] != item["expected_hash"]
                    ):
                        raise ValueError(
                            "batch scope admission failed: " + str(checked)
                        )
                    receipts[item["spec"]] = {
                        "binding": scoped,
                        "instruction": request["instruction"],
                        "source_event_id": event,
                    }
            state["used_event_ids"].append(event)
            state.update(
                phase="executing",
                receipt={
                    "binding": binding,
                    "instruction": request["instruction"],
                    "source_event_id": event,
                },
                receipts=receipts,
            )
            write_execution_state(root, task, state)
            return admission | {
                "phase": "executing",
                "source_event_id": event,
                "evidence_trust": "caller-attested-not-host-authenticated",
            }
        if operation == "status":
            binding = _admit(
                root, request, state, validation_assessor=validation_assessor
            )
            return {
                "binding": binding,
                "verdict": "PASS",
                "phase": "executing",
                "product_code_allowed": True,
                "spec_discussion_allowed": True,
            }
        if operation == "complete":
            _admit(root, request, state, validation_assessor=validation_assessor)
            result = assess_project_validation(
                root,
                request["spec"],
                phase=request.get("phase", "acceptance"),
                validation_assessor=validation_assessor,
            )
            if request.get("phase", "acceptance") not in {"acceptance", "release"}:
                return _blocked("completion requires acceptance or release evidence")
            return result | {
                "product_code_allowed": False,
                "spec_discussion_allowed": True,
                "enforcement_scope": "managed-entrypoint-only",
            }
        if operation == "apply":
            return _apply(
                root,
                request,
                state,
                validation_assessor=validation_assessor,
                candidate_validator=candidate_validator,
            )
        raise ValueError("unknown managed operation")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return _blocked(str(exc))


def _audit_source_trace(packet: dict) -> dict:
    """Cross-check normalized observations with supplied raw desktop item records.

    Unknown command effects are incomplete evidence, never an inferred read.
    Source capture remains caller-attested rather than host-authenticated.
    """
    gaps = []
    violations = []
    sources = packet.get("sources")
    events = packet.get("events")
    root = packet.get("project_root")
    if (
        packet.get("schema_version") != 2
        or not isinstance(sources, list)
        or not sources
        or not isinstance(events, list)
        or not isinstance(root, str)
        or not root.strip()
    ):
        return {
            "verdict": "BLOCKED",
            "reason": "missing raw trace evidence",
            "enforcement_scope": "observed-trace-only",
        }
    root = root.replace("\\", "/").rstrip("/") + "/"
    by_id = {}
    for item in sources:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not item["id"]
            or item["id"] in by_id
        ):
            gaps.append("missing or duplicate raw source identity")
            continue
        by_id[item["id"]] = item
        if item.get("type") == "fileChange":
            changes = item.get("changes")
            if not isinstance(changes, list) or not changes:
                gaps.append("file change has no target evidence")
                continue
            for change in changes:
                path = change.get("path") if isinstance(change, dict) else None
                if not isinstance(path, str) or not path.replace("\\", "/").startswith(
                    root
                ):
                    gaps.append("file change outside observed project")
                    continue
                relative = path.replace("\\", "/")[len(root) :]
                parts = relative.split("/")
                if any(
                    not part
                    or part in {".", ".."}
                    or part != part.rstrip(" .")
                    or ":" in part
                    for part in parts
                ):
                    gaps.append(
                        "noncanonical raw target cannot establish governance-only writes"
                    )
                    continue
                if parts[0] not in {"specs", "spec-governance"}:
                    violations.append(
                        {
                            "source_ref": item["id"],
                            "reason": "raw direct product write bypasses managed entrypoint",
                            "path": path,
                        }
                    )
        elif item.get("type") == "commandExecution":
            # This bounded adapter does not parse arbitrary PowerShell/Python effects.
            gaps.append(
                "command effects require independently verified execution evidence: "
                + item["id"]
            )
        elif item.get("type") not in {"userMessage", "agentMessage", "reasoning"}:
            gaps.append("unsupported raw source type: " + str(item.get("type")))
    refs = set()
    positions = {ref: index for index, ref in enumerate(by_id)}
    last_position = -1
    for event in events:
        if not isinstance(event, dict):
            gaps.append("invalid normalized event")
            continue
        ref = event.get("source_ref")
        source = by_id.get(ref) if isinstance(ref, str) else None
        if source is None:
            gaps.append("normalized event has no raw source")
            continue
        refs.add(ref)
        if positions[ref] < last_position:
            violations.append(
                {
                    "source_ref": ref,
                    "reason": "normalized event order differs from raw source order",
                }
            )
        last_position = positions[ref]
        if (
            event.get("kind")
            in {"admission", "managed_write", "spec_saved", "context", "turn_start"}
            and source.get("type") != "commandExecution"
        ):
            gaps.append("tool state cannot be attested by a non-tool source")
        if event.get("kind") == "direct_write" and source.get("type") not in {
            "fileChange",
            "commandExecution",
        }:
            gaps.append("write observation requires a tool source")
        if event.get("kind") == "reply" and (
            source.get("type") != "agentMessage"
            or event.get("text") != source.get("text")
        ):
            violations.append(
                {"source_ref": ref, "reason": "reply differs from raw emitted message"}
            )
        if source.get("type") == "userMessage" and event.get("kind") not in {
            "requirement",
            "decision",
            "pause",
            "discussion_pause",
        }:
            gaps.append(
                "raw user decisions require explicit semantic classification; they cannot attest tools or be discarded as reads"
            )
    if set(by_id) - refs:
        gaps.append("unmapped raw sources")
    normalized = (
        audit_trace(events) if events else {"verdict": "BLOCKED", "violations": []}
    )
    violations.extend(normalized.get("violations", []))
    return {
        "verdict": "FAIL"
        if violations
        else "BLOCKED"
        if gaps or normalized["verdict"] != "PASS"
        else "PASS",
        "violations": violations,
        "missing_evidence": gaps,
        "enforcement_scope": "observed-trace-only",
        "evidence_trust": "caller-supplied-raw-records",
    }


def audit_trace(events: list[dict] | dict) -> dict:
    """Audit normalized observed tool events; missing evidence never proves compliance."""
    if isinstance(events, dict):
        return _audit_source_trace(events)
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
            if turn is not None and isinstance(observed.get("spec_presentation"), dict):
                observed["spec_presentation"] = {
                    **observed["spec_presentation"],
                    "reply_text": event.get("text"),
                    "stage": "emitted",
                    "source_ref": event.get("source_ref"),
                }
                continue
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
                proposal_presented=True,
                presentation_ref=event.get("presentation_ref"),
                spec_presentation={**event["spec_presentation"], "stage": "prepared"}
                if isinstance(event.get("spec_presentation"), dict)
                else None,
                execution=event.get("execution") if authorized else None,
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


def main(validation_assessor=None) -> int:
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
                args.project_root,
                json.loads(args.request.read_text(encoding="utf-8")),
                validation_assessor=validation_assessor,
            )
    except (OSError, ValueError, TypeError) as exc:
        result = _blocked(str(exc))
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
