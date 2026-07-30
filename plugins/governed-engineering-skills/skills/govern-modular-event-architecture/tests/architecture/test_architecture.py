"""Project-local entrypoint for the skill's schema 2.0.2 architecture tests."""

from __future__ import annotations

import runpy
from pathlib import Path


runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "test_architecture.py"),
    run_name="__main__",
)
