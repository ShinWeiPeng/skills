#!/usr/bin/env python3
"""Assess implementation and durable project context from repository evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


IMPLEMENTATION_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}


def _is_stateful_context(path: Path) -> bool:
    normalized = path.as_posix().casefold()
    name = path.name.casefold()
    return (
        name in {"context.md", "prd.md", "spec.md"}
        or normalized == "architecture/manifest.yaml"
        or normalized.startswith("architecture/decisions/")
        or normalized.startswith("docs/spec")
        or normalized.startswith("specs/")
    )


class RepositoryEvidencePort(Protocol):
    """Demand-owned read-only repository evidence boundary."""

    def collect(self, project_root: Path) -> list[dict[str, Any]]:
        """Return normalized tracked and untracked repository evidence."""


def assess_project_state(
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return the three-state project assessment for normalized evidence."""

    assessed: list[dict[str, Any]] = []
    implementation = "absent"
    stateful_context = "absent"
    ambiguous_source_placeholder = False
    ambiguous_generic_artifact = False
    for item in evidence:
        row = dict(item)
        row.setdefault("size_bytes", 1)
        if row.get("exclusion_reason"):
            row["classification"] = "excluded"
            row["reason"] = str(row["exclusion_reason"])
            row.pop("exclusion_reason", None)
            assessed.append(row)
            continue
        row.pop("exclusion_reason", None)
        path = Path(str(row["path"]))
        if (
            path.suffix.casefold() in IMPLEMENTATION_SUFFIXES
            and row.get("size_bytes") == 0
        ):
            row["classification"] = "ambiguous"
            row["reason"] = "empty source placeholder does not prove implementation"
            ambiguous_source_placeholder = True
        elif path.suffix.casefold() in IMPLEMENTATION_SUFFIXES:
            row["classification"] = "implementation"
            row["reason"] = "recognized product or test source suffix"
            implementation = "present"
        elif _is_stateful_context(path):
            row["classification"] = "stateful-context"
            row["reason"] = "recognized durable project context"
            stateful_context = "present"
        else:
            row["classification"] = "ambiguous"
            row["reason"] = "weak artifact alone does not prove either project axis"
            ambiguous_generic_artifact = True
        assessed.append(row)

    strong_evidence_present = (
        implementation == "present" or stateful_context == "present"
    )
    if ambiguous_source_placeholder and implementation == "absent":
        implementation = "indeterminate"
    elif (
        ambiguous_generic_artifact
        and not strong_evidence_present
        and implementation == "absent"
    ):
        implementation = "indeterminate"
    if (
        ambiguous_generic_artifact
        and not strong_evidence_present
        and stateful_context == "absent"
    ):
        stateful_context = "indeterminate"

    return {
        "implementation": implementation,
        "stateful_context": stateful_context,
        "evidence": assessed,
    }
