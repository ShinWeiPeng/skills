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
    stage = "verification-ladder"
    failure_kind = "unknown"
    try:
        if not cli.is_file():
            failure_kind = "missing-entrypoint"
            raise ValueError(str(cli))
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
        failure_kind = (
            "dependency-load-failure"
            if "ModuleNotFoundError" in run.stderr or "ImportError" in run.stderr
            else "malformed-output"
        )
        result = json.loads(run.stdout)
        if (
            not isinstance(result, dict)
            or result.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}
            or run.returncode not in {0, 2}
            or (result["verdict"] == "PASS") != (run.returncode == 0)
        ):
            failure_kind = (
                "exit-code-mismatch"
                if isinstance(result, dict)
                and result.get("verdict") in {"PASS", "FAIL", "BLOCKED"}
                else "malformed-output"
            )
            raise ValueError("invalid validation CLI result")
        result.setdefault("capabilities", {})["verification-ladder"] = {
            "callable": True,
            "entrypoint": str(cli),
            "arguments": command[2:],
            "exit_code": run.returncode,
            "check_verdict": result["verdict"],
            "evidence": "validated-cli-result",
        }
        if result["verdict"] != "PASS":
            result.setdefault("diagnoses", []).append(
                {
                    "category": "validation-failure"
                    if result["verdict"] == "FAIL"
                    else "investigate",
                    "source": "verification-ladder",
                    "evidence": {
                        "verdict": result["verdict"],
                        "errors": result.get("errors", []),
                    },
                    "affected_scope": ["validation-" + phase],
                    "repair_suggestion": "Inspect the original planning or evidence diagnostics; preserve required validation methods.",
                    "authorization": "reuse-current-scope-or-prepare-reviewable-repair",
                    "recheck_command": list(command),
                    "success_condition": "valid CLI result and passing required check",
                    "resume_target": phase,
                    "phase": phase,
                }
            )
        architecture = Path(project_root) / "architecture/manifest.yaml"
        if architecture.is_file():
            stage = "test-validation-layout"
            layout_cli = (
                Path(__file__).resolve().parents[2]
                / "govern-modular-event-architecture/scripts/architecture_cli.py"
            )
            command = [
                sys.executable,
                str(layout_cli),
                "layout",
                "--manifest",
                str(architecture),
            ]
            if not layout_cli.is_file():
                failure_kind = "missing-entrypoint"
                raise ValueError(str(layout_cli))
            layout_run = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120,
                env=os.environ | {"PYTHONIOENCODING": "utf-8"},
            )
            if len(layout_run.stdout) > 4194304:
                raise ValueError("layout response exceeds bounded contract")
            failure_kind = (
                "dependency-load-failure"
                if "ModuleNotFoundError" in layout_run.stderr
                or "ImportError" in layout_run.stderr
                else "malformed-output"
            )
            layout = json.loads(layout_run.stdout)
            if (
                not isinstance(layout, dict)
                or layout.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}
                or layout_run.returncode
                != {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[layout["verdict"]]
            ):
                failure_kind = (
                    "exit-code-mismatch"
                    if isinstance(layout, dict)
                    and layout.get("verdict") in {"PASS", "FAIL", "BLOCKED"}
                    else "malformed-output"
                )
                raise ValueError("invalid layout CLI result")
            result["layout"] = layout
            result.setdefault("capabilities", {})["test-validation-layout"] = {
                "callable": True,
                "entrypoint": str(layout_cli),
                "arguments": ["layout", "--manifest", str(architecture)],
                "exit_code": layout_run.returncode,
                "check_verdict": layout["verdict"],
                "evidence": "validated-cli-result",
            }
            if layout["verdict"] != "PASS":
                result.setdefault("diagnoses", []).append(
                    {
                        "category": "project-configuration"
                        if any(
                            item.get("configuration")
                            for item in layout.get("diagnostics", [])
                        )
                        else "validation-failure"
                        if layout["verdict"] == "FAIL"
                        else "investigate",
                        "source": stage,
                        "evidence": layout,
                        "affected_scope": ["layout-dependent-validation"],
                        "repair_suggestion": "Resolve the original layout diagnostics without changing acceptance thresholds.",
                        "authorization": "reuse-current-scope-or-prepare-reviewable-repair",
                        "recheck_command": command,
                        "success_condition": "layout verdict PASS",
                        "resume_target": phase,
                        "phase": phase,
                    }
                )
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
        if isinstance(exc, subprocess.TimeoutExpired):
            failure_kind = "timeout"
        elif isinstance(exc, OSError):
            failure_kind = "process-launch-failure"
        return {
            "verdict": "BLOCKED",
            "required_gates": ["verification-ladder"],
            "required_layers": [],
            "errors": [f"project validation unavailable: {exc}"],
            "device_actions_authorized": False,
            "capabilities": {stage: {"callable": False, "evidence": failure_kind}},
            "diagnoses": [
                {
                    "category": failure_kind,
                    "source": stage,
                    "evidence": str(exc),
                    "affected_scope": [stage],
                    "repair_suggestion": "Inspect the entrypoint, runtime and original CLI output; repair only within the authorized contract.",
                    "authorization": "reuse-current-scope-or-prepare-reviewable-repair",
                    "recheck_command": command,
                    "success_condition": "valid CLI result and passing required check",
                    "resume_target": phase,
                    "phase": phase,
                }
            ],
        }
