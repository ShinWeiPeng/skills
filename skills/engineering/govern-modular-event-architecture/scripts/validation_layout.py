"""Dedicated test/layout governance; independent of production type catalogs."""

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
        # Legacy analyzer/isolation declarations remain readable for migration.
        # They are not executed and never grant architecture or runtime coverage.
        coverage["dependency_analysis"] = "outside-layout-scope"
        coverage["language_analysis"] = "not-required"
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
