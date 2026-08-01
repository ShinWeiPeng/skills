#!/usr/bin/env python3
"""Bootstrap versioned architecture governance files from a confirmed YAML spec."""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

from check_architecture import (
    SCHEMA_VERSION,
    STANDARD_VERSION,
    exit_code,
    load_yaml,
    render_text,
    validate_manifest,
)
from render_architecture import render_documents, write_documents
from governance_adoption import write_adoption_documents


SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets" / "project"


def _render(path: Path, replacements: dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _governance_files(
    project_root: Path, *, include_c_toolchain: bool
) -> dict[Path, str | Path]:
    files: dict[Path, str | Path] = {
        project_root / "AGENTS.md": ASSETS / "AGENTS.md.tmpl",
        project_root / "architecture" / "decisions" / "ADR-0001-modular-event-architecture.md": ASSETS / "ADR-0001-modular-event-architecture.md.tmpl",
        project_root / "tests" / "architecture" / "test_architecture.py": ASSETS / "test_architecture.py.tmpl",
        project_root / "tools" / "architecture" / "architecture_cli.py": SKILL_ROOT / "scripts" / "architecture_cli.py",
        project_root / "tools" / "architecture" / "check_architecture.py": SKILL_ROOT / "scripts" / "check_architecture.py",
        project_root / "tools" / "architecture" / "governance_adoption.py": SKILL_ROOT / "scripts" / "governance_adoption.py",
        project_root / "tools" / "architecture" / "python_analyzer.py": SKILL_ROOT / "scripts" / "python_analyzer.py",
        project_root / "tools" / "architecture" / "schema_description.py": SKILL_ROOT / "scripts" / "schema_description.py",
        project_root / "tools" / "architecture" / "schema_v2.py": SKILL_ROOT / "scripts" / "schema_v2.py",
        project_root / "tools" / "architecture" / "realtime_analysis.py": SKILL_ROOT / "scripts" / "realtime_analysis.py",
        project_root / "tools" / "architecture" / "type_catalog.py": SKILL_ROOT / "scripts" / "type_catalog.py",
        project_root / "tools" / "architecture" / "state_catalog.py": SKILL_ROOT / "scripts" / "state_catalog.py",
        project_root / "tools" / "architecture" / "source_sets.py": SKILL_ROOT / "scripts" / "source_sets.py",
        project_root / "tools" / "architecture" / "boundary_catalog.py": SKILL_ROOT / "scripts" / "boundary_catalog.py",
        project_root / "tools" / "architecture" / "ast_analyzer.py": SKILL_ROOT / "scripts" / "ast_analyzer.py",
        project_root / "tools" / "architecture" / "c_analyzer.py": SKILL_ROOT / "scripts" / "c_analyzer.py",
        project_root / "tools" / "architecture" / "libclang_toolchain_contract.py": SKILL_ROOT / "scripts" / "libclang_toolchain_contract.py",
        project_root / "tools" / "architecture" / "libclang_toolchain_adapter.py": SKILL_ROOT / "scripts" / "libclang_toolchain_adapter.py",
        project_root / "tools" / "architecture" / "render_architecture.py": SKILL_ROOT / "scripts" / "render_architecture.py",
        project_root / "tools" / "architecture" / "requirements.txt": SKILL_ROOT / "requirements-architecture.txt",
    }
    if include_c_toolchain:
        files[project_root / "architecture" / "toolchain-lock.yaml"] = (
            ASSETS / "toolchain-lock.yaml"
        )
    return files


def bootstrap(project_root: Path, spec_path: Path) -> list[Path]:
    project_root = project_root.resolve()
    spec = load_yaml(spec_path)
    adoption = spec.pop(
        "adoption",
        {
            "schema_version": SCHEMA_VERSION,
            "project_stage": "new",
            "applicable_analyzers": [
                name
                for name, configured in (
                    ("python", spec.get("python_analyzer", {}).get("status") == "required"),
                    ("c-cpp", spec.get("c_analyzer", {}).get("ast", {}).get("status") == "required"),
                )
                if configured
            ],
            "runtime_validation": {
                "applicability": "not-applicable",
                "rationale": "No target-runtime acceptance claim was declared in the confirmed bootstrap spec.",
            },
            "tool_host_evidence": {
                "operating_systems": ["windows", "linux"],
                "python_versions": ["3.11", "3.12", "3.13"],
            },
        },
    )
    spec.setdefault("standard_version", STANDARD_VERSION)
    spec.setdefault("schema_version", SCHEMA_VERSION)
    spec.setdefault("adr_exceptions", [])
    spec.setdefault("ports", [])
    spec.setdefault("events", [])
    spec.setdefault("types", [])
    spec.setdefault("type_exclusions", [])
    spec.setdefault("state_objects", [])
    spec.setdefault("boundary_mappings", [])
    spec.setdefault("source_sets", [])
    spec.setdefault("composition_roots", [])
    if spec.get("schema_version") == SCHEMA_VERSION:
        spec.setdefault("flows", [])
        spec.setdefault("project", {}).setdefault("documentation_language", "zh-TW")
        for field in (
            "workloads",
            "execution_profiles",
            "execution_units",
            "execution_mappings",
            "execution_channels",
            "data_access_profiles",
            "microarchitecture_profiles",
            "platform_variants",
            "realtime_scheduling_studies",
            "validation_profiles",
        ):
            spec.setdefault(field, [])
    manifest_path = project_root / "architecture" / "manifest.yaml"
    adoption_path = project_root / "architecture" / "adoption.yaml"
    baseline_path = project_root / "architecture" / "baseline.yaml"
    diagnostics = validate_manifest(spec, manifest_path)
    if exit_code(diagnostics) != 0:
        raise ValueError("confirmed spec is invalid:\n" + render_text(diagnostics))

    files = _governance_files(
        project_root,
        include_c_toolchain=(
            spec.get("c_analyzer", {}).get("ast", {}).get("status") == "required"
        ),
    )
    document_contents = render_documents(spec)
    extra_paths = [manifest_path, adoption_path, baseline_path]
    extra_paths.extend(manifest_path.parent / relative for relative in document_contents)
    extra_paths.extend(
        [
            manifest_path.parent / "generated" / "adoption-readiness.md",
            manifest_path.parent / "generated" / "adoption-readiness.json",
        ]
    )
    existing = sorted(path for path in [*files, *extra_paths] if path.exists())
    if existing:
        raise FileExistsError("refusing to overwrite governance files:\n" + "\n".join(str(path) for path in existing))

    replacements = {
        "PROJECT_NAME": str(spec["project"]["name"]),
        "DATE": dt.date.today().isoformat(),
    }
    written: list[Path] = []
    for destination, source in files.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_path = Path(source)
        if source_path.suffix == ".tmpl":
            destination.write_text(_render(source_path, replacements), encoding="utf-8")
        else:
            shutil.copy2(source_path, destination)
        written.append(destination)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding="utf-8")
    written.append(manifest_path)
    written.extend(write_documents(spec, manifest_path))
    adoption_path.write_text(
        yaml.safe_dump(adoption, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    baseline = {"schema_version": SCHEMA_VERSION, "violations": []}
    baseline_path.write_text(
        yaml.safe_dump(baseline, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    written.extend([adoption_path, baseline_path])
    bootstrap_evidence = {
        "phase": "development",
        "gate_result": "BLOCKED",
        "readiness_status": "DISCOVERED",
        "exit_code": 2,
        "analyzers": {},
        "diagnostics": [],
    }
    written.extend(
        write_adoption_documents(
            manifest_path, spec, adoption, baseline, bootstrap_evidence
        )
    )
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        written = bootstrap(args.project_root, args.spec)
    except (FileExistsError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("Created architecture governance files:")
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    print(
        "ERROR: direct legacy CLI removed; use architecture_cli.py bootstrap instead.",
        file=sys.stderr,
    )
    raise SystemExit(2)
