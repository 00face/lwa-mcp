"""Bounded in-process event bridge for the opt-in Textual controller."""

from __future__ import annotations

from collections import deque

MAX_BRIDGE_EVENTS = 200


class TextualEventBridge:
    """Queue transport-neutral LWA events without retaining unbounded history."""

    def __init__(self, *, max_events: int = MAX_BRIDGE_EVENTS) -> None:
        if not 1 <= max_events <= MAX_BRIDGE_EVENTS:
            raise ValueError(f"max_events must be between 1 and {MAX_BRIDGE_EVENTS}")
        self._events: deque[dict[str, object]] = deque(maxlen=max_events)

    def publish(self, event: dict[str, object]) -> None:
        if isinstance(event, dict) and event:
            self._events.append(dict(event))

    def drain(self) -> list[dict[str, object]]:
        events = list(self._events)
        self._events.clear()
        return events
