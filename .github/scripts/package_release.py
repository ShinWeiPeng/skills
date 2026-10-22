#!/usr/bin/env python3
"""Select, version and publish independently reviewed packages in one repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


def git(root, *arguments, input=None, env=None, check=True):
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        input=input,
        env=env,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def select_packages(paths, packages):
    selected = set()
    for raw in paths:
        path = raw.replace("\\", "/")
        if path in {
            "README.md",
            "LICENSE",
            "AGENTS.md",
            "CLAUDE.md",
        } or path.startswith(("specs/", "artifacts/", "spec-governance/")):
            continue
        owners = [
            name
            for name, package in packages.items()
            if path.startswith(package["root"].rstrip("/") + "/")
        ]
        selected.update(owners or packages)
    return [name for name in packages if name in selected]


def assert_package_scope(package_root, paths):
    prefix = package_root.rstrip("/") + "/"
    for path in paths:
        if not path.startswith(prefix) or ".." in PurePosixPath(path).parts:
            raise ValueError(
                "version operation changed a path outside its package: " + path
            )


def compare_release_identity(current, tagged):
    if tagged is None:
        return "create"
    if current != tagged:
        raise ValueError(
            "existing release tag has a different package version or fingerprint"
        )
    return "existing"


def load_packages(root):
    document = json.loads((root / "release-packages.json").read_text(encoding="utf-8"))
    if document.get("schema_version") != 1 or not document.get("packages"):
        raise ValueError("invalid release package registry")
    packages = document["packages"]
    for name, package in packages.items():
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            raise ValueError("invalid package name")
        for key in ("root", "version_file", "state_file", "publication_dir"):
            relative = package[key]
            if (
                PurePosixPath(relative).is_absolute()
                or ".." in PurePosixPath(relative).parts
            ):
                raise ValueError("package path escapes repository")
            (root / relative).resolve().relative_to(root.resolve())
        for key in ("version_branch", "publication_branch"):
            branch = package[key]
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", branch) or any(
                x in branch for x in ("..", "//", "@{")
            ):
                raise ValueError("invalid release branch")
        if package["version_branch"] == package["publication_branch"]:
            raise ValueError("version and publication branches must differ")
    branches = [
        p[k]
        for p in packages.values()
        for k in ("version_branch", "publication_branch")
    ]
    if len(branches) != len(set(branches)):
        raise ValueError("packages share a mutable release branch")
    return packages


def command(root, arguments):
    argv = [
        sys.executable if part == "python" and index == 0 else part
        for index, part in enumerate(arguments)
    ]
    return subprocess.run(
        argv, cwd=root, capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout.strip()


def current_identity(root, package):
    version = json.loads((root / package["version_file"]).read_text(encoding="utf-8"))[
        "version"
    ]
    fingerprint = command(root, package["commands"]["fingerprint"])
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint):
        raise ValueError("fingerprint command did not return a release identity")
    return {"version": version, "fingerprint": fingerprint}


def tagged_identity(root, package, tag):
    if git(
        root, "show-ref", "--verify", "--quiet", "refs/tags/" + tag, check=False
    ).returncode:
        return None
    for path in [package["state_file"], *package.get("legacy_state_files", [])]:
        found = git(root, "show", tag + ":" + path, check=False)
        if found.returncode == 0:
            state = json.loads(found.stdout)
            return {
                "version": state["current_version"],
                "fingerprint": state["production_fingerprint"],
            }
    raise ValueError("existing tag has no inspectable package release state")


def remote_head(root, branch):
    lines = git(root, "ls-remote", "origin", "refs/heads/" + branch).stdout.strip()
    if not lines:
        return None
    return lines.split()[0]


def publish_directory(root, publication, branch, previous):
    """Publish with a private Git index and a lease, without touching source/index."""
    if remote_head(root, branch) != previous:
        raise ValueError("publication base changed; preserve the newer remote branch")
    publication = Path(publication).resolve()
    if not publication.is_dir() or not any(publication.iterdir()):
        raise ValueError("publication tree is empty")
    for path in publication.rglob("*"):
        if path.is_symlink() or ".git" in path.relative_to(publication).parts:
            raise ValueError("publication contains a redirected or Git control path")
    git_directory = git(root, "rev-parse", "--absolute-git-dir").stdout.strip()
    with tempfile.TemporaryDirectory(
        prefix=".package-publication-index-", dir=root
    ) as temporary:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / "index"))
        prefix = [
            "git",
            "--git-dir=" + git_directory,
            "--work-tree=" + str(publication),
        ]

        def operation(*args):
            return subprocess.run(
                [*prefix, *args],
                cwd=publication,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

        operation("read-tree", "--empty")
        operation("add", "--force", "--all")
        tree = operation("write-tree")
        if previous:
            git(root, "fetch", "--no-tags", "origin", "refs/heads/" + branch)
        env.setdefault("GIT_AUTHOR_NAME", "github-actions[bot]")
        env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
        env.setdefault(
            "GIT_AUTHOR_EMAIL", "41898282+github-actions[bot]@users.noreply.github.com"
        )
        env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])
        arguments = ["commit-tree", tree]
        if previous:
            arguments.extend(["-p", previous])
        commit = git(
            root, *arguments, input="Publish " + branch + "\n", env=env
        ).stdout.strip()
        git(
            root,
            "push",
            "--force-with-lease=refs/heads/" + branch + ":" + (previous or ""),
            "origin",
            commit + ":refs/heads/" + branch,
        )
        return commit


def update_version_pr(root, name, package):
    command(root, package["commands"]["check"])
    before = json.loads((root / package["version_file"]).read_text(encoding="utf-8"))[
        "version"
    ]
    command(root, package["commands"]["apply"])
    after = json.loads((root / package["version_file"]).read_text(encoding="utf-8"))[
        "version"
    ]
    if before == after:
        return False
    changed = git(root, "diff", "HEAD", "--name-only", "-z").stdout.split("\0")
    untracked = git(
        root, "ls-files", "--others", "--exclude-standard", "-z"
    ).stdout.split("\0")
    assert_package_scope(package["root"], [p for p in changed + untracked if p])
    branch = package["version_branch"]
    previous = remote_head(root, branch)
    git(root, "checkout", "-B", branch)
    git(root, "add", "--", package["root"])
    git(
        root,
        "-c",
        "user.name=github-actions[bot]",
        "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit",
        "-m",
        "chore: version " + name + " " + after,
    )
    git(
        root,
        "push",
        "--force-with-lease=refs/heads/" + branch + ":" + (previous or ""),
        "origin",
        "HEAD:refs/heads/" + branch,
    )
    query = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--base",
            "main",
            "--head",
            branch,
            "--json",
            "number",
        ],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    existing = json.loads(query.stdout)
    if len(existing) > 1:
        raise ValueError("multiple Version PRs use the same package branch")
    with tempfile.TemporaryDirectory(prefix="package-version-pr-") as temporary:
        body = Path(temporary) / "body.md"
        body.write_text(
            "Apply the reviewed release intent for **"
            + name
            + " "
            + after
            + "**.\n\nUpdates only this package's version, changelog, release state and consumed changesets. Publication runs after this Version PR is merged and package checks pass.\n",
            encoding="utf-8",
        )
        arguments = (
            ["gh", "pr", "edit", str(existing[0]["number"])]
            if existing
            else ["gh", "pr", "create", "--base", "main", "--head", branch]
        )
        subprocess.run(
            [
                *arguments,
                "--title",
                "chore: version " + name + " " + after,
                "--body-file",
                str(body),
            ],
            cwd=root,
            check=True,
        )
    return True


def publish_package(root, name, package):
    command(root, package["commands"]["check"])
    identity = current_identity(root, package)
    state = json.loads((root / package["state_file"]).read_text(encoding="utf-8"))
    if (
        state["current_version"] != identity["version"]
        or state["production_fingerprint"] != identity["fingerprint"]
    ):
        raise ValueError(
            "publication requires the reviewed version and production fingerprint"
        )
    tag = name + "@" + identity["version"]
    disposition = compare_release_identity(
        identity, tagged_identity(root, package, tag)
    )
    previous = remote_head(root, package["publication_branch"])
    old_payload = None
    if previous:
        git(
            root,
            "fetch",
            "--no-tags",
            "origin",
            "refs/heads/" + package["publication_branch"],
        )
        old_payload = json.loads(
            git(root, "show", previous + ":publication-record.json").stdout
        )
        published_version = tuple(
            map(int, old_payload["artifact"]["version"].split("."))
        )
        current_version = tuple(map(int, identity["version"].split(".")))
        if current_version < published_version:
            raise ValueError(
                "stale workflow cannot downgrade an already published package"
            )
    source = git(root, "rev-parse", "HEAD").stdout.strip()
    tag_commit = (
        git(root, "rev-parse", tag + "^{commit}").stdout.strip()
        if disposition == "existing"
        else source
    )
    context = {
        "{source_commit}": source,
        "{source_tag_commit}": tag_commit,
        "{previous_publication_commit}": previous or "none:first-publication",
    }
    for build in package["commands"]["build"]:
        command(root, [context.get(argument, argument) for argument in build])
    publication = root / package["publication_dir"]
    payload = json.loads(
        (publication / "publication-record.json").read_text(encoding="utf-8")
    )
    if (
        payload["artifact"]["version"] != identity["version"]
        or payload["source_tag_commit"] != tag_commit
        or payload["rollback"]["previous_publication_commit"]
        != context["{previous_publication_commit}"]
    ):
        raise ValueError(
            "publication metadata differs from the inspected source and previous release"
        )
    if (
        old_payload
        and old_payload["artifact"]["version"] == identity["version"]
        and old_payload["artifact"] != payload["artifact"]
    ):
        raise ValueError(
            "same published version cannot contain different artifact content"
        )
    if disposition == "create":
        git(root, "tag", tag)
    # An identical push is safe; also retries a local tag whose previous push failed.
    git(root, "push", "origin", "refs/tags/" + tag)
    if old_payload and old_payload["artifact"] == payload["artifact"]:
        return "unchanged"
    publish_directory(root, publication, package["publication_branch"], previous)
    return "published"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["detect", "version", "publish"])
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--package")
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    packages = load_packages(root)
    try:
        if args.operation == "detect":
            if not args.base or args.base == "0" * 40:
                selected = list(packages)
            else:
                git(root, "cat-file", "-e", args.base + "^{commit}")
                paths = git(
                    root,
                    "diff",
                    "--name-only",
                    "--no-renames",
                    "-z",
                    args.base,
                    args.head,
                ).stdout.split("\0")
                selected = select_packages([p for p in paths if p], packages)
            outputs = {
                name: "true" if name in selected else "false" for name in packages
            }
        else:
            package = packages[args.package]
            if args.operation == "version":
                outputs = {
                    "changed": str(
                        update_version_pr(root, args.package, package)
                    ).lower()
                }
            else:
                outputs = {"publication": publish_package(root, args.package, package)}
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as stream:
                stream.write(
                    "".join(key + "=" + value + "\n" for key, value in outputs.items())
                )
        print(json.dumps(outputs, sort_keys=True))
        return 0
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError):
            print((error.stdout or "") + (error.stderr or ""), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
