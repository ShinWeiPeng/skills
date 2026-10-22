#!/usr/bin/env python3
"""Install the shared Doc Coauthoring skill directly into personal skill directories."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import io
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import uuid
import urllib.parse
import urllib.request
import zipfile

NAME = "doc-coauthoring"
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
TARGETS = {"codex": ".agents", "claude": ".claude"}


def guard(path):
    """Reject redirection rather than traversing a user-controlled link."""
    path = Path(path).absolute()
    for item in (path, *path.parents):
        if item.is_symlink() or (
            item.exists()
            and getattr(item.lstat(), "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)
        ):
            raise ValueError("Preserve redirected path: " + str(item))
    return path


def inventory(directory):
    guard(directory)
    result = {}
    for path in sorted(directory.rglob("*")):
        guard(path)
        if path.is_file():
            if path.stat().st_nlink > 1:
                raise ValueError("Preserve shared file: " + str(path))
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        elif not path.is_dir():
            raise ValueError("Unsupported file: " + str(path))
    return result


def hashes(files):
    return {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


def download(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "doc-coauthoring-installer"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(32 * 1024 * 1024 + 1)
    if len(data) > 32 * 1024 * 1024:
        raise ValueError("Release download exceeds the supported size.")
    return data


@contextmanager
def source_package(args):
    local = Path(__file__).resolve().parents[1]
    if args.source is not None:
        if args.release_version and payload(args.source)[0] != args.release_version:
            raise ValueError("The local source does not match --version.")
        yield args.source
        return
    if args.release_version is None and (local / "package.json").is_file():
        yield local
        return
    version = args.release_version or "latest"
    if version == "latest":
        record = json.loads(
            download(
                "https://raw.githubusercontent.com/ShinWeiPeng/skills/"
                "doc-coauthoring-release/publication-record.json"
            )
        )
        version = record["artifact"]["version"]
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("Choose a stable release version: MAJOR.MINOR.PATCH")
    tag = urllib.parse.quote(NAME + "@" + version, safe="")
    archive_data = download(
        "https://codeload.github.com/ShinWeiPeng/skills/zip/refs/tags/" + tag
    )
    with tempfile.TemporaryDirectory(prefix="doc-coauthoring-download-") as temporary:
        source = Path(temporary)
        seen = set()
        total = 0
        with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
            for info in archive.infolist():
                name = PurePosixPath(info.filename)
                if name.is_absolute() or ".." in name.parts or "\\" in info.filename:
                    raise ValueError("Unsafe release archive path.")
                parts = name.parts
                if len(parts) < 3 or parts[1] != NAME or info.is_dir():
                    continue
                relative = PurePosixPath(*parts[2:]).as_posix()
                if relative not in {
                    "package.json",
                    "UPSTREAM.md",
                    "LICENSE",
                    "NOTICE",
                } and not (relative.startswith("skills/" + NAME + "/")):
                    continue
                if stat.S_ISLNK(info.external_attr >> 16) or relative in seen:
                    raise ValueError("Redirected or duplicate release archive entry.")
                seen.add(relative)
                total += info.file_size
                if total > 8 * 1024 * 1024 or len(seen) > 1000:
                    raise ValueError("Release payload exceeds the supported size.")
                target = source.joinpath(*parts[2:])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info))
        if payload(source)[0] != version:
            raise ValueError("Release package version does not match its selected tag.")
        yield source


def payload(source):
    source = guard(source)
    metadata = json.loads(guard(source / "package.json").read_text(encoding="utf-8"))
    version = metadata.get("version", "")
    if metadata.get("name") != NAME or not VERSION.fullmatch(version):
        raise ValueError("Source must be a versioned Doc Coauthoring package.")
    skill = source / "skills" / NAME
    files = {}
    for path in sorted(skill.rglob("*")):
        guard(path)
        if path.is_file():
            relative = path.relative_to(skill).as_posix()
            if "__pycache__" in path.parts:
                continue
            data = path.read_bytes()
            try:
                data = data.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
            except UnicodeDecodeError:
                pass
            files[relative] = data
    required = {
        "SKILL.md",
        "agents/openai.yaml",
        "references/codex.md",
        "references/claude.md",
    }
    if not required <= set(files):
        raise ValueError(
            "Incomplete skill payload: " + str(sorted(required - set(files)))
        )
    if not re.search(
        r"(?m)^name: doc-coauthoring\s*$", files["SKILL.md"].decode("utf-8")
    ):
        raise ValueError("The source skill identity is invalid.")
    for name in ("UPSTREAM.md", "LICENSE", "NOTICE"):
        path = guard(source / name)
        files["references/" + name] = path.read_bytes()
    files["SKILL.md"] = files["SKILL.md"].replace(
        b"../../UPSTREAM.md", b"references/UPSTREAM.md"
    )
    return version, files


def write_files(directory, files):
    guard(directory).mkdir(parents=True, exist_ok=True)
    for relative, data in files.items():
        path = guard(directory / relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def atomic_json(path, data):
    guard(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as staged:
        stage = Path(staged.name)
        staged.write(
            (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")
        )
    try:
        os.replace(stage, path)
    finally:
        stage.unlink(missing_ok=True)


def read_state(root):
    path = guard(root / "state.json")
    if not path.exists():
        versions = guard(root / "versions")
        if versions.exists() and any(versions.iterdir()):
            raise ValueError(
                "Unknown version store; preserve it and inspect " + str(root)
            )
        return {"schema_version": 1, "versions": {}, "active": {}}
    state = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(state, dict)
        or state.get("schema_version") != 1
        or not isinstance(state.get("versions"), dict)
        or not isinstance(state.get("active"), dict)
    ):
        raise ValueError("Unknown installer state; preserve " + str(path))
    for version, record in state["versions"].items():
        if not VERSION.fullmatch(version) or not isinstance(record, dict):
            raise ValueError("Invalid stored version; preserve installer state.")
        files = record.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError("Invalid stored inventory; preserve installer state.")
        for name, digest in files.items():
            if (
                not isinstance(name, str)
                or "\\" in name
                or Path(name).is_absolute()
                or ".." in Path(name).parts
                or not isinstance(digest, str)
                or not re.fullmatch(r"[0-9a-f]{64}", digest)
            ):
                raise ValueError(
                    "Invalid stored file identity; preserve installer state."
                )
    for target, record in state["active"].items():
        if (
            target not in TARGETS
            or not isinstance(record, dict)
            or record.get("version") not in state["versions"]
            or (
                record.get("previous") is not None
                and record["previous"] not in state["versions"]
            )
        ):
            raise ValueError("Invalid activation state; preserve installer state.")
    return state


def active_path(home, target):
    return guard(home / TARGETS[target] / "skills" / NAME)


def verify_version(root, state, version):
    if version not in state["versions"]:
        raise ValueError("Version is not installed: " + version)
    directory = guard(root / "versions" / version)
    if (
        not directory.is_dir()
        or inventory(directory) != state["versions"][version]["files"]
    ):
        raise ValueError(
            "Stored version was modified; preserve and inspect " + str(directory)
        )
    return directory


def check_active(home, state, target):
    active = active_path(home, target)
    previous = state["active"].get(target)
    if active.exists():
        if not previous or not active.is_dir():
            raise ValueError(
                "Unknown existing skill; preserve it and move it aside manually: "
                + str(active)
            )
        expected = state["versions"][previous["version"]]["files"]
        if inventory(active) != expected:
            raise ValueError(
                "Locally modified skill; preserve your edits before retrying: "
                + str(active)
            )
    return active


def remove_stage(root, directory):
    guard(directory).resolve().relative_to(guard(root / "staging").resolve())
    inventory(directory)
    shutil.rmtree(directory)


def activate(home, root, state, selections):
    active_paths = {target: check_active(home, state, target) for target in selections}
    sources = {
        target: verify_version(root, state, version)
        for target, version in selections.items()
    }
    updated = [
        target
        for target, version in selections.items()
        if not active_paths[target].exists()
        or state["active"].get(target, {}).get("version") != version
    ]
    changed = [
        target
        for target in updated
        if not active_paths[target].exists()
        or inventory(active_paths[target])
        != state["versions"][selections[target]]["files"]
    ]
    if not updated:
        print("No changes: identical skill content is already active.")
        return
    stage = guard(root / "staging" / uuid.uuid4().hex)
    stage.mkdir(parents=True)
    applied = []
    moved = []
    try:
        for target in changed:
            shutil.copytree(sources[target], stage / (target + "-new"))
        for target in changed:
            active = active_paths[target]
            guard(active.parent).mkdir(parents=True, exist_ok=True)
            check_active(home, state, target)
            if active.exists():
                os.replace(active, stage / (target + "-old"))
                moved.append(target)
            os.replace(stage / (target + "-new"), active)
            applied.append(target)
        next_state = json.loads(json.dumps(state))
        for target in updated:
            old_version = state["active"].get(target, {}).get("version")
            next_state["active"][target] = {
                "version": selections[target],
                "previous": (
                    state["active"].get(target, {}).get("previous")
                    if old_version == selections[target]
                    else old_version
                ),
            }
        atomic_json(root / "state.json", next_state)
    except Exception:
        # Move only our new activations out of discovery; retain backups if recovery fails.
        for target in reversed(changed):
            active = active_paths[target]
            if target in applied:
                os.replace(active, stage / (target + "-failed"))
            if target in moved:
                os.replace(stage / (target + "-old"), active)
        raise
    else:
        try:
            remove_stage(root, stage)
        except (OSError, ValueError) as error:
            print(
                "Activation succeeded; cleanup deferred at "
                + str(stage)
                + ": "
                + str(error),
                file=sys.stderr,
            )
    for target in updated:
        print(target + ": active " + selections[target])


def install(home, root, state, source, targets):
    version, files = payload(source)
    for target in targets:
        check_active(home, state, target)
    expected = hashes(files)
    destination = guard(root / "versions" / version)
    if version in state["versions"]:
        verify_version(root, state, version)
        if state["versions"][version]["files"] != expected:
            raise ValueError("Different content already exists for version " + version)
    elif destination.exists():
        raise ValueError(
            "Unknown existing version directory; preserve " + str(destination)
        )
    else:
        stage = guard(root / "staging" / uuid.uuid4().hex)
        try:
            write_files(stage, files)
            if inventory(stage) != expected:
                raise ValueError("Staged payload validation failed.")
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage, destination)
        finally:
            if stage.exists():
                remove_stage(root, stage)
        state["versions"][version] = {"files": expected, "source": str(source)}
        # Persist the retained version before activation; failure cannot lose an old activation.
        atomic_json(root / "state.json", state)
    activate(home, root, state, dict.fromkeys(targets, version))
    return version


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "operation",
        nargs="?",
        choices=["install", "switch", "rollback", "list"],
        default="install",
    )
    result.add_argument("selected_version", nargs="?")
    result.add_argument("--home", type=Path, default=Path.home())
    result.add_argument("--target", choices=["codex", "claude", "both"])
    result.add_argument(
        "--source", type=Path, help="Use a local package instead of a download."
    )
    result.add_argument(
        "--version", dest="release_version", help="Install a release version or latest."
    )
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    if args.operation != "list" and not args.target:
        if not sys.stdin.isatty():
            print("Choose --target codex, claude, or both.", file=sys.stderr)
            return 2
        try:
            choice = input(
                "Install for 1) Codex  2) Claude Code  3) Both [3]: "
            ).strip()
        except EOFError:
            print("Choose --target codex, claude, or both.", file=sys.stderr)
            return 2
        args.target = {"": "both", "1": "codex", "2": "claude", "3": "both"}.get(choice)
        if not args.target:
            print("Invalid target selection.", file=sys.stderr)
            return 2
    targets = list(TARGETS) if args.target == "both" else [args.target]
    acquired = False
    try:
        home = guard(args.home)
        root = guard(home / ".doc-coauthoring")
        lock = root / ".install.lock"
        root.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(guard(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        acquired = True
        os.close(descriptor)
        state = read_state(root)
        if args.operation == "install":
            if args.selected_version:
                raise ValueError("Use switch VERSION to activate a retained version.")
            with source_package(args) as source:
                version = install(home, root, state, source, targets)
            print("Doc Coauthoring " + version + " installed without a plugin.")
        elif args.operation == "list":
            if not state["versions"]:
                print("No installed versions.")
            for version in sorted(
                state["versions"], key=lambda value: tuple(map(int, value.split(".")))
            ):
                verify_version(root, state, version)
                users = [
                    target
                    for target, row in state["active"].items()
                    if row["version"] == version
                ]
                print(
                    version + (" active: " + ", ".join(users) if users else " retained")
                )
        else:
            if args.operation == "switch":
                if not args.selected_version or not VERSION.fullmatch(
                    args.selected_version
                ):
                    raise ValueError(
                        "Choose a stored version: switch MAJOR.MINOR.PATCH"
                    )
                selections = dict.fromkeys(targets, args.selected_version)
            else:
                selections = {}
                for target in targets:
                    previous = state["active"].get(target, {}).get("previous")
                    if not previous:
                        raise ValueError("No previous version for " + target)
                    selections[target] = previous
            activate(home, root, state, selections)
        return 0
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile) as error:
        print("Installation stopped: " + str(error), file=sys.stderr)
        return 1
    finally:
        if acquired:
            try:
                lock.unlink()
            except OSError as error:
                print(
                    "Lock cleanup deferred at " + str(lock) + ": " + str(error),
                    file=sys.stderr,
                )


if __name__ == "__main__":
    raise SystemExit(main())
