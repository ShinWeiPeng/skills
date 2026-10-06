"""Generate the complete manifest from uniquely owned Markdown design sources."""

from __future__ import annotations
import copy
import json
import sys
from pathlib import Path
import yaml

_owner = Path(__file__).resolve().parents[2] / "spec-governance/scripts"
if _owner.is_dir():
    sys.path.insert(0, str(_owner))
from document_bundle import parse_design, render_design, strict_yaml
from document_updates import safe_path, digest, assert_complete, locked_documents


def source_documents(manifest):
    """Every existing top-level field is preserved, including extension catalogs."""
    documents = {}
    design = manifest.get("implementation_design", {})
    for key, value in manifest.items():
        if key in {"modules", "flows"} and isinstance(value, list) and value:
            kind = "module" if key == "modules" else "flow"
            for row in value:
                identity = row.get("id")
                if (
                    not isinstance(identity, str)
                    or not identity
                    or "/" in identity
                    or "\\" in identity
                ):
                    raise ValueError("invalid source record ID")
                path = f"architecture/designs/{key}/{identity}.md"
                if path in documents:
                    raise ValueError("duplicate catalog ID: " + identity)
                data = {"manifest_record": row}
                if isinstance(design, dict) and identity in design.get(key, {}):
                    data["implementation_design"] = design[key][identity]
                documents[path] = render_design(identity, 1, kind, data)
        elif key == "implementation_design" and isinstance(value, dict):
            remainder = {
                k: v
                for k, v in value.items()
                if k not in {"modules", "flows", "interfaces"}
            }
            documents["architecture/designs/catalog/implementation_design.md"] = (
                render_design(
                    "CAT-implementation_design",
                    1,
                    "catalog",
                    {"manifest_field": "implementation_design", "value": remainder},
                )
            )
            for identity, record in value.get("interfaces", {}).items():
                if not isinstance(identity, str) or "/" in identity or "\\" in identity:
                    raise ValueError("invalid interface source ID")
                documents[f"architecture/designs/modules/interface-{identity}.md"] = (
                    render_design(
                        identity, 1, "interface", {"implementation_design": record}
                    )
                )
        elif key in {"platform_design", "execution_design"}:
            kind = key.split("_")[0]
            if not isinstance(value, dict) or set(value) != {"id", "version", "data"}:
                raise ValueError("expected platform/execution envelope")
            documents[f"architecture/designs/{kind}/{kind}.md"] = render_design(
                value["id"],
                value["version"],
                kind,
                {"manifest_field": key, "value": value["data"]},
            )
        else:
            if not isinstance(key, str) or not key.replace("_", "").isalnum():
                raise ValueError("invalid manifest field name")
            documents[f"architecture/designs/catalog/{key}.md"] = render_design(
                "CAT-" + key, 1, "catalog", {"manifest_field": key, "value": value}
            )
    if len({p.casefold() for p in documents}) != len(documents):
        raise ValueError("duplicate portable source path")
    index = {
        "format_version": 1,
        "id": "DESIGN-COLLECTION",
        "version": 1,
        "documents": list(documents),
    }
    documents["architecture/designs/index.yaml"] = yaml.safe_dump(
        index, sort_keys=False
    )
    return documents


@locked_documents
def generate_manifest(root, *, overlay=None):
    """Read current sources or a reviewed candidate overlay through the same parser."""
    root = Path(root).resolve()
    overlay = overlay or {}

    def read(relative):
        if relative in overlay:
            return overlay[relative]
        return safe_path(root, relative).read_text(encoding="utf-8")

    index = strict_yaml(
        read("architecture/designs/index.yaml"), "architecture/designs/index.yaml"
    )
    if (
        not isinstance(index, dict)
        or set(index) != {"format_version", "id", "version", "documents"}
        or index["format_version"] != 1
        or index["id"] != "DESIGN-COLLECTION"
        or type(index["version"]) is not int
        or index["version"] < 1
        or not isinstance(index["documents"], list)
    ):
        raise ValueError("unsupported design source index")
    if any(not isinstance(p, str) for p in index["documents"]) or len(
        {p.casefold() for p in index["documents"]}
    ) != len(index["documents"]):
        raise ValueError("duplicate source index path")
    assert_complete(
        root,
        [
            "architecture/designs/index.yaml",
            *index["documents"],
            "architecture/manifest.yaml",
        ],
    )
    manifest = {}
    modules = []
    flows = []
    implementation = {"modules": {}, "interfaces": {}, "flows": {}}
    identities = set()
    ownership = {}
    for relative in index["documents"]:
        if (
            not isinstance(relative, str)
            or not relative.startswith("architecture/designs/")
            or not relative.endswith(".md")
        ):
            raise ValueError("source index path outside current designs")
        safe_path(root, relative)
        record = parse_design(read(relative), relative)
        identity = record["id"]
        kind = record["kind"]
        data = record["data"]
        if identity in identities:
            raise ValueError(relative + ": duplicate design ID")
        identities.add(identity)
        if kind in {"catalog", "platform", "execution"}:
            if set(data) != {"manifest_field", "value"}:
                raise ValueError(relative + ": expected manifest_field and value")
            field = data["manifest_field"]
            if (
                not isinstance(field, str)
                or field in manifest
                or (field in {"modules", "flows"} and data["value"] != [])
            ):
                raise ValueError(
                    relative + ": duplicate or invalid manifest field owner"
                )
            manifest[field] = (
                {
                    "id": record["id"],
                    "version": record["version"],
                    "data": copy.deepcopy(data["value"]),
                }
                if kind in {"platform", "execution"}
                else copy.deepcopy(data["value"])
            )
            ownership[field] = relative
        elif kind in {"module", "flow"}:
            if (
                set(data) - {"manifest_record", "implementation_design"}
                or not isinstance(data.get("manifest_record"), dict)
                or data["manifest_record"].get("id") != identity
            ):
                raise ValueError(relative + ": record identity or fields differ")
            collection = "modules" if kind == "module" else "flows"
            (modules if kind == "module" else flows).append(data["manifest_record"])
            ownership[collection + "/" + identity] = relative
            if "implementation_design" in data:
                implementation[collection][identity] = data["implementation_design"]
        else:
            if set(data) != {"implementation_design"}:
                raise ValueError(relative + ": invalid interface design")
            implementation["interfaces"][identity] = data["implementation_design"]
            ownership["interfaces/" + identity] = relative
    # Source order retains original catalog order; no loss of extension keys.
    if modules or "modules" in manifest:
        manifest["modules"] = modules
    if flows or "flows" in manifest:
        manifest["flows"] = flows
    if "implementation_design" in manifest:
        if not isinstance(manifest["implementation_design"], dict):
            raise ValueError("implementation design catalog must be a mapping")
        if set(manifest["implementation_design"]) & set(implementation):
            raise ValueError("duplicate implementation design collection owner")
        manifest["implementation_design"].update(implementation)
    elif any(implementation.values()):
        raise ValueError("implementation design envelope has no owner")
    return manifest, ownership


def check_sources(root, manifest):
    root = Path(root)
    index = root / "architecture/designs/index.yaml"
    if not index.exists():
        return [
            {
                "rule_id": "DOC-SOURCE-001",
                "severity": "MUST",
                "configuration": True,
                "disposition": "active",
                "location": "architecture/designs/index.yaml",
                "message": "legacy manifest requires source migration before current design/implementation checks",
            }
        ]
    try:
        generated, owners = generate_manifest(root)
        if generated != manifest:
            raise ValueError(
                "generated manifest differs from maintained Markdown sources"
            )
        return []
    except (ValueError, OSError) as error:
        return [
            {
                "rule_id": "DOC-SOURCE-001",
                "severity": "MUST",
                "configuration": True,
                "disposition": "active",
                "location": "architecture/designs",
                "message": str(error),
            }
        ]


def migration_plan(root, manifest_path):
    root = Path(root).resolve()
    manifest_path = Path(manifest_path)
    original = manifest_path.read_bytes()
    manifest = strict_yaml(original.decode(), "architecture/manifest.yaml")
    files = source_documents(manifest)
    projected, _ = generate_manifest(root, overlay=files)
    if projected != manifest:
        raise ValueError("legacy source conversion changed manifest semantics")
    history = f"architecture/history/manifest/{digest(original)}.yaml"
    files[history] = original.decode()
    proof = {
        "format_version": 1,
        "source_sha256": digest(original),
        "history": history,
        "fields": sorted(manifest),
        "owners": generate_manifest(root, overlay=files)[1],
    }
    files["architecture/designs/migration-proof.json"] = (
        json.dumps(proof, sort_keys=True, ensure_ascii=True, indent=2) + "\n"
    )
    return files


@locked_documents
def source_versions(root, overlay=None):
    overlay = overlay or {}

    def read(path):
        return (
            overlay[path]
            if path in overlay
            else safe_path(root, path).read_text(encoding="utf-8")
        )

    index = strict_yaml(
        read("architecture/designs/index.yaml"), "architecture/designs/index.yaml"
    )
    records = {}
    for path in index["documents"]:
        record = parse_design(read(path), path)
        if record["id"] in records:
            raise ValueError("duplicate source ID")
        records[record["id"]] = {"version": record["version"], "kind": record["kind"]}
    return records
