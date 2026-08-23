from __future__ import annotations

import pytest


def test_native_frame_draws_wireframe_regions_and_borders():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.rows = []

        def getmaxyx(self):
            return (24, 80)

        def addnstr(self, row, column, text, *_args):
            self.rows.append((row, text))

    screen = Screen()
    prompt_row, columns = terminal_frame._draw_frame(
        screen,
        codex_lines=["Codex output"],
        lwa_lines=["Codex session connected."],
        prompt="hello",
        active_surface="lwa",
        renderer="test renderer",
    )
    rendered = "\n".join(text for _, text in screen.rows)
    assert prompt_row == 20
    assert columns == 80
    assert "+" in rendered and "LWA FRAME - test renderer" in rendered
    assert "CODEX FEED" in rendered
    assert "CODEX PROMPT" in rendered
    assert "LWA FEED" in rendered
    assert "LWA PROMPT" in rendered
    assert "draft only" in rendered
    assert "Codex output" in rendered

    screen.rows.clear()
    terminal_frame._draw_frame(
        screen,
        codex_lines=[],
        lwa_lines=[],
        prompt="",
        active_surface="lwa",
        renderer="test renderer",
        codex_prompt="direct codex text",
        lwa_prompt="unfinalized lwa text",
    )
    separated = "\n".join(text for _, text in screen.rows)
    assert "direct codex text" in separated
    assert "unfinalized lwa text" in separated


def test_native_frame_has_narrow_terminal_fallback():
    from lwa_mcp import terminal_frame

    class Screen:
        def getmaxyx(self):
            return (10, 20)

        def addnstr(self, *_args):
            self.text = _args[2]

    screen = Screen()
    prompt_row, columns = terminal_frame._draw_frame(
        screen, codex_lines=[], lwa_lines=[], prompt="", active_surface="lwa", renderer="test"
    )
    assert prompt_row == 9
    assert columns == 20
    assert "too small" in screen.text


def test_native_frame_consumes_mouse_escape_sequence_without_exit():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(["\x1b", "[", "<", "6", "4", ";", "1", "0", ";", "2", "0", "M"])

        def get_wch(self):
            return next(self.keys)

    assert terminal_frame._read_key(Screen()) == ("__LWA_MOUSE__", 64, 9, 19, "M")


def test_native_frame_returns_tab_from_escape_sequence_reader():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(["\x1b", "\t"])

        def get_wch(self):
            return next(self.keys)

    assert terminal_frame._read_key(Screen()) == "\t"


def test_diagnostic_key_class_never_classifies_text_as_payload():
    from lwa_mcp import terminal_frame

    assert terminal_frame._diagnostic_key_class("secret prompt") == ("string", None)
    assert terminal_frame._diagnostic_key_class("x") == ("text", None)
    assert terminal_frame._diagnostic_key_class("__LWA_SHIFT_LEFT__") == (
        "control_sequence",
        "shift-left",
    )
    assert terminal_frame._diagnostic_key_class(9) == ("curses_code", "tab")


def test_diagnostic_mouse_button_collapses_terminal_specific_codes():
    from lwa_mcp import terminal_frame

    assert terminal_frame._diagnostic_mouse_button(64) == "wheel"
    assert terminal_frame._diagnostic_mouse_button(32) == "motion"
    assert terminal_frame._diagnostic_mouse_button(0) == "left"
    assert terminal_frame._diagnostic_mouse_button(3) == "release"


def test_native_mouse_mask_requests_drag_positions_when_supported():
    from lwa_mcp import terminal_frame

    expected = terminal_frame.curses.ALL_MOUSE_EVENTS | getattr(
        terminal_frame.curses, "REPORT_MOUSE_POSITION", 0
    )
    assert terminal_frame._native_mouse_mask() == expected


def test_native_tab_and_backtab_insert_five_spaces_without_focus_switch():
    from lwa_mcp import terminal_frame
    from lwa_mcp.prompt_editor import PromptEditor

    editor = PromptEditor()
    assert terminal_frame._insert_native_tab(editor, 9, native_split=True) is True
    assert editor.text == "     "
    assert terminal_frame._insert_native_tab(editor, "\t", native_split=True) is True
    assert terminal_frame._insert_native_tab(editor, getattr(terminal_frame.curses, "KEY_BTAB", -999), native_split=True) is True
    assert editor.text == "               "
    assert terminal_frame._insert_native_tab(editor, 9, native_split=False) is False


def test_cursor_position_is_pane_local_and_bounded():
    from lwa_mcp import terminal_frame

    assert terminal_frame._cursor_position(
        active_surface="lwa",
        cursor_column=999,
        prompt_row=999,
        rows=24,
        columns=80,
        left_width=30,
        native_split=True,
    ) == (23, 28)
    assert terminal_frame._cursor_position(
        active_surface="codex",
        cursor_column=10,
        prompt_row=10,
        rows=24,
        columns=80,
        left_width=30,
        native_split=True,
    ) is None


def test_sgr_left_drag_classifies_press_motion_and_release():
    from lwa_mcp import terminal_frame

    assert terminal_frame._sgr_left_drag(0, "M") == "press"
    assert terminal_frame._sgr_left_drag(32, "M") == "motion"
    assert terminal_frame._sgr_left_drag(0, "m") == "release"
    assert terminal_frame._sgr_left_drag(64, "M") is None


@pytest.mark.parametrize(
    ("sequence", "expected"),
    [
        (["\x1b", "[", "A"], "KEY_UP"),
        (["\x1b", "[", "B"], "KEY_DOWN"),
        (["\x1b", "[", "3", "~"], "KEY_DC"),
    ],
)
def test_native_frame_decodes_raw_navigation_and_delete_sequences(sequence, expected):
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(sequence)

        def get_wch(self):
            return next(self.keys)

    value = terminal_frame._read_key(Screen())
    assert value == getattr(__import__("curses"), expected)


def test_native_frame_decodes_shift_enter_as_newline():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(["\x1b", "[", "1", "3", ";", "2", "u"])

        def get_wch(self):
            return next(self.keys)

    assert terminal_frame._read_key(Screen()) == "\n"


def test_native_frame_decodes_whole_shift_enter_sequence():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(["\x1b", "[13;2u"])

        def get_wch(self):
            return next(self.keys)

    assert terminal_frame._read_key(Screen()) == "\n"


def test_native_frame_decodes_alt_enter_sequence():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(["\x1b", "[13;3u"])

        def get_wch(self):
            return next(self.keys)

    assert terminal_frame._read_key(Screen()) == "__LWA_ALT_ENTER__"


def test_native_frame_decodes_esc_return_as_alt_enter():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(["\x1b", "\r"])

        def get_wch(self):
            return next(self.keys)

    assert terminal_frame._read_key(Screen()) == "__LWA_ALT_ENTER__"


def test_native_frame_decodes_bracketed_paste():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(["\x1b", "[200~", "pasted ", "text", "\x1b", "[201~"])

        def get_wch(self):
            return next(self.keys)

    assert terminal_frame._read_key(Screen()) == ("__LWA_PASTE__", "pasted text")


def test_native_frame_decodes_characterwise_bracketed_paste():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(
                ["\x1b", "[", "2", "0", "0", "~", "p", "a", "s", "t", "e", "d", "\x1b", "[", "2", "0", "1", "~"]
            )

        def get_wch(self):
            return next(self.keys)

    assert terminal_frame._read_key(Screen()) == ("__LWA_PASTE__", "pasted")


def test_native_frame_decodes_chunked_bracketed_paste():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(["\x1b[201~"])

        def get_wch(self):
            return next(self.keys)

    class ChunkScreen(Screen):
        def __init__(self):
            self.keys = iter(["\x1b[200~make pacman clone", "\x1b[201~"])

    assert terminal_frame._read_key(ChunkScreen()) == (
        "__LWA_PASTE__",
        "make pacman clone",
    )


def test_bracketed_paste_preserves_crlf_payload(monkeypatch):
    from lwa_mcp import terminal_frame

    class Output:
        def __init__(self):
            self.value = ""

        def isatty(self):
            return True

        def write(self, value):
            self.value += value

        def flush(self):
            return None

    output = Output()
    monkeypatch.setattr(terminal_frame.sys, "stdout", output)
    terminal_frame._set_bracketed_paste(True)
    assert output.value == "\x1b[?2004h"


def test_prompt_view_places_cursor_on_text_row():
    from lwa_mcp import terminal_frame

    class Screen:
        def getmaxyx(self):
            return (24, 80)

        def addnstr(self, *_args):
            return None

    screen = Screen()
    prompt_row, _ = terminal_frame._draw_frame(
        screen,
        codex_lines=[],
        lwa_lines=[],
        prompt="",
        cursor=0,
        active_surface="lwa",
        renderer="test",
        lwa_prompt="hello",
        lwa_cursor=5,
    )
    assert prompt_row == 20


def test_prompt_view_scrolls_multiline_text_with_cursor():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.rows = []

        def getmaxyx(self):
            return (24, 80)

        def addnstr(self, row, _column, text, *_args):
            self.rows.append((row, text))

    screen = Screen()
    terminal_frame._draw_frame(
        screen,
        codex_lines=[],
        lwa_lines=[],
        prompt="",
        cursor=0,
        active_surface="lwa",
        renderer="test",
        lwa_prompt="one\ntwo\nthree\nfour",
        lwa_cursor=len("one\ntwo\nthree\nfour"),
    )
    rendered = "\n".join(text for _, text in screen.rows)
    assert "three" in rendered and "four" in rendered

    screen.rows.clear()
    terminal_frame._draw_frame(
        screen,
        codex_lines=[],
        lwa_lines=[],
        prompt="",
        cursor=0,
        active_surface="lwa",
        renderer="test",
        lwa_prompt="one\ntwo\nthree\nfour",
        lwa_cursor=0,
    )
    rendered = "\n".join(text for _, text in screen.rows)
    assert "one" in rendered and "two" in rendered


def test_codex_submission_uses_terminal_return():
    from lwa_mcp.terminal_frame import _codex_submission

    assert _codex_submission("review me") == "\x1b[200~review me\x1b[201~\r"
    assert _codex_submission("line one\nline two\n") == "\x1b[200~line one\nline two\x1b[201~\r"


def test_codex_submission_preserves_slash_commands_verbatim():
    from lwa_mcp.terminal_frame import _codex_submission

    assert _codex_submission("/help") == "\x1b[200~/help\x1b[201~\r"
    assert _codex_submission("/model gpt-5.6-luna") == (
        "\x1b[200~/model gpt-5.6-luna\x1b[201~\r"
    )


def test_codex_slash_command_completion():
    from lwa_mcp.terminal_frame import _complete_codex_slash_command

    text, cursor, matches = _complete_codex_slash_command("/hel", 4)
    assert (text, cursor, matches) == ("/help", 5, ["/help"])

    text, cursor, matches = _complete_codex_slash_command("/help ", 6)
    assert text == "/help " and cursor == 6 and matches == []
    text, cursor, matches = _complete_codex_slash_command("/pet", 4)
    assert (text, cursor, matches) == ("/pets", 5, ["/pets"])


def test_codex_slash_suggestions_are_prompt_local():
    from lwa_mcp import terminal_frame

    assert terminal_frame._codex_slash_suggestions("/per", 4) == ["› /permissions"]
    suggestions = terminal_frame._codex_slash_suggestions("/pets", 5)
    assert suggestions[0].startswith("› /pets")
    assert "follow-up" in suggestions[1]


def test_codex_permission_modal_is_extracted_from_feed():
    from lwa_mcp import terminal_frame

    lines = [
        "ordinary Codex output",
        "Update Model Permissions",
        "1. Ask for approval (current)",
        "2. Approve for me",
        "Press enter to confirm or esc to go back",
    ]
    modal = terminal_frame._codex_modal_lines(lines)
    assert modal[0] == "Update Model Permissions"
    assert modal[-1].startswith("Press enter")


def test_exact_slash_commands_expose_followup_hints():
    from lwa_mcp.terminal_frame import CODEX_SLASH_FOLLOWUPS

    assert "pet" in CODEX_SLASH_FOLLOWUPS["/pets"]
    assert "permission" in CODEX_SLASH_FOLLOWUPS["/permissions"]


def test_latest_codex_response_returns_last_nonempty_block():
    from lwa_mcp.terminal_frame import _latest_codex_response

    assert _latest_codex_response(["old", "", "new one", "new two", ""]) == "new one\nnew two"


def test_native_frame_decodes_alt_shift_enter_transfer():
    from lwa_mcp import terminal_frame

    class Screen:
        def __init__(self):
            self.keys = iter(["\x1b", "[13;4u"])

        def get_wch(self):
            return next(self.keys)

    assert terminal_frame._read_key(Screen()) == "__LWA_TRANSFER_RESPONSE__"


@pytest.mark.asyncio
async def test_native_frame_uses_one_interactive_session_for_both_prompt_surfaces(monkeypatch):
    from lwa_mcp import terminal_frame

    class FakeScreen:
        def __init__(self):
            self.keys = iter(["a", "\t", "\x7f", "b", "\r", "\x03", "\x11"])

        def getmaxyx(self):
            return (24, 80)

        def keypad(self, enabled):
            return None

        def nodelay(self, enabled):
            return None

        def erase(self):
            return None

        def addnstr(self, *args):
            return None

        def move(self, *args):
            return None

        def refresh(self):
            return None

        def get_wch(self):
            return next(self.keys)

    class FakeSession:
        def __init__(self, sink, executable):
            self.sink = sink
            self.executable = executable
            self.process = None
            self.writes = []
            self.resizes = []
            self.closed = False

        async def start(self):
            self.process = object()
            await self.sink({"type": "status", "state": "running", "message": "ready"})

        async def write(self, text):
            self.writes.append(text)

        async def resize(self, columns, rows):
            self.resizes.append((columns, rows))

        async def close(self):
            self.closed = True

    created = []

    def make_session(sink, executable):
        session = FakeSession(sink, executable)
        created.append(session)
        return session

    monkeypatch.setattr(terminal_frame, "CodexSession", make_session)
    session_screen = FakeScreen()
    result = await terminal_frame._interactive(session_screen, "codex-test")

    session = created[0]
    assert result == 0
    assert session.writes == ["\x1b[200~b\x1b[201~\r"]
    assert session.resizes == [(80, 24)]
    assert session.closed is True
