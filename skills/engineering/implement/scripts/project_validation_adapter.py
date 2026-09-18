"""Bounded technical adapter for the verification planner's public JSON CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def assess_project_validation(
    project_root, spec=None, *, phase="planning", candidate_text=None
):
    """Read project facts through the selected package; never operate a device."""
    cli = (
        Path(__file__).resolve().parents[2]
        / "verification-ladder/scripts/project_validation.py"
    )
    command = [
        sys.executable,
        str(cli),
        "--project-root",
        str(project_root),
        "--phase",
        phase,
    ]
    if spec:
        command += ["--spec", spec]
    if candidate_text is not None:
        command.append("--candidate-stdin")
    try:
        run = subprocess.run(
            command,
            input=candidate_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
            env=os.environ | {"PYTHONIOENCODING": "utf-8"},
        )
        if len(run.stdout) > 4194304:
            raise ValueError("validation response exceeds bounded contract")
        result = json.loads(run.stdout)
        if (
            not isinstance(result, dict)
            or result.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}
            or run.returncode not in {0, 2}
            or (result["verdict"] == "PASS") != (run.returncode == 0)
        ):
            raise ValueError("invalid validation CLI result")
        architecture = Path(project_root) / "architecture/manifest.yaml"
        if architecture.is_file():
            layout_cli = (
                Path(__file__).resolve().parents[2]
                / "govern-modular-event-architecture/scripts/architecture_cli.py"
            )
            layout_run = subprocess.run(
                [
                    sys.executable,
                    str(layout_cli),
                    "layout",
                    "--manifest",
                    str(architecture),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
                env=os.environ | {"PYTHONIOENCODING": "utf-8"},
            )
            if len(layout_run.stdout) > 4194304:
                raise ValueError("layout response exceeds bounded contract")
            layout = json.loads(layout_run.stdout)
            if (
                layout.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}
                or layout_run.returncode
                != {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[layout["verdict"]]
            ):
                raise ValueError("invalid layout CLI result")
            result["layout"] = layout
            result["required_gates"] = sorted(
                set(result.get("required_gates", [])) | {"test-validation-layout"}
            )
            # Planning/enablement authorizes remediation, never overall acceptance.
            if phase in {"acceptance", "release"} and layout["verdict"] != "PASS":
                result["verdict"] = layout["verdict"]
                result.setdefault("errors", []).append(
                    "whole-project test/validation layout is not PASS"
                )
        return result
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {
            "verdict": "BLOCKED",
            "required_gates": ["verification-ladder"],
            "required_layers": [],
            "errors": [f"project validation unavailable: {exc}"],
            "device_actions_authorized": False,
        }
