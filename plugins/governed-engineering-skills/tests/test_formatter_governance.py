from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = REPOSITORY_ROOT / "skills" / "engineering"
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "engineering" / "formatter-governance"
POLICY_CLI = SKILL_ROOT / "scripts" / "formatter_policy.py"
CANONICAL_SPEC = b"""---
spec_version: 1
spec_id: SPEC-0001
revision: 1
status: confirmed
change_set: demo
---
"""


def run_policy(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(POLICY_CLI), *args],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initialize_repository(root: Path, files: dict[str, bytes]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    for args in (
        ("init",),
        ("config", "user.email", "formatter-tests@example.invalid"),
        ("config", "user.name", "Formatter Tests"),
        ("add", "."),
        ("commit", "-m", "fixture"),
    ):
        subprocess.run(
            ["git", "-C", str(root), *args],
            text=True,
            capture_output=True,
            check=True,
        )


class FormatterSelectionContractTests(unittest.TestCase):
    def test_greenfield_languages_select_the_governed_defaults(self) -> None:
        expected = {
            "python": "ruff",
            "javascript": "prettier",
            "typescript": "prettier",
            "json": "prettier",
            "css": "prettier",
            "markdown": "prettier",
            "yaml": "prettier",
            "c": "clang-format",
            "cpp": "clang-format",
            "go": "gofmt",
            "rust": "rustfmt",
            "csharp": "dotnet format",
            "java": "google-java-format",
        }

        for language, formatter in expected.items():
            with self.subTest(language=language):
                result = run_policy(
                    "select",
                    "--implementation",
                    "absent",
                    "--context",
                    "absent",
                    "--language",
                    language,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                decision = json.loads(result.stdout)
                self.assertEqual("PASS", decision["status"])
                self.assertEqual("greenfield", decision["project_kind"])
                self.assertEqual(formatter, decision["formatter"])

    def test_governed_rust_and_csharp_commands_expand_exact_program_files(self) -> None:
        for language in ("rust", "csharp"):
            with self.subTest(language=language):
                result = run_policy(
                    "select",
                    "--implementation",
                    "absent",
                    "--context",
                    "absent",
                    "--language",
                    language,
                )

                self.assertEqual(0, result.returncode, result.stderr)
                decision = json.loads(result.stdout)
                self.assertIn("<files>", decision["check"])
                self.assertIn("<files>", decision["write"])

    def test_existing_project_preserves_discovered_repository_formatter(self) -> None:
        result = run_policy(
            "select",
            "--implementation",
            "present",
            "--context",
            "present",
            "--language",
            "python",
            "--repository-formatter",
            "black",
            "--repository-check-argv",
            '["black", "--check", "."]',
            "--repository-write-argv",
            '["black", "."]',
        )

        self.assertEqual(0, result.returncode, result.stderr)
        decision = json.loads(result.stdout)
        self.assertEqual("PASS", decision["status"])
        self.assertEqual("existing", decision["project_kind"])
        self.assertEqual("black", decision["formatter"])
        self.assertEqual(["black", "--check", "."], decision["check"])
        self.assertEqual(["black", "."], decision["write"])

    def test_existing_project_without_repository_formatter_uses_governed_fallback(
        self,
    ) -> None:
        result = run_policy(
            "select",
            "--implementation",
            "present",
            "--context",
            "present",
            "--language",
            "python",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        decision = json.loads(result.stdout)
        self.assertEqual("PASS", decision["status"])
        self.assertEqual("existing", decision["project_kind"])
        self.assertEqual("ruff", decision["formatter"])
        self.assertEqual("governed-fallback", decision["policy_source"])

    def test_indeterminate_project_state_fails_closed(self) -> None:
        result = run_policy(
            "select",
            "--implementation",
            "indeterminate",
            "--context",
            "absent",
            "--language",
            "python",
        )

        self.assertEqual(2, result.returncode)
        decision = json.loads(result.stdout)
        self.assertEqual("BLOCKED", decision["status"])
        self.assertEqual("indeterminate", decision["project_kind"])

    def test_language_aliases_resolve_to_the_canonical_policy(self) -> None:
        for language, formatter in (("c++", "clang-format"), ("c#", "dotnet format")):
            with self.subTest(language=language):
                result = run_policy(
                    "select",
                    "--implementation",
                    "absent",
                    "--context",
                    "absent",
                    "--language",
                    language,
                )
                self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(formatter, json.loads(result.stdout)["formatter"])


class FullFormatWorkflowTests(unittest.TestCase):
    def test_canonical_spec_requires_one_affirmative_format_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": CANONICAL_SPEC,
                    "src/app.py": b"VALUE = 1\n",
                },
            )
            common = (
                "full-format",
                "--project-root",
                str(root),
                "--implementation",
                "present",
                "--context",
                "present",
                "--language",
                "python",
                "--canonical-spec",
                "specs/SPEC-0001-demo.md",
                "--spec-verification-status",
                "pass",
                "--formatter-available",
                "true",
            )

            pending = run_policy(*common, "--confirmation", "pending")
            declined = run_policy(*common, "--confirmation", "no")
            ambiguous = run_policy(*common, "--confirmation", "ambiguous")
            accepted = run_policy(*common, "--confirmation", "yes")

            self.assertEqual(2, pending.returncode)
            self.assertEqual(
                "confirmation-required", json.loads(pending.stdout)["reason_code"]
            )
            self.assertFalse(json.loads(declined.stdout)["format_write_allowed"])
            self.assertEqual(2, ambiguous.returncode)
            self.assertFalse(json.loads(ambiguous.stdout)["format_write_allowed"])
            self.assertTrue(json.loads(accepted.stdout)["format_write_allowed"])

    def test_noncanonical_spec_metadata_cannot_trigger_format_authorization(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": b"---\nstatus: confirmed\n---\n",
                    "src/app.py": b"VALUE = 1\n",
                },
            )

            result = run_policy(
                "full-format",
                "--project-root",
                str(root),
                "--implementation",
                "present",
                "--context",
                "present",
                "--language",
                "python",
                "--canonical-spec",
                "specs/SPEC-0001-demo.md",
                "--spec-verification-status",
                "pass",
                "--confirmation",
                "yes",
                "--formatter-available",
                "true",
            )

            self.assertEqual(2, result.returncode)
            self.assertEqual(
                "canonical-spec-invalid", json.loads(result.stdout)["reason_code"]
            )

    def test_program_scope_includes_source_and_tests_but_excludes_repository_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": CANONICAL_SPEC,
                    "src/app.py": b"VALUE = 1\n",
                    "tests/test_app.py": b"def test_app():\n    assert True\n",
                    "skills/engineering/spec-governance/scripts/spec_contract.py": b"VALUE = 1\n",
                    "spec-governance/scratch.py": b"SCRATCH = True\n",
                    "docs/example.py": b"EXAMPLE = True\n",
                    "config/settings.py": b"SETTING = True\n",
                    "setup.py": b"from setuptools import setup\n",
                    "generated/client.py": b"GENERATED = True\n",
                    "vendor/library.py": b"VENDORED = True\n",
                    "build/output.py": b"OUTPUT = True\n",
                    "pyproject.toml": b"[tool.demo]\n",
                },
            )

            result = run_policy(
                "full-format",
                "--project-root",
                str(root),
                "--implementation",
                "present",
                "--context",
                "present",
                "--language",
                "python",
                "--canonical-spec",
                "specs/SPEC-0001-demo.md",
                "--spec-verification-status",
                "pass",
                "--confirmation",
                "yes",
                "--formatter-available",
                "true",
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                [
                    "skills/engineering/spec-governance/scripts/spec_contract.py",
                    "src/app.py",
                    "tests/test_app.py",
                ],
                json.loads(result.stdout)["program_files"],
            )

    def test_dirty_program_files_block_while_unrelated_dirty_files_do_not(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": CANONICAL_SPEC,
                    "src/app.py": b"VALUE = 1\n",
                    "README.md": b"clean\n",
                },
            )
            args = (
                "full-format",
                "--project-root",
                str(root),
                "--implementation",
                "present",
                "--context",
                "present",
                "--language",
                "python",
                "--canonical-spec",
                "specs/SPEC-0001-demo.md",
                "--spec-verification-status",
                "pass",
                "--confirmation",
                "yes",
                "--formatter-available",
                "true",
            )

            source = root / "src" / "app.py"
            source.write_bytes(b"VALUE=2\n")
            before = file_hash(source)
            blocked = run_policy(*args)

            self.assertEqual(2, blocked.returncode)
            self.assertEqual(["src/app.py"], json.loads(blocked.stdout)["dirty_files"])
            self.assertEqual(before, file_hash(source))

            subprocess.run(
                ["git", "-C", str(root), "checkout", "--", "src/app.py"],
                check=True,
                capture_output=True,
            )
            readme = root / "README.md"
            readme.write_bytes(b"dirty but unrelated\n")
            unrelated_before = file_hash(readme)
            passed = run_policy(*args)

            self.assertEqual(0, passed.returncode, passed.stderr)
            self.assertTrue(json.loads(passed.stdout)["format_write_allowed"])
            self.assertEqual(unrelated_before, file_hash(readme))

    def test_completed_format_requires_cli_write_and_follow_up_check(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": CANONICAL_SPEC,
                    "src/app.py": b"VALUE = 1\n",
                },
            )
            common = (
                "full-format",
                "--project-root",
                str(root),
                "--implementation",
                "present",
                "--context",
                "present",
                "--language",
                "python",
                "--canonical-spec",
                "specs/SPEC-0001-demo.md",
                "--spec-verification-status",
                "pass",
                "--confirmation",
                "yes",
                "--formatter-available",
                "true",
            )

            plan = run_policy(*common, "--execution-mode", "cli")
            self.assertTrue(json.loads(plan.stdout)["format_write_allowed"])
            (root / "src" / "app.py").write_bytes(b"VALUE = 2\n")
            result_evidence = (
                "--pre-write-clean-status",
                "pass",
                "--write-status",
                "pass",
                "--check-status",
                "pass",
            )
            ide = run_policy(*common, *result_evidence, "--execution-mode", "ide")
            cli = run_policy(*common, *result_evidence, "--execution-mode", "cli")

            self.assertEqual(2, ide.returncode)
            self.assertEqual("cli-required", json.loads(ide.stdout)["reason_code"])
            completed = json.loads(cli.stdout)
            self.assertEqual(0, cli.returncode, cli.stderr)
            self.assertTrue(completed["format_completed"])
            self.assertEqual(
                [
                    "ruff",
                    "format",
                    "--config",
                    "format.line-ending = 'lf'",
                    "src/app.py",
                ],
                completed["write"],
            )
            self.assertEqual(
                [
                    "ruff",
                    "format",
                    "--config",
                    "format.line-ending = 'lf'",
                    "--check",
                    "src/app.py",
                ],
                completed["check"],
            )
            self.assertEqual("separate", completed["delivery_validation"])

    def test_missing_formatter_requires_authorized_successful_installation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": CANONICAL_SPEC,
                    "src/app.py": b"VALUE = 1\n",
                },
            )
            common = (
                "full-format",
                "--project-root",
                str(root),
                "--implementation",
                "present",
                "--context",
                "present",
                "--language",
                "python",
                "--canonical-spec",
                "specs/SPEC-0001-demo.md",
                "--spec-verification-status",
                "pass",
                "--confirmation",
                "yes",
            )

            missing = run_policy(
                *common,
                "--formatter-available",
                "false",
                "--install-permission",
                "missing",
            )
            denied = run_policy(
                *common,
                "--formatter-available",
                "false",
                "--install-permission",
                "denied",
            )
            failed = run_policy(
                *common,
                "--formatter-available",
                "false",
                "--install-permission",
                "authorized",
                "--install-status",
                "fail",
            )
            failed_despite_partial_availability = run_policy(
                *common,
                "--formatter-available",
                "true",
                "--install-permission",
                "authorized",
                "--install-status",
                "fail",
            )
            installed = run_policy(
                *common,
                "--formatter-available",
                "true",
                "--install-permission",
                "authorized",
                "--install-status",
                "pass",
            )

            self.assertEqual(
                "installation-authorization-required",
                json.loads(missing.stdout)["reason_code"],
            )
            self.assertEqual(
                "installation-denied", json.loads(denied.stdout)["reason_code"]
            )
            self.assertEqual(
                "installation-failed", json.loads(failed.stdout)["reason_code"]
            )
            self.assertEqual(
                "installation-failed",
                json.loads(failed_despite_partial_availability.stdout)["reason_code"],
            )
            self.assertEqual(0, installed.returncode, installed.stderr)
            self.assertTrue(json.loads(installed.stdout)["format_write_allowed"])

    def test_repository_formatter_without_explicit_file_scope_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": CANONICAL_SPEC,
                    "src/app.js": b"export const value = 1;\n",
                },
            )

            result = run_policy(
                "full-format",
                "--project-root",
                str(root),
                "--implementation",
                "present",
                "--context",
                "present",
                "--language",
                "javascript",
                "--canonical-spec",
                "specs/SPEC-0001-demo.md",
                "--spec-verification-status",
                "pass",
                "--confirmation",
                "yes",
                "--repository-formatter",
                "prettier-script",
                "--repository-check-argv",
                '["npm", "run", "format:check"]',
                "--repository-write-argv",
                '["npm", "run", "format"]',
                "--formatter-available",
                "true",
            )

            self.assertEqual(2, result.returncode)
            self.assertEqual(
                "unscoped-formatter-command",
                json.loads(result.stdout)["reason_code"],
            )

    def test_repository_formatter_expands_its_only_scope_placeholder(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": CANONICAL_SPEC,
                    "src/app.js": b"export const value = 1;\n",
                },
            )

            result = run_policy(
                "full-format",
                "--project-root",
                str(root),
                "--implementation",
                "present",
                "--context",
                "present",
                "--language",
                "javascript",
                "--canonical-spec",
                "specs/SPEC-0001-demo.md",
                "--spec-verification-status",
                "pass",
                "--confirmation",
                "yes",
                "--repository-formatter",
                "prettier",
                "--repository-check-argv",
                '["prettier", "--check", "."]',
                "--repository-write-argv",
                '["prettier", "--write", "."]',
                "--formatter-available",
                "true",
            )

            self.assertEqual(0, result.returncode, result.stderr)
            decision = json.loads(result.stdout)
            self.assertEqual(["prettier", "--check", "src/app.js"], decision["check"])
            self.assertEqual(["prettier", "--write", "src/app.js"], decision["write"])

    def test_repository_formatter_with_extra_file_scope_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": CANONICAL_SPEC,
                    "src/app.js": b"export const value = 1;\n",
                    "docs/example.js": b"export const example = 1;\n",
                },
            )

            result = run_policy(
                "full-format",
                "--project-root",
                str(root),
                "--implementation",
                "present",
                "--context",
                "present",
                "--language",
                "javascript",
                "--canonical-spec",
                "specs/SPEC-0001-demo.md",
                "--spec-verification-status",
                "pass",
                "--confirmation",
                "yes",
                "--repository-formatter",
                "prettier-script",
                "--repository-check-argv",
                '["prettier", "--check", "src/app.js", "docs/example.js"]',
                "--repository-write-argv",
                '["prettier", "--write", "src/app.js", "docs/example.js"]',
                "--formatter-available",
                "true",
            )

            self.assertEqual(2, result.returncode)
            self.assertEqual(
                "unscoped-formatter-command",
                json.loads(result.stdout)["reason_code"],
            )

    def test_repository_formatter_rejects_every_extra_repository_path(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT) as directory:
            root = Path(directory)
            initialize_repository(
                root,
                {
                    "specs/SPEC-0001-demo.md": CANONICAL_SPEC,
                    "src/app.js": b"export const value = 1;\n",
                    "docs/README.md": b"# Example\n",
                },
            )
            command_pairs = (
                (
                    '["prettier", "--check", ".", "docs"]',
                    '["prettier", "--write", ".", "docs"]',
                ),
                (
                    '["prettier", "--check", "src/app.js", "docs/README.md"]',
                    '["prettier", "--write", "src/app.js", "docs/README.md"]',
                ),
                (
                    '["prettier", "--check", ".", "docs/"]',
                    '["prettier", "--write", ".", "docs/"]',
                ),
                (
                    '["prettier", "--check", ".", "docs/*.md"]',
                    '["prettier", "--write", ".", "docs/*.md"]',
                ),
                (
                    json.dumps(["prettier", "--check", ".", str(root.parent)]),
                    json.dumps(["prettier", "--write", ".", str(root.parent)]),
                ),
            )

            for check_argv, write_argv in command_pairs:
                with self.subTest(check_argv=check_argv):
                    result = run_policy(
                        "full-format",
                        "--project-root",
                        str(root),
                        "--implementation",
                        "present",
                        "--context",
                        "present",
                        "--language",
                        "javascript",
                        "--canonical-spec",
                        "specs/SPEC-0001-demo.md",
                        "--spec-verification-status",
                        "pass",
                        "--confirmation",
                        "yes",
                        "--repository-formatter",
                        "prettier-script",
                        "--repository-check-argv",
                        check_argv,
                        "--repository-write-argv",
                        write_argv,
                        "--formatter-available",
                        "true",
                    )

                    self.assertEqual(2, result.returncode)
                    self.assertEqual(
                        "unscoped-formatter-command",
                        json.loads(result.stdout)["reason_code"],
                    )


class FormatterMutationGateTests(unittest.TestCase):
    def test_minimal_scaffold_is_allowed_before_formatter_availability(self) -> None:
        result = run_policy(
            "gate",
            "--operation",
            "minimal-scaffold",
            "--formatter-available",
            "false",
            "--check-status",
            "not-run",
            "--project-kind",
            "greenfield",
            "--selection-status",
            "pass",
            "--preflight-status",
            "pass",
            "--project-root",
            str(REPOSITORY_ROOT),
            "--selected-formatter",
            "ruff",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        decision = json.loads(result.stdout)
        self.assertEqual("PASS", decision["status"])
        self.assertTrue(decision["minimal_scaffold_allowed"])
        self.assertFalse(decision["product_code_allowed"])

    def test_product_code_requires_available_formatter_and_passing_check(self) -> None:
        blocked = run_policy(
            "gate",
            "--operation",
            "product-code",
            "--formatter-available",
            "false",
            "--check-status",
            "not-run",
            "--project-kind",
            "greenfield",
            "--selection-status",
            "pass",
            "--preflight-status",
            "pass",
            "--project-root",
            str(REPOSITORY_ROOT),
            "--selected-formatter",
            "ruff",
        )
        passed = run_policy(
            "gate",
            "--operation",
            "product-code",
            "--formatter-available",
            "true",
            "--check-status",
            "pass",
            "--project-kind",
            "greenfield",
            "--selection-status",
            "pass",
            "--preflight-status",
            "pass",
            "--project-root",
            str(REPOSITORY_ROOT),
            "--selected-formatter",
            "ruff",
        )

        self.assertEqual(2, blocked.returncode)
        self.assertEqual("BLOCKED", json.loads(blocked.stdout)["status"])
        self.assertEqual(0, passed.returncode, passed.stderr)
        self.assertTrue(json.loads(passed.stdout)["product_code_allowed"])

    def test_install_or_download_requires_explicit_authorization(self) -> None:
        result = run_policy(
            "gate",
            "--operation",
            "minimal-scaffold",
            "--formatter-available",
            "false",
            "--check-status",
            "not-run",
            "--project-kind",
            "greenfield",
            "--selection-status",
            "pass",
            "--preflight-status",
            "pass",
            "--project-root",
            str(REPOSITORY_ROOT),
            "--selected-formatter",
            "ruff",
            "--install-requested",
        )

        self.assertEqual(2, result.returncode)
        decision = json.loads(result.stdout)
        self.assertEqual("BLOCKED", decision["status"])
        self.assertIn("authorization", decision["reason"].casefold())

    def test_gate_rejects_missing_or_inapplicable_prior_evidence(self) -> None:
        blocked_preflight = run_policy(
            "gate",
            "--operation",
            "minimal-scaffold",
            "--formatter-available",
            "false",
            "--check-status",
            "not-run",
            "--project-kind",
            "greenfield",
            "--selection-status",
            "pass",
            "--preflight-status",
            "blocked",
            "--project-root",
            str(REPOSITORY_ROOT),
            "--selected-formatter",
            "ruff",
        )
        existing_scaffold = run_policy(
            "gate",
            "--operation",
            "minimal-scaffold",
            "--formatter-available",
            "true",
            "--check-status",
            "pass",
            "--project-kind",
            "existing",
            "--selection-status",
            "pass",
            "--preflight-status",
            "not-applicable",
            "--project-root",
            str(REPOSITORY_ROOT),
            "--selected-formatter",
            "black",
        )

        self.assertEqual(2, blocked_preflight.returncode)
        self.assertEqual(2, existing_scaffold.returncode)
        self.assertEqual("BLOCKED", json.loads(blocked_preflight.stdout)["status"])
        self.assertEqual("BLOCKED", json.loads(existing_scaffold.stdout)["status"])

    def test_product_gate_rejects_empty_formatter_identity(self) -> None:
        result = run_policy(
            "gate",
            "--operation",
            "product-code",
            "--formatter-available",
            "true",
            "--check-status",
            "pass",
            "--project-kind",
            "greenfield",
            "--selection-status",
            "pass",
            "--preflight-status",
            "pass",
            "--project-root",
            str(REPOSITORY_ROOT),
            "--selected-formatter",
            "",
        )

        self.assertEqual(2, result.returncode)
        self.assertEqual("BLOCKED", json.loads(result.stdout)["status"])


class ScaffoldPreflightIntegrationTests(unittest.TestCase):
    def test_existing_target_is_blocked_and_byte_for_byte_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "pyproject.toml"
            target.write_bytes(b"[tool.black]\nline-length = 88\n")
            before = file_hash(target)

            result = run_policy(
                "preflight",
                "--project-root",
                str(root),
                "--scaffold-path",
                "pyproject.toml",
            )

            self.assertEqual(2, result.returncode)
            decision = json.loads(result.stdout)
            self.assertEqual("BLOCKED", decision["status"])
            self.assertEqual(before, decision["collisions"][0]["sha256"])
            self.assertEqual(before, file_hash(target))

    def test_non_empty_incompatible_root_is_blocked_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "legacy.txt"
            existing.write_bytes(b"preserve me\n")
            before = file_hash(existing)

            result = run_policy(
                "preflight",
                "--project-root",
                str(root),
                "--scaffold-path",
                "pyproject.toml",
            )

            self.assertEqual(2, result.returncode)
            decision = json.loads(result.stdout)
            self.assertEqual("incompatible-existing-path", decision["reason_code"])
            self.assertEqual(before, file_hash(existing))
            self.assertFalse((root / "pyproject.toml").exists())

    def test_nested_duplicate_project_target_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo"
            root.mkdir()

            result = run_policy(
                "preflight",
                "--project-root",
                str(root),
                "--scaffold-path",
                "demo/pyproject.toml",
            )

            self.assertEqual(2, result.returncode)
            decision = json.loads(result.stdout)
            self.assertEqual("nested-project-collision", decision["reason_code"])
            self.assertFalse((root / "demo").exists())

    def test_allowed_root_entry_cannot_hide_existing_scaffold_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "src" / "legacy.py"
            existing.parent.mkdir()
            existing.write_bytes(b"VALUE = 1\n")
            before = file_hash(existing)

            result = run_policy(
                "preflight",
                "--project-root",
                str(root),
                "--scaffold-path",
                "src/new.py",
                "--allow-existing",
                "src",
            )

            self.assertEqual(2, result.returncode)
            decision = json.loads(result.stdout)
            self.assertEqual("scaffold-path-collision", decision["reason_code"])
            self.assertEqual("src", decision["collisions"][0]["path"])
            self.assertEqual(before, file_hash(existing))
            self.assertFalse((root / "src" / "new.py").exists())


class FormatterSkillIntegrationTests(unittest.TestCase):
    def test_promoted_skill_and_distribution_inventories_are_consistent(self) -> None:
        self.assertTrue((SKILL_ROOT / "SKILL.md").is_file())
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue(
            (
                REPOSITORY_ROOT / "docs" / "engineering" / "formatter-governance.md"
            ).is_file()
        )

        claude_manifest = json.loads(
            (REPOSITORY_ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn(
            "./skills/engineering/formatter-governance", claude_manifest["skills"]
        )
        compatibility = json.loads(
            (REPOSITORY_ROOT / "distribution" / "skill-compatibility.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("formatter-governance", compatibility["skills"])
        for inventory in (
            REPOSITORY_ROOT / "README.md",
            SKILLS_ROOT / "README.md",
        ):
            self.assertIn("formatter-governance", inventory.read_text(encoding="utf-8"))

    def test_delivery_workflows_invoke_one_policy_owner_without_mapping_copies(
        self,
    ) -> None:
        formatter_names = (
            "ruff",
            "prettier",
            "clang-format",
            "gofmt",
            "rustfmt",
            "dotnet format",
            "google-java-format",
        )
        for skill in ("ask-matt", "tdd", "implement", "code-review"):
            text = (SKILLS_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("/formatter-governance", text, skill)
            for formatter in formatter_names:
                self.assertNotIn(formatter, text.casefold(), f"{skill}: {formatter}")

    def test_architecture_declares_one_l2_owner_and_formatter_gate(self) -> None:
        manifest = (REPOSITORY_ROOT / "architecture" / "manifest.yaml").read_text(
            encoding="utf-8"
        )
        self.assertEqual(1, manifest.count("- id: formatter_governance_domain"))
        self.assertIn("parent: delivery_workflow_domain", manifest)
        self.assertIn("governed-change-set-lifecycle.formatter-gate", manifest)
        self.assertIn(
            "implementation_status: implemented",
            manifest.split("- id: formatter_governance_domain", 1)[1].split("- id:", 1)[
                0
            ],
        )


if __name__ == "__main__":
    unittest.main()
