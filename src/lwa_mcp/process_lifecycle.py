"""Process-lifetime safeguards for stdio-bound Lwa child processes."""

from __future__ import annotations

import ctypes
import signal
import sys
from collections.abc import Callable

PR_SET_PDEATHSIG = 1
SIGTERM = signal.SIGTERM

_prctl: Callable[[int, int], int] | None = None
if sys.platform.startswith("linux"):
    try:
        _libc = ctypes.CDLL(None, use_errno=True)
        _native_prctl = _libc.prctl
        _native_prctl.argtypes = [ctypes.c_int, ctypes.c_ulong]
        _native_prctl.restype = ctypes.c_int

        def _prctl(option: int, value: int) -> int:
            return _native_prctl(option, value)
    except (AttributeError, OSError):
        _prctl = None


def install_parent_death_signal() -> bool:
    """Ask Linux to terminate this child when its owning host process exits."""
    if _prctl is None:
        return False
    try:
        return _prctl(PR_SET_PDEATHSIG, SIGTERM) == 0
    except OSError:
        return False
