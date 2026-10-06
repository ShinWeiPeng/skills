"""Translate bounded Codex lifecycle hooks to the spec owner's discussion API."""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
import re
import shlex
import sys
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SKILLS / "spec-governance/scripts"))
sys.path.insert(0, str(SKILLS / "engineering-risk-routing/scripts"))
from spec_delivery import manage_delivery_discussion, resolve_delivery_project


def _context(event, message):
    return {
        "hookSpecificOutput": {"hookEventName": event, "additionalContext": message}
    }


def _request_path(value, root):
    if not isinstance(value, str):
        return False
    path = Path(value)
    target = path if path.is_absolute() else root / path
    expected = root / "spec-governance" / target.name
    return (
        bool(re.fullmatch(r"DISCUSSION-REQUEST-[A-Za-z0-9_-]+\.json", target.name))
        and target.absolute() == expected
        and target.resolve() == expected
        and not target.is_symlink()
        and (not target.exists() or target.stat().st_nlink == 1)
    )


def _recovery_or_read(payload):
    """Recognize bounded native payloads before touching possibly broken state."""
    name = payload.get("tool_name", "")
    if not isinstance(name, str):
        return False
    name = name.split(".")[-1]
    data = payload.get("tool_input", {})
    if not isinstance(data, dict):
        return False
    if name in {"Read", "Glob", "Grep", "read_file", "list_directory"}:
        return True
    host = Path(payload["cwd"]).resolve(strict=True)
    task = payload.get("session_id")
    root = (
        resolve_delivery_project(host, task)
        if isinstance(task, str) and task.strip()
        else host
    )
    if name in {"Edit", "Write"}:
        return _request_path(data.get("file_path", data.get("path")), root)
    if name == "apply_patch":
        patch = data.get("input", data.get("patch", data.get("command", "")))
        if (
            not isinstance(patch, str)
            or not patch.startswith("*** Begin Patch\n")
            or not patch.rstrip().endswith("*** End Patch")
        ):
            return False
        headers = re.findall(
            r"(?m)^\*\*\* (Add File|Update File|Delete File|Move to): (.+)$", patch
        )
        return bool(headers) and all(
            action in {"Add File", "Update File"} and _request_path(path, root)
            for action, path in headers
        )
    if name not in {"Bash", "exec_command"}:
        return False
    workdir = data.get("workdir")
    if workdir is not None:
        if not isinstance(workdir, str):
            return False
        directory = Path(workdir)
        directory = directory if directory.is_absolute() else root / directory
        if directory.resolve() != root:
            return False
    command = data.get("cmd", data.get("command", ""))
    if not isinstance(command, str):
        return False
    # PowerShell's single leading call operator is allowed, shell composition isn't.
    command = command.strip()
    if command.startswith("& "):
        command = command[2:].lstrip()
    if re.search(r"[;|&><`\n\r$()]", command):
        return False
    if re.fullmatch(
        r"(?:git status(?: --short)?|git diff(?: --stat| --name-only)?|pwd|Get-Location)",
        command,
    ):
        return True
    if re.fullmatch(
        r"(?:rg|Get-Content|Get-ChildItem)(?: [^\r\n]*)?", command
    ) and not any(
        token in command for token in ("--pre", "--hostname-bin", "--output", "{", "}")
    ):
        return True
    try:
        argv = [
            token[1:-1]
            if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'"
            else token
            for token in shlex.split(command, posix=False)
        ]
    except ValueError:
        return False
    if len(argv) < 2:
        return False
    runtime = Path(argv.pop(0))
    if (
        str(runtime) not in {"python", "python3", "python.exe", "py"}
        and runtime.resolve() != Path(sys.executable).resolve()
    ):
        return False
    if argv[:2] == ["-X", "utf8"]:
        argv = argv[2:]
    if not argv:
        return False
    script = Path(argv.pop(0))
    script = script if script.is_absolute() else root / script
    owner = SKILLS / "spec-governance/scripts/discussion_state.py"
    if script.resolve() != owner.resolve() or script.is_symlink():
        return False
    if len(argv) != 4 or argv[0] != "--project-root" or argv[2] != "--request":
        return False
    project = Path(argv[1])
    project = project if project.is_absolute() else root / project
    return project.resolve() == root and _request_path(argv[3], root)


def _failure(payload, reason):
    if payload.get("hook_event_name") == "PreToolUse":
        try:
            recovery = _recovery_or_read(payload)
        except (OSError, ValueError, TypeError, KeyError):
            recovery = False
        if not recovery:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
    return {
        "systemMessage": reason
        + " Discussion and SPEC recovery remain available; synchronization is not verified."
    }


def handle_hook(payload):
    event = payload.get("hook_event_name")
    task = payload.get("session_id")
    root = resolve_delivery_project(Path(payload["cwd"]), payload.get("session_id"))
    base = {"task_ref": task}
    if event == "SessionStart":
        result = manage_delivery_discussion(root, {**base, "operation": "resume"})
        active = result["state"]["active_turn"]
        return _context(
            event,
            "This adapter invocation supports SPEC synchronization checks; host trust/loading/firing still needs separate evidence. Restore original turn "
            + str(active)
            + "; resume preserves automatic-repair history. Saving and rechecking remain available. No host-wide interception is claimed.",
        )
    turn = payload.get("turn_id")
    base["turn_id"] = turn
    if event == "UserPromptSubmit":
        prompt = payload.get("prompt", "")
        # Host input has no authoritative engineering-intent field. Establish an
        # obligation without guessing from keywords or inheriting a prior topic.
        engineering = False
        result = manage_delivery_discussion(
            root,
            {
                **base,
                "operation": "enter",
                "prompt": prompt,
                "source_ref": "host:UserPromptSubmit:" + str(turn),
                "engineering": engineering,
            },
        )
        return _context(
            event,
            "grilling owns all engineering discussion. Persist goals, constraints, sourced facts and decisions "
            "before substantive answers; support skills may investigate without invented questions. Current entry: "
            + json.dumps(result, ensure_ascii=False)
            + ". Unknown intent must be classified via discussion_state.py as engineering or non-engineering "
            "with a reason; keyword nonmatches are not exemptions. Observe items and source_refs, reconcile accepted decisions, then record every item_binding and current binding; "
            "reply wording is audit only. Saving failures must not prevent discussion or recovery. Formal SPEC requires a complete adopted change; candidates do not authorize work.",
        )
    if event == "PreToolUse":
        if _recovery_or_read(payload):
            return _context(
                event,
                "Read/SPEC recovery is allowed independently of synchronization. Product authorization is unchanged.",
            )
        result = manage_delivery_discussion(root, {**base, "operation": "status"})
        if result["verdict"] == "PASS":
            return {}
        return {
            "hookSpecificOutput": {
                "hookEventName": event,
                "permissionDecision": "deny",
                "permissionDecisionReason": "Save/classify the matching discussion before dependent work. "
                + json.dumps(result),
            }
        }
    if event == "Stop":
        result = manage_delivery_discussion(
            root,
            {
                **base,
                "operation": "stop",
                "reply_text": payload.get("last_assistant_message") or "",
                "stop_hook_active": payload.get("stop_hook_active", False),
            },
        )
        if result.get("decision") == "block":
            return {"decision": "block", "reason": result["reason"]}
        if result["verdict"] != "PASS":
            return {"systemMessage": result["reason"]}
        return {}
    raise ValueError("unsupported hook event")


def main():
    payload = {}
    try:
        raw = sys.stdin.read(131073)
        if len(raw) > 131072:
            raise ValueError("hook input exceeds 128 KiB")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("hook input must be an object")
        result = handle_hook(payload)
        package_version = "unverified"
        for parent in Path(__file__).resolve().parents:
            manifest = parent / ".codex-plugin/plugin.json"
            if manifest.is_file():
                package_version = str(
                    json.loads(manifest.read_text(encoding="utf-8")).get(
                        "version", "unverified"
                    )
                )
                break
        manage_delivery_discussion(
            Path(payload["cwd"]),
            {
                "operation": "record-hook-observation",
                "task_ref": payload["session_id"],
                "turn_id": payload.get("turn_id"),
                "observation": {
                    "event": payload["hook_event_name"],
                    "host_root": str(Path(payload["cwd"]).resolve()),
                    "entrypoint_sha256": hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                    "package_version": package_version,
                    "input_sha256": hashlib.sha256(
                        json.dumps(payload, sort_keys=True).encode()
                    ).hexdigest(),
                    "result_sha256": hashlib.sha256(
                        json.dumps(result, sort_keys=True).encode()
                    ).hexdigest(),
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                },
            },
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        reason = "Discussion hook failed; saved scope cannot be verified: " + str(exc)
        result = _failure(payload if isinstance(payload, dict) else {}, reason)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
