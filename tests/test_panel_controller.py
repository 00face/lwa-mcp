from __future__ import annotations

from lwa_mcp.panel_controller import (
    FocusBroker,
    PanelEvent,
    PanelLifecycle,
    PanelState,
    Surface,
    reduce_panel,
    semantic_key,
)


def test_focus_reducer_is_symmetric_and_clears_selection():
    state = reduce_panel(
        reduce_panel(
            reduce_panel(
                PanelState(
                    focus=Surface.LWA,
                    selection_surface=Surface.LWA,
                ),
                PanelEvent.FOCUS_NEXT,
            ),
            PanelEvent.FOCUS_PREVIOUS,
        ),
        PanelEvent.EXIT,
    )
    assert state.focus is Surface.LWA
    assert state.selection_surface is None
    assert state.lifecycle is PanelLifecycle.STOPPING


def test_native_focus_broker_records_exact_target_and_effect():
    calls: list[str] = []
    broker = FocusBroker(mode="native")

    transition = broker.focus_next(effect=lambda target: calls.append(target.value) or True)

    assert calls == ["codex"]
    assert transition.source is Surface.LWA
    assert transition.target is Surface.CODEX
    assert transition.mode == "native"
    assert transition.result == "accepted"
    assert broker.surface is Surface.CODEX


def test_focus_effect_failure_is_recoverable_and_state_remains_authoritative():
    broker = FocusBroker(mode="native")
    transition = broker.focus_next(effect=lambda _target: False)

    assert transition.result == "effect-rejected"
    assert broker.surface is Surface.CODEX
    assert len(broker.transitions) == 1


def test_focus_broker_soak_alternates_exactly_100_times_without_drift():
    broker = FocusBroker(mode="native")
    for _ in range(100):
        broker.focus_next()

    assert len(broker.transitions) == 100
    assert broker.surface is Surface.LWA
    assert all(item.result == "accepted" for item in broker.transitions)
    assert all(
        (item.source, item.target) == (Surface.LWA, Surface.CODEX)
        if index % 2 == 0
        else (item.source, item.target) == (Surface.CODEX, Surface.LWA)
        for index, item in enumerate(broker.transitions)
    )


def test_semantic_key_normalizes_tab_variants_and_exit():
    assert semantic_key("\t") == "focus_next"
    assert semantic_key(9) == "focus_next"
    assert semantic_key("__LWA_SHIFT_TAB__") == "focus_previous"
    assert semantic_key(17) == "exit"
    assert semantic_key("ordinary text") is None
