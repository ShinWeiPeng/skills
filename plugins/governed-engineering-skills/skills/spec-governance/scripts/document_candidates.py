"""Stage immutable candidate bytes through the working SPEC owner; no execution grant."""

import json
import re
from pathlib import Path
from document_bundle import (
    parse_design,
    strict_yaml,
    read_spec_document,
    MARKER,
    render_design,
)
from document_updates import digest, safe_path


def stage_candidate(
    root, working_id, content, *, expected_revision, expected_hash, base_refs=None
):
    import spec_contract as owner
    from legacy_document_migration import migrate_spec, owner_references

    root = Path(root).resolve()
    resolved = owner.resolve_working_bundle(root, reference=working_id)
    reference = resolved.get("working_spec")
    if (
        resolved.get("state") != "working"
        or not reference
        or reference["status"] != "working"
    ):
        raise ValueError("candidate staging requires an unconfirmed working SPEC")
    if (
        reference["revision"] != expected_revision
        or reference["snapshot_hash"] != expected_hash
    ):
        raise ValueError("stale working SPEC")
    path = root / reference["snapshot_path"]
    relative = path.relative_to(root).as_posix()

    def unchanged(binding):
        current = owner.resolve_working_bundle(root, reference=working_id).get(
            "working_spec", {}
        )
        if (
            current.get("revision") != expected_revision
            or current.get("snapshot_hash") != expected_hash
        ):
            raise ValueError("working SPEC changed while preparing candidate")

    if not path.read_bytes().startswith(MARKER.encode()):
        migrate_spec(
            root,
            relative,
            binding={"working_id": working_id, "snapshot_hash": expected_hash},
            authorize=unchanged,
            allow_working=True,
        )
    if content.lstrip().startswith("format_version:"):
        record = strict_yaml(content, "candidate collection")
        if (
            set(record) != {"format_version", "id", "version", "documents"}
            or record["id"] != "DESIGN-COLLECTION"
            or record["format_version"] != 1
            or type(record["version"]) is not int
            or record["version"] < 1
            or not isinstance(record["documents"], list)
        ):
            raise ValueError("invalid candidate collection index")
        suffix = ".yaml"
    else:
        record = parse_design(content, "candidate")
        suffix = ".md"
    # Capture the real preparation baseline, including exact bytes; never infer it at application.
    current_path = None
    if record["id"] == "DESIGN-COLLECTION":
        current_path = "architecture/designs/index.yaml"
    elif (root / "architecture/designs/index.yaml").is_file():
        index = strict_yaml(
            (root / "architecture/designs/index.yaml").read_text(encoding="utf-8"),
            "current index",
        )
        for source in index["documents"]:
            previous = parse_design(
                safe_path(root, source).read_text(encoding="utf-8"), source
            )
            if previous["id"] == record["id"]:
                if current_path is not None:
                    raise ValueError("duplicate current design identity")
                current_path = source
    candidates = {}
    baseline = None
    if current_path is not None and safe_path(root, current_path).exists():
        original = safe_path(root, current_path).read_bytes()
        old = (
            strict_yaml(original.decode(), current_path)
            if suffix == ".yaml"
            else parse_design(original.decode(), current_path)
        )
        if record["version"] != old["version"] + 1:
            raise ValueError("candidate must advance its captured base version")
        saved = f"specs/{path.name[:9]}/candidates/base-{old['id']}-v{old['version']}-{digest(original)[:16]}{suffix}"
        candidates[saved] = original.decode()
        baseline = {
            "id": old["id"],
            "version": old["version"],
            "path": saved,
            "sha256": digest(original),
        }
    elif record["version"] != 1:
        raise ValueError("candidate has no current base version")
    base_content = render_design(
        "BASE-" + record["id"],
        record["version"],
        "catalog",
        {
            "candidate_id": record["id"],
            "candidate_version": record["version"],
            "current_path": current_path,
            "base_reference": baseline,
        },
    )
    base_path = f"specs/{path.name[:9]}/candidates/BASE-{record['id']}-v{record['version']}-{digest(base_content.encode())[:16]}.md"
    candidates[base_path] = base_content
    base_ref = {
        "id": "BASE-" + record["id"],
        "version": record["version"],
        "path": base_path,
        "sha256": digest(base_content.encode()),
    }
    candidate = f"specs/{path.name[:9]}/candidates/{record['id']}-v{record['version']}-{digest(content.encode())[:16]}{suffix}"
    safe_path(root, candidate)
    ref = {
        "id": record["id"],
        "version": record["version"],
        "path": candidate,
        "sha256": digest(content.encode()),
    }
    refs_path = path.parent / path.name[:9] / "references.yaml"
    refs = strict_yaml(refs_path.read_text(encoding="utf-8"), str(refs_path))["designs"]
    if base_refs is not None:
        if not isinstance(base_refs, list):
            raise ValueError("expected reviewed base references")
        refs = base_refs
    refs = [r for r in refs if r["id"] not in {record["id"], base_ref["id"]}] + [
        ref,
        base_ref,
    ]
    if record["id"] == "DESIGN-COLLECTION" and baseline is not None:
        for source in sorted(set(old["documents"]) - set(record["documents"])):
            original = safe_path(root, source).read_bytes()
            retired = parse_design(original.decode(), source)
            saved = f"specs/{path.name[:9]}/candidates/base-removed-{retired['id']}-v{retired['version']}-{digest(original)[:16]}.md"
            candidates[saved] = original.decode()
            metadata = render_design(
                "REMOVE-" + retired["id"],
                retired["version"],
                "catalog",
                {
                    "removed_id": retired["id"],
                    "current_path": source,
                    "base_reference": {
                        "id": retired["id"],
                        "version": retired["version"],
                        "path": saved,
                        "sha256": digest(original),
                    },
                },
            )
            saved_meta = f"specs/{path.name[:9]}/candidates/REMOVE-{retired['id']}-{digest(metadata.encode())[:16]}.md"
            candidates[saved_meta] = metadata
            refs = [
                r
                for r in refs
                if r["id"] not in {retired["id"], "REMOVE-" + retired["id"]}
            ] + [
                {
                    "id": "REMOVE-" + retired["id"],
                    "version": retired["version"],
                    "path": saved_meta,
                    "sha256": digest(metadata.encode()),
                }
            ]

    binding = digest(json.dumps(refs, sort_keys=True, separators=(",", ":")).encode())
    snapshot = read_spec_document(path)
    snapshot = re.sub(
        r"\n<!-- fixed-design-collection:[a-f0-9]{64} -->\n", "\n", snapshot
    )
    marker = "\n<!-- fixed-design-collection:" + binding + " -->\n"
    snapshot = snapshot.replace("## Solution\n", "## Solution\n" + marker, 1)
    with owner_references(refs, candidates | {candidate: content}):
        result = owner.reconcile_working_bundle(
            root,
            working_id,
            snapshot,
            {
                "kind": "design-collection",
                "source_refs": [candidate],
                "affected_ids": [],
                "conflicts": [],
                "open_decisions": [],
            },
            expected_revision=expected_revision,
            expected_hash=expected_hash,
        )
    if result.get("verdict") != "PASS":
        raise ValueError(result.get("reason", str(result)))
    return {
        "verdict": "PASS",
        "candidate": ref,
        "working_spec": result["working_spec"],
        "product_code_allowed": False,
        "confirmation_required": True,
    }


def main():
    import sys

    request = json.load(sys.stdin)
    try:
        if request.get("operation") == "resume-owner-write":
            from legacy_document_migration import resume_owner_write

            result = resume_owner_write(
                Path(request["project_root"]),
                request["operation_id"],
                request["working_reference"],
            )
        else:
            result = stage_candidate(
                Path(request["project_root"]),
                request["working_reference"],
                request["content"],
                expected_revision=request["expected_revision"],
                expected_hash=request["expected_hash"],
                base_refs=request.get("base_refs"),
            )
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {
            "verdict": "BLOCKED",
            "reason": str(error),
            "product_code_allowed": False,
        }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
