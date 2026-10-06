from __future__ import annotations
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "CLAUDE.md").is_file())
PLUGIN = ROOT / "dist/governed-engineering-skills/skills"
sys.path.insert(0, str(PLUGIN / "spec-governance/scripts"))
sys.path.insert(0, str(PLUGIN / "implement/scripts"))
sys.path.insert(0, str(PLUGIN / "govern-modular-event-architecture/scripts"))
import spec_contract as spec
from document_bundle import (
    read_spec_document,
    split_spec,
    parse_design,
    render_design,
    spec_hash,
)
from document_updates import prepare_update, resume_update, assert_complete, digest
from legacy_document_migration import migrate_spec, resume_migration
from design_sources import source_documents, generate_manifest, check_sources
from managed_delivery import execute_request
from test_spec_governance import confirmed_spec


class DocumentGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        result = spec.start_working_bundle(
            self.root,
            "payment-retry",
            confirmed_spec(status="working"),
            task_ref="task-A",
        )
        ref = result["working_spec"]
        result = spec.materialize_working_bundle(
            self.root,
            ref["working_id"],
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.relative = result["canonical_spec"]["path"]
        self.path = self.root / self.relative
        self.base = {
            "task_ref": "task-A",
            "spec": self.relative,
            "working_reference": ref["working_id"],
        }
        self.original = self.path.read_bytes()

    def authorize(self):
        r = execute_request(
            self.root,
            self.base
            | {
                "operation": "authorize",
                "instruction": "開始執行",
                "source_event_id": "user-test",
                "expected_hash": spec_hash(self.path),
            },
        )
        self.assertEqual("PASS", r["verdict"], r)

    def write_files(self, files):
        for p, c in files.items():
            target = self.root / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(c, encoding="utf-8", newline="\n")

    def test_actual_owner_and_delivery_keep_authority_after_migration(self):
        self.authorize()
        r = execute_request(self.root, self.base | {"operation": "migrate-documents"})
        self.assertEqual("PASS", r["verdict"], r)
        self.assertEqual(self.original, read_spec_document(self.path).encode())
        self.assertEqual("PASS", spec.verify_spec_path(self.path)["verdict"])
        self.assertEqual(
            "PASS",
            execute_request(self.root, self.base | {"operation": "status"})["verdict"],
        )
        self.assertEqual(
            "PASS",
            execute_request(self.root, self.base | {"operation": "migrate-documents"})[
                "verdict"
            ],
        )
        self.assertEqual(
            1, len(list((self.root / "architecture/history/specs").rglob("*.md")))
        )

    def test_changed_part_denies_old_execution_but_unrelated_file_does_not(self):
        self.authorize()
        execute_request(self.root, self.base | {"operation": "migrate-documents"})
        (self.root / "unrelated.md").write_text("other", encoding="utf-8")
        self.assertEqual(
            "PASS",
            execute_request(self.root, self.base | {"operation": "status"})["verdict"],
        )
        p = self.path.parent / self.path.name[:9] / "requirements.md"
        p.write_text(
            p.read_text(encoding="utf-8").replace("three times", "four times"),
            encoding="utf-8",
        )
        self.assertEqual(
            "BLOCKED",
            execute_request(self.root, self.base | {"operation": "status"})["verdict"],
        )

    def test_missing_part_and_undefined_format_are_located(self):
        files = split_spec(self.original.decode(), self.relative)
        self.write_files(files)
        p = self.path.parent / self.path.name[:9] / "acceptance.md"
        p.unlink()
        with self.assertRaisesRegex(ValueError, "acceptance.md"):
            read_spec_document(self.path)
        self.write_files(files)
        refs = self.path.parent / self.path.name[:9] / "references.yaml"
        refs.write_text(
            refs.read_text(encoding="utf-8").replace(
                "format_version: 1", "format_version: 9"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "unsupported"):
            read_spec_document(self.path)

    def test_design_format_rejects_double_sources_dates_and_duplicate_yaml(self):
        good = render_design("MOD-1", 1, "module", {"manifest_record": {"id": "MOD-1"}})
        self.assertEqual("MOD-1", parse_design(good, "module.md")["id"])
        for bad in [
            good.replace("| version | 1 |", "| version | 1 |\n| version | 2 |"),
            good.replace("manifest_record:", "version: 2\nmanifest_record:"),
            good.replace("  id: MOD-1", "  id: MOD-1\n  id: MOD-2"),
            good.replace("  id: MOD-1", "  id: 2026-10-02"),
        ]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_design(bad, "module.md")

    def test_failure_is_repaired_and_original_update_completed(self):
        changes = {
            "architecture/designs/a.md": {"before_sha256": None, "content": "a"},
            "architecture/designs/b.md": {"before_sha256": None, "content": "b"},
        }
        binding = {"task": "A"}
        prepare_update(
            self.root,
            "update",
            changes,
            binding=binding,
            validate_candidate=lambda files: None,
        )

        def fail(path):
            raise OSError("injected write interruption")

        with self.assertRaises(OSError):
            resume_update(
                self.root,
                "update",
                binding=binding,
                authorize=lambda b: None,
                validate_result=lambda: None,
                after_write=fail,
            )
        with self.assertRaisesRegex(ValueError, "incomplete"):
            assert_complete(self.root, changes)

        # Repair the failing writer, then verify actual desired bytes and complete the original plan.
        def verify():
            self.assertEqual("a", (self.root / "architecture/designs/a.md").read_text())
            self.assertEqual("b", (self.root / "architecture/designs/b.md").read_text())

        result = resume_update(
            self.root,
            "update",
            binding=binding,
            authorize=lambda b: None,
            validate_result=verify,
        )
        self.assertEqual("effective", result["status"])
        assert_complete(self.root, changes)
        self.assertEqual(
            "effective",
            resume_update(
                self.root,
                "update",
                binding=binding,
                authorize=lambda b: None,
                validate_result=verify,
            )["status"],
        )

    def test_recovery_retains_concurrent_edits_and_revocation(self):
        changes = {"architecture/designs/a.md": {"before_sha256": None, "content": "a"}}
        binding = {"task": "A"}
        prepare_update(
            self.root,
            "update",
            changes,
            binding=binding,
            validate_candidate=lambda files: None,
        )
        self.write_files({"architecture/designs/a.md": "someone else"})
        with self.assertRaisesRegex(ValueError, "concurrent"):
            resume_update(
                self.root,
                "update",
                binding=binding,
                authorize=lambda b: None,
                validate_result=lambda: None,
            )
        self.assertEqual(
            "someone else", (self.root / "architecture/designs/a.md").read_text()
        )

        def revoked(b):
            raise ValueError("revoked")

        with self.assertRaisesRegex(ValueError, "revoked"):
            resume_update(
                self.root,
                "update",
                binding=binding,
                authorize=revoked,
                validate_result=lambda: None,
            )

    def test_manifest_sources_preserve_all_catalogs_and_extensions(self):
        manifest = {
            "schema_version": "2.2.0",
            "modules": [{"id": "m1", "extra": {"nested": [1, 2]}}],
            "flows": [{"id": "f1"}],
            "custom_extension": {"unusual": ["kept"]},
            "implementation_design": {
                "version": 1,
                "modules": {"m1": {"groups": {"x": "kept"}}},
                "flows": {},
                "interfaces": {"i1": {"module_ref": "m1"}},
            },
        }
        files = source_documents(manifest)
        self.write_files(files)
        generated, owners = generate_manifest(self.root)
        self.assertEqual(manifest, generated)
        self.assertIn("custom_extension", owners)
        self.assertEqual([], check_sources(self.root, generated))
        generated["custom_extension"] = {}
        self.assertTrue(check_sources(self.root, generated))

    def test_fixed_design_hash_and_version_shared_between_specs(self):
        path = "architecture/designs/modules/m1.md"
        text = render_design("m1", 1, "module", {"manifest_record": {"id": "m1"}})
        self.write_files({path: text})
        refs = [
            {"id": "m1", "version": 1, "path": path, "sha256": digest(text.encode())}
        ]
        files = split_spec(self.original.decode(), self.relative, design_refs=refs)
        self.write_files(files)
        read_spec_document(self.path)
        self.write_files({path: text.replace("| version | 1 |", "| version | 2 |")})
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            read_spec_document(self.path)

    def test_crlf_migration_retains_exact_receipt_and_original_bytes(self):
        self.original = self.original.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        self.path.write_bytes(self.original)
        # Fixture owner metadata hashes normalized authored content; raw authorization binds CRLF.
        self.base["expected_hash"] = digest(self.original)
        self.authorize()
        result = execute_request(
            self.root, self.base | {"operation": "migrate-documents"}
        )
        self.assertEqual("PASS", result["verdict"], result)
        from document_bundle import read_spec_bytes

        self.assertEqual(self.original, read_spec_bytes(self.path))
        self.assertEqual(
            "PASS",
            execute_request(self.root, self.base | {"operation": "status"})["verdict"],
        )

    def test_portable_paths_reject_windows_aliases(self):
        from document_updates import safe_path

        for path in [
            ".GIT/a",
            "architecture/a.",
            "architecture/a ",
            "architecture/NUL.md",
            "architecture/a:b",
            "architecture//a",
        ]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                safe_path(self.root, path)

    def test_catalog_cannot_override_record_owned_collections(self):
        manifest = {
            "modules": [{"id": "m"}],
            "flows": [],
            "implementation_design": {
                "version": 1,
                "modules": {},
                "flows": {},
                "interfaces": {},
            },
        }
        files = source_documents(manifest)
        target = "architecture/designs/catalog/implementation_design.md"
        files[target] = render_design(
            "CAT-implementation_design",
            1,
            "catalog",
            {
                "manifest_field": "implementation_design",
                "value": {"version": 1, "modules": {"m": {"hidden": "bad"}}},
            },
        )
        self.write_files(files)
        with self.assertRaisesRegex(ValueError, "duplicate implementation"):
            generate_manifest(self.root)

    def test_empty_catalogs_are_preserved(self):
        manifest = {"modules": [], "flows": [], "custom_extension": {"version": 7}}
        self.write_files(source_documents(manifest))
        self.assertEqual(manifest, generate_manifest(self.root)[0])

    def test_history_cannot_be_overwritten(self):
        self.write_files({"architecture/history/old.md": "original"})
        with self.assertRaisesRegex(ValueError, "immutable"):
            prepare_update(
                self.root,
                "bad",
                {
                    "architecture/history/old.md": {
                        "before_sha256": digest(b"original"),
                        "content": "changed",
                    }
                },
                binding={},
                validate_candidate=lambda files: None,
            )

    def draft(self):
        r = spec.reopen_spec(
            self.root,
            self.path,
            expected_revision=1,
            reason="candidate design",
            task_ref="task-A",
        )
        self.assertEqual("PASS", r["verdict"], r)
        return r["working_spec"]

    def test_candidate_collection_confirmation_and_tampering(self):
        from document_candidates import stage_candidate
        from document_bundle import strict_yaml

        ref = self.draft()
        result = stage_candidate(
            self.root,
            ref["working_id"],
            render_design("m1", 1, "module", {"manifest_record": {"id": "m1"}}),
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        ref = result["working_spec"]
        self.assertFalse(result["product_code_allowed"])
        fixed = strict_yaml(
            (self.root / "specs/SPEC-0001/references.yaml").read_text(), "refs"
        )["designs"]
        self.assertEqual({"m1", "BASE-m1"}, {r["id"] for r in fixed})
        result = spec.materialize_working_bundle(
            self.root,
            ref["working_id"],
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.authorize()
        candidate = self.root / fixed[0]["path"]
        candidate.write_text(candidate.read_text() + "changed")
        self.assertEqual(
            "BLOCKED",
            execute_request(self.root, self.base | {"operation": "status"})["verdict"],
        )

    def test_preparation_baseline_retains_competing_same_version_bytes(self):
        from document_candidates import stage_candidate
        from document_bundle import strict_yaml
        from architecture_document_update import prepare_design_update

        self.write_files(source_documents({"modules": [{"id": "m1"}], "flows": []}))
        source = "architecture/designs/modules/m1.md"
        original = (self.root / source).read_text()
        ref = self.draft()
        candidate = original.replace("| version | 1 |", "| version | 2 |")
        stage_candidate(
            self.root,
            ref["working_id"],
            candidate,
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        refs = strict_yaml(
            (self.root / "specs/SPEC-0001/references.yaml").read_text(), "refs"
        )["designs"]
        (self.root / source).write_text(
            original.replace("id: m1", "id: m1\n  note: competing"), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "base changed"):
            prepare_design_update(
                self.root,
                "competing",
                {source: candidate},
                binding={},
                confirmed_refs=refs,
                authorize=lambda b: None,
            )
        self.assertIn("competing", (self.root / source).read_text())
        self.assertFalse(
            (self.root / "spec-governance/document-updates/competing.json").exists()
        )

    def test_historical_read_does_not_authorize_old_current_dependency(self):
        from document_bundle import assert_current_designs

        source = "architecture/designs/modules/m1.md"
        self.write_files(source_documents({"modules": [{"id": "m1"}], "flows": []}))
        original = (self.root / source).read_bytes()
        refs = [{"id": "m1", "version": 1, "path": source, "sha256": digest(original)}]
        self.write_files(
            split_spec(self.original.decode(), self.relative, design_refs=refs)
        )
        self.write_files(
            {
                f"architecture/history/designs/m1/v1-{digest(original)}.md": original.decode(),
                source: original.decode().replace("| version | 1 |", "| version | 2 |"),
            }
        )
        read_spec_document(self.path)
        with self.assertRaisesRegex(ValueError, "current design differs"):
            assert_current_designs(self.root, self.path)

    def test_owner_interruption_recovers_audit_and_replays(self):
        from unittest import mock
        import document_updates
        from legacy_document_migration import resume_owner_write
        from document_candidates import stage_candidate

        ref = self.draft()
        # Migrate first so fault injection targets the real owner transition.
        migrate_spec(
            self.root,
            self.relative,
            binding={},
            authorize=lambda b: None,
            allow_working=True,
        )
        actual = document_updates.atomic_bytes
        failed = [False]

        def fail(path, data):
            if path.name == "references.yaml" and not failed[0]:
                failed[0] = True
                raise OSError("injected owner write failure")
            return actual(path, data)

        with mock.patch.object(document_updates, "atomic_bytes", side_effect=fail):
            with self.assertRaisesRegex(OSError, "injected"):
                stage_candidate(
                    self.root,
                    ref["working_id"],
                    render_design("m1", 1, "module", {"manifest_record": {"id": "m1"}}),
                    expected_revision=ref["revision"],
                    expected_hash=ref["snapshot_hash"],
                )
        plans = [
            json.loads(p.read_text())
            for p in (self.root / "spec-governance/document-updates").glob(
                "owner-*.json"
            )
        ]
        operation = next(
            p["operation_id"] for p in plans if p["status"] == "incomplete"
        )
        result = resume_owner_write(self.root, operation, ref["working_id"])
        self.assertEqual("PASS", result["verdict"])
        self.assertEqual("continuous", result["working_spec"]["continuity"])
        again = resume_owner_write(self.root, operation, ref["working_id"])
        self.assertEqual(
            result["working_spec"]["snapshot_hash"],
            again["working_spec"]["snapshot_hash"],
        )
        self.assertFalse(again["product_code_allowed"])
        (
            self.root
            / ("spec-governance/document-updates/" + operation + "-owner-complete.json")
        ).unlink()
        lost_response = resume_owner_write(self.root, operation, ref["working_id"])
        self.assertEqual(
            again["working_spec"]["snapshot_hash"],
            lost_response["working_spec"]["snapshot_hash"],
        )

    def test_case_aliases_rejected_before_effects(self):
        with self.assertRaisesRegex(ValueError, "duplicate portable"):
            prepare_update(
                self.root,
                "aliases",
                {
                    "architecture/M.md": {"before_sha256": None, "content": "a"},
                    "architecture/m.md": {"before_sha256": None, "content": "b"},
                },
                binding={},
                validate_candidate=lambda f: None,
            )
        self.assertFalse((self.root / "architecture/M.md").exists())
        with self.assertRaisesRegex(ValueError, "duplicate portable"):
            source_documents({"modules": [{"id": "m"}, {"id": "M"}]})

    def test_recovery_attempt_storage_remains_bounded(self):
        prepare_update(
            self.root,
            "bounded",
            {"architecture/a.md": {"before_sha256": None, "content": "a"}},
            binding={},
            validate_candidate=lambda f: None,
        )
        plan = self.root / "spec-governance/document-updates/bounded.json"
        state = json.loads(plan.read_text())
        state["attempts"] = [{"attempt": i} for i in range(64)]
        plan.write_text(json.dumps(state))
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, "exhausted"):
                resume_update(
                    self.root,
                    "bounded",
                    binding={},
                    authorize=lambda b: None,
                    validate_result=lambda: None,
                )
            self.assertEqual(64, len(json.loads(plan.read_text())["attempts"]))

    def test_confirmed_design_update_and_product_application_end_to_end(self):
        import importlib.util, yaml
        from document_candidates import stage_candidate
        from render_architecture import render_documents

        loader = importlib.util.spec_from_file_location(
            "document_fixture",
            ROOT
            / "tests/modules/governance_workflow_domain/architecture/test_architecture.py",
        )
        fixture_module = importlib.util.module_from_spec(loader)
        loader.loader.exec_module(fixture_module)
        manifest = fixture_module.valid_manifest()
        self.write_files(source_documents(manifest))
        self.write_files(
            {"architecture/manifest.yaml": yaml.safe_dump(manifest, sort_keys=False)}
            | {
                "architecture/" + p.as_posix(): c
                for p, c in render_documents(manifest).items()
            }
        )
        source = "architecture/designs/modules/feature.md"
        old = parse_design((self.root / source).read_text(), source)
        old["data"]["manifest_record"]["description"]["purpose"] = (
            "Updated feature responsibility"
        )
        candidate = render_design("feature", 2, "module", old["data"])
        ref = self.draft()
        result = stage_candidate(
            self.root,
            ref["working_id"],
            candidate,
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        ref = result["working_spec"]
        confirmed = spec.materialize_working_bundle(
            self.root,
            ref["working_id"],
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", confirmed["verdict"], confirmed)
        self.authorize()
        result = execute_request(
            self.root,
            self.base
            | {
                "operation": "update-documents",
                "operation_id": "formal-feature",
                "sources": {source: candidate},
            },
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertEqual("effective", result["update_status"])
        self.assertEqual([], check_sources(self.root, generate_manifest(self.root)[0]))
        folder = self.root / "src/feature"
        folder.mkdir(parents=True)
        result = execute_request(
            self.root,
            self.base
            | {
                "operation": "apply",
                "patch": {
                    "path": "src/feature/feature.c",
                    "before_sha256": None,
                    "content": "int feature(void){return 1;}\n",
                },
            },
        )
        self.assertEqual("PASS", result["verdict"], result)
        replay = execute_request(
            self.root,
            self.base
            | {
                "operation": "resume-design-documents",
                "operation_id": "formal-feature",
            },
        )
        self.assertEqual("PASS", replay["verdict"], replay)

    def test_unindexed_candidate_cannot_become_effective(self):
        from document_candidates import stage_candidate
        from document_bundle import strict_yaml
        from architecture_document_update import prepare_design_update

        self.write_files(source_documents({"modules": [], "flows": []}))
        ref = self.draft()
        candidate = render_design(
            "unlisted", 1, "module", {"manifest_record": {"id": "unlisted"}}
        )
        stage_candidate(
            self.root,
            ref["working_id"],
            candidate,
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        refs = strict_yaml(
            (self.root / "specs/SPEC-0001/references.yaml").read_text(), "refs"
        )["designs"]
        source = "architecture/designs/modules/unlisted.md"
        with self.assertRaisesRegex(ValueError, "absent from the final collection"):
            prepare_design_update(
                self.root,
                "unindexed",
                {source: candidate},
                binding={},
                confirmed_refs=refs,
                authorize=lambda b: None,
            )
        self.assertFalse((self.root / source).exists())
        self.assertFalse(
            (self.root / "spec-governance/document-updates/unindexed.json").exists()
        )

    def test_file_operations_require_current_design_dependency(self):
        source = "architecture/designs/modules/m1.md"
        self.write_files(source_documents({"modules": [{"id": "m1"}], "flows": []}))
        from document_candidates import stage_candidate

        original = (self.root / source).read_text()
        ref = self.draft()
        candidate = original.replace("| version | 1 |", "| version | 2 |")
        result = stage_candidate(
            self.root,
            ref["working_id"],
            candidate,
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        ref = result["working_spec"]
        result = spec.materialize_working_bundle(
            self.root,
            ref["working_id"],
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.authorize()
        self.write_files(
            {source: candidate.replace("| version | 2 |", "| version | 3 |")}
        )
        target = self.root / "program.txt"
        target.write_text("retained")
        for action in ("mkdir", "move", "delete"):
            with self.subTest(action=action):
                request = self.base | {
                    "operation": "file-operation",
                    "action": action,
                    "path": "new-dir" if action == "mkdir" else "program.txt",
                    "destination": "moved.txt",
                    "before_sha256": digest(target.read_bytes()),
                }
                result = execute_request(self.root, request)
                self.assertEqual("BLOCKED", result["verdict"], result)
                self.assertIn("current design differs", result["reason"])
        self.assertEqual("retained", target.read_text())
        self.assertFalse((self.root / "new-dir").exists())
        self.assertFalse((self.root / "moved.txt").exists())

    def test_recovery_audit_interruption_resumes_from_original_entry(self):
        from unittest import mock
        import document_updates
        from legacy_document_migration import resume_owner_write
        from document_candidates import stage_candidate

        ref = self.draft()
        migrate_spec(
            self.root,
            self.relative,
            binding={},
            authorize=lambda b: None,
            allow_working=True,
        )
        actual = document_updates.atomic_bytes
        first = [False]

        def fail_initial(path, data):
            if path.name == "references.yaml" and not first[0]:
                first[0] = True
                raise OSError("injected initial failure")
            return actual(path, data)

        with mock.patch.object(
            document_updates, "atomic_bytes", side_effect=fail_initial
        ):
            with self.assertRaisesRegex(OSError, "initial"):
                stage_candidate(
                    self.root,
                    ref["working_id"],
                    render_design("m1", 1, "module", {"manifest_record": {"id": "m1"}}),
                    expected_revision=ref["revision"],
                    expected_hash=ref["snapshot_hash"],
                )
        plans = [
            json.loads(p.read_text())
            for p in (self.root / "spec-governance/document-updates").glob(
                "owner-*.json"
            )
        ]
        operation = next(
            p["operation_id"] for p in plans if p["status"] == "incomplete"
        )

        def fail_audit(path, data):
            result = actual(path, data)
            if (
                path.name == "discussion.md"
                and b'"event_type":"document-recovery"' in data
            ):
                raise OSError("injected audit failure after effect")
            return result

        with mock.patch.object(
            document_updates, "atomic_bytes", side_effect=fail_audit
        ):
            with self.assertRaisesRegex(OSError, "audit"):
                resume_owner_write(self.root, operation, ref["working_id"])
        self.assertTrue(
            (
                self.root
                / (
                    "spec-governance/document-updates/"
                    + operation
                    + "-audit-child.json"
                )
            ).exists()
        )
        result = resume_owner_write(self.root, operation, ref["working_id"])
        self.assertEqual("PASS", result["verdict"])
        self.assertEqual("continuous", result["working_spec"]["continuity"])
        again = resume_owner_write(self.root, operation, ref["working_id"])
        self.assertEqual(
            result["working_spec"]["snapshot_hash"],
            again["working_spec"]["snapshot_hash"],
        )

    def test_collection_rebase_preserves_confirmed_order_or_rejects(self):
        import yaml
        from document_candidates import stage_candidate
        from document_bundle import strict_yaml
        from architecture_document_update import prepare_design_update

        self.write_files(
            source_documents({"modules": [{"id": "m1"}, {"id": "m2"}], "flows": []})
        )
        index_path = "architecture/designs/index.yaml"
        original = strict_yaml((self.root / index_path).read_text(), "index")
        candidate = yaml.safe_dump(
            original
            | {"version": 2, "documents": list(reversed(original["documents"]))},
            sort_keys=False,
        )
        ref = self.draft()
        stage_candidate(
            self.root,
            ref["working_id"],
            candidate,
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        refs = strict_yaml(
            (self.root / "specs/SPEC-0001/references.yaml").read_text(), "refs"
        )["designs"]
        extra = "architecture/designs/catalog/extra.md"
        self.write_files(
            {
                extra: render_design(
                    "CAT-extra", 1, "catalog", {"manifest_field": "extra", "value": {}}
                ),
                index_path: yaml.safe_dump(
                    original
                    | {"version": 2, "documents": original["documents"] + [extra]},
                    sort_keys=False,
                ),
            }
        )
        live = (self.root / index_path).read_bytes()
        with self.assertRaisesRegex(ValueError, "order conflicts"):
            prepare_design_update(
                self.root,
                "order-conflict",
                {index_path: candidate},
                binding={},
                confirmed_refs=refs,
                authorize=lambda b: None,
            )
        self.assertEqual(live, (self.root / index_path).read_bytes())
        self.assertFalse(
            (
                self.root / "spec-governance/document-updates/order-conflict.json"
            ).exists()
        )

    def test_completion_preserves_split_document_source(self):
        migrate_spec(self.root, self.relative, binding={}, authorize=lambda b: None)
        result = spec.mark_spec_implemented(
            self.path,
            {"AC-001": "PASS host fixture"},
            spec_review_passed=True,
            authorized=True,
            validation_assessor=lambda *a, **k: {"verdict": "PASS"},
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertTrue(
            self.path.read_bytes().startswith(b"<!-- document-bundle:1 -->")
        )
        projection = read_spec_document(self.path)
        self.assertIn("status: implemented", projection)
        self.assertIn(
            "PASS host fixture",
            (self.root / "specs/SPEC-0001/acceptance.md").read_text(),
        )

    def test_file_operation_validation_runs_outside_document_lock(self):
        import subprocess

        self.authorize()
        child = "import sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nfrom document_updates import document_lock\nwith document_lock(Path(sys.argv[2])): print('locked')\n"
        assessments = []

        def assessor(root, path, **kwargs):
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    child,
                    str(PLUGIN / "spec-governance/scripts"),
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            assessments.append(result)
            return {
                "verdict": "PASS"
                if result.returncode == 0 and "locked" in result.stdout
                else "BLOCKED"
            }

        result = execute_request(
            self.root,
            self.base
            | {"operation": "file-operation", "action": "mkdir", "path": "created"},
            validation_assessor=assessor,
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertTrue(assessments)
        self.assertTrue((self.root / "created").is_dir())


if __name__ == "__main__":
    unittest.main()
