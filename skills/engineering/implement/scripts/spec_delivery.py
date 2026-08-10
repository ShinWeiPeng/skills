#!/usr/bin/env python3
"""Delivery-owned adapter for canonical specification context."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


SKILLS_ROOT = Path(__file__).resolve().parents[2]
SPEC_SCRIPTS_ROOT = SKILLS_ROOT / "spec-governance" / "scripts"
if str(SPEC_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SPEC_SCRIPTS_ROOT))

from spec_contract import resolve_spec_context


def assess_delivery_spec_context(
    project_root: Path,
    prompt: str,
    *,
    tracker_path: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Project the canonical child result into the delivery workflow contract."""
    return resolve_spec_context(
        project_root,
        prompt,
        tracker_path=tracker_path,
        branch=branch,
    )
