#!/usr/bin/env python3
"""Validate personal Git Marketplace identity and cross-surface invocation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from assemble_plugin import (  # noqa: E402
    DistributionError,
    MARKETPLACE_BRANCH,
    MARKETPLACE_PATH,
    MARKETPLACE_REPOSITORY,
    MARKETPLACE_SPARSE_PATHS,
    _validate_schema,
)


PLACEHOLDER = "EVIDENCE_MUST_SUPPLY"
SURFACES = ("chatgpt-work-web", "codex")
BUCKETS = ("engineering", "productivity")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _validate_evidence_file(repo_root: Path, record: object, label: str) -> list[str]:
    if not isinstance(record, dict) or set(record) != {"kind", "path", "sha256"}:
        return [f"{label}: invocation evidence must be a repository-file record"]
    if record.get("kind") != "repository-file":
        return [f"{label}: unsupported invocation evidence kind"]
    relative = record.get("path")
    checksum = record.get("sha256")
    if not isinstance(relative, str) or relative == PLACEHOLDER:
        return [f"{label}: invocation evidence path is missing"]
    path = (repo_root / relative).resolve()
    evidence_root = (repo_root / "distribution" / "evidence").resolve()
    if path == evidence_root or evidence_root not in path.parents:
        return [f"{label}: invocation evidence must be under distribution/evidence"]
    if not path.is_file() or path.stat().st_size == 0:
        return [f"{label}: invocation evidence file is absent or empty"]
    actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if checksum != actual:
        return [f"{label}: invocation evidence checksum does not match"]
    return []


def validate(
    repo_root: Path,
    evidence_path: Path,
    artifact: Path,
    publication_path: Path,
    *,
    branch_commit: str | None = None,
) -> list[str]:
    errors: list[str] = []
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"release evidence input is unavailable or invalid: {exc}"]
    if evidence.get("status") != "accepted":
        return ["Personal Marketplace release evidence is still pending"]
    try:
        schema = json.loads(
            (repo_root / "distribution" / "personal-marketplace-release-evidence.schema.json").read_text(
                encoding="utf-8"
            )
        )
        _validate_schema(evidence, schema, "release-evidence")
    except (OSError, json.JSONDecodeError, DistributionError) as exc:
        return [f"release evidence schema validation failed: {exc}"]
    try:
        inventory = json.loads((artifact / "artifact-inventory.json").read_text(encoding="utf-8"))
        publication = json.loads(publication_path.read_text(encoding="utf-8"))
        compatibility = json.loads(
            (repo_root / "distribution" / "skill-compatibility.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        return [f"release evidence input is unavailable or invalid: {exc}"]

    marketplace = evidence.get("marketplace")
    expected_marketplace = {
        "repository_url": publication.get("repository_url"),
        "git_ref": publication.get("git_ref"),
        "source_commit": publication.get("source_commit"),
        "source_tag": publication.get("source_tag"),
        "marketplace_path": publication.get("marketplace_path"),
        "sparse_paths": publication.get("sparse_paths"),
    }
    if not isinstance(marketplace, dict):
        errors.append("Personal Marketplace identity is missing")
    else:
        if marketplace.get("repository_url") != MARKETPLACE_REPOSITORY:
            errors.append("Personal Marketplace repository_url does not match the supported repository")
        if marketplace.get("git_ref") != MARKETPLACE_BRANCH:
            errors.append("Personal Marketplace git_ref must be marketplace-release")
        if marketplace.get("marketplace_path") != MARKETPLACE_PATH:
            errors.append("Personal Marketplace catalog path is incorrect")
        if marketplace.get("sparse_paths") != list(MARKETPLACE_SPARSE_PATHS):
            errors.append("Personal Marketplace sparse paths are incorrect")
        evidence_branch_commit = marketplace.get("branch_commit")
        if not isinstance(evidence_branch_commit, str) or not SHA40.fullmatch(evidence_branch_commit):
            errors.append("Personal Marketplace branch_commit must be a concrete Git commit")
        elif branch_commit is None or evidence_branch_commit != branch_commit:
            errors.append("Personal Marketplace branch_commit does not match the checked-out branch commit")
        for field, value in expected_marketplace.items():
            if marketplace.get(field) != value:
                errors.append(f"Personal Marketplace {field} does not match the publication candidate")

    artifact_evidence = evidence.get("artifact")
    expected_artifact = {
        "name": inventory.get("plugin_name"),
        "version": inventory.get("version"),
        "content_fingerprint": inventory.get("content_fingerprint"),
    }
    publication_artifact = publication.get("artifact")
    publication_identity = (
        {
            "name": publication_artifact.get("name"),
            "version": publication_artifact.get("version"),
            "content_fingerprint": publication_artifact.get("content_fingerprint"),
        }
        if isinstance(publication_artifact, dict)
        else None
    )
    if artifact_evidence != expected_artifact or publication_identity != expected_artifact:
        errors.append("Personal Marketplace evidence does not identify the assembled Plugin artifact")

    invocations = evidence.get("invocations")
    representatives = compatibility.get("representative_invocations", {})
    for surface in SURFACES:
        for bucket in BUCKETS:
            record = invocations.get(surface, {}).get(bucket, {}) if isinstance(invocations, dict) else {}
            if record.get("skill") != representatives.get(bucket):
                errors.append(f"{surface}/{bucket}: representative Skill does not match inventory")
            errors.extend(_validate_evidence_file(repo_root, record.get("evidence"), f"{surface}/{bucket}"))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--publication", type=Path)
    parser.add_argument("--branch-commit")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    evidence = (
        args.evidence or repo_root / "distribution" / "personal-marketplace-release-evidence.json"
    ).resolve()
    artifact = (args.artifact or repo_root / "dist" / "governed-engineering-skills").resolve()
    publication = (
        args.publication or repo_root / "dist" / "marketplace-release" / "publication-record.json"
    ).resolve()
    errors = validate(
        repo_root,
        evidence,
        artifact,
        publication,
        branch_commit=args.branch_commit,
    )
    if errors:
        print("\n".join(f"BLOCKED: {error}" for error in errors))
        return 1
    print("PASS: personal Marketplace release evidence matches the current publication candidate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
