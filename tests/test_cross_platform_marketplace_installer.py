from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CrossPlatformMarketplaceInstallerTests(unittest.TestCase):
    def test_public_installation_surface_and_provider_policy(self) -> None:
        linux_launcher = ROOT / "Install Governed Engineering Skills.sh"
        windows_launcher = ROOT / "Install Governed Engineering Skills.cmd"
        linux_installer = ROOT / "scripts" / "install-marketplace.sh"
        windows_installer = ROOT / "scripts" / "install-marketplace.ps1"
        provider_path = ROOT / "distribution" / "installer-providers.json"

        for path in (
            linux_launcher,
            windows_launcher,
            linux_installer,
            windows_installer,
            provider_path,
        ):
            self.assertTrue(path.is_file(), path)

        providers = json.loads(provider_path.read_text(encoding="utf-8"))
        self.assertEqual("governed-engineering", providers["marketplace"]["name"])
        self.assertEqual("marketplace-release", providers["marketplace"]["ref"])
        self.assertEqual(
            [".agents/plugins", "plugins/governed-engineering-skills"],
            providers["marketplace"]["sparse_paths"],
        )
        self.assertRegex(providers["codex"]["minimum_version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual("@openai/codex", providers["codex"]["package"])
        self.assertEqual("Git.Git", providers["platforms"]["windows"]["git_package"])
        self.assertEqual("winget", providers["platforms"]["windows"]["provider"])
        self.assertEqual("apt", providers["platforms"]["debian"]["provider"])
        self.assertEqual("dnf", providers["platforms"]["fedora"]["provider"])

        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual("governed-engineering-development", marketplace["name"])

        linux_text = linux_installer.read_text(encoding="utf-8")
        windows_text = windows_installer.read_text(encoding="utf-8")
        for text in (linux_text, windows_text):
            self.assertNotIn("plugin remove", text)
        self.assertIn("plugin add", linux_text)
        self.assertIn("login status", linux_text)
        self.assertIn("Invoke-CodexNative", windows_text)
        self.assertIn("Invoke-CodexChecked", windows_text)
        self.assertIn("@('login','status')", windows_text)
        self.assertIn("@('plugin','add'", windows_text)

        self.assertIn("install-marketplace.ps1", windows_launcher.read_text(encoding="utf-8"))
        self.assertIn("install-marketplace.sh", linux_launcher.read_text(encoding="utf-8"))

    def test_linux_installer_upgrades_old_codex_and_installs_marketplace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp = Path(temporary_directory)
            bin_dir = temp / "bin"
            bin_dir.mkdir()
            command_log = temp / "commands.log"
            version_file = temp / "codex-version"
            version_file.write_text("0.120.0", encoding="utf-8")

            (bin_dir / "git").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            (bin_dir / "id").write_text(
                '#!/bin/sh\n[ "$1" = "-u" ] && { printf "0\\n"; exit 0; }\nexit 1\n',
                encoding="utf-8",
            )
            (bin_dir / "npm").write_text(
                "#!/bin/sh\n"
                'printf "npm %s\\n" "$*" >> "$COMMAND_LOG"\n'
                'printf "0.147.0" > "$CODEX_VERSION_FILE"\n',
                encoding="utf-8",
            )
            (bin_dir / "codex").write_text(
                "#!/bin/sh\n"
                'printf "codex %s\\n" "$*" >> "$COMMAND_LOG"\n'
                'printf "cwd %s\\n" "$PWD" >> "$COMMAND_LOG"\n'
                'case "$*" in\n'
                '  "--version") printf "codex-cli %s\\n" "$(cat "$CODEX_VERSION_FILE")" ;;\n'
                '  "login status") exit 0 ;;\n'
                '  "plugin marketplace list --json") printf \'%s\\n\' "$MARKETPLACE_JSON"; exit "${MARKETPLACE_LIST_EXIT:-0}" ;;\n'
                '  "plugin marketplace add "*) exit 0 ;;\n'
                '  "plugin marketplace upgrade governed-engineering") exit 0 ;;\n'
                '  "plugin add governed-engineering-skills@governed-engineering") exit 0 ;;\n'
                '  "plugin list --json") printf \'{"installed":[{"pluginId":"governed-engineering-skills@governed-engineering"}]}\\n\' ;;\n'
                '  *) exit 1 ;;\n'
                "esac\n",
                encoding="utf-8",
            )
            for executable in bin_dir.iterdir():
                executable.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{bin_dir}:{environment['PATH']}",
                    "COMMAND_LOG": str(command_log),
                    "CODEX_VERSION_FILE": str(version_file),
                    "MARKETPLACE_JSON": '{"marketplaces":[]}',
                    "TMPDIR": str(temp),
                }
            )
            result = subprocess.run(
                [str(ROOT / "scripts" / "install-marketplace.sh"), "--non-interactive"],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            commands = command_log.read_text(encoding="utf-8")
            self.assertIn("npm install --global @openai/codex@0.147.0", commands)
            self.assertIn(
                "codex plugin marketplace add https://github.com/ShinWeiPeng/skills.git "
                "--ref marketplace-release --sparse .agents/plugins --sparse "
                "plugins/governed-engineering-skills",
                commands,
            )
            self.assertNotIn("plugin remove", commands)
            codex_working_directories = [
                line.removeprefix("cwd ")
                for line in commands.splitlines()
                if line.startswith("cwd ")
            ]
            self.assertTrue(codex_working_directories)
            self.assertEqual([str(temp)] * len(codex_working_directories), codex_working_directories)

            command_log.write_text("", encoding="utf-8")
            environment["MARKETPLACE_JSON"] = json.dumps(
                {
                    "marketplaces": [
                        {
                            "name": "governed-engineering",
                            "marketplaceSource": {
                                "sourceType": "git",
                                "source": "https://github.com/ShinWeiPeng/skills.git",
                            },
                        }
                    ]
                }
            )
            matching_result = subprocess.run(
                [str(ROOT / "scripts" / "install-marketplace.sh"), "--non-interactive"],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, matching_result.returncode, matching_result.stdout + matching_result.stderr)
            self.assertIn(
                "codex plugin marketplace upgrade governed-engineering",
                command_log.read_text(encoding="utf-8"),
            )

            conflict_sources = (
                {"name": "governed-engineering", "root": "/tmp/local-marketplace"},
                {
                    "name": "governed-engineering",
                    "marketplaceSource": {
                        "sourceType": "git",
                        "source": "https://github.com/example/other.git",
                    },
                },
                [
                    {
                        "name": "governed-engineering",
                        "marketplaceSource": {
                            "sourceType": "git",
                            "source": "https://github.com/ShinWeiPeng/skills.git",
                        },
                    },
                    {"name": "governed-engineering", "root": "/tmp/local-marketplace"},
                ],
            )
            for conflict_source in conflict_sources:
                with self.subTest(conflict_source=conflict_source):
                    command_log.write_text("", encoding="utf-8")
                    marketplaces = (
                        conflict_source if isinstance(conflict_source, list) else [conflict_source]
                    )
                    environment["MARKETPLACE_JSON"] = json.dumps(
                        {"marketplaces": marketplaces}
                    )
                    conflict_result = subprocess.run(
                        [str(ROOT / "scripts" / "install-marketplace.sh"), "--non-interactive"],
                        cwd=ROOT,
                        env=environment,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(1, conflict_result.returncode)
                    self.assertIn("conflicts with the required Git Marketplace", conflict_result.stderr)
                    conflict_commands = command_log.read_text(encoding="utf-8")
                    self.assertNotIn("plugin marketplace add", conflict_commands)
                    self.assertNotIn("plugin marketplace upgrade", conflict_commands)
                    self.assertNotIn("plugin marketplace remove", conflict_commands)

            command_log.write_text("", encoding="utf-8")
            environment["MARKETPLACE_JSON"] = '{"marketplaces":[]}'
            environment["MARKETPLACE_LIST_EXIT"] = "23"
            inventory_failure = subprocess.run(
                [str(ROOT / "scripts" / "install-marketplace.sh"), "--non-interactive"],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(1, inventory_failure.returncode)
            self.assertIn("Marketplace inventory could not be read", inventory_failure.stderr)
            failure_commands = command_log.read_text(encoding="utf-8")
            self.assertNotIn("plugin marketplace add", failure_commands)
            self.assertNotIn("plugin marketplace upgrade", failure_commands)


if __name__ == "__main__":
    unittest.main()
