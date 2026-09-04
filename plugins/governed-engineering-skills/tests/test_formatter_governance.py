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
        self.assertTrue((REPOSITORY_ROOT / "docs" / "engineering" / "formatter-governance.md").is_file())

        claude_manifest = json.loads(
            (REPOSITORY_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertIn("./skills/engineering/formatter-governance", claude_manifest["skills"])
        compatibility = json.loads(
            (REPOSITORY_ROOT / "distribution" / "skill-compatibility.json").read_text(encoding="utf-8")
        )
        self.assertIn("formatter-governance", compatibility["skills"])
        for inventory in (
            REPOSITORY_ROOT / "README.md",
            SKILLS_ROOT / "README.md",
        ):
            self.assertIn("formatter-governance", inventory.read_text(encoding="utf-8"))

    def test_delivery_workflows_invoke_one_policy_owner_without_mapping_copies(self) -> None:
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
        self.assertIn("implementation_status: implemented", manifest.split("- id: formatter_governance_domain", 1)[1].split("- id:", 1)[0])


if __name__ == "__main__":
    unittest.main()
