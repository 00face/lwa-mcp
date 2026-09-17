"""Small, explicit resource guards for long-running terminal sessions."""

from __future__ import annotations

import os
import time
from collections.abc import Iterable


def budget_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    """Read a safe integer budget without allowing pathological values."""
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def budget_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    """Read a safe floating-point budget without allowing busy-loop values."""
    try:
        value = float(os.environ.get(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def redraw_due(
    previous_signature: object,
    signature: object,
    last_render_at: float,
    *,
    minimum_interval: float,
) -> bool:
    """Allow a repaint when visible state changed or the interval elapsed."""
    return signature != previous_signature or time.monotonic() - last_render_at >= minimum_interval


class BoundedLines(list[str]):
    """List-compatible transcript storage with a hard retained-line limit."""

    def __init__(self, values: Iterable[str] = (), *, max_lines: int = 120) -> None:
        self.max_lines = max(20, max_lines)
        super().__init__(values)
        self._trim()

    def append(self, value: str) -> None:
        super().append(value)
        self._trim()

    def extend(self, values: Iterable[str]) -> None:
        super().extend(values)
        self._trim()

    def _trim(self) -> None:
        if len(self) > self.max_lines:
            del self[: len(self) - self.max_lines]
