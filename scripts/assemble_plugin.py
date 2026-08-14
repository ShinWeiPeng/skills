#!/usr/bin/env python3
"""Assemble and verify the governed plugin from repository-owned skill sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PLUGIN_NAME = "governed-engineering-skills"
MARKETPLACE_NAME = "governed-engineering"
DEVELOPMENT_MARKETPLACE_NAME = "governed-engineering-development"
SHELL_PATH = Path("plugins") / PLUGIN_NAME
PROMOTED_BUCKETS = (Path("skills/engineering"), Path("skills/productivity"))
INVENTORY_NAME = "artifact-inventory.json"
MARKETPLACE_BRANCH = "marketplace-release"
MARKETPLACE_REPOSITORY = "https://github.com/ShinWeiPeng/skills.git"
MARKETPLACE_PATH = ".agents/plugins/marketplace.json"
MARKETPLACE_SPARSE_PATHS = (".agents/plugins", f"plugins/{PLUGIN_NAME}")
PUBLICATION_RECORD_NAME = "publication-record.json"


class DistributionError(RuntimeError):
    """The assembled plugin does not match its authoritative repository inputs."""


def classify_invocation_mode(
    skill_text: str,
    openai_metadata: str,
    *,
    skill_name: str,
) -> str:
    """Validate and classify the cross-host invocation metadata contract."""
    parts = skill_text.split("---", 2)
    frontmatter = parts[1] if len(parts) == 3 else ""
    claude_manual = re.search(
        r"(?m)^disable-model-invocation:\s*true\s*$",
        frontmatter,
    ) is not None
    codex_manual = re.search(
        r"(?m)^\s*allow_implicit_invocation:\s*false\s*$",
        openai_metadata,
    ) is not None
    codex_redundant_true = re.search(
        r"(?m)^\s*allow_implicit_invocation:\s*true\s*$",
        openai_metadata,
    ) is not None
    if codex_redundant_true:
        raise DistributionError(
            f"automatic skill must omit allow_implicit_invocation: true: {skill_name}"
        )
    if claude_manual != codex_manual:
        raise DistributionError(
            f"manual invocation metadata disagrees across hosts: {skill_name}"
        )
    return "manual" if claude_manual else "automatic"


def strip_claude_invocation_frontmatter(skill_text: str) -> str:
    """Remove Claude-only invocation metadata without changing Skill body text."""
    parts = skill_text.split("---", 2)
    if len(parts) != 3 or parts[0] != "":
        raise DistributionError("SKILL.md is missing leading YAML frontmatter")
    frontmatter = "".join(
        line
        for line in parts[1].splitlines(keepends=True)
        if line.strip() != "disable-model-invocation: true"
    )
    return "---" + frontmatter + "---" + parts[2]


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repository_files(repo_root: Path, relative_root: Path) -> list[Path]:
    completed = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            relative_root.as_posix(),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise DistributionError(completed.stderr.strip() or "unable to inventory repository files")
    prefix = relative_root.as_posix().rstrip("/") + "/"
    paths: list[Path] = []
    for line in completed.stdout.splitlines():
        normalized = line.replace("\\", "/")
        if not normalized.startswith(prefix):
            continue
        relative = Path(normalized)
        source = repo_root / relative
        if source.is_file() and "__pycache__" not in relative.parts and source.suffix != ".pyc":
            paths.append(relative)
    return sorted(paths, key=lambda item: item.as_posix())


def promoted_skills(repo_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for bucket in PROMOTED_BUCKETS:
        root = repo_root / bucket
        for skill in sorted((path for path in root.iterdir() if path.is_dir()), key=lambda item: item.name):
            if skill.name in result:
                raise DistributionError(f"duplicate promoted skill name: {skill.name}")
            if not (skill / "SKILL.md").is_file():
                raise DistributionError(f"promoted skill is missing SKILL.md: {skill.relative_to(repo_root)}")
            result[skill.name] = skill
    return result


def _copy_repository_tree(repo_root: Path, relative_root: Path, destination: Path) -> None:
    for relative in _repository_files(repo_root, relative_root):
        within_root = relative.relative_to(relative_root)
        if within_root.parts and within_root.parts[0] == "skills":
            continue
        target = destination / within_root
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_root / relative, target)


def _copy_skill(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "validation-evidence.md"),
    )
    skill_file = destination / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    normalized = strip_claude_invocation_frontmatter(text)
    skill_file.write_text(normalized, encoding="utf-8", newline="")


def _assert_replaceable_output(repo_root: Path, output: Path) -> None:
    if output == repo_root or output in repo_root.parents:
        raise DistributionError("artifact output cannot be the repository or one of its ancestors")
    if not output.exists():
        return
    if output.is_dir() and not any(output.iterdir()):
        return
    inventory_path = output / INVENTORY_NAME
    try:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DistributionError(
            "refusing to replace an existing directory without a valid Plugin artifact identity"
        ) from exc
    if inventory.get("plugin_name") != PLUGIN_NAME:
        raise DistributionError("refusing to replace an existing directory owned by another artifact")


def _inventory(artifact: Path) -> dict[str, object]:
    manifest_path = artifact / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = []
    for path in sorted((item for item in artifact.rglob("*") if item.is_file()), key=lambda item: item.relative_to(artifact).as_posix()):
        relative = path.relative_to(artifact).as_posix()
        if relative == INVENTORY_NAME:
            continue
        files.append({"path": relative, "sha256": _sha256(path), "size": path.stat().st_size})
    identity = {
        "schema_version": "1.0.0",
        "plugin_name": manifest["name"],
        "version": manifest["version"],
        "files": files,
    }
    identity["content_fingerprint"] = "sha256:" + hashlib.sha256(_json_bytes(identity)).hexdigest()
    return identity


def _synchronize_release_state_fingerprint(artifact: Path) -> None:
    version_tool = artifact / "scripts" / "version_governance.py"
    completed = subprocess.run(
        [sys.executable, str(version_tool), "sync-fingerprint"],
        cwd=artifact,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise DistributionError(
            f"unable to synchronize assembled Plugin release state: {detail}"
        )


def _normalize_windows_inherited_acl(staging: Path) -> None:
    """Prevent a sandbox-created staging ACL from becoming the user's final artifact ACL."""
    if sys.platform != "win32":
        return
    commands = (
        ["icacls.exe", str(staging), "/inheritance:e", "/T", "/C", "/Q", "/L"],
        ["icacls.exe", str(staging), "/reset", "/T", "/C", "/Q", "/L"],
    )
    for command in commands:
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise DistributionError(
                "unable to normalize inherited Windows access on the staged Plugin"
                + (f": {detail}" if detail else "")
            )


def assemble(repo_root: Path, output: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    output = output.resolve()
    shell = repo_root / SHELL_PATH
    if not shell.is_dir():
        raise DistributionError(f"plugin shell is missing: {shell}")
    if (shell / "skills").exists():
        raise DistributionError("tracked plugin shell must not contain a skills tree")
    skills = promoted_skills(repo_root)
    for name, source in skills.items():
        classify_invocation_mode(
            (source / "SKILL.md").read_text(encoding="utf-8"),
            (source / "agents" / "openai.yaml").read_text(encoding="utf-8"),
            skill_name=name,
        )
    _assert_replaceable_output(repo_root, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}-staging-", dir=output.parent)
    )
    try:
        _copy_repository_tree(repo_root, SHELL_PATH, staging)
        for name, source in skills.items():
            _copy_skill(source, staging / "skills" / name)
        _synchronize_release_state_fingerprint(staging)
        result = _inventory(staging)
        (staging / INVENTORY_NAME).write_bytes(_json_bytes(result))
        _normalize_windows_inherited_acl(staging)
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
        return result
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def validate_artifact(repo_root: Path, artifact: Path) -> dict[str, object]:
    artifact = artifact.resolve()
    inventory_path = artifact / INVENTORY_NAME
    if not inventory_path.is_file():
        raise DistributionError(f"artifact is missing {INVENTORY_NAME}")
    declared = json.loads(inventory_path.read_text(encoding="utf-8"))
    actual = _inventory(artifact)
    if declared != actual:
        raise DistributionError("artifact inventory or content fingerprint does not match its files")
    with tempfile.TemporaryDirectory(prefix="governed-plugin-") as temporary:
        expected_path = Path(temporary) / PLUGIN_NAME
        expected = assemble(repo_root, expected_path)
        if expected != actual:
            raise DistributionError("artifact differs from authoritative repository sources")
    return actual


def localize_artifact(
    repo_root: Path,
    artifact: Path,
    *,
    cachebuster: str | None = None,
) -> dict[str, object]:
    """Add one local-only Codex cachebuster to an inventory-valid formal artifact."""
    inventory_path = artifact / INVENTORY_NAME
    if not inventory_path.is_file():
        raise DistributionError(f"artifact is missing {INVENTORY_NAME}")
    declared = json.loads(inventory_path.read_text(encoding="utf-8"))
    if declared != _inventory(artifact):
        raise DistributionError("artifact inventory or content fingerprint does not match its files")
    manifest_path = artifact / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    formal_version = str(manifest.get("version", "")).split("+", 1)[0]
    token = cachebuster or datetime.now(timezone.utc).strftime("local-%Y%m%d%H%M%S%f")
    token = re.sub(r"[^a-z0-9-]+", "-", token.strip().lower()).strip("-")
    if not formal_version or not token:
        raise DistributionError("local cachebuster requires a formal version and non-empty token")
    manifest["version"] = f"{formal_version}+codex.{token}"
    manifest_path.write_bytes(_json_bytes(manifest))
    _synchronize_release_state_fingerprint(artifact)
    result = _inventory(artifact)
    (artifact / INVENTORY_NAME).write_bytes(_json_bytes(result))
    return result


def _tree_fingerprint(root: Path) -> str:
    files = []
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix()
        if relative == PUBLICATION_RECORD_NAME:
            continue
        files.append({"path": relative, "sha256": _sha256(path), "size": path.stat().st_size})
    return "sha256:" + hashlib.sha256(_json_bytes(files)).hexdigest()


def _assert_replaceable_publication_output(output: Path) -> None:
    if not output.exists():
        return
    record = output / PUBLICATION_RECORD_NAME
    try:
        payload = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DistributionError(
            "refusing to replace an existing directory without a personal Marketplace publication identity"
        ) from exc
    expected_identity = {
        "channel": "personal-git-marketplace",
        "repository_url": MARKETPLACE_REPOSITORY,
        "git_ref": MARKETPLACE_BRANCH,
    }
    if any(payload.get(field) != value for field, value in expected_identity.items()):
        raise DistributionError("refusing to replace an existing directory owned by another publication")
    artifact = payload.get("artifact")
    if not isinstance(artifact, dict) or artifact.get("name") != PLUGIN_NAME:
        raise DistributionError("refusing to replace an existing directory owned by another publication")


def write_marketplace_publication(
    repo_root: Path,
    artifact: Path,
    result: dict[str, object],
    output: Path,
    *,
    source_commit: str,
    previous_publication_commit: str,
) -> Path:
    output = output.resolve()
    if output == repo_root.resolve() or output in repo_root.resolve().parents:
        raise DistributionError("Marketplace output cannot be the repository or one of its ancestors")
    _assert_replaceable_publication_output(output)
    if output.exists():
        shutil.rmtree(output)
    plugin_destination = output / "plugins" / PLUGIN_NAME
    plugin_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(artifact, plugin_destination)

    catalog = json.loads((repo_root / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
    plugins = catalog.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1 or plugins[0].get("name") != PLUGIN_NAME:
        raise DistributionError("personal Marketplace catalog must contain exactly the governed Plugin")
    catalog["name"] = MARKETPLACE_NAME
    plugins[0]["source"] = {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"}
    catalog_path = output / MARKETPLACE_PATH
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_bytes(_json_bytes(catalog))

    record = output / PUBLICATION_RECORD_NAME
    payload = {
        "schema_version": "1.0.0",
        "channel": "personal-git-marketplace",
        "repository_url": MARKETPLACE_REPOSITORY,
        "git_ref": MARKETPLACE_BRANCH,
        "source_commit": source_commit,
        "source_tag": f"{PLUGIN_NAME}@{result['version']}",
        "marketplace_path": MARKETPLACE_PATH,
        "sparse_paths": list(MARKETPLACE_SPARSE_PATHS),
        "artifact": {
            "name": result["plugin_name"],
            "version": result["version"],
            "content_fingerprint": result["content_fingerprint"],
            "inventory": f"plugins/{PLUGIN_NAME}/{INVENTORY_NAME}",
        },
        "tree_fingerprint": _tree_fingerprint(output),
        "installation_steps": [
            f"Add {MARKETPLACE_REPOSITORY} as a personal Git Marketplace",
            f"Use Git reference {MARKETPLACE_BRANCH}",
            f"Use sparse paths {', '.join(MARKETPLACE_SPARSE_PATHS)}",
            "Install the governed Plugin in Codex Desktop or Codex CLI",
        ],
        "rollback": {
            "method": f"Restore {MARKETPLACE_BRANCH} to the previous validated generated commit",
            "previous_publication_commit": previous_publication_commit,
        },
        "evidence_checklist": [
            "Codex resolves the expected Plugin name, version, Git reference, and fingerprint",
            "Codex Desktop or CLI invokes one representative engineering Skill",
            "Codex Desktop or CLI invokes one representative productivity Skill",
        ],
    }
    record.write_bytes(_json_bytes(payload))
    return record


def _validate_schema(value: object, schema: dict[str, object], path: str = "handoff") -> None:
    expected_type = schema.get("type")
    type_map = {"object": dict, "array": list, "string": str, "boolean": bool}
    if expected_type in type_map and not isinstance(value, type_map[expected_type]):
        raise DistributionError(f"{path} must be {expected_type}")
    if "const" in schema and value != schema["const"]:
        raise DistributionError(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise DistributionError(f"{path} has an unsupported value")
    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            raise DistributionError(f"{path} is too short")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.fullmatch(pattern, value):
            raise DistributionError(f"{path} does not match its required pattern")
    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            raise DistributionError(f"{path} does not contain enough items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema(item, item_schema, f"{path}[{index}]")
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [name for name in required if name not in value]
        if missing:
            raise DistributionError(f"{path} is missing required fields: {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise DistributionError(f"{path} has unsupported fields: {extra}")
        for name, child_schema in properties.items():
            if name in value and isinstance(child_schema, dict):
                _validate_schema(value[name], child_schema, f"{path}.{name}")


def validate_marketplace_publication(
    publication_root: Path,
    payload: dict[str, object],
    schema: dict[str, object],
) -> None:
    _validate_schema(payload, schema)
    if payload["sparse_paths"] != list(MARKETPLACE_SPARSE_PATHS):
        raise DistributionError("Marketplace sparse paths do not match the supported consumer tree")
    catalog_path = publication_root / MARKETPLACE_PATH
    plugin_path = publication_root / "plugins" / PLUGIN_NAME
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        inventory = json.loads((plugin_path / INVENTORY_NAME).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DistributionError(f"Marketplace publication tree is incomplete: {exc}") from exc
    plugins = catalog.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        raise DistributionError("Marketplace catalog must contain exactly one Plugin")
    entry = plugins[0]
    if entry.get("name") != PLUGIN_NAME or entry.get("source") != {
        "source": "local",
        "path": f"./plugins/{PLUGIN_NAME}",
    }:
        raise DistributionError("Marketplace catalog does not resolve the generated Plugin tree")
    expected_artifact = {
        "name": inventory.get("plugin_name"),
        "version": inventory.get("version"),
        "content_fingerprint": inventory.get("content_fingerprint"),
        "inventory": f"plugins/{PLUGIN_NAME}/{INVENTORY_NAME}",
    }
    if payload["artifact"] != expected_artifact:
        raise DistributionError("Marketplace publication identity does not match the Plugin inventory")
    if _inventory(plugin_path) != inventory:
        raise DistributionError("Marketplace Plugin files do not match their inventory")
    if payload["tree_fingerprint"] != _tree_fingerprint(publication_root):
        raise DistributionError("Marketplace publication tree fingerprint does not match its files")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("assemble", "validate", "localize"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--marketplace-publication", action="store_true")
    parser.add_argument("--marketplace-output", type=Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--previous-publication-commit", default="none:first-publication")
    parser.add_argument("--cachebuster")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    artifact = (args.output or args.artifact or repo_root / "dist" / PLUGIN_NAME).resolve()
    try:
        if args.command == "assemble":
            result = assemble(repo_root, artifact)
            if args.marketplace_publication:
                source_commit = args.source_commit
                if not source_commit:
                    completed = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=repo_root,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    source_commit = completed.stdout.strip()
                publication_root = (
                    args.marketplace_output or repo_root / "dist" / MARKETPLACE_BRANCH
                ).resolve()
                record = write_marketplace_publication(
                    repo_root,
                    artifact,
                    result,
                    publication_root,
                    source_commit=source_commit,
                    previous_publication_commit=args.previous_publication_commit,
                )
                schema = json.loads(
                    (repo_root / "distribution" / "personal-marketplace-publication.schema.json").read_text(
                        encoding="utf-8"
                    )
                )
                validate_marketplace_publication(publication_root, json.loads(record.read_text(encoding="utf-8")), schema)
        elif args.command == "validate":
            result = validate_artifact(repo_root, artifact)
        else:
            result = localize_artifact(
                repo_root,
                artifact,
                cachebuster=args.cachebuster,
            )
    except (DistributionError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(
        json.dumps(
            {
                "plugin_name": result["plugin_name"],
                "version": result["version"],
                "content_fingerprint": result["content_fingerprint"],
                "file_count": len(result["files"]),
                "artifact": str(artifact),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
