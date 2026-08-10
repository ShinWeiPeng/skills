import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ArchitectureSmokeTest(unittest.TestCase):
    def test_manifest_passes(self):
        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "architecture" / "check.py"),
            "--manifest",
            str(PROJECT_ROOT / "architecture" / "manifest.yaml"),
            "--format",
            "text",
        ]
        baseline = PROJECT_ROOT / "architecture" / "baseline.yaml"
        if baseline.exists():
            command.extend(["--baseline", str(baseline)])
        result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

