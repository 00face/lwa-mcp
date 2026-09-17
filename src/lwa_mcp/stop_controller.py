"""Idempotent cancellation boundary for bounded multi-provider execution."""

from __future__ import annotations

import asyncio


class StopController:
    def __init__(self) -> None:
        self.reason: str | None = None
        self._children: set[asyncio.Task[object]] = set()

    def register(self, task: asyncio.Task[object]) -> None:
        if self.reason is not None:
            task.cancel()
            return
        self._children.add(task)
        task.add_done_callback(self._children.discard)

    def stop(self, reason: str) -> None:
        if not reason or self.reason is not None:
            return
        self.reason = reason
        for task in tuple(self._children):
            task.cancel()
        self._children.clear()
