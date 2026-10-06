"""Dedicated test/layout governance; independent of production type catalogs."""

import ast
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import sys
import stat
import yaml


ROLES = {
    "test",
    "support",
    "fixture",
    "validation-definition",
    "run-output",
    "legacy-output",
    "specification",
    "production",
    "tooling",
    "documentation",
    "template",
    "generated",
    "third-party",
    "build-output",
    "governance-state",
    "metadata",
}
CODE = {".py", ".c", ".cpp", ".cc", ".h", ".hpp", ".rs", ".go", ".js", ".ts", ".java"}


def _diag(items, rule, path, expected, reason, blocked=False):
    items.append(
        dict(
            rule_id=rule,
            severity="MUST",
            location=path,
            expected=expected,
            message=reason + "; expected " + expected,
            configuration=blocked,
            disposition="active",
        )
    )


def _matches(path, entry):
    return any(
        fnmatch.fnmatchcase(path, pattern) for pattern in entry.get("include", [])
    ) and not any(
        fnmatch.fnmatchcase(path, pattern) for pattern in entry.get("exclude", [])
    )


def _safe(root, relative):
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or ":" in relative
        or relative.startswith("/")
        or any(p in {"", ".", ".."} for p in relative.split("/"))
    ):
        raise ValueError("expected portable project-relative path")
    current = root
    for part in relative.split("/"):
        current /= part
        if (
            current.is_symlink()
            or (
                current.exists()
                and getattr(current.lstat(), "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            )
            or getattr(current, "is_junction", lambda: False)()
        ):
            raise ValueError("redirected path")
    return current


def _read(path):
    if path.stat().st_size > 1048576:
        raise ValueError("policy/evidence exceeds 1 MiB")
    result = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError("expected a mapping")
    return result


def _suite(path):
    parts = path.split("/")
    return (
        "/".join(parts[:3])
        if len(parts) > 3 and parts[:2] in (["tests", "modules"], ["tests", "flows"])
        else None
    )


def _edge(items, source, target, records):
    source_role = records[source]["role"]
    target_role = records[target]["role"]
    if source_role == "production" and target_role in {"test", "support", "fixture"}:
        _diag(
            items,
            "DEP001",
            source,
            "production contracts",
            "production depends on test asset: " + target,
        )
    if "/support/" in target and _suite(target) and _suite(source) != _suite(target):
        _diag(
            items,
            "DEP002",
            source,
            "tests/support/<capability>/",
            "cross-suite private helper: " + target,
        )
    if (
        (source_role == "support" or source.startswith("tests/support/"))
        and target_role == "test"
        and "/support/" not in target
    ):
        _diag(
            items,
            "DEP003",
            source,
            "support independent of cases",
            "support depends on case: " + target,
        )


def _python_edges(root, records, items, resolutions, external_modules):
    files = [
        p
        for p, e in records.items()
        if p.endswith(".py")
        and e["role"] in {"test", "support", "production", "tooling"}
    ]
    names = {}
    for path in files:
        name = path[:-3].replace("/", ".")
        if name.endswith(".__init__"):
            name = name[:-9]
        components = name.split(".")
        for offset in range(len(components)):
            names.setdefault(".".join(components[offset:]), []).append(path)
    edges = 0
    for path in sorted(files):
        try:
            tree = ast.parse((root / path).read_text(encoding="utf-8-sig"))
        except (SyntaxError, UnicodeError, OSError) as exc:
            _diag(items, "DEP004", path, "parseable Python AST", str(exc), True)
            continue
        dynamic_aliases = {
            "__import__",
            "import_module",
            "spec_from_file_location",
            "run_path",
            "exec",
            "eval",
        }
        for imported_node in ast.walk(tree):
            if isinstance(imported_node, ast.ImportFrom):
                for alias in imported_node.names:
                    if alias.name in dynamic_aliases:
                        dynamic_aliases.add(alias.asname or alias.name)
        for node in ast.walk(tree):
            imported = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    package = path.split("/")[: -node.level]
                    base = ".".join(package + ([base] if base else []))
                imported = [base] + [
                    base + "." + alias.name
                    for alias in node.names
                    if base + "." + alias.name in names
                ]
            for name in imported:
                targets = sorted(set(names.get(name, [])))
                if len(targets) > 1:
                    sibling = str(Path(path).parent / (name + ".py")).replace("\\", "/")
                    targets = [sibling] if sibling in targets else targets
                if len(targets) > 1:
                    _diag(
                        items,
                        "DEP005",
                        path,
                        "unambiguous import resolution",
                        name,
                        True,
                    )
                elif targets:
                    _edge(items, path, targets[0], records)
                    edges += 1
                elif name.split(".")[0] not in set(sys.stdlib_module_names) | set(
                    external_modules
                ):
                    _diag(
                        items,
                        "DEP005",
                        path,
                        "existing owned test dependency",
                        name,
                        True,
                    )
            if isinstance(node, ast.Call):
                function = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                if function in dynamic_aliases:
                    evidence = resolutions.get(path, {})
                    digest = hashlib.sha256((root / path).read_bytes()).hexdigest()
                    if (
                        evidence.get("sha256") != digest
                        or not evidence.get("rationale")
                        or not isinstance(evidence.get("targets"), list)
                    ):
                        _diag(
                            items,
                            "DEP006",
                            path,
                            "source-bound dynamic dependency resolution",
                            "dynamic loading requires reviewed targets",
                            True,
                        )
                    else:
                        for target in evidence["targets"]:
                            if target not in records:
                                _diag(
                                    items,
                                    "DEP006",
                                    path,
                                    "existing resolved target",
                                    str(target),
                                    True,
                                )
                            else:
                                _edge(items, path, target, records)
        if records[path]["role"] == "test":
            for node in ast.walk(tree):
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    targets = (
                        node.targets if isinstance(node, ast.Assign) else [node.target]
                    )
                    for target in targets:
                        if (
                            isinstance(target, ast.Attribute)
                            and target.attr.startswith("_")
                            and not (
                                isinstance(target.value, ast.Name)
                                and target.value.id in {"self", "cls"}
                            )
                        ):
                            _diag(
                                items,
                                "DEP007",
                                path,
                                "module-owned controlled test seam",
                                "private attribute mutation requires an owned test hook",
                            )
    return dict(
        files=len(files), edges=edges, mode="python-ast-and-source-bound-resolutions"
    )


def assess_layout(project_root, manifest, *, analyzer_evidence=None):
    """Return full-scope diagnostics and honest rule coverage; never mutate files."""
    root = Path(project_root).resolve()
    items = []
    records = {}
    coverage = {}
    try:
        policy = _read(_safe(root, "validation/layout.yaml"))
        if (
            policy.get("schema_version") != 1
            or type(policy.get("schema_version")) is not int
        ):
            raise ValueError("adopt validation/layout.yaml schema_version: 1")
        allowed = {
            "schema_version",
            "entries",
            "required_analyzers",
            "references",
            "output_bindings",
            "external_resources",
            "dynamic_dependencies",
            "release_isolation",
            "external_modules",
        }
        if set(policy) - allowed or not isinstance(policy.get("entries"), list):
            raise ValueError("unknown layout field or missing entries")
        entries = policy["entries"]
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or entry.get("role") not in ROLES
                or not isinstance(entry.get("include"), list)
                or not entry["include"]
                or not all(
                    isinstance(p, str)
                    and p
                    and not p.startswith("/")
                    and ".." not in p.split("/")
                    for p in entry["include"]
                )
            ):
                raise ValueError("invalid role declaration")
            if entry["role"] in {
                "third-party",
                "build-output",
                "generated",
                "fixture",
                "template",
                "legacy-output",
            } and not entry.get("provenance"):
                raise ValueError("provenance required for " + entry["role"])
        module_ids = {m["id"] for m in manifest.get("modules", [])}
        flow_ids = {f["id"] for f in manifest.get("flows", [])}
        storage_path = (
            Path(__file__).resolve().parents[2] / "verification-ladder/scripts"
        )
        if storage_path.is_dir():
            sys.path.insert(0, str(storage_path))
        from run_storage import can_prune

        for current, directories, files in os.walk(root, followlinks=False):
            keep = []
            for name in sorted(directories):
                relative = (Path(current) / name).relative_to(root).as_posix()
                if relative == ".git":
                    continue
                _safe(root, relative)
                pruned = [
                    e
                    for e in entries
                    if e["role"] in {"third-party", "build-output"}
                    and _matches(relative + "/", e)
                ]
                if pruned and can_prune(
                    relative, entries, {"third-party", "build-output"}
                ):
                    # Exclusions must also match an architecture source-set boundary.
                    source_sets = manifest.get("source_sets", [])
                    proven = any(
                        s.get("classification") == "build-output"
                        and s.get("provenance")
                        and _matches(relative + "/", s)
                        for s in source_sets
                    )
                    if not proven:
                        _diag(
                            items,
                            "LAY009",
                            relative,
                            "provenance-controlled architecture source set",
                            "unproven exclusion",
                            True,
                        )
                    continue
                keep.append(name)
            directories[:] = keep
            for name in sorted(files):
                relative = (Path(current) / name).relative_to(root).as_posix()
                _safe(root, relative)
                if relative in {".gitignore", ".gitattributes", ".git"}:
                    continue
                matches = [e for e in entries if _matches(relative, e)]
                if len(matches) != 1:
                    _diag(
                        items,
                        "LAY001",
                        relative,
                        "exactly one declared role",
                        "unknown or ambiguous classification",
                        True,
                    )
                    continue
                entry = matches[0]
                role = entry["role"]
                records[relative] = entry
                parts = relative.split("/")
                if "tests" in parts[1:] and role not in {
                    "run-output",
                    "legacy-output",
                    "fixture",
                    "template",
                    "generated",
                    "build-output",
                    "third-party",
                }:
                    _diag(
                        items,
                        "LAY002",
                        relative,
                        "tests/modules/<module-id>/ or tests/flows/<flow-id>/",
                        "legacy nested test root",
                    )
                if (
                    "validation" in parts[1:]
                    and parts[0] != "artifacts"
                    and role not in {"template", "fixture", "generated"}
                ):
                    _diag(
                        items,
                        "LAY002",
                        relative,
                        "validation/ definitions or artifacts/ run outputs",
                        "legacy nested validation root",
                    )
                if Path(relative).suffix == ".py" and role in {
                    "production",
                    "tooling",
                    "metadata",
                    "documentation",
                }:
                    tree = ast.parse((root / relative).read_text(encoding="utf-8-sig"))
                    test_functions = any(
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name.startswith("test_")
                        for node in tree.body
                    )
                    test_classes = any(
                        isinstance(node, ast.ClassDef)
                        and any(
                            (
                                isinstance(base, ast.Attribute)
                                and base.attr == "TestCase"
                            )
                            or (isinstance(base, ast.Name) and base.id == "TestCase")
                            for base in node.bases
                        )
                        for node in tree.body
                    )
                    if test_functions or test_classes:
                        _diag(
                            items,
                            "LAY002",
                            relative,
                            "declared owned tests/ source",
                            "test declarations classified as non-test code",
                        )
                if role in {"test", "support", "fixture"}:
                    valid = (
                        len(parts) >= 4
                        and parts[0] == "tests"
                        and parts[1] in {"modules", "flows", "support"}
                    )
                    expected = "tests/modules/<module-id>/ or tests/flows/<flow-id>/ or tests/support/<capability>/"
                    if not valid:
                        _diag(
                            items, "LAY002", relative, expected, "misplaced test asset"
                        )
                    elif parts[1] != "support":
                        known = module_ids if parts[1] == "modules" else flow_ids
                        if entry.get("owner") != parts[2] or parts[2] not in known:
                            _diag(
                                items,
                                "LAY005",
                                relative,
                                "declared existing Module/Flow owner",
                                "unknown or mismatched owner",
                                True,
                            )
                    elif not entry.get("owner") or entry["owner"] not in module_ids:
                        _diag(
                            items,
                            "LAY005",
                            relative,
                            "shared support owner Module",
                            "unknown support owner",
                            True,
                        )
                if role == "validation-definition" and parts[0] != "validation":
                    _diag(
                        items,
                        "LAY002",
                        relative,
                        "validation/",
                        "misplaced validation definition",
                    )
                if role == "run-output" and (
                    len(parts) < 4
                    or parts[:2]
                    not in (["artifacts", "tests"], ["artifacts", "validation"])
                ):
                    _diag(
                        items,
                        "LAY003",
                        relative,
                        "artifacts/<kind>/<run-id>/",
                        "output lacks independent run identity",
                    )
                if role == "legacy-output" and parts[:2] != ["artifacts", "legacy"]:
                    _diag(
                        items,
                        "LAY003",
                        relative,
                        "artifacts/legacy/<migration>/",
                        "legacy output lacks migration boundary",
                    )
                if role in {"run-output", "legacy-output"} and parts[0] != "artifacts":
                    _diag(
                        items,
                        "LAY003",
                        relative,
                        "artifacts/<kind>/<run-id>/",
                        "misplaced generated evidence",
                    )
                if parts[0] == "specs" and (
                    "evidence" in parts
                    or role != "specification"
                    or Path(relative).suffix.lower() != ".md"
                ):
                    _diag(
                        items,
                        "LAY003",
                        relative,
                        "artifacts/<kind>/<run-id>/",
                        "specs contains non-specification data",
                    )
                if (
                    parts[0] == "validation"
                    and (
                        Path(relative).suffix.lower() in {".log", ".png", ".csv"}
                        or name.startswith("evidence-")
                        or "report" in name.lower()
                    )
                    and role != "template"
                ):
                    _diag(
                        items,
                        "LAY003",
                        relative,
                        "artifacts/<kind>/<run-id>/",
                        "generated evidence in definition area",
                    )
                if parts[0] == "tests" and role in {"run-output", "legacy-output"}:
                    _diag(
                        items,
                        "LAY003",
                        relative,
                        "artifacts/<kind>/<run-id>/",
                        "test output mixed with input",
                    )
                if role == "test" and Path(relative).suffix.lower() in {
                    ".log",
                    ".png",
                    ".csv",
                }:
                    _diag(
                        items,
                        "LAY001",
                        relative,
                        "explicit curated fixture provenance or artifacts/",
                        "ambiguous input/output",
                        True,
                    )
        run_roots = sorted(
            {
                "/".join(p.split("/")[:3])
                for p, e in records.items()
                if e["role"] == "run-output" and len(p.split("/")) >= 4
            }
        )
        if run_roots:
            storage_path = (
                Path(__file__).resolve().parents[2] / "verification-ladder/scripts"
            )
            if storage_path.is_dir():
                sys.path.insert(0, str(storage_path))
            from run_storage import validate_run, read_json

            for run in run_roots:
                terminal = _safe(root, run + "/manifest.json")
                try:
                    if terminal.is_file():
                        validate_run(root, terminal)
                    else:
                        identity = read_json(_safe(root, run + "/.run.json"))
                        if identity.get("run_id") != run.split("/")[-1]:
                            raise ValueError("incomplete run identity mismatch")
                        # Incomplete allocation is retained but never acceptance evidence.
                        pass
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    _diag(
                        items,
                        "RUN001",
                        run,
                        "valid allocated run or intact terminal manifest",
                        str(exc),
                    )
        required = policy.get("required_analyzers", [])
        if not isinstance(required, list):
            raise ValueError("required_analyzers must be a list")
        if "python" in required:
            coverage["python"] = _python_edges(
                root,
                records,
                items,
                policy.get("dynamic_dependencies", {}),
                policy.get("external_modules", []),
            )
        for capability in required:
            if capability == "python":
                continue
            evidence = (analyzer_evidence or {}).get(capability)
            if (
                not evidence
                or evidence.get("mode") != "ast"
                or evidence.get("test_dependency_coverage") != "complete"
            ):
                _diag(
                    items,
                    "CAP001",
                    "validation/layout.yaml",
                    "capable " + str(capability) + " test dependency adapter",
                    "required capability unavailable",
                    True,
                )
            else:
                coverage[capability] = evidence
        for path, entry in records.items():
            suffix = Path(path).suffix
            if entry["role"] in {"production", "test", "support"} and suffix in CODE:
                needed = (
                    "python"
                    if suffix == ".py"
                    else "c-cpp"
                    if suffix in {".c", ".cpp", ".cc", ".h", ".hpp"}
                    else suffix[1:]
                )
                if needed not in required:
                    _diag(
                        items,
                        "CAP001",
                        path,
                        "required analyzer: " + needed,
                        "dependency coverage undeclared",
                        True,
                    )
        for reference in policy.get("references", []):
            path = _safe(root, reference["path"])
            if not path.is_file() or hashlib.sha256(
                path.read_bytes()
            ).hexdigest() != reference.get("sha256"):
                _diag(
                    items,
                    "REF001",
                    reference["path"],
                    "existing hash-bound fixed reference",
                    "missing or changed reference",
                )
        for binding in policy.get("output_bindings", []):
            path = binding.get("root")
            if path not in {"artifacts/tests", "artifacts/validation"}:
                _diag(
                    items,
                    "LAY006",
                    str(path),
                    "artifacts/tests or artifacts/validation",
                    "invalid writer destination",
                )
        for resource in policy.get("external_resources", []):
            if (
                resource.get("isolation") not in {"per-case", "serialized"}
                or not resource.get("owner")
                or not resource.get("cleanup")
            ):
                _diag(
                    items,
                    "ISO001",
                    "validation/layout.yaml",
                    "owner, isolation and cleanup",
                    "shared external resource lacks isolation",
                    True,
                )
        if policy.get("release_isolation"):
            _diag(
                items,
                "CAP002",
                "validation/layout.yaml",
                "source-bound build/runtime release isolation evidence",
                "test control release claim requires capable evidence adapter",
                True,
            )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        SyntaxError,
        yaml.YAMLError,
    ) as exc:
        _diag(
            items,
            "LAY000",
            "validation/layout.yaml",
            "valid explicit layout adoption",
            str(exc),
            True,
        )
    items.sort(key=lambda d: (d["location"], d["rule_id"], d["message"]))
    verdict = (
        "FAIL"
        if any(not d["configuration"] for d in items)
        else "BLOCKED"
        if items
        else "PASS"
    )
    return dict(
        verdict=verdict,
        diagnostics=items,
        coverage=dict(
            layout="whole-filesystem-declared-scope",
            runtime_isolation="not-proven-by-layout",
            **coverage,
        ),
        files=sum(
            e["role"] not in {"run-output", "legacy-output", "governance-state"}
            for e in records.values()
        ),
    )
