#!/usr/bin/env python3
"""Validate the governed plugin inventory and isolation invariants."""

from __future__ import annotations

import json
import re
from pathlib import Path

from version_governance import validate_repository


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PLUGIN_ROOT / "skills"
EXPECTED_SKILLS = {
    "ask-matt", "diagnosing-bugs", "grill-with-docs", "triage",
    "improve-codebase-architecture", "setup-matt-pocock-skills", "tdd",
    "to-spec", "to-tickets", "wayfinder", "implement", "prototype",
    "research", "domain-modeling", "codebase-design", "code-review",
    "resolving-merge-conflicts", "grill-me", "grilling", "handoff", "teach",
    "writing-great-skills", "clarify-improvement-proposals", "explain-code-flow",
    "govern-modular-event-architecture", "validate-on-device",
    "engineering-risk-routing",
}


def main() -> int:
    errors: list[str] = []
    actual = {path.name for path in SKILLS_ROOT.iterdir() if path.is_dir()}
    if actual != EXPECTED_SKILLS:
        errors.append(
            f"skill inventory mismatch: missing={sorted(EXPECTED_SKILLS - actual)}, "
            f"extra={sorted(actual - EXPECTED_SKILLS)}"
        )
    if "hackmd-note-writer" in actual:
        errors.append("hackmd-note-writer must remain outside this plugin")
    for route_name in ("ask-matt", "handoff"):
        route_text = (SKILLS_ROOT / route_name / "SKILL.md").read_text(
            encoding="utf-8"
        ).casefold()
        if "hackmd" in route_text or "note-writer" in route_text:
            errors.append(f"{route_name}: learning-note routing must remain absent")

    for name in sorted(actual):
        skill_file = SKILLS_ROOT / name / "SKILL.md"
        openai_yaml = SKILLS_ROOT / name / "agents" / "openai.yaml"
        if not skill_file.is_file():
            errors.append(f"{name}: missing SKILL.md")
            continue
        text = skill_file.read_text(encoding="utf-8")
        match = re.search(r"^name:\s*['\"]?([^'\"\r\n]+)", text, re.MULTILINE)
        if not match or match.group(1).strip() != name:
            errors.append(f"{name}: frontmatter name does not match directory")
        if not openai_yaml.is_file():
            errors.append(f"{name}: missing agents/openai.yaml")

    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    if manifest.get("name") != PLUGIN_ROOT.name:
        errors.append("plugin manifest name does not match folder")
    if manifest.get("skills") != "./skills/":
        errors.append("plugin manifest must discover ./skills/")
    errors.extend(validate_repository(PLUGIN_ROOT, ci=True))

    user_absolute_path = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/]+", re.IGNORECASE)
    for path in PLUGIN_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if user_absolute_path.search(text):
            errors.append(f"non-portable user path: {path.relative_to(PLUGIN_ROOT)}")
    if any(path.name == "__pycache__" for path in PLUGIN_ROOT.rglob("__pycache__")):
        errors.append("__pycache__ must not be vendored")

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(
        f"PASS: {len(actual)} skills; version metadata consistent; "
        "HackMD isolated; no user-absolute paths"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
