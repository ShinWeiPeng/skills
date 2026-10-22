"""The clean checkout remains usable without tracking local validation state."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / ".github/scripts/prepare_validation.py"


class PreparationTests(unittest.TestCase):
    def setUp(self):
        cache = ROOT / ".test-tmp"
        cache.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=cache)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / ".github/validation"
        self.source.mkdir(parents=True)
        for name in ("layout.yaml", "verification-ladder.yaml"):
            (self.source / name).write_bytes(b"schema_version: 1\n")

    def run_prepare(self):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(self.root)],
            capture_output=True,
            text=True,
        )

    def test_clean_checkout_and_repeated_updates(self):
        self.assertEqual(0, self.run_prepare().returncode)
        (self.source / "layout.yaml").write_bytes(b"schema_version: 1\nentries: []\n")
        self.assertEqual(0, self.run_prepare().returncode)
        self.assertEqual(
            (self.source / "layout.yaml").read_bytes(),
            (self.root / "validation/layout.yaml").read_bytes(),
        )

    def test_human_edit_is_preserved_before_any_other_update(self):
        self.assertEqual(0, self.run_prepare().returncode)
        (self.root / "validation/verification-ladder.yaml").write_bytes(b"my edit\n")
        (self.source / "layout.yaml").write_bytes(b"changed upstream\n")
        self.assertNotEqual(0, self.run_prepare().returncode)
        self.assertEqual(
            b"my edit\n",
            (self.root / "validation/verification-ladder.yaml").read_bytes(),
        )
        self.assertEqual(
            b"schema_version: 1\n", (self.root / "validation/layout.yaml").read_bytes()
        )

    def test_existing_equivalent_configuration_is_adopted(self):
        (self.root / "validation").mkdir()
        (self.root / "validation/layout.yaml").write_bytes(b"schema_version: 1\n")
        self.assertEqual(0, self.run_prepare().returncode)

    def test_redirected_destination_preserves_external_files(self):
        outside = self.root / "outside"
        outside.mkdir()
        sentinel = outside / "layout.yaml"
        sentinel.write_bytes(b"private\n")
        link = self.root / "validation"
        if os.name == "nt":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                capture_output=True,
            )
            self.assertEqual(0, result.returncode)
        else:
            link.symlink_to(outside, target_is_directory=True)
        try:
            self.assertNotEqual(0, self.run_prepare().returncode)
            self.assertEqual(b"private\n", sentinel.read_bytes())
        finally:
            if os.name == "nt":
                link.rmdir()
            else:
                link.unlink()
