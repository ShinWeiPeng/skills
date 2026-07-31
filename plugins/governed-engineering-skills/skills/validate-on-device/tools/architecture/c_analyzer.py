#!/usr/bin/env python3
"""Analyze C/C++ include edges and public-header framework leakage."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from check_architecture import (
    BANNED_AI_APPROVERS,
    Diagnostic,
    ManifestError,
    dependency_violation,
    exit_code,
    load_yaml,
    render_text,
    validate_manifest,
)


SOURCE_SUFFIXES = {".c", ".h", ".cc", ".cpp", ".hh", ".hpp"}
INCLUDE_PATTERN = re.compile(r'^\s*#\s*include\s*"([^"]+)"')


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _relative_display(path: Path, root: Path) -> str:
    """Return a stable relative path even when Windows mixes 8.3 and long names."""
    return Path(os.path.relpath(str(path), str(root))).as_posix()


def _module_roots(project_root: Path, modules: dict[str, dict[str, Any]]) -> dict[str, list[Path]]:
    return {
        module_id: [(project_root / str(item)).resolve() for item in module.get("paths", [])]
        for module_id, module in modules.items()
    }


def _owner(path: Path, roots: dict[str, list[Path]]) -> str | None:
    candidates: list[tuple[int, str]] = []
    for module_id, module_roots in roots.items():
        for root in module_roots:
            if _inside(path, root):
                candidates.append((len(root.parts), module_id))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _source_files(
    project_root: Path,
    roots: dict[str, list[Path]],
    compile_commands: Path | None,
) -> tuple[list[Path], str, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    if compile_commands and compile_commands.is_file():
        try:
            entries = json.loads(compile_commands.read_text(encoding="utf-8"))
            files = []
            for entry in entries:
                if not isinstance(entry, dict) or "file" not in entry:
                    continue
                candidate = Path(str(entry["file"]))
                if not candidate.is_absolute():
                    candidate = Path(str(entry.get("directory", project_root))) / candidate
                candidate = candidate.resolve()
                if candidate.suffix.lower() in SOURCE_SUFFIXES and _inside(candidate, project_root):
                    files.append(candidate)
            return sorted(set(files)), "compile_commands+lexical", diagnostics
        except (OSError, json.JSONDecodeError) as exc:
            diagnostics.append(Diagnostic("CTOOL001", "MUST", str(compile_commands), f"invalid compile_commands.json: {exc}", True))
            return [], "compile_commands+lexical", diagnostics
    files: set[Path] = set()
    for module_roots in roots.values():
        for root in module_roots:
            if root.is_dir():
                files.update(path.resolve() for path in root.rglob("*") if path.suffix.lower() in SOURCE_SUFFIXES)
    return sorted(files), "lexical", diagnostics


def _resolve_include(
    include: str,
    source: Path,
    project_root: Path,
    known_files: list[Path],
) -> Path | None:
    direct = (source.parent / include).resolve()
    if direct.is_file() and _inside(direct, project_root):
        return direct
    root_relative = (project_root / include).resolve()
    if root_relative.is_file() and _inside(root_relative, project_root):
        return root_relative
    normalized = Path(include).as_posix()
    matches = [path for path in known_files if path.as_posix().endswith("/" + normalized)]
    return matches[0] if len(matches) == 1 else None


def _cycle(graph: dict[str, set[str]]) -> list[str] | None:
    active: list[str] = []
    done: set[str] = set()

    def visit(node: str) -> list[str] | None:
        if node in active:
            index = active.index(node)
            return active[index:] + [node]
        if node in done:
            return None
        active.append(node)
        for target in sorted(graph.get(node, set())):
            found = visit(target)
            if found:
                return found
        active.pop()
        done.add(node)
        return None

    for node in sorted(graph):
        found = visit(node)
        if found:
            return found
    return None


def _apply_dispositions(
    diagnostics: list[Diagnostic],
    manifest: dict[str, Any],
    manifest_path: Path,
    baseline_path: Path | None,
) -> None:
    baseline: set[tuple[str, str]] = set()
    if baseline_path and baseline_path.is_file():
        try:
            for entry in load_yaml(baseline_path).get("violations", []):
                if isinstance(entry, dict):
                    baseline.add((str(entry.get("rule_id")), str(entry.get("location"))))
        except ManifestError:
            pass
    exceptions = []
    for item in manifest.get("adr_exceptions", []):
        if not isinstance(item, dict) or item.get("status") != "accepted":
            continue
        approver = set(re.findall(r"[a-z]+", str(item.get("approved_by", "")).lower()))
        adr = manifest_path.parent / str(item.get("adr", ""))
        if not approver.intersection(BANNED_AI_APPROVERS) and item.get("approval_reference") and adr.is_file():
            exceptions.append(item)
    for diagnostic in diagnostics:
        if diagnostic.configuration:
            continue
        if (diagnostic.rule_id, diagnostic.location) in baseline:
            diagnostic.disposition = "baseline"
            continue
        for item in exceptions:
            if diagnostic.rule_id == item.get("rule_id") and diagnostic.location.startswith(str(item.get("scope", ""))):
                diagnostic.disposition = f"adr:{item.get('adr')}"
                break


def analyze(
    manifest: dict[str, Any],
    manifest_path: Path,
    project_root: Path,
    baseline_path: Path | None = None,
) -> tuple[list[Diagnostic], str]:
    diagnostics = validate_manifest(manifest, manifest_path, baseline_path)
    if exit_code(diagnostics) == 2:
        return diagnostics, "not-run"
    modules = {
        str(item["id"]): item
        for item in manifest.get("modules", [])
        if isinstance(item, dict) and item.get("id")
    }
    roots = _module_roots(project_root, modules)
    config = manifest.get("c_analyzer", {}) if isinstance(manifest.get("c_analyzer", {}), dict) else {}
    compile_commands_value = config.get("compile_commands", "compile_commands.json")
    compile_commands = project_root / str(compile_commands_value) if compile_commands_value else None
    files, mode, tool_diagnostics = _source_files(project_root, roots, compile_commands)
    diagnostics.extend(tool_diagnostics)
    known_files = sorted(set(files) | {path.resolve() for paths in roots.values() for root in paths if root.is_dir() for path in root.rglob("*") if path.suffix.lower() in SOURCE_SUFFIXES})

    ports = [item for item in manifest.get("ports", []) if isinstance(item, dict)]
    port_owner_by_implementation: dict[str, set[str]] = {}
    for port in ports:
        for adapter in port.get("implemented_by", []):
            port_owner_by_implementation.setdefault(str(adapter), set()).add(str(port.get("owner")))

    actual_graph: dict[str, set[str]] = {module_id: set() for module_id in modules}
    seen_edges: set[tuple[str, str, str]] = set()
    for source in files:
        source_owner = _owner(source, roots)
        if source_owner is None:
            continue
        try:
            lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            diagnostics.append(Diagnostic("CTOOL002", "MUST", str(source), f"cannot read source: {exc}", True))
            continue
        for line_number, line in enumerate(lines, 1):
            match = INCLUDE_PATTERN.match(line)
            if not match:
                continue
            target_file = _resolve_include(match.group(1), source, project_root, known_files)
            if target_file is None:
                continue
            target_owner = _owner(target_file, roots)
            if target_owner is None or target_owner == source_owner:
                continue
            location = f"{_relative_display(source, project_root)}:{line_number}"
            edge_key = (source_owner, target_owner, location)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            actual_graph[source_owner].add(target_owner)
            if target_owner not in modules[source_owner].get("depends_on", []):
                diagnostics.append(Diagnostic("CDEP001", "MUST", location, f"actual include edge {source_owner}->{target_owner} is not declared"))
            violation = dependency_violation(modules[source_owner], modules[target_owner], port_owner_by_implementation)
            if violation:
                diagnostics.append(Diagnostic(violation[0], "MUST", location, violation[1]))

    found_cycle = _cycle(actual_graph)
    if found_cycle:
        diagnostics.append(Diagnostic("CDEP002", "MUST", "->".join(found_cycle), "actual C/C++ include cycle is forbidden"))

    forbidden_includes = [str(item) for item in config.get("forbidden_public_includes", [])]
    forbidden_symbols = [str(item) for item in config.get("forbidden_public_symbols", [])]
    for module_id, module in modules.items():
        if manifest.get("schema_version") == "1.1.0":
            status = module.get("implementation_status")
            severity = "MUST" if status == "implemented" else "SHOULD"
            for module_path in module.get("paths", []):
                resolved_module_path = project_root / str(module_path)
                if not resolved_module_path.exists():
                    diagnostics.append(
                        Diagnostic(
                            "CSYM001",
                            severity,
                            str(module_path),
                            f"{status} module path does not exist",
                        )
                    )
            for field in ("entrypoints", "public_symbols"):
                for entry in module.get(field, []):
                    if not isinstance(entry, dict):
                        continue
                    relative_path = str(entry.get("path", ""))
                    source_path = project_root / relative_path
                    if source_path.suffix.lower() not in SOURCE_SUFFIXES:
                        continue
                    location = f"{module_id}.{field}:{relative_path}"
                    if not source_path.is_file():
                        diagnostics.append(
                            Diagnostic("CSYM002", severity, location, f"{status} C/C++ symbol file does not exist")
                        )
                        continue
                    symbol = str(entry.get("symbol", ""))
                    content = source_path.read_text(encoding="utf-8", errors="replace")
                    if not re.search(rf"\b{re.escape(symbol)}\b", content):
                        diagnostics.append(
                            Diagnostic("CSYM003", severity, location, f"symbol {symbol!r} was not found")
                        )
        if module.get("level") not in {"L0", "L1", "L2"}:
            continue
        public_patterns = list(module.get("public_headers", []))
        if manifest.get("schema_version") == "1.1.0":
            public_patterns.extend(
                str(entry.get("path"))
                for entry in module.get("public_symbols", [])
                if isinstance(entry, dict) and Path(str(entry.get("path", ""))).suffix.lower() in {".h", ".hh", ".hpp"}
            )
        for pattern in public_patterns:
            for header in project_root.glob(str(pattern)):
                if not header.is_file():
                    continue
                lines = header.read_text(encoding="utf-8", errors="replace").splitlines()
                for line_number, line in enumerate(lines, 1):
                    location = f"{_relative_display(header, project_root)}:{line_number}"
                    include_match = INCLUDE_PATTERN.match(line)
                    if include_match and any(token in include_match.group(1) for token in forbidden_includes):
                        diagnostics.append(Diagnostic("CLEAK001", "MUST", location, f"framework include leaks through public contract: {include_match.group(1)}"))
                    for symbol in forbidden_symbols:
                        if re.search(rf"\b{re.escape(symbol)}\b", line):
                            diagnostics.append(Diagnostic("CLEAK002", "MUST", location, f"framework symbol leaks through public contract: {symbol}"))

    c_diagnostics = [item for item in diagnostics if item.rule_id.startswith("C") or item.rule_id in {"DEP001", "DEP002", "DEP003"}]
    _apply_dispositions(c_diagnostics, manifest, manifest_path, baseline_path)
    return diagnostics, mode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        manifest = load_yaml(args.manifest)
        diagnostics, mode = analyze(manifest, args.manifest, args.project_root.resolve(), args.baseline)
    except ManifestError as exc:
        diagnostics = [Diagnostic("CTOOL000", "MUST", str(args.manifest), str(exc), True)]
        mode = "not-run"
    if args.format == "json":
        print(json.dumps({"analysis_mode": mode, "exit_code": exit_code(diagnostics), "diagnostics": [asdict(item) for item in diagnostics]}, indent=2))
    else:
        print(f"analysis_mode={mode}")
        print(render_text(diagnostics))
    return exit_code(diagnostics)


if __name__ == "__main__":
    raise SystemExit(main())
