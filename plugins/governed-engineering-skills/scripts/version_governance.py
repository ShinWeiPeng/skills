#!/usr/bin/env python3
"""Validate and release the governed plugin with stable-only SemVer."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:\+codex\.([0-9A-Za-z-]+))?$"
)
LEGACY_MIGRATION_VERSION = "0.5.0-beta.6"
LEGACY_MIGRATION_PREVIOUS_VERSION = "0.5.0-beta.5"
LEGACY_MIGRATION_TARGET = "0.5.0"
INTENT_FIELDS = frozenset({"bump", "changesets", "summary"})
STATE_FIELDS = frozenset(
    {
        "schema_version",
        "current_version",
        "previous_version",
        "bump",
        "production_fingerprint",
        "applied_changesets",
    }
)
CHANGELOG_SECTIONS = ("Breaking Changes", "Added", "Changed", "Fixed")
BUMP_RANK = {"patch": 0, "minor": 1, "major": 2}
FINGERPRINT_EXCLUDED_PARTS = (
    ".changeset",
    "__pycache__",
    "tests",
)
FINGERPRINT_EXCLUDED_FILES = (
    "CHANGELOG.md",
    "package.json",
    ".codex-plugin/plugin.json",
    "architecture/adoption.yaml",
    "architecture/baseline.yaml",
)


def parse_semver(
    text: str, *, allow_cachebuster: bool = False
) -> tuple[int, int, int, str | None]:
    """Parse stable SemVer plus the one supported local-only cachebuster."""
    match = SEMVER_RE.fullmatch(text)
    if not match:
        raise ValueError(f"invalid stable governed plugin version: {text}")
    cachebuster = match.group(4)
    if cachebuster and not allow_cachebuster:
        raise ValueError("formal version must not contain a Codex cachebuster")
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        cachebuster,
    )


def with_cachebuster(version: str, cachebuster: str) -> str:
    """Return one local-only Codex build suffix without changing the version."""
    formal = version.split("+", 1)[0]
    parse_semver(formal)
    if not re.fullmatch(r"[0-9a-z]+(?:-[0-9a-z]+)*", cachebuster):
        raise ValueError(
            "cachebuster must contain lowercase letters, digits, or single hyphens"
        )
    return f"{formal}+codex.{cachebuster}"


def _bumped_version(current: tuple[int, int, int, str | None], bump: str) -> str:
    major, minor, patch = current[:3]
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown bump: {bump}")


def next_version(current: str, *, bump: str) -> str:
    """Return the next stable version, including the one authorized migration."""
    if bump not in BUMP_RANK:
        raise ValueError(f"unknown bump: {bump}")
    if current == LEGACY_MIGRATION_VERSION:
        return LEGACY_MIGRATION_TARGET
    return _bumped_version(parse_semver(current), bump)


def _fingerprint_path(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    relative_text = relative.as_posix()
    if any(part in FINGERPRINT_EXCLUDED_PARTS for part in relative.parts):
        return False
    if relative_text.startswith("architecture/generated/"):
        return False
    if relative_text.startswith("release/"):
        return False
    if relative_text in FINGERPRINT_EXCLUDED_FILES:
        return False
    if path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg"}:
        return False
    return True


def production_fingerprint(root: Path = PLUGIN_ROOT) -> str:
    """Hash release-affecting plugin sources while excluding release metadata."""
    digest = hashlib.sha256()
    for path in sorted(
        (
            item
            for item in root.rglob("*")
            if item.is_file() and _fingerprint_path(item, root)
        ),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return f"sha256:{digest.hexdigest()}"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _formal_manifest_version(manifest_version: str) -> str:
    return manifest_version.split("+codex.", 1)[0]


def _changeset_bump(path: Path, package_name: str) -> str | None:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None
    _, marker, remainder = text.partition("\n---\n")
    if not marker:
        return None
    match = re.search(
        rf'^["\']?{re.escape(package_name)}["\']?\s*:\s*(major|minor|patch)\s*$',
        text.split("\n---\n", 1)[0],
        re.MULTILINE,
    )
    if not match or not remainder.strip():
        return None
    return match.group(1)


def _highest_bump(bumps: list[str]) -> str:
    if not bumps or any(bump not in BUMP_RANK for bump in bumps):
        raise ValueError("changesets must declare major, minor, or patch")
    return max(bumps, key=BUMP_RANK.__getitem__)


def _render_changelog_entry(version: str, summary: dict[str, list[str]]) -> str:
    if not isinstance(summary, dict):
        raise ValueError("release summary must be an object")
    lines = [f"## {version}", ""]
    wrote_section = False
    for section in CHANGELOG_SECTIONS:
        entries = summary.get(section, [])
        if not isinstance(entries, list):
            raise ValueError(f"release summary section {section} must be a list")
        clean = [str(entry).strip() for entry in entries if str(entry).strip()]
        if not clean:
            continue
        wrote_section = True
        lines.extend([f"### {section}", ""])
        lines.extend(f"- {entry}" for entry in clean)
        lines.append("")
    if not wrote_section:
        raise ValueError("release summary must contain at least one changelog section")
    return "\n".join(lines)


def _pending_changesets(
    root: Path,
    applied_changesets: list[str],
) -> set[str]:
    all_changesets = {
        path.stem
        for path in (root / ".changeset").glob("*.md")
        if path.name.lower() != "readme.md"
    }
    return all_changesets - set(applied_changesets)


def _validate_intent(
    root: Path,
    intent: dict[str, Any],
    pending_changesets: set[str],
    package_name: str,
) -> list[str]:
    errors: list[str] = []
    unknown = sorted(set(intent) - INTENT_FIELDS)
    if unknown:
        errors.append(
            "release intent contains obsolete or unknown fields: "
            + ", ".join(unknown)
        )
    intended_value = intent.get("changesets", [])
    if not isinstance(intended_value, list):
        errors.append("release intent changesets must be a list")
        intended: set[str] = set()
    else:
        intended = {str(item) for item in intended_value}
        if len(intended) != len(intended_value):
            errors.append("release intent changesets must be unique")
    if intended != pending_changesets:
        errors.append("release intent changesets do not match pending plugin changesets")

    bumps: list[str] = []
    for changeset_id in sorted(pending_changesets):
        try:
            declared = _changeset_bump(
                root / ".changeset" / f"{changeset_id}.md",
                package_name,
            )
        except OSError as exc:
            errors.append(f"changeset {changeset_id} is missing: {exc}")
            continue
        if declared is None:
            errors.append(f"changeset {changeset_id} has an invalid declaration")
        else:
            bumps.append(declared)
    if bumps:
        expected_bump = _highest_bump(bumps)
        if intent.get("bump") != expected_bump:
            errors.append(
                "release intent bump must match the highest pending changeset bump"
            )
    elif intent.get("bump") not in BUMP_RANK:
        errors.append("release intent bump must be major, minor, or patch")

    try:
        _render_changelog_entry("0.0.0", intent.get("summary", {}))
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def validate_repository(root: Path = PLUGIN_ROOT, *, ci: bool = True) -> list[str]:
    """Validate repository version metadata without changing files."""
    errors: list[str] = []
    try:
        package = _read_json(root / "package.json")
        manifest = _read_json(root / ".codex-plugin" / "plugin.json")
        state = _read_json(root / ".changeset" / "release-state.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"release metadata unreadable: {exc}"]

    intent_path = root / ".changeset" / "release-intent.json"
    intent: dict[str, Any] | None = None
    if intent_path.is_file():
        try:
            intent = _read_json(intent_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"release intent unreadable: {exc}")

    package_version = str(package.get("version", ""))
    manifest_version = str(manifest.get("version", ""))
    migration_pending = (
        package_version == LEGACY_MIGRATION_VERSION and intent is not None
    )
    try:
        parse_semver(package_version)
    except ValueError as exc:
        if not migration_pending:
            errors.append(str(exc))

    manifest_has_cachebuster = "+codex." in manifest_version
    try:
        parse_semver(manifest_version, allow_cachebuster=not ci)
    except ValueError:
        if migration_pending and manifest_version == LEGACY_MIGRATION_VERSION:
            pass
        elif ci and manifest_has_cachebuster:
            errors.append("formal CI version must not contain a Codex cachebuster")
        else:
            errors.append(f"invalid stable plugin manifest version: {manifest_version}")

    if package.get("name") != "governed-engineering-skills" or not package.get(
        "private"
    ):
        errors.append(
            "package.json must describe the private governed-engineering-skills package"
        )
    if manifest.get("name") != package.get("name"):
        errors.append("package.json and plugin.json names differ")
    if ci:
        if package_version != manifest_version:
            errors.append("package.json and plugin.json versions differ")
    elif package_version != _formal_manifest_version(manifest_version):
        errors.append("local manifest cachebuster does not preserve package version")

    changelog_path = root / "CHANGELOG.md"
    try:
        changelog = changelog_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"CHANGELOG.md unreadable: {exc}")
    else:
        if f"## {package_version}\n" not in changelog.replace("\r\n", "\n"):
            errors.append("CHANGELOG.md does not contain the current package version")

    if state.get("current_version") != package_version:
        errors.append("release-state current_version differs from package.json")
    bump = str(state.get("bump", ""))
    previous_version = str(state.get("previous_version", ""))
    if migration_pending:
        if previous_version != LEGACY_MIGRATION_PREVIOUS_VERSION:
            errors.append("legacy migration state has an unexpected previous version")
    else:
        if state.get("schema_version") != "2.0":
            errors.append("release-state schema_version must be 2.0")
        unknown_state = sorted(set(state) - STATE_FIELDS)
        if unknown_state:
            errors.append(
                "release-state contains obsolete or unknown fields: "
                + ", ".join(unknown_state)
            )
        try:
            if next_version(previous_version, bump=bump) != package_version:
                errors.append(
                    "release-state does not describe the actual stable version transition"
                )
        except ValueError as exc:
            errors.append(f"release-state transition is invalid: {exc}")

    applied_value = state.get("applied_changesets")
    if not isinstance(applied_value, list) or not applied_value:
        errors.append("release-state must name at least one applied changeset")
        applied_changesets: list[str] = []
    else:
        applied_changesets = [str(item) for item in applied_value]
        for changeset_id in applied_changesets:
            try:
                declared = _changeset_bump(
                    root / ".changeset" / f"{changeset_id}.md",
                    str(package.get("name", "")),
                )
            except OSError as exc:
                errors.append(
                    f"applied changeset {changeset_id} is missing: {exc}"
                )
            else:
                if declared is None:
                    errors.append(
                        f"applied changeset {changeset_id} has an invalid declaration"
                    )

    pending_changesets = _pending_changesets(root, applied_changesets)
    if pending_changesets:
        if intent is None:
            errors.append("pending plugin changesets require release-intent.json")
        else:
            errors.extend(
                _validate_intent(
                    root,
                    intent,
                    pending_changesets,
                    str(package.get("name", "")),
                )
            )
    elif intent is not None:
        errors.append("release intent exists without pending plugin changesets")

    actual_fingerprint = production_fingerprint(root)
    if state.get("production_fingerprint") != actual_fingerprint and not pending_changesets:
        errors.append("release-state production fingerprint is stale")
    return list(dict.fromkeys(errors))


def apply_release(
    root: Path,
    *,
    bump: str,
    summary: dict[str, list[str]],
    changeset_ids: list[str],
) -> str:
    """Validate all release inputs in memory, then write one stable release."""
    package_path = root / "package.json"
    manifest_path = root / ".codex-plugin" / "plugin.json"
    state_path = root / ".changeset" / "release-state.json"
    package = _read_json(package_path)
    manifest = _read_json(manifest_path)
    state = _read_json(state_path)
    current = str(package["version"])
    if current != str(manifest["version"]) or current != str(state["current_version"]):
        raise ValueError("release metadata must agree before release")
    target = next_version(current, bump=bump)
    fingerprint = production_fingerprint(root)
    applied_changesets = [str(item) for item in state.get("applied_changesets", [])]
    pending_changesets = _pending_changesets(root, applied_changesets)
    if fingerprint != state.get("production_fingerprint") and not pending_changesets:
        raise ValueError(
            "release-affecting source change requires a new plugin changeset"
        )
    if set(changeset_ids) != pending_changesets or len(changeset_ids) != len(
        pending_changesets
    ):
        raise ValueError(
            "release changesets must exactly match pending plugin changesets"
        )

    bumps: list[str] = []
    for changeset_id in changeset_ids:
        changeset_path = root / ".changeset" / f"{changeset_id}.md"
        try:
            declared = _changeset_bump(changeset_path, str(package["name"]))
        except OSError as exc:
            raise ValueError(
                f"changeset {changeset_id} is missing: {exc}"
            ) from exc
        if declared is None:
            raise ValueError(f"changeset {changeset_id} has an invalid declaration")
        bumps.append(declared)
    if not bumps:
        raise ValueError("release requires at least one new plugin changeset")
    if _highest_bump(bumps) != bump:
        raise ValueError(
            "release bump must match the highest pending changeset bump"
        )
    changelog_entry = _render_changelog_entry(target, summary)

    archive_root = root / ".changeset" / "applied" / current
    archive_root.mkdir(parents=True, exist_ok=True)
    for changeset_id in applied_changesets:
        source = root / ".changeset" / f"{changeset_id}.md"
        if source.is_file():
            destination = archive_root / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            source.unlink()

    package["version"] = target
    manifest["version"] = target
    new_state = {
        "schema_version": "2.0",
        "current_version": target,
        "previous_version": current,
        "bump": bump,
        "production_fingerprint": fingerprint,
        "applied_changesets": list(changeset_ids),
    }

    changelog_path = root / "CHANGELOG.md"
    existing = changelog_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    heading, separator, body = existing.partition("\n")
    if not separator:
        raise ValueError("CHANGELOG.md must begin with a heading")
    new_changelog = f"{heading}\n\n{changelog_entry}\n{body.lstrip()}"
    _write_json(package_path, package)
    _write_json(manifest_path, manifest)
    _write_json(state_path, new_state)
    changelog_path.write_text(new_changelog, encoding="utf-8", newline="\n")
    return target


def apply_pending_intent(root: Path = PLUGIN_ROOT) -> str | None:
    """Apply one isolated stable plugin release intent for the Version PR."""
    intent_path = root / ".changeset" / "release-intent.json"
    if not intent_path.is_file():
        return None
    errors = validate_repository(root, ci=True)
    if errors:
        raise ValueError("; ".join(errors))
    intent = _read_json(intent_path)
    target = apply_release(
        root,
        bump=str(intent.get("bump", "")),
        summary=intent.get("summary", {}),
        changeset_ids=[str(item) for item in intent.get("changesets", [])],
    )
    intent_path.unlink()
    return target


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _create_tag(root: Path, *, write: bool) -> str:
    version = str(_read_json(root / "package.json")["version"])
    parse_semver(version)
    tag = f"governed-engineering-skills@{version}"
    if not write:
        return tag
    existing = subprocess.run(
        ["git", "tag", "--list", tag],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if existing:
        tagged_commit = subprocess.run(
            ["git", "rev-list", "-n", "1", tag],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        head_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if tagged_commit != head_commit:
            raise ValueError(f"tag {tag} already points at a different commit")
    else:
        subprocess.run(["git", "tag", tag], cwd=root, check=True)
    return tag


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PLUGIN_ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    check_parser = commands.add_parser("check")
    check_parser.add_argument("--local", action="store_true")
    commands.add_parser("fingerprint")
    commands.add_parser("apply-intent")
    next_parser = commands.add_parser("next")
    next_parser.add_argument(
        "--bump",
        choices=("major", "minor", "patch"),
        required=True,
    )
    release_parser = commands.add_parser(
        "promote",
        help="Apply one stable release; command name retained for compatibility.",
    )
    release_parser.add_argument(
        "--bump",
        choices=("major", "minor", "patch"),
        required=True,
    )
    release_parser.add_argument("--summary", required=True)
    release_parser.add_argument("--changeset", action="append", default=[])
    tag_parser = commands.add_parser("tag")
    tag_parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    try:
        if args.command == "check":
            errors = validate_repository(root, ci=not args.local)
            if errors:
                print("\n".join(f"ERROR: {error}" for error in errors))
                return 1
            print("PASS: governed plugin version metadata is consistent")
            return 0
        if args.command == "fingerprint":
            print(production_fingerprint(root))
            return 0
        if args.command == "apply-intent":
            target = apply_pending_intent(root)
            if target is None:
                print("PASS: no pending governed plugin release intent")
            else:
                print(f"PASS: applied governed plugin release intent for {target}")
            return 0
        if args.command == "next":
            current = str(_read_json(root / "package.json")["version"])
            print(next_version(current, bump=args.bump))
            return 0
        if args.command == "promote":
            target = apply_release(
                root,
                bump=args.bump,
                summary=_load_json(args.summary),
                changeset_ids=args.changeset,
            )
            print(f"PASS: released governed plugin {target}")
            return 0
        if args.command == "tag":
            print(_create_tag(root, write=args.write))
            return 0
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
