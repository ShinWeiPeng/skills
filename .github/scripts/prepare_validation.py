"""Materialize ignored compatibility settings from tracked CI definitions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile


FILES = ("layout.yaml", "verification-ladder.yaml")


def safe(path: Path) -> Path:
    for candidate in (path, *path.parents):
        if candidate.is_symlink() or (
            candidate.exists()
            and getattr(candidate.lstat(), "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)
        ):
            raise ValueError(f"redirected validation path: {candidate}")
    return path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(root: Path) -> None:
    root = root.absolute()
    directory = safe(root / "validation")
    marker = safe(directory / ".prepared-from-ci.json")
    previous = json.loads(marker.read_text(encoding="utf-8")) if marker.exists() else {}
    planned = {}
    for name in FILES:
        source = safe(root / ".github" / "validation" / name)
        data = source.read_bytes()
        target = safe(directory / name)
        if target.exists():
            existing = target.read_bytes()
            if existing != data and previous.get(name) != digest(existing):
                raise ValueError(f"preserve edited local configuration: {target}")
        planned[name] = data
    # Complete preflight before changing any configuration.
    directory.mkdir(exist_ok=True)
    for name, data in planned.items():
        target = safe(directory / name)
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as staged:
            staged.write(data)
            stage = Path(staged.name)
        try:
            safe(target)
            os.replace(stage, target)
        finally:
            stage.unlink(missing_ok=True)
    marker.write_text(
        json.dumps({name: digest(data) for name, data in planned.items()}, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    prepare(parser.parse_args().project_root)
    print("Validation compatibility settings prepared; local outputs remain ignored.")


if __name__ == "__main__":
    main()
