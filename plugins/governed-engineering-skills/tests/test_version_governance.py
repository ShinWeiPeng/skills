from __future__ import annotations

import importlib.util
import json
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
    def test_parse_semver_and_cachebuster(self) -> None:
        self.assertEqual((0, 2, 0, "beta", 1, None), MODULE.parse_semver("0.2.0-beta.1"))
        self.assertEqual(
            (0, 2, 0, "beta", 1, "local-20260731-120000"),
            MODULE.parse_semver(
                "0.2.0-beta.1+codex.local-20260731-120000",
                allow_cachebuster=True,
            ),
        )
        with self.assertRaises(ValueError):
            MODULE.parse_semver("0.2")
        with self.assertRaises(ValueError):
            MODULE.parse_semver("0.2.0-beta.0")
        with self.assertRaises(ValueError):
            MODULE.parse_semver(
                "0.2.0-beta.1+codex.local-20260731-120000",
                allow_cachebuster=False,
            )
        self.assertEqual(
            "0.2.0-beta.1+codex.local-20260731-120001",
            MODULE.with_cachebuster(
                "0.2.0-beta.1+codex.old-token",
                "local-20260731-120001",
            ),
        )

    def test_minor_release_progression(self) -> None:
        self.assertEqual(
            "0.2.0-beta.1",
            MODULE.next_version("0.1.0", bump="minor", target_stage="beta", risk="high"),
        )
        self.assertEqual(
            "0.2.0-beta.2",
            MODULE.next_version("0.2.0-beta.1", bump="minor", target_stage="beta", risk="high"),
        )
        self.assertEqual(
            "0.2.0-rc.1",
            MODULE.next_version("0.2.0-beta.2", bump="minor", target_stage="rc", risk="high"),
        )
        self.assertEqual(
            "0.2.0",
            MODULE.next_version("0.2.0-rc.1", bump="minor", target_stage="stable", risk="high"),
        )

    def test_rc_feature_change_starts_next_release_group(self) -> None:
        self.assertEqual(
            "0.3.0-beta.1",
            MODULE.next_version("0.2.0-rc.1", bump="minor", target_stage="beta", risk="high"),
        )

    def test_explicit_minor_prerelease_group_transition(self) -> None:
        self.assertEqual(
            "0.3.0-beta.1",
            MODULE.next_version(
                "0.2.0-beta.1",
                bump="minor",
                target_stage="beta",
                risk="high",
                new_release_group=True,
            ),
        )
        for current, bump, stage in (
            ("0.2.0", "minor", "beta"),
            ("0.2.0-beta.1", "patch", "beta"),
            ("0.2.0-beta.1", "minor", "stable"),
        ):
            with self.subTest(current=current, bump=bump, stage=stage):
                with self.assertRaises(ValueError):
                    MODULE.next_version(
                        current,
                        bump=bump,
                        target_stage=stage,
                        risk="high",
                        new_release_group=True,
                    )

    def test_patch_policy(self) -> None:
        self.assertEqual(
            "0.2.1",
            MODULE.next_version("0.2.0", bump="patch", target_stage="stable", risk="low"),
        )
        self.assertEqual(
            "0.2.1-rc.1",
            MODULE.next_version("0.2.0", bump="patch", target_stage="rc", risk="high"),
        )
        with self.assertRaises(ValueError):
            MODULE.next_version("0.2.0", bump="patch", target_stage="stable", risk="high")

    def test_stable_promotion_requires_matching_rc_evidence(self) -> None:
        errors = MODULE.validate_promotion_evidence(
            "0.2.0-rc.1",
            "0.2.0",
            risk="high",
            current_fingerprint="sha256:one",
            final_rc_fingerprint="sha256:two",
            approval=None,
            validation_evidence=[],
        )
        self.assertIn("stable promotion fingerprint differs from final RC", errors)
        self.assertIn("stable promotion requires non-AI approval", errors)
        self.assertIn("stable promotion requires reinstall and new-task evidence", errors)

    def test_stable_promotion_accepts_complete_evidence(self) -> None:
        errors = MODULE.validate_promotion_evidence(
            "0.2.0-rc.1",
            "0.2.0",
            risk="high",
            current_fingerprint="sha256:same",
            final_rc_fingerprint="sha256:same",
            approval={
                "approved_by": "Hugo Peng",
                "approval_reference": "review-42",
                "approved_at": "2026-07-31",
            },
            validation_evidence=[
                {"kind": "reinstall", "reference": "VAL-REINSTALL-42"},
                {"kind": "new-task", "reference": "VAL-NEW-TASK-42"},
            ],
        )
        self.assertEqual([], errors)


class RepositoryPolicyTests(unittest.TestCase):
    def make_repo(self, version: str = "0.2.0-beta.1") -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "plugin"
        root.mkdir()
        (root / ".codex-plugin").mkdir()
        (root / ".changeset").mkdir()
        (root / "release").mkdir()
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
            f"# Governed Engineering Skills\n\n## {version}\n\n### Changed\n\n- Test.\n",
            encoding="utf-8",
        )
        (root / ".changeset" / "release-state.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "current_version": version,
                    "previous_version": "0.1.0",
                    "release_group": "0.2.0",
                    "bump": "minor",
                    "risk": "high",
                    "production_fingerprint": MODULE.production_fingerprint(root),
                    "final_rc_fingerprint": None,
                    "applied_changesets": ["test-change"],
                    "approval": None,
                    "validation_evidence": [],
                    "open_blockers": [],
                }
            ),
            encoding="utf-8",
        )
        (root / ".changeset" / "test-change.md").write_text(
            '---\n"governed-engineering-skills": minor\n---\n\nTest change.\n',
            encoding="utf-8",
        )
        state_path = root / ".changeset" / "release-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["production_fingerprint"] = MODULE.production_fingerprint(root)
        state_path.write_text(json.dumps(state), encoding="utf-8")
        return root

    def test_repository_versions_and_changelog_must_match(self) -> None:
        root = self.make_repo()
        self.assertEqual([], MODULE.validate_repository(root, ci=True))
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        package["version"] = "0.2.0-beta.2"
        (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
        self.assertIn(
            "package.json and plugin.json versions differ",
            MODULE.validate_repository(root, ci=True),
        )

    def test_ci_rejects_cachebuster_but_local_validation_accepts_it(self) -> None:
        root = self.make_repo()
        manifest_path = root / ".codex-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] += "+codex.local-20260731-120000"
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
        self.assertTrue(any("applied changeset test-change is missing" in error for error in errors))

    def test_source_change_requires_a_new_changeset(self) -> None:
        root = self.make_repo()
        (root / "skills" / "changed.md").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "requires a new plugin changeset"):
            MODULE.apply_promotion(
                root,
                bump="minor",
                target_stage="beta",
                risk="high",
                summary={"Changed": ["Changed a governed skill."]},
                changeset_ids=[],
                approval=None,
                validation_evidence=[],
            )

    def test_plugin_promotion_does_not_touch_parent_changesets_context(self) -> None:
        root = self.make_repo()
        parent_changesets = root.parent / ".changeset"
        parent_changesets.mkdir()
        parent_state = parent_changesets / "pre.json"
        parent_state.write_text('{"mode":"pre","tag":"next"}\n', encoding="utf-8")
        before = parent_state.read_bytes()
        target = MODULE.apply_promotion(
            root,
            bump="minor",
            target_stage="beta",
            risk="high",
            summary={"Changed": ["Refined beta validation."]},
            changeset_ids=[],
            approval=None,
            validation_evidence=[],
        )
        self.assertEqual("0.2.0-beta.2", target)
        self.assertEqual(before, parent_state.read_bytes())

    def test_one_dot_zero_requires_accepted_human_approved_adr(self) -> None:
        errors = MODULE.validate_promotion_evidence(
            "1.0.0-rc.1",
            "1.0.0",
            risk="high",
            current_fingerprint="sha256:same",
            final_rc_fingerprint="sha256:same",
            approval={
                "approved_by": "Hugo Peng",
                "approval_reference": "release-review",
                "approved_at": "2026-07-31",
            },
            validation_evidence=[
                {"kind": "reinstall", "reference": "VAL-REINSTALL"},
                {"kind": "new-task", "reference": "VAL-NEW-TASK"},
            ],
            compatibility_adr={"status": "proposed"},
        )
        self.assertIn("1.0.0 requires an accepted compatibility ADR", errors)

    def test_stable_promotion_rejects_open_blockers_before_writing(self) -> None:
        root = self.make_repo("0.2.0-rc.1")
        state_path = root / ".changeset" / "release-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(
            {
                "previous_version": "0.2.0-beta.1",
                "final_rc_fingerprint": MODULE.production_fingerprint(root),
                "production_fingerprint": MODULE.production_fingerprint(root),
                "validation_evidence": [
                    {"kind": kind, "reference": f"VAL-{kind}"}
                    for kind in MODULE.RC_EVIDENCE_KINDS
                ],
                "open_blockers": ["BLOCK-1"],
            }
        )
        state_path.write_text(json.dumps(state), encoding="utf-8")
        before = (root / "package.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "zero open blockers"):
            MODULE.apply_promotion(
                root,
                bump="minor",
                target_stage="stable",
                risk="high",
                summary={"Changed": ["Promoted the release candidate."]},
                changeset_ids=[],
                approval={
                    "approved_by": "Hugo Peng",
                    "approval_reference": "release-review",
                    "approved_at": "2026-07-31",
                },
                validation_evidence=[
                    {"kind": "reinstall", "reference": "VAL-REINSTALL"},
                    {"kind": "new-task", "reference": "VAL-NEW-TASK"},
                ],
            )
        self.assertEqual(before, (root / "package.json").read_bytes())

    def test_pending_changeset_is_applied_by_shared_version_flow(self) -> None:
        root = self.make_repo()
        (root / "skills" / "changed.md").write_text("changed", encoding="utf-8")
        (root / ".changeset" / "beta-fix.md").write_text(
            '---\n"governed-engineering-skills": minor\n---\n\nRefine beta behavior.\n',
            encoding="utf-8",
        )
        intent_path = root / ".changeset" / "release-intent.json"
        intent_path.write_text(
            json.dumps(
                {
                    "bump": "minor",
                    "target_stage": "beta",
                    "risk": "high",
                    "changesets": ["beta-fix"],
                    "summary": {"Changed": ["Refined beta behavior."]},
                    "approval": None,
                    "validation_evidence": [],
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual([], MODULE.validate_repository(root, ci=True))
        self.assertEqual("0.2.0-beta.2", MODULE.apply_pending_intent(root))
        self.assertFalse(intent_path.exists())
        self.assertEqual([], MODULE.validate_repository(root, ci=True))

    def test_same_prerelease_group_accepts_historical_changesets_with_different_bumps(
        self,
    ) -> None:
        root = self.make_repo()
        (root / "skills" / "patch.md").write_text("patch", encoding="utf-8")
        (root / ".changeset" / "patch-fix.md").write_text(
            '---\n"governed-engineering-skills": patch\n---\n\nFix beta behavior.\n',
            encoding="utf-8",
        )

        target = MODULE.apply_promotion(
            root,
            bump="patch",
            target_stage="beta",
            risk="high",
            summary={"Fixed": ["Fixed beta behavior."]},
            changeset_ids=["patch-fix"],
            approval=None,
            validation_evidence=[],
        )

        self.assertEqual("0.2.0-beta.2", target)
        state = json.loads(
            (root / ".changeset" / "release-state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(["test-change", "patch-fix"], state["applied_changesets"])
        self.assertEqual([], MODULE.validate_repository(root, ci=True))

    def test_explicit_new_release_group_is_applied_by_shared_version_flow(self) -> None:
        root = self.make_repo()
        (root / "skills" / "changed.md").write_text("changed", encoding="utf-8")
        (root / ".changeset" / "new-minor.md").write_text(
            '---\n"governed-engineering-skills": minor\n---\n\nStart a new minor beta.\n',
            encoding="utf-8",
        )
        intent_path = root / ".changeset" / "release-intent.json"
        intent_path.write_text(
            json.dumps(
                {
                    "bump": "minor",
                    "target_stage": "beta",
                    "risk": "high",
                    "new_release_group": True,
                    "changesets": ["new-minor"],
                    "summary": {"Changed": ["Started a new minor beta."]},
                    "approval": None,
                    "validation_evidence": [],
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual([], MODULE.validate_repository(root, ci=True))
        self.assertEqual("0.3.0-beta.1", MODULE.apply_pending_intent(root))
        state = json.loads(
            (root / ".changeset" / "release-state.json").read_text(encoding="utf-8")
        )
        self.assertTrue(state["new_release_group"])
        self.assertEqual(["new-minor"], state["applied_changesets"])
        self.assertTrue((root / ".changeset" / "applied" / "0.2.0" / "test-change.md").is_file())
        self.assertFalse(intent_path.exists())
        self.assertEqual([], MODULE.validate_repository(root, ci=True))

    def test_new_release_group_archives_previous_changesets(self) -> None:
        root = self.make_repo("0.2.0")
        (root / "skills" / "patch.md").write_text("patch", encoding="utf-8")
        (root / ".changeset" / "patch-fix.md").write_text(
            '---\n"governed-engineering-skills": patch\n---\n\nFix patch behavior.\n',
            encoding="utf-8",
        )
        target = MODULE.apply_promotion(
            root,
            bump="patch",
            target_stage="stable",
            risk="low",
            summary={"Fixed": ["Fixed patch behavior."]},
            changeset_ids=["patch-fix"],
            approval=None,
            validation_evidence=[],
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


class ReleaseWorkflowContractTests(unittest.TestCase):
    def _release_tooling_job(self) -> str:
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "release.yml"
        ).read_text(encoding="utf-8")
        job_marker = "  release-tooling-validation:"
        self.assertIn(job_marker, workflow)
        _, _, workflow_after_job_marker = workflow.partition(job_marker)
        release_tooling_job, _, _ = workflow_after_job_marker.partition("\n  release:")
        return release_tooling_job

    def test_changesets_validation_checkout_fetches_full_history(self) -> None:
        release_tooling_job = self._release_tooling_job()
        checkout_marker = "      - name: Checkout"
        self.assertIn(checkout_marker, release_tooling_job)
        _, _, workflow_after_checkout_marker = release_tooling_job.partition(
            checkout_marker
        )
        checkout_step, _, _ = workflow_after_checkout_marker.partition(
            "\n      - name:"
        )

        self.assertIn(
            "\n        with:\n          fetch-depth: 0",
            checkout_step,
        )

    def test_changesets_validation_materializes_main_for_pull_requests(self) -> None:
        release_tooling_job = self._release_tooling_job()

        self.assertIn(
            "\n      - name: Prepare Changesets base branch"
            "\n        if: github.event_name == 'pull_request'"
            "\n        run: git branch --track main origin/main",
            release_tooling_job,
        )

    def test_version_pull_request_skips_pending_changeset_validation(self) -> None:
        release_tooling_job = self._release_tooling_job()
        step_marker = "      - name: Validate root Changesets release plan"
        self.assertIn(step_marker, release_tooling_job)
        _, _, workflow_after_marker = release_tooling_job.partition(step_marker)
        validation_step, _, _ = workflow_after_marker.partition("\n      - name:")

        self.assertIn(
            "\n        if: github.event_name != 'pull_request'"
            " || github.head_ref != 'changeset-release/main'",
            validation_step,
        )

    def test_governed_plugin_text_files_checkout_with_lf(self) -> None:
        attributes_path = REPOSITORY_ROOT / ".gitattributes"
        self.assertTrue(attributes_path.is_file())
        attributes = attributes_path.read_text(encoding="utf-8")

        self.assertIn(
            "plugins/governed-engineering-skills/** text=auto eol=lf",
            attributes.splitlines(),
        )

    def test_version_step_provides_github_token_to_changesets(self) -> None:
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "release.yml"
        ).read_text(encoding="utf-8")
        step_marker = "      - name: Prepare root and plugin version files"
        self.assertIn(step_marker, workflow)
        _, _, workflow_after_marker = workflow.partition(step_marker)
        version_step, _, _ = workflow_after_marker.partition("\n      - name:")

        self.assertIn(
            "\n        env:\n          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}",
            version_step,
        )


if __name__ == "__main__":
    unittest.main()
