#!/usr/bin/env python3
"""Check or refresh pinned vendored skill snapshots without overwriting overlays."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = PLUGIN_ROOT / "vendor-lock.json"
SKILLS_ROOT = PLUGIN_ROOT / "skills"
MATT_SKILLS = {
    "ask-matt": "skills/engineering/ask-matt",
    "diagnosing-bugs": "skills/engineering/diagnosing-bugs",
    "grill-with-docs": "skills/engineering/grill-with-docs",
    "triage": "skills/engineering/triage",
    "improve-codebase-architecture": "skills/engineering/improve-codebase-architecture",
    "setup-matt-pocock-skills": "skills/engineering/setup-matt-pocock-skills",
    "tdd": "skills/engineering/tdd",
    "to-spec": "skills/engineering/to-spec",
    "to-tickets": "skills/engineering/to-tickets",
    "wayfinder": "skills/engineering/wayfinder",
    "implement": "skills/engineering/implement",
    "prototype": "skills/engineering/prototype",
    "research": "skills/engineering/research",
    "domain-modeling": "skills/engineering/domain-modeling",
    "codebase-design": "skills/engineering/codebase-design",
    "code-review": "skills/engineering/code-review",
    "resolving-merge-conflicts": "skills/engineering/resolving-merge-conflicts",
    "grill-me": "skills/productivity/grill-me",
    "grilling": "skills/productivity/grilling",
    "handoff": "skills/productivity/handoff",
    "teach": "skills/productivity/teach",
    "writing-great-skills": "skills/productivity/writing-great-skills",
}
GOVERNANCE_SKILLS = {
    "clarify-improvement-proposals",
    "explain-code-flow",
    "govern-modular-event-architecture",
    "validate-on-device",
}
OVERLAYS = {
    "ask-matt",
    "grill-me",
    "diagnosing-bugs",
    "grill-with-docs",
    "triage",
    "improve-codebase-architecture",
    "setup-matt-pocock-skills",
    "tdd",
    "to-spec",
    "to-tickets",
    "wayfinder",
    "implement",
    "prototype",
    "domain-modeling",
    "codebase-design",
    "code-review",
    "resolving-merge-conflicts",
    "handoff",
    "teach",
    "writing-great-skills",
    "govern-modular-event-architecture",
    "validate-on-device",
}


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if (
            "__pycache__" in path.parts
            or path.suffix == ".pyc"
            or path.name == "validation-evidence.md"
        ):
            continue
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_lock() -> dict:
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def initialize(matt_root: Path, governance_root: Path) -> int:
    entries = []
    for name, source_path in MATT_SKILLS.items():
        source = matt_root / source_path
        entries.append(
            {
                "name": name,
                "source_kind": "matt",
                "source_path": source_path,
                "source_sha256": tree_hash(source),
                "integrated_sha256": tree_hash(SKILLS_ROOT / name),
                "overlay": name in OVERLAYS,
            }
        )
    for name in sorted(GOVERNANCE_SKILLS):
        source = governance_root / name
        entries.append(
            {
                "name": name,
                "source_kind": "governance",
                "source_path": name,
                "source_sha256": tree_hash(source),
                "integrated_sha256": tree_hash(SKILLS_ROOT / name),
                "overlay": name in OVERLAYS,
            }
        )
    entries.append(
        {
            "name": "engineering-risk-routing",
            "source_kind": "integration",
            "source_path": "skills/engineering-risk-routing",
            "source_sha256": tree_hash(SKILLS_ROOT / "engineering-risk-routing"),
            "integrated_sha256": tree_hash(SKILLS_ROOT / "engineering-risk-routing"),
            "overlay": True,
        }
    )
    lock = {
        "schema_version": "1.0.0",
        "matt_commit": "2ab9580",
        "skills": entries,
    }
    LOCK_PATH.write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"PASS: initialized {len(entries)} pinned skill snapshots")
    return 0


def check() -> int:
    lock = load_lock()
    errors = []
    for entry in lock["skills"]:
        destination = SKILLS_ROOT / entry["name"]
        if not destination.is_dir():
            errors.append(f"missing vendored skill: {entry['name']}")
            continue
        actual = tree_hash(destination)
        if actual != entry["integrated_sha256"]:
            errors.append(f"integrated drift: {entry['name']}")
    if errors:
        print("\n".join(f"BLOCKED: {error}" for error in errors))
        return 2
    print(f"PASS: {len(lock['skills'])} pinned skill snapshots match vendor-lock.json")
    return 0


def refresh(matt_root: Path, governance_root: Path) -> int:
    lock = load_lock()
    blocked = []
    refreshed = []
    for entry in lock["skills"]:
        if entry["source_kind"] == "matt":
            source = matt_root / entry["source_path"]
        elif entry["source_kind"] == "governance":
            source = governance_root / entry["name"]
        else:
            continue
        source_hash = tree_hash(source)
        if entry["overlay"] and source_hash != entry["source_sha256"]:
            blocked.append(entry["name"])
            continue
        if not entry["overlay"] and source_hash != entry["source_sha256"]:
            destination = SKILLS_ROOT / entry["name"]
            shutil.rmtree(destination)
            shutil.copytree(
                source,
                destination,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "validation-evidence.md"),
            )
            entry["source_sha256"] = source_hash
            entry["integrated_sha256"] = tree_hash(destination)
            refreshed.append(entry["name"])
    if blocked:
        print("BLOCKED: upstream drift requires overlay review: " + ", ".join(blocked))
        return 2
    LOCK_PATH.write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("PASS: refreshed " + (", ".join(refreshed) if refreshed else "no snapshots"))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--refresh", action="store_true")
    group.add_argument("--initialize", action="store_true")
    parser.add_argument("--matt-root", type=Path)
    parser.add_argument("--governance-root", type=Path)
    args = parser.parse_args()
    if args.check:
        return check()
    if args.matt_root is None or args.governance_root is None:
        parser.error("--refresh/--initialize require --matt-root and --governance-root")
    if args.initialize:
        return initialize(args.matt_root, args.governance_root)
    return refresh(args.matt_root, args.governance_root)


if __name__ == "__main__":
    raise SystemExit(main())
