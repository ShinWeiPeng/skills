"""External CLI contracts for the document package release lifecycle."""

import json
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]


class DocReleaseTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".test-tmp").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix="doc-release-contract-", dir=ROOT / ".test-tmp"
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.package = self.root / "doc-coauthoring"
        shutil.copytree(
            ROOT / "doc-coauthoring",
            self.package,
            ignore=shutil.ignore_patterns("dist", "__pycache__", ".changeset"),
        )
        subprocess.run(
            ["git", "-C", str(self.root), "init", "--quiet", "--template="], check=True
        )
        # Fixed public inputs keep these lifecycle cases valid after real releases.
        changesets = self.package / ".changeset"
        changesets.mkdir()
        for name in [
            "package.json",
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ]:
            data = json.loads((self.package / name).read_text(encoding="utf-8"))
            data["version"] = "0.0.0"
            (self.package / name).write_text(json.dumps(data), encoding="utf-8")
        (self.package / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
        (changesets / "release-state.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "current_version": "0.0.0",
                    "production_fingerprint": None,
                    "applied_changesets": [],
                }
            )
        )
        (changesets / "initial-doc-coauthoring.md").write_text(
            '---\n"doc-coauthoring": minor\n---\nInitial public contract fixture.\n'
        )
        (changesets / "release-intent.json").write_text(
            json.dumps(
                {
                    "bump": "minor",
                    "changesets": ["initial-doc-coauthoring"],
                    "summary": {
                        "Breaking Changes": [],
                        "Added": ["Initial workflow"],
                        "Changed": [],
                        "Fixed": [],
                    },
                }
            )
        )
        self.stage()

    def stage(self):
        subprocess.run(
            ["git", "-C", str(self.root), "add", "--all"],
            check=True,
            capture_output=True,
        )

    def cli(self, operation, expected=0):
        result = subprocess.run(
            [sys.executable, str(self.package / "scripts/release.py"), operation],
            cwd=self.root,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.stderr = result.stderr
        return result.stdout.strip()

    def read(self, path):
        return json.loads((self.package / path).read_text(encoding="utf-8"))

    def test_yaml_syntax_and_codex_interface_are_validated_before_release(self):
        skill = self.package / "skills/doc-coauthoring/SKILL.md"
        original = skill.read_text(encoding="utf-8")
        broken = original.split("description: ", 1)
        skill.write_text(
            broken[0]
            + "description: Draft docs: review them"
            + broken[1][broken[1].index("\n") :],
            encoding="utf-8",
        )
        self.cli("check", expected=1)
        self.assertIn("invalid YAML", self.stderr)
        skill.write_text(original, encoding="utf-8")
        (self.package / "skills/doc-coauthoring/agents/openai.yaml").write_text(
            "interface: [unterminated", encoding="utf-8"
        )
        self.cli("check", expected=1)
        self.assertIn("invalid YAML", self.stderr)

    def test_output_redirect_cannot_delete_a_marked_directory_outside_package(self):
        self.cli("check")
        outside = self.root / "outside"
        artifact = outside / "doc-coauthoring"
        artifact.mkdir(parents=True)
        sentinel = artifact / "important.txt"
        sentinel.write_text("preserve this file", encoding="utf-8")
        (artifact / ".generated-doc-coauthoring").write_text("prior artifact")
        link = self.package / "dist"
        if os.name == "nt":
            subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
                check=True,
                capture_output=True,
            )
        else:
            link.symlink_to(outside, target_is_directory=True)
        try:
            self.cli("assemble", expected=1)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve this file")
            self.assertIn("redirected package path", self.stderr)
        finally:
            if link.is_symlink():
                link.unlink()
            else:
                os.rmdir(link)

    def test_portable_content_fingerprint_has_a_fixed_mixed_case_vector(self):
        spec = importlib.util.spec_from_file_location(
            "doc_release", ROOT / "doc-coauthoring/scripts/release.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tree = self.root / "mixed-case-vector"
        (tree / "a").mkdir(parents=True)
        for relative, content in [
            ("a/agents.md", b"metadata\n"),
            ("Z.txt", b"alpha\n"),
            ("a/SKILL.md", b"workflow\n"),
        ]:
            (tree / relative).write_bytes(content)
        self.assertEqual(
            module.tree_fingerprint(tree),
            "sha256:b753ea2ed36bbd498f998ad012ced1ab22d8fd2a4e65e69981913c41b218a8ac",
        )

    def test_initial_minor_release_is_shared_across_harnesses_and_idempotent(self):
        self.cli("check")
        self.cli("apply-intent")
        for path in [
            "package.json",
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ]:
            self.assertEqual(self.read(path)["version"], "0.1.0")
        self.assertTrue(
            (
                self.package / ".changeset/applied/0.1.0/initial-doc-coauthoring.md"
            ).is_file()
        )
        self.assertFalse((self.package / ".changeset/release-intent.json").exists())
        self.stage()
        self.assertFalse(json.loads(self.cli("apply-intent"))["changed"])
        self.assertIn("## 0.1.0", (self.package / "CHANGELOG.md").read_text())

    def test_changed_production_requires_intent_but_untracked_files_do_not(self):
        self.cli("apply-intent")
        self.stage()
        fingerprint = self.cli("fingerprint")
        (self.package / "skills/doc-coauthoring/untracked.md").write_text("local only")
        self.assertEqual(self.cli("fingerprint"), fingerprint)
        self.cli("check")
        source = self.package / "skills/doc-coauthoring/SKILL.md"
        source.write_text(
            source.read_text(encoding="utf-8") + "\nChanged workflow.\n",
            encoding="utf-8",
        )
        self.assertNotEqual(self.cli("fingerprint"), fingerprint)
        self.cli("check", expected=1)

    def test_highest_pending_bump_and_exact_changeset_set_are_required(self):
        (self.package / ".changeset/second.md").write_text(
            '---\n"doc-coauthoring": major\n---\nA breaking workflow change.\n'
        )
        intent = self.read(".changeset/release-intent.json")
        intent["changesets"].append("second")
        (self.package / ".changeset/release-intent.json").write_text(json.dumps(intent))
        self.stage()
        self.cli("check", expected=1)
        intent["bump"] = "major"
        (self.package / ".changeset/release-intent.json").write_text(json.dumps(intent))
        self.cli("apply-intent")
        self.assertEqual(self.read("package.json")["version"], "1.0.0")

    def test_build_is_deterministic_and_validation_rejects_artifact_drift(self):
        self.cli("apply-intent")
        self.stage()
        before = subprocess.check_output(
            ["git", "-C", str(self.root), "write-tree"], text=True
        )
        first = json.loads(self.cli("assemble"))
        self.assertEqual(first, json.loads(self.cli("assemble")))
        self.cli("validate")
        self.assertEqual(
            (
                self.package / "dist/doc-coauthoring/.generated-doc-coauthoring"
            ).read_bytes(),
            b"Generated by scripts/release.py\n",
        )
        self.assertEqual(
            (
                self.package / "dist/doc-coauthoring-release/.generated-doc-coauthoring"
            ).read_bytes(),
            b"Generated publication\n",
        )
        self.assertEqual(
            subprocess.check_output(
                ["git", "-C", str(self.root), "write-tree"], text=True
            ),
            before,
        )
        artifact = self.package / "dist/doc-coauthoring/skills/doc-coauthoring/SKILL.md"
        artifact.write_text("drift")
        self.cli("validate", expected=1)


if __name__ == "__main__":
    unittest.main()
