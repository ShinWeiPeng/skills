#!/usr/bin/env python3
"""Release the doc-coauthoring package without touching sibling package state."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

NAME = "doc-coauthoring"
MANIFESTS = ["package.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json"]
SECTIONS = ["Breaking Changes", "Added", "Changed", "Fixed"]
FILES = {"README.md", "UPSTREAM.md", "NOTICE", "LICENSE", *MANIFESTS[1:]}


def read(root, relative):
    return json.loads((root / relative).read_text(encoding="utf-8"))


def write(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def guarded_path(root, path):
    """Reject redirected descendants and verify the resolved package boundary."""
    root = root.resolve()
    relative = path.absolute().relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink() or (
            current.exists()
            and getattr(current.lstat(), "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)
        ):
            raise ValueError("redirected package path: " + str(current))
    path.resolve().relative_to(root)
    return path


def yaml_mapping(text, label):
    try:
        import yaml
    except ImportError as error:
        raise ValueError(
            "release checks require PyYAML; install requirements-release.txt"
        ) from error
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise ValueError("invalid YAML in " + label) from error
    if not isinstance(value, dict):
        raise ValueError(label + " must be a YAML mapping")
    return value


def tracked(root):
    git_root = Path(
        subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"], text=True
        ).strip()
    ).resolve()
    prefix = root.relative_to(git_root)
    result = subprocess.check_output(
        [
            "git",
            "-C",
            str(git_root),
            "ls-files",
            "--cached",
            "--full-name",
            "-z",
            "--",
            prefix.as_posix(),
        ]
    )
    files = []
    for item in result.split(b"\0"):
        if not item:
            continue
        relative = Path(item.decode("utf-8")).relative_to(prefix).as_posix()
        if relative in FILES or relative.startswith("skills/"):
            path = guarded_path(root, root / relative)
            if not path.is_file() or path.is_symlink():
                raise ValueError(
                    "tracked package source is absent or redirected: " + relative
                )
            files.append(relative)
    required = FILES | {
        "skills/doc-coauthoring/SKILL.md",
        "skills/doc-coauthoring/agents/openai.yaml",
        "skills/doc-coauthoring/references/codex.md",
        "skills/doc-coauthoring/references/claude.md",
    }
    if not required.issubset(files):
        raise ValueError(
            "package inventory is incomplete: " + str(sorted(required - set(files)))
        )
    return sorted(files)


def canonical_bytes(path):
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
    except UnicodeDecodeError:
        return raw


def fingerprint(root):
    digest = hashlib.sha256()
    for relative in tracked(root):
        content = canonical_bytes(root / relative)
        if relative in MANIFESTS:
            value = json.loads(content)
            value.pop("version", None)
            content = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        digest.update(relative.encode() + b"\0" + content + b"\0")
    return "sha256:" + digest.hexdigest()


def pending(root):
    changesets = {}
    for path in sorted((root / ".changeset").glob("*.md")):
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path.stem):
            raise ValueError("invalid changeset ID")
        match = re.fullmatch(
            r'---\s*\n"doc-coauthoring": (patch|minor|major)\n---\n[\s\S]+',
            path.read_text(encoding="utf-8"),
        )
        if not match:
            raise ValueError("invalid doc-coauthoring changeset: " + path.name)
        changesets[path.stem] = match.group(1)
    return changesets


def check(root):
    versions = [read(root, path)["version"] for path in MANIFESTS]
    if len(set(versions)) != 1 or not re.fullmatch(
        r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", versions[0]
    ):
        raise ValueError(
            "both harness manifests and package.json must share one stable version"
        )
    for path in MANIFESTS:
        if read(root, path)["name"] != NAME:
            raise ValueError("package identity changed")
    if read(root, MANIFESTS[1])["skills"] != "./skills/" or read(root, MANIFESTS[2])[
        "skills"
    ] != ["./skills/doc-coauthoring"]:
        raise ValueError("harnesses must reference the shared skill source")
    skill = (root / "skills/doc-coauthoring/SKILL.md").read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill, re.DOTALL)
    if not frontmatter:
        raise ValueError("shared SKILL.md requires YAML frontmatter")
    metadata = yaml_mapping(frontmatter[1], "SKILL.md frontmatter")
    if (
        metadata.get("name") != NAME
        or not isinstance(metadata.get("description"), str)
        or not metadata["description"].strip()
        or len(metadata["description"]) > 1024
    ):
        raise ValueError("shared SKILL.md requires valid name and description")
    agent = yaml_mapping(
        (root / "skills/doc-coauthoring/agents/openai.yaml").read_text(
            encoding="utf-8"
        ),
        "agents/openai.yaml",
    )
    interface = agent.get("interface", {})
    if (
        not isinstance(interface, dict)
        or not all(
            isinstance(interface.get(key), str) and interface[key].strip()
            for key in ["display_name", "short_description", "default_prompt"]
        )
        or not 25 <= len(interface["short_description"]) <= 64
        or "$doc-coauthoring" not in interface["default_prompt"]
    ):
        raise ValueError("invalid Codex skill interface metadata")
    for relative in tracked(root):
        if not relative.endswith(".md"):
            continue
        source = root / relative
        for link in re.findall(
            r"\[[^\]]*\]\(([^)\s]+)\)", source.read_text(encoding="utf-8")
        ):
            if ":" in link or link.startswith("#"):
                continue
            target = (source.parent / link.split("#")[0]).resolve()
            target.relative_to(root)
            if not target.exists():
                raise ValueError("missing local document reference: " + link)
    state = read(root, ".changeset/release-state.json")
    if state["schema_version"] != 1 or state["current_version"] != versions[0]:
        raise ValueError("formal version differs from release state")
    production = fingerprint(root)
    changesets = pending(root)
    intent_path = root / ".changeset/release-intent.json"
    if intent_path.exists():
        intent = read(root, ".changeset/release-intent.json")
        if set(intent) != {"bump", "changesets", "summary"} or not changesets:
            raise ValueError("release intent requires pending changesets")
        if (
            not isinstance(intent["changesets"], list)
            or len(intent["changesets"]) != len(set(intent["changesets"]))
            or set(intent["changesets"]) != set(changesets)
        ):
            raise ValueError(
                "release intent must consume exactly the pending package changesets"
            )
        ranks = {"patch": 0, "minor": 1, "major": 2}
        if intent["bump"] != max(changesets.values(), key=ranks.get):
            raise ValueError("intent bump must match highest pending changeset")
        summary = intent["summary"]
        if (
            not isinstance(summary, dict)
            or set(summary) != set(SECTIONS)
            or not all(
                isinstance(items, list)
                and all(isinstance(item, str) and item.strip() for item in items)
                for items in summary.values()
            )
            or not any(summary.values())
        ):
            raise ValueError("release summary requires the four changelog sections")
    elif changesets or state["production_fingerprint"] != production:
        raise ValueError(
            "changed production or pending changesets require a release intent"
        )
    if versions[0] != "0.0.0" and ("## " + versions[0] + "\n") not in (
        root / "CHANGELOG.md"
    ).read_text(encoding="utf-8"):
        raise ValueError("current version has no changelog entry")
    return {"version": versions[0], "fingerprint": production}


def apply_intent(root):
    identity = check(root)
    if not (root / ".changeset/release-intent.json").exists():
        return False
    intent = read(root, ".changeset/release-intent.json")
    numbers = [int(part) for part in identity["version"].split(".")]
    index = {"major": 0, "minor": 1, "patch": 2}[intent["bump"]]
    numbers[index] += 1
    numbers[index + 1 :] = [0] * (2 - index)
    version = ".".join(map(str, numbers))
    destination = root / ".changeset/applied" / version
    if destination.exists():
        raise ValueError("refusing to overwrite existing release history")
    for path in MANIFESTS:
        manifest = read(root, path)
        manifest["version"] = version
        write(root, path, manifest)
    destination.mkdir(parents=True)
    for name in intent["changesets"]:
        (root / ".changeset" / (name + ".md")).rename(destination / (name + ".md"))
    changelog = (
        "## "
        + version
        + "\n\n"
        + "".join(
            "### "
            + section
            + "\n\n"
            + "".join("- " + item + "\n" for item in intent["summary"][section])
            + "\n"
            for section in SECTIONS
        )
    )
    old = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n" + changelog + old.removeprefix("# Changelog\n").lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    write(
        root,
        ".changeset/release-state.json",
        {
            "schema_version": 1,
            "current_version": version,
            "previous_version": identity["version"],
            "production_fingerprint": identity["fingerprint"],
            "applied_changesets": intent["changesets"],
        },
    )
    (root / ".changeset/release-intent.json").unlink()
    return True


def tree_fingerprint(root):
    digest = hashlib.sha256()
    for path in sorted(
        root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()
    ):
        guarded_path(root, path)
        if path.is_file():
            digest.update(
                path.relative_to(root).as_posix().encode()
                + b"\0"
                + path.read_bytes()
                + b"\0"
            )
    return "sha256:" + digest.hexdigest()


def replace_generated(root, stage, destination):
    # Verify both resolved paths immediately before replacement or recursive removal.
    guarded_path(root, stage).resolve().relative_to(root / "dist")
    guarded_path(root, destination).resolve().relative_to(root / "dist")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if (
            destination.is_symlink()
            or not (destination / ".generated-doc-coauthoring").is_file()
        ):
            raise ValueError("refusing to replace an unrelated output directory")
        shutil.rmtree(guarded_path(root, destination))
    guarded_path(root, stage).replace(guarded_path(root, destination))


def assemble(
    root,
    *,
    source_commit="none:working-tree",
    source_tag_commit=None,
    previous_publication_commit="none:first-publication",
):
    identity = check(root)
    dist = guarded_path(root, root / "dist")
    dist.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".doc-coauthoring-stage-", dir=dist
    ) as temporary:
        staging = Path(temporary)
        artifact = staging / NAME
        artifact.mkdir()
        for relative in tracked(root):
            destination = artifact / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(canonical_bytes(root / relative))
        (artifact / ".generated-doc-coauthoring").write_text(
            "Generated by scripts/release.py\n", encoding="utf-8", newline="\n"
        )
        publication = staging / (NAME + "-release")
        plugin = publication / "plugins" / NAME
        plugin.parent.mkdir(parents=True)
        shutil.copytree(artifact, plugin)
        entry = {
            "name": NAME,
            "source": {"source": "local", "path": "./plugins/" + NAME},
        }
        write(
            publication,
            ".agents/plugins/marketplace.json",
            {
                "name": NAME,
                "interface": {"displayName": "Doc Coauthoring"},
                "plugins": [entry],
            },
        )
        write(
            publication,
            ".claude-plugin/marketplace.json",
            {
                "name": NAME,
                "owner": {"name": "ShinWeiPeng"},
                "plugins": [
                    {
                        "name": NAME,
                        "source": "./plugins/" + NAME,
                        "description": "Three-stage document coauthoring for Codex and Claude.",
                    }
                ],
            },
        )
        payload = {
            "source_commit": source_commit,
            "source_tag": NAME + "@" + identity["version"],
            "source_tag_commit": source_tag_commit or source_commit,
            "rollback": {"previous_publication_commit": previous_publication_commit},
            "artifact": {
                "plugin_name": NAME,
                "version": identity["version"],
                "production_fingerprint": identity["fingerprint"],
                "content_fingerprint": tree_fingerprint(artifact),
            },
        }
        write(publication, "publication-record.json", payload)
        (publication / ".generated-doc-coauthoring").write_text(
            "Generated publication\n", encoding="utf-8", newline="\n"
        )
        replace_generated(root, artifact, dist / NAME)
        replace_generated(root, publication, dist / (NAME + "-release"))
    return payload


def validate(root):
    check(root)
    artifact = guarded_path(root, root / "dist" / NAME)
    expected_paths = set(tracked(root)) | {".generated-doc-coauthoring"}
    actual_paths = {
        p.relative_to(artifact).as_posix() for p in artifact.rglob("*") if p.is_file()
    }
    if expected_paths != actual_paths or any(
        (artifact / path).is_symlink()
        or (artifact / path).read_bytes() != canonical_bytes(root / path)
        for path in expected_paths - {".generated-doc-coauthoring"}
    ):
        raise ValueError("artifact differs from authoritative tracked sources")
    publication = guarded_path(root, root / "dist" / (NAME + "-release"))
    payload = read(publication, "publication-record.json")
    identity = check(root)
    expected = {
        "plugin_name": NAME,
        "version": identity["version"],
        "production_fingerprint": identity["fingerprint"],
        "content_fingerprint": tree_fingerprint(artifact),
    }
    if (
        payload["artifact"] != expected
        or tree_fingerprint(publication / "plugins" / NAME)
        != expected["content_fingerprint"]
    ):
        raise ValueError("publication differs from assembled package")
    if (
        read(publication, ".agents/plugins/marketplace.json")["plugins"][0]["source"][
            "path"
        ]
        != "./plugins/" + NAME
        or read(publication, ".claude-plugin/marketplace.json")["plugins"][0]["source"]
        != "./plugins/" + NAME
    ):
        raise ValueError("publication marketplace reference is invalid")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=["check", "fingerprint", "apply-intent", "assemble", "validate"],
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--source-commit", default="none:working-tree")
    parser.add_argument("--source-tag-commit")
    parser.add_argument(
        "--previous-publication-commit", default="none:first-publication"
    )
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.operation == "fingerprint":
            print(fingerprint(root))
            return 0
        if args.operation == "apply-intent":
            result = {"changed": apply_intent(root)}
        elif args.operation == "assemble":
            result = assemble(
                root,
                source_commit=args.source_commit,
                source_tag_commit=args.source_tag_commit,
                previous_publication_commit=args.previous_publication_commit,
            )
        else:
            result = {"check": check, "validate": validate}[args.operation](root)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (
        ValueError,
        KeyError,
        OSError,
        TypeError,
        subprocess.CalledProcessError,
    ) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
