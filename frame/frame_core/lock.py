from __future__ import annotations

import fcntl
from contextlib import contextmanager
from pathlib import Path


class LockUnavailableError(RuntimeError):
    pass


@contextmanager
def hold_lock(path: Path, *, non_blocking: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as lock_file:
        operation = fcntl.LOCK_EX | (fcntl.LOCK_NB if non_blocking else 0)
        try:
            fcntl.flock(lock_file.fileno(), operation)
        except BlockingIOError as error:
            raise LockUnavailableError(f"Lock already held: {path}") from error

        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
