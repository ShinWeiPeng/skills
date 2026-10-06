"""Durable, optimistic document updates owned by specification governance.

The caller owns execution authorization. Recovery checks the same reviewed plan,
never resets it, and validates the whole result before marking it effective.
"""

from __future__ import annotations
import hashlib
import json
import os
import threading
import re
from pathlib import Path
from contextvars import ContextVar

_VALIDATING = ContextVar("document_update_validation", default=frozenset())
_LOCKED_ROOT = ContextVar("document_lock_root", default=None)

from contextlib import contextmanager
from functools import wraps


@contextmanager
def document_lock(root):
    root = Path(root).resolve()
    identity = (str(root), os.getpid(), threading.get_ident())
    if _LOCKED_ROOT.get() == identity:
        yield
        return
    from state_lock import project_state_lock

    with project_state_lock(root, "document-collection"):
        token = _LOCKED_ROOT.set(identity)
        try:
            yield
        finally:
            _LOCKED_ROOT.reset(token)


def locked_documents(function):
    @wraps(function)
    def run(root, *args, **kwargs):
        with document_lock(root):
            return function(root, *args, **kwargs)

    return run


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    root = Path(root).resolve(strict=True)
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("expected a nonempty portable project-relative path")
    path = Path(relative)
    reserved = {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(1, 10)),
        *(f"lpt{i}" for i in range(1, 10)),
    }
    if any(
        not part or part.split(".")[0].casefold() in reserved
        for part in relative.split("/")
    ):
        raise ValueError("reserved or empty document path component")
    if any(
        part != part.rstrip(" .")
        or ":" in part
        or any(ord(c) < 32 or c in '<>"|?*' for c in part)
        for part in relative.split("/")
    ):
        raise ValueError("unsafe portable path component: " + relative)
    if any(
        part.casefold() in {".git", ".codex", ".agents", "..", "."}
        for part in relative.split("/")
    ):
        raise ValueError("protected document path: " + relative)
    if path.is_absolute() or any(
        p in {".", "..", ".git", ".codex", ".agents"} for p in path.parts
    ):
        raise ValueError("unsafe document path: " + relative)
    target = root / path
    for parent in [target, *target.parents]:
        if parent == root:
            break
        if parent.is_symlink() or (parent.exists() and parent.resolve() != parent):
            raise ValueError("redirected document path: " + relative)
    target.resolve().relative_to(root)
    if target.exists() and (not target.is_file() or target.stat().st_nlink != 1):
        raise ValueError("document must be an ordinary unshared file: " + relative)
    return target


def atomic_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    import tempfile

    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _save(path, state):
    atomic_bytes(
        path,
        (
            json.dumps(state, sort_keys=True, ensure_ascii=True, indent=2) + "\n"
        ).encode(),
    )


def _plan_path(root, operation_id):
    if not isinstance(operation_id, str) or not re.fullmatch(
        r"[a-zA-Z0-9_-]{1,100}", operation_id
    ):
        raise ValueError("invalid update operation ID")
    return safe_path(root, "spec-governance/document-updates/" + operation_id + ".json")


@locked_documents
def prepare_update(root, operation_id, changes, *, binding, validate_candidate):
    """Check all candidate bytes, reserve the immutable plan, retain original bytes."""
    if not isinstance(changes, dict) or not changes or len(changes) > 256:
        raise ValueError("expected 1..256 reviewed document replacements")
    rows = {}
    portable_targets = set()
    for relative, change in sorted(changes.items()):
        target = safe_path(root, relative)
        identity = relative.casefold()
        if identity in portable_targets:
            raise ValueError("duplicate portable document target: " + relative)
        portable_targets.add(identity)
        if not isinstance(change, dict) or set(change) != {"before_sha256", "content"}:
            raise ValueError("invalid replacement: " + relative)
        data = (
            change["content"].encode("utf-8") if change["content"] is not None else None
        )
        if data is not None and len(data) > 1048576:
            raise ValueError("document replacement exceeds 1 MiB")
        old = target.read_bytes() if target.exists() else None
        if (
            relative.casefold().startswith("architecture/history/")
            and old is not None
            and old != data
        ):
            raise ValueError("immutable history cannot be replaced: " + relative)
        if (digest(old) if old is not None else None) != change["before_sha256"]:
            raise ValueError("candidate base changed: " + relative)
        rows[relative] = {
            "before_sha256": change["before_sha256"],
            "before_hex": old.hex() if old is not None else None,
            "after_sha256": digest(data) if data is not None else None,
            "after_hex": data.hex() if data is not None else None,
        }
    validate_candidate(
        {
            p: bytes.fromhex(row["after_hex"]) if row["after_hex"] is not None else None
            for p, row in rows.items()
        }
    )
    path = _plan_path(root, operation_id)
    state = {
        "format_version": 1,
        "operation_id": operation_id,
        "binding": binding,
        "files": rows,
        "written": [],
        "status": "prepared",
        "attempts": [],
        "cause": None,
    }
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if any(
            previous.get(key) != state[key]
            for key in ["format_version", "operation_id", "binding", "files"]
        ):
            raise ValueError("operation ID already reserved for a different plan")
        return previous
    _save(path, state)
    return state


@locked_documents
def resume_update(
    root, operation_id, *, binding, authorize, validate_result, after_write=None
):
    """Solve an interrupted update without overwriting later edits or replaying writes."""
    from state_lock import project_state_lock

    path = _plan_path(root, operation_id)
    with project_state_lock(Path(root), "document-update:" + operation_id):
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("format_version") != 1 or state.get("binding") != binding:
            raise ValueError("update binding differs from reviewed plan")
        authorize(binding)  # current task/SPEC authority, not an acceptance gate
        try:
            for relative, row in state["files"].items():
                target = safe_path(root, relative)
                actual = digest(target.read_bytes()) if target.exists() else None
                if actual not in {row["before_sha256"], row["after_sha256"]}:
                    raise ValueError("concurrent modification retained: " + relative)
            if state["status"] == "effective":
                if any(
                    (
                        digest(safe_path(root, p).read_bytes())
                        if safe_path(root, p).exists()
                        else None
                    )
                    != row["after_sha256"]
                    for p, row in state["files"].items()
                ):
                    raise ValueError("effective update has drifted")
                validate_result()
                return state
            if len(state["attempts"]) >= 64:
                raise ValueError(
                    "recovery history exhausted; investigate and reserve an evidenced successor"
                )
            state["status"] = "updating"
            state["attempts"].append(
                {"attempt": len(state["attempts"]) + 1, "cause": state.get("cause")}
            )
            _save(path, state)
            for relative, row in state["files"].items():
                target = safe_path(root, relative)
                actual = digest(target.read_bytes()) if target.exists() else None
                if actual != row["after_sha256"]:
                    if actual != row["before_sha256"]:
                        raise ValueError(
                            "concurrent modification retained: " + relative
                        )
                    if row["after_hex"] is None:
                        target.unlink()
                    else:
                        atomic_bytes(target, bytes.fromhex(row["after_hex"]))
                if relative not in state["written"]:
                    state["written"].append(relative)
                _save(path, state)
                if after_write:
                    after_write(relative)
            token = _VALIDATING.set(_VALIDATING.get() | {operation_id})
            try:
                validate_result()
            finally:
                _VALIDATING.reset(token)
            state.update(status="effective", cause=None)
            _save(path, state)
            return state
        except BaseException as error:
            state.update(
                status="incomplete", cause=type(error).__name__ + ": " + str(error)
            )
            _save(path, state)
            raise


def assert_complete(root, relatives):
    """Deny dependent reads of any partially applied update; recovery stays usable."""
    directory = Path(root) / "spec-governance/document-updates"
    for path in directory.glob("*.json"):
        state = json.loads(path.read_text(encoding="utf-8"))
        if (
            state.get("status") in {"updating", "incomplete"}
            and state["operation_id"] not in _VALIDATING.get()
            and set(relatives) & set(state["files"])
        ):
            raise ValueError(
                "document update incomplete: "
                + state["operation_id"]
                + "; resume the reserved update"
            )


_RECOVERY_FILES = ContextVar("document_recovery_originals", default=None)


@contextmanager
def recovery_originals(root, operation_id):
    """Only the composed recovery authority check uses reserved original dependencies."""
    root = Path(root).resolve()
    with document_lock(root):
        plan = json.loads(_plan_path(root, operation_id).read_text(encoding="utf-8"))
        originals = {
            str(safe_path(root, p)): bytes.fromhex(row["before_hex"])
            for p, row in plan["files"].items()
            if row["before_hex"] is not None
        }
        token = _RECOVERY_FILES.set((root, originals))
        validating = _VALIDATING.set(_VALIDATING.get() | {operation_id})
        try:
            yield
        finally:
            _VALIDATING.reset(validating)
            _RECOVERY_FILES.reset(token)


def reference_bytes(path):
    current = _RECOVERY_FILES.get()
    if current and str(Path(path)) in current[1]:
        return current[1][str(Path(path))]
    return Path(path).read_bytes()


@contextmanager
def candidate_documents(root, files):
    """Read-only overlay for the owner's complete candidate validation."""
    root = Path(root).resolve()
    with document_lock(root):
        values = {str(safe_path(root, p)): c.encode("utf-8") for p, c in files.items()}
        token = _RECOVERY_FILES.set((root, values))
        try:
            yield
        finally:
            _RECOVERY_FILES.reset(token)


@contextmanager
def validation_operations(*operations):
    """Scope only the reserved parent and its verified audit child during recovery."""
    token = _VALIDATING.set(_VALIDATING.get() | set(operations))
    try:
        yield
    finally:
        _VALIDATING.reset(token)
