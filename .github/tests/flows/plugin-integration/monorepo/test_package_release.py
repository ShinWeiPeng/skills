"""Public contracts for independently released packages in one Git repository."""

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import sys
from unittest import mock
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SPEC = importlib.util.spec_from_file_location(
    "package_release", ROOT / ".github/scripts/package_release.py"
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class PackageSelectionTests(unittest.TestCase):
    def setUp(self):
        self.packages = {
            "engineering": {"root": "governed-engineering-skills"},
            "docs": {"root": "doc-coauthoring"},
        }

    def test_one_package_does_not_select_its_sibling(self):
        self.assertEqual(
            release.select_packages(
                ["doc-coauthoring/skills/doc-coauthoring/SKILL.md"], self.packages
            ),
            ["docs"],
        )
        self.assertEqual(
            release.select_packages(
                ["governed-engineering-skills/skills/engineering/tdd/SKILL.md"],
                self.packages,
            ),
            ["engineering"],
        )

    def test_shared_and_unknown_paths_are_conservative(self):
        for path in [
            ".github/workflows/release.yml",
            "release-packages.json",
            "unexpected.txt",
        ]:
            self.assertEqual(
                release.select_packages([path], self.packages), ["engineering", "docs"]
            )

    def test_navigation_docs_do_not_release_packages(self):
        self.assertEqual(
            release.select_packages(
                ["README.md", "specs/SPEC-0064-plan.md"], self.packages
            ),
            [],
        )

    def test_scope_rejects_sibling_and_prefix_confusion(self):
        release.assert_package_scope(
            "doc-coauthoring", ["doc-coauthoring/package.json"]
        )
        for path in [
            "doc-coauthoring-evil/package.json",
            "governed-engineering-skills/package.json",
            "../doc-coauthoring/package.json",
        ]:
            with self.assertRaises(ValueError):
                release.assert_package_scope("doc-coauthoring", [path])


class ImmutableReleaseTests(unittest.TestCase):
    def test_other_package_commit_does_not_invalidate_an_old_tag(self):
        current = {"version": "1.2.0", "fingerprint": "sha256:literal-release"}
        self.assertEqual(
            release.compare_release_identity(current, dict(current)), "existing"
        )

    def test_same_version_different_content_is_rejected(self):
        with self.assertRaises(ValueError):
            release.compare_release_identity(
                {"version": "1.2.0", "fingerprint": "new"},
                {"version": "1.2.0", "fingerprint": "old"},
            )

    def test_absent_tag_can_be_created_once(self):
        self.assertEqual(
            release.compare_release_identity(
                {"version": "1.2.0", "fingerprint": "known"}, None
            ),
            "create",
        )


class PublicationAdapterTests(unittest.TestCase):
    def git(self, root, *args):
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
        ).stdout.strip()

    def test_publication_preserves_main_index_and_rejects_stale_lease(self):
        with tempfile.TemporaryDirectory(
            prefix="package-contract-", dir=ROOT
        ) as temporary:
            root = Path(temporary) / "source"
            bare = Path(temporary) / "remote.git"
            root.mkdir()
            subprocess.run(
                [
                    "git",
                    "init",
                    "--bare",
                    "--initial-branch=main",
                    "--template=",
                    str(bare),
                ],
                check=True,
                capture_output=True,
            )
            self.git(root, "init", "--initial-branch=main", "--template=")
            self.git(root, "config", "user.name", "Contract Test")
            self.git(root, "config", "user.email", "test@example.invalid")
            (root / "main.txt").write_text("source stays intact\n")
            self.git(root, "add", "main.txt")
            self.git(root, "commit", "-m", "base")
            self.git(root, "remote", "add", "origin", str(bare))
            before_head = self.git(root, "rev-parse", "HEAD")
            before_index = self.git(root, "write-tree")
            publication = Path(temporary) / "publication"
            publication.mkdir()
            (publication / "manifest.json").write_text('{"version":"0.1.0"}')
            first = release.publish_directory(
                root, publication, "doc-coauthoring-release", None
            )
            self.assertEqual(self.git(root, "rev-parse", "HEAD"), before_head)
            self.assertEqual(self.git(root, "write-tree"), before_index)
            self.assertIn('"0.1.0"', self.git(root, "show", first + ":manifest.json"))
            (publication / "manifest.json").write_text('{"version":"0.2.0"}')
            second = release.publish_directory(
                root, publication, "doc-coauthoring-release", first
            )
            self.assertNotEqual(first, second)
            with self.assertRaises(ValueError):
                release.publish_directory(
                    root, publication, "doc-coauthoring-release", first
                )
            self.assertEqual(
                self.git(
                    root, "ls-remote", "origin", "refs/heads/doc-coauthoring-release"
                ).split()[0],
                second,
            )


class PackageLauncherTests(unittest.TestCase):
    def test_package_launcher_preserves_arguments_and_exit_status(self):
        with tempfile.TemporaryDirectory(
            prefix="launcher contract ", dir=ROOT
        ) as directory:
            root = Path(directory)
            package = root / "governed-engineering-skills"
            package.mkdir()
            scripts = package / "scripts"
            scripts.mkdir()
            if os.name == "nt":
                name = "Install Governed Engineering Skills.cmd"
                launcher = package / name
                shutil.copyfile(ROOT / "governed-engineering-skills" / name, launcher)
                (scripts / "install-marketplace.ps1").write_text(
                    "param([string]$Marker, [string]$Words)\n"
                    'Write-Output "[$Marker]"\n'
                    'Write-Output "[$Words]"\n'
                    "exit 23\n"
                )
                command = [
                    "cmd.exe",
                    "/d",
                    "/c",
                    "call",
                    str(launcher),
                    "marker",
                    "two words",
                ]
            else:
                name = "Install Governed Engineering Skills.sh"
                launcher = package / name
                shutil.copyfile(ROOT / "governed-engineering-skills" / name, launcher)
                child = scripts / "install-marketplace.sh"
                child.write_text('#!/bin/sh\nprintf "[%s]\\n" "$@"\nexit 23\n')
                child.chmod(0o755)
                command = ["sh", str(launcher), "marker", "two words"]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env=os.environ | {"GOVERNED_INSTALLER_NO_DELAY": "1"},
            )
            self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
            self.assertIn("[marker]", result.stdout)
            self.assertIn("[two words]", result.stdout)


if __name__ == "__main__":
    unittest.main()


class ReleaseRecoveryTests(unittest.TestCase):
    """Real Git refs with a minimal package-command fake and no GitHub writes."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix="release-recovery-", dir=ROOT
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "source"
        self.root.mkdir()
        remote = Path(self.temporary.name) / "remote.git"
        self.git("init", "--quiet", "--initial-branch=main", "--template=")
        subprocess.run(
            [
                "git",
                "init",
                "--bare",
                "--initial-branch=main",
                "--template=",
                str(remote),
            ],
            capture_output=True,
            check=True,
        )
        self.git("config", "user.name", "Release Contract")
        self.git("config", "user.email", "release@example.invalid")
        self.git("remote", "add", "origin", str(remote))
        (self.root / ".gitignore").write_text("output/\n")
        (self.root / "fixture-build.py").write_text(
            'import json,sys\nfrom pathlib import Path\np=Path("output");p.mkdir(exist_ok=True)\nv=json.loads(Path("package.json").read_text())["version"]\npayload={"artifact":{"version":v,"content_fingerprint":"content-"+v},"source_commit":sys.argv[1],"source_tag_commit":sys.argv[2],"rollback":{"previous_publication_commit":sys.argv[3]}}\n(p/"publication-record.json").write_text(json.dumps(payload))\n'
        )
        self.package = {
            "root": "sample",
            "version_file": "package.json",
            "state_file": "state.json",
            "publication_dir": "output",
            "publication_branch": "sample-release",
            "commands": {
                "check": ["python", "-c", "pass"],
                "fingerprint": ["python", "-c", "print('sha256:'+'a'*64)"],
                "build": [
                    [
                        "python",
                        "fixture-build.py",
                        "{source_commit}",
                        "{source_tag_commit}",
                        "{previous_publication_commit}",
                    ]
                ],
            },
        }
        self.version("0.1.0")

    def git(self, *args):
        return release.git(self.root, *args).stdout.strip()

    def version(self, value):
        (self.root / "package.json").write_text(json.dumps({"version": value}))
        (self.root / "state.json").write_text(
            json.dumps(
                {
                    "current_version": value,
                    "production_fingerprint": "sha256:" + "a" * 64,
                }
            )
        )
        self.git("add", "--all")
        self.git("commit", "-m", value)
        return self.git("rev-parse", "HEAD")

    def publish(self):
        return release.publish_package(self.root, "sample", self.package)

    def test_old_workflow_cannot_downgrade_and_rollback_records_actual_previous_sha(
        self,
    ):
        first_source = self.git("rev-parse", "HEAD")
        self.assertEqual(self.publish(), "published")
        first_publication = release.remote_head(self.root, "sample-release")
        first_tag = self.git("rev-parse", "sample@0.1.0")
        self.assertEqual(self.publish(), "unchanged")
        self.assertEqual(first_tag, self.git("rev-parse", "sample@0.1.0"))
        self.version("0.2.0")
        self.assertEqual(self.publish(), "published")
        latest = release.remote_head(self.root, "sample-release")
        record = json.loads(self.git("show", latest + ":publication-record.json"))
        self.assertEqual(
            record["rollback"]["previous_publication_commit"], first_publication
        )
        self.assertEqual(
            record["source_tag_commit"], self.git("rev-parse", "sample@0.2.0")
        )
        self.git("checkout", "--detach", first_source)
        with self.assertRaisesRegex(ValueError, "stale workflow"):
            self.publish()
        self.assertEqual(release.remote_head(self.root, "sample-release"), latest)

    def test_old_workflow_cannot_replace_a_newer_version_pr_branch(self):
        old_source = self.git("rev-parse", "HEAD")
        current = self.version("0.2.0")
        self.git(
            "push",
            "origin",
            "HEAD:refs/heads/main",
            "HEAD:refs/heads/plugin-release/sample",
        )
        self.git("checkout", "--detach", old_source)
        package = dict(self.package, version_branch="plugin-release/sample")
        with self.assertRaisesRegex(ValueError, "stale workflow"):
            release.update_version_pr(self.root, "sample", package)
        self.assertEqual(
            release.remote_head(self.root, "plugin-release/sample"), current
        )
        self.assertEqual(
            json.loads((self.root / "package.json").read_text())["version"], "0.1.0"
        )

    def test_retry_after_tag_success_and_publication_failure_keeps_tag_identity(self):
        with mock.patch.object(
            release,
            "publish_directory",
            side_effect=OSError("temporary publication failure"),
        ):
            with self.assertRaises(OSError):
                self.publish()
        tag = self.git("rev-parse", "sample@0.1.0")
        self.assertIsNone(release.remote_head(self.root, "sample-release"))
        self.assertEqual(self.publish(), "published")
        self.assertEqual(self.git("rev-parse", "sample@0.1.0"), tag)


class VersionPrIsolationTests(unittest.TestCase):
    def test_different_package_versions_merge_in_either_order(self):
        for order in [("engineering", "docs"), ("docs", "engineering")]:
            with (
                self.subTest(order=order),
                tempfile.TemporaryDirectory(
                    prefix="independent-versions-", dir=ROOT
                ) as directory,
            ):
                root = Path(directory) / "source"
                root.mkdir()
                remote = Path(directory) / "remote.git"
                release.git(
                    root, "init", "--quiet", "--initial-branch=main", "--template="
                )
                subprocess.run(
                    [
                        "git",
                        "init",
                        "--bare",
                        "--initial-branch=main",
                        "--template=",
                        str(remote),
                    ],
                    check=True,
                    capture_output=True,
                )
                for key, value in [
                    ("user.name", "Contract Test"),
                    ("user.email", "test@example.invalid"),
                ]:
                    release.git(root, "config", key, value)
                release.git(root, "remote", "add", "origin", str(remote))
                # A demand-owned command port fake: formal bump validation is independently
                # covered by each real package engine, while Git and PR orchestration remain real.
                provider = root / "package-port.py"
                provider.write_text(
                    'import json,sys\nfrom pathlib import Path\nr=Path(sys.argv[1]);i=r/"intent.json"\nif sys.argv[2]=="apply" and i.exists():\n v=json.loads(i.read_text())["next"];(r/"package.json").write_text(json.dumps({"version":v}));(r/"CHANGELOG.md").write_text(v);i.unlink()\n'
                )
                packages = {}
                for name, version, next_version, branch in [
                    ("engineering", "0.23.1", "0.23.2", "plugin-release/main"),
                    ("docs", "0.0.0", "0.1.0", "plugin-release/doc-coauthoring"),
                ]:
                    package_root = root / name
                    package_root.mkdir()
                    (package_root / "package.json").write_text(
                        json.dumps({"version": version})
                    )
                    (package_root / "intent.json").write_text(
                        json.dumps({"next": next_version})
                    )
                    packages[name] = {
                        "root": name,
                        "version_file": name + "/package.json",
                        "version_branch": branch,
                        "commands": {
                            "check": ["python", str(provider), name, "check"],
                            "apply": ["python", str(provider), name, "apply"],
                        },
                    }
                release.git(root, "add", "--all")
                release.git(root, "commit", "-m", "feature intents")
                release.git(root, "push", "origin", "main")
                base = release.git(root, "rev-parse", "HEAD").stdout.strip()
                requests = []
                original_run = subprocess.run

                def boundary(arguments, *args, **kwargs):
                    if arguments[0] == "gh":
                        requests.append(arguments)
                        return subprocess.CompletedProcess(
                            arguments,
                            0,
                            "[]"
                            if arguments[2] == "list"
                            else "https://example.invalid/review",
                            "",
                        )
                    return original_run(arguments, *args, **kwargs)

                with mock.patch.object(release.subprocess, "run", side_effect=boundary):
                    for name in ["engineering", "docs"]:
                        release.git(root, "checkout", "main")
                        self.assertTrue(
                            release.update_version_pr(root, name, packages[name])
                        )
                        paths = release.git(
                            root, "diff", "--name-only", base, "HEAD"
                        ).stdout.splitlines()
                        self.assertTrue(paths)
                        self.assertTrue(
                            all(path.startswith(name + "/") for path in paths), paths
                        )
                self.assertEqual(len([r for r in requests if r[2] == "create"]), 2)
                for name in order:
                    release.git(root, "checkout", "main")
                    release.git(
                        root,
                        "merge",
                        "--no-ff",
                        packages[name]["version_branch"],
                        "-m",
                        "merge " + name,
                    )
                    release.git(root, "push", "origin", "main")
                self.assertEqual(
                    json.loads((root / "engineering/package.json").read_text())[
                        "version"
                    ],
                    "0.23.2",
                )
                self.assertEqual(
                    json.loads((root / "docs/package.json").read_text())["version"],
                    "0.1.0",
                )
                self.assertFalse((root / "engineering/intent.json").exists())
                self.assertFalse((root / "docs/intent.json").exists())
