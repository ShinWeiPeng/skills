from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


POLICY_PATH = Path(__file__).resolve().parents[1] / "references" / "formatter-policy.json"
PROJECT_STATES = ("absent", "present", "indeterminate")
DEFAULT_GOVERNANCE_PATHS = {
    ".agents",
    ".git",
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTEXT.md",
    "architecture",
    "spec-governance",
    "specs",
}


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def select_formatter(args: argparse.Namespace) -> dict:
    if "indeterminate" in (args.implementation, args.context):
        return {
            "status": "BLOCKED",
            "project_kind": "indeterminate",
            "reason": "ProjectState must be resolved before formatter selection.",
        }

    if (args.implementation, args.context) == ("absent", "absent"):
        policy = load_policy()
        language = policy.get("aliases", {}).get(args.language, args.language)
        language_policy = policy["languages"].get(language)
        if language_policy is None:
            return {
                "status": "BLOCKED",
                "project_kind": "greenfield",
                "reason": f"No governed formatter default for {args.language}.",
            }
        return {
            "status": "PASS",
            "project_kind": "greenfield",
            "language": language,
            "requested_language": args.language,
            **language_policy,
        }

    if not (
        args.repository_formatter
        and args.repository_formatter.strip()
        and args.repository_check_argv
        and args.repository_write_argv
    ):
        return {
            "status": "BLOCKED",
            "project_kind": "existing",
            "reason": "Repository formatter identity and commands have not been discovered.",
        }
    return {
        "status": "PASS",
        "project_kind": "existing",
        "formatter": args.repository_formatter.strip(),
        "check": args.repository_check_argv,
        "write": args.repository_write_argv,
        "reason": "Preserve the repository formatter and style.",
    }


def mutation_gate(args: argparse.Namespace) -> dict:
    try:
        project_root = Path(args.project_root).resolve(strict=True)
    except OSError as error:
        return {
            "status": "BLOCKED",
            "project_root": args.project_root,
            "reason": f"Exact project root is invalid: {error}",
        }
    if not args.selected_formatter.strip():
        return {
            "status": "BLOCKED",
            "project_root": str(project_root),
            "reason": "Formatter identity is missing.",
        }
    evidence = {
        "project_kind": args.project_kind,
        "project_root": str(project_root),
        "formatter": args.selected_formatter.strip(),
        "selection_status": args.selection_status.upper(),
        "preflight_status": args.preflight_status.upper(),
    }
    if not project_root.is_dir():
        return {"status": "BLOCKED", **evidence, "reason": "Project root is not a directory."}
    if args.selection_status != "pass":
        return {"status": "BLOCKED", **evidence, "reason": "Formatter selection has not passed."}
    if args.project_kind == "greenfield" and args.preflight_status != "pass":
        return {"status": "BLOCKED", **evidence, "reason": "Greenfield scaffold preflight has not passed."}
    if args.project_kind == "existing" and args.preflight_status != "not-applicable":
        return {"status": "BLOCKED", **evidence, "reason": "Existing projects do not use greenfield scaffold preflight."}
    if args.operation == "minimal-scaffold" and args.project_kind != "greenfield":
        return {"status": "BLOCKED", **evidence, "reason": "Minimal scaffold is allowed only for greenfield projects."}
    if args.install_requested and not args.install_authorized:
        return {
            "status": "BLOCKED",
            **evidence,
            "minimal_scaffold_allowed": False,
            "product_code_allowed": False,
            "reason": "Formatter installation or download requires explicit authorization.",
        }

    if args.operation == "minimal-scaffold":
        return {
            "status": "PASS",
            **evidence,
            "minimal_scaffold_allowed": True,
            "product_code_allowed": False,
            "reason": "Only minimal scaffold without product behavior is allowed.",
        }

    if not args.formatter_available:
        return {
            "status": "BLOCKED",
            **evidence,
            "minimal_scaffold_allowed": False,
            "product_code_allowed": False,
            "reason": "The selected formatter is unavailable.",
        }
    if args.check_status != "pass":
        return {
            "status": "BLOCKED",
            **evidence,
            "minimal_scaffold_allowed": False,
            "product_code_allowed": False,
            "reason": "The non-mutating formatter check has not passed.",
        }
    return {
        "status": "PASS",
        **evidence,
        "minimal_scaffold_allowed": False,
        "product_code_allowed": True,
        "reason": "Formatter availability and non-mutating check are verified.",
    }


def path_hash(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    for child in sorted(path.rglob("*"), key=lambda item: item.as_posix()):
        relative = child.relative_to(path).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        if child.is_file() and not child.is_symlink():
            digest.update(child.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def scaffold_preflight(args: argparse.Namespace) -> dict:
    requested_root = Path(args.project_root)
    try:
        project_root = requested_root.resolve(strict=True)
    except OSError as error:
        return {"status": "BLOCKED", "reason_code": "invalid-project-root", "reason": str(error)}
    if not project_root.is_dir():
        return {
            "status": "BLOCKED",
            "reason_code": "invalid-project-root",
            "reason": "The exact project root is not a directory.",
        }

    candidates = []
    for value in args.scaffold_path:
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            return {
                "status": "BLOCKED",
                "reason_code": "unsafe-scaffold-path",
                "reason": f"Scaffold path must stay relative to the project root: {value}",
            }
        if relative.parts[0].casefold() == project_root.name.casefold():
            return {
                "status": "BLOCKED",
                "reason_code": "nested-project-collision",
                "reason": f"Scaffold path repeats the selected project root: {value}",
            }
        candidate = project_root / relative
        try:
            candidate.resolve(strict=False).relative_to(project_root)
        except ValueError:
            return {
                "status": "BLOCKED",
                "reason_code": "unsafe-scaffold-path",
                "reason": f"Scaffold path resolves outside the project root: {value}",
            }
        candidates.append(candidate)

    collision_paths = []
    for candidate in candidates:
        inspected = [candidate]
        parent = candidate.parent
        while parent != project_root:
            inspected.append(parent)
            parent = parent.parent
        for path in inspected:
            if (path.exists() or path.is_symlink()) and path not in collision_paths:
                collision_paths.append(path)
    collisions = [
        {
            "path": path.relative_to(project_root).as_posix(),
            "kind": "directory" if path.is_dir() else "file",
            "sha256": path_hash(path),
        }
        for path in collision_paths
    ]
    if collisions:
        return {
            "status": "BLOCKED",
            "reason_code": "scaffold-path-collision",
            "project_root": str(project_root),
            "collisions": collisions,
        }

    allowed = DEFAULT_GOVERNANCE_PATHS | set(args.allow_existing)
    incompatible = sorted(
        child.name for child in project_root.iterdir() if child.name not in allowed
    )
    if incompatible:
        return {
            "status": "BLOCKED",
            "reason_code": "incompatible-existing-path",
            "project_root": str(project_root),
            "incompatible_paths": incompatible,
            "collisions": [],
        }

    return {
        "status": "PASS",
        "reason_code": "preflight-clear",
        "project_root": str(project_root),
        "scaffold_paths": [candidate.relative_to(project_root).as_posix() for candidate in candidates],
        "collisions": [],
    }


def parse_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def parse_argv(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError("expected a JSON argv array") from error
    if not isinstance(parsed, list) or not parsed or not all(
        isinstance(item, str) and item for item in parsed
    ):
        raise argparse.ArgumentTypeError("expected a non-empty JSON string array")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate governed formatter policy.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    select = subparsers.add_parser("select")
    select.add_argument("--implementation", choices=PROJECT_STATES, required=True)
    select.add_argument("--context", choices=PROJECT_STATES, required=True)
    select.add_argument("--language", required=True)
    select.add_argument("--repository-formatter")
    select.add_argument("--repository-check-argv", type=parse_argv)
    select.add_argument("--repository-write-argv", type=parse_argv)
    select.set_defaults(handler=select_formatter)
    gate = subparsers.add_parser("gate")
    gate.add_argument(
        "--operation", choices=("minimal-scaffold", "product-code"), required=True
    )
    gate.add_argument(
        "--formatter-available", choices=(True, False), type=parse_bool, required=True
    )
    gate.add_argument("--check-status", choices=("not-run", "pass", "fail"), required=True)
    gate.add_argument("--project-kind", choices=("greenfield", "existing"), required=True)
    gate.add_argument("--selection-status", choices=("pass", "blocked"), required=True)
    gate.add_argument(
        "--preflight-status", choices=("pass", "blocked", "not-applicable"), required=True
    )
    gate.add_argument("--project-root", required=True)
    gate.add_argument("--selected-formatter", required=True)
    gate.add_argument("--install-requested", action="store_true")
    gate.add_argument("--install-authorized", action="store_true")
    gate.set_defaults(handler=mutation_gate)
    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--project-root", required=True)
    preflight.add_argument("--scaffold-path", action="append", required=True)
    preflight.add_argument("--allow-existing", action="append", default=[])
    preflight.set_defaults(handler=scaffold_preflight)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = args.handler(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
