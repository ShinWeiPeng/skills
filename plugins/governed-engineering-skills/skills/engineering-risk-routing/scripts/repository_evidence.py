#!/usr/bin/env python3
"""Read tracked and non-ignored untracked repository artifacts without mutation."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


EXCLUDED_NAMES = {".gitattributes", ".gitignore", ".gitmodules"}
EXCLUDED_PARTS = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "generated",
    "node_modules",
    "target",
    "venv",
}


def _exclusion_reason(relative: str) -> str | None:
    path = Path(relative)
    folded_parts = {part.casefold() for part in path.parts}
    if path.name.casefold() in EXCLUDED_NAMES:
        return "repository control metadata is excluded"
    excluded = sorted(folded_parts & EXCLUDED_PARTS)
    if excluded:
        return f"excluded repository path component: {excluded[0]}"
    return None


def _git_paths(root: Path, *arguments: str) -> list[str]:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        item.replace("\\", "/")
        for item in completed.stdout.split("\0")
        if item
    ]


class GitFilesystemRepositoryEvidenceAdapter:
    """Git-aware implementation of the repository evidence query."""

    @staticmethod
    def _artifact_row(
        root: Path,
        relative: str,
        tracking: str,
    ) -> dict[str, Any] | None:
        normalized = relative.replace("\\", "/")
        exclusion_reason = _exclusion_reason(normalized)
        candidate = root / normalized
        if exclusion_reason is not None:
            return {
                "path": normalized,
                "tracking": tracking,
                "size_bytes": 0,
                "exclusion_reason": exclusion_reason,
            }
        if candidate.is_symlink():
            return {
                "path": normalized,
                "tracking": tracking,
                "size_bytes": 0,
                "exclusion_reason": (
                    "symbolic links are excluded from repository evidence"
                ),
            }
        if not candidate.is_file():
            return None
        return {
            "path": normalized,
            "tracking": tracking,
            "size_bytes": candidate.stat().st_size,
            "exclusion_reason": None,
        }

    def collect(self, project_root: Path) -> list[dict[str, Any]]:
        root = project_root.resolve()
        if not root.is_dir():
            raise ValueError(f"project root is not a readable directory: {root}")

        is_git = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
        ).returncode == 0

        rows: list[dict[str, Any]] = []
        if is_git:
            tracked = _git_paths(root, "ls-files", "-z")
            untracked = _git_paths(
                root,
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
            )
            for path in tracked:
                row = self._artifact_row(root, path, "tracked")
                if row is not None:
                    rows.append(row)
            for path in untracked:
                row = self._artifact_row(root, path, "untracked")
                if row is not None:
                    rows.append(row)
        else:
            for current, directories, files in os.walk(root, followlinks=False):
                current_path = Path(current)
                retained_directories = []
                for directory in directories:
                    candidate = current_path / directory
                    relative = candidate.relative_to(root).as_posix()
                    row = self._artifact_row(root, relative, "untracked")
                    if row is not None and row["exclusion_reason"] is not None:
                        rows.append(row)
                    else:
                        retained_directories.append(directory)
                directories[:] = retained_directories
                for filename in files:
                    relative = (
                        (current_path / filename).relative_to(root).as_posix()
                    )
                    row = self._artifact_row(root, relative, "untracked")
                    if row is not None:
                        rows.append(row)

        return sorted(rows, key=lambda row: (row["path"], row["tracking"]))
