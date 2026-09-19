"""Durable discussion obligations owned by spec governance, independent of execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from contextlib import nullcontext
from pathlib import Path
from uuid import uuid4

from spec_contract import (
    REQUIRED_SECTIONS,
    _append_journal_event,
    _atomic_write,
    _contract_completeness_gaps,
    _migrate_flat_bundle,
    _read_journal,
    _redact_sensitive_content,
    _replace_metadata,
    _snapshot_rows,
    assess_turn_context,
    materialize_working_bundle,
    project_state_lock,
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


def _project_binding_path(root, task):
    path, _ = _paths(root, task)
    binding = path.with_name("PROJECT-" + _hash(task) + ".json")
    if binding.is_symlink() or (
        binding.exists() and (not binding.is_file() or binding.stat().st_nlink != 1)
    ):
        raise ValueError("project binding must be an ordinary unshared file")
    return binding


def resolve_discussion_project(root: Path, task: str) -> Path:
    """Resolve an explicit task mapping; never choose a child repository."""
    host = root.resolve(strict=True)
    path = _project_binding_path(host, task)
    if not path.exists():
        return host
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "task_ref", "host_root", "project_root"}
        or value["schema_version"] != 1
        or value["task_ref"] != task
        or value["host_root"] != str(host)
    ):
        raise ValueError("invalid task project binding")
    target = Path(_text(value["project_root"], "project_root"))
    if not target.is_absolute() or not target.is_dir() or target.resolve() != target:
        raise ValueError("bound project root moved or is redirected")
    return target


def _bind_project(root, request):
    host = root.resolve(strict=True)
    task = _text(request.get("task_ref"), "task_ref")
    candidate = Path(_text(request.get("project_root"), "project_root"))
    if not candidate.is_absolute() or not candidate.is_dir():
        raise ValueError("explicit existing absolute project root required")
    target = candidate.resolve(strict=True)
    value = {
        "schema_version": 1,
        "task_ref": task,
        "host_root": str(host),
        "project_root": str(target),
    }
    with project_state_lock(host, "project-binding:" + task):
        path = _project_binding_path(host, task)
        if path.exists():
            if json.loads(path.read_text(encoding="utf-8")) != value:
                raise ValueError(
                    "task is already bound; implicit project relocation is prohibited"
                )
            return {"verdict": "PASS", "project_root": str(target), "replayed": True}
        state_path, _ = _paths(host, task)
        state = _load(state_path, task)
        if target != host and any(
            row.get("working_id") for row in state["turns"].values()
        ):
            raise ValueError(
                "task already owns a SPEC here; preserve it rather than relocate implicitly"
            )
        pending_sources = [
            {
                "turn_id": row["turn_id"],
                "source_ref": row["source_ref"],
                "prompt": row["prompt"],
            }
            for row in state["turns"].values()
            if row.get("kind") == "unknown"
        ]
        if target != host:
            with project_state_lock(target, "project-binding:" + task):
                destination, _ = _paths(target, task)
                target_state = _load(destination, task)
                for turn, row in state["turns"].items():
                    if (
                        turn in target_state["turns"]
                        and target_state["turns"][turn] != row
                    ):
                        raise ValueError(
                            "target has conflicting pending turn; retain both stores"
                        )
                    if target_state["active_turn"] not in {None, state["active_turn"]}:
                        raise ValueError(
                            "target has another active turn; retain both stores"
                        )
                    target_state["turns"][turn] = row
                    target_state["active_turn"] = state["active_turn"]
                _atomic_write(
                    destination,
                    json.dumps(target_state, ensure_ascii=False, indent=2) + "\n",
                )
        # Commit the pointer last; interruption leaves the source recoverable.
        _atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return {
        "pending_sources": pending_sources,
        "verdict": "PASS",
        "project_root": str(target),
        "replayed": False,
        "product_code_allowed": False,
    }


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


def _project_mapping_gap(root):
    if (root / ".git").exists() or (root / "specs").is_dir():
        return False
    return any(child.is_dir() and (child / ".git").exists() for child in root.iterdir())


def _mapping_block():
    return {
        "verdict": "BLOCKED",
        "mapping_gap": True,
        "reason": "bind the task to an explicit project root; source retained",
        "product_code_allowed": False,
    }


def _enter_engineering(root, task, row):
    if _project_mapping_gap(root):
        raise ValueError("explicit project binding required; source retained")
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


def _sources(row):
    return sorted(
        {
            row["source_ref"],
            *row.get("carried_sources", []),
            *(item["source_ref"] for item in row.get("additional_prompts", [])),
        }
    )


def _items_reviewed(row):
    # Legacy observations remain readable with an explicit weaker coverage label.
    return "items" not in row or (
        isinstance(row["items"], dict)
        and set(_sources(row)) <= set(row.get("reviewed_sources", []))
    )


def _item_bindings(root, working, items, bindings):
    if not isinstance(bindings, dict) or set(bindings) != set(items):
        raise ValueError("save a binding for every identified item")
    rows = _snapshot_rows((root / working["snapshot_path"]).read_text(encoding="utf-8"))
    adopted_decisions = set()
    for identity, item in items.items():
        refs = bindings[identity]
        if not isinstance(refs, list) or any(
            not isinstance(ref, str) or ref not in rows for ref in refs
        ):
            raise ValueError("identified item refers to a missing contract row")
        if item["kind"] == "accepted" and not any(
            ref.startswith("DEC-") for ref in refs
        ):
            raise ValueError("every accepted item needs a saved DEC row")
        if item["kind"] == "accepted" and not any(
            ref.startswith("DEC-")
            and re.search(
                r"(?<![\w-])" + re.escape(item["source_ref"]) + r"(?![\w-])",
                rows[ref].get("source", ""),
            )
            for ref in refs
        ):
            raise ValueError("accepted item source must match its saved DEC source")
        if item["kind"] == "accepted":
            decisions = {ref for ref in refs if ref.startswith("DEC-")}
            if adopted_decisions & decisions:
                raise ValueError(
                    "distinct accepted items require distinct saved DEC rows"
                )
            adopted_decisions.update(decisions)
        if item["kind"] == "candidate" and refs:
            raise ValueError("candidate items cannot claim adopted contract rows")
    return bindings


def _saved(root, task, row, reply=None):
    if row["kind"] == "non-engineering":
        return not row.get("carried_sources")
    if not _items_reviewed(row):
        return False
    saved = row.get("saved")
    if row["kind"] != "engineering" or not isinstance(saved, dict):
        return False
    if saved.get("task_ref") != task or saved.get("turn_id") != row["turn_id"]:
        return False
    if saved["binding"] != _binding(root, task, row):
        return False
    working = _working(root, task, row)
    if row.get("items") is not None:
        if saved.get("identified_items") != row["items"] or saved.get(
            "reviewed_sources"
        ) != row.get("reviewed_sources"):
            return False
        _item_bindings(root, working, row["items"], saved.get("item_bindings"))
    events, continuity = _read_journal(root / working["journal_path"])
    # Reply wording is audit evidence, not a requirement-synchronization gate.
    return continuity == "continuous" and any(
        e.get("event_hash") == saved["event_hash"]
        and e.get("delta", {}).get("discussion")
        == {k: v for k, v in saved.items() if k != "event_hash"}
        for e in events
    )


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
                "identified_items": row.get("items"),
                "reviewed_sources": row.get("reviewed_sources"),
                "owner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            },
            sort_keys=True,
        )
    )


def _operate(root, state, request):
    task = state["task_ref"]
    operation = request["operation"]
    if operation in {"hook-health", "record-hook-observation"}:
        observations = state.setdefault("hook_observations", [])
        if not isinstance(observations, list) or any(
            not isinstance(row, dict) for row in observations
        ):
            raise ValueError(
                "invalid hook observation history; preserve for investigation"
            )
        if operation == "record-hook-observation":
            observation = request.get("observation")
            fields = {
                "event",
                "host_root",
                "entrypoint_sha256",
                "package_version",
                "input_sha256",
                "result_sha256",
                "observed_at",
            }
            if not isinstance(observation, dict) or set(observation) != fields:
                raise ValueError("bounded hook observation fields required")
            observation = {
                key: _text(value, "observation." + key)
                for key, value in observation.items()
            }
            if observation["event"] not in {
                "SessionStart",
                "UserPromptSubmit",
                "PreToolUse",
                "Stop",
            }:
                raise ValueError("unsupported observed adapter event")
            observation.update(
                task_ref=task,
                turn_id=request.get("turn_id"),
                project_root=str(root),
                provenance="caller-attested-adapter-stdin",
            )
            if observation not in observations:
                observations.append(observation)
            if len(observations) > 256:
                state["truncated_hook_observations"] = (
                    state.get("truncated_hook_observations", 0)
                    + len(observations)
                    - 256
                )
                del observations[:-256]
        return {
            "verdict": "PASS",
            "product_code_allowed": False,
            "supported": {
                "adapter_events": [
                    "SessionStart",
                    "UserPromptSubmit",
                    "PreToolUse",
                    "Stop",
                ],
                "host": "unverified",
            },
            "trusted": "unverified",
            "loaded": "unverified",
            "fired": "unverified",
            "adapter_observations": observations,
            "truncated_observations": state.get("truncated_hook_observations", 0),
        }
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
                row["reviewed_sources"] = []
                if row["kind"] == "engineering":
                    _append(root, _working(root, task, row), update)
            if request.get("engineering") is True and existing[0]["kind"] == "unknown":
                if _project_mapping_gap(root):
                    return _mapping_block()
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
            "items": None,
            "reviewed_sources": [],
            "repair_used": False,
            "repair_keys": [],
            "saved": None,
        }
        if active and (
            active["kind"] == "engineering" or active.get("carried_sources")
        ):
            try:
                unresolved = active["kind"] != "engineering" or not _saved(
                    root, task, active
                )
            except (OSError, ValueError, KeyError, TypeError):
                unresolved = True
            if unresolved:
                row["items"] = (
                    dict(active["items"])
                    if isinstance(active.get("items"), dict)
                    else None
                )
                row["carried_sources"] = _sources(active)
            if active.get("working_id"):
                row["working_id"] = active["working_id"]
        if request.get("working_reference"):
            row["working_id"] = _text(request["working_reference"], "working_reference")
        state["turns"][turn] = row
        state["active_turn"] = turn
        if request.get("engineering") is True:
            if _project_mapping_gap(root):
                return _mapping_block()
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
    if operation == "observe":
        if row["kind"] != "engineering":
            raise ValueError(
                "classify the engineering discussion before identifying items"
            )
        items = request.get("items")
        if not isinstance(items, list) or len(items) > 256:
            raise ValueError("items must be a bounded list")
        sources = request.get("source_refs")
        if (
            not isinstance(sources, list)
            or any(not isinstance(v, str) or not v.strip() for v in sources)
            or not set(_sources(row)) <= set(sources)
        ):
            raise ValueError("review every current and carried discussion source")
        current = dict(row.get("items") or {})
        for item in items:
            if not isinstance(item, dict) or set(item) != {
                "id",
                "kind",
                "source_ref",
                "text",
            }:
                raise ValueError("item requires id, kind, source_ref and text")
            normalized = {
                k: _redact_sensitive_content(_text(v, "item." + k))
                for k, v in item.items()
            }
            if item["kind"] not in {"accepted", "candidate", "fact", "question"}:
                raise ValueError("explicit item classification is required")
            if normalized["source_ref"] not in sources:
                raise ValueError("item source was not explicitly reviewed")
            identity = normalized["id"]
            if identity in current and current[identity] != normalized:
                raise ValueError(
                    "item identity already has different source/content; record a sourced correction separately"
                )
            current[identity] = normalized
        if len(current) > 256:
            raise ValueError("identified item count exceeds the bounded turn contract")
        changed = current != row.get("items") or sorted(set(sources)) != row.get(
            "reviewed_sources"
        )
        if changed:
            row["items"] = current
            row["reviewed_sources"] = sorted(set(sources))
            row["saved"] = None
        return {
            "verdict": "PASS",
            "identified_items": current,
            "replayed": not changed,
            "product_code_allowed": False,
        }
    if operation == "record":
        if row["kind"] != "engineering":
            raise ValueError("classify the engineering discussion before saving")
        working = _working(root, task, row)
        if request.get("binding") != _binding(root, task, row):
            raise ValueError("stale or mismatched working binding")
        if not _items_reviewed(row):
            raise ValueError(
                "identify and review this turn's items and sources before saving"
            )
        bindings = None
        if row.get("items") is not None:
            bindings = _item_bindings(
                root, working, row["items"], request.get("item_bindings", {})
            )
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
                if "items" in row:
                    observed = (row.get("items") or {}).get(candidate["id"], {})
                    if observed.get("kind") != "accepted" or observed.get(
                        "source_ref"
                    ) != candidate.get("user_source_ref"):
                        raise ValueError(
                            "accepted candidate requires a matching identified item and user source"
                        )
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
        if bindings is not None:
            record.update(
                identified_items=row["items"],
                item_bindings=bindings,
                reviewed_sources=row.get("reviewed_sources"),
            )
        prior = row.get("saved")
        replayed = isinstance(prior, dict) and record == {
            k: v for k, v in prior.items() if k != "event_hash"
        }
        if not replayed:
            event = _append(root, working, record)
            row["saved"] = {**record, "event_hash": event["event_hash"]}
        if not _saved(root, task, row):
            raise ValueError("saved discussion failed document/journal readback")
        return {
            "verdict": "PASS",
            "binding": record["binding"],
            "event_hash": row["saved"]["event_hash"],
            "product_code_allowed": False,
            "confirmation": confirmation,
            "replayed": replayed,
            "saved_items": sorted(row.get("items") or {}),
            "spec_presentation": assess_turn_context(
                root, reference=working["working_id"], task_ref=task
            )["spec_presentation"]
            | {"status": working["status"]},
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
            "item_coverage": "unreviewed"
            if not _items_reviewed(row)
            else "identified-items-only"
            if "items" in row
            else "legacy-unregistered",
            "source_refs": _sources(row),
            "pending_items": [] if saved else sorted(row.get("items") or {}),
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
            "observe the actual items and source_refs, reconcile decisions, then record every item binding with current SPEC binding; final reply wording is audit only. Do not invent decisions, adopt candidates, "
            "authorize implementation or repeat unchanged failures. If this fails report unsaved scope and finish normally; saving and repair remain available."
        )
        return {
            "verdict": "BLOCKED",
            "decision": "block",
            "reason": row["repair_prompt"],
        }
    raise ValueError("unsupported discussion operation")


def discussion_request(root: Path, request: dict) -> dict:
    """Serialize binding and task operations without losing pending source records."""
    host = root.resolve(strict=True)
    if request.get("operation") == "bind-project":
        return _bind_project(host, request)
    task = _text(request.get("task_ref"), "task_ref")
    with project_state_lock(host, "project-binding:" + task):
        root = resolve_discussion_project(host, task)
        target_lock = (
            project_state_lock(root, "project-binding:" + task)
            if root != host
            else nullcontext()
        )
        with target_lock:
            return _discussion_request_at_root(root, request)


def _discussion_request_at_root(root, request):
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
        return result | {"project_root": str(root)}


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
