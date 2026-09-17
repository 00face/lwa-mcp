"""Opt-in Textual controller for the LWA pane; Codex remains a separate pane."""

from __future__ import annotations

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.events import Key
from textual.suggester import SuggestFromList
from textual.widgets import Footer, Header, Input, Static, TextArea

from .pet_renderer import render_configured_pet
from .textual_bridge import TextualEventBridge
from .ui_profiles import OperationalStatus, format_operational_status

ALLOWED_COMMANDS = frozenset({
    "/lwa", "/consensus", "/route", "/pets", "/status", "/help",
    "/gates", "/workorders", "/doctor",
})
COMMAND_ALIASES = {"/wo": "/workorders", "/health": "/doctor"}
COMPLETION_OPTIONS = (
    "/lwa",
    "/consensus",
    "/route",
    "/pets",
    "/gates",
    "/workorders",
    "/doctor",
    "/wo",
    "/health",
    "/status",
    "/help",
    "Run the relevant tests",
    "Show the current work order status",
)
MAX_PET_FRAMES = 96


class LwaController(App[None]):
    """Small, headless-testable LWA controller shell."""

    BINDINGS: ClassVar = [
        ("ctrl+alt+q", "quit", "Quit LWA"),
        ("ctrl+l", "focus_prompt", "Focus prompt"),
        ("ctrl+c", "ignore_ctrl_c", ""),
    ]
    DEFAULT_CSS = """
    Screen { background: $surface; }
    Header { background: $panel; color: $accent; }
    #lwa-main { height: 1fr; padding: 0 1; }
    #brand { height: 1; color: $accent; text-style: bold; }
    #status { height: 2; color: $text-muted; content-align: left middle; }
    #pet { height: 5; border: round $accent; color: $accent; content-align: center middle; }
    #events { height: 1fr; border: round $accent; scrollbar-size: 1 1; }
    #prompt { dock: bottom; margin-top: 1; }
    #events:focus { border: double $success; }
    #prompt:focus { border: double $success; }
    """

    def __init__(self, *, initial_log: list[str] | None = None, bridge: TextualEventBridge | None = None) -> None:
        super().__init__()
        self.initial_log = initial_log or []
        self.bridge = bridge
        self.operational_status = OperationalStatus()
        self.last_command: str | None = None
        self.command_history: list[str] = []
        self._history_index: int | None = None
        self._pet_frames: tuple[str, ...] = ()
        self._pet_index = 0
        self._pet_timer = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="lwa-main"):
            yield Static("◈ LWA OPERATIONS CONSOLE", id="brand")
            yield Static("LWA · READY · Codex remains independent", id="status")
            yield Static("Pet: unavailable", id="pet")
            yield TextArea(read_only=True, show_line_numbers=False, id="events")
            yield Static("Ctrl+L prompt · Right accepts completion · Ctrl+Alt+Q exits", id="hint")
            yield Input(
                placeholder="Enter prompt or /lwa command · Right accepts suggestion",
                suggester=SuggestFromList(COMPLETION_OPTIONS),
                id="prompt",
            )
        yield Footer()

    def on_mount(self) -> None:
        for line in self.initial_log:
            self.append_event(line)
        pet = render_configured_pet(renderer="text-fallback")
        if pet is not None:
            self.set_pet_frames([pet.text_fallback])
            self.append_event(f"Pet loaded: {pet.name} ({pet.source}).")
        else:
            self.append_event("Pet unavailable: no configured Codex pet could be loaded.")
        self.query_one("#prompt", Input).focus()
        if self.bridge is not None:
            for event in self.bridge.drain():
                self.handle_event(event)

    def action_focus_prompt(self) -> None:
        self.query_one("#prompt", Input).focus()

    def action_ignore_ctrl_c(self) -> None:
        """Keep Ctrl+C available to the terminal without quitting LWA."""

    def on_key(self, event: Key) -> None:
        """Reserve Ctrl+C for terminal copy/cancel semantics, not application quit."""
        if event.key == "ctrl+c":
            event.stop()
        elif event.key in {"up", "down"} and self.focused is not None and self.focused.id == "prompt":
            self._navigate_history(event.key == "up")
            event.stop()

    def _navigate_history(self, older: bool) -> None:
        if not self.command_history:
            return
        if self._history_index is None:
            self._history_index = len(self.command_history)
        self._history_index += -1 if older else 1
        self._history_index = max(0, min(len(self.command_history), self._history_index))
        value = "" if self._history_index == len(self.command_history) else self.command_history[self._history_index]
        self.query_one("#prompt", Input).value = value

    def append_event(self, message: str) -> None:
        """Append one bounded LWA event for bridge adapters."""
        if isinstance(message, str) and message.strip():
            log = self.query_one("#events", TextArea)
            lines = (log.text.splitlines() + [message.strip()])[-200:]
            log.text = "\n".join(lines)

    def set_status(self, message: str) -> None:
        """Update visible status without adding log noise."""
        self.query_one("#status", Static).update(message)

    def set_operational_status(self, status: OperationalStatus) -> None:
        """Render structured operational state in the shared status surface."""
        self.operational_status = status
        self.set_status(format_operational_status(status))

    def set_pet_frames(self, frames: list[str] | tuple[str, ...], *, interval: float = 0.12) -> None:
        """Set a bounded text pet animation with one replaceable timer."""
        if not 0.02 <= interval <= 5:
            raise ValueError("pet animation interval must be between 0.02 and 5 seconds")
        self._pet_frames = tuple(str(frame) for frame in frames[:MAX_PET_FRAMES] if str(frame))
        self._pet_index = 0
        if self._pet_timer is not None:
            self._pet_timer.pause()
        pet = self.query_one("#pet", Static)
        if not self._pet_frames:
            pet.update("Pet: unavailable")
            self._pet_timer = None
            return
        pet.update(self._pet_frames[0])
        self._pet_timer = self.set_interval(interval, self._advance_pet)

    def _advance_pet(self) -> None:
        if not self._pet_frames:
            return
        self._pet_index = (self._pet_index + 1) % len(self._pet_frames)
        try:
            self.query_one("#pet", Static).update(self._pet_frames[self._pet_index])
        except NoMatches:
            # A final timer tick may race widget-tree teardown in headless runs.
            if self._pet_timer is not None:
                self._pet_timer.pause()
                self._pet_timer = None

    def on_unmount(self) -> None:
        """Stop animation before Textual removes the widget tree."""
        if self._pet_timer is not None:
            self._pet_timer.pause()
            self._pet_timer = None

    def handle_event(self, event: dict[str, object]) -> None:
        """Ingest one bounded bridge event without depending on its transport."""
        if not isinstance(event, dict):
            return
        message = event.get("message") or event.get("data")
        if isinstance(message, str) and message.strip():
            self.append_event(message)
        state = event.get("state")
        if isinstance(state, str) and state.strip():
            self.set_status(f"LWA · {state.strip()}")

    def on_resize(self, event: object) -> None:
        """Expose layout size through the visible status line."""
        size = getattr(event, "size", None)
        if size is not None:
            self.set_status(f"LWA controller · {size.width}×{size.height} · Codex remains independent")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if value.startswith("/"):
            command = value.split(maxsplit=1)[0]
            canonical = COMMAND_ALIASES.get(command, command)
            if canonical not in ALLOWED_COMMANDS:
                self.append_event(f"Rejected command: {command}")
                self.set_status(f"LWA · rejected command {command}; try /lwa, /consensus, /route, or /pets")
            else:
                self.last_command = value
                self.command_history.append(value)
                self.command_history = self.command_history[-50:]
                self._history_index = None
                self.append_event(f"Command accepted: {value}")
                self.set_status(f"LWA · command queued: {canonical}")
        elif value:
            self.append_event(f"Prompt ready: {len(value)} characters")
            self._history_index = None
        event.input.value = ""


def main() -> None:
    LwaController().run()
