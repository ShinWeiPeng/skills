"""Public contracts for independently released packages in one Git repository."""

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
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


class CompatibilityLauncherTests(unittest.TestCase):
    def test_root_launcher_delegates_arguments_and_exit_status(self):
        with tempfile.TemporaryDirectory(
            prefix="launcher contract ", dir=ROOT
        ) as directory:
            root = Path(directory)
            package = root / "governed-engineering-skills"
            package.mkdir()
            if os.name == "nt":
                name = "Install Governed Engineering Skills.cmd"
                launcher = root / name
                shutil.copyfile(ROOT / name, launcher)
                (package / name).write_text(
                    "@echo off\necho [%1]\necho [%~2]\nexit /b 23\n"
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
                launcher = root / name
                shutil.copyfile(ROOT / name, launcher)
                child = package / name
                child.write_text('#!/bin/sh\nprintf "[%s]\\n" "$@"\nexit 23\n')
                child.chmod(0o755)
                command = ["sh", str(launcher), "marker", "two words"]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
            self.assertIn("[marker]", result.stdout)
            self.assertIn("[two words]", result.stdout)


if __name__ == "__main__":
    unittest.main()
