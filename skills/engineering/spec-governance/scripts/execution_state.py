"""Project-local execution receipts; caller evidence is not host authentication."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from document_bundle import (
    read_spec_document,
    read_spec_bytes,
    spec_hash,
    design_binding,
)

from spec_contract import (
    _atomic_write,
    _normalized_json,
    _read_journal,
    _split_spec_audit,
    assess_project_validation,
    assess_turn_context,
    project_state_lock,
)


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
    events, continuity = _read_journal(journal)
    if continuity != "continuous":
        raise ValueError("execution requires continuous discussion history")
    return {
        "project_root": str(root),
        "task_ref": task_ref,
        "spec_path": canonical.relative_to(root).as_posix(),
        "spec_hash": spec_hash(canonical),
        "design_set_hash": design_binding(canonical),
        "working_id": working["working_id"],
        "snapshot_hash": working["snapshot_hash"],
        "journal_hash": hashlib.sha256(read_spec_bytes(journal)).hexdigest(),
        "journal_tip": events[-1]["event_hash"] if journal == canonical else None,
    }


def execution_binding_matches(root: Path, previous: dict, current: dict) -> bool:
    """Accept only unchanged bindings or a verified discussion-only extension."""
    if (
        isinstance(previous, dict)
        and "design_set_hash" not in previous
        and current.get("design_set_hash") is None
    ):
        previous = previous | {"design_set_hash": None}
    if previous == current:
        return True
    if isinstance(previous, dict) and "journal_tip" not in previous:
        if previous == {k: v for k, v in current.items() if k != "journal_tip"}:
            return True
        tip = _legacy_binding_tip(root, previous, current)
        if tip is None:
            return False
        previous = previous | {"journal_tip": tip}
    if not isinstance(previous, dict) or not previous.get("journal_tip"):
        return False
    variable = {"spec_hash", "journal_hash", "journal_tip"}
    if {k: v for k, v in previous.items() if k not in variable} != {
        k: v for k, v in current.items() if k not in variable
    }:
        return False
    events, continuity = _read_journal(root / current["spec_path"])
    if continuity != "continuous" or events[-1]["event_hash"] != current["journal_tip"]:
        return False
    anchors = [
        i
        for i, event in enumerate(events)
        if event["event_hash"] == previous["journal_tip"]
    ]
    if len(anchors) != 1:
        return False
    extension = events[anchors[0] + 1 :]
    return bool(extension) and all(
        event.get("event_type") == "discussion"
        and event.get("working_id") == current["working_id"]
        and event.get("snapshot_hash") == current["snapshot_hash"]
        and event.get("previous_snapshot_hash") == current["snapshot_hash"]
        and not event.get("affected_ids")
        and not event.get("conflicts")
        and not event.get("open_decisions")
        for event in extension
    )


def preparation_contract_hash(root: Path, spec_path: str) -> str:
    """Bind pending preparation to all authored content except lifecycle status."""
    body, _ = _split_spec_audit(read_spec_document(root / spec_path))
    body = re.sub(
        r"(?m)^status: (working|confirmed)$", "status: preparation", body, count=1
    )
    designs = design_binding(root / spec_path)
    if designs is not None:
        body += "\nfixed-designs:" + designs
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _preparation_proof_matches(root: Path, application: dict, current: dict) -> bool:
    """Verify original bytes and the exact owner-derived transition, never ID deltas."""
    from spec_contract import (
        _mapping_preparation_plan,
        _validate_preparation_baseline,
        _mapping_candidate_matches,
        _snapshot_hash,
        _replace_metadata,
    )

    proof = application.get("preparation_proof")
    if not isinstance(proof, dict) or proof.get("rule_version") not in {1, 2}:
        return False
    previous = application.get("binding", {})
    try:
        data = bytes.fromhex(proof["original_document_hex"])
        original = data.decode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        if digest != previous["spec_hash"] or digest != previous["journal_hash"]:
            return False
        if _snapshot_hash(original) != previous["snapshot_hash"]:
            return False
        variable = {"spec_hash", "journal_hash", "journal_tip", "snapshot_hash"}
        if {k: v for k, v in previous.items() if k not in variable} != {
            k: v for k, v in current.items() if k not in variable
        }:
            return False
        _validate_preparation_baseline(
            root, application.get("preparation_validation_baseline")
        )
        planned = _mapping_preparation_plan(root, original)
        if any(
            proof.get(k) != planned[k] for k in ("inputs", "additions", "rule_version")
        ):
            return False
        candidate = proof.get("candidate")
        if not isinstance(candidate, str) or not _mapping_candidate_matches(
            root, planned["candidate"], candidate
        ):
            return False
        working_hash = _snapshot_hash(candidate)
        confirmed_hash = _snapshot_hash(
            _replace_metadata(candidate, status="confirmed")
        )
        events, continuity = _read_journal(root / current["spec_path"])
        if (
            continuity != "continuous"
            or events[-1]["event_hash"] != current["journal_tip"]
        ):
            return False
        anchors = [
            i
            for i, e in enumerate(events)
            if e["event_hash"] == previous["journal_tip"]
        ]
        if len(anchors) != 1:
            return False
        suffix = events[anchors[0] + 1 :]
        snapshot = previous["snapshot_hash"]
        reconciled = confirmed = False
        for event in suffix:
            permitted_ids = (
                {key.split(".")[0] for key in planned["additions"]}
                if proof["rule_version"] == 2
                else set()
            )
            if (
                event.get("working_id") != current["working_id"]
                or set(event.get("affected_ids", [])) - permitted_ids
                or event.get("conflicts")
                or event.get("open_decisions")
            ):
                return False
            if event.get("previous_snapshot_hash") != snapshot:
                return False
            kind = event.get("event_type")
            if kind == "reconcile" and not reconciled and not confirmed:
                reconciled = True
                snapshot = working_hash
            elif kind == "materialize" and reconciled and not confirmed:
                confirmed = True
                snapshot = confirmed_hash
            elif kind != "discussion":
                return False
            if event.get("snapshot_hash") != snapshot:
                return False
        return reconciled and snapshot == current["snapshot_hash"]
    except (ValueError, TypeError, KeyError, OSError):
        return False


def preparation_binding_matches(root: Path, application: dict, current: dict) -> bool:
    """Permit only a pending grant's unchanged, audited confirmation transition."""
    if _preparation_proof_matches(root, application, current):
        return True
    previous = application.get("binding")
    if execution_binding_matches(root, previous, current):
        return True
    if not isinstance(previous, dict) or not previous.get("journal_tip"):
        return False
    variable = {"spec_hash", "journal_hash", "journal_tip", "snapshot_hash"}
    if {k: v for k, v in previous.items() if k not in variable} != {
        k: v for k, v in current.items() if k not in variable
    }:
        return False
    if application.get("preparation_contract_hash") != preparation_contract_hash(
        root, current["spec_path"]
    ):
        return False
    events, continuity = _read_journal(root / current["spec_path"])
    anchors = [
        i
        for i, event in enumerate(events)
        if event["event_hash"] == previous["journal_tip"]
    ]
    if (
        continuity != "continuous"
        or len(anchors) != 1
        or events[-1]["event_hash"] != current["journal_tip"]
    ):
        return False
    suffix = events[anchors[0] + 1 :]
    return (
        bool(suffix)
        and sum(e.get("event_type") == "materialize" for e in suffix) == 1
        and all(
            e.get("event_type") in {"discussion", "materialize"}
            and not e.get("affected_ids")
            and not e.get("conflicts")
            and not e.get("open_decisions")
            for e in suffix
        )
    )


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
    raw = read_spec_bytes(path)
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
    for field in (
        "receipts",
        "recovery",
        "pending_authorizations",
        "fulfilled_authorizations",
        "acceptance_repairs",
        "acceptance_drafts",
        "continuations",
        "superseded_authorizations",
    ):
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
    for field in ("authorization_history", "acceptance_repair_history"):
        if field in value and (
            not isinstance(value[field], list)
            or any(not isinstance(row, dict) for row in value[field])
        ):
            raise ValueError("invalid " + field + "; preserve for investigation")
    value["_loaded_sha256"] = hashlib.sha256(raw).hexdigest()
    return value


def write_execution_state(root: Path, task_ref: str, value: dict) -> None:
    """Compare and commit state under a short per-task lock, preserving newer writes."""
    path = _state_path(root, task_ref)
    with project_state_lock(root, "execution:" + task_ref):
        actual = (
            hashlib.sha256(read_spec_bytes(path)).hexdigest() if path.exists() else None
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
        value["_loaded_sha256"] = hashlib.sha256(read_spec_bytes(path)).hexdigest()


def _legacy_binding_tip(root: Path, previous: dict, current: dict) -> str | None:
    """Recover an anchor only by reproducing the original bound document bytes.

    Keep the receipt unchanged. Unknown historical serializers/layouts are not
    guessed from a matching semantic snapshot; they remain a diagnostic gap.
    """
    variable = {"spec_hash", "journal_hash", "journal_tip"}
    if {k: v for k, v in previous.items() if k not in variable} != {
        k: v for k, v in current.items() if k not in variable
    } or previous.get("spec_hash") != previous.get("journal_hash"):
        return None
    path = root / current["spec_path"]
    events, continuity = _read_journal(path)
    if continuity != "continuous" or not events:
        return None
    body, _ = _split_spec_audit(read_spec_document(path))
    history, serialized = [], []
    # Incremental prefix serialization is bounded by the existing journal size.
    # Hash equality proves the old byte representation, not merely a revision.
    for item in events:
        discussion = item.get("delta", {}).get("discussion", {})
        summary = discussion.get("summary") or discussion.get("goal")
        if summary:
            history.append(
                "- "
                + str(discussion.get("source_ref", "unknown"))
                + ": "
                + str(summary).replace("\n", " ")
            )
        serialized.append(_normalized_json(item))
        old = (
            body
            + "\n<!-- spec-audit:start -->\n## Discussion History\n\n"
            + "\n".join(history)
            + "\n\n### Source and Revision Audit\n\n```jsonl\n"
            + "\n".join(serialized)
            + "\n```\n<!-- spec-audit:end -->\n"
        )
        for raw in (old.encode("utf-8"), old.replace("\n", "\r\n").encode("utf-8")):
            if hashlib.sha256(raw).hexdigest() == previous["spec_hash"]:
                return item["event_hash"]
    return None


def assess_execution_compatibility(
    root: Path,
    spec_path: str,
    working_reference: str,
    task_ref: str,
    runtime: dict,
    *,
    persist: bool = False,
    validation_assessor=None,
) -> dict:
    """Inventory supported SPEC/receipt/validation formats; never grant execution.

    This owner alone saves the cache using the execution state's compare-and-swap.
    A cache is a performance hint, not authorization or acceptance evidence.
    """
    denied = {
        "verdict": "BLOCKED",
        "product_code_allowed": False,
        "next_action": "diagnose-compatibility",
        "reused": False,
    }
    try:
        root = root.resolve()
        state = read_execution_state(root, task_ref)
        current = execution_binding(root, spec_path, working_reference, task_ref)
        events, continuity = _read_journal(root / spec_path)
        if continuity != "continuous":
            raise ValueError("unverifiable SPEC history")
        validation = {}
        for relative in [
            "architecture/adoption.yaml",
            "architecture/manifest.yaml",
            "validation/verification-ladder.yaml",
            "validation/on-device.yaml",
            "validation/layout.yaml",
            f"validation/acceptance-{Path(spec_path).name[:9]}.json",
        ]:
            path = root / relative
            if path.is_symlink() or path.resolve().is_relative_to(root) is False:
                raise ValueError("validation input must not be redirected")
            validation[relative] = (
                hashlib.sha256(read_spec_bytes(path)).hexdigest()
                if path.exists()
                else None
            )
        authority = {
            k: state.get(k)
            for k in [
                "schema_version",
                "phase",
                "receipt",
                "receipts",
                "pending_authorizations",
                "fulfilled_authorizations",
                "used_event_ids",
            ]
        }
        validation_check = assess_project_validation(
            root, spec_path, validation_assessor=validation_assessor
        )
        if not isinstance(validation_check, dict):
            raise TypeError("validation assessment must be an object")
        layout_check = validation_check.get("layout", {"verdict": "PASS"})
        validation_ready = (
            validation_check.get("verdict") == "PASS"
            and isinstance(layout_check, dict)
            and layout_check.get("verdict") == "PASS"
        )
        if any(validation.values()) and validation_assessor is None:
            validation_ready = False
            validation_check = {
                "verdict": "BLOCKED",
                "errors": [
                    "Validation inputs require the authoritative validation assessor."
                ],
            }
        facts = {
            "schema_version": 1,
            "root": str(root),
            "task_ref": task_ref,
            "spec_path": spec_path,
            "snapshot_hash": current["snapshot_hash"],
            "binding_validity": [
                execution_binding_matches(root, r.get("binding"), current)
                for r in (
                    [state.get("receipt") or {}]
                    + list(state.get("receipts", {}).values())
                    + list(state.get("pending_authorizations", {}).values())
                )
            ],
            "contract_history": [
                e["event_hash"]
                for e in events
                if e.get("event_type") != "discussion"
                or e.get("affected_ids")
                or e.get("conflicts")
                or e.get("open_decisions")
                or e.get("snapshot_hash") != current["snapshot_hash"]
                or e.get("previous_snapshot_hash") != current["snapshot_hash"]
            ],
            "runtime": runtime,
            "validation_assessor_available": validation_assessor is not None,
            "authority": authority,
            "validation": validation,
            "validation_assessment": validation_check,
        }
        fingerprint = hashlib.sha256(_normalized_json(facts).encode()).hexdigest()
        saved = state.get("compatibility")
        if isinstance(saved, dict) and saved.get("fingerprint") == fingerprint:
            report = saved.get("report")
            if (
                isinstance(report, dict)
                and report.get("verdict") == "PASS"
                and saved.get("report_hash")
                == hashlib.sha256(_normalized_json(report).encode()).hexdigest()
            ):
                return report | {
                    "reused": True,
                    "scan_reason": "unchanged-verified-inputs",
                }
        rows = [
            {
                "kind": "spec",
                "path": spec_path,
                "disposition": "reuse",
                "reason": "matched current specification with continuous history",
            }
        ]
        receipts = list(state.get("receipts", {}).values())
        if state.get("receipt") and state["receipt"] not in receipts:
            receipts.append(state["receipt"])
        receipts.extend(state.get("pending_authorizations", {}).values())
        usable_authorization = False
        for receipt in receipts:
            binding = receipt.get("binding", {})
            if not isinstance(binding, dict):
                raise TypeError("authorization binding must be an object")
            if binding.get("spec_path") != spec_path:
                continue
            is_pending = receipt in state.get("pending_authorizations", {}).values()
            matched = state["phase"] != "suspended" and (
                preparation_binding_matches(root, receipt, current)
                if is_pending
                else execution_binding_matches(root, binding, current)
            )
            usable_authorization = usable_authorization or matched
            legacy = "journal_tip" not in binding
            rows.append(
                {
                    "kind": "authorization",
                    "source_event_id": receipt.get("source_event_id"),
                    "disposition": ("verified-legacy-read" if legacy else "reuse")
                    if matched
                    else "unknown",
                    "reason": "original binding retained; history verified"
                    if matched
                    else "stale, revoked or unprovable authorization",
                }
            )
        if usable_authorization:
            for row in rows:
                if row["kind"] == "authorization" and row["disposition"] == "unknown":
                    row["disposition"] = "not-reusable"
        for relative, digest in validation.items():
            # An absent optional profile is not a claim that a device is needed.
            rows.append(
                {
                    "kind": "validation",
                    "path": relative,
                    "disposition": ("reuse" if digest else "not-required")
                    if validation_ready
                    else "unknown",
                    "sha256": digest,
                }
            )
        report = {
            "verdict": "BLOCKED"
            if any(r["disposition"] == "unknown" for r in rows)
            else "PASS",
            "product_code_allowed": False,
            "reused": False,
            "fingerprint": fingerprint,
            "scan_reason": "changed-or-untrusted-inputs",
            "runtime": runtime,
            "inventory": rows,
            "next_action": "run-existing-admission-and-deterministic-preparation",
            "validation_assessment": validation_check,
            "preparation_allowed": not any(
                r["kind"] == "authorization" and r["disposition"] == "unknown"
                for r in rows
            ),
            "enforcement_scope": "managed-workflow-only",
        }
        if report["verdict"] == "BLOCKED":
            report["next_action"] = "diagnose-compatibility"
        if persist and report["verdict"] == "PASS":
            state["compatibility"] = {
                "fingerprint": fingerprint,
                "report": report,
                "report_hash": hashlib.sha256(
                    _normalized_json(report).encode()
                ).hexdigest(),
            }
            write_execution_state(root, task_ref, state)
        return report
    except (OSError, ValueError, KeyError, TypeError) as error:
        return denied | {"reason": str(error)}
