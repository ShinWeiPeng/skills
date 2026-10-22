"""Linux desktop entry and terminal wrapper contracts with isolated user directories."""

import ctypes
import ctypes.util
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[5]
PACKAGE = ROOT / "doc-coauthoring"


class DesktopInstallTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".test-tmp").mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(
            prefix="doc-desktop-", dir=ROOT / ".test-tmp"
        )
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.package = self.root / "package space 中文 & $value"
        shutil.copytree(
            PACKAGE, self.package, ignore=shutil.ignore_patterns("dist", "__pycache__")
        )
        self.wrapper = self.package / "scripts/install-gui.sh"

    def shell(self):
        shell = (
            Path("C:/Program Files/Git/bin/bash.exe")
            if os.name == "nt"
            else shutil.which("sh")
        )
        if not shell or not Path(shell).is_file():
            self.skipTest("POSIX shell unavailable")
        return str(shell)

    def run_wrapper(self, *args, enter="\n"):
        env = dict(os.environ)
        env["PATH"] = (
            str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        )
        return subprocess.run(
            [self.shell(), str(self.wrapper), *args, "--home", str(self.home)],
            cwd=self.root,
            input=enter,
            text=True,
            capture_output=True,
            env=env,
            timeout=30,
        )

    def test_wrapper_reports_success_failure_and_eof_without_changing_status(self):
        result = self.run_wrapper("install", "--target", "both")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Exit code: 0", result.stdout)
        self.assertIn("Press Enter", result.stdout)
        skill = self.home / ".agents/skills/doc-coauthoring/SKILL.md"
        skill.write_text("Personal changes", encoding="utf-8")
        result = self.run_wrapper("install", "--target", "codex", enter="")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Locally modified", result.stdout + result.stderr)
        self.assertIn("Exit code: 1", result.stdout)
        self.assertEqual(skill.read_text(), "Personal changes")
        result = self.run_wrapper("list", enter="")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Exit code: 0", result.stdout)

    @unittest.skipIf(os.name == "nt", "Real POSIX PTY required")
    def test_interactive_targets_keep_result_visible_until_enter(self):
        import pty

        for choice, targets in [
            ("1", ["codex"]),
            ("2", ["claude"]),
            ("3", ["codex", "claude"]),
        ]:
            home = self.root / ("user-" + choice)
            home.mkdir()
            master, slave = pty.openpty()
            process = subprocess.Popen(
                ["sh", str(self.wrapper), "--home", str(home)],
                cwd=self.root,
                stdin=slave,
                stdout=slave,
                stderr=slave,
            )
            os.close(slave)
            try:
                os.write(master, (choice + "\n").encode())
                output = b""
                deadline = time.monotonic() + 20
                while b"Press Enter" not in output and time.monotonic() < deadline:
                    if select.select([master], [], [], 0.1)[0]:
                        try:
                            chunk = os.read(master, 8192)
                        except OSError:
                            break
                        if not chunk:
                            break
                        output += chunk
                    if process.poll() is not None:
                        break
                self.assertIn(b"Exit code: 0", output, output.decode(errors="replace"))
                self.assertIn(b"Press Enter", output, output.decode(errors="replace"))
                self.assertIsNone(process.poll(), "Result terminal must wait for Enter")
                os.write(master, b"\n")
                self.assertEqual(process.wait(timeout=10), 0)
                for target, folder in [("codex", ".agents"), ("claude", ".claude")]:
                    self.assertEqual(
                        (home / folder / "skills/doc-coauthoring/SKILL.md").exists(),
                        target in targets,
                    )
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                os.close(master)

    @unittest.skipIf(os.name == "nt", "Linux desktop tools required")
    def test_desktop_and_shell_syntax_are_valid(self):
        validator = shutil.which("desktop-file-validate")
        if not validator:
            self.skipTest("desktop-file-validate unavailable")
        for command in [
            [validator, str(self.package / "Install Doc Coauthoring.desktop")],
            ["sh", "-n", str(self.wrapper)],
        ]:
            result = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipIf(os.name == "nt", "GLib desktop parser requires Linux")
    def test_desktop_bootstrap_handles_local_path_and_file_uri(self):
        library = ctypes.util.find_library("glib-2.0")
        if not library:
            self.skipTest("GLib unavailable")
        glib = ctypes.CDLL(library)
        pointer = ctypes.c_void_p
        string = ctypes.c_char_p
        glib.g_key_file_new.restype = pointer
        glib.g_key_file_load_from_file.argtypes = [
            pointer,
            string,
            ctypes.c_int,
            pointer,
        ]
        glib.g_key_file_get_string.argtypes = [pointer, string, string, pointer]
        glib.g_key_file_get_string.restype = pointer
        glib.g_key_file_get_boolean.argtypes = [pointer, string, string, pointer]
        glib.g_key_file_free.argtypes = [pointer]
        glib.g_free.argtypes = [pointer]
        glib.g_shell_parse_argv.argtypes = [
            string,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.POINTER(string)),
            pointer,
        ]
        glib.g_strfreev.argtypes = [ctypes.POINTER(string)]
        desktop = self.package / "Install Doc Coauthoring.desktop"
        keyfile = glib.g_key_file_new()
        try:
            self.assertTrue(
                glib.g_key_file_load_from_file(keyfile, os.fsencode(desktop), 0, None)
            )
            self.assertTrue(
                glib.g_key_file_get_boolean(
                    keyfile, b"Desktop Entry", b"Terminal", None
                )
            )
            command = glib.g_key_file_get_string(
                keyfile, b"Desktop Entry", b"Exec", None
            )
            try:
                count = ctypes.c_int()
                values = ctypes.POINTER(string)()
                self.assertTrue(
                    glib.g_shell_parse_argv(
                        ctypes.string_at(command),
                        ctypes.byref(count),
                        ctypes.byref(values),
                        None,
                    )
                )
                try:
                    parsed = [values[i].decode("utf-8") for i in range(count.value)]
                finally:
                    glib.g_strfreev(values)
            finally:
                glib.g_free(command)
        finally:
            glib.g_key_file_free(keyfile)
        self.assertIn("%k", parsed)
        for location in (str(desktop), desktop.as_uri()):
            argv = [
                location if arg == "%k" else arg.replace("%%", "%") for arg in parsed
            ]
            result = subprocess.run(
                argv,
                cwd=self.root,
                input="\n",
                text=True,
                capture_output=True,
                env=dict(os.environ, HOME=str(self.home)),
                timeout=30,
            )
            # A piped, non-TTY installer asks for an explicit target; bootstrap still
            # must find our wrapper and preserve its visible failure and exit status.
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Choose --target", result.stdout + result.stderr)
            self.assertIn("Exit code: 2", result.stdout)
            self.assertIn("Press Enter", result.stdout)
        for location in ("", "file://remote-host/tmp/installer.desktop"):
            argv = [
                location if arg == "%k" else arg.replace("%%", "%") for arg in parsed
            ]
            result = subprocess.run(
                argv,
                cwd=self.root,
                input="",
                text=True,
                capture_output=True,
                timeout=10,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Press Enter", result.stdout + result.stderr)
            self.assertFalse((self.home / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
