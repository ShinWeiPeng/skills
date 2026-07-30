from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Protocol


PASSIVE_RISKS = {"passive", "build"}


def _terminate_tree(process: subprocess.Popen[bytes]) -> bool:
    if os.name == "nt":
        killed = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, shell=False)
        success = killed.returncode == 0
    else:
        try:
            os.killpg(process.pid, 15)
        except ProcessLookupError:
            pass
        time.sleep(0.1)
        try:
            os.killpg(process.pid, 9)
        except ProcessLookupError:
            pass
        success = True
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        success = False
    return success


class CollectionInputPort(Protocol):
    def submit(self, action: str, approvals: set[str]) -> dict[str, Any]: ...


class CollectionOutputPort(Protocol):
    def publish(self, event: dict[str, Any]) -> None: ...


class TransportPort(Protocol):
    def capture(self, output: Path) -> dict[str, Any]: ...


def run_action(profile: dict[str, Any], name: str, approvals: set[str]) -> dict[str, Any]:
    action = profile.get("actions", {}).get(name)
    if not isinstance(action, dict):
        return {"status": "BLOCKED", "reason": f"action {name!r} is not declared", "spawned": False}
    risk = action.get("risk", "passive")
    if risk not in PASSIVE_RISKS and risk not in approvals:
        return {"status": "BLOCKED", "reason": f"approval for risk {risk!r} is required", "risk": risk, "spawned": False}
    argv = [action["executable"], *action.get("args", [])]
    project_root = Path(profile.get("_project_root", ".")).resolve()
    cwd_value = Path(action.get("cwd", "."))
    cwd = (project_root / cwd_value).resolve() if not cwd_value.is_absolute() else cwd_value.resolve()
    if not cwd.is_relative_to(project_root):
        return {"status": "BLOCKED", "reason": "action cwd escapes the project root", "cwd": str(cwd), "spawned": False}
    started = time.monotonic()
    max_output = int(action.get("max_output_bytes", 1048576))
    artifact_path = None
    artifact_limit = None
    if action.get("bounded_artifact"):
        artifact_path = (project_root / str(action["bounded_artifact"])).resolve()
        if not artifact_path.is_relative_to(project_root):
            return {"status": "BLOCKED", "reason": "bounded_artifact escapes the project root", "spawned": False}
        artifact_limit = int(action["max_artifact_bytes"])
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False, start_new_session=os.name != "nt", creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
        captured = bytearray()
        output_exceeded = threading.Event()

        def drain() -> None:
            assert process.stdout is not None
            while True:
                chunk = process.stdout.read(65536)
                if not chunk:
                    return
                remaining = max_output - len(captured)
                if remaining > 0:
                    captured.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    output_exceeded.set()
                    return

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        termination_reason = None
        timeout_seconds = float(action.get("timeout_seconds", 300))
        while process.poll() is None:
            if output_exceeded.is_set():
                termination_reason = "action output exceeded max_output_bytes"
            elif artifact_path is not None and artifact_path.exists() and artifact_path.stat().st_size >= artifact_limit:
                termination_reason = "bounded artifact reached max_artifact_bytes"
            elif time.monotonic() - started >= timeout_seconds:
                termination_reason = "action timed out after execution began"
            if termination_reason:
                if not _terminate_tree(process):
                    termination_reason += "; process-tree termination was not confirmed"
                break
            time.sleep(0.02)
        reader.join(timeout=1)
        if process.stdout is not None:
            process.stdout.close()
        stdout = captured.decode("utf-8", errors="replace")
        stderr = ""
        stdout_size = len(captured)
        stderr_size = 0
        return_code = process.returncode
    except FileNotFoundError:
        return {"status": "BLOCKED", "reason": f"executable not found: {argv[0]}", "argv": argv, "cwd": str(cwd), "spawned": False}
    except Exception as exc:
        termination_confirmed = True if process is None else _terminate_tree(process)
        return {"status": "BLOCKED", "reason": f"action raised {type(exc).__name__}: {exc}; process-tree termination confirmed={termination_confirmed}", "argv": argv, "cwd": str(cwd), "spawned": process is not None}
    if output_exceeded.is_set() and termination_reason is None:
        termination_reason = "action output exceeded max_output_bytes"
    exceeded = output_exceeded.is_set() or termination_reason == "bounded artifact reached max_artifact_bytes"
    timed_out = termination_reason == "action timed out after execution began"
    return {
        "status": "FAIL" if timed_out else ("BLOCKED" if exceeded else ("PASS" if return_code == 0 else "FAIL")),
        "reason": termination_reason,
        "argv": argv,
        "cwd": str(cwd),
        "exit_code": return_code,
        "stdout": stdout,
        "stderr": stderr,
        "output_bytes": f">{max_output}" if exceeded else stdout_size + stderr_size,
        "max_output_bytes": max_output,
        "elapsed_seconds": time.monotonic() - started,
        "risk": risk,
        "spawned": True,
    }
