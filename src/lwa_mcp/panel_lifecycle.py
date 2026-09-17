"""Idempotent lifecycle boundary for panel-owned resources."""

from __future__ import annotations

from collections.abc import Awaitable, Callable


class PanelLifecycle:
    """Ensure cancellation, exit, and error paths close a session once."""

    def __init__(self, close: Callable[[], Awaitable[None]]) -> None:
        self._close = close
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    async def close_once(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._close()
