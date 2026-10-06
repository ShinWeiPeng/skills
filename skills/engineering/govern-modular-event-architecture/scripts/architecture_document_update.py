"""Architecture-owned generation composed with the SPEC owner's durable writer."""

from pathlib import Path
import yaml
from document_bundle import parse_design, strict_yaml, _resolve_design
from document_updates import (
    digest,
    safe_path,
    prepare_update,
    resume_update,
    locked_documents,
)
from design_sources import generate_manifest, source_versions, migration_plan
from render_architecture import render_documents, GENERATED_MARKER


def _replace(root, files):
    return {
        p: {
            "before_sha256": digest(safe_path(root, p).read_bytes())
            if safe_path(root, p).exists()
            else None,
            "content": text,
        }
        for p, text in files.items()
    }


@locked_documents
def prepare_design_update(
    root, operation_id, sources, *, binding, confirmed_refs, authorize, migration=False
):
    root = Path(root).resolve()
    authorize(binding)
    if migration:
        if sources:
            raise ValueError("migration derives sources from the original manifest")
        files = migration_plan(root, root / "architecture/manifest.yaml")
    else:
        if not isinstance(sources, dict) or not sources or len(sources) > 128:
            raise ValueError("bounded source changes required")
        files = dict(sources)
        confirmed = {(r["id"], r["version"], r["sha256"]) for r in confirmed_refs}
        baselines = {}
        for ref in confirmed_refs:
            if ref["id"].startswith("BASE-"):
                record = parse_design(
                    _resolve_design(root, ref).read_text(encoding="utf-8"), ref["path"]
                )
                value = record["data"]
                if set(value) != {
                    "candidate_id",
                    "candidate_version",
                    "current_path",
                    "base_reference",
                }:
                    raise ValueError("invalid confirmed baseline")
                if (
                    record["id"] != "BASE-" + value["candidate_id"]
                    or record["version"] != value["candidate_version"]
                ):
                    raise ValueError("baseline identity differs")
                if value["candidate_id"] in baselines:
                    raise ValueError("duplicate confirmed baseline")
                baselines[value["candidate_id"]] = value

        def baseline_matches(path, record):
            base = baselines.get(record["id"])
            if base is None or base["candidate_version"] != record["version"]:
                raise ValueError("candidate preparation baseline missing: " + path)
            target = safe_path(root, path)
            if base["base_reference"] is None:
                if base["current_path"] is not None or target.exists():
                    raise ValueError("new candidate base changed: " + path)
            else:
                row = base["base_reference"]
                _resolve_design(root, row)
                if (
                    base["current_path"] != path
                    or not target.is_file()
                    or digest(target.read_bytes()) != row["sha256"]
                ):
                    raise ValueError(
                        "candidate base changed; retained difference: " + path
                    )

        for path, text in sources.items():
            if path == "architecture/designs/index.yaml":
                record = strict_yaml(text, path)
                if (
                    record["id"],
                    record["version"],
                    digest(text.encode()),
                ) not in confirmed:
                    raise ValueError("changed source collection was not confirmed")
                base = baselines.get(record["id"])
                target = safe_path(root, path)
                if (
                    base
                    and base["base_reference"]
                    and base["current_path"] == path
                    and digest(target.read_bytes()) != base["base_reference"]["sha256"]
                ):
                    # Preserve unrelated membership edits; apply only the confirmed delta.
                    base_row = base["base_reference"]
                    original = strict_yaml(
                        _resolve_design(root, base_row).read_text(encoding="utf-8"),
                        "confirmed collection base",
                    )
                    current = strict_yaml(target.read_text(encoding="utf-8"), path)
                    old_members = set(original["documents"])
                    desired = set(record["documents"])
                    live = set(current["documents"])
                    touched = old_members ^ desired
                    append_only_order = [
                        p for p in original["documents"] if p in desired
                    ] + [p for p in record["documents"] if p not in old_members]
                    if record["documents"] != append_only_order:
                        raise ValueError(
                            "candidate collection order conflicts with changed base; retained difference"
                        )
                    if (
                        current["id"] != original["id"]
                        or current["version"] < original["version"]
                        or any((p in live) != (p in old_members) for p in touched)
                    ):
                        raise ValueError(
                            "candidate collection base conflict; retained difference"
                        )
                    projected = current | {
                        "version": current["version"] + 1,
                        "documents": [
                            p
                            for p in current["documents"]
                            if p not in old_members - desired
                        ]
                        + [
                            p for p in record["documents"] if p in desired - old_members
                        ],
                    }
                    files[path] = yaml.safe_dump(projected, sort_keys=False)
                    files[f"spec-governance/design-rebases/{operation_id}.json"] = (
                        __import__("json").dumps(
                            {
                                "approved": record,
                                "base": original,
                                "concurrent": current,
                                "effective": projected,
                                "semantics": "same confirmed membership delta; unrelated sources retained",
                            },
                            sort_keys=True,
                            indent=2,
                        )
                        + "\n"
                    )
                    record = projected
                    text = files[path]
                else:
                    baseline_matches(path, record)
                previous = strict_yaml(
                    safe_path(root, path).read_text(encoding="utf-8"), path
                )
                if record["id"] != previous["id"] or (
                    text.encode() != safe_path(root, path).read_bytes()
                    and record["version"] != previous["version"] + 1
                ):
                    raise ValueError("collection identity/version changed incorrectly")
                continue
            if not path.startswith("architecture/designs/") or not path.endswith(".md"):
                raise ValueError("only maintained design sources can be changed")
            record = parse_design(text, path)
            if (
                record["id"],
                record["version"],
                digest(text.encode()),
            ) not in confirmed:
                raise ValueError(
                    "candidate was not part of the confirmed SPEC collection: " + path
                )
            baseline_matches(path, record)
            current = safe_path(root, path)
            if current.exists():
                old = current.read_bytes()
                previous = parse_design(old.decode(), path)
                if previous["id"] != record["id"] or previous["kind"] != record["kind"]:
                    raise ValueError("stable design identity/kind changed")
                if (
                    old != text.encode()
                    and record["version"] != previous["version"] + 1
                ):
                    raise ValueError("changed design must advance exactly one version")
                history = f"architecture/history/designs/{previous['id']}/v{previous['version']}-{digest(old)}.md"
                files[history] = old.decode()
            elif record["version"] != 1:
                raise ValueError("new design starts at version 1")
    projected, _ = generate_manifest(root, overlay=files)
    if not migration:
        old_index = strict_yaml(
            safe_path(root, "architecture/designs/index.yaml").read_text(
                encoding="utf-8"
            ),
            "index",
        )
        new_index = strict_yaml(
            files.get(
                "architecture/designs/index.yaml",
                safe_path(root, "architecture/designs/index.yaml").read_text(
                    encoding="utf-8"
                ),
            ),
            "index",
        )
        for source in sources:
            if (
                source != "architecture/designs/index.yaml"
                and source not in new_index["documents"]
            ):
                raise ValueError(
                    "changed source is absent from the final collection: " + source
                )
        changed_collection = set(old_index["documents"]) ^ set(new_index["documents"])
        if changed_collection and "architecture/designs/index.yaml" not in sources:
            raise ValueError(
                "source membership change requires the confirmed collection index"
            )
        for path in new_index["documents"]:
            if path not in old_index["documents"]:
                content = files.get(
                    path,
                    safe_path(root, path).read_text(encoding="utf-8")
                    if safe_path(root, path).exists()
                    else "",
                )
                record = parse_design(content, path)
                if (
                    record["id"],
                    record["version"],
                    digest(content.encode()),
                ) not in confirmed:
                    raise ValueError(
                        "newly activated design was not confirmed: " + path
                    )
        validate_candidate(root, projected, source_versions(root, files))
    files["architecture/manifest.yaml"] = yaml.safe_dump(
        projected, sort_keys=False, allow_unicode=True
    )
    expected = render_documents(projected)
    for path, content in expected.items():
        relative = "architecture/" + path.as_posix()
        target = safe_path(root, relative)
        if target.exists() and not target.read_text(encoding="utf-8").startswith(
            GENERATED_MARKER
        ):
            raise ValueError("generated target contains authored work: " + relative)
        files[relative] = content
    changes = _replace(root, files)
    if not migration:
        removed = set(old_index["documents"]) - set(new_index["documents"])
        for path in removed:
            target = safe_path(root, path)
            old = target.read_bytes()
            record = parse_design(old.decode(), path)
            confirmed_removal = next(
                (r for r in confirmed_refs if r["id"] == "REMOVE-" + record["id"]), None
            )
            if confirmed_removal is None:
                raise ValueError("removed design baseline was not confirmed: " + path)
            removal = parse_design(
                _resolve_design(root, confirmed_removal).read_text(encoding="utf-8"),
                confirmed_removal["path"],
            )["data"]
            if (
                set(removal) != {"removed_id", "current_path", "base_reference"}
                or removal["removed_id"] != record["id"]
                or removal["current_path"] != path
            ):
                raise ValueError("removal baseline identity differs")
            _resolve_design(root, removal["base_reference"])
            if digest(old) != removal["base_reference"]["sha256"]:
                raise ValueError(
                    "removed design base changed; retained difference: " + path
                )
            history = f"architecture/history/designs/{record['id']}/v{record['version']}-{digest(old)}.md"
            changes.update(_replace(root, {history: old.decode()}))
            changes[path] = {"before_sha256": digest(old), "content": None}
        if "architecture/designs/index.yaml" in sources:
            old = safe_path(root, "architecture/designs/index.yaml").read_bytes()
            history = f"architecture/history/designs/{old_index['id']}/v{old_index['version']}-{digest(old)}.yaml"
            changes.update(_replace(root, {history: old.decode()}))
    from render_architecture import EXTERNALLY_GENERATED_DOCUMENTS

    generated = root / "architecture/generated"
    for path in generated.rglob("*.md") if generated.is_dir() else []:
        relative = path.relative_to(root / "architecture")
        if (
            relative not in expected
            and relative not in EXTERNALLY_GENERATED_DOCUMENTS
            and path.read_text(encoding="utf-8").startswith(GENERATED_MARKER)
        ):
            changes[path.relative_to(root).as_posix()] = {
                "before_sha256": digest(path.read_bytes()),
                "content": None,
            }
    return prepare_update(
        root,
        operation_id,
        changes,
        binding=binding,
        validate_candidate=lambda candidate: None,
    )


def validate_candidate(root, manifest, versions):
    from check_architecture import validate_manifest
    from design_contract import validate_designs
    from coding_rule_contract import validate_rule_binding
    from os_design_contract import validate_os_designs

    diagnostics = validate_manifest(
        manifest,
        Path(root) / "architecture/manifest.yaml",
        None,
        None,
        check_docs=False,
    )
    messages = [d.message for d in diagnostics if d.severity == "MUST"]
    for checker in (validate_designs, validate_rule_binding):
        messages += [d["message"] for d in checker(manifest)]
    messages += [
        d["message"] for d in validate_os_designs(manifest, "design", versions)
    ]
    if messages:
        raise ValueError("candidate feasibility failed: " + "; ".join(messages))


def resume_design_update(root, operation_id, *, binding, authorize, migration=False):
    def verify():
        manifest, _ = generate_manifest(root)
        actual = strict_yaml(
            safe_path(root, "architecture/manifest.yaml").read_text(encoding="utf-8"),
            "architecture/manifest.yaml",
        )
        if actual != manifest:
            raise ValueError("manifest/source drift")
        if not migration:
            validate_candidate(root, manifest, source_versions(root))
        for path, content in render_documents(manifest).items():
            target = safe_path(root, "architecture/" + path.as_posix())
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                raise ValueError("generated view drift: " + str(path))
        from render_architecture import compare_documents

        if compare_documents(manifest, Path(root) / "architecture/manifest.yaml"):
            raise ValueError("generated views have stale or missing entries")

    return resume_update(
        root, operation_id, binding=binding, authorize=authorize, validate_result=verify
    )
