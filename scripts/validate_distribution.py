#!/usr/bin/env python3
"""Validate single-source Plugin assembly and Codex distribution metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from assemble_plugin import (  # noqa: E402
    DEVELOPMENT_MARKETPLACE_NAME,
    PLUGIN_NAME,
    assemble,
    promoted_skills,
    validate_artifact,
    validate_marketplace_publication,
    write_marketplace_publication,
)


MANDATORY_CAPABILITY_EVIDENCE = {
    "code-review": ("git diff", "sub-agent"),
    "diagnosing-bugs": ("regression",),
    "domain-modeling": ("CONTEXT.md", "ADRs"),
    "grill-with-docs": ("CONTEXT.md", "ADR"),
    "grill-me": ("spec-governance",),
    "grilling": ("spec-governance",),
    "handoff": ("temporary directory",),
    "implement": ("Implement the work",),
    "improve-codebase-architecture": ("codebase", "HTML"),
    "prototype": ("prototype",),
    "research": ("Markdown file in the repo",),
    "resolving-merge-conflicts": ("git merge", "rebase"),
    "setup-matt-pocock-skills": ("Scaffold", "repo"),
    "tdd": ("test", "code"),
    "teach": ("current directory",),
    "to-spec": ("issue tracker",),
    "to-tickets": ("issue tracker",),
    "triage": ("issue tracker",),
    "wayfinder": ("issue tracker",),
}
REQUIRED_INSTALLER_PATHS = (
    "Install Governed Engineering Skills.cmd",
    "Install Governed Engineering Skills.sh",
    "scripts/install-marketplace.ps1",
    "scripts/install-marketplace.sh",
    "distribution/installer-providers.json",
    "scripts/install-local.ps1",
    "plugins/governed-engineering-skills/scripts/install-local.ps1",
    "plugins/governed-engineering-skills/tests/test_install_local.ps1",
)


def compatibility_dependency_errors(
    entries: dict, skills: dict[str, Path]
) -> list[str]:
    errors: list[str] = []
    for name, entry in entries.items():
        dependencies = entry.get("host_dependencies")
        if not isinstance(dependencies, list):
            errors.append(f"{name}: host_dependencies must be a list")
    for name, markers in MANDATORY_CAPABILITY_EVIDENCE.items():
        skill_text = (skills[name] / "SKILL.md").read_text(
            encoding="utf-8", errors="ignore"
        )
        missing = [
            marker
            for marker in markers
            if marker.casefold() not in skill_text.casefold()
        ]
        if missing:
            errors.append(
                f"{name}: mandatory capability evidence changed; missing markers {missing}"
            )
    return errors


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(repo_root: Path) -> list[str]:
    errors: list[str] = []
    plugin_shell = repo_root / "plugins" / PLUGIN_NAME
    if (plugin_shell / "skills").exists():
        errors.append("plugin shell contains a duplicate skills tree")
    for relative in REQUIRED_INSTALLER_PATHS:
        if not (repo_root / relative).is_file():
            errors.append(f"required installer surface is missing: {relative}")

    manifest_path = repo_root / "architecture" / "manifest.yaml"
    if not manifest_path.is_file():
        errors.append("repository-root architecture/manifest.yaml is missing")
    else:
        architecture_text = manifest_path.read_text(encoding="utf-8")
        if "local_install_adapter" not in architecture_text:
            errors.append("formal architecture does not declare local_install_adapter")
    if (plugin_shell / "architecture").exists():
        errors.append("formal architecture still exists inside the plugin shell")

    skills = promoted_skills(repo_root)
    if len(skills) != 29:
        errors.append(f"expected 29 promoted skills, found {len(skills)}")
    for name, root in skills.items():
        if not (root / "agents" / "openai.yaml").is_file():
            errors.append(f"{name}: missing agents/openai.yaml")

    claude_manifest_path = repo_root / ".claude-plugin" / "plugin.json"
    try:
        claude_manifest = _load_json(claude_manifest_path)
        declared = {Path(value).name for value in claude_manifest["skills"]}
        if declared != set(skills) or len(claude_manifest["skills"]) != len(skills):
            errors.append(
                "Claude Plugin manifest does not list exactly the promoted Skills"
            )
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"invalid Claude Plugin manifest: {exc}")

    root_readme = (repo_root / "README.md").read_text(encoding="utf-8", errors="ignore")
    for name, root in skills.items():
        bucket = root.parent.name
        expected_link = f"./skills/{bucket}/{name}/SKILL.md"
        if expected_link not in root_readme:
            errors.append(f"root README is missing promoted Skill link: {name}")
        bucket_readme = (root.parent / "README.md").read_text(
            encoding="utf-8", errors="ignore"
        )
        if f"./{name}/SKILL.md" not in bucket_readme:
            errors.append(f"{bucket} README is missing promoted Skill link: {name}")
        if not (repo_root / "docs" / bucket / f"{name}.md").is_file():
            errors.append(f"promoted Skill is missing docs page: {name}")

    compatibility_path = repo_root / "distribution" / "skill-compatibility.json"
    try:
        compatibility = _load_json(compatibility_path)
        entries = compatibility["skills"]
        if set(entries) != set(skills):
            errors.append(
                "compatibility inventory does not exactly match promoted skills"
            )
        classifications = {
            name: entry.get("classification") for name, entry in entries.items()
        }
        invalid = {
            name: value
            for name, value in classifications.items()
            if value not in {"codex-compatible", "blocked"}
        }
        if invalid:
            errors.append(f"invalid compatibility classifications: {invalid}")
        for name, entry in entries.items():
            if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                errors.append(f"{name}: compatibility reason is required")
        errors.extend(compatibility_dependency_errors(entries, skills))
        blocked = sorted(
            name for name, value in classifications.items() if value == "blocked"
        )
        if blocked:
            errors.append(
                "release-blocked compatibility entries: " + ", ".join(blocked)
            )
        representatives = compatibility["representative_invocations"]
        for bucket in ("engineering", "productivity"):
            name = representatives.get(bucket)
            if classifications.get(name) != "codex-compatible":
                errors.append(f"{bucket} representative must be Codex-compatible")
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"invalid compatibility inventory: {exc}")

    marketplace_path = repo_root / ".agents" / "plugins" / "marketplace.json"
    try:
        marketplace = _load_json(marketplace_path)
        if marketplace.get("name") != DEVELOPMENT_MARKETPLACE_NAME:
            errors.append(
                f"source Marketplace name must be {DEVELOPMENT_MARKETPLACE_NAME}"
            )
        entries = [
            entry
            for entry in marketplace["plugins"]
            if entry.get("name") == PLUGIN_NAME
        ]
        if len(entries) != 1:
            errors.append(
                "manual maintainer Marketplace must contain exactly one governed plugin"
            )
        else:
            source = entries[0].get("source", {})
            if source != {
                "source": "local",
                "path": "./dist/governed-engineering-skills",
            }:
                errors.append(
                    "manual maintainer Marketplace must target the assembled Plugin artifact"
                )
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"invalid manual maintainer Marketplace: {exc}")

    try:
        providers = _load_json(repo_root / "distribution" / "installer-providers.json")
        if providers["marketplace"]["name"] != "governed-engineering":
            errors.append("installer provider Marketplace identity is invalid")
        if providers["codex"]["package"] != "@openai/codex":
            errors.append("installer provider Codex package identity is invalid")
        if set(providers["platforms"]) != {"windows", "debian", "fedora"}:
            errors.append("installer provider platform matrix is invalid")
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"invalid installer provider manifest: {exc}")

    user_docs = [repo_root / "README.md"] + list((repo_root / "docs").rglob("*.md"))
    forbidden = re.compile(
        r"(?i)(administrator-approved private Workspace|Workspace administrator)"
    )
    for path in user_docs:
        if path.is_file() and forbidden.search(
            path.read_text(encoding="utf-8", errors="ignore")
        ):
            errors.append(
                f"user-facing document advertises an unsupported Workspace installation: {path.relative_to(repo_root)}"
            )

    try:
        with tempfile.TemporaryDirectory(
            prefix="distribution-validation-"
        ) as temporary:
            artifact = Path(temporary) / PLUGIN_NAME
            result = assemble(repo_root, artifact)
            validate_artifact(repo_root, artifact)
            publication_root = Path(temporary) / "marketplace-release"
            record = write_marketplace_publication(
                repo_root,
                artifact,
                result,
                publication_root,
                source_commit="0" * 40,
                previous_publication_commit="none:first-publication",
            )
            payload = _load_json(record)
            schema = _load_json(
                repo_root
                / "distribution"
                / "personal-marketplace-publication.schema.json"
            )
            validate_marketplace_publication(publication_root, payload, schema)
            if payload.get("channel") != "personal-git-marketplace":
                errors.append(
                    "Marketplace publication does not identify the personal Git channel"
                )
    except Exception as exc:  # report all bounded assembly failures together
        errors.append(f"assembly validation failed: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    errors = validate(args.repo_root.resolve())
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(
        "PASS: single-source assembly, Codex compatibility inventory, and optional Git Marketplace publication"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
