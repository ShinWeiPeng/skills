"""Public direct-install CLI contracts; fixtures use isolated user directories."""

import json
import os
import importlib.util
import contextlib
import io
import zipfile
from unittest import mock
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
INSTALLER = ROOT / "doc-coauthoring/scripts/install.py"


class DirectInstallTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".test-tmp").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(
            prefix="doc-direct-install-", dir=ROOT / ".test-tmp"
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.package = self.root / "source"
        shutil.copytree(
            ROOT / "doc-coauthoring",
            self.package,
            ignore=shutil.ignore_patterns("dist", "__pycache__", ".changeset"),
        )
        # Keep fixtures valid when the release workflow advances package metadata.
        self.initial_version = json.loads(
            (self.package / "package.json").read_text(encoding="utf-8")
        )["version"]
        major, minor, patch = self.initial_version.split(".")
        self.next_version = f"{major}.{minor}.{int(patch) + 1}"

    def cli(self, *args, expected=0):
        result = subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                *args,
                "--home",
                str(self.home),
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def install(self, target="codex", expected=0):
        return self.cli(
            "install",
            "--target",
            target,
            "--source",
            str(self.package),
            expected=expected,
        )

    def active(self, target="codex"):
        directory = ".agents" if target == "codex" else ".claude"
        return self.home / directory / "skills/doc-coauthoring"

    def version(self, version, marker):
        metadata = self.package / "package.json"
        data = json.loads(metadata.read_text(encoding="utf-8"))
        data["version"] = version
        metadata.write_text(json.dumps(data), encoding="utf-8")
        skill = self.package / "skills/doc-coauthoring/SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + marker, encoding="utf-8")

    def test_versions_switch_independently_and_rollback(self):
        self.install("both")
        original = (self.active() / "SKILL.md").read_bytes()
        self.version(self.next_version, "\nVersion two fixture.\n")
        self.install("codex")
        updated = (self.active() / "SKILL.md").read_bytes()
        self.assertNotEqual(original, updated)
        self.assertEqual((self.active("claude") / "SKILL.md").read_bytes(), original)
        store = self.home / ".doc-coauthoring/versions"
        self.assertEqual(
            (store / self.initial_version / "SKILL.md").read_bytes(), original
        )
        self.assertEqual((store / self.next_version / "SKILL.md").read_bytes(), updated)
        self.cli("switch", self.initial_version, "--target", "codex")
        self.assertEqual((self.active() / "SKILL.md").read_bytes(), original)
        self.cli("rollback", "--target", "codex")
        self.assertEqual((self.active() / "SKILL.md").read_bytes(), updated)
        self.install("claude")
        self.cli("switch", self.initial_version, "--target", "claude")
        self.assertEqual((self.active("claude") / "SKILL.md").read_bytes(), original)
        self.cli("rollback", "--target", "claude")
        self.assertEqual((self.active("claude") / "SKILL.md").read_bytes(), updated)
        self.assertEqual(len(list((self.home / ".claude/skills").iterdir())), 1)
        result = self.cli("list")
        self.assertIn(self.initial_version, result.stdout)
        self.assertIn(self.next_version, result.stdout)

    @unittest.skipUnless(os.name == "nt", "Windows command launcher requires Windows")
    def test_windows_double_click_launcher_forwards_arguments(self):
        launcher = self.package / "Install Doc Coauthoring.cmd"
        result = subprocess.run(
            [
                "cmd.exe",
                "/d",
                "/c",
                "call",
                str(launcher),
                "install",
                "--target",
                "codex",
                "--home",
                str(self.home),
            ],
            input="\n",
            text=True,
            capture_output=True,
            cwd=self.root,
            env=dict(os.environ, DOC_COAUTHORING_NO_PAUSE="1"),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.active() / "SKILL.md").exists())

    def test_posix_launcher_forwards_arguments(self):
        shell = (
            Path("C:/Program Files/Git/bin/bash.exe")
            if os.name == "nt"
            else shutil.which("sh")
        )
        if not shell or not Path(shell).exists():
            self.skipTest("No POSIX shell available")
        launcher = self.package / "Install Doc Coauthoring.sh"
        env = dict(os.environ)
        env["PATH"] = (
            str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        )
        result = subprocess.run(
            [
                str(shell),
                str(launcher),
                "install",
                "--target",
                "claude",
                "--home",
                str(self.home),
            ],
            text=True,
            capture_output=True,
            cwd=self.root,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.active("claude") / "SKILL.md").exists())

    def test_release_artifact_contains_runnable_direct_installers(self):
        changesets = self.package / ".changeset"
        changesets.mkdir()
        (changesets / "release-state.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "current_version": self.initial_version,
                    "production_fingerprint": None,
                    "applied_changesets": [],
                }
            ),
            encoding="utf-8",
        )
        (changesets / "direct-install.md").write_text(
            '---\n"doc-coauthoring": minor\n---\nDirect installation.\n',
            encoding="utf-8",
        )
        (changesets / "release-intent.json").write_text(
            json.dumps(
                {
                    "bump": "minor",
                    "changesets": ["direct-install"],
                    "summary": {
                        "Breaking Changes": [],
                        "Added": ["Direct installation"],
                        "Changed": [],
                        "Fixed": [],
                    },
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "-C", str(self.root), "init", "--quiet", "--template="],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "add", "--", "source"],
            check=True,
            capture_output=True,
        )
        for operation in ("assemble", "validate"):
            result = subprocess.run(
                [
                    sys.executable,
                    str(self.package / "scripts/release.py"),
                    operation,
                    "--root",
                    str(self.package),
                ],
                cwd=self.root,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        artifact = self.package / "dist/doc-coauthoring"
        for relative in (
            "Install Doc Coauthoring.cmd",
            "Install Doc Coauthoring.sh",
            "scripts/install.py",
            "scripts/install.ps1",
            "scripts/install-gui.sh",
            "Install Doc Coauthoring.desktop",
            "package.json",
        ):
            self.assertTrue((artifact / relative).is_file(), relative)
        result = subprocess.run(
            [
                sys.executable,
                str(artifact / "scripts/install.py"),
                "install",
                "--target",
                "codex",
                "--home",
                str(self.home),
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.active() / "SKILL.md").is_file())

    def archive(self, extra=None):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            for path in self.package.rglob("*"):
                if path.is_file():
                    archive.writestr(
                        "release/doc-coauthoring/"
                        + path.relative_to(self.package).as_posix(),
                        path.read_bytes(),
                    )
            if extra:
                archive.writestr(*extra)
        return data.getvalue()

    def test_released_package_download_and_payload_validation(self):
        module = self.module()
        requested = []
        archive = self.archive()

        def urlopen(request, **kwargs):
            url = request.full_url
            requested.append(url)
            if "publication-record.json" in url:
                return io.BytesIO(
                    json.dumps({"artifact": {"version": self.initial_version}}).encode()
                )
            return io.BytesIO(archive)

        with mock.patch("urllib.request.urlopen", urlopen):
            result = module.main(
                [
                    "install",
                    "--version",
                    "latest",
                    "--target",
                    "codex",
                    "--home",
                    str(self.home),
                ]
            )
        self.assertEqual(result, 0)
        self.assertTrue((self.active() / "SKILL.md").is_file())
        self.assertTrue(
            any(f"doc-coauthoring%40{self.initial_version}" in url for url in requested)
        )

    def test_malformed_or_unavailable_download_preserves_previous_activation(self):
        self.install()
        before = self.snapshot(self.home)
        module = self.module()
        malicious = self.archive(("release/doc-coauthoring/../escape.txt", "bad"))
        with mock.patch("urllib.request.urlopen", return_value=io.BytesIO(malicious)):
            with contextlib.redirect_stderr(io.StringIO()):
                result = module.main(
                    [
                        "install",
                        "--version",
                        self.next_version,
                        "--target",
                        "codex",
                        "--home",
                        str(self.home),
                    ]
                )
        self.assertEqual(result, 1)
        self.assertEqual(self.snapshot(self.home), before)
        with mock.patch(
            "urllib.request.urlopen", side_effect=OSError("Network unavailable")
        ):
            with contextlib.redirect_stderr(io.StringIO()):
                result = module.main(
                    [
                        "install",
                        "--version",
                        self.next_version,
                        "--target",
                        "codex",
                        "--home",
                        str(self.home),
                    ]
                )
        self.assertEqual(result, 1)
        self.assertEqual(self.snapshot(self.home), before)

    def snapshot(self, directory):
        return {
            str(path.relative_to(directory)): (
                path.read_bytes(),
                path.stat().st_mtime_ns,
            )
            for path in directory.rglob("*")
            if path.is_file()
        }

    def module(self):
        spec = importlib.util.spec_from_file_location(
            "direct_install_under_test", INSTALLER
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_committed_activation_reports_success_when_backup_cleanup_is_locked(self):
        self.install("both")
        self.version(self.next_version, "\nUpdated fixture.\n")
        module = self.module()
        with mock.patch.object(
            module.shutil, "rmtree", side_effect=OSError("Backup locked")
        ):
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                result = module.main(
                    [
                        "install",
                        "--source",
                        str(self.package),
                        "--target",
                        "both",
                        "--home",
                        str(self.home),
                    ]
                )
        self.assertEqual(result, 0)
        self.assertIn("cleanup", errors.getvalue().lower())
        self.assertIn("Backup locked", errors.getvalue())
        state = json.loads((self.home / ".doc-coauthoring/state.json").read_text())
        for target in ("codex", "claude"):
            self.assertEqual(state["active"][target]["version"], self.next_version)
            self.assertIn(
                "Updated fixture", (self.active(target) / "SKILL.md").read_text()
            )
        self.assertTrue(any((self.home / ".doc-coauthoring/staging").iterdir()))

    @unittest.skipUnless(os.name == "nt", "Windows interpreter probes require Windows")
    def test_windows_failed_interpreter_probe_tries_next_candidate(self):
        binary = self.root / "probe-bin"
        binary.mkdir()
        shutil.copyfile(shutil.which("where.exe"), binary / "py.exe")
        (binary / "python3.cmd").write_text('@"' + sys.executable + '" %*\n')
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.package / "scripts/install.ps1"),
                "install",
                "--target",
                "codex",
                "--home",
                str(self.home),
            ],
            text=True,
            capture_output=True,
            cwd=self.root,
            env=dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"]),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.active() / "SKILL.md").exists())

    def test_documented_linux_bootstrap_propagates_initial_download_failure(self):
        shell = (
            Path("C:/Program Files/Git/bin/bash.exe")
            if os.name == "nt"
            else shutil.which("sh")
        )
        if not shell or not Path(shell).exists():
            self.skipTest("No POSIX shell available")
        binary = self.root / "download-bin"
        binary.mkdir()
        fake_curl = binary / "curl"
        fake_curl.write_text("#!/bin/sh\nexit 22\n", encoding="utf-8")
        fake_curl.chmod(0o755)
        readme = (ROOT / "doc-coauthoring/README.md").read_text(encoding="utf-8")
        command = readme.split("```sh\n")[2].split("```", 1)[0].strip()
        result = subprocess.run(
            [
                str(shell),
                "-c",
                'PATH="$(pwd)/download-bin:$PATH"; export PATH; ' + command,
            ],
            capture_output=True,
            text=True,
            cwd=self.root,
            env=dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"]),
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.active().exists())

    def test_identical_reinstall_preserves_files_and_timestamps(self):
        self.install("both")
        before = self.snapshot(self.home)
        self.install("both")
        self.assertEqual(self.snapshot(self.home), before)

    def test_new_version_with_identical_skill_does_not_rewrite_active_files(self):
        self.install()
        before = self.snapshot(self.active())
        self.version(self.next_version, "")
        self.install()
        self.assertEqual(self.snapshot(self.active()), before)
        self.assertIn(f"{self.next_version} active: codex", self.cli("list").stdout)

    def test_same_version_with_different_content_is_rejected(self):
        self.install()
        before = self.snapshot(self.home)
        self.version(self.initial_version, "\nDifferent content at same version.\n")
        result = self.install(expected=1)
        self.assertIn("Different content", result.stderr)
        self.assertEqual(self.snapshot(self.home), before)

    def test_modified_and_unknown_skills_are_preserved(self):
        self.install()
        skill = self.active() / "SKILL.md"
        skill.write_text("Personal changes", encoding="utf-8")
        before = self.snapshot(self.home)
        result = self.install(expected=1)
        self.assertIn("Locally modified", result.stderr)
        self.assertEqual(self.snapshot(self.home), before)
        unknown = self.active("claude")
        unknown.mkdir(parents=True)
        (unknown / "SKILL.md").write_text("Unmanaged", encoding="utf-8")
        result = self.install("claude", expected=1)
        self.assertIn("Unknown existing skill", result.stderr)
        self.assertEqual((unknown / "SKILL.md").read_text(), "Unmanaged")

    def test_corrupt_store_cannot_be_activated(self):
        self.install()
        stored = (
            self.home / ".doc-coauthoring/versions" / self.initial_version / "SKILL.md"
        )
        stored.write_text("Unexpected changes", encoding="utf-8")
        before = self.snapshot(self.active())
        result = self.cli(
            "switch", self.initial_version, "--target", "codex", expected=1
        )
        self.assertIn("Stored version was modified", result.stderr)
        self.assertEqual(self.snapshot(self.active()), before)

    def test_second_target_activation_failure_restores_both_targets(self):
        self.install("both")
        self.version(self.next_version, "\nNew fixture.\n")
        self.install("codex")
        self.cli("switch", self.initial_version, "--target", "codex")
        before = {
            target: self.snapshot(self.active(target)) for target in ("codex", "claude")
        }
        state = self.home / ".doc-coauthoring/state.json"
        old_state = state.read_bytes()
        module = self.module()
        replace = module.os.replace
        failed = []

        def external_replace(source, destination):
            if Path(destination) == self.active("claude") and not failed:
                failed.append(True)
                raise OSError("Injected external rename failure")
            return replace(source, destination)

        with mock.patch.object(module.os, "replace", external_replace):
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                result = module.main(
                    [
                        "switch",
                        self.next_version,
                        "--target",
                        "both",
                        "--home",
                        str(self.home),
                    ]
                )
        self.assertEqual(result, 1)
        self.assertIn("Injected external rename failure", errors.getvalue())
        self.assertEqual(state.read_bytes(), old_state)
        for target in before:
            self.assertEqual(self.snapshot(self.active(target)), before[target])

    def test_failed_first_install_exposes_no_partial_skill(self):
        module = self.module()
        replace = module.os.replace
        failed = []

        def external_replace(source, destination):
            if Path(destination) == self.active("claude") and not failed:
                failed.append(True)
                raise OSError("Injected first-install activation failure")
            return replace(source, destination)

        with mock.patch.object(module.os, "replace", external_replace):
            with contextlib.redirect_stderr(io.StringIO()):
                result = module.main(
                    [
                        "install",
                        "--source",
                        str(self.package),
                        "--target",
                        "both",
                        "--home",
                        str(self.home),
                    ]
                )
        self.assertEqual(result, 1)
        self.assertFalse(self.active().exists())
        self.assertFalse(self.active("claude").exists())
        state = json.loads((self.home / ".doc-coauthoring/state.json").read_text())
        self.assertEqual(state["active"], {})

    def test_noninteractive_target_and_lock_rejection_are_actionable(self):
        result = self.cli("install", "--source", str(self.package), expected=2)
        self.assertIn("--target", result.stderr)
        root = self.home / ".doc-coauthoring"
        root.mkdir(exist_ok=True)
        lock = root / ".install.lock"
        lock.write_text("Another installer")
        self.install(expected=1)
        self.assertEqual(lock.read_text(), "Another installer")

    def test_incomplete_source_and_missing_version_preserve_active_skill(self):
        self.install()
        before = self.snapshot(self.active())
        (self.package / "skills/doc-coauthoring/references/codex.md").unlink()
        self.install(expected=1)
        self.cli("switch", self.next_version, "--target", "codex", expected=1)
        self.assertEqual(self.snapshot(self.active()), before)

    def test_default_personal_scope_works_outside_a_project(self):
        result = subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                "install",
                "--source",
                str(self.package),
                "--target",
                "both",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            env=dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home)),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for target in ("codex", "claude"):
            self.assertTrue((self.active(target) / "SKILL.md").is_file())
        self.assertEqual(
            self.snapshot(self.active()).keys(),
            self.snapshot(self.active("claude")).keys(),
        )
        for relative in self.snapshot(self.active()):
            self.assertEqual(
                (self.active() / relative).read_bytes(),
                (self.active("claude") / relative).read_bytes(),
            )

    def test_install_copies_complete_skill_without_plugin_state(self):
        result = self.install()
        active = self.active()
        self.assertIn(self.initial_version, result.stdout)
        self.assertTrue((active / "SKILL.md").is_file())
        self.assertTrue((active / "references/codex.md").is_file())
        self.assertTrue((active / "references/claude.md").is_file())
        self.assertTrue((active / "agents/openai.yaml").is_file())
        self.assertTrue((active / "references/UPSTREAM.md").is_file())
        self.assertIn(
            "references/UPSTREAM.md",
            (active / "SKILL.md").read_text(encoding="utf-8"),
        )
        self.assertFalse((self.home / ".codex/plugins").exists())
        self.assertFalse((self.home / ".claude/plugins").exists())
        self.assertFalse(self.active("claude").exists())
        source = self.package / "skills/doc-coauthoring"
        for path in source.rglob("*"):
            if path.is_file():
                relative = path.relative_to(source)
                expected = path.read_bytes().replace(b"\r\n", b"\n")
                if relative.as_posix() == "SKILL.md":
                    expected = expected.replace(
                        b"../../UPSTREAM.md", b"references/UPSTREAM.md"
                    )
                self.assertEqual((active / relative).read_bytes(), expected)
        for name in ("UPSTREAM.md", "LICENSE", "NOTICE"):
            self.assertEqual(
                (active / "references" / name).read_bytes(),
                (self.package / name).read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
