import json
from pathlib import Path
import sys
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "skills/engineering/govern-modular-event-architecture/scripts")
)
from validation_layout import assess_layout


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {
            "modules": [{"id": "one"}, {"id": "two"}],
            "flows": [{"id": "journey"}],
        }
        self.policy = {
            "schema_version": 1,
            "entries": [
                {"include": ["validation/**"], "role": "validation-definition"},
                {"include": ["tests/modules/one/**"], "role": "test", "owner": "one"},
                {"include": ["tests/modules/two/**"], "role": "test", "owner": "two"},
                {"include": ["src/**"], "role": "production", "owner": "one"},
                {"include": ["specs/**"], "role": "specification"},
            ],
            "required_analyzers": ["python"],
            "references": [],
            "output_bindings": [],
            "external_resources": [],
        }

    def write(self, path, content=""):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")

    def assess(self):
        self.write("validation/layout.yaml", yaml.safe_dump(self.policy))
        return assess_layout(self.root, self.manifest)

    def test_vendor_exclusion_cannot_hide_owned_dependency(self):
        self.policy["entries"].extend(
            [
                {
                    "include": ["vendor/**"],
                    "exclude": ["vendor/adapter.py"],
                    "role": "third-party",
                    "provenance": "upstream",
                },
                {
                    "include": ["vendor/adapter.py"],
                    "role": "production",
                    "owner": "one",
                },
            ]
        )
        self.write("tests/modules/one/test_one.py", "VALUE = 1")
        self.write("vendor/adapter.py", "from tests.modules.one.test_one import VALUE")
        result = self.assess()
        self.assertEqual(result["verdict"], "FAIL")
        self.assertTrue(any(d["rule_id"] == "DEP001" for d in result["diagnostics"]))

    def test_valid_owned_test(self):
        self.write("tests/modules/one/test_one.py", "def test_one(): assert True")
        self.assertEqual(self.assess()["verdict"], "PASS")

    def test_ignored_old_evidence_is_not_hidden(self):
        self.write("specs/evidence/report.json", "{}")
        self.write(".gitignore", "specs/evidence/")
        result = self.assess()
        self.assertEqual(result["verdict"], "FAIL")
        self.assertTrue(
            any(
                d["rule_id"] == "LAY003"
                and d["expected"] == "artifacts/<kind>/<run-id>/"
                for d in result["diagnostics"]
            )
        )

    def test_unknown_and_ambiguous_roles_block(self):
        self.write("unknown.xyz")
        self.assertEqual(self.assess()["verdict"], "BLOCKED")
        self.policy["entries"].append({"include": ["unknown.xyz"], "role": "tooling"})
        self.policy["entries"].append({"include": ["unknown.xyz"], "role": "fixture"})
        self.assertEqual(self.assess()["verdict"], "BLOCKED")

    def test_private_helper_cross_use_fails(self):
        self.write("tests/modules/one/support/helper.py", "VALUE = 1")
        self.write(
            "tests/modules/two/test_two.py",
            "from tests.modules.one.support.helper import VALUE",
        )
        self.assertEqual(self.assess()["verdict"], "FAIL")

    def test_production_test_dependency_fails(self):
        self.write("tests/modules/one/test_one.py", "VALUE = 1")
        self.write("src/main.py", "from tests.modules.one.test_one import VALUE")
        self.assertEqual(self.assess()["verdict"], "FAIL")

    def test_unknown_owner_and_analyzer_block(self):
        self.write("tests/modules/one/test_one.py", "")
        self.policy["entries"][1]["owner"] = "missing"
        self.assertEqual(self.assess()["verdict"], "BLOCKED")
        self.policy["entries"][1]["owner"] = "one"
        self.policy["required_analyzers"] = ["rust"]
        self.assertEqual(self.assess()["verdict"], "BLOCKED")

    def test_terminal_test_run_is_not_a_legacy_test_root(self):
        sys.path.insert(0, str(ROOT / "skills/engineering/verification-ladder/scripts"))
        from run_storage import allocate_run, finalize_run

        self.write("architecture/manifest.yaml", json.dumps(self.manifest))
        self.policy["entries"].extend(
            [
                {"include": ["architecture/**"], "role": "metadata"},
                {"include": ["artifacts/tests/**"], "role": "run-output"},
            ]
        )
        run = allocate_run(
            self.root,
            "tests",
            metadata={
                "target": {"module": "one"},
                "scenario": "fixture",
                "tool": {"name": "fixture", "version": "1"},
                "command": ["fixture"],
                "source": {"revision": "fixture", "dirty_sha256": "0" * 64},
                "inputs": {},
            },
        )
        (run / "result.txt").write_text("observed")
        finalize_run(self.root, run, "PASS")
        result = self.assess()
        self.assertEqual(result["verdict"], "PASS", result)

    def test_flat_artifact_cannot_pass(self):
        self.policy["entries"].append(
            {"include": ["artifacts/**"], "role": "run-output"}
        )
        self.write("artifacts/report.json", "{}")
        self.assertEqual(self.assess()["verdict"], "FAIL")

    def test_dynamic_alias_cannot_hide_private_dependency(self):
        self.write("tests/modules/one/support/helper.py", "VALUE = 1")
        self.write(
            "tests/modules/two/test_two.py",
            "from importlib import import_module as load\nload('tests.modules.one.support.helper')",
        )
        result = self.assess()
        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertTrue(any(d["rule_id"] == "DEP006" for d in result["diagnostics"]))

    def test_alternate_import_root_still_checks_private_support(self):
        self.write("tests/modules/one/support/helper.py", "VALUE = 1")
        self.write(
            "tests/modules/two/test_two.py",
            "from modules.one.support.helper import VALUE",
        )
        self.assertEqual(self.assess()["verdict"], "FAIL")

    def test_unresolved_dependency_is_not_silently_external(self):
        self.write("tests/modules/one/test_one.py", "import support.secret")
        self.assertEqual(self.assess()["verdict"], "BLOCKED")

    def test_tooling_role_cannot_hide_old_tests(self):
        self.policy["entries"].append({"include": ["tools/**"], "role": "tooling"})
        self.write("tools/tests/case.py", "def test_case(): pass")
        self.assertEqual(self.assess()["verdict"], "FAIL")

    def test_shared_support_cannot_import_cases(self):
        self.policy["entries"].append(
            {"include": ["tests/support/**"], "role": "support", "owner": "one"}
        )
        self.write("tests/modules/one/test_one.py", "VALUE = 1")
        self.write(
            "tests/support/shared/helper.py",
            "from tests.modules.one.test_one import VALUE",
        )
        self.assertEqual(self.assess()["verdict"], "FAIL")

    def test_explicit_curated_fixture_is_input(self):
        self.policy["entries"][1]["exclude"] = ["tests/modules/one/support/**"]
        self.policy["entries"].append(
            {
                "include": ["tests/modules/one/support/**"],
                "role": "fixture",
                "owner": "one",
                "provenance": "curated independent reference vectors",
            }
        )
        self.write("tests/modules/one/support/reference.csv", "x,y\n1,2\n")
        self.assertEqual(self.assess()["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main()
