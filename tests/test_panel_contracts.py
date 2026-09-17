from __future__ import annotations

import asyncio

from lwa_mcp.panel_input import InputAction, route_key
from lwa_mcp.panel_lifecycle import PanelLifecycle
from lwa_mcp.panel_rendering import PanelGeometry, cursor_row


def test_input_router_has_stable_global_actions():
    assert route_key("\t") is InputAction.FOCUS_NEXT
    assert route_key("__LWA_SHIFT_TAB__") is InputAction.FOCUS_PREVIOUS
    assert route_key("\x03") is InputAction.COPY
    assert route_key("\x11") is InputAction.EXIT
    assert route_key("x") is InputAction.TEXT


def test_input_router_keeps_partial_or_graphics_sequences_out_of_global_actions():
    for value in ("\x1b", "[", "\x1b_G", "__LWA_GRAPHICS_RESPONSE__", None, object()):
        assert route_key(value) is InputAction.TEXT


def test_geometry_clamps_each_panel_scroll_independently():
    geometry = PanelGeometry.from_screen(24, 100, native_split=False)
    assert geometry.left_width < geometry.columns
    assert geometry.clamp_scroll(999, 100) == 89
    assert geometry.clamp_scroll(-1, 100) == 0
    assert cursor_row(15, 0) == 16
    assert cursor_row(15, 1) == 17


def test_lifecycle_close_is_idempotent():
    calls: list[str] = []

    async def close() -> None:
        calls.append("closed")

    async def scenario() -> None:
        lifecycle = PanelLifecycle(close)
        await asyncio.gather(lifecycle.close_once(), lifecycle.close_once())
        assert lifecycle.closed

    asyncio.run(scenario())
    assert calls == ["closed"]
