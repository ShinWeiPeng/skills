from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


POLICY_PATH = (
    Path(__file__).resolve().parents[1] / "references" / "formatter-policy.json"
)
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


def governed_language_policy(language: str) -> tuple[str, dict | None]:
    policy = load_policy()
    canonical_language = policy.get("aliases", {}).get(language, language)
    return canonical_language, policy["languages"].get(canonical_language)


def collect_program_files(project_root: Path, language: str) -> list[str]:
    policy = load_policy()
    scope_policy = policy["program_scope"]
    extensions = set(scope_policy["extensions"].get(language, []))
    excluded_parts = {part.casefold() for part in scope_policy["excluded_path_parts"]}
    excluded_roots = {part.casefold() for part in scope_policy["excluded_root_paths"]}
    excluded_filenames = {
        filename.casefold() for filename in scope_policy["excluded_filenames"]
    }
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        candidates = (
            path.relative_to(project_root).as_posix()
            for path in project_root.rglob("*")
            if path.is_file()
        )
    else:
        candidates = (
            value.decode("utf-8") for value in completed.stdout.split(b"\0") if value
        )
    selected = []
    for value in candidates:
        relative = Path(value)
        if relative.parts and relative.parts[0].casefold() in excluded_roots:
            continue
        if relative.name.casefold() in excluded_filenames:
            continue
        if any(part.casefold() in excluded_parts for part in relative.parts):
            continue
        if relative.suffix.casefold() in extensions:
            selected.append(relative.as_posix())
    return sorted(set(selected))


def dirty_program_files(
    project_root: Path, program_files: list[str]
) -> list[str] | None:
    if not program_files:
        return []
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "status",
            "--porcelain=v1",
            "-z",
            "--",
            *program_files,
        ],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return sorted(
        {
            entry[3:].decode("utf-8").replace("\\", "/")
            for entry in completed.stdout.split(b"\0")
            if len(entry) > 3
        }
    )


def scoped_argv(
    argv: list[str],
    program_files: list[str],
    require_explicit_scope: bool,
    formatter: str,
) -> list[str] | None:
    if require_explicit_scope:
        placeholders = [value for value in argv if value in (".", "<files>")]
        if len(placeholders) != 1:
            return None
        formatter_prefix = formatter.split()
        prefix_length = (
            len(formatter_prefix)
            if argv[: len(formatter_prefix)] == formatter_prefix
            else 1
        )
        if any(
            value not in (".", "<files>") and not value.startswith("-")
            for value in argv[prefix_length:]
        ):
            return None

    scoped = []
    for value in argv:
        if value in (".", "<files>"):
            scoped.extend(program_files)
        else:
            scoped.append(value)
    return scoped


def canonical_spec_is_valid(spec_path: Path, spec_text: str) -> bool:
    filename = re.fullmatch(
        r"(SPEC-\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md", spec_path.name
    )
    if filename is None or not spec_text.startswith("---\n"):
        return False
    try:
        frontmatter, _ = spec_text[4:].split("\n---\n", 1)
    except ValueError:
        return False
    metadata = {}
    for line in frontmatter.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    return (
        metadata.get("spec_version") == "1"
        and metadata.get("spec_id") == filename.group(1)
        and metadata.get("revision", "").isdigit()
        and int(metadata["revision"]) > 0
        and metadata.get("status") in ("confirmed", "implemented")
        and metadata.get("change_set") == filename.group(2)
    )


def select_formatter(args: argparse.Namespace) -> dict:
    if "indeterminate" in (args.implementation, args.context):
        return {
            "status": "BLOCKED",
            "project_kind": "indeterminate",
            "reason": "ProjectState must be resolved before formatter selection.",
        }

    if (args.implementation, args.context) == ("absent", "absent"):
        language, language_policy = governed_language_policy(args.language)
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

    repository_evidence = (
        args.repository_formatter,
        args.repository_check_argv,
        args.repository_write_argv,
    )
    if any(repository_evidence) and not all(repository_evidence):
        return {
            "status": "BLOCKED",
            "project_kind": "existing",
            "reason": "Repository formatter evidence is incomplete.",
        }
    if not any(repository_evidence):
        language, language_policy = governed_language_policy(args.language)
        if language_policy is None:
            return {
                "status": "BLOCKED",
                "project_kind": "existing",
                "reason": f"No governed formatter fallback for {args.language}.",
            }
        return {
            "status": "PASS",
            "project_kind": "existing",
            "language": language,
            "requested_language": args.language,
            "policy_source": "governed-fallback",
            **language_policy,
            "reason": "No repository formatter was discovered; use the governed fallback.",
        }
    language, _ = governed_language_policy(args.language)
    return {
        "status": "PASS",
        "project_kind": "existing",
        "language": language,
        "requested_language": args.language,
        "formatter": args.repository_formatter.strip(),
        "check": args.repository_check_argv,
        "write": args.repository_write_argv,
        "policy_source": "repository",
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
        return {
            "status": "BLOCKED",
            **evidence,
            "reason": "Project root is not a directory.",
        }
    if args.selection_status != "pass":
        return {
            "status": "BLOCKED",
            **evidence,
            "reason": "Formatter selection has not passed.",
        }
    if args.project_kind == "greenfield" and args.preflight_status != "pass":
        return {
            "status": "BLOCKED",
            **evidence,
            "reason": "Greenfield scaffold preflight has not passed.",
        }
    if args.project_kind == "existing" and args.preflight_status != "not-applicable":
        return {
            "status": "BLOCKED",
            **evidence,
            "reason": "Existing projects do not use greenfield scaffold preflight.",
        }
    if args.operation == "minimal-scaffold" and args.project_kind != "greenfield":
        return {
            "status": "BLOCKED",
            **evidence,
            "reason": "Minimal scaffold is allowed only for greenfield projects.",
        }
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


def full_format_workflow(args: argparse.Namespace) -> dict:
    project_root = Path(args.project_root).resolve()
    spec_path = (project_root / args.canonical_spec).resolve()
    try:
        spec_path.relative_to(project_root / "specs")
        spec_text = spec_path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return {
            "status": "BLOCKED",
            "reason_code": "canonical-spec-required",
            "reason": "A governed canonical SPEC under specs/ is required.",
        }
    if args.spec_verification_status != "pass" or not canonical_spec_is_valid(
        spec_path, spec_text
    ):
        return {
            "status": "BLOCKED",
            "reason_code": "canonical-spec-invalid",
            "reason": "A canonical SPEC and passing spec-governance verification are required.",
        }

    selection = select_formatter(args)
    if selection["status"] != "PASS":
        return selection
    program_files = collect_program_files(project_root, selection["language"])
    if not program_files:
        return {
            **selection,
            "status": "BLOCKED",
            "reason_code": "empty-program-scope",
            "reason": "No product-source or test files match the governed language scope.",
        }
    require_explicit_scope = selection.get("policy_source") == "repository"
    scoped_check = scoped_argv(
        selection["check"],
        program_files,
        require_explicit_scope,
        selection["formatter"],
    )
    scoped_write = scoped_argv(
        selection["write"],
        program_files,
        require_explicit_scope,
        selection["formatter"],
    )
    if scoped_check is None or scoped_write is None:
        return {
            **selection,
            "status": "BLOCKED",
            "reason_code": "unscoped-formatter-command",
            "program_files": program_files,
            "reason": "Repository formatter commands must declare the governed file scope.",
        }
    selection = {
        **selection,
        "check": scoped_check,
        "write": scoped_write,
    }
    evidence = {
        **selection,
        "canonical_spec": spec_path.relative_to(project_root).as_posix(),
        "spec_verification_status": args.spec_verification_status,
        "program_files": program_files,
        "confirmation_required": True,
        "format_write_allowed": False,
        "format_completed": False,
        "delivery_validation": "separate",
        "install_permission": args.install_permission,
        "install_status": args.install_status,
        "pre_write_clean_status": args.pre_write_clean_status,
    }
    if args.confirmation == "pending":
        return {
            **evidence,
            "status": "BLOCKED",
            "reason_code": "confirmation-required",
            "reason": "Ask once whether to format the complete program-source scope.",
        }
    if args.confirmation != "yes":
        return {
            **evidence,
            "status": "PASS" if args.confirmation == "no" else "BLOCKED",
            "reason_code": "format-declined"
            if args.confirmation == "no"
            else "confirmation-ambiguous",
            "reason": "Formatting was declined."
            if args.confirmation == "no"
            else "Formatting requires an affirmative answer.",
        }
    if args.write_status == "not-run":
        dirty_files = dirty_program_files(project_root, program_files)
        if dirty_files is None:
            return {
                **evidence,
                "status": "BLOCKED",
                "reason_code": "target-cleanliness-unverified",
                "reason": "Git could not verify the program-source target state.",
            }
        if dirty_files:
            return {
                **evidence,
                "status": "BLOCKED",
                "reason_code": "dirty-program-targets",
                "dirty_files": dirty_files,
                "reason": "Pre-existing program-source changes block full formatting.",
            }
    elif args.pre_write_clean_status != "pass":
        return {
            **evidence,
            "status": "BLOCKED",
            "reason_code": "pre-write-clean-evidence-required",
            "reason": "Completed formatter evidence requires a passing pre-write clean-target check.",
        }
    if args.execution_mode != "cli":
        return {
            **evidence,
            "status": "BLOCKED",
            "reason_code": "cli-required",
            "reason": "Formatter write and check evidence must come from the CLI.",
        }
    if args.install_permission == "authorized" and args.install_status == "fail":
        return {
            **evidence,
            "status": "BLOCKED",
            "reason_code": "installation-failed",
            "reason": "The authorized formatter installation failed.",
        }
    if not args.formatter_available:
        if args.install_permission in ("not-requested", "missing"):
            return {
                **evidence,
                "status": "BLOCKED",
                "reason_code": "installation-authorization-required",
                "reason": "Native installation authorization is required.",
            }
        if args.install_permission == "denied":
            return {
                **evidence,
                "status": "BLOCKED",
                "reason_code": "installation-denied",
                "reason": "Formatter installation authorization was denied.",
            }
        if args.install_status != "pass":
            return {
                **evidence,
                "status": "BLOCKED",
                "reason_code": "installation-pending",
                "reason": "The authorized formatter installation has not passed.",
            }
        return {
            **evidence,
            "status": "BLOCKED",
            "reason_code": "formatter-unavailable",
            "reason": "The selected formatter CLI is unavailable.",
        }
    if args.write_status == "fail":
        return {
            **evidence,
            "status": "BLOCKED",
            "reason_code": "format-write-failed",
            "reason": "The formatter CLI write failed.",
        }
    if args.write_status == "pass" and args.check_status != "pass":
        return {
            **evidence,
            "status": "BLOCKED",
            "reason_code": "formatter-check-failed",
            "reason": "The formatter follow-up non-mutating CLI check did not pass.",
        }
    if args.write_status == "not-run" and args.check_status != "not-run":
        return {
            **evidence,
            "status": "BLOCKED",
            "reason_code": "invalid-execution-order",
            "reason": "A formatter check result cannot complete a write that did not run.",
        }
    if args.write_status == "pass":
        return {
            **evidence,
            "status": "PASS",
            "reason_code": "format-completed",
            "format_write_allowed": True,
            "format_completed": True,
            "reason": "CLI formatter write and follow-up check passed.",
        }
    return {
        **evidence,
        "status": "PASS",
        "reason_code": "format-write-authorized",
        "format_write_allowed": True,
        "reason": "The complete program-source formatting write is authorized.",
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
        return {
            "status": "BLOCKED",
            "reason_code": "invalid-project-root",
            "reason": str(error),
        }
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
        "scaffold_paths": [
            candidate.relative_to(project_root).as_posix() for candidate in candidates
        ],
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
    if (
        not isinstance(parsed, list)
        or not parsed
        or not all(isinstance(item, str) and item for item in parsed)
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
    full_format = subparsers.add_parser("full-format")
    full_format.add_argument("--project-root", required=True)
    full_format.add_argument("--implementation", choices=PROJECT_STATES, required=True)
    full_format.add_argument("--context", choices=PROJECT_STATES, required=True)
    full_format.add_argument("--language", required=True)
    full_format.add_argument("--canonical-spec", required=True)
    full_format.add_argument(
        "--spec-verification-status",
        choices=("not-run", "pass", "blocked"),
        default="not-run",
    )
    full_format.add_argument(
        "--confirmation",
        choices=("pending", "yes", "no", "ambiguous"),
        default="pending",
    )
    full_format.add_argument("--repository-formatter")
    full_format.add_argument("--repository-check-argv", type=parse_argv)
    full_format.add_argument("--repository-write-argv", type=parse_argv)
    full_format.add_argument(
        "--formatter-available", choices=(True, False), type=parse_bool, required=True
    )
    full_format.add_argument("--execution-mode", choices=("cli", "ide"), default="cli")
    full_format.add_argument(
        "--install-permission",
        choices=("not-requested", "missing", "denied", "authorized"),
        default="not-requested",
    )
    full_format.add_argument(
        "--install-status",
        choices=("not-needed", "not-run", "pass", "fail"),
        default="not-needed",
    )
    full_format.add_argument(
        "--write-status", choices=("not-run", "pass", "fail"), default="not-run"
    )
    full_format.add_argument(
        "--pre-write-clean-status",
        choices=("not-run", "pass", "fail"),
        default="not-run",
    )
    full_format.add_argument(
        "--check-status", choices=("not-run", "pass", "fail"), default="not-run"
    )
    full_format.set_defaults(handler=full_format_workflow)
    gate = subparsers.add_parser("gate")
    gate.add_argument(
        "--operation", choices=("minimal-scaffold", "product-code"), required=True
    )
    gate.add_argument(
        "--formatter-available", choices=(True, False), type=parse_bool, required=True
    )
    gate.add_argument(
        "--check-status", choices=("not-run", "pass", "fail"), required=True
    )
    gate.add_argument(
        "--project-kind", choices=("greenfield", "existing"), required=True
    )
    gate.add_argument("--selection-status", choices=("pass", "blocked"), required=True)
    gate.add_argument(
        "--preflight-status",
        choices=("pass", "blocked", "not-applicable"),
        required=True,
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
