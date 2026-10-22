"""Bounded real GIO/terminal adapter observation; run explicitly on Linux.

Uses a private HOME and D-Bus session. No real profile installation or desktop
trust settings are changed. Screenshots cover only the terminal owned by that
private session. File-manager double-click/trust behavior is a separate claim.
"""

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib


class WindowAttributes(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
        ("border", ctypes.c_int),
        ("depth", ctypes.c_int),
        ("visual", ctypes.c_void_p),
        ("root", ctypes.c_ulong),
        ("window_class", ctypes.c_int),
        ("bit_gravity", ctypes.c_int),
        ("win_gravity", ctypes.c_int),
        ("backing_store", ctypes.c_int),
        ("backing_planes", ctypes.c_ulong),
        ("backing_pixel", ctypes.c_ulong),
        ("save_under", ctypes.c_int),
        ("colormap", ctypes.c_ulong),
        ("map_installed", ctypes.c_int),
        ("map_state", ctypes.c_int),
        ("all_events", ctypes.c_long),
        ("your_events", ctypes.c_long),
        ("propagate_mask", ctypes.c_long),
        ("override_redirect", ctypes.c_int),
        ("screen", ctypes.c_void_p),
    ]


class TerminalWindow:
    def __init__(self):
        self.x = ctypes.CDLL(ctypes.util.find_library("X11"))
        self.xt = ctypes.CDLL(ctypes.util.find_library("Xtst"))
        p, u, i = ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = p
        self.display = self.x.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError("No X11 graphical display available")
        self.x.XDefaultRootWindow.argtypes = [p]
        self.x.XDefaultRootWindow.restype = u
        self.root = self.x.XDefaultRootWindow(self.display)
        self.x.XQueryTree.argtypes = [
            p,
            u,
            ctypes.POINTER(u),
            ctypes.POINTER(u),
            ctypes.POINTER(ctypes.POINTER(u)),
            ctypes.POINTER(ctypes.c_uint),
        ]
        self.x.XInternAtom.argtypes = [p, ctypes.c_char_p, i]
        self.x.XInternAtom.restype = u
        self.x.XGetWindowProperty.argtypes = [
            p,
            u,
            u,
            ctypes.c_long,
            ctypes.c_long,
            i,
            u,
            ctypes.POINTER(u),
            ctypes.POINTER(i),
            ctypes.POINTER(u),
            ctypes.POINTER(u),
            ctypes.POINTER(p),
        ]
        self.x.XFree.argtypes = [p]
        self.x.XSetInputFocus.argtypes = [p, u, i, u]
        self.x.XRaiseWindow.argtypes = [p, u]
        self.x.XSync.argtypes = [p, i]
        self.x.XKeysymToKeycode.argtypes = [p, u]
        self.x.XKeysymToKeycode.restype = ctypes.c_uint
        self.xt.XTestFakeKeyEvent.argtypes = [p, ctypes.c_uint, i, u]
        self.x.XGetGeometry.argtypes = [
            p,
            u,
            ctypes.POINTER(u),
            ctypes.POINTER(i),
            ctypes.POINTER(i),
            ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint),
        ]
        self.x.XGetImage.argtypes = [p, u, i, i, ctypes.c_uint, ctypes.c_uint, u, i]
        self.x.XGetImage.restype = p
        self.x.XGetPixel.argtypes = [p, i, i]
        self.x.XGetPixel.restype = u
        self.x.XDestroyImage.argtypes = [p]
        self.x.XGetWindowAttributes.argtypes = [p, u, ctypes.POINTER(WindowAttributes)]
        handler_type = ctypes.CFUNCTYPE(i, p, p)
        self.error_handler = handler_type(lambda display, event: 0)
        self.x.XSetErrorHandler.argtypes = [handler_type]
        self.x.XSetErrorHandler(self.error_handler)
        self.pid_atom = self.x.XInternAtom(self.display, b"_NET_WM_PID", 0)

    def children(self, window):
        root, parent = ctypes.c_ulong(), ctypes.c_ulong()
        values = ctypes.POINTER(ctypes.c_ulong)()
        count = ctypes.c_uint()
        if not self.x.XQueryTree(
            self.display,
            window,
            ctypes.byref(root),
            ctypes.byref(parent),
            ctypes.byref(values),
            ctypes.byref(count),
        ):
            return []
        result = [values[n] for n in range(count.value)]
        if values:
            self.x.XFree(values)
        return result

    def window_pid(self, window):
        kind, count, after = ctypes.c_ulong(), ctypes.c_ulong(), ctypes.c_ulong()
        form, value = ctypes.c_int(), ctypes.c_void_p()
        self.x.XGetWindowProperty(
            self.display,
            window,
            self.pid_atom,
            0,
            1,
            0,
            6,
            ctypes.byref(kind),
            ctypes.byref(form),
            ctypes.byref(count),
            ctypes.byref(after),
            ctypes.byref(value),
        )
        try:
            return (
                ctypes.cast(value, ctypes.POINTER(ctypes.c_ulong))[0]
                if value and count.value
                else None
            )
        finally:
            if value:
                self.x.XFree(value)

    def viewable(self, window):
        attributes = WindowAttributes()
        return (
            self.x.XGetWindowAttributes(self.display, window, ctypes.byref(attributes))
            and attributes.map_state == 2
            and attributes.width > 100
            and attributes.height > 60
        )

    def owned(self, pid):
        windows = self.children(self.root)
        for window in windows:
            if self.window_pid(window) == pid and self.viewable(window):
                return window
        for parent in windows:
            for window in self.children(parent):
                if self.window_pid(window) == pid and self.viewable(window):
                    return window
        return None

    def key(self, window, keysym):
        self.x.XRaiseWindow(self.display, window)
        self.x.XSetInputFocus(self.display, window, 1, 0)
        self.x.XSync(self.display, 0)
        time.sleep(0.15)
        code = self.x.XKeysymToKeycode(self.display, keysym)
        if not code:
            raise RuntimeError("Requested key is unavailable")
        self.xt.XTestFakeKeyEvent(self.display, code, 1, 0)
        self.xt.XTestFakeKeyEvent(self.display, code, 0, 0)
        self.x.XSync(self.display, 0)

    def capture(self, window, output):
        root, x, y = ctypes.c_ulong(), ctypes.c_int(), ctypes.c_int()
        width, height, border, depth = [ctypes.c_uint() for _ in range(4)]
        if not self.x.XGetGeometry(
            self.display,
            window,
            ctypes.byref(root),
            ctypes.byref(x),
            ctypes.byref(y),
            ctypes.byref(width),
            ctypes.byref(height),
            ctypes.byref(border),
            ctypes.byref(depth),
        ):
            raise RuntimeError("Terminal geometry unavailable")
        if width.value * height.value > 4000000:
            raise RuntimeError("Terminal capture exceeds bounded size")
        bitmap = self.x.XGetImage(
            self.display,
            window,
            0,
            0,
            width.value,
            height.value,
            ctypes.c_ulong(-1).value,
            2,
        )
        if not bitmap:
            raise RuntimeError("Terminal capture unavailable")
        try:
            rows = bytearray()
            for row in range(height.value):
                rows.append(0)
                for column in range(width.value):
                    pixel = self.x.XGetPixel(bitmap, column, row)
                    rows.extend(((pixel >> 16) & 255, (pixel >> 8) & 255, pixel & 255))
        finally:
            self.x.XDestroyImage(bitmap)

        def chunk(kind, data):
            return (
                struct.pack(">I", len(data))
                + kind
                + data
                + struct.pack(">I", zlib.crc32(kind + data))
            )

        output.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + chunk(
                b"IHDR",
                struct.pack(">IIBBBBB", width.value, height.value, 8, 2, 0, 0, 0),
            )
            + chunk(b"IDAT", zlib.compress(bytes(rows)))
            + chunk(b"IEND", b"")
        )


def inventory(path):
    return {
        p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in path.rglob("*")
        if p.is_file()
    }


def child_processes(pid):
    result = set()
    for task in Path("/proc", str(pid), "task").glob("*"):
        try:
            result.update(map(int, (task / "children").read_text().split()))
        except (FileNotFoundError, ProcessLookupError):
            pass
    return result


def wrapper_process(server_pid, wrapper):
    for pid in child_processes(server_pid):
        try:
            argv = Path("/proc", str(pid), "cmdline").read_bytes().split(b"\0")
            if os.fsencode(wrapper) in argv:
                return pid
        except (FileNotFoundError, ProcessLookupError):
            pass
    raise RuntimeError("Cannot identify this terminal's installer wrapper")


def session(args):
    from gi.repository import Gio, GLib

    output = Path(args.output).resolve()
    package = Path(args.package).resolve()
    home = Path.home()
    desktop = package / "Install Doc Coauthoring.desktop"
    terminal = TerminalWindow()
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    rows = []
    service_pid = None
    try:
        cases = [(choice, choice, False) for choice in args.choices] + [
            ("conflict", "1", True)
        ]
        for case, choice, expect_failure in cases:
            if expect_failure:
                skill = home / ".agents/skills/doc-coauthoring/SKILL.md"
                skill.write_bytes(skill.read_bytes() + b"\nPersonal test change\n")
            before = {
                target: inventory(home / folder / "skills/doc-coauthoring")
                for target, folder in [("codex", ".agents"), ("claude", ".claude")]
            }
            app = Gio.DesktopAppInfo.new_from_filename(str(desktop))
            if app is None:
                raise RuntimeError("GIO rejected the real desktop entry")
            app.launch([], Gio.AppLaunchContext())
            deadline = time.monotonic() + 20
            window = None
            while time.monotonic() < deadline:
                try:
                    result = connection.call_sync(
                        "org.freedesktop.DBus",
                        "/org/freedesktop/DBus",
                        "org.freedesktop.DBus",
                        "GetConnectionUnixProcessID",
                        GLib.Variant("(s)", ("org.gnome.Terminal",)),
                        GLib.VariantType("(u)"),
                        Gio.DBusCallFlags.NONE,
                        1000,
                        None,
                    )
                    service_pid = result.unpack()[0]
                    window = terminal.owned(service_pid)
                    if window:
                        break
                except GLib.Error:
                    pass
                time.sleep(0.1)
            if not window:
                raise RuntimeError(
                    "No GNOME Terminal window owned by the private D-Bus session"
                )
            time.sleep(0.5)
            terminal.capture(window, output / ("case-" + case + "-prompt.png"))
            wrapper_pid = wrapper_process(
                service_pid, package / "scripts/install-gui.sh"
            )
            terminal.key(window, ord(choice))
            time.sleep(0.2)
            terminal.capture(window, output / ("case-" + case + "-selected.png"))
            terminal.key(window, 0xFF0D)
            targets = {"1": ["codex"], "2": ["claude"], "3": ["codex", "claude"]}[
                choice
            ]
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if not child_processes(wrapper_pid):
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError(
                    "Installer child did not finish before the observation bound"
                )
            if not all(
                (
                    home
                    / (".agents" if t == "codex" else ".claude")
                    / "skills/doc-coauthoring/SKILL.md"
                ).is_file()
                for t in targets
            ):
                raise RuntimeError(
                    "Installation did not produce the selected isolated skills"
                )
            time.sleep(0.5)
            if not terminal.owned(service_pid):
                raise RuntimeError("Terminal closed before Enter")
            terminal.capture(window, output / ("case-" + case + "-result.png"))
            after = {
                target: inventory(home / folder / "skills/doc-coauthoring")
                for target, folder in [("codex", ".agents"), ("claude", ".claude")]
            }
            if expect_failure and after != before:
                raise RuntimeError(
                    "Conflict installation changed preserved skill content"
                )
            for target in ("codex", "claude"):
                if target not in targets and after[target] != before[target]:
                    raise RuntimeError("Unselected target changed")
            if (home / ".codex/plugins").exists() or (
                home / ".claude/plugins"
            ).exists():
                raise RuntimeError("Unexpected plugin state")
            terminal.key(window, 0xFF0D)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and terminal.owned(service_pid):
                time.sleep(0.1)
            if terminal.owned(service_pid):
                raise RuntimeError("Terminal did not close after Enter")
            rows.append(
                dict(
                    case=case,
                    expected_exit_code=1 if expect_failure else 0,
                    choice=choice,
                    selected=targets,
                    window_pid=service_pid,
                    result_visible_before_enter=True,
                    closed_after_enter=True,
                    files=after,
                )
            )
        (output / "graphical-observations.json").write_text(
            json.dumps(
                dict(
                    mode="real GIO DesktopAppInfo and GNOME Terminal under private HOME/D-Bus, X11 input/capture",
                    file_manager_double_click="NOT RUN",
                    first_launch_trust="NOT RUN",
                    terminal_text_review="Pending inspection of captured terminal images",
                    observations=rows,
                ),
                indent=2,
            ),
            encoding="utf-8",
        )
        return 0
    finally:
        if service_pid:
            # Only the GNOME Terminal service obtained from this private bus.
            try:
                os.kill(service_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--choices", default="123", choices=["123", "3"])
    parser.add_argument("--session", action="store_true")
    args = parser.parse_args()
    if args.session:
        return session(args)
    root = Path(__file__).resolve().parents[5]
    (root / ".test-tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="doc-graphical-", dir=root / ".test-tmp"
    ) as directory:
        copied = Path(directory) / "package space \u4e2d\u6587"
        shutil.copytree(
            args.package, copied, ignore=shutil.ignore_patterns("dist", "__pycache__")
        )
        home = Path(directory) / "home"
        home.mkdir()
        env = dict(
            os.environ, HOME=str(home), GDK_BACKEND="x11", XDG_CURRENT_DESKTOP="GNOME"
        )
        env.pop("DBUS_SESSION_BUS_ADDRESS", None)
        env.pop("AT_SPI_BUS_ADDRESS", None)
        result = subprocess.run(
            [
                "dbus-run-session",
                "--",
                sys.executable,
                str(Path(__file__).resolve()),
                "--session",
                "--package",
                str(copied),
                "--output",
                args.output,
                "--choices",
                args.choices,
            ],
            env=env,
            timeout=150,
        )
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
