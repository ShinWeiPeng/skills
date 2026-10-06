"""Evidence-preserving format migration; unknown facts remain decisions."""

from __future__ import annotations
import json
from pathlib import Path
from document_bundle import (
    MARKER,
    read_spec_document,
    read_spec_bytes,
    split_spec,
    spec_hash,
)
from document_updates import digest, prepare_update, resume_update, safe_path


def migrate_spec(root, relative, *, binding, authorize, allow_working=False):
    root = Path(root).resolve()
    path = safe_path(root, relative)
    if path.read_text(encoding="utf-8").startswith(MARKER):
        read_spec_document(path)
        return {
            "status": "effective",
            "migration_required": False,
            "canonical": relative,
        }
    original = path.read_bytes()
    text = original.decode("utf-8")
    from spec_contract import validate_spec_text, _repository_spec_ids

    checked = validate_spec_text(text, known_spec_ids=_repository_spec_ids(root))
    if checked["verdict"] != "PASS" and not (
        allow_working and "\nstatus: working\n" in text
    ):
        raise ValueError(
            "legacy contract needs investigation: " + "; ".join(checked["errors"])
        )
    files = split_spec(text, relative)
    source_hash = digest(original)
    history = f"architecture/history/specs/{path.stem}/{source_hash}.md"
    source = safe_path(root, history)
    if source.exists() and source.read_bytes() != original:
        raise ValueError("immutable history conflict: " + history)
    files[history] = text
    proof_path = f"spec-governance/document-migrations/{path.stem}-{source_hash}.json"
    proof = {
        "format_version": 1,
        "canonical": relative,
        "original_sha256": source_hash,
        "original_hex": original.hex(),
        "history": history,
        "binding": binding,
        "files": {p: digest(c.encode()) for p, c in files.items()},
        "semantic_projection_sha256": source_hash,
        "facts_inferred": False,
        "requirements_changed": False,
    }
    files[proof_path] = (
        json.dumps(proof, sort_keys=True, ensure_ascii=True, indent=2) + "\n"
    )
    changes = {
        p: {
            "before_sha256": digest(safe_path(root, p).read_bytes())
            if safe_path(root, p).exists()
            else None,
            "content": content,
        }
        for p, content in files.items()
    }
    operation = "migrate-" + path.stem + "-" + source_hash[:16]
    prepare_update(
        root,
        operation,
        changes,
        binding=binding,
        validate_candidate=lambda candidates: None,
    )

    def validate():
        if read_spec_bytes(path) != original or spec_hash(path) != source_hash:
            raise ValueError("migration changed canonical semantics or source bytes")

    result = resume_update(
        root, operation, binding=binding, authorize=authorize, validate_result=validate
    )
    return {
        "status": result["status"],
        "migration_required": False,
        "canonical": relative,
        "proof": proof_path,
    }


def resume_migration(root, operation_id, *, binding, authorize):
    """Use the reserved originals after partial writes, never infer a new baseline."""
    root = Path(root).resolve()
    plan = json.loads(
        safe_path(
            root, "spec-governance/document-updates/" + operation_id + ".json"
        ).read_text(encoding="utf-8")
    )
    proof_rows = [
        row
        for p, row in plan["files"].items()
        if p.startswith("spec-governance/document-migrations/")
    ]
    if len(proof_rows) != 1:
        raise ValueError("reserved migration proof missing or ambiguous")
    proof = json.loads(bytes.fromhex(proof_rows[0]["after_hex"]))
    original = bytes.fromhex(proof["original_hex"])
    if digest(original) != proof["original_sha256"] or proof["binding"] != binding:
        raise ValueError("migration source evidence differs")

    def validate():
        if read_spec_bytes(root / proof["canonical"]) != original:
            raise ValueError("migration changed canonical semantics")

    return resume_update(
        root,
        operation_id,
        binding=binding,
        authorize=authorize,
        validate_result=validate,
    )


def write_spec_document(path, text):
    """Owner-only lifecycle replacement of an already migrated document set."""
    path = Path(path)
    root = path.parent.parent.resolve()
    relative = "specs/" + path.name
    refs_path = path.parent / path.name[:9] / "references.yaml"
    from document_bundle import strict_yaml

    refs = strict_yaml(refs_path.read_text(encoding="utf-8"), str(refs_path))
    override = _OWNER_REFERENCES.get()
    if override is not None:
        refs = refs | {"designs": override[0]}
    files = split_spec(text, relative, design_refs=refs["designs"])
    if override is not None:
        candidate_prefix = f"specs/{path.name[:9]}/candidates/"
        for candidate, content in override[1].items():
            if not candidate.startswith(candidate_prefix):
                raise ValueError("candidate outside selected SPEC")
            target = safe_path(root, candidate)
            if target.exists() and target.read_bytes() != content.encode():
                raise ValueError("immutable candidate conflict: " + candidate)
        files.update(override[1])
    current = read_spec_document(path)
    operation = (
        "owner-" + digest((relative + "\0" + current + "\0" + text).encode())[:40]
    )
    changes = {
        p: {
            "before_sha256": digest(safe_path(root, p).read_bytes())
            if safe_path(root, p).exists()
            else None,
            "content": c,
        }
        for p, c in files.items()
    }
    binding = {
        "canonical": relative,
        "previous_projection": digest(current.encode()),
        "next_projection": digest(text.encode()),
    }
    from document_updates import candidate_documents

    def validate_prepared(candidates):
        with candidate_documents(root, files):
            if read_spec_document(path) != text:
                raise ValueError("candidate SPEC projection differs")

    prepare_update(
        root, operation, changes, binding=binding, validate_candidate=validate_prepared
    )

    parent = _RECOVERY_PARENT.get()
    if parent is not None:
        from document_updates import atomic_bytes

        link = {"parent": parent, "child": operation, "binding": binding}
        link_path = safe_path(
            root, "spec-governance/document-updates/" + parent + "-audit-child.json"
        )
        if (
            link_path.exists()
            and json.loads(link_path.read_text(encoding="utf-8")) != link
        ):
            raise ValueError("reserved owner audit child differs")
        atomic_bytes(link_path, (json.dumps(link, sort_keys=True) + "\n").encode())

    def validate():
        if read_spec_document(path) != text:
            raise ValueError("owner replacement projection differs")

    # The existing owner lifecycle already holds its SPEC lock and checks authority.
    resume_update(
        root,
        operation,
        binding=binding,
        authorize=lambda value: None,
        validate_result=validate,
    )


from contextvars import ContextVar
from contextlib import contextmanager

_OWNER_REFERENCES = ContextVar("working_spec_design_references", default=None)
_RECOVERY_PARENT = ContextVar("owner_recovery_parent", default=None)


@contextmanager
def owner_references(refs, candidates):
    token = _OWNER_REFERENCES.set((refs, candidates))
    try:
        yield
    finally:
        _OWNER_REFERENCES.reset(token)


def _resume_owner_write(root, operation_id, working_id):
    """Finish a reserved owner transition, preserving its bytes and audit lineage."""
    from document_updates import recovery_originals
    import spec_contract as owner

    root = Path(root).resolve()
    plan = json.loads(
        safe_path(
            root, "spec-governance/document-updates/" + operation_id + ".json"
        ).read_text(encoding="utf-8")
    )
    binding = plan.get("binding", {})
    if set(binding) != {"canonical", "previous_projection", "next_projection"}:
        raise ValueError("not an owner document transition")
    path = safe_path(root, binding["canonical"])
    prefix = f"specs/{path.name[:9]}/"
    if any(
        p != binding["canonical"] and not p.startswith(prefix) for p in plan["files"]
    ):
        raise ValueError("owner transition exceeds selected SPEC")
    with recovery_originals(root, operation_id):
        previous = read_spec_document(path)
    if digest(previous.encode()) != binding["previous_projection"]:
        raise ValueError("reserved owner baseline differs")
    metadata, errors = owner._metadata(previous)
    if errors or metadata.get("working_id") != working_id:
        raise ValueError("owner recovery identity differs")

    def validate():
        if digest(read_spec_document(path).encode()) != binding["next_projection"]:
            raise ValueError("reserved owner result differs")

    recovered_path = safe_path(
        root,
        "spec-governance/document-updates/" + operation_id + "-owner-complete.json",
    )
    if recovered_path.exists():
        completed = json.loads(recovered_path.read_text(encoding="utf-8"))
        if (
            completed.get("binding") != binding
            or completed.get("working_id") != working_id
            or digest(read_spec_document(path).encode()) != completed["projection"]
        ):
            raise ValueError("completed owner recovery has drifted")
        return {
            "verdict": "PASS",
            "update_status": "effective",
            "working_spec": owner._working_reference(root, path, path),
            "product_code_allowed": False,
        }
    audit_completed = False
    if plan["status"] == "effective":
        from document_updates import candidate_documents

        prepared = {
            p: bytes.fromhex(row["after_hex"]).decode()
            for p, row in plan["files"].items()
            if row["after_hex"] is not None
        }
        with candidate_documents(root, prepared):
            intended = read_spec_document(path)
        current = read_spec_document(path)
        events, continuity = owner._read_journal(path)
        audit_completed = bool(
            continuity == "continuous"
            and events
            and events[-1]["event_type"] == "document-recovery"
            and events[-1].get("delta", {}).get("document_operation") == operation_id
            and events[-1]["previous_snapshot_hash"] == owner._snapshot_hash(previous)
            and owner._snapshot_hash(current)
            == owner._snapshot_hash(intended)
            == events[-1]["snapshot_hash"]
        )
    if audit_completed:
        result = {"status": "effective"}
    else:
        result = resume_update(
            root,
            operation_id,
            binding=binding,
            authorize=lambda b: None,
            validate_result=validate,
        )
    current = read_spec_document(path)
    events, continuity = owner._read_journal(path)
    current_hash = owner._snapshot_hash(current)
    if not events or events[-1].get("snapshot_hash") != current_hash:
        if (
            continuity != "continuous"
            or not events
            or events[-1].get("snapshot_hash") != owner._snapshot_hash(previous)
        ):
            raise ValueError("owner audit baseline differs")
        consistency = owner._snapshot_consistency(previous, current)
        parent_token = _RECOVERY_PARENT.set(operation_id)
        try:
            owner._append_journal_event(
                path,
                event_type="document-recovery",
                working_id=working_id,
                revision=int(owner._metadata(current)[0]["revision"]),
                previous_snapshot_hash=owner._snapshot_hash(previous),
                snapshot_hash=current_hash,
                continuity=continuity,
                delta=consistency["delta"] | {"document_operation": operation_id},
                relationships=consistency["relationships"],
                conflicts=consistency["conflicts"],
                open_decisions=consistency["open_decisions"],
                verdict=consistency["verdict"],
            )
        finally:
            _RECOVERY_PARENT.reset(parent_token)
    from document_updates import atomic_bytes

    atomic_bytes(
        recovered_path,
        (
            json.dumps(
                {
                    "binding": binding,
                    "working_id": working_id,
                    "projection": digest(read_spec_document(path).encode()),
                },
                sort_keys=True,
            )
            + "\n"
        ).encode(),
    )
    return {
        "verdict": "PASS",
        "update_status": result["status"],
        "working_spec": owner._working_reference(root, path, path),
        "product_code_allowed": False,
    }


def resume_owner_write(root, operation_id, working_id):
    """Resume both the source transition and a durably linked audit transition."""
    from state_lock import project_state_lock
    from document_updates import (
        document_lock,
        recovery_originals,
        candidate_documents,
        validation_operations,
    )
    import spec_contract as owner

    root = Path(root).resolve()
    with project_state_lock(root, "spec:" + working_id), document_lock(root):
        link_path = safe_path(
            root,
            "spec-governance/document-updates/" + operation_id + "-audit-child.json",
        )
        if link_path.exists():
            link = json.loads(link_path.read_text(encoding="utf-8"))
            parent = json.loads(
                safe_path(
                    root, "spec-governance/document-updates/" + operation_id + ".json"
                ).read_text(encoding="utf-8")
            )
            if (
                set(link) != {"parent", "child", "binding"}
                or link["parent"] != operation_id
                or parent["status"] != "effective"
            ):
                raise ValueError("invalid owner audit relationship")
            child = json.loads(
                safe_path(
                    root, "spec-governance/document-updates/" + link["child"] + ".json"
                ).read_text(encoding="utf-8")
            )
            binding = child["binding"]
            if (
                binding != link["binding"]
                or set(binding)
                != {"canonical", "previous_projection", "next_projection"}
                or binding["canonical"] != parent["binding"]["canonical"]
                or binding["previous_projection"]
                != parent["binding"]["next_projection"]
            ):
                raise ValueError("owner audit binding differs")
            path = safe_path(root, binding["canonical"])
            prefix = f"specs/{path.name[:9]}/"
            if any(
                p != binding["canonical"] and not p.startswith(prefix)
                for p in child["files"]
            ):
                raise ValueError("owner audit exceeds selected SPEC")
            with validation_operations(operation_id, link["child"]):
                with recovery_originals(root, link["child"]):
                    before = read_spec_document(path)
                if digest(before.encode()) != binding["previous_projection"]:
                    raise ValueError("owner audit baseline differs")
                prepared = {
                    p: bytes.fromhex(r["after_hex"]).decode()
                    for p, r in child["files"].items()
                    if r["after_hex"] is not None
                }
                with candidate_documents(root, prepared):
                    intended = read_spec_document(path)
                    events, continuity = owner._read_journal(path)
                if (
                    digest(intended.encode()) != binding["next_projection"]
                    or owner._metadata(intended)[0].get("working_id") != working_id
                    or continuity != "continuous"
                    or not events
                    or events[-1]["event_type"] != "document-recovery"
                    or events[-1].get("delta", {}).get("document_operation")
                    != operation_id
                ):
                    raise ValueError("owner audit identity or lineage differs")

                def validate():
                    if read_spec_document(path) != intended:
                        raise ValueError("recovered owner audit differs")

                resume_update(
                    root,
                    link["child"],
                    binding=binding,
                    authorize=lambda b: None,
                    validate_result=validate,
                )
                return _resume_owner_write(root, operation_id, working_id)
        return _resume_owner_write(root, operation_id, working_id)
