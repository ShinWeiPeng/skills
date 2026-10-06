"""Shared cross-process state lock for SPEC and document owners."""

from __future__ import annotations
import errno
import hashlib
import os
import time
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def project_state_lock(root: Path, key: str, timeout: float = 30.0):
    """Lock a stable inode briefly; the OS releases ownership on process exit."""
    directory = root.resolve() / "spec-governance"
    if directory.is_symlink() or directory.resolve() != directory:
        raise ValueError("governance directory must not be redirected")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (".state-" + hashlib.sha256(key.encode()).hexdigest() + ".lock")
    if path.is_symlink():
        raise ValueError("state lock must not be redirected")
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN}:
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"shared state remained locked for {timeout:g}s; holder unknown; preserve pending edits and reread before retrying"
                    )
                time.sleep(0.01)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
