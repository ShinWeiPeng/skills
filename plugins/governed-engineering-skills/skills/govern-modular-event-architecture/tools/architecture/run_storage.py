"""Versioned run storage adapter. Hashes prove integrity, not observations."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid
from contextlib import contextmanager
from contextvars import ContextVar


def safe_path(root, value):
    root = Path(root).resolve()
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    if ".." in candidate.parts:
        raise ValueError("path traversal is forbidden")
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("path is outside project") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if (
            current.is_symlink()
            or (
                current.exists()
                and getattr(current.lstat(), "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            )
            or getattr(current, "is_junction", lambda: False)()
        ):
            raise ValueError("symlink/junction is forbidden: " + str(current))
    return candidate


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    path = Path(path)
    if path.stat().st_size > 1048576:
        raise ValueError("JSON exceeds 1 MiB")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _metadata(metadata):
    required = {"target", "scenario", "tool", "command", "source", "inputs"}
    if (
        not isinstance(metadata, dict)
        or set(metadata) - (required | {"spec", "acceptance", "scenarios"})
        or not required <= set(metadata)
    ):
        raise ValueError(
            "run metadata requires target/scenario/tool/command/source/inputs"
        )
    target = metadata["target"]
    if (
        not isinstance(target, dict)
        or len(target) != 1
        or not set(target) <= {"module", "flow"}
        or not all(isinstance(v, str) and v for v in target.values())
    ):
        raise ValueError("run target must identify one Module or Flow")
    if not isinstance(metadata["scenario"], str) or not metadata["scenario"]:
        raise ValueError("scenario required")
    if "scenarios" in metadata and (
        not isinstance(metadata["scenarios"], list)
        or any(not isinstance(v, str) or not v for v in metadata["scenarios"])
        or len(set(metadata["scenarios"])) != len(metadata["scenarios"])
    ):
        raise ValueError("scenarios must be unique non-empty strings")
    tool = metadata["tool"]
    if (
        not isinstance(tool, dict)
        or set(tool) != {"name", "version"}
        or not all(isinstance(v, str) and v for v in tool.values())
    ):
        raise ValueError("tool name and version required")
    if (
        not isinstance(metadata["command"], list)
        or not metadata["command"]
        or not all(isinstance(v, str) for v in metadata["command"])
    ):
        raise ValueError("command argv required")
    source = metadata["source"]
    if (
        not isinstance(source, dict)
        or set(source) != {"revision", "dirty_sha256"}
        or not isinstance(source["revision"], str)
        or not source["revision"]
        or not re.fullmatch(r"[0-9a-f]{64}", str(source["dirty_sha256"]))
    ):
        raise ValueError("source revision and dirty digest required")
    if not isinstance(metadata["inputs"], dict) or not all(
        isinstance(k, str) and k and re.fullmatch(r"[0-9a-f]{64}", str(v))
        for k, v in metadata["inputs"].items()
    ):
        raise ValueError("inputs must map identifiers to SHA-256")
    if "spec" in metadata and not re.fullmatch(r"SPEC-\d{4}", str(metadata["spec"])):
        raise ValueError("invalid SPEC identity")
    if "acceptance" in metadata and (
        "spec" not in metadata
        or not isinstance(metadata["acceptance"], list)
        or not all(re.fullmatch(r"AC-\d{3}", str(v)) for v in metadata["acceptance"])
    ):
        raise ValueError("invalid acceptance identities")


def validate_target(root, metadata):
    import yaml

    manifest_path = safe_path(root, "architecture/manifest.yaml")
    if not manifest_path.is_file() or manifest_path.stat().st_size > 1048576:
        raise ValueError("run requires a bounded architecture owner catalog")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8-sig"))
    target_kind, target_id = next(iter(metadata["target"].items()))
    if target_id not in {
        item.get("id") for item in manifest.get(target_kind + "s", [])
    }:
        raise ValueError("unknown run target owner")


def allocate_run(root, kind, run_id=None, metadata=None):
    """Exclusively allocate an owned run. Existing identities are never reused."""
    _metadata(metadata)
    validate_target(root, metadata)
    run_id = run_id or uuid.uuid4().hex
    if (
        kind not in {"tests", "validation"}
        or not isinstance(run_id, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", run_id)
    ):
        raise ValueError("invalid run kind or ID")
    path = safe_path(root, Path("artifacts") / kind / run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()  # exclusive across processes
    record = dict(
        schema_version=1, run_id=run_id, kind=kind, started_at=_now(), metadata=metadata
    )
    with (path / ".run.json").open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
    return path


def _identity(root, path):
    path = safe_path(root, path)
    parts = path.relative_to(Path(root).resolve()).parts
    if (
        len(parts) != 3
        or parts[0] != "artifacts"
        or parts[1] not in {"tests", "validation"}
    ):
        raise ValueError("expected artifacts/tests|validation/<run-id>")
    record = read_json(safe_path(root, path / ".run.json"))
    if (
        set(record) != {"schema_version", "run_id", "kind", "started_at", "metadata"}
        or type(record["schema_version"]) is not int
        or record["schema_version"] != 1
        or record["run_id"] != parts[2]
        or record["kind"] != parts[1]
    ):
        raise ValueError("run identity mismatch")
    _metadata(record["metadata"])
    validate_target(root, record["metadata"])
    if datetime.fromisoformat(record["started_at"]).utcoffset() is None:
        raise ValueError("run timestamps require timezone")
    return path, record


_active_operation = ContextVar("run_operation", default=None)


@contextmanager
def operation(root, path):
    """Serialize collection through terminal publication; failed runs retain locks."""
    path, identity = _identity(root, path)
    if (path / "manifest.json").exists() or (path / ".finalizing").exists():
        raise ValueError("finalized/finalizing run cannot be continued")
    if _active_operation.get() == path:
        yield identity
        return
    lock = path / ".operation.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write("exclusive run operation\n")
    # A previous holder may publish between our precheck and exclusive open.
    if (path / "manifest.json").exists() or (path / ".finalizing").exists():
        lock.unlink()
        raise ValueError("run became terminal before operation admission")
    token = _active_operation.set(path)
    try:
        yield identity
    except BaseException:
        raise
    else:
        lock.unlink()
    finally:
        _active_operation.reset(token)


def _files(root, path):
    result = {}
    for current, directories, files in os.walk(path, followlinks=False):
        for name in directories + files:
            safe_path(root, Path(current) / name)
        for name in sorted(files):
            file = Path(current) / name
            relative = file.relative_to(path).as_posix()
            if relative in {
                "manifest.json",
                ".manifest.pending",
                ".finalizing",
                ".operation.lock",
            }:
                continue
            result[relative] = sha256(file)
    return dict(sorted(result.items()))


def finalize_run(root, path, outcome):
    """Publish once after collection stops. Interrupted finalization is incomplete."""
    path, record = _identity(root, path)
    if outcome not in {"PASS", "FAIL", "BLOCKED"}:
        raise ValueError("invalid terminal outcome")
    if (path / "manifest.json").exists():
        raise FileExistsError("finalized run is immutable")
    with (path / ".finalizing").open("x", encoding="utf-8") as stream:
        stream.write("exclusive finalization; never reclaim automatically\n")
    manifest = dict(
        record,
        status="completed",
        outcome=outcome,
        ended_at=_now(),
        files=_files(root, path),
    )
    staging = path / ".manifest.pending"
    with staging.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    # Hard-link publication is atomic and fails if another terminal exists.
    os.link(staging, path / "manifest.json")
    staging.unlink()
    return manifest


def validate_run(root, reference):
    """Validate an explicit terminal reference; never select a latest run."""
    reference = safe_path(root, reference)
    if reference.name != "manifest.json" or not reference.is_file():
        raise ValueError("explicit completed manifest.json required")
    path, identity = _identity(root, reference.parent)
    manifest = read_json(reference)
    if set(manifest) != set(identity) | {
        "status",
        "outcome",
        "ended_at",
        "files",
    } or any(manifest.get(k) != v for k, v in identity.items()):
        raise ValueError("manifest metadata mismatch")
    if manifest["status"] != "completed" or manifest["outcome"] not in {
        "PASS",
        "FAIL",
        "BLOCKED",
    }:
        raise ValueError("run is not terminal")
    end = datetime.fromisoformat(manifest["ended_at"])
    if end.utcoffset() is None or end < datetime.fromisoformat(manifest["started_at"]):
        raise ValueError("invalid terminal time")
    if not isinstance(manifest["files"], dict) or manifest["files"] != _files(
        root, path
    ):
        raise ValueError("artifact file set or SHA-256 mismatch")
    return manifest


def can_prune(relative, entries, ignored_roles):
    """Prune only unconditional subtrees with no potentially governed descendants."""
    import fnmatch

    matching = [
        e
        for e in entries
        if e.get("role") in ignored_roles
        and not e.get("exclude")
        and any(fnmatch.fnmatchcase(relative + "/", p) for p in e.get("include", []))
    ]
    if not matching:
        return False
    for entry in entries:
        if entry.get("role") in ignored_roles:
            continue
        for pattern in entry.get("include", []):
            prefix = re.split(r"[?*\[]", pattern, maxsplit=1)[0]
            if prefix.startswith(relative + "/") or (relative + "/").startswith(prefix):
                return False
    return True


def source_snapshot(root):
    """Capture governed source content; selectors are separately validated inputs."""
    import subprocess

    root = Path(root).resolve()

    def git(*args):
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, timeout=30
        )
        if result.returncode:
            raise ValueError("source provenance unavailable: Git command failed")
        return result.stdout

    try:
        revision = git("rev-parse", "HEAD").decode().strip()
    except ValueError:
        revision = "unversioned"
    # Include ignored governed source: Git identifies revision, never scan scope.
    import fnmatch
    import yaml

    policy_path = safe_path(root, "validation/layout.yaml")
    if not policy_path.is_file():
        raise ValueError("source snapshot requires explicit layout adoption")
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8-sig"))
    entries = policy.get("entries", [])
    digest = hashlib.sha256()
    ignored_roles = {
        "run-output",
        "legacy-output",
        "third-party",
        "build-output",
        "governance-state",
    }
    for current, directories, files in os.walk(root, followlinks=False):
        retained = []
        for name in sorted(directories):
            relative = (Path(current) / name).relative_to(root).as_posix()
            if relative == ".git":
                continue
            safe_path(root, relative)
            if can_prune(relative, entries, ignored_roles):
                continue
            retained.append(name)
        directories[:] = retained
        for name in sorted(files):
            path = safe_path(root, Path(current) / name)
            relative = path.relative_to(root).as_posix()
            matches = [
                e
                for e in entries
                if any(fnmatch.fnmatchcase(relative, p) for p in e.get("include", []))
                and not any(
                    fnmatch.fnmatchcase(relative, p) for p in e.get("exclude", [])
                )
            ]
            if len(matches) != 1:
                if relative in {".gitignore", ".gitattributes"}:
                    continue
                raise ValueError(
                    "source snapshot has unclassified/ambiguous path: " + relative
                )
            if re.fullmatch(r"validation/run-references-SPEC-\d{4}\.json", relative):
                continue  # Selection changes do not change the source under test.
            if matches[0]["role"] not in ignored_roles:
                digest.update(relative.encode())
                digest.update(bytes.fromhex(sha256(path)))
    return {"revision": revision, "dirty_sha256": digest.hexdigest()}
