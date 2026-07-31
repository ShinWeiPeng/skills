#!/usr/bin/env python3
"""Validate and promote the governed plugin's isolated SemVer lifecycle."""

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
    r"(?:-(alpha|beta|rc)\.([1-9]\d*))?"
    r"(?:\+codex\.([0-9A-Za-z-]+))?$"
)
AI_APPROVER_RE = re.compile(r"\b(ai|codex|gpt|chatgpt|assistant|model)\b", re.IGNORECASE)
CHANGELOG_SECTIONS = ("Breaking Changes", "Added", "Changed", "Fixed")
RC_EVIDENCE_KINDS = (
    "unit",
    "integration",
    "bootstrap",
    "renderer",
    "skill-release-gate",
    "plugin-release-gate",
)
STABLE_EVIDENCE_KINDS = ("reinstall", "new-task")
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
) -> tuple[int, int, int, str | None, int | None, str | None]:
    """Parse the supported SemVer subset and reject ambiguous spellings."""
    match = SEMVER_RE.fullmatch(text)
    if not match:
        raise ValueError(f"invalid governed plugin version: {text}")
    cachebuster = match.group(6)
    if cachebuster and not allow_cachebuster:
        raise ValueError("formal version must not contain a Codex cachebuster")
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        match.group(4),
        int(match.group(5)) if match.group(5) else None,
        cachebuster,
    )


def _base_version(parts: tuple[int, int, int, str | None, int | None, str | None]) -> str:
    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def with_cachebuster(version: str, cachebuster: str) -> str:
    """Return one local-only Codex build suffix without changing the base version."""
    formal = version.split("+", 1)[0]
    parse_semver(formal)
    if not re.fullmatch(r"[0-9a-z]+(?:-[0-9a-z]+)*", cachebuster):
        raise ValueError("cachebuster must contain lowercase letters, digits, or single hyphens")
    return f"{formal}+codex.{cachebuster}"


def _bumped_base(
    current: tuple[int, int, int, str | None, int | None, str | None],
    bump: str,
) -> tuple[int, int, int]:
    major, minor, patch = current[:3]
    if bump == "major":
        return major + 1, 0, 0
    if bump == "minor":
        return major, minor + 1, 0
    if bump == "patch":
        return major, minor, patch + 1
    raise ValueError(f"unknown bump: {bump}")


def next_version(current: str, *, bump: str, target_stage: str, risk: str) -> str:
    """Return the next legal version or raise before any file mutation."""
    parts = parse_semver(current)
    major, minor, patch, stage, stage_number, _ = parts
    if target_stage not in {"alpha", "beta", "rc", "stable"}:
        raise ValueError(f"unknown target stage: {target_stage}")
    if risk not in {"low", "high"}:
        raise ValueError(f"unknown risk: {risk}")

    if stage is None:
        next_major, next_minor, next_patch = _bumped_base(parts, bump)
        base = f"{next_major}.{next_minor}.{next_patch}"
        if bump in {"major", "minor"}:
            if target_stage not in {"alpha", "beta"}:
                raise ValueError("major/minor releases must enter alpha or beta")
            return f"{base}-{target_stage}.1"
        if risk == "high":
            if target_stage != "rc":
                raise ValueError("high-risk patch must enter RC")
            return f"{base}-rc.1"
        if target_stage != "stable":
            raise ValueError("low-risk patch releases directly to stable")
        return base

    base = f"{major}.{minor}.{patch}"
    assert stage_number is not None
    if stage == "alpha":
        if target_stage == "alpha":
            return f"{base}-alpha.{stage_number + 1}"
        if target_stage == "beta":
            return f"{base}-beta.1"
        raise ValueError("alpha must progress through beta")
    if stage == "beta":
        if target_stage == "beta":
            return f"{base}-beta.{stage_number + 1}"
        if target_stage == "rc":
            return f"{base}-rc.1"
        raise ValueError("beta must progress through RC")
    if target_stage == "rc":
        return f"{base}-rc.{stage_number + 1}"
    if target_stage == "stable":
        return base
    if target_stage in {"alpha", "beta"}:
        next_major, next_minor, next_patch = _bumped_base(parts, bump)
        next_base = f"{next_major}.{next_minor}.{next_patch}"
        return f"{next_base}-{target_stage}.1"
    raise ValueError("illegal release transition")


def _is_non_ai_approval(approval: dict[str, Any] | None) -> bool:
    if not approval:
        return False
    approver = str(approval.get("approved_by", "")).strip()
    reference = str(approval.get("approval_reference", "")).strip()
    approved_at = str(approval.get("approved_at", "")).strip()
    return bool(
        approver
        and reference
        and approved_at
        and not AI_APPROVER_RE.search(approver)
    )


def validate_promotion_evidence(
    current: str,
    target: str,
    *,
    risk: str,
    current_fingerprint: str,
    final_rc_fingerprint: str | None,
    approval: dict[str, Any] | None,
    validation_evidence: list[dict[str, Any]],
    compatibility_adr: dict[str, Any] | None = None,
) -> list[str]:
    """Validate evidence that cannot be inferred from the version string."""
    del risk
    errors: list[str] = []
    current_parts = parse_semver(current)
    target_parts = parse_semver(target)
    current_stage = current_parts[3]
    target_stage = target_parts[3]
    evidence_kinds = {
        str(item.get("kind", "")).strip()
        for item in validation_evidence
        if str(item.get("reference", "")).strip()
    }

    if target_stage == "rc" and current_stage in {"alpha", "beta"}:
        missing = sorted(set(RC_EVIDENCE_KINDS) - evidence_kinds)
        if missing:
            errors.append(f"RC promotion missing validation evidence: {', '.join(missing)}")

    if target_stage is None and current_stage == "rc":
        if current_fingerprint != final_rc_fingerprint:
            errors.append("stable promotion fingerprint differs from final RC")
        if not _is_non_ai_approval(approval):
            errors.append("stable promotion requires non-AI approval")
        if not set(STABLE_EVIDENCE_KINDS).issubset(evidence_kinds):
            errors.append("stable promotion requires reinstall and new-task evidence")

    if target_parts[:3] == (1, 0, 0) and target_stage is None:
        if not compatibility_adr or compatibility_adr.get("status") != "accepted":
            errors.append("1.0.0 requires an accepted compatibility ADR")
        elif not _is_non_ai_approval(compatibility_adr.get("approval")):
            errors.append("1.0.0 compatibility ADR requires non-AI approval")
    return errors


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
        (item for item in root.rglob("*") if item.is_file() and _fingerprint_path(item, root)),
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


def validate_repository(root: Path = PLUGIN_ROOT, *, ci: bool = True) -> list[str]:
    """Validate repository version metadata without changing files."""
    errors: list[str] = []
    try:
        package = _read_json(root / "package.json")
        manifest = _read_json(root / ".codex-plugin" / "plugin.json")
        state = _read_json(root / ".changeset" / "release-state.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"release metadata unreadable: {exc}"]

    package_version = str(package.get("version", ""))
    manifest_version = str(manifest.get("version", ""))
    try:
        parse_semver(package_version)
    except ValueError as exc:
        errors.append(str(exc))
    try:
        manifest_parts = parse_semver(manifest_version, allow_cachebuster=not ci)
    except ValueError:
        if ci and "+codex." in manifest_version:
            errors.append("formal CI version must not contain a Codex cachebuster")
        else:
            errors.append(f"invalid plugin manifest version: {manifest_version}")
        manifest_parts = None

    if package.get("name") != "governed-engineering-skills" or not package.get("private"):
        errors.append("package.json must describe the private governed-engineering-skills package")
    if manifest.get("name") != package.get("name"):
        errors.append("package.json and plugin.json names differ")
    if ci:
        if package_version != manifest_version:
            errors.append("package.json and plugin.json versions differ")
    elif package_version != _formal_manifest_version(manifest_version):
        errors.append("local manifest cachebuster does not preserve package base version")

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
    try:
        package_parts = parse_semver(package_version)
        expected_group = _base_version(package_parts)
        if state.get("release_group") != expected_group:
            errors.append("release-state release_group differs from current base version")
    except ValueError:
        pass
    actual_fingerprint = production_fingerprint(root)
    previous_version = str(state.get("previous_version", ""))
    bump = str(state.get("bump", ""))
    risk = str(state.get("risk", ""))
    try:
        current_stage = parse_semver(package_version)[3] or "stable"
        if next_version(
            previous_version,
            bump=bump,
            target_stage=current_stage,
            risk=risk,
        ) != package_version:
            errors.append("release-state does not describe the actual version transition")
    except ValueError as exc:
        errors.append(f"release-state transition is invalid: {exc}")

    applied_changesets = state.get("applied_changesets")
    if not isinstance(applied_changesets, list) or not applied_changesets:
        errors.append("release-state must name at least one applied changeset")
    else:
        for changeset_id in applied_changesets:
            changeset_path = root / ".changeset" / f"{changeset_id}.md"
            try:
                declared_bump = _changeset_bump(changeset_path, str(package.get("name", "")))
            except OSError as exc:
                errors.append(f"applied changeset {changeset_id} is missing: {exc}")
                continue
            if declared_bump != bump:
                errors.append(
                    f"applied changeset {changeset_id} does not declare the release-state bump"
                )

    all_changesets = {
        path.stem
        for path in (root / ".changeset").glob("*.md")
        if path.name.lower() != "readme.md"
    }
    applied_set = {
        str(item) for item in applied_changesets
    } if isinstance(applied_changesets, list) else set()
    pending_changesets = all_changesets - applied_set
    intent_path = root / ".changeset" / "release-intent.json"
    intent: dict[str, Any] | None = None
    if intent_path.is_file():
        try:
            intent = _read_json(intent_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"release intent unreadable: {exc}")
    if pending_changesets:
        if intent is None:
            errors.append("pending plugin changesets require release-intent.json")
        else:
            intended = {str(item) for item in intent.get("changesets", [])}
            if intended != pending_changesets:
                errors.append("release intent changesets do not match pending plugin changesets")
    elif intent is not None:
        errors.append("release intent exists without pending plugin changesets")

    if state.get("production_fingerprint") != actual_fingerprint and not pending_changesets:
        errors.append("release-state production fingerprint is stale")

    if package_parts[3] == "rc":
        evidence_kinds = {
            str(item.get("kind", "")).strip()
            for item in state.get("validation_evidence", [])
            if isinstance(item, dict) and str(item.get("reference", "")).strip()
        }
        missing = sorted(set(RC_EVIDENCE_KINDS) - evidence_kinds)
        if missing:
            errors.append(f"current RC is missing validation evidence: {', '.join(missing)}")
    if package_parts[3] is None:
        stable_errors = validate_promotion_evidence(
            previous_version,
            package_version,
            risk=risk,
            current_fingerprint=actual_fingerprint,
            final_rc_fingerprint=state.get("final_rc_fingerprint"),
            approval=state.get("approval"),
            validation_evidence=state.get("validation_evidence", []),
            compatibility_adr=state.get("compatibility_adr"),
        )
        errors.extend(stable_errors)
        if state.get("open_blockers"):
            errors.append("stable release must not contain open blockers")
    if manifest_parts and manifest_parts[5] and ci:
        errors.append("formal CI version must not contain a Codex cachebuster")
    return list(dict.fromkeys(errors))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _render_changelog_entry(version: str, summary: dict[str, list[str]]) -> str:
    lines = [f"## {version}", ""]
    wrote_section = False
    for section in CHANGELOG_SECTIONS:
        entries = summary.get(section, [])
        if not entries:
            continue
        wrote_section = True
        lines.extend([f"### {section}", ""])
        lines.extend(f"- {entry.strip()}" for entry in entries if entry.strip())
        lines.append("")
    if not wrote_section:
        raise ValueError("release summary must contain at least one changelog section")
    return "\n".join(lines)


def apply_promotion(
    root: Path,
    *,
    bump: str,
    target_stage: str,
    risk: str,
    summary: dict[str, list[str]],
    changeset_ids: list[str],
    approval: dict[str, Any] | None,
    validation_evidence: list[dict[str, Any]],
    compatibility_adr: dict[str, Any] | None = None,
) -> str:
    """Atomically validate inputs in memory, then write one promotion."""
    package_path = root / "package.json"
    manifest_path = root / ".codex-plugin" / "plugin.json"
    state_path = root / ".changeset" / "release-state.json"
    package = _read_json(package_path)
    manifest = _read_json(manifest_path)
    state = _read_json(state_path)
    current = str(package["version"])
    if current != str(manifest["version"]) or current != str(state["current_version"]):
        raise ValueError("release metadata must agree before promotion")
    target = next_version(current, bump=bump, target_stage=target_stage, risk=risk)
    fingerprint = production_fingerprint(root)
    applied_changesets = [str(item) for item in state.get("applied_changesets", [])]
    new_changesets = [item for item in changeset_ids if item not in applied_changesets]
    if fingerprint != state.get("production_fingerprint") and not new_changesets:
        raise ValueError("release-affecting source change requires a new plugin changeset")
    for changeset_id in new_changesets:
        changeset_path = root / ".changeset" / f"{changeset_id}.md"
        try:
            declared_bump = _changeset_bump(changeset_path, str(package["name"]))
        except OSError as exc:
            raise ValueError(f"changeset {changeset_id} is missing: {exc}") from exc
        if declared_bump != bump:
            raise ValueError(f"changeset {changeset_id} must declare bump {bump}")
    target_group = _base_version(parse_semver(target))
    current_group = str(state.get("release_group", ""))
    if target_group != current_group and not new_changesets:
        raise ValueError("a new release group requires a new plugin changeset")
    errors = validate_promotion_evidence(
        current,
        target,
        risk=risk,
        current_fingerprint=fingerprint,
        final_rc_fingerprint=state.get("final_rc_fingerprint"),
        approval=approval,
        validation_evidence=validation_evidence,
        compatibility_adr=compatibility_adr,
    )
    if parse_semver(target)[3] is None and state.get("open_blockers"):
        errors.append("stable promotion requires zero open blockers")
    if errors:
        raise ValueError("; ".join(errors))
    changelog_entry = _render_changelog_entry(target, summary)

    package["version"] = target
    manifest["version"] = target
    state["previous_version"] = current
    state["current_version"] = target
    state["release_group"] = target_group
    state["bump"] = bump
    state["risk"] = risk
    state["production_fingerprint"] = fingerprint
    if target_group != current_group:
        archive_root = root / ".changeset" / "applied" / current_group
        archive_root.mkdir(parents=True, exist_ok=True)
        for changeset_id in applied_changesets:
            source = root / ".changeset" / f"{changeset_id}.md"
            if source.is_file():
                destination = archive_root / source.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                source.unlink()
        state["applied_changesets"] = new_changesets
    else:
        state["applied_changesets"] = applied_changesets + new_changesets
    if parse_semver(target)[3] == "rc":
        state["final_rc_fingerprint"] = fingerprint
    elif parse_semver(target)[3] in {"alpha", "beta"}:
        state["final_rc_fingerprint"] = None
    state["approval"] = approval
    state["validation_evidence"] = validation_evidence

    changelog_path = root / "CHANGELOG.md"
    existing = changelog_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    heading, separator, body = existing.partition("\n")
    if not separator:
        raise ValueError("CHANGELOG.md must begin with a heading")
    new_changelog = f"{heading}\n\n{changelog_entry}\n{body.lstrip()}"
    _write_json(package_path, package)
    _write_json(manifest_path, manifest)
    _write_json(state_path, state)
    changelog_path.write_text(new_changelog, encoding="utf-8", newline="\n")
    return target


def apply_pending_intent(root: Path = PLUGIN_ROOT) -> str | None:
    """Apply one isolated plugin release intent for the shared Version PR."""
    intent_path = root / ".changeset" / "release-intent.json"
    if not intent_path.is_file():
        return None
    intent = _read_json(intent_path)
    target = apply_promotion(
        root,
        bump=str(intent.get("bump", "")),
        target_stage=str(intent.get("target_stage", "")),
        risk=str(intent.get("risk", "")),
        summary=intent.get("summary", {}),
        changeset_ids=[str(item) for item in intent.get("changesets", [])],
        approval=intent.get("approval"),
        validation_evidence=intent.get("validation_evidence", []),
        compatibility_adr=intent.get("compatibility_adr"),
    )
    intent_path.unlink()
    return target


def _load_optional_json(path: str | None, default: Any) -> Any:
    if not path:
        return default
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
    next_parser.add_argument("--bump", choices=("major", "minor", "patch"), required=True)
    next_parser.add_argument("--stage", choices=("alpha", "beta", "rc", "stable"), required=True)
    next_parser.add_argument("--risk", choices=("low", "high"), required=True)
    promote_parser = commands.add_parser("promote")
    promote_parser.add_argument("--bump", choices=("major", "minor", "patch"), required=True)
    promote_parser.add_argument("--stage", choices=("alpha", "beta", "rc", "stable"), required=True)
    promote_parser.add_argument("--risk", choices=("low", "high"), required=True)
    promote_parser.add_argument("--summary", required=True)
    promote_parser.add_argument("--changeset", action="append", default=[])
    promote_parser.add_argument("--approval")
    promote_parser.add_argument("--evidence")
    promote_parser.add_argument("--compatibility-adr")
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
            print(
                next_version(
                    current,
                    bump=args.bump,
                    target_stage=args.stage,
                    risk=args.risk,
                )
            )
            return 0
        if args.command == "promote":
            target = apply_promotion(
                root,
                bump=args.bump,
                target_stage=args.stage,
                risk=args.risk,
                summary=_load_optional_json(args.summary, {}),
                changeset_ids=args.changeset,
                approval=_load_optional_json(args.approval, None),
                validation_evidence=_load_optional_json(args.evidence, []),
                compatibility_adr=_load_optional_json(args.compatibility_adr, None),
            )
            print(f"PASS: promoted governed plugin to {target}")
            return 0
        if args.command == "tag":
            print(_create_tag(root, write=args.write))
            return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
