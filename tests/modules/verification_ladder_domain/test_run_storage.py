import concurrent.futures
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "skills/engineering/verification-ladder/scripts"))
from run_storage import allocate_run, finalize_run, validate_run, operation


class RunStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "architecture").mkdir()
        (self.root / "architecture/manifest.yaml").write_text(
            json.dumps({"modules": [{"id": "example"}]})
        )

    def allocate(self, identity="sample"):
        return allocate_run(
            self.root,
            "tests",
            identity,
            {
                "target": {"module": "example"},
                "scenario": "unit",
                "tool": {"name": "unittest", "version": "3"},
                "command": ["python", "-m", "unittest"],
                "source": {"revision": "abc", "dirty_sha256": "0" * 64},
                "inputs": {},
            },
        )

    def test_operation_lock_covers_terminal_publication(self):
        from unittest.mock import patch
        import run_storage

        path = self.allocate()
        original = run_storage.os.link

        def publish(source, destination):
            self.assertTrue((path / ".operation.lock").exists())
            with self.assertRaises(ValueError):
                with operation(self.root, path):
                    self.fail("finalization must reject any continuation")
            return original(source, destination)

        with (
            operation(self.root, path),
            patch.object(run_storage.os, "link", side_effect=publish),
        ):
            finalize_run(self.root, path, "PASS")
        self.assertFalse((path / ".operation.lock").exists())
        self.assertEqual(
            validate_run(self.root, path / "manifest.json")["outcome"], "PASS"
        )

    def test_terminal_published_between_precheck_and_lock_is_rejected(self):
        from unittest.mock import patch

        path = self.allocate()
        original = Path.open

        def delayed_open(file, *args, **kwargs):
            if file == path / ".operation.lock":
                finalize_run(self.root, path, "PASS")
            return original(file, *args, **kwargs)

        with patch.object(Path, "open", delayed_open), self.assertRaises(ValueError):
            with operation(self.root, path):
                self.fail("terminal run admitted")
        self.assertEqual(
            validate_run(self.root, path / "manifest.json")["outcome"], "PASS"
        )

    def test_reclassified_vendor_source_changes_snapshot(self):
        from run_storage import source_snapshot

        (self.root / "validation").mkdir()
        (self.root / "vendor").mkdir()
        (self.root / "vendor/adapter.py").write_text("value = 1")
        entries = [
            {"include": ["architecture/**", "validation/**"], "role": "metadata"},
            {
                "include": ["vendor/**"],
                "exclude": ["vendor/adapter.py"],
                "role": "third-party",
            },
            {"include": ["vendor/adapter.py"], "role": "production"},
        ]
        (self.root / "validation/layout.yaml").write_text(
            json.dumps({"entries": entries})
        )
        before = source_snapshot(self.root)
        (self.root / "vendor/adapter.py").write_text("value = 2")
        self.assertNotEqual(before, source_snapshot(self.root))

    def test_incomplete_and_terminal_outcomes(self):
        for outcome in ("PASS", "FAIL", "BLOCKED"):
            path = self.allocate(outcome)
            with self.assertRaises(ValueError):
                validate_run(self.root, path / "manifest.json")
            (path / "result.txt").write_text(outcome)
            finalize_run(self.root, path, outcome)
            self.assertEqual(
                validate_run(self.root, path / "manifest.json")["outcome"], outcome
            )
            with self.assertRaises((ValueError, FileExistsError)):
                finalize_run(self.root, path, "PASS")

    def test_duplicate_allocation_is_exclusive(self):
        def attempt(_):
            try:
                self.allocate()
                return True
            except FileExistsError:
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(attempt, range(8))), 1)

    def test_tamper_and_added_output_rejected(self):
        path = self.allocate()
        (path / "report.txt").write_text("original")
        finalize_run(self.root, path, "PASS")
        (path / "report.txt").write_text("changed")
        with self.assertRaises(ValueError):
            validate_run(self.root, path / "manifest.json")

    def test_escape_and_missing_metadata_rejected(self):
        with self.assertRaises(ValueError):
            self.allocate("../escape")
        with self.assertRaises(ValueError):
            allocate_run(self.root, "tests", "bad", {})

    def test_parallel_distinct_runs_preserve_contents(self):
        def run(i):
            path = self.allocate(str(i))
            (path / "report.txt").write_text(str(i))
            finalize_run(self.root, path, "PASS")
            return validate_run(self.root, path / "manifest.json")["run_id"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(set(pool.map(run, range(8))), {str(i) for i in range(8)})

    def test_added_file_invalidates_terminal_evidence(self):
        path = self.allocate()
        finalize_run(self.root, path, "PASS")
        (path / "extra.log").write_text("unbound")
        with self.assertRaises(ValueError):
            validate_run(self.root, path / "manifest.json")

    def test_finalization_is_exclusive(self):
        path = self.allocate()

        def finalize(_):
            try:
                finalize_run(self.root, path, "PASS")
                return True
            except (ValueError, FileExistsError):
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(finalize, range(8))), 1)
        self.assertEqual(
            validate_run(self.root, path / "manifest.json")["outcome"], "PASS"
        )

    def test_unknown_target_does_not_allocate(self):
        (self.root / "architecture/manifest.yaml").write_text('{"modules": []}')
        with self.assertRaises(ValueError):
            self.allocate()
        self.assertFalse((self.root / "artifacts/tests/sample").exists())

    def test_interrupted_finalize_remains_incomplete(self):
        from unittest.mock import patch
        import run_storage

        path = self.allocate()
        with patch.object(
            run_storage.os, "link", side_effect=OSError("injected publish failure")
        ):
            with self.assertRaises(OSError):
                finalize_run(self.root, path, "PASS")
        with self.assertRaises(ValueError):
            validate_run(self.root, path / "manifest.json")
        with self.assertRaises(FileExistsError):
            finalize_run(self.root, path, "PASS")


if __name__ == "__main__":
    unittest.main()
