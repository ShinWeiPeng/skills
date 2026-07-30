#!/usr/bin/env python3
"""Preview or apply an architecture manifest migration from 1.0.0 to 1.1.0."""

from __future__ import annotations

import argparse
import copy
import difflib
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

from check_architecture import LEGACY_SCHEMA_VERSION, LEGACY_STANDARD_VERSION, SCHEMA_VERSION, STANDARD_VERSION, load_yaml


def _dump(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def migrate(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    if data.get("schema_version") == SCHEMA_VERSION and data.get("standard_version") == STANDARD_VERSION:
        return copy.deepcopy(data), []
    if data.get("schema_version") != LEGACY_SCHEMA_VERSION or data.get("standard_version") != LEGACY_STANDARD_VERSION:
        raise ValueError("only standard/schema 1.0.0 can migrate to 1.1.0")

    migrated = copy.deepcopy(data)
    migrated["standard_version"] = STANDARD_VERSION
    migrated["schema_version"] = SCHEMA_VERSION
    project = migrated.setdefault("project", {})
    project.setdefault("documentation_language", "zh-TW")
    modules = [item for item in migrated.get("modules", []) if isinstance(item, dict)]
    ports = [item for item in migrated.get("ports", []) if isinstance(item, dict)]
    events = [item for item in migrated.get("events", []) if isinstance(item, dict)]
    checklist: list[str] = []

    for module in modules:
        module_id = str(module.get("id", "module"))
        purpose = module.pop("responsibility", "TODO: describe module purpose")
        owned_ports = [port for port in ports if port.get("owner") == module_id]
        module["implementation_status"] = "implemented"
        module["description"] = {
            "purpose": purpose,
            "input_ports": [str(port.get("id")) for port in owned_ports if port.get("direction") == "input"],
            "output_ports": [str(port.get("id")) for port in owned_ports if port.get("direction") == "output"],
            "emitted_events": [str(event.get("id")) for event in events if event.get("owner") == module_id],
            "owned_state": [],
            "side_effects": [],
            "errors": [],
            "invariants": [],
        }
        base_path = str((module.get("paths") or ["src"])[0]).rstrip("/")
        module["entrypoints"] = [
            {"path": f"{base_path}/TODO", "symbol": "TODO", "kind": "TODO"}
        ]
        public_path = str((module.get("public_headers") or [f"{base_path}/TODO"])[0])
        module["public_symbols"] = [
            {"path": public_path, "symbol": "TODO", "kind": "TODO"}
        ]
        checklist.extend(
            [
                f"{module_id}: complete owned_state, side_effects, errors, and invariants",
                f"{module_id}: replace TODO entrypoint and public symbol metadata",
            ]
        )

    module_symbols = {
        str(module.get("id")): str(module.get("public_symbols", [{}])[0].get("symbol", "TODO"))
        for module in modules
    }
    for port in ports:
        port_id = str(port.get("id", "port"))
        timing = "sync" if port.get("kind") in {"command", "query", "dependency"} else "async"
        port["description"] = {
            "purpose": f"TODO: describe {port_id}",
            "data": "TODO: describe data crossing this boundary",
            "timing": timing,
            "immediate_rejections": [],
        }
        port["symbols"] = [module_symbols.get(str(port.get("owner")), "TODO")]
        checklist.append(f"{port_id}: complete purpose, data semantics, timing, rejection cases, and symbols")

    for event in events:
        event_id = str(event.get("id", "event"))
        event["description"] = {
            "purpose": f"TODO: describe {event_id}",
            "emitted_when": "TODO: describe emission condition",
            "payload_fields": [],
            "intended_consumers": [],
        }
        checklist.append(f"{event_id}: complete purpose, emission condition, payload fields, and consumers")

    migrated["flows"] = []
    checklist.append("Define L0/L1-owned end-to-end flows before completing migration")
    return migrated, checklist


def migrate_baseline(data: dict[str, Any]) -> dict[str, Any]:
    version = data.get("schema_version")
    if version == SCHEMA_VERSION:
        return copy.deepcopy(data)
    if version != LEGACY_SCHEMA_VERSION:
        raise ValueError("baseline must use schema 1.0.0 or 1.1.0")
    migrated = copy.deepcopy(data)
    migrated["schema_version"] = SCHEMA_VERSION
    return migrated


def migrate_file(path: Path, write: bool = False) -> tuple[str, list[str], bool]:
    original_data = load_yaml(path)
    migrated, checklist = migrate(original_data)
    operations: list[tuple[Path, str, str]] = [
        (path, path.read_text(encoding="utf-8"), _dump(migrated))
    ]
    baseline_path = path.parent / "baseline.yaml"
    if baseline_path.is_file():
        baseline = load_yaml(baseline_path)
        operations.append(
            (baseline_path, baseline_path.read_text(encoding="utf-8"), _dump(migrate_baseline(baseline)))
        )
        checklist.append("baseline.yaml: schema version advances to 1.1.0; violation entries remain unchanged")

    changed_operations = [operation for operation in operations if operation[1] != operation[2]]
    diff = "".join(
        "".join(
            difflib.unified_diff(
                original_text.splitlines(keepends=True),
                migrated_text.splitlines(keepends=True),
                fromfile=str(target),
                tofile=str(target) + " (1.1.0)",
            )
        )
        for target, original_text, migrated_text in changed_operations
    )
    if write and changed_operations:
        for target, _, _ in changed_operations:
            backup = target.with_name(target.name + ".bak")
            if backup.exists():
                raise FileExistsError(f"refusing to replace existing backup: {backup}")
        for target, _, migrated_text in changed_operations:
            backup = target.with_name(target.name + ".bak")
            shutil.copy2(target, backup)
            temporary = target.with_name(target.name + ".tmp")
            temporary.write_text(migrated_text, encoding="utf-8")
            os.replace(temporary, target)
    return diff, checklist, bool(changed_operations)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--to", required=True, choices=(SCHEMA_VERSION,))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        diff, checklist, changed = migrate_file(args.manifest, args.write)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if diff:
        print(diff, end="" if diff.endswith("\n") else "\n")
    else:
        print("No migration changes required.")
    if checklist:
        print("Migration checklist:")
        for item in checklist:
            print(f"- {item}")
    if args.write and changed:
        print(f"Updated migration files beside {args.manifest}; each changed file has a .bak backup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
