"""Pure panel state, focus, and input contracts for the LWA terminal frame.

This module deliberately has no curses or tmux dependency.  The terminal
frame supplies effects (selecting a pane, redrawing, copying) after the
reducer has produced a semantic decision.  Keeping this boundary pure makes
focus regressions testable without starting a terminal.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from enum import StrEnum


class Surface(StrEnum):
    LWA = "lwa"
    CODEX = "codex"


class PanelLifecycle(StrEnum):
    STARTING = "starting"
    READY = "ready"
    STOPPING = "stopping"
    STOPPED = "stopped"


class PanelEvent(StrEnum):
    FOCUS_NEXT = "focus_next"
    FOCUS_PREVIOUS = "focus_previous"
    FOCUS_LWA = "focus_lwa"
    FOCUS_CODEX = "focus_codex"
    EXIT = "exit"


@dataclass(frozen=True)
class PanelState:
    """The state that must be consistent across embedded and native modes."""

    focus: Surface = Surface.LWA
    lifecycle: PanelLifecycle = PanelLifecycle.STARTING
    modal: bool = False
    lwa_scroll: int = 0
    codex_scroll: int = 0
    selection_surface: Surface | None = None


@dataclass(frozen=True)
class FocusTransition:
    source: Surface
    target: Surface
    event: str
    mode: str
    result: str = "accepted"


def reduce_panel(state: PanelState, event: PanelEvent) -> PanelState:
    """Apply one semantic panel event without performing terminal effects."""
    if event is PanelEvent.EXIT:
        return replace(state, lifecycle=PanelLifecycle.STOPPING)
    if event in (PanelEvent.FOCUS_NEXT, PanelEvent.FOCUS_PREVIOUS):
        target = Surface.CODEX if state.focus is Surface.LWA else Surface.LWA
        return replace(state, focus=target, selection_surface=None)
    if event is PanelEvent.FOCUS_LWA:
        return replace(state, focus=Surface.LWA, selection_surface=None)
    if event is PanelEvent.FOCUS_CODEX:
        return replace(state, focus=Surface.CODEX, selection_surface=None)
    return state


class FocusBroker:
    """Single owner of logical focus transitions and their diagnostics."""

    def __init__(self, *, mode: str = "embedded", initial: Surface = Surface.LWA) -> None:
        self.mode = mode
        self.state = PanelState(focus=initial, lifecycle=PanelLifecycle.READY)
        self.transitions: list[FocusTransition] = []

    @property
    def surface(self) -> Surface:
        return self.state.focus

    def transition(
        self,
        event: PanelEvent,
        *,
        effect: Callable[[Surface], bool] | None = None,
    ) -> FocusTransition:
        source = self.state.focus
        next_state = reduce_panel(self.state, event)
        target = next_state.focus
        result = "accepted"
        if target is not source and effect is not None:
            try:
                if not effect(target):
                    result = "effect-rejected"
            except Exception:  # noqa: BLE001 - diagnostics must not kill input
                result = "effect-error"
        self.state = next_state
        transition = FocusTransition(source, target, event.value, self.mode, result)
        self.transitions.append(transition)
        return transition

    def focus_next(self, *, effect: Callable[[Surface], bool] | None = None) -> FocusTransition:
        return self.transition(PanelEvent.FOCUS_NEXT, effect=effect)

    def focus_previous(self, *, effect: Callable[[Surface], bool] | None = None) -> FocusTransition:
        return self.transition(PanelEvent.FOCUS_PREVIOUS, effect=effect)


def semantic_key(value: object) -> str | None:
    """Normalize raw key values shared by curses and terminal adapters."""
    if value in ("\t", 9, "__LWA_TAB__"):
        return PanelEvent.FOCUS_NEXT.value
    if value in ("__LWA_SHIFT_TAB__", "KEY_BTAB"):
        return PanelEvent.FOCUS_PREVIOUS.value
    if value in ("\x11", 17, "__LWA_EXIT__"):
        return PanelEvent.EXIT.value
    return None


def transitions_for(events: Iterable[PanelEvent], *, mode: str = "embedded") -> list[FocusTransition]:
    """Small deterministic helper used by parity tests and diagnostics."""
    broker = FocusBroker(mode=mode)
    return [broker.transition(event) for event in events]
