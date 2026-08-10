from __future__ import annotations

import json
import hashlib
import platform
import re
import shutil
import socket
import time
from pathlib import Path
from typing import Any


class PlatformTransportAdapter:
    """Marker contract for OS, serial, TCP, process, and file adapters."""

    provider: str


PROVIDER_COMMANDS = {
    "etw-wpr": ("wpr",),
    "perf-ftrace": ("perf",),
    "instruments-xctest": ("xcrun", "xctrace"),
    "structured-log": (),
}


def probe(profile: dict[str, Any]) -> dict[str, Any]:
    target = profile["target"]
    provider = target["provider"]
    commands = {name: shutil.which(name) for name in PROVIDER_COMMANDS[provider]}
    available = all(commands.values()) if commands else True
    actual = provider
    fallback_reason = None
    if not available and target.get("fallback") == "structured-log":
        actual = "structured-log"
        fallback_reason = "selected native provider is unavailable"
    transport = profile.get("transport", {})
    return {
        "host_os": platform.system().lower(),
        "target_platform": target["platform"],
        "requested_provider": provider,
        "actual_provider": actual,
        "provider_available": available,
        "probe_scope": "passive-availability-only",
        "capture_readiness": "unverified-until-approved-action-or-import",
        "commands": commands,
        "fallback_reason": fallback_reason,
        "transport_type": transport.get("type"),
        "status": "PASS" if available or actual == "structured-log" else "BLOCKED",
    }


def _binding(profile: dict[str, Any]) -> dict[str, Any]:
    transport = profile.get("transport", {})
    name = transport.get("binding")
    bindings = profile.get("bindings", {})
    if name and isinstance(bindings, dict) and isinstance(bindings.get(name), dict):
        merged = dict(transport)
        merged.update(bindings[name])
        return merged
    return dict(transport)


def _capture_timeout(profile: dict[str, Any], scenario: dict[str, Any]) -> float:
    transport_limit = float(_binding(profile).get("timeout_seconds", float("inf")))
    return min(transport_limit, float(scenario["max_duration_ms"]) / 1000.0)


def _session_complete(data: bytearray, scenario: dict[str, Any]) -> bool:
    text = data.decode("utf-8", errors="ignore")
    begin = re.search(rf"VAL_SESSION_BEGIN\b[^\r\n]*\brun=([^\s]+)[^\r\n]*\bscenario={re.escape(str(scenario['id']))}\b", text)
    if begin is None:
        return False
    reason = re.escape(str(scenario["completion"]["session_end_reason"]))
    return re.search(rf"VAL_SESSION_END\b[^\r\n]*\brun={re.escape(begin.group(1))}\b[^\r\n]*\breason={reason}\b", text) is not None


def capture_tcp(profile: dict[str, Any], scenario: dict[str, Any], output: Path) -> dict[str, Any]:
    cfg = _binding(profile)
    timeout = _capture_timeout(profile, scenario)
    max_bytes = int(cfg.get("max_bytes", 1048576))
    mode = cfg.get("type")
    host = str(cfg.get("host", "127.0.0.1"))
    port = int(cfg["port"])
    started = time.monotonic()
    data = bytearray()
    if mode == "tcp-client":
        with socket.create_connection((host, port), timeout=timeout) as conn:
            conn.settimeout(min(1.0, timeout))
            while len(data) < max_bytes and time.monotonic() - started < timeout:
                try:
                    chunk = conn.recv(min(65536, max_bytes - len(data)))
                except socket.timeout:
                    continue
                if not chunk:
                    break
                data.extend(chunk)
                if _session_complete(data, scenario):
                    break
    elif mode == "tcp-server":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((host, port))
            server.listen(1)
            server.settimeout(timeout)
            conn, _ = server.accept()
            with conn:
                conn.settimeout(min(1.0, timeout))
                while len(data) < max_bytes and time.monotonic() - started < timeout:
                    try:
                        chunk = conn.recv(min(65536, max_bytes - len(data)))
                    except socket.timeout:
                        continue
                    if not chunk:
                        break
                    data.extend(chunk)
                    if _session_complete(data, scenario):
                        break
    else:
        raise ValueError("TCP capture requires tcp-client or tcp-server")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bytes(data))
    capped = len(data) >= max_bytes
    complete = _session_complete(data, scenario)
    reason = "capture reached max_bytes; completeness cannot be proven" if capped else (None if complete else "matching session completion was not observed before the bounded capture ended")
    return {"status": "PASS" if complete and not capped else "BLOCKED", "reason": reason, "completion_seen": complete, "bytes": len(data), "elapsed_seconds": time.monotonic() - started, "output": str(output)}


def capture_serial(profile: dict[str, Any], scenario: dict[str, Any], output: Path, approvals: set[str]) -> dict[str, Any]:
    cfg = _binding(profile)
    if cfg.get("dtr") is None or cfg.get("rts") is None:
        if "serial-open-reset" not in approvals:
            return {"status": "BLOCKED", "reason": "DTR/RTS are unknown; serial-open-reset approval is required"}
    try:
        import serial
    except ImportError:
        return {"status": "BLOCKED", "reason": "pyserial is unavailable"}
    timeout = _capture_timeout(profile, scenario)
    max_bytes = int(cfg.get("max_bytes", 1048576))
    port = cfg.get("port")
    if not port:
        return {"status": "BLOCKED", "reason": "serial port binding is missing"}
    started = time.monotonic()
    data = bytearray()
    conn = serial.Serial(port=None, baudrate=int(cfg.get("baud", 115200)), timeout=0.2)
    try:
        if cfg.get("dtr") is not None:
            conn.dtr = bool(cfg["dtr"])
        if cfg.get("rts") is not None:
            conn.rts = bool(cfg["rts"])
        conn.port = port
        conn.open()
        while len(data) < max_bytes and time.monotonic() - started < timeout:
            chunk = conn.read(min(4096, max_bytes - len(data)))
            if chunk:
                data.extend(chunk)
                if _session_complete(data, scenario):
                    break
    finally:
        conn.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bytes(data))
    capped = len(data) >= max_bytes
    complete = _session_complete(data, scenario)
    reason = "capture reached max_bytes; completeness cannot be proven" if capped else (None if complete else "matching session completion was not observed before the bounded capture ended")
    return {"status": "PASS" if complete and not capped else "BLOCKED", "reason": reason, "completion_seen": complete, "bytes": len(data), "elapsed_seconds": time.monotonic() - started, "output": str(output)}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_bounded_json(path: Path, max_bytes: int = 1048576) -> dict[str, Any]:
    data = bytearray()
    with path.open("rb") as source:
        while True:
            chunk = source.read(min(65536, max_bytes - len(data) + 1))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > max_bytes:
                raise ValueError(f"{path} exceeds {max_bytes} bytes")
    value = json.loads(data.decode("utf-8"), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-standard JSON number {token}")))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def hash_evidence_reference(project_root: Path, value: str, max_bytes: int) -> dict[str, Any]:
    root = project_root.resolve()
    candidate = Path(value)
    path = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    if not path.is_relative_to(root):
        raise ValueError("evidence path escapes the project root")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("evidence file exceeds transport.max_bytes")
            digest.update(chunk)
    return {"path": path.relative_to(root).as_posix(), "sha256": digest.hexdigest(), "bytes": size}


def write_text_exclusive(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as target:
        target.write(text)


def write_json_exclusive(path: Path, value: dict[str, Any]) -> None:
    write_text_exclusive(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")
