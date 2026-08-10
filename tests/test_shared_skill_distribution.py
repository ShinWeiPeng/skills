from __future__ import annotations

import importlib.util
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ASSEMBLER = REPO_ROOT / "scripts" / "assemble_plugin.py"
VALIDATOR = REPO_ROOT / "scripts" / "validate_distribution.py"
RELEASE_VALIDATOR = REPO_ROOT / "scripts" / "validate_personal_marketplace_release.py"
PLUGIN_SHELL = REPO_ROOT / "plugins" / "governed-engineering-skills"
DIST_PLUGIN = REPO_ROOT / "dist" / "governed-engineering-skills"
PROMOTED_ROOTS = (
    REPO_ROOT / "skills" / "engineering",
    REPO_ROOT / "skills" / "productivity",
)


def load_assembler():
    spec = importlib.util.spec_from_file_location("assemble_plugin", ASSEMBLER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load assembly entrypoint")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_distribution", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load distribution validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_release_validator():
    spec = importlib.util.spec_from_file_location("validate_personal_marketplace_release", RELEASE_VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load personal Marketplace release validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SharedSkillDistributionTests(unittest.TestCase):
    def test_plugin_shell_contains_no_tracked_skill_tree(self) -> None:
        self.assertFalse((PLUGIN_SHELL / "skills").exists())

    def test_removed_local_installer_does_not_exist(self) -> None:
        self.assertFalse((REPO_ROOT / "Install Governed Engineering Skills.cmd").exists())
        self.assertFalse((PLUGIN_SHELL / "scripts" / "install-local.ps1").exists())
        self.assertFalse((PLUGIN_SHELL / "tests" / "test_install_local.ps1").exists())

    def test_formal_architecture_is_repository_scoped(self) -> None:
        manifest = REPO_ROOT / "architecture" / "manifest.yaml"
        self.assertTrue(manifest.is_file())
        self.assertFalse((PLUGIN_SHELL / "architecture").exists())
        text = manifest.read_text(encoding="utf-8")
        self.assertNotIn("local_install_adapter", text)

    def test_algorithm_records_reference_existing_source_and_test_paths(self) -> None:
        for record in sorted((REPO_ROOT / "architecture" / "algorithms").glob("ALG-*.md")):
            metadata = record.read_text(encoding="utf-8").split("## Problem", 1)[0]
            referenced_paths = [
                line.split("`", 2)[1]
                for line in metadata.splitlines()
                if "`" in line and ("path" in line.casefold() or line.lstrip().startswith("- `"))
            ]
            for relative in referenced_paths:
                self.assertTrue(
                    (REPO_ROOT / relative).exists(),
                    f"{record.name} references a missing source/test path: {relative}",
                )
    def test_all_promoted_skills_have_unique_names(self) -> None:
        names = [
            path.name
            for root in PROMOTED_ROOTS
            for path in root.iterdir()
            if path.is_dir()
        ]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(28, len(names))

    def test_clean_assembly_is_deterministic_and_detects_drift(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = Path(first_dir) / "plugin"
            second = Path(second_dir) / "plugin"
            first_result = module.assemble(REPO_ROOT, first)
            second_result = module.assemble(REPO_ROOT, second)
            self.assertEqual(first_result["content_fingerprint"], second_result["content_fingerprint"])
            self.assertEqual(first_result["files"], second_result["files"])
            changed = first / "skills" / "ask-matt" / "SKILL.md"
            changed.write_text(changed.read_text(encoding="utf-8") + "\ndrift\n", encoding="utf-8")
            with self.assertRaises(module.DistributionError):
                module.validate_artifact(REPO_ROOT, first)

    def test_validation_rejects_absent_missing_and_extra_artifacts(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as output_dir:
            artifact = Path(output_dir) / "plugin"
            with self.assertRaises(module.DistributionError):
                module.validate_artifact(REPO_ROOT, artifact)
            module.assemble(REPO_ROOT, artifact)
            removed = artifact / "skills" / "grilling" / "SKILL.md"
            removed.unlink()
            with self.assertRaises(module.DistributionError):
                module.validate_artifact(REPO_ROOT, artifact)
            module.assemble(REPO_ROOT, artifact)
            (artifact / "unexpected.txt").write_text("extra", encoding="utf-8")
            with self.assertRaises(module.DistributionError):
                module.validate_artifact(REPO_ROOT, artifact)

    def test_current_artifact_can_be_reassembled_safely(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as output_dir:
            artifact = Path(output_dir) / "plugin"
            first = module.assemble(REPO_ROOT, artifact)
            second = module.assemble(REPO_ROOT, artifact)
            self.assertEqual(first["content_fingerprint"], second["content_fingerprint"])

    def test_versioned_artifact_passes_its_own_integration_validation(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as output_dir:
            temporary_root = Path(output_dir)
            repository = temporary_root / "repository"
            shell = repository / "plugins" / "governed-engineering-skills"
            shutil.copytree(PLUGIN_SHELL, shell)
            for promoted_root in PROMOTED_ROOTS:
                shutil.copytree(
                    promoted_root,
                    repository / promoted_root.relative_to(REPO_ROOT),
                )
            subprocess.run(["git", "init", "--quiet"], cwd=repository, check=True)
            subprocess.run(["git", "add", "-A"], cwd=repository, check=True)

            applied = subprocess.run(
                [
                    sys.executable,
                    str(shell / "scripts" / "version_governance.py"),
                    "apply-intent",
                ],
                cwd=repository,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, applied.returncode, applied.stdout + applied.stderr)

            artifact = temporary_root / "governed-engineering-skills"
            module.assemble(repository, artifact)
            integrated = subprocess.run(
                [
                    sys.executable,
                    str(artifact / "scripts" / "validate_integration.py"),
                ],
                cwd=repository,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                0,
                integrated.returncode,
                integrated.stdout + integrated.stderr,
            )

    def test_assembly_removes_claude_only_invocation_metadata(self) -> None:
        module = load_assembler()
        source = (REPO_ROOT / "skills" / "engineering" / "implement" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("disable-model-invocation: true", source)
        with tempfile.TemporaryDirectory() as output_dir:
            artifact = Path(output_dir) / "plugin"
            module.assemble(REPO_ROOT, artifact)
            assembled = (artifact / "skills" / "implement" / "SKILL.md").read_text(encoding="utf-8")
            metadata = (artifact / "skills" / "implement" / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertNotIn("disable-model-invocation", assembled)
            self.assertIn("allow_implicit_invocation: false", metadata)

    def test_assembly_preserves_invocation_examples_in_skill_body(self) -> None:
        module = load_assembler()
        source = (
            "---\nname: fixture\ndisable-model-invocation: true\n---\n"
            "Body example:\ndisable-model-invocation: true\n"
        )
        assembled = module.strip_claude_invocation_frontmatter(source)
        frontmatter, body = assembled.split("---", 2)[1:]
        self.assertNotIn("disable-model-invocation", frontmatter)
        self.assertIn("disable-model-invocation: true", body)

    def test_marketplace_publication_tree_uses_assembled_identity(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as output_dir:
            artifact = Path(output_dir) / "plugin"
            result = module.assemble(REPO_ROOT, artifact)
            publication_root = Path(output_dir) / "marketplace"
            publication = module.write_marketplace_publication(
                REPO_ROOT,
                artifact,
                result,
                publication_root,
                source_commit="a" * 40,
                previous_publication_commit="none:first-publication",
            )
            payload = json.loads(publication.read_text(encoding="utf-8"))
            self.assertEqual(result["plugin_name"], payload["artifact"]["name"])
            self.assertEqual(result["version"], payload["artifact"]["version"])
            self.assertEqual(result["content_fingerprint"], payload["artifact"]["content_fingerprint"])
            self.assertEqual("https://github.com/ShinWeiPeng/skills.git", payload["repository_url"])
            self.assertEqual("marketplace-release", payload["git_ref"])
            self.assertEqual(
                [".agents/plugins", "plugins/governed-engineering-skills"],
                payload["sparse_paths"],
            )
            self.assertIn("installation_steps", payload)
            self.assertIn("rollback", payload)
            self.assertIn("evidence_checklist", payload)
            catalog = json.loads(
                (publication_root / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                "./plugins/governed-engineering-skills",
                catalog["plugins"][0]["source"]["path"],
            )
            self.assertTrue(
                (publication_root / "plugins" / "governed-engineering-skills" / "artifact-inventory.json").is_file()
            )
            schema = json.loads((REPO_ROOT / "distribution" / "personal-marketplace-publication.schema.json").read_text(encoding="utf-8"))
            module.validate_marketplace_publication(publication_root, payload, schema)
            (publication_root / "plugins" / "governed-engineering-skills" / "README.md").write_text(
                "drift", encoding="utf-8"
            )
            with self.assertRaises(module.DistributionError):
                module.validate_marketplace_publication(publication_root, payload, schema)

    def test_marketplace_publication_schema_rejects_malformed_identity_fields(self) -> None:
        module = load_assembler()
        schema = json.loads((REPO_ROOT / "distribution" / "personal-marketplace-publication.schema.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as output_dir:
            artifact = Path(output_dir) / "plugin"
            result = module.assemble(REPO_ROOT, artifact)
            publication_root = Path(output_dir) / "marketplace"
            payload = json.loads(
                module.write_marketplace_publication(
                    REPO_ROOT,
                    artifact,
                    result,
                    publication_root,
                    source_commit="a" * 40,
                    previous_publication_commit="none:first-publication",
                ).read_text(encoding="utf-8")
            )
            payload["artifact"] = {}
            payload["git_ref"] = "main"
            payload["sparse_paths"] = ["../outside"]
            with self.assertRaises(module.DistributionError):
                module.validate_marketplace_publication(publication_root, payload, schema)

    def test_marketplace_publication_is_git_tree_deterministic(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as output_dir:
            root = Path(output_dir)
            artifact = root / "plugin"
            result = module.assemble(REPO_ROOT, artifact)
            tree_ids = []
            for name in ("first", "second"):
                publication_root = root / name
                module.write_marketplace_publication(
                    REPO_ROOT,
                    artifact,
                    result,
                    publication_root,
                    source_commit="a" * 40,
                    previous_publication_commit="none:first-publication",
                )
                subprocess.run(["git", "init", "--quiet"], cwd=publication_root, check=True)
                subprocess.run(["git", "add", "-A"], cwd=publication_root, check=True)
                tree_ids.append(
                    subprocess.run(
                        ["git", "write-tree"],
                        cwd=publication_root,
                        text=True,
                        capture_output=True,
                        check=True,
                    ).stdout.strip()
                )
            self.assertEqual(tree_ids[0], tree_ids[1])

    def test_marketplace_publication_refuses_unrelated_output(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as output_dir:
            root = Path(output_dir)
            artifact = root / "plugin"
            result = module.assemble(REPO_ROOT, artifact)
            unrelated = root / "marketplace"
            unrelated.mkdir()
            (unrelated / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(module.DistributionError):
                module.write_marketplace_publication(
                    REPO_ROOT,
                    artifact,
                    result,
                    unrelated,
                    source_commit="a" * 40,
                    previous_publication_commit="none:first-publication",
                )
            self.assertEqual("keep", (unrelated / "keep.txt").read_text(encoding="utf-8"))

    def test_assembly_refuses_to_replace_an_unrelated_existing_directory(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as output_dir:
            unrelated = Path(output_dir) / "unrelated"
            unrelated.mkdir()
            (unrelated / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(module.DistributionError):
                module.assemble(REPO_ROOT, unrelated)
            self.assertEqual("keep", (unrelated / "keep.txt").read_text(encoding="utf-8"))

    def test_default_output_path_still_requires_artifact_identity(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as root_dir:
            root = Path(root_dir)
            default_output = root / "dist" / module.PLUGIN_NAME
            default_output.mkdir(parents=True)
            (default_output / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(module.DistributionError):
                module._assert_replaceable_output(root, default_output)
            self.assertEqual("keep", (default_output / "keep.txt").read_text(encoding="utf-8"))

    def test_repository_distribution_validation_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR), "--repo-root", str(REPO_ROOT)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_dist_is_ignored(self) -> None:
        ignored = subprocess.run(
            ["git", "check-ignore", "dist/governed-engineering-skills/.probe"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, ignored.returncode, ignored.stdout + ignored.stderr)

    def test_release_workflow_assembles_before_consuming_the_artifact(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        release_job = workflow[workflow.index("\n  release:\n"):]
        assemble_at = release_job.index("assemble_plugin.py assemble")
        validate_at = release_job.index("assemble_plugin.py validate")
        version_at = release_job.index("version_governance.py")
        publish_at = release_job.index("Publish the generated personal Marketplace branch")
        evidence_at = release_job.index("validate_personal_marketplace_release.py")
        self.assertLess(assemble_at, validate_at)
        self.assertLess(validate_at, version_at)
        self.assertLess(version_at, publish_at)
        self.assertLess(publish_at, evidence_at)
        self.assertIn('git worktree add --detach "$publication_worktree"', release_job)
        self.assertIn(
            'git -C "$publication_worktree" rm -rf --ignore-unmatch .',
            release_job,
        )
        self.assertIn('git -C "$publication_worktree" add -A', release_job)
        self.assertIn('"$remote_tag_commit" != "$GITHUB_SHA"', release_job)
        self.assertIn('exit 1', release_job)
        self.assertIn('--branch-commit "$branch_commit"', release_job)
        self.assertNotIn("Workspace publication", release_job)

    def test_marketplace_publication_can_populate_an_empty_orphan_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            publication_worktree = root / "publication-worktree"

            def run_git(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["git", *args],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            initialized = run_git("init", "--initial-branch", "main", str(repository))
            self.assertEqual(0, initialized.returncode, initialized.stdout + initialized.stderr)
            (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
            staged = run_git("-C", str(repository), "add", "seed.txt")
            self.assertEqual(0, staged.returncode, staged.stdout + staged.stderr)
            committed = run_git(
                "-C",
                str(repository),
                "-c",
                "user.name=Marketplace Test",
                "-c",
                "user.email=marketplace@example.invalid",
                "commit",
                "-m",
                "seed",
            )
            self.assertEqual(0, committed.returncode, committed.stdout + committed.stderr)
            detached = run_git(
                "-C",
                str(repository),
                "worktree",
                "add",
                "--detach",
                str(publication_worktree),
            )
            self.assertEqual(0, detached.returncode, detached.stdout + detached.stderr)
            orphaned = run_git(
                "-C",
                str(publication_worktree),
                "switch",
                "--orphan",
                "marketplace-release-publication",
            )
            self.assertEqual(0, orphaned.returncode, orphaned.stdout + orphaned.stderr)

            cleaned = run_git(
                "-C",
                str(publication_worktree),
                "rm",
                "-rf",
                "--ignore-unmatch",
                ".",
            )
            self.assertEqual(0, cleaned.returncode, cleaned.stdout + cleaned.stderr)
            (publication_worktree / "plugins" / "governed-engineering-skills").mkdir(
                parents=True
            )
            (publication_worktree / "publication-record.json").write_text(
                "{}\n", encoding="utf-8"
            )
            (
                publication_worktree
                / "plugins"
                / "governed-engineering-skills"
                / "artifact-inventory.json"
            ).write_text("{}\n", encoding="utf-8")
            published = run_git("-C", str(publication_worktree), "add", "-A")
            self.assertEqual(0, published.returncode, published.stdout + published.stderr)
            tracked = run_git("-C", str(publication_worktree), "ls-files")
            self.assertEqual(0, tracked.returncode, tracked.stdout + tracked.stderr)
            self.assertEqual(
                [
                    "plugins/governed-engineering-skills/artifact-inventory.json",
                    "publication-record.json",
                ],
                tracked.stdout.splitlines(),
            )

    def test_release_acceptance_is_blocked_while_personal_evidence_is_pending(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RELEASE_VALIDATOR), "--repo-root", str(REPO_ROOT)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(1, completed.returncode)
        self.assertIn("still pending", completed.stdout)

    def test_complete_personal_marketplace_evidence_accepts_only_the_current_artifact(self) -> None:
        assembler = load_assembler()
        module = load_release_validator()
        with tempfile.TemporaryDirectory() as output_dir:
            temporary_root = Path(output_dir)
            artifact = temporary_root / "artifact"
            inventory = assembler.assemble(REPO_ROOT, artifact)
            distribution = temporary_root / "distribution"
            evidence_root = distribution / "evidence"
            evidence_root.mkdir(parents=True)
            (distribution / "skill-compatibility.json").write_text(
                (REPO_ROOT / "distribution" / "skill-compatibility.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (distribution / "personal-marketplace-release-evidence.schema.json").write_text(
                (REPO_ROOT / "distribution" / "personal-marketplace-release-evidence.schema.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            invocations = {}
            for surface in ("chatgpt-work-web", "codex"):
                invocations[surface] = {}
                for bucket, skill in (("engineering", "codebase-design"), ("productivity", "writing-great-skills")):
                    relative = Path("distribution") / "evidence" / f"{surface}-{bucket}.txt"
                    file_path = temporary_root / relative
                    file_path.write_text(f"auditable {surface} {bucket} result", encoding="utf-8")
                    invocations[surface][bucket] = {
                        "skill": skill,
                        "evidence": {
                            "kind": "repository-file",
                            "path": relative.as_posix(),
                            "sha256": "sha256:" + hashlib.sha256(file_path.read_bytes()).hexdigest(),
                        },
                    }
            publication_root = temporary_root / "marketplace"
            publication_path = assembler.write_marketplace_publication(
                REPO_ROOT,
                artifact,
                inventory,
                publication_root,
                source_commit="a" * 40,
                previous_publication_commit="none:first-publication",
            )
            publication = json.loads(publication_path.read_text(encoding="utf-8"))
            evidence = {
                "schema_version": "1.0.0",
                "status": "accepted",
                "marketplace": {
                    "repository_url": publication["repository_url"],
                    "git_ref": publication["git_ref"],
                    "branch_commit": "b" * 40,
                    "source_commit": publication["source_commit"],
                    "source_tag": publication["source_tag"],
                    "marketplace_path": publication["marketplace_path"],
                    "sparse_paths": publication["sparse_paths"],
                },
                "artifact": {
                    "name": inventory["plugin_name"],
                    "version": inventory["version"],
                    "content_fingerprint": inventory["content_fingerprint"],
                },
                "invocations": invocations,
            }
            path = temporary_root / "release-evidence.json"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            self.assertEqual(
                [],
                module.validate(
                    temporary_root, path, artifact, publication_path, branch_commit="b" * 40
                ),
            )
            branch_errors = module.validate(
                temporary_root, path, artifact, publication_path, branch_commit="c" * 40
            )
            self.assertTrue(any("checked-out branch commit" in error for error in branch_errors))
            evidence["unexpected"] = True
            path.write_text(json.dumps(evidence), encoding="utf-8")
            schema_errors = module.validate(
                temporary_root, path, artifact, publication_path, branch_commit="b" * 40
            )
            self.assertTrue(any("schema" in error for error in schema_errors), schema_errors)
            del evidence["unexpected"]
            evidence["marketplace"]["git_ref"] = "main"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            errors = module.validate(
                temporary_root, path, artifact, publication_path, branch_commit="b" * 40
            )
            self.assertTrue(any("git_ref" in error for error in errors), errors)
            evidence["marketplace"]["git_ref"] = "marketplace-release"
            evidence["invocations"]["codex"]["engineering"]["evidence"]["sha256"] = "sha256:" + "0" * 64
            path.write_text(json.dumps(evidence), encoding="utf-8")
            errors = module.validate(
                temporary_root, path, artifact, publication_path, branch_commit="b" * 40
            )
            self.assertTrue(any("checksum does not match" in error for error in errors), errors)

    def test_git_status_is_unchanged_by_default_assembly(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=REPO_ROOT, text=True, capture_output=True, check=True,
        ).stdout
        subprocess.run(
            [sys.executable, str(ASSEMBLER), "assemble"],
            cwd=REPO_ROOT, text=True, capture_output=True, check=True,
        )
        after = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=REPO_ROOT, text=True, capture_output=True, check=True,
        ).stdout
        self.assertEqual(before, after)

    def test_invocation_metadata_is_consistent(self) -> None:
        for root in PROMOTED_ROOTS:
            for skill_dir in (path for path in root.iterdir() if path.is_dir()):
                skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                metadata = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
                user_invoked = "disable-model-invocation: true" in skill.split("---", 2)[1]
                codex_false = "allow_implicit_invocation: false" in metadata
                codex_true = "allow_implicit_invocation: true" in metadata
                self.assertEqual(user_invoked, codex_false, skill_dir.name)
                self.assertFalse(codex_true, skill_dir.name)

    def test_invocation_metadata_contract_rejects_both_mismatch_directions(self) -> None:
        module = load_assembler()
        with self.assertRaises(module.DistributionError):
            module.classify_invocation_mode(
                "---\nname: fixture\ndisable-model-invocation: true\n---\n",
                "policy: {}\n",
                skill_name="manual-without-codex-policy",
            )
        with self.assertRaises(module.DistributionError):
            module.classify_invocation_mode(
                "---\nname: fixture\n---\n",
                "policy:\n  allow_implicit_invocation: false\n",
                skill_name="automatic-with-manual-policy",
            )
        with self.assertRaises(module.DistributionError):
            module.classify_invocation_mode(
                "---\nname: fixture\n---\n",
                "policy:\n  allow_implicit_invocation: true\n",
                skill_name="automatic-with-redundant-policy",
            )

    def test_assembled_plugin_preserves_manual_only_codex_policy_matrix(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as output_dir:
            artifact = Path(output_dir) / "plugin"
            module.assemble(REPO_ROOT, artifact)
            for root in PROMOTED_ROOTS:
                for skill_dir in (path for path in root.iterdir() if path.is_dir()):
                    source_skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                    source_metadata = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
                    mode = module.classify_invocation_mode(
                        source_skill,
                        source_metadata,
                        skill_name=skill_dir.name,
                    )
                    assembled_skill = (artifact / "skills" / skill_dir.name / "SKILL.md").read_text(encoding="utf-8")
                    assembled_metadata = (artifact / "skills" / skill_dir.name / "agents" / "openai.yaml").read_text(encoding="utf-8")
                    assembled_frontmatter = assembled_skill.split("---", 2)[1]
                    self.assertNotIn("disable-model-invocation", assembled_frontmatter)
                    self.assertEqual(
                        mode == "manual",
                        "allow_implicit_invocation: false" in assembled_metadata,
                        skill_dir.name,
                    )

    def test_agents_points_fresh_tasks_to_ask_matt_without_becoming_plugin_authority(self) -> None:
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("ask-matt", agents)
        self.assertIn("every software-engineering request", agents)
        ask_matt = (REPO_ROOT / "skills" / "engineering" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("bundled contracts", ask_matt)
        self.assertIn("Never require", ask_matt)

    def test_assembled_plugin_routes_without_repository_agents_file(self) -> None:
        module = load_assembler()
        with tempfile.TemporaryDirectory() as output_dir:
            root = Path(output_dir)
            artifact = root / "plugin"
            project = root / "consumer"
            project.mkdir()
            self.assertFalse((project / "AGENTS.md").exists())
            subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True, text=True)
            module.assemble(REPO_ROOT, artifact)
            self.assertTrue((artifact / "skills" / "ask-matt" / "SKILL.md").is_file())
            completed = subprocess.run(
                [
                    sys.executable,
                    str(artifact / "skills" / "engineering-risk-routing" / "scripts" / "guided_workflow_router.py"),
                    "--prompt",
                    "add a payment retry feature",
                    "--project-root",
                    str(project),
                    "--branch",
                    "unrelated",
                    "--json",
                ],
                cwd=artifact,
                text=True,
                capture_output=True,
                check=False,
                encoding="utf-8",
            )
            result = json.loads(completed.stdout)
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertEqual("grill-me", result["selected_skill"])
            self.assertEqual("to-spec", result["resume_target"])

    def test_readme_invocation_groups_match_skill_metadata(self) -> None:
        root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        reference = root_readme[root_readme.index("## Reference"):]
        sections = {
            "engineering": reference[reference.index("### Engineering"):reference.index("### Productivity")],
            "productivity": reference[reference.index("### Productivity"):],
        }
        for root in PROMOTED_ROOTS:
            bucket = root.name
            user_section, model_section = sections[bucket].split("**Model-invoked**", 1)
            bucket_readme = (root / "README.md").read_text(encoding="utf-8")
            bucket_user, bucket_model = bucket_readme.split("## Model-invoked", 1)
            for skill_dir in (path for path in root.iterdir() if path.is_dir()):
                skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                user_invoked = "disable-model-invocation: true" in skill.split("---", 2)[1]
                root_link = f"./skills/{bucket}/{skill_dir.name}/SKILL.md"
                bucket_link = f"./{skill_dir.name}/SKILL.md"
                self.assertIn(root_link, user_section if user_invoked else model_section, skill_dir.name)
                self.assertIn(bucket_link, bucket_user if user_invoked else bucket_model, skill_dir.name)

    def test_compatibility_scan_rejects_host_dependent_cross_product_skill(self) -> None:
        module = load_validator()
        compatibility = json.loads(
            (REPO_ROOT / "distribution" / "skill-compatibility.json").read_text(encoding="utf-8")
        )["skills"]
        compatibility["code-review"] = {
            "classification": "cross-product",
            "reason": "negative fixture",
            "host_dependencies": [],
        }
        skills = module.promoted_skills(REPO_ROOT)
        errors = module.compatibility_dependency_errors(compatibility, skills)
        self.assertTrue(any("code-review" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
