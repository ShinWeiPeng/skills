import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "CLAUDE.md").is_file())
sys.path.insert(0, str(ROOT / "skills/engineering/implement/scripts"))
from managed_delivery import execute_request


TEST_TEMP_ROOT = ROOT / ".test-tmp" / "document-writes"
TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class DocumentWriteTests(unittest.TestCase):
    def test_document_write_needs_no_execution_receipt_or_compatibility(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            result = execute_request(
                root,
                {
                    "operation": "write-document",
                    "patch": {
                        "path": "docs/plan.md",
                        "before_sha256": None,
                        "content": "# Draft\n",
                    },
                },
            )
            self.assertEqual("PASS", result["verdict"], result)
            self.assertFalse(result["product_code_allowed"])
            self.assertEqual("# Draft\n", (root / "docs/plan.md").read_text())
            self.assertFalse(list((root / "spec-governance").glob("*execution*")))

    def test_document_writer_rejects_product_or_operational_skill_targets(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            for path in (
                "src/app.py",
                "docs/run.py",
                "skills/engineering/implement/SKILL.md",
                "config/runtime.yaml",
                "../outside.md",
            ):
                with self.subTest(path=path):
                    target = root / path
                    if not path.startswith(".."):
                        target.parent.mkdir(parents=True, exist_ok=True)
                    result = execute_request(
                        root,
                        {
                            "operation": "write-document",
                            "patch": {
                                "path": path,
                                "before_sha256": None,
                                "content": "replacement",
                            },
                        },
                    )
                    self.assertEqual("BLOCKED", result["verdict"], result)
                    if not path.startswith(".."):
                        self.assertFalse(target.exists())

    def test_stale_document_base_preserves_concurrent_content(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            target = root / "README.md"
            target.write_text("another writer")
            result = execute_request(
                root,
                {
                    "operation": "write-document",
                    "patch": {
                        "path": "README.md",
                        "before_sha256": hashlib.sha256(b"old").hexdigest(),
                        "content": "mine",
                    },
                },
            )
            self.assertEqual("BLOCKED", result["verdict"])
            self.assertEqual("another writer", target.read_text())

    def test_architecture_design_document_is_not_a_product_execution_grant(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            (root / "architecture").mkdir()
            result = execute_request(
                root,
                {
                    "operation": "write-document",
                    "patch": {
                        "path": "architecture/manifest.yaml",
                        "before_sha256": None,
                        "content": "schema_version: 2.2.0\n",
                    },
                },
            )
            self.assertEqual("PASS", result["verdict"], result)
            self.assertFalse(result["product_code_allowed"])
