from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]
MODULE_PATH = PLUGIN_ROOT / "scripts" / "version_governance.py"
SPEC = importlib.util.spec_from_file_location("version_governance", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SemVerPolicyTests(unittest.TestCase):
    def test_parse_stable_semver_and_local_cachebuster(self) -> None:
        self.assertEqual((0, 5, 0, None), MODULE.parse_semver("0.5.0"))
        self.assertEqual(
            (0, 5, 0, "local-20260805-120000"),
            MODULE.parse_semver(
                "0.5.0+codex.local-20260805-120000",
                allow_cachebuster=True,
            ),
        )
        for invalid in (
            "0.5",
            "0.5.0-beta.7",
            "0.5.0-rc.1",
            "0.5.0+build.1",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    MODULE.parse_semver(invalid)

    def test_cachebuster_preserves_stable_formal_version(self) -> None:
        self.assertEqual(
            "0.5.0+codex.local-20260805-120001",
            MODULE.with_cachebuster(
                "0.5.0+codex.old-token",
                "local-20260805-120001",
            ),
        )

    def test_stable_versions_advance_by_semver_bump(self) -> None:
        self.assertEqual("1.0.0", MODULE.next_version("0.5.2", bump="major"))
        self.assertEqual("0.6.0", MODULE.next_version("0.5.2", bump="minor"))
        self.assertEqual("0.5.3", MODULE.next_version("0.5.2", bump="patch"))

    def test_only_the_authorized_prerelease_can_stabilize(self) -> None:
        self.assertEqual(
            "0.5.0",
            MODULE.next_version("0.5.0-beta.6", bump="minor"),
        )
        for unsupported in ("0.5.0-beta.5", "0.6.0-beta.1", "0.5.0-rc.1"):
            with self.subTest(unsupported=unsupported):
                with self.assertRaises(ValueError):
                    MODULE.next_version(unsupported, bump="minor")


class RepositoryPolicyTests(unittest.TestCase):
    def make_repo(
        self,
        version: str = "0.2.0",
        *,
        previous_version: str = "0.1.0",
        bump: str = "minor",
        temporary_parent: Path | None = None,
    ) -> Path:
        temporary = tempfile.TemporaryDirectory(dir=temporary_parent)
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "plugin"
        root.mkdir()
        (root / ".codex-plugin").mkdir()
        (root / ".changeset").mkdir()
        (root / "skills").mkdir()
        (root / ".codex-plugin" / "plugin.json").write_text(
            json.dumps({"name": "governed-engineering-skills", "version": version}),
            encoding="utf-8",
        )
        (root / "package.json").write_text(
            json.dumps(
                {
                    "name": "governed-engineering-skills",
                    "version": version,
                    "private": True,
                }
            ),
            encoding="utf-8",
        )
        (root / "CHANGELOG.md").write_text(
            f"# Governed Engineering Skills\n\n## {version}\n\n"
            "### Changed\n\n- Test.\n",
            encoding="utf-8",
        )
        (root / ".changeset" / "test-change.md").write_text(
            f'---\n"governed-engineering-skills": {bump}\n---\n\nTest change.\n',
            encoding="utf-8",
        )
        state = {
            "schema_version": "2.0",
            "current_version": version,
            "previous_version": previous_version,
            "bump": bump,
            "production_fingerprint": "",
            "applied_changesets": ["test-change"],
        }
        state_path = root / ".changeset" / "release-state.json"
        state_path.write_text(json.dumps(state), encoding="utf-8")
        state["production_fingerprint"] = MODULE.production_fingerprint(root)
        state_path.write_text(json.dumps(state), encoding="utf-8")
        return root

    def write_change(
        self,
        root: Path,
        change_id: str,
        bump: str,
        *,
        source_text: str,
    ) -> None:
        (root / "skills" / f"{change_id}.md").write_text(
            source_text,
            encoding="utf-8",
        )
        (root / ".changeset" / f"{change_id}.md").write_text(
            f'---\n"governed-engineering-skills": {bump}\n---\n\n'
            f"{source_text}\n",
            encoding="utf-8",
        )

    def write_intent(
        self,
        root: Path,
        *,
        bump: str,
        changesets: list[str],
        extra: dict[str, object] | None = None,
    ) -> Path:
        intent = {
            "bump": bump,
            "changesets": changesets,
            "summary": {"Changed": ["Applied governed plugin changes."]},
        }
        if extra:
            intent.update(extra)
        path = root / ".changeset" / "release-intent.json"
        path.write_text(json.dumps(intent), encoding="utf-8")
        return path

    def test_repository_versions_and_changelog_must_match(self) -> None:
        root = self.make_repo()
        self.assertEqual([], MODULE.validate_repository(root, ci=True))
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        package["version"] = "0.2.1"
        (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
        self.assertIn(
            "package.json and plugin.json versions differ",
            MODULE.validate_repository(root, ci=True),
        )

    def test_ci_rejects_cachebuster_but_local_validation_accepts_it(self) -> None:
        root = self.make_repo()
        manifest_path = root / ".codex-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] += "+codex.local-20260805-120000"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertIn(
            "formal CI version must not contain a Codex cachebuster",
            MODULE.validate_repository(root, ci=True),
        )
        self.assertEqual([], MODULE.validate_repository(root, ci=False))

    def test_missing_applied_changeset_is_rejected(self) -> None:
        root = self.make_repo()
        (root / ".changeset" / "test-change.md").unlink()
        errors = MODULE.validate_repository(root, ci=True)
        self.assertTrue(
            any("applied changeset test-change is missing" in error for error in errors)
        )

    def test_source_change_requires_a_new_changeset(self) -> None:
        root = self.make_repo()
        (root / "skills" / "changed.md").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "requires a new plugin changeset"):
            MODULE.apply_release(
                root,
                bump="patch",
                summary={"Changed": ["Changed a governed skill."]},
                changeset_ids=[],
            )

    def test_release_does_not_touch_parent_changesets_context(self) -> None:
        root = self.make_repo()
        parent_changesets = root.parent / ".changeset"
        parent_changesets.mkdir()
        parent_state = parent_changesets / "pre.json"
        parent_state.write_text('{"mode":"pre","tag":"next"}\n', encoding="utf-8")
        before = parent_state.read_bytes()
        self.write_change(root, "patch-fix", "patch", source_text="patch")
        target = MODULE.apply_release(
            root,
            bump="patch",
            summary={"Fixed": ["Fixed stable behavior."]},
            changeset_ids=["patch-fix"],
        )
        self.assertEqual("0.2.1", target)
        self.assertEqual(before, parent_state.read_bytes())

    def test_pending_intent_applies_stable_patch(self) -> None:
        root = self.make_repo()
        self.write_change(root, "patch-fix", "patch", source_text="patch")
        intent_path = self.write_intent(
            root,
            bump="patch",
            changesets=["patch-fix"],
        )
        self.assertEqual([], MODULE.validate_repository(root, ci=True))
        self.assertEqual("0.2.1", MODULE.apply_pending_intent(root))
        self.assertFalse(intent_path.exists())
        self.assertEqual([], MODULE.validate_repository(root, ci=True))

    def test_intent_bump_matches_highest_pending_changeset(self) -> None:
        root = self.make_repo()
        self.write_change(root, "patch-fix", "patch", source_text="patch")
        self.write_change(root, "minor-feature", "minor", source_text="minor")
        self.write_intent(
            root,
            bump="patch",
            changesets=["patch-fix", "minor-feature"],
        )
        self.assertIn(
            "release intent bump must match the highest pending changeset bump",
            MODULE.validate_repository(root, ci=True),
        )

    def test_intent_rejects_prerelease_promotion_fields(self) -> None:
        root = self.make_repo()
        self.write_change(root, "patch-fix", "patch", source_text="patch")
        self.write_intent(
            root,
            bump="patch",
            changesets=["patch-fix"],
            extra={"target_stage": "beta", "risk": "high"},
        )
        self.assertIn(
            "release intent contains obsolete or unknown fields: risk, target_stage",
            MODULE.validate_repository(root, ci=True),
        )

    def test_new_stable_version_archives_previous_changesets(self) -> None:
        root = self.make_repo()
        self.write_change(root, "patch-fix", "patch", source_text="patch")
        target = MODULE.apply_release(
            root,
            bump="patch",
            summary={"Fixed": ["Fixed patch behavior."]},
            changeset_ids=["patch-fix"],
        )
        self.assertEqual("0.2.1", target)
        state = json.loads(
            (root / ".changeset" / "release-state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(["patch-fix"], state["applied_changesets"])
        self.assertTrue(
            (root / ".changeset" / "applied" / "0.2.0" / "test-change.md").is_file()
        )
        self.assertEqual([], MODULE.validate_repository(root, ci=True))

    def test_authorized_beta_six_migrates_once_to_stable(self) -> None:
        root = self.make_repo(
            "0.5.0-beta.6",
            previous_version="0.5.0-beta.5",
            bump="minor",
        )
        state_path = root / ".changeset" / "release-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(
            {
                "schema_version": "1.0",
                "release_group": "0.5.0",
                "risk": "high",
                "final_rc_fingerprint": None,
                "approval": None,
                "validation_evidence": [],
                "open_blockers": [],
                "new_release_group": False,
            }
        )
        state_path.write_text(json.dumps(state), encoding="utf-8")
        state["production_fingerprint"] = MODULE.production_fingerprint(root)
        state_path.write_text(json.dumps(state), encoding="utf-8")
        self.write_change(root, "stable-policy", "minor", source_text="stable only")
        intent_path = self.write_intent(
            root,
            bump="minor",
            changesets=["stable-policy"],
        )

        self.assertEqual([], MODULE.validate_repository(root, ci=True))
        self.assertEqual("0.5.0", MODULE.apply_pending_intent(root))
        self.assertFalse(intent_path.exists())
        migrated = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "schema_version",
                "current_version",
                "previous_version",
                "bump",
                "production_fingerprint",
                "applied_changesets",
            },
            set(migrated),
        )
        self.assertEqual("2.0", migrated["schema_version"])
        self.assertEqual([], MODULE.validate_repository(root, ci=True))

    def test_tag_cli_never_moves_an_existing_stable_tag(self) -> None:
        root = self.make_repo(temporary_parent=REPOSITORY_ROOT)
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Version Test"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "version-test@example.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        first = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--root",
                str(root),
                "tag",
                "--write",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        tag = "governed-engineering-skills@0.2.0"
        tagged_commit = subprocess.run(
            ["git", "rev-list", "-n", "1", tag],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        (root / "README.md").write_text("later commit\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "later"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        second = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--root",
                str(root),
                "tag",
                "--write",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(1, second.returncode)
        self.assertIn("already points at a different commit", second.stdout)
        self.assertEqual(
            tagged_commit,
            subprocess.run(
                ["git", "rev-list", "-n", "1", tag],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
        )


class ReleaseWorkflowContractTests(unittest.TestCase):
    def _workflow(self) -> str:
        return (
            REPOSITORY_ROOT / ".github" / "workflows" / "release.yml"
        ).read_text(encoding="utf-8")

    def _release_tooling_job(self) -> str:
        workflow = self._workflow()
        job_marker = "  release-tooling-validation:"
        self.assertIn(job_marker, workflow)
        _, _, after = workflow.partition(job_marker)
        release_tooling_job, _, _ = after.partition("\n  release:")
        return release_tooling_job

    def test_release_validation_is_plugin_only(self) -> None:
        release_tooling_job = self._release_tooling_job()
        self.assertIn(
            "\n      - name: Validate governed plugin release metadata"
            "\n        run: python plugins/governed-engineering-skills/"
            "scripts/version_governance.py check",
            release_tooling_job,
        )
        for forbidden in (
            "Prepare Changesets base branch",
            "Setup Node.js",
            "npm ci",
            "npm audit",
            "npx changeset status",
        ):
            self.assertNotIn(forbidden, release_tooling_job)

    def test_root_release_tooling_is_removed(self) -> None:
        for obsolete_path in (
            REPOSITORY_ROOT / ".changeset",
            REPOSITORY_ROOT / "package.json",
            REPOSITORY_ROOT / "package-lock.json",
        ):
            self.assertFalse(obsolete_path.exists())

    def test_governed_plugin_text_files_checkout_with_lf(self) -> None:
        attributes = (REPOSITORY_ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "plugins/governed-engineering-skills/** text=auto eol=lf",
            attributes.splitlines(),
        )

    def test_version_step_applies_only_plugin_release_intent(self) -> None:
        workflow = self._workflow()
        marker = "      - name: Apply governed plugin release intent"
        self.assertIn(marker, workflow)
        _, _, after = workflow.partition(marker)
        step, _, _ = after.partition("\n      - name:")
        self.assertIn(
            "\n          python plugins/governed-engineering-skills/"
            "scripts/version_governance.py apply-intent"
            "\n          python plugins/governed-engineering-skills/"
            "scripts/version_governance.py check",
            step,
        )
        self.assertNotIn("npm", step)
        self.assertNotIn("GITHUB_TOKEN", step)

    def test_version_pull_request_selection_ignores_closed_pull_requests(self) -> None:
        workflow = self._workflow()
        marker = "      - name: Create or update the governed plugin Version Pull Request"
        self.assertIn(marker, workflow)
        _, _, after = workflow.partition(marker)
        step, _, _ = after.partition("\n      - name:")
        self.assertIn(
            'gh pr list --state open --base main --head "$branch"',
            step,
        )
        self.assertIn('branch="plugin-release/main"', step)
        self.assertIn(
            '--title "chore: version governed engineering skills"',
            step,
        )
        self.assertNotIn("changeset-release/main", step)

    def test_release_tag_is_created_only_when_missing(self) -> None:
        workflow = self._workflow()
        marker = "      - name: Create missing governed plugin release tag"
        self.assertIn(marker, workflow)
        _, _, after = workflow.partition(marker)
        step, _, _ = after.partition("\n      - name:")
        self.assertIn(
            'tag="$(python plugins/governed-engineering-skills/'
            'scripts/version_governance.py tag)"',
            step,
        )
        self.assertIn(
            'git ls-remote --exit-code --tags origin "refs/tags/$tag"',
            step,
        )
        self.assertIn('git push origin "refs/tags/$tag"', step)
        self.assertNotIn("git push origin --tags", step)

    def test_version_contract_is_stable_only(self) -> None:
        docs = (PLUGIN_ROOT / "docs" / "versioning.md").read_text(encoding="utf-8")
        rules = (PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        adr = (
            PLUGIN_ROOT
            / "architecture"
            / "decisions"
            / "ADR-0013-continuous-stable-plugin-versioning.md"
        )
        self.assertIn("stable-only", docs)
        self.assertIn("stable-only", rules)
        self.assertTrue(adr.is_file())
        for obsolete in (
            "## Maturity stages",
            "## Promotion evidence",
            "MAJOR and MINOR releases progress through beta",
            "RC promotion requires",
        ):
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, docs)


if __name__ == "__main__":
    unittest.main()
