"""Renderer-neutral UI profiles and bounded events for LWA surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from .terminal_protocol import detect_terminal_capabilities

Renderer = Literal["plain", "ansi", "graphics"]
MAX_EVENT_TEXT = 2000


@dataclass(frozen=True, slots=True)
class UIProfile:
    renderer: Renderer
    color: bool
    unicode: bool
    graphics: bool
    animation: bool


@dataclass(frozen=True, slots=True)
class OperationalStatus:
    state: str = "ready"
    route: str = "local"
    effort: str = "auto"
    quota: str = "unknown"
    memory: str = "off"


def format_operational_status(status: OperationalStatus, *, plain: bool = False) -> str:
    """Return a compact status line suitable for any renderer."""
    if plain:
        return f"LWA {status.state} | route={status.route} effort={status.effort} quota={status.quota} memory={status.memory}"
    return (
        f"LWA · {status.state} · route:{status.route} · effort:{status.effort} · "
        f"quota:{status.quota} · memory:{status.memory}"
    )


def detect_ui_profile(env: Mapping[str, str] | None = None) -> UIProfile:
    """Choose the smallest honest renderer from terminal capabilities."""
    capabilities = detect_terminal_capabilities(env)
    values = env or {}
    no_color = values.get("NO_COLOR") is not None or values.get("TERM", "").lower() == "dumb"
    if no_color:
        return UIProfile("plain", False, False, False, False)
    graphics = capabilities.kitty_graphics or capabilities.sixel_graphics or "ghostty" in capabilities.renderer.lower()
    return UIProfile("graphics" if graphics else "ansi", True, capabilities.unicode, graphics, graphics)


def bounded_ui_event(kind: str, message: str = "", **fields: object) -> dict[str, object]:
    """Build a bounded, renderer-neutral event safe for every UI surface."""
    clean_kind = kind.strip()
    if not clean_kind:
        raise ValueError("event kind is required")
    clean_message = message.strip()[:MAX_EVENT_TEXT]
    return {"type": clean_kind, "message": clean_message, **fields}
