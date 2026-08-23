"""Low-dependency interactive terminal frame for the Lwa command-line surface."""

from __future__ import annotations

import asyncio
import curses
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from contextlib import suppress

from .codex_session import BridgeCodexSession, CodexSession, NativeTmuxCodexSession
from .image_compositor import (
    ImageFrame,
    kitty_delete_sequence,
    kitty_graphics_sequence,
    kitty_put_sequence,
    kitty_transmit_sequence,
)
from .panel_controller import FocusBroker, PanelEvent, Surface
from .panel_lifecycle import PanelLifecycle
from .panel_rendering import PanelGeometry
from .pet_renderer import (
    PetPlaybackState,
    PetSemanticState,
    build_pet_playback_state,
    discover_codex_pet_names,
    pet_track_for_state,
    render_configured_pet,
    resolve_pet_selection,
)
from .prompt_editor import PromptEditor
from .prompt_finalizer import finalize_prompt
from .resource_budget import BoundedLines, budget_float, budget_int, redraw_due
from .terminal_protocol import (
    TerminalTextBuffer,
    detect_terminal_capabilities,
    redact_terminal_text,
    visible_text,
)

CODEX_SLASH_COMMANDS = (
    "/help",
    "/model",
    "/status",
    "/usage",
    "/clear",
    "/compact",
    "/diff",
    "/review",
    "/mention",
    "/mcp",
    "/pets",
    "/init",
    "/undo",
    "/redo",
    "/permissions",
    "/approvals",
    "/feedback",
    "/fork",
    "/logout",
    "/new",
    "/plan",
    "/theme",
    "/quit",
    "/exit",
)
NATIVE_PET_IDLE_INTERVAL = 0.36
NATIVE_PET_ACTION_INTERVAL = 0.12
# Keep LWA's image namespace separate from Codex's own native pet IDs. Both
# panes share the terminal graphics namespace even though they are different
# tmux panes; using 9001 here allowed Codex to overwrite LWA's selected pet.
LWA_PET_IMAGE_ID = 19001


def _toggle_prompt_surface(active_surface: str) -> str:
    return "codex" if active_surface == "lwa" else "lwa"


def _focus_native_codex_pane(pane_id: str) -> None:
    """Transfer keyboard focus to the real Codex tmux pane."""
    _focus_trace(f"request_codex pane={pane_id}")
    tmux = shutil.which("tmux")
    if not tmux:
        return
    try:
        # Mouse selection/scrolling can leave the pane in tmux copy mode. Exit
        # that mode before handing focus back so Codex's prompt is immediately
        # writable instead of showing a yellow key-table/status overlay.
        subprocess.run(
            [tmux, "send-keys", "-t", pane_id, "-X", "cancel"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1,
            check=False,
        )
        subprocess.run(
            [tmux, "select-pane", "-t", pane_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return


def _focus_native_lwa_pane() -> None:
    """Return keyboard focus to the LWA controller pane after local commands."""
    _focus_trace("request_lwa")
    tmux = shutil.which("tmux")
    pane_id = os.environ.get("TMUX_PANE")
    if not tmux or not pane_id:
        return
    try:
        subprocess.run(
            [tmux, "send-keys", "-t", pane_id, "-X", "cancel"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1,
            check=False,
        )
        subprocess.run(
            [tmux, "select-pane", "-t", pane_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return


def _focus_trace(event: str) -> None:
    """Write secret-free focus diagnostics when investigating pane handoff."""
    if os.environ.get("LWA_FOCUS_TRACE", "1").lower() in {"0", "false", "off", "no"}:
        return
    try:
        from .debug_log import write_startup_event

        write_startup_event("lwa-focus", event)
    except Exception:  # noqa: BLE001 - diagnostics must never affect input
        return


def _diagnostic_key_class(key: object) -> tuple[str, str | None]:
    """Classify input without retaining printable input or escape payloads."""
    if isinstance(key, tuple) and key and key[0] == "__LWA_MOUSE__":
        return "mouse_tuple", "mouse"
    if isinstance(key, tuple) and key and key[0] == "__LWA_PASTE__":
        return "paste_tuple", "paste"
    if isinstance(key, int):
        if key == 9:
            return "curses_code", "tab"
        if key in {10, 13}:
            return "curses_code", "enter"
        if key == 3:
            return "curses_code", "copy"
        if key == 17:
            return "curses_code", "quit"
        return "curses_code", None
    if not isinstance(key, str):
        return type(key).__name__, None
    normalized = {
        "__LWA_SHIFT_LEFT__": "shift-left",
        "__LWA_SHIFT_RIGHT__": "shift-right",
        "__LWA_SHIFT_UP__": "shift-up",
        "__LWA_SHIFT_DOWN__": "shift-down",
        "__LWA_SHIFT_TAB__": "shift-tab",
        "__LWA_ALT_ENTER__": "alt-enter",
        "\t": "tab",
        "\r": "enter",
        "\n": "newline",
        "\x03": "copy",
        "\x11": "quit",
        "\x1b": "escape",
    }.get(key)
    if normalized:
        return "control_sequence", normalized
    if len(key) == 1 and key.isprintable():
        return "text", None
    return "string", None


def _diagnostic_mouse_button(button: int) -> str:
    """Return a stable mouse class, excluding terminal-specific coordinates."""
    if button & 64:
        return "wheel"
    if button & 32:
        return "motion"
    return {0: "left", 1: "middle", 2: "right", 3: "release"}.get(button & 3, "other")


 
CODEX_SLASH_FOLLOWUPS = {
    "/pets": "optional pet name or action",
    "/permissions": "optional permission target or mode",
    "/model": "model name",
    "/mention": "file or path",
    "/mcp": "server or tool name",
    "/theme": "theme name",
}
LWA_SLASH_OPTIONS = (
    "/lwa mode semantic",
    "/lwa consensus",
    "/lwa pingpong on",
    "/lwa correct review",
)

_COLOR_PAIRS: dict[str, int] = {}


def renderer_capability() -> str:
    """Report the host renderer without claiming to replace it."""
    return detect_terminal_capabilities().renderer


def _initialize_colors() -> None:
    """Install optional semantic colors; curses remains usable without them."""
    _COLOR_PAIRS.clear()
    try:
        if not curses.has_colors():
            return
        curses.start_color()
        with suppress(curses.error):
            curses.use_default_colors()
        palette = (
            ("error", curses.COLOR_RED),
            ("warning", curses.COLOR_YELLOW),
            ("code", curses.COLOR_CYAN),
            ("status", curses.COLOR_GREEN),
            ("accent", curses.COLOR_MAGENTA),
        )
        for index, (name, color) in enumerate(palette, start=1):
            try:
                curses.init_pair(index, color, -1)
                _COLOR_PAIRS[name] = index
            except curses.error:
                continue
    except curses.error:
        _COLOR_PAIRS.clear()


def _semantic_attr(text: str) -> int:
    """Return a non-essential semantic color attribute for a feed line."""
    if not _COLOR_PAIRS:
        return 0
    if re.search(r"error|failed|exception|traceback", text, re.IGNORECASE):
        name = "error"
    elif re.search(r"warning|caution|risk", text, re.IGNORECASE):
        name = "warning"
    elif text.lstrip().startswith((">", "›", "$", "❯")):
        name = "status"
    elif re.search(r"```|\b(const|let|var|def|class|function|import|from)\b", text):
        name = "code"
    else:
        name = "accent" if text.strip() else "status"
    return curses.color_pair(_COLOR_PAIRS[name])


def _complete_codex_slash_command(text: str, cursor: int) -> tuple[str, int, list[str]]:
    """Complete the current slash-command token without changing arguments."""
    line_start = text.rfind("\n", 0, cursor) + 1
    token_start = max(line_start, text.rfind(" ", line_start, cursor) + 1)
    token = text[token_start:cursor]
    if not token.startswith("/"):
        return text, cursor, []
    matches = [command for command in CODEX_SLASH_COMMANDS if command.startswith(token)]
    if len(matches) != 1:
        return text, cursor, matches
    completed = matches[0]
    updated = text[:token_start] + completed + text[cursor:]
    return updated, cursor + len(completed) - len(token), matches


def _codex_slash_suggestions(text: str, cursor: int) -> list[str]:
    """Build Codex-owned prompt suggestions for the native pane."""
    line_start = text.rfind("\n", 0, cursor) + 1
    token_start = max(line_start, text.rfind(" ", line_start, cursor) + 1)
    token = text[token_start:cursor]
    if not token.startswith("/"):
        return []
    exact = text.strip()
    if exact in CODEX_SLASH_COMMANDS:
        followup = CODEX_SLASH_FOLLOWUPS.get(exact, "optional arguments")
        return [f"› {exact}  Run command", f"  {exact}  follow-up: {followup}"]
    matches = [command for command in CODEX_SLASH_COMMANDS if command.startswith(token)]
    return [f"› {command}" for command in matches[:5]]


def _lwa_slash_suggestions(text: str) -> list[str]:
    """Return local LWA modal options without forwarding them to Codex."""
    if text.strip() in {"/lwa", "/lwa "}:
        return list(LWA_SLASH_OPTIONS)
    return []


def _codex_modal_lines(lines: list[str]) -> list[str]:
    """Extract a bounded Codex-owned confirmation dialog from PTY history."""
    start = -1
    for index, line in enumerate(lines):
        if re.search(r"update model permissions|update permissions", line, re.IGNORECASE):
            start = index
    if start < 0:
        return []
    # Codex wraps this dialog according to PTY width. A narrow terminal can
    # therefore put the confirmation footer well beyond twelve logical lines.
    window = lines[start : min(len(lines), start + 40)]
    footer_index = next(
        (
            index
            for index, line in enumerate(window)
            if re.search(r"press enter to confirm|press esc to go back|esc to go back", line, re.IGNORECASE)
        ),
        -1,
    )
    # Keep the title and choices visible even while Codex is still painting
    # the dialog. The footer is not guaranteed to arrive in the same PTY
    # chunk, especially while the MCP status line is being redrawn.
    end = footer_index + 1 if footer_index >= 0 else min(len(window), 18)
    extracted = [redact_terminal_text(line) for line in window[:end] if line.strip()]
    if footer_index < 0:
        extracted.append("Press Enter to confirm · Esc to go back")
    return extracted[-18:]


def _add_line(screen: curses.window, row: int, text: str, columns: int, attr: int = 0) -> None:
    if 0 <= row < screen.getmaxyx()[0] and columns > 1:
        try:
            screen.addnstr(row, 0, text, max(1, columns - 1), attr)
        except curses.error:
            pass


def _frame_line(screen: curses.window, row: int, text: str, columns: int, attr: int = 0) -> None:
    """Draw one clipped line inside the ASCII LWA frame."""
    if columns < 4:
        _add_line(screen, row, text, columns, attr)
        return
    _add_line(screen, row, f"| {text[: max(0, columns - 4)]:<{max(0, columns - 4)}} |", columns, attr)


def _pane_line(screen: curses.window, row: int, column: int, width: int, text: str, attr: int = 0) -> None:
    if 0 <= row < screen.getmaxyx()[0] and width > 1:
        try:
            screen.addnstr(row, column, text[: max(1, width - 1)].ljust(max(1, width - 1)), max(1, width - 1), attr)
        except curses.error:
            pass


def _wrapped_lwa_lines(lines: list[str], width: int) -> list[tuple[int, int, str]]:
    """Return display rows mapped to source line and character offset."""
    result: list[tuple[int, int, str]] = []
    limit = max(1, width)
    for source_index, line in enumerate(lines):
        chunks = textwrap.wrap(
            line,
            width=limit,
            expand_tabs=True,
            replace_whitespace=False,
            drop_whitespace=False,
            break_long_words=True,
            break_on_hyphens=False,
        ) or [""]
        offset = 0
        for chunk in chunks:
            result.append((source_index, offset, chunk))
            offset += len(chunk)
    return result


def _copy_to_clipboard(text: str) -> str:
    """Copy text using the first clipboard helper available on the host."""
    commands = (
        ("xclip", ["xclip", "-selection", "clipboard"]),
        ("xsel", ["xsel", "--clipboard", "--input"]),
        ("wl-copy", ["wl-copy"]),
    )
    for name, command in commands:
        if shutil.which(name) is None:
            continue
        try:
            completed = subprocess.run(
                command,
                input=text,
                text=True,
                capture_output=True,
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if completed.returncode == 0:
            return name
    return ""


def _place_native_images(
    frames: list[ImageFrame],
    *,
    row: int,
    columns: int,
    renderer: str,
    column: int = 2,
    image_id: int | None = None,
    image_columns: int | None = None,
    tmux_target: str | None = None,
    preload_frames: list[ImageFrame] | None = None,
    clear_image_ids: list[int] | None = None,
    top_anchor: bool = False,
) -> int:
    """Place validated frames only on a Kitty/Ghostty-compatible native host.

    Curses owns the text grid. This small escape hatch runs after refresh so a
    graphics-capable terminal owns the pixel layer, while plain curses never
    receives image bytes or unknown control sequences.
    """
    if not frames or not ("kitty" in renderer.lower() or "ghostty" in renderer.lower()):
        return 0
    placed = 0
    try:
        output = sys.stdout

        def passthrough(sequence: str) -> str:
            if not os.environ.get("TMUX"):
                return sequence
            # tmux requires its passthrough DCS wrapper and doubled ESC bytes
            # before forwarding Kitty graphics to Ghostty/Kitty.
            return "\x1bPtmux;\x1b" + sequence.replace("\x1b", "\x1b\x1b") + "\x1b\\"

        absolute_origin: tuple[int, int] | None = None
        if os.environ.get("TMUX") and tmux_target:
            try:
                geometry = subprocess.run(
                    ["tmux", "display-message", "-p", "-t", tmux_target, "#{pane_left},#{pane_top},#{pane_width},#{pane_height}"],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=True,
                ).stdout.strip().split(",")
                if len(geometry) == 4:
                    left, top, width, height = (int(value) for value in geometry)
                    absolute_origin = (left, max(top, top + 1 if top_anchor else top + height - 8))
                    columns = width
            except (OSError, subprocess.SubprocessError, ValueError):
                absolute_origin = None

        animation_frames = frames[-96:]
        if clear_image_ids:
            # Clear only LWA-owned IDs, once per pet/session lifecycle. Do not
            # clear on frame replacement: that creates a visible loop blink.
            for stale_id in clear_image_ids:
                output.write(passthrough(kitty_delete_sequence(stale_id)))
        if tmux_target and preload_frames:
            for index, preload in enumerate(preload_frames):
                output.write(passthrough(kitty_transmit_sequence(preload, image_id=9001 + index)))
        for frame_index, frame in enumerate(animation_frames):
            requested_columns = image_columns or max(1, min(columns // 2, 24))
            safe_column = max(1, min(column, max(1, columns - requested_columns)))
            if tmux_target and image_id is not None and preload_frames:
                image_sequence = kitty_put_sequence(
                    image_id=image_id,
                    columns=requested_columns,
                    rows=6,
                )
            elif tmux_target and image_id is not None:
                # Variant C: Ghostty visibly accepts client-driven replacement
                # of one stable image id. This is the currently observed
                # working native baseline; preloaded placement is static on
                # the operator's host.
                image_sequence = kitty_graphics_sequence(
                    frame,
                    columns=requested_columns,
                    rows=6,
                    image_id=image_id,
                )
            else:
                image_sequence = kitty_graphics_sequence(
                    frame,
                    columns=requested_columns,
                    rows=6,
                    image_id=image_id,
                )
            if absolute_origin is not None:
                absolute_column = absolute_origin[0] + max(0, columns - requested_columns - 1)
                absolute_row = absolute_origin[1]
                output.write(passthrough(f"\x1b7\x1b[{max(1, absolute_row + 1)};{max(1, absolute_column + 1)}H{image_sequence}\x1b8"))
            else:
                output.write(f"\x1b7\x1b[{max(1, row + 1)};{safe_column}H")
                output.write(passthrough(image_sequence))
                output.write("\x1b8")
            placed += 1
        output.flush()
    except (OSError, UnicodeError):
        return 0
    return placed


def _latest_codex_response(lines: list[str]) -> str:
    """Return the latest non-empty response block from bounded Codex history."""
    index = len(lines) - 1
    while index >= 0 and not lines[index].strip():
        index -= 1
    end = index + 1
    while index >= 0 and lines[index].strip():
        index -= 1
    return "\n".join(lines[index + 1 : end]).strip()


def _insert_native_tab(editor: PromptEditor, key: object, *, native_split: bool) -> bool:
    """Keep native Tab navigation local to the prompt editor.

    Native pane movement is owned exclusively by Alt+Left/Alt+Right. Some
    terminals still deliver Tab or BackTab to curses despite tmux bindings,
    so both forms become a predictable five-space insertion instead of a
    focus transition.
    """
    backtab = getattr(curses, "KEY_BTAB", -999)
    if native_split and key in {9, "\t", backtab, "__LWA_SHIFT_TAB__"}:
        editor.insert("     ")
        return True
    return False


def _cursor_position(
    *,
    active_surface: str,
    cursor_column: int,
    prompt_row: int,
    rows: int,
    columns: int,
    left_width: int,
    native_split: bool,
) -> tuple[int, int] | None:
    """Return a bounded cursor location for the locally-owned surface."""
    if native_split and active_surface == "codex":
        # Codex owns the real cursor in its native tmux pane.
        return None
    pane_start = 3 if active_surface == "lwa" else left_width + 3
    pane_end = left_width - 2 if active_surface == "lwa" else columns - 2
    row = max(0, min(rows - 1, prompt_row))
    column = max(pane_start, min(pane_end, pane_start + max(0, cursor_column)))
    return row, column


def _sgr_left_drag(button: int, action: str) -> str | None:
    """Classify SGR left-button press, motion, and release events."""
    if button & 64:
        return None
    left_button = (button & 3) == 0
    if not left_button:
        return None
    if action == "m":
        return "release"
    if button & 32:
        return "motion"
    return "press"


def _draw_frame(
    screen: curses.window,
    *,
    codex_lines: list[str],
    lwa_lines: list[str],
    prompt: str,
    cursor: int = 0,
    active_surface: str,
    renderer: str,
    scroll_offset: int = 0,
    codex_prompt: str | None = None,
    codex_cursor: int | None = None,
    lwa_prompt: str | None = None,
    lwa_cursor: int | None = None,
    codex_prompt_selection: tuple[int, int] | None = None,
    lwa_prompt_selection: tuple[int, int] | None = None,
    lwa_scroll_offset: int = 0,
    selected_codex_lines: set[int] | None = None,
    selected_lwa_lines: set[int] | None = None,
    codex_suggestions: list[str] | None = None,
    lwa_suggestions: list[str] | None = None,
    native_split: bool = False,
    pet_lines: list[str] | None = None,
) -> tuple[int, int]:
    """Render left LWA and right Codex panes; return active prompt row/width."""
    rows, columns = screen.getmaxyx()
    if rows < 15 or columns < 24:
        _add_line(screen, 0, "LWA / CODEX (terminal too small; resize to continue)", columns, curses.A_BOLD)
        return max(0, rows - 1), columns

    geometry = PanelGeometry.from_screen(rows, columns, native_split=native_split)
    bottom = rows - 1
    left_width = geometry.left_width
    right_column = geometry.right_column
    right_width = geometry.right_width
    feed_start = geometry.feed_start
    lwa_prompt_heading = geometry.lwa_prompt_heading
    codex_prompt_heading = geometry.codex_prompt_heading
    feed_bottom = max(feed_start, codex_prompt_heading - 1)
    codex_height = geometry.feed_height
    border = "+" + "-" * max(0, columns - 2) + "+"
    _add_line(screen, 0, border, columns)
    _add_line(screen, 1, f"| LWA FRAME - {renderer}"[: max(0, columns - 1)], columns, curses.A_BOLD)
    for row in range(2, bottom):
        try:
            screen.addch(row, left_width, "│")
        except (AttributeError, curses.error):
            pass
    _pane_line(screen, 2, 1, left_width - 1, "LWA FEED · responses/status", curses.A_BOLD)
    if not native_split:
        _pane_line(screen, 2, right_column + 1, right_width - 1, "CODEX FEED", curses.A_BOLD)
    end = max(0, len(codex_lines) - max(0, scroll_offset))
    visible = codex_lines[max(0, end - codex_height) : end]
    for index in range(codex_height):
        line_number = max(0, end - codex_height) + index
        attr = _semantic_attr(visible[index] if index < len(visible) else "")
        if selected_codex_lines and line_number in selected_codex_lines:
            attr |= curses.A_REVERSE
        if not native_split:
            _pane_line(screen, feed_start + index, right_column + 1, right_width - 1, visible[index] if index < len(visible) else "", attr)
    lwa_display = _wrapped_lwa_lines(lwa_lines, max(1, left_width - 3))
    lwa_end = max(0, len(lwa_display) - max(0, lwa_scroll_offset))
    lwa_feed_visible = lwa_display[max(0, lwa_end - max(1, feed_bottom - feed_start)) : lwa_end]
    for index in range(max(1, feed_bottom - feed_start)):
        source_number, _offset, display_text = lwa_feed_visible[index] if index < len(lwa_feed_visible) else (-1, 0, "")
        attr = _semantic_attr(display_text) if display_text else 0
        if selected_lwa_lines and source_number in selected_lwa_lines:
            attr |= curses.A_REVERSE
        _pane_line(screen, feed_start + index, 1, left_width - 1, display_text, attr)
    separator_row = max(feed_start, lwa_prompt_heading - 4)
    _pane_line(screen, separator_row, 1, left_width - 1, "─" * max(1, left_width - 2), curses.A_DIM)
    if pet_lines:
        pet_top = max(feed_start, lwa_prompt_heading - min(4, len(pet_lines)) - 1)
        for index, line in enumerate(pet_lines[-4:]):
            _pane_line(screen, pet_top + index, 2, left_width - 3, line, _semantic_attr(line))
    scrollbar_column = columns - 2 if native_split else left_width - 1
    if len(lwa_display) > max(1, feed_bottom - feed_start):
        track_height = max(1, feed_bottom - feed_start)
        thumb_height = max(1, track_height * track_height // len(lwa_display))
        max_offset = max(1, len(lwa_display) - track_height)
        thumb_top = feed_start + (track_height - thumb_height) * min(lwa_scroll_offset, max_offset) // max_offset
        for row in range(feed_start, feed_start + track_height):
            glyph = "█" if thumb_top <= row < thumb_top + thumb_height else "│"
            _pane_line(screen, row, scrollbar_column, 2, glyph, curses.A_DIM)

    modal_lines = [] if native_split else _codex_modal_lines(codex_lines)
    if modal_lines:
        modal_height = min(len(modal_lines) + 2, max(3, codex_prompt_heading - feed_start - 1))
        modal_top = max(feed_start + 1, codex_prompt_heading - modal_height - 1)
        modal_width = max(8, right_width - 2)
        _pane_line(screen, modal_top, right_column + 1, modal_width, "+" + "-" * max(1, modal_width - 3) + "+", curses.A_BOLD)
        for index, line in enumerate(modal_lines[: modal_height - 2], start=1):
            _pane_line(screen, modal_top + index, right_column + 1, modal_width, "| " + line + " |", _semantic_attr(line))
        _pane_line(screen, modal_top + modal_height - 1, right_column + 1, modal_width, "+" + "-" * max(1, modal_width - 3) + "+", curses.A_BOLD)

    codex_marker = "*" if active_surface == "codex" else " "
    lwa_marker = "*" if active_surface == "lwa" else " "
    codex_prompt = prompt if codex_prompt is None else codex_prompt
    lwa_prompt = prompt if lwa_prompt is None else lwa_prompt
    codex_cursor = cursor if codex_cursor is None else codex_cursor
    lwa_cursor = cursor if lwa_cursor is None else lwa_cursor

    def prompt_view(value: str, position: int) -> tuple[list[str], int, int, int]:
        lines = value.split("\n") or [""]
        before = value[:position].split("\n")
        current_line = len(before) - 1
        if len(lines) == 1:
            visible_start = -1
        else:
            visible_start = max(0, min(current_line, len(lines) - 2))
        visible = lines[visible_start:] if visible_start == -1 else lines[visible_start : visible_start + 2]
        if len(visible) == 1:
            visible.insert(0, "")
        return visible, len(before[-1]), current_line - visible_start, 0 if visible_start == -1 else visible_start

    codex_visible, _codex_column, codex_offset, codex_start_line = prompt_view(codex_prompt, codex_cursor)
    lwa_visible, _lwa_column, lwa_offset, lwa_start_line = prompt_view(lwa_prompt, lwa_cursor)

    def draw_prompt_lines(row, column, width, prefix, lines, start_line, value, selection):
        line_starts = []
        position = 0
        for line in value.split("\n"):
            line_starts.append(position)
            position += len(line) + 1
        for index, line in enumerate(lines[:2]):
            _pane_line(screen, row + index, column, width, prefix + line)
            if selection is None:
                continue
            global_start = line_starts[min(start_line + index, len(line_starts) - 1)]
            overlap_start = max(selection[0], global_start)
            overlap_end = min(selection[1], global_start + len(line))
            if overlap_start >= overlap_end:
                continue
            highlight_column = column + len(prefix) + overlap_start - global_start
            highlight = line[overlap_start - global_start : overlap_end - global_start]
            try:
                screen.addnstr(row + index, highlight_column, highlight, len(highlight), curses.A_REVERSE)
            except curses.error:
                pass

    lwa_title = f"{lwa_marker} LWA PROMPT · draft only"
    if lwa_prompt_selection:
        lwa_title += f" · selected {lwa_prompt_selection[1] - lwa_prompt_selection[0]} chars"
    _pane_line(screen, lwa_prompt_heading, 1, left_width - 1, lwa_title, curses.A_BOLD)
    draw_prompt_lines(
        lwa_prompt_heading + 1, 1, left_width - 1,
        "> " if active_surface == "lwa" else "  ", lwa_visible, lwa_start_line,
        lwa_prompt, lwa_prompt_selection,
    )
    if not native_split:
        _pane_line(screen, codex_prompt_heading, right_column + 1, right_width - 1, f"{codex_marker} CODEX PROMPT (direct PTY input)", curses.A_BOLD)
        draw_prompt_lines(
            codex_prompt_heading + 1, right_column + 1, right_width - 1,
            "> " if active_surface == "codex" else "  ", codex_visible, codex_start_line,
            codex_prompt, codex_prompt_selection,
        )
        for index, suggestion in enumerate((codex_suggestions or [])[:2]):
            _pane_line(screen, codex_prompt_heading + 3 + index, right_column + 1, right_width - 1, suggestion, _semantic_attr(suggestion))
    if lwa_suggestions:
        _pane_line(screen, lwa_prompt_heading - 3, 1, left_width - 1, "LWA COMMAND MODAL · Enter choose · Esc close", curses.A_BOLD)
        for index, suggestion in enumerate(lwa_suggestions[:2]):
            _pane_line(screen, lwa_prompt_heading - 2 + index, 1, left_width - 1, suggestion, _semantic_attr(suggestion))
    navigation_hint = (
        "Alt+Left: LWA | Alt+Right: Codex"
        if native_split
        else "Tab/Shift+Tab: switch pane"
    )
    _pane_line(screen, rows - 3, 1, columns - 1, f"{navigation_hint} | Enter: submit | Alt+Enter: send Codex | Ctrl-C: copy | Ctrl-Q: exit")
    _pane_line(screen, rows - 2, 1, columns - 1, "LWA controller · Codex native right pane" if native_split else "LWA left · Codex right · pane-local scroll and selection")
    _add_line(screen, bottom, border, columns)
    active_offset = codex_offset if active_surface == "codex" else lwa_offset
    active_heading = codex_prompt_heading if active_surface == "codex" else lwa_prompt_heading
    prompt_row = active_heading + 2 if active_offset else active_heading + 1
    return prompt_row, columns


def _read_key(screen: curses.window):
    """Read one key while swallowing a terminal mouse escape sequence."""
    try:
        key = screen.get_wch()
    except curses.error:
        return None
    if isinstance(key, str):
        for opener in ("\x1b[200~", "[200~"):
            if opener in key:
                payload = key.split(opener, 1)[1]
                if "\x1b[201~" in payload:
                    payload = payload.split("\x1b[201~", 1)[0]
                    return ("__LWA_PASTE__", payload)
                return _read_bracketed_paste(screen, payload)
    # Some terminal adapters return the complete graphics response as one
    # string instead of delivering it character-by-character.
    if isinstance(key, str) and key.startswith("\x1b_G"):
        return "__LWA_GRAPHICS_RESPONSE__"
    if key != "\x1b":
        return key
    # Mouse reporting commonly begins with ESC [ < ... M. With nodelay
    # enabled, consume the already-buffered sequence instead of treating its
    # ESC prefix as LWA exit.
    mappings = {
        "[A": getattr(curses, "KEY_UP", None),
        "[B": getattr(curses, "KEY_DOWN", None),
        "[C": getattr(curses, "KEY_RIGHT", None),
        "[D": getattr(curses, "KEY_LEFT", None),
        "[5~": getattr(curses, "KEY_PPAGE", None),
        "[6~": getattr(curses, "KEY_NPAGE", None),
        "[3~": getattr(curses, "KEY_DC", None),
        "[1;2A": "__LWA_SHIFT_UP__",
        "[1;2B": "__LWA_SHIFT_DOWN__",
        "[1;2C": "__LWA_SHIFT_RIGHT__",
        "[1;2D": "__LWA_SHIFT_LEFT__",
        "[Z": "__LWA_SHIFT_TAB__",
        "[13;4u": "__LWA_TRANSFER_RESPONSE__",
        "[13;4~": "__LWA_TRANSFER_RESPONSE__",
        "[27;4;13~": "__LWA_TRANSFER_RESPONSE__",
    }
    buffered = []
    try:
        for _ in range(32):
            next_key = screen.get_wch()
            if next_key is None:
                break
            if next_key == "\t":
                return "\t"
            if next_key in {"\r", "\n"}:
                return "__LWA_ALT_ENTER__"
            if next_key == "_" or (isinstance(next_key, str) and next_key.startswith("_G")):
                # Kitty/Ghostty may acknowledge an image transmit with a
                # response such as ESC_Gi=9001;OK ESC\\. It is terminal
                # protocol, never prompt input, and must not become an Esc
                # exit followed by leaked text in the user's shell.
                response = [next_key]
                if isinstance(next_key, str) and next_key.startswith("_G") and response[-1].endswith("\\"):
                    return "__LWA_GRAPHICS_RESPONSE__"
                try:
                    for _ in range(128):
                        value = screen.get_wch()
                        response.append(value)
                        if len(response) >= 2 and response[-2:] == ["\x1b", "\\"]:
                            return "__LWA_GRAPHICS_RESPONSE__"
                except (curses.error, StopIteration):
                    return "__LWA_GRAPHICS_RESPONSE__"
                return "__LWA_GRAPHICS_RESPONSE__"
            if isinstance(next_key, str) and next_key.startswith("["):
                if next_key == "[200~":
                    return _read_bracketed_paste(screen)
                if next_key.startswith("[200~"):
                    return _read_bracketed_paste(screen, next_key[5:])
                if next_key in mappings:
                    return mappings[next_key]
                if next_key in {"[13;3u", "[13;3~", "[27;3;13~", "[13;3;1~"}:
                    return "__LWA_ALT_ENTER__"
                if next_key in {"[13;2u", "[13;2~", "[27;2;13~", "[13;2;1~"}:
                    return "\n"
            buffered.append(next_key)
            if isinstance(next_key, str) and len(buffered) > 1 and "@" <= next_key <= "~":
                if buffered and buffered[0] == "[":
                    sequence = "".join(buffered)
                    if sequence == "[200~":
                        return _read_bracketed_paste(screen)
                    if sequence.startswith("[<") and sequence[-1:] in {"M", "m"}:
                        try:
                            button, x, y = sequence[2:-1].split(";", 2)
                            return ("__LWA_MOUSE__", int(button), int(x) - 1, int(y) - 1, sequence[-1])
                        except ValueError:
                            return None
                    if sequence in {"[1;2A", "[1;2B"}:
                        return mappings[sequence]
                    if sequence in {"[13;4u", "[13;4~", "[27;4;13~"}:
                        return "__LWA_TRANSFER_RESPONSE__"
                    if sequence in {"[13;2u", "[13;2~", "[27;2;13~", "[13;2;1~"}:
                        return "\n"
                    if sequence in {"[13;3u", "[13;3~", "[27;3;13~", "[13;3;1~"}:
                        return "__LWA_ALT_ENTER__"
                    return mappings.get(sequence)
                break
    except (curses.error, StopIteration):
        pass
    return "\x1b"


def _read_bracketed_paste(screen: curses.window, initial: str = "") -> tuple[str, str]:
    """Read a terminal bracketed-paste payload without submitting it."""
    pasted: list[str] = [initial]
    try:
        while True:
            value = screen.get_wch()
            if value in {"[201~", "\x1b[201~"}:
                return ("__LWA_PASTE__", "".join(pasted))
            if value != "\x1b":
                pasted.append(value)
                continue
            sequence = ["\x1b"]
            for _ in range(5):
                sequence.append(screen.get_wch())
                if "".join(sequence) == "\x1b[201~":
                    return ("__LWA_PASTE__", "".join(pasted))
            pasted.extend(sequence)
    except (curses.error, StopIteration):
        return ("__LWA_PASTE__", "".join(pasted))


def _set_bracketed_paste(enabled: bool) -> None:
    """Ask the host terminal to delimit clipboard paste payloads."""
    sequence = ("\x1b[?2004h" if enabled else "\x1b[?2004l")
    try:
        output = sys.stdout
        if output.isatty():
            output.write(sequence)
            output.flush()
            return
    except (OSError, ValueError):
        pass
    try:
        curses.putp(sequence.encode())
    except (curses.error, TypeError):
        pass


def _codex_submission(text: str) -> str:
    """Paste a reviewed prompt, then submit it with one terminal Return.

    Raw newlines in a multiline prompt are interpreted as Enter by many TUI
    applications. Bracketed paste makes Codex treat them as prompt content;
    the trailing CR remains the user's single submit action.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    return "\x1b[200~" + normalized + "\x1b[201~\r"


async def _interactive(
    screen: curses.window,
    executable: str,
    bridge_socket: str | None = None,
    native_tmux_pane: str | None = None,
) -> int:
    try:
        curses.curs_set(1)
    except curses.error:
        pass
    _initialize_colors()
    screen.keypad(True)
    screen.nodelay(True)
    try:
        mouse_mask = curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.mouseinterval(0)
        _focus_trace(f"mouse_config curses_mask={int(mouse_mask[0]) if mouse_mask else 0} tmux={bool(native_tmux_pane)}")
    except curses.error:
        pass
    try:
        curses.curs_set(1)
    except curses.error:
        pass
    # Kitty/Ghostty otherwise blink the software cursor again on every full
    # curses repaint. A steady block keeps the active prompt discoverable.
    if "kitty" in renderer_capability().lower() or "ghostty" in renderer_capability().lower():
        try:
            sys.stdout.write("\x1b[2 q")
            sys.stdout.flush()
        except (OSError, UnicodeError):
            pass
    # Preserve CR (Return) separately from LF (Ctrl-J/newline insertion).
    try:
        curses.nonl()
    except curses.error:
        pass
    _set_bracketed_paste(True)

    codex_lines = []
    codex_buffer = TerminalTextBuffer()
    # Small, non-sensitive boot screen for the LWA side in every renderer.
    lwa_lines = BoundedLines([
        "LWA bootscreen · controller ready.",
        r" /\_/\\",
        "( o.o )",
        " > ^ <",
    ], max_lines=budget_int("LWA_MAX_FEED_LINES", 240, minimum=80, maximum=2000))
    editors = {"codex": PromptEditor(), "lwa": PromptEditor()}
    active_surface = "lwa"
    focus_broker = FocusBroker(
        mode="native" if native_tmux_pane else "embedded",
        initial=Surface.LWA,
    )
    session_active = True
    pipeline_busy = False
    pipeline_task: asyncio.Task[None] | None = None
    codex_scroll = 0
    selection_anchor: int | None = None
    selection_focus: int | None = None
    lwa_selection_anchor: tuple[int, int] | None = None
    lwa_selection_focus: tuple[int, int] | None = None
    clipboard_task: asyncio.Task[None] | None = None
    last_geometry: tuple[int, int] | None = None
    native_frames: list[ImageFrame] = []
    native_pet_frames: list[ImageFrame] = []
    native_pet_playback: PetPlaybackState | None = None
    native_pet_generation = 0
    native_pet_idle_frames: list[ImageFrame] = []
    native_pet_action_tracks: tuple[list[ImageFrame], ...] = ()
    native_pet_track: list[ImageFrame] = []
    native_pet_action_number = 0
    native_pet_action_until = 0.0
    native_pet_track_name = "idle"
    native_pet_index = 0
    native_pet_last = 0.0
    native_pet_placed: tuple[int, int, int, str, str, int] | None = None
    native_pet_cleanup_done = False
    native_pet_response_pending = False
    native_pet_state = PetSemanticState.IDLE
    native_pet_name: str | None = None
    pet_text_lines: list[str] = []
    codex_suggestions: list[str] = []
    lwa_suggestions: list[str] = []
    lwa_scroll = 0
    last_render_signature: object = None
    last_render_at = 0.0
    last_cursor_trace: tuple[str, int, int, bool] | None = None
    redraw_interval = budget_float(
        "LWA_REDRAW_INTERVAL", 0.04, minimum=0.02, maximum=0.25
    )

    def focus_effect(target: Surface) -> bool:
        """Apply the broker's decision to the terminal-specific adapter."""
        if native_tmux_pane and target is Surface.CODEX:
            _focus_native_codex_pane(native_tmux_pane)
        elif native_tmux_pane and target is Surface.LWA:
            _focus_native_lwa_pane()
        return True

    def focus_to(target: Surface, source: str) -> None:
        """Transition focus once, then synchronize legacy drawing state."""
        nonlocal active_surface
        event = PanelEvent.FOCUS_CODEX if target is Surface.CODEX else PanelEvent.FOCUS_LWA
        transition = focus_broker.transition(event, effect=focus_effect)
        active_surface = transition.target.value
        _focus_trace(
            "focus_transition "
            f"source={transition.source.value} target={transition.target.value} "
            f"event={transition.event} mode={transition.mode} source_input={source} "
            f"result={transition.result}"
        )

    def focus_next(source: str, *, previous: bool = False) -> None:
        nonlocal active_surface
        transition = (
            focus_broker.focus_previous(effect=focus_effect)
            if previous
            else focus_broker.focus_next(effect=focus_effect)
        )
        active_surface = transition.target.value
        _focus_trace(
            "focus_transition "
            f"source={transition.source.value} target={transition.target.value} "
            f"event={transition.event} mode={transition.mode} source_input={source} "
            f"result={transition.result}"
        )

    def refresh_independent_pet(name_override: str | None = None) -> None:
        nonlocal native_pet_index, native_pet_placed, native_pet_cleanup_done
        nonlocal native_pet_idle_frames, native_pet_action_tracks, native_pet_track
        nonlocal native_pet_track_name, native_pet_playback, native_pet_generation, native_pet_action_until
        nonlocal native_pet_action_number, native_pet_name
        try:
            pet = render_configured_pet(override=name_override, renderer=renderer_capability())
            if pet is None:
                requested = name_override or "configured"
                lwa_lines.append(f"Pet unavailable: no valid Codex asset for {requested}.")
                return
            candidate = build_pet_playback_state(pet, generation=native_pet_generation + 1)
        except Exception as exc:  # noqa: BLE001 - a bad optional pet must not kill the TUI
            lwa_lines.append(f"Pet switch rejected: {redact_terminal_text(str(exc))}")
            return
        native_pet_generation = candidate.generation
        native_pet_playback = candidate
        native_pet_name = pet.name
        lwa_lines.append(f"Pet loaded: {pet.name}.")
        pet_text_lines[:] = [f"PET · {pet.name}", *pet.text_fallback.splitlines()]
        if "kitty" in renderer_capability().lower() or "ghostty" in renderer_capability().lower():
            native_pet_frames[:] = list(candidate.frames)
            native_pet_idle_frames = list(candidate.idle)
            native_pet_action_tracks = tuple(list(track) for track in candidate.actions)
            native_pet_track = list(candidate.welcome or pet_track_for_state(candidate, native_pet_state))
            native_pet_track_name = "welcome" if candidate.welcome else native_pet_state.value
            native_pet_index = 0
            native_pet_placed = None
            native_pet_cleanup_done = False
            native_pet_action_until = 0.0
            native_pet_action_number = 0
        else:
            lwa_lines.append(pet.text_fallback)

    def set_pet_state(state: PetSemanticState) -> None:
        nonlocal native_pet_state, native_pet_index, native_pet_track, native_pet_track_name, native_pet_placed
        native_pet_state = state
        if native_pet_playback is None:
            return
        native_pet_track = list(pet_track_for_state(native_pet_playback, state))
        native_pet_track_name = state.value
        native_pet_index = 0
        native_pet_placed = None

    def trigger_pet_action() -> None:
        nonlocal native_pet_action_number, native_pet_action_until, native_pet_index, native_pet_track, native_pet_track_name, native_pet_placed, native_pet_state
        if not native_pet_action_tracks:
            set_pet_state(PetSemanticState.RUNNING)
            return
        now = time.monotonic()
        if now < native_pet_action_until:
            return
        track_index = native_pet_action_number % len(native_pet_action_tracks)
        native_pet_action_number += 1
        native_pet_track = native_pet_action_tracks[track_index]
        native_pet_track_name = f"action-{track_index + 1}"
        native_pet_index = 0
        native_pet_placed = None
        native_pet_action_until = now + len(native_pet_track) * NATIVE_PET_ACTION_INTERVAL
        native_pet_state = PetSemanticState.RUNNING

    def trigger_pet_completion() -> None:
        nonlocal native_pet_action_until, native_pet_index, native_pet_track, native_pet_track_name, native_pet_placed
        if native_pet_playback is None or not native_pet_playback.completion:
            return
        native_pet_track = list(native_pet_playback.completion)
        native_pet_track_name = "completion"
        native_pet_index = 0
        native_pet_placed = None
        native_pet_action_until = time.monotonic() + len(native_pet_track) * NATIVE_PET_ACTION_INTERVAL
        set_pet_state(PetSemanticState.READY)

    def lwa_selected_text(
        anchor: tuple[int, int], focus: tuple[int, int]
    ) -> tuple[str, int, int]:
        start, stop = sorted((anchor, focus))
        if start[0] == stop[0]:
            return lwa_lines[start[0]][start[1] : stop[1]], start[0], stop[0]
        parts = [lwa_lines[start[0]][start[1] :]]
        parts.extend(lwa_lines[start[0] + 1 : stop[0]])
        parts.append(lwa_lines[stop[0]][: stop[1]])
        return "\n".join(parts), start[0], stop[0]

    def lwa_selection_point(mouse_x: int, mouse_y: int, rows: int) -> tuple[int, int] | None:
        feed_start = 3
        feed_height = max(1, max(feed_start, rows - 10) - feed_start)
        display = _wrapped_lwa_lines(lwa_lines, max(1, columns - 4))
        feed_end = max(0, len(display) - lwa_scroll)
        first = max(0, feed_end - feed_height)
        display_index = first + mouse_y - feed_start
        if not (feed_start <= mouse_y < feed_start + feed_height and 0 <= display_index < feed_end):
            return None
        source_line, offset, text = display[display_index]
        column = offset + max(0, min(len(text), mouse_x - 1))
        return source_line, column

    def classify_pet_event(message: str, state: object) -> PetSemanticState | None:
        """Map portable status text to a semantic pet state."""
        value = str(state or "").lower()
        text = message.lower()
        if value in {"error", "failed", "blocked", "exception"} or re.search(
            r"\b(error|failed|failure|exception|crash|blocked)\b", text
        ):
            return PetSemanticState.BLOCKED
        if value in {"needs-input", "approval", "waiting", "input-required"} or re.search(
            r"\b(approval|approve|permission|confirm|waiting for|needs input|question)\b", text
        ):
            return PetSemanticState.NEEDS_INPUT
        if value in {"completed", "complete", "ready", "success", "finished"} or re.search(
            r"\b(completed|complete|ready|success|finished)\b", text
        ):
            return PetSemanticState.READY
        if value in {"running", "working", "processing", "starting"} or re.search(
            r"\b(running|working|processing|executing|reasoning|starting)\b", text
        ):
            return PetSemanticState.RUNNING
        return None

    async def emit(event: dict[str, object]) -> None:
        nonlocal codex_scroll, session_active, native_pet_response_pending
        kind = event.get("type")
        if kind == "terminal":
            clean = visible_text(str(event.get("data", "")))
            codex_buffer.feed(clean)
            codex_lines[:] = codex_buffer.lines
            codex_scroll = 0
            # PTY hosts do not share a portable response-complete event. The
            # first visible bytes after a direct submission are the stable
            # cross-terminal signal for the completion track.
            if clean.strip() and native_pet_response_pending:
                native_pet_response_pending = False
                set_pet_state(PetSemanticState.RUNNING)
        elif kind in {"status", "session"}:
            message = str(event.get("message", event.get("state", "session event")))
            lwa_lines.append(message)
            del lwa_lines[:-80]
            event_state = classify_pet_event(message, event.get("state"))
            if event_state is not None:
                set_pet_state(event_state)
            if event.get("state") in {"exited", "error"}:
                session_active = False
        elif kind == "graphics":
            if event.get("state") == "fallback":
                lwa_lines.append(f"Graphics fallback: {event.get('message', 'unsupported image payload')}")
            elif event.get("frame"):
                frame_data = event["frame"]
                if isinstance(frame_data, dict):
                    try:
                        native_frames.append(
                            ImageFrame(
                                str(frame_data["mime_type"]),
                                str(frame_data["data_base64"]),
                                int(frame_data["byte_length"]),
                                int(frame_data["width"]) if frame_data.get("width") else None,
                                int(frame_data["height"]) if frame_data.get("height") else None,
                            )
                        )
                        del native_frames[:-4]
                    except (KeyError, TypeError, ValueError):
                        lwa_lines.append("Graphics fallback: invalid image frame")

    async def copy_selection(text: str, start: int, stop: int, label: str = "Codex") -> None:
        copied = await asyncio.to_thread(_copy_to_clipboard, text)
        lwa_lines.append(
            f"Copied {label} output lines {start + 1}-{stop + 1} via {copied or 'no clipboard helper'}."
        )

    async def copy_prompt_text(text: str, label: str) -> None:
        copied = await asyncio.to_thread(_copy_to_clipboard, text)
        lwa_lines.append(f"Copied {label} via {copied or 'no clipboard helper'}.")

    async def run_lwa_pipeline(prompt_text: str) -> None:
        """Improve an LWA draft through consensus and load it for review in Codex Prompt."""
        nonlocal active_surface, pipeline_busy
        try:
            from .service import RouterService

            lwa_lines.append("LWA pipeline: preparing prompt-improvement consensus...")
            service = RouterService()
            await service.initialize()
            improvement_request = (
                "Improve the following user draft into a precise, complete, high-quality prompt "
                "for Codex. Preserve the user's intent and important constraints. Return only "
                "the final Codex-ready prompt, with no commentary about the editing process.\n\n"
                "USER DRAFT:\n"
                f"{prompt_text}"
            )
            prepared = await service.prepare_consensus(improvement_request)
            summary = prepared.get("preflight", {})
            if not summary.get("working_may_begin"):
                confirmation = summary.get("confirmation_token")
                if not confirmation:
                    raise RuntimeError("LWA consensus requires an approval gate before provider work")
                service.approve_preflight(confirmation)
            lwa_lines.append("LWA pipeline: consensus providers working...")
            result = await service.run_prepared_task(summary["plan_token"])
            if result.get("status") != "completed":
                detail = result.get("error") or result.get("message") or "LWA consensus did not complete"
                raise RuntimeError(f"LWA consensus stopped: {detail}")
            synthesis = result.get("synthesis", {})
            synthesized_text = str(synthesis.get("text", "")).strip()
            if not synthesized_text:
                raise RuntimeError("LWA consensus completed without a synthesized response")
            if not session_active:
                raise RuntimeError("Codex session ended before LWA consensus completed")
            codex_editor = editors["codex"]
            codex_editor.text = synthesized_text
            codex_editor.cursor = len(synthesized_text)
            trigger_pet_completion()
            focus_to(Surface.LWA if native_tmux_pane else Surface.CODEX, "lwa-pipeline")
            lwa_lines.append(
                f"LWA pipeline: prompt improvement complete; Codex Prompt loaded ({len(synthesized_text)} chars). Press Alt+Enter to send."
            )
        except Exception as exc:  # noqa: BLE001
            set_pet_state(PetSemanticState.BLOCKED)
            lwa_lines.append(f"LWA pipeline stopped: {redact_terminal_text(str(exc))}")
        finally:
            pipeline_busy = False

    async def run_debug_snapshot(rows: int, columns: int) -> None:
        nonlocal pipeline_busy
        try:
            from .debug_log import collect_debug_snapshot, format_debug_snapshot, write_debug_log

            snapshot = await asyncio.to_thread(
                collect_debug_snapshot,
                executable=executable,
                session_active=session_active,
                pipeline_busy=pipeline_busy,
                scroll_offset=codex_scroll,
                rows=rows,
                columns=columns,
            )
            path = await asyncio.to_thread(write_debug_log, snapshot)
            lwa_lines.extend(format_debug_snapshot(snapshot, path))
        except Exception as exc:  # noqa: BLE001
            lwa_lines.append(f"Debug collection stopped: {redact_terminal_text(str(exc))}")
        finally:
            pipeline_busy = False

    if native_tmux_pane:
        session = NativeTmuxCodexSession(emit, native_tmux_pane)
    elif bridge_socket:
        session = BridgeCodexSession(emit, bridge_socket)
    else:
        try:
            session = CodexSession(emit, executable, disable_lwa_mcp=True)
        except TypeError as exc:
            if "disable_lwa_mcp" not in str(exc):
                raise
            session = CodexSession(emit, executable)
    lifecycle = PanelLifecycle(session.close)
    await session.start()
    if native_tmux_pane or bridge_socket:
        if not session.is_running:
            return 127
    elif session.process is None:
        return 127
    # Codex's TUI does not reliably accept input until the PTY has a real
    # geometry. Establish it before the first frame/input event.
    initial_rows, initial_columns = screen.getmaxyx()
    try:
        # tmux owns the native Codex pane geometry. Resizing it from the LWA
        # pane feeds the left pane's dimensions back into the right pane and
        # causes a repaint/resize loop in native split mode.
        if not native_tmux_pane:
            await session.resize(max(20, initial_columns), max(8, initial_rows))
        last_geometry = (max(20, initial_columns), max(8, initial_rows))
        # Codex suppresses pets under tmux. LWA therefore owns this reliable
        # compatibility mirror and places it at the Codex-side coordinates.
        refresh_independent_pet()
        if native_tmux_pane:
            # tmux gives focus to the newly-created Codex pane after split.
            # LWA commands, including /pets, must start in the LWA controller.
            _focus_native_lwa_pane()
    except RuntimeError as exc:
        session_active = False
        lwa_lines.append(str(exc))

    try:
        while True:
            rows, columns = screen.getmaxyx()
            geometry = (max(20, columns), max(8, rows))
            if session_active and not native_tmux_pane and geometry != last_geometry:
                try:
                    await session.resize(*geometry)
                except RuntimeError as exc:
                    session_active = False
                    lwa_lines.append(str(exc))
                last_geometry = geometry

            render_signature = (
                rows,
                columns,
                active_surface,
                editors["lwa"].text,
                editors["lwa"].cursor,
                editors["codex"].text,
                editors["codex"].cursor,
                len(codex_lines),
                codex_lines[-1] if codex_lines else "",
                len(lwa_lines),
                lwa_lines[-1] if lwa_lines else "",
                codex_scroll,
                lwa_scroll,
                pipeline_busy,
                native_pet_index,
                native_pet_track_name,
                native_pet_generation,
            )
            if not redraw_due(
                last_render_signature,
                render_signature,
                last_render_at,
                minimum_interval=redraw_interval,
            ):
                await asyncio.sleep(0.02)
                continue
            last_render_signature = render_signature
            last_render_at = time.monotonic()

            screen.erase()
            prompt_row, frame_columns = _draw_frame(
                screen,
                codex_lines=codex_lines,
                lwa_lines=lwa_lines,
                prompt="",
                cursor=0,
                active_surface=active_surface,
                renderer=renderer_capability(),
                scroll_offset=codex_scroll,
                codex_prompt=editors["codex"].text,
                codex_cursor=editors["codex"].cursor,
                codex_prompt_selection=editors["codex"].selection,
                lwa_prompt=editors["lwa"].text,
                lwa_cursor=editors["lwa"].cursor,
                lwa_prompt_selection=editors["lwa"].selection,
                lwa_scroll_offset=lwa_scroll,
                selected_codex_lines=(
                    set(range(min(selection_anchor, selection_focus), max(selection_anchor, selection_focus) + 1))
                    if selection_anchor is not None and selection_focus is not None
                    else None
                ),
                selected_lwa_lines=(
                    set(
                        range(
                            min(lwa_selection_anchor[0], lwa_selection_focus[0]),
                            max(lwa_selection_anchor[0], lwa_selection_focus[0]) + 1,
                        )
                    )
                    if lwa_selection_anchor is not None and lwa_selection_focus is not None
                    else None
                ),
                codex_suggestions=codex_suggestions,
                lwa_suggestions=lwa_suggestions,
                native_split=bool(native_tmux_pane),
                pet_lines=(
                    pet_text_lines
                    if not ("kitty" in renderer_capability().lower() or "ghostty" in renderer_capability().lower())
                    else []
                ),
            )
            try:
                left_width = max(28, min(frame_columns // 3, 48))
                editor = editors[active_surface]
                cursor_column = len(editor.text[: editor.cursor].split("\n")[-1])
                cursor_position = _cursor_position(
                    active_surface=active_surface,
                    cursor_column=cursor_column,
                    prompt_row=prompt_row,
                    rows=rows,
                    columns=frame_columns,
                    left_width=left_width,
                    native_split=bool(native_tmux_pane),
                )
                if cursor_position is not None:
                    screen.move(*cursor_position)
                    cursor_owner = "codex" if native_tmux_pane and active_surface == "codex" else "lwa"
                    cursor_trace = (cursor_owner, cursor_position[0], cursor_position[1], True)
                    if cursor_trace != last_cursor_trace:
                        _focus_trace(
                            f"cursor owner={cursor_owner} row={cursor_position[0]} "
                            f"column={cursor_position[1]} visible=true"
                        )
                        last_cursor_trace = cursor_trace
            except curses.error:
                pass
            screen.refresh()
            if native_frames:
                placed = _place_native_images(native_frames, row=3, columns=frame_columns, renderer=renderer_capability())
                if placed:
                    native_frames.clear()
            track_interval = (
                NATIVE_PET_IDLE_INTERVAL
                if native_pet_track_name == "idle"
                else NATIVE_PET_ACTION_INTERVAL
            )
            if native_pet_frames and (time.monotonic() - native_pet_last) >= track_interval:
                native_pet_last = time.monotonic()
                next_index = native_pet_index + 1
                if next_index >= len(native_pet_track):
                    if native_pet_state in {PetSemanticState.RUNNING, PetSemanticState.READY} and not native_pet_response_pending:
                        set_pet_state(PetSemanticState.IDLE)
                        next_index = 0
                    elif native_pet_playback is not None:
                        native_pet_track = list(pet_track_for_state(native_pet_playback, native_pet_state))
                        native_pet_track_name = native_pet_state.value
                    else:
                        native_pet_track = native_pet_idle_frames or native_pet_frames
                        native_pet_track_name = PetSemanticState.IDLE.value
                    next_index = 0
                native_pet_index = next_index
                native_pet_placed = None
            pet_signature = (
                native_pet_index,
                rows,
                frame_columns,
                renderer_capability(),
                native_pet_track_name,
                native_pet_generation,
            )
            if native_pet_frames and native_pet_placed != pet_signature:
                pane_width = frame_columns if native_tmux_pane else max(28, min(frame_columns // 3, 48))
                pet_columns = max(4, min(8, pane_width // 6))
                # A switch replaces the track while the terminal loop is
                # repainting. Keep the optional graphics path defensive: a
                # malformed/empty Codex cache frame must never terminate LWA.
                if native_pet_track:
                    native_pet_index %= len(native_pet_track)
                    try:
                        placed = _place_native_images(
                            [native_pet_track[native_pet_index]],
                            row=max(3, rows - 10),
                            column=max(2, pane_width - pet_columns - 1),
                            columns=pane_width,
                            renderer=renderer_capability(),
                            image_id=LWA_PET_IMAGE_ID,
                            image_columns=pet_columns,
                            tmux_target=native_tmux_pane,
                            preload_frames=None,
                            clear_image_ids=(
                                list(range(LWA_PET_IMAGE_ID, LWA_PET_IMAGE_ID + 12))
                                if not native_pet_cleanup_done
                                else None
                            ),
                            top_anchor=True,
                        )
                    except (OSError, RuntimeError, TypeError, ValueError, IndexError) as exc:
                        lwa_lines.append(f"Pet graphics fallback: {redact_terminal_text(str(exc))}")
                        native_pet_frames.clear()
                        native_pet_placed = None
                        placed = 0
                    if placed:
                        native_pet_placed = pet_signature
                        native_pet_cleanup_done = True

            key = _read_key(screen)
            if key is None:
                await asyncio.sleep(0.02)
                continue
            raw_class, normalized = _diagnostic_key_class(key)
            if raw_class != "text":
                _focus_trace(
                    f"key raw_class={raw_class}"
                    + (f" normalized={normalized}" if normalized else "")
                )
            editor = editors[active_surface]
            if isinstance(key, int):
                if key == 17:  # Ctrl+Q: exit the combined LWA/Codex surface.
                    focus_broker.transition(PanelEvent.EXIT)
                    return 0
                if key in {9, getattr(curses, "KEY_BTAB", -999)}:
                    if _insert_native_tab(editor, key, native_split=bool(native_tmux_pane)):
                        codex_suggestions.clear()
                        lwa_suggestions.clear()
                        continue
                    focus_next(
                        "shift-tab" if key != 9 else "tab",
                        previous=key != 9,
                    )
                    codex_suggestions.clear()
                    lwa_suggestions.clear()
                    continue
                if key in {getattr(curses, "KEY_BACKSPACE", -1), getattr(curses, "KEY_DC", -1)}:
                    if key == getattr(curses, "KEY_DC", -1):
                        editor.delete()
                    else:
                        editor.backspace()
                    if active_surface == "codex":
                        codex_suggestions[:] = _codex_slash_suggestions(editor.text, editor.cursor)
                    else:
                        lwa_suggestions[:] = _lwa_slash_suggestions(editor.text)
                    continue
                if key in {10, getattr(curses, "KEY_ENTER", -1)}:
                    editor.newline()
                    if active_surface == "codex":
                        codex_suggestions.clear()
                    else:
                        lwa_suggestions.clear()
                    continue
                # Keep scroll local to the bounded Codex history. No scroll
                # event is ever forwarded to the child PTY.
                if key == getattr(curses, "KEY_MOUSE", -1):
                    try:
                        _, mouse_x, mouse_y, _, buttons = curses.getmouse()
                    except curses.error:
                        mouse_x, mouse_y, buttons = -1, -1, 0
                    left_width = columns if native_tmux_pane else max(28, min(columns // 3, 48))
                    lwa_prompt_heading = rows - 6
                    codex_prompt_heading = rows - 9
                    codex_start = 3
                    codex_height = max(1, codex_prompt_heading - 1 - codex_start)
                    end = max(0, len(codex_lines) - codex_scroll)
                    first = max(0, end - codex_height)
                    codex_index = first + (mouse_y - codex_start)
                    in_codex_pane = not native_tmux_pane and mouse_x > left_width
                    in_codex_feed = in_codex_pane and codex_start <= mouse_y < codex_start + codex_height and 0 <= codex_index < end
                    if native_tmux_pane:
                        lwa_point = lwa_selection_point(mouse_x, mouse_y, rows)
                        in_lwa_feed = lwa_point is not None
                        left_pressed = getattr(curses, "BUTTON1_PRESSED", 0)
                        left_moved = getattr(curses, "BUTTON1_MOVED", 0)
                        left_released = getattr(curses, "BUTTON1_RELEASED", 0)
                        if buttons & left_pressed:
                            _focus_trace(
                                f"mouse_event action=press button=left x={mouse_x} y={mouse_y}"
                            )
                        elif buttons & left_moved:
                            _focus_trace(
                                f"mouse_event action=motion button=left x={mouse_x} y={mouse_y}"
                            )
                        elif buttons & left_released:
                            _focus_trace(
                                f"mouse_event action=release button=release x={mouse_x} y={mouse_y}"
                            )
                        if buttons & (left_pressed | left_moved) and in_lwa_feed:
                            if lwa_selection_anchor is None:
                                lwa_selection_anchor = lwa_point
                                _focus_trace("selection surface=lwa phase=anchor length=0")
                            elif buttons & left_moved:
                                _focus_trace("selection surface=lwa phase=dragging length=unknown")
                            lwa_selection_focus = lwa_point
                            continue
                        if buttons & left_released and lwa_selection_anchor is not None:
                            if lwa_point is not None:
                                lwa_selection_focus = lwa_point
                            selected, start, stop = lwa_selected_text(lwa_selection_anchor, lwa_selection_focus)
                            _focus_trace(
                                f"selection surface=lwa phase=selected length={len(selected)}"
                            )
                            if clipboard_task is None or clipboard_task.done():
                                clipboard_task = asyncio.create_task(
                                    copy_selection(selected, start, stop, "LWA")
                                )
                            continue
                    if buttons & getattr(curses, "BUTTON1_PRESSED", 0) and in_codex_feed:
                        if selection_anchor is None:
                            selection_anchor = codex_index
                        selection_focus = codex_index
                        continue
                    if buttons & getattr(curses, "BUTTON1_RELEASED", 0) and selection_anchor is not None:
                        if in_codex_feed:
                            selection_focus = codex_index
                        start = min(selection_anchor, selection_focus)
                        stop = max(selection_anchor, selection_focus)
                        if clipboard_task is None or clipboard_task.done():
                            clipboard_task = asyncio.create_task(
                                copy_selection("\n".join(codex_lines[start : stop + 1]), start, stop)
                            )
                        selection_anchor = None
                        selection_focus = None
                        continue
                    if in_codex_pane and codex_prompt_heading < mouse_y < codex_prompt_heading + 3 and buttons & (
                        getattr(curses, "BUTTON1_PRESSED", 0)
                        | getattr(curses, "BUTTON1_CLICKED", 0)
                    ):
                        focus_to(Surface.CODEX, "mouse")
                    elif not in_codex_pane and lwa_prompt_heading < mouse_y < lwa_prompt_heading + 3 and buttons & (
                        getattr(curses, "BUTTON1_PRESSED", 0)
                        | getattr(curses, "BUTTON1_CLICKED", 0)
                    ):
                        focus_to(Surface.LWA, "mouse")
                    if buttons & (getattr(curses, "BUTTON4_PRESSED", 0) | getattr(curses, "BUTTON4_CLICKED", 0)):
                        if in_codex_pane:
                            codex_scroll = min(len(codex_lines), codex_scroll + 3)
                        elif native_tmux_pane:
                            lwa_scroll = min(len(_wrapped_lwa_lines(lwa_lines, max(1, columns - 4))), lwa_scroll + 3)
                    elif in_codex_pane and buttons & (
                        getattr(curses, "BUTTON5_PRESSED", 0) | getattr(curses, "BUTTON5_CLICKED", 0)
                    ):
                        codex_scroll = max(0, codex_scroll - 3)
                    elif native_tmux_pane and buttons & (
                        getattr(curses, "BUTTON5_PRESSED", 0) | getattr(curses, "BUTTON5_CLICKED", 0)
                    ):
                        lwa_scroll = max(0, lwa_scroll - 3)
                    continue
                if key == getattr(curses, "KEY_PPAGE", -1):
                    if active_surface == "codex":
                        codex_scroll = min(len(codex_lines), codex_scroll + 10)
                    elif native_tmux_pane:
                        lwa_scroll = min(len(_wrapped_lwa_lines(lwa_lines, max(1, columns - 4))), lwa_scroll + 10)
                    continue
                if key == getattr(curses, "KEY_NPAGE", -1):
                    if active_surface == "codex":
                        codex_scroll = max(0, codex_scroll - 10)
                    elif native_tmux_pane:
                        lwa_scroll = max(0, lwa_scroll - 10)
                    continue
                if key == getattr(curses, "KEY_UP", -1):
                    editor.up()
                    continue
                if key == getattr(curses, "KEY_DOWN", -1):
                    editor.down()
                    continue
                if key == getattr(curses, "KEY_LEFT", -1):
                    editor.left()
                    continue
                if key == getattr(curses, "KEY_RIGHT", -1):
                    editor.right()
                    continue
                if key == getattr(curses, "KEY_HOME", -1):
                    editor.home()
                    continue
                if key == getattr(curses, "KEY_END", -1):
                    editor.end()
                    continue
                # Ignore all other curses key codes rather than treating an
                # implementation-specific integer as prompt input.
                continue
            if isinstance(key, tuple) and key[0] == "__LWA_PASTE__":
                pasted = key[1].replace("\r\n", "\n").replace("\r", "\n")
                editors[active_surface].insert(pasted)
                if active_surface == "codex":
                    codex_suggestions[:] = _codex_slash_suggestions(
                        editors[active_surface].text, editors[active_surface].cursor
                    )
                lwa_lines.append(
                    f"Clipboard pasted into {active_surface.upper()} Prompt ({len(pasted)} characters)."
                )
                continue
            if isinstance(key, tuple) and key[0] == "__LWA_MOUSE__":
                _, mouse_button, mouse_x, mouse_y, mouse_action = key
                if native_tmux_pane:
                    if mouse_button & 64:
                        if mouse_button & 1:
                            lwa_scroll = max(0, lwa_scroll - 3)
                        else:
                            lwa_scroll = min(len(_wrapped_lwa_lines(lwa_lines, max(1, columns - 4))), lwa_scroll + 3)
                    elif mouse_y < rows - 6:
                        lwa_point = lwa_selection_point(mouse_x, mouse_y, rows)
                        if lwa_point is not None:
                            drag_action = _sgr_left_drag(mouse_button, mouse_action)
                            if drag_action in {"press", "motion", "release"}:
                                _focus_trace(
                                    f"mouse_event action={drag_action} "
                                    f"button={_diagnostic_mouse_button(mouse_button)} "
                                    f"x={mouse_x} y={mouse_y}"
                                )
                            if drag_action == "press":
                                lwa_selection_anchor = lwa_point
                                lwa_selection_focus = lwa_point
                                _focus_trace("selection surface=lwa phase=anchor length=0")
                            elif drag_action == "motion" and lwa_selection_anchor is not None:
                                lwa_selection_focus = lwa_point
                                _focus_trace("selection surface=lwa phase=dragging length=unknown")
                            elif drag_action == "release" and lwa_selection_anchor is not None:
                                lwa_selection_focus = lwa_point
                                selected, start, stop = lwa_selected_text(lwa_selection_anchor, lwa_selection_focus)
                                _focus_trace(
                                    f"selection surface=lwa phase=selected length={len(selected)}"
                                )
                                if clipboard_task is None or clipboard_task.done():
                                    clipboard_task = asyncio.create_task(
                                        copy_selection(selected, start, stop, "LWA")
                                    )
                    elif mouse_y >= rows - 6:
                        focus_to(Surface.LWA, "mouse")
                    continue
                continue
            if key == "__LWA_TRANSFER_RESPONSE__":
                if selection_anchor is not None and selection_focus is not None:
                    start = min(selection_anchor, selection_focus)
                    stop = max(selection_anchor, selection_focus)
                    transferred = "\n".join(codex_lines[start : stop + 1]).strip()
                else:
                    transferred = _latest_codex_response(codex_lines)
                if transferred:
                    editors["lwa"].insert(transferred)
                    focus_to(Surface.LWA, "response-transfer")
                    lwa_lines.append(
                        f"Codex response transferred to LWA Prompt ({len(transferred)} characters)."
                    )
                else:
                    lwa_lines.append("No Codex response is available to transfer.")
                continue
            if key == "__LWA_GRAPHICS_RESPONSE__":
                continue
            if key == "\x1b":
                if lwa_suggestions:
                    lwa_suggestions.clear()
                    continue
                return 0
            if key in {"\t", "__LWA_SHIFT_TAB__"}:
                if _insert_native_tab(
                    editor,
                    key,
                    native_split=bool(native_tmux_pane),
                ):
                    codex_suggestions.clear()
                    lwa_suggestions.clear()
                    continue
                focus_next(
                    "shift-tab" if key == "__LWA_SHIFT_TAB__" else "tab",
                    previous=key == "__LWA_SHIFT_TAB__",
                )
                codex_suggestions.clear()
                lwa_suggestions.clear()
                continue
            editor = editors[active_surface]
            if key in {"__LWA_SHIFT_UP__", "__LWA_SHIFT_DOWN__"}:
                if active_surface == "codex" and session_active:
                    shortcut = "\x1b[1;2A" if key == "__LWA_SHIFT_UP__" else "\x1b[1;2B"
                    try:
                        await session.write(shortcut)
                        direction = "up" if key == "__LWA_SHIFT_UP__" else "down"
                        lwa_lines.append(f"Codex model variant shortcut sent: Shift+{direction.title()}.")
                    except RuntimeError as exc:
                        session_active = False
                        lwa_lines.append(str(exc))
                continue
            if key in {"__LWA_SHIFT_LEFT__", "__LWA_SHIFT_RIGHT__"}:
                if key == "__LWA_SHIFT_LEFT__":
                    editor.move_left(select=True)
                else:
                    editor.move_right(select=True)
                continue
            if key == "\x03":
                if editors[active_surface].selected_text():
                    copied = editors[active_surface].selected_text()
                    label = f"{active_surface.upper()} prompt selection"
                elif selection_anchor is not None and selection_focus is not None:
                    start = min(selection_anchor, selection_focus)
                    stop = max(selection_anchor, selection_focus)
                    copied = "\n".join(codex_lines[start : stop + 1]).strip()
                    label = "Codex selection"
                elif lwa_selection_anchor is not None and lwa_selection_focus is not None:
                    copied, _, _ = lwa_selected_text(lwa_selection_anchor, lwa_selection_focus)
                    label = "LWA selection"
                else:
                    copied = editors[active_surface].text
                    label = f"{active_surface.upper()} prompt"
                if copied:
                    if clipboard_task is None or clipboard_task.done():
                        clipboard_task = asyncio.create_task(copy_prompt_text(copied, label))
                else:
                    lwa_lines.append("Nothing to copy.")
                continue
            if key == "\x11":  # Ctrl+Q
                focus_broker.transition(PanelEvent.EXIT)
                return 0
            if key == "__LWA_ALT_ENTER__":
                codex_editor = editors["codex"]
                text = codex_editor.text
                codex_editor.clear()
                codex_suggestions.clear()
                if text and session_active:
                    trigger_pet_action()
                    try:
                        native_pet_response_pending = True
                        lwa_lines.append(f"Submitting {len(text)} characters to Codex PTY...")
                        await session.write(_codex_submission(text))
                        lwa_lines.append("Codex Prompt sent to the PTY via Alt+Enter.")
                    except RuntimeError as exc:
                        session_active = False
                        lwa_lines.append(str(exc))
                continue
            if key == "\n":
                editor.newline()
                continue
            if key in ("\r", getattr(curses, "KEY_ENTER", -1)):
                text = editor.text
                editor.clear()
                if active_surface == "codex":
                    codex_suggestions[:] = _codex_slash_suggestions(text, len(text))
                else:
                    lwa_suggestions[:] = _lwa_slash_suggestions(text)
                if not text:
                    continue
                if active_surface == "lwa":
                    trigger_pet_action()
                    if text.strip() in {"/lwa", "/lwa "}:
                        lwa_suggestions[:] = _lwa_slash_suggestions(text)
                        continue
                    if text.strip().lower() == "debug":
                        editor.clear()
                        pipeline_busy = True
                        pipeline_task = asyncio.create_task(run_debug_snapshot(rows, columns))
                        continue
                    if text.strip().lower().startswith("/pets"):
                        editor.clear()
                        parts = text.strip().split(maxsplit=1)
                        selection = parts[1].strip().lower() if len(parts) == 2 else "next"
                        available = discover_codex_pet_names()
                        if available:
                            lwa_lines.append(
                                f"Codex pets ({len(available)}): {', '.join(available)} · active: {native_pet_name or 'none'}"
                            )
                        requested = resolve_pet_selection(selection, native_pet_name, available)
                        if selection in {"list", "reload", "refresh"}:
                            lwa_lines.append("Pet catalog refreshed; use /pets <name>, /pets <number>, or /pets next.")
                        elif requested:
                            refresh_independent_pet(requested)
                        elif not available:
                            lwa_lines.append("No Codex pet assets are currently available.")
                        else:
                            lwa_lines.append(f"Unknown pet selection: {selection}. Use a name, number, or next.")
                        codex_suggestions.clear()
                        lwa_suggestions.clear()
                        _focus_native_lwa_pane()
                        continue
                    finalized = finalize_prompt(text, mode="semantic")
                    if pipeline_busy:
                        lwa_lines.append("LWA pipeline is still working; wait for completion.")
                    elif session_active:
                        editor.clear()
                        pipeline_busy = True
                        lwa_lines.append(
                            f"LWA prompt locked {finalized.status} · {finalized.input_chars} → {finalized.output_chars} chars."
                        )
                        pipeline_task = asyncio.create_task(run_lwa_pipeline(finalized.text))
                else:
                    trigger_pet_action()
                    if text.strip().lower().startswith("/pets"):
                        parts = text.strip().split(maxsplit=1)
                        selection = parts[1].strip().lower() if len(parts) == 2 else "next"
                        available = discover_codex_pet_names()
                        if available:
                            lwa_lines.append(
                                f"Codex pets ({len(available)}): {', '.join(available)} · active: {native_pet_name or 'none'}"
                            )
                        requested = resolve_pet_selection(selection, native_pet_name, available)
                        if selection in {"list", "reload", "refresh"}:
                            lwa_lines.append("Pet catalog refreshed; use /pets <name>, /pets <number>, or /pets next.")
                        elif requested:
                            refresh_independent_pet(requested)
                        elif not available:
                            lwa_lines.append("No Codex pet assets are currently available.")
                        else:
                            lwa_lines.append(f"Unknown pet selection: {selection}. Use a name, number, or next.")
                        codex_suggestions.clear()
                        lwa_suggestions.clear()
                        continue
                    if session_active:
                        try:
                            native_pet_response_pending = True
                            await session.write(_codex_submission(text))
                        except RuntimeError as exc:
                            session_active = False
                            lwa_lines.append(str(exc))
                    lwa_lines.append("Direct Codex Prompt sent to the PTY.")
                continue
            if key in (curses.KEY_BACKSPACE, getattr(curses, "KEY_DC", -1), "\b", "\x7f"):
                if key in (getattr(curses, "KEY_DC", -1),):
                    editor.delete()
                else:
                    editor.backspace()
            elif key in (getattr(curses, "KEY_LEFT", -1),):
                editor.left()
            elif key in (getattr(curses, "KEY_RIGHT", -1),):
                editor.right()
            elif key in (getattr(curses, "KEY_HOME", -1),):
                editor.home()
            elif key in (getattr(curses, "KEY_END", -1),):
                editor.end()
            elif key in (getattr(curses, "KEY_UP", -1),):
                editor.up()
            elif key in (getattr(curses, "KEY_DOWN", -1),):
                editor.down()
            elif isinstance(key, str) and key.isprintable():
                editor.insert(key)
            if active_surface == "codex":
                codex_suggestions[:] = _codex_slash_suggestions(editor.text, editor.cursor)
    finally:
        _set_bracketed_paste(False)
        if "kitty" in renderer_capability().lower() or "ghostty" in renderer_capability().lower():
            try:
                sys.stdout.write("\x1b[0 q")
                sys.stdout.flush()
            except (OSError, UnicodeError):
                pass
        if clipboard_task is not None and not clipboard_task.done():
            clipboard_task.cancel()
            with suppress(asyncio.CancelledError):
                await clipboard_task
        if pipeline_task is not None and not pipeline_task.done():
            pipeline_task.cancel()
            with suppress(asyncio.CancelledError):
                await pipeline_task
        await lifecycle.close_once()


def run(
    executable: str | None = None,
    *,
    bridge_socket: str | None = None,
    native_tmux_pane: str | None = None,
) -> int:
    with suppress(Exception):
        from .debug_log import write_startup_event

        write_startup_event("lwa-native-terminal", "launch_attempt")
    codex = executable or shutil.which("codex")
    if not codex:
        print("Lwa: Codex was not found on PATH.")
        return 127

    try:
        return curses.wrapper(
            lambda screen: asyncio.run(_interactive(screen, codex, bridge_socket, native_tmux_pane))
        )
    except (KeyboardInterrupt, asyncio.CancelledError):
        # Alt/control sequences and terminal shutdown must not print a Python
        # traceback after curses has started managing the screen.
        return 130
    except (curses.error, OSError) as exc:
        if isinstance(exc, OSError):
            print(f"Lwa: could not start Codex: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        try:
            from .debug_log import write_startup_error

            path = write_startup_error("lwa-native-terminal", exc)
            print(f"Lwa: startup failed: {redact_terminal_text(str(exc))}", file=sys.stderr)
            print(f"Lwa startup log: {path}", file=sys.stderr)
        except Exception:  # noqa: BLE001
            print(f"Lwa: startup failed: {redact_terminal_text(str(exc))}", file=sys.stderr)
        return 1
