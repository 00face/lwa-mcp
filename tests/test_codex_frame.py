from __future__ import annotations

import json
from html.parser import HTMLParser
from importlib.resources import files

import pytest


def test_codex_workspace_and_socket_are_additive():
    from lwa_mcp import dashboard

    paths = {getattr(route, "path", None) for route in dashboard.app.routes}
    assert "/" in paths
    assert "/codex" in paths
    assert "/ws/codex" in paths
    assert "/api/codex/capabilities" in paths


def test_codex_workspace_contains_required_low_resource_surfaces():
    static = files("lwa_mcp").joinpath("static")
    html = static.joinpath("codex.html").read_text(encoding="utf-8")
    css = static.joinpath("codex.css").read_text(encoding="utf-8")
    js = static.joinpath("codex.js").read_text(encoding="utf-8")
    for marker in ("Codex Feed", "Codex Prompt", "LWA Feed", "LWA Prompt", "shaderCanvas", "lowResource", "pauseFeed", "terminalText", "terminalTabs", "newTab"):
        assert marker in html
    assert "WebSocket" in js
    assert "webgl" in js
    assert "text fallback" in js
    assert "focus-visible" in css
    assert "lastAnnouncement" in js
    assert "transcript.textContent" in js
    assert "aria-selected" in js
    assert "newTab" in js
    assert "3000" in js  # bounded terminal history
    assert "low-resource" in css


def test_codex_workspace_has_accessible_control_associations():
    class AccessibilityParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.controls = []
            self.labels = set()
            self.elements = {}

        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            element_id = attributes.get("id")
            if element_id:
                self.elements[element_id] = (tag, attributes)
            if tag == "label" and attributes.get("for"):
                self.labels.add(attributes["for"])
            if tag in {"input", "textarea", "select"} and element_id:
                self.controls.append((element_id, attributes))

    html = files("lwa_mcp").joinpath("static", "codex.html").read_text(encoding="utf-8")
    parser = AccessibilityParser()
    parser.feed(html)

    assert {control_id for control_id, _ in parser.controls} <= parser.labels
    assert parser.elements["terminalCanvas"][1]["tabindex"] == "0"
    assert parser.elements["terminalCanvas"][1]["aria-live"] == "off"
    assert parser.elements["terminalText"][1]["role"] == "log"
    assert parser.elements["terminalText"][1]["aria-live"] == "off"
    assert parser.elements["prompt"][1]["aria-describedby"] == "lwaPromptHint"


def test_prompt_finalizer_has_explicit_modes_and_redacted_metadata():
    from lwa_mcp.prompt_finalizer import finalize_prompt

    finalized = finalize_prompt("keep\n\n\nthis", mode="compact")
    assert finalized.text == "keep\n\nthis"
    assert finalized.status == "deterministic_compact"
    assert "keep" not in repr(finalized.public_json())
    assert finalize_prompt("literal", mode="raw").status == "raw_bypass"
    assert finalize_prompt("literal", mode="semantic").status == "semantic_unavailable_bypass"


def test_terminal_output_masks_credential_shaped_values():
    from lwa_mcp.terminal_protocol import redact_terminal_text

    output = redact_terminal_text(
        "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234 "
        "Authorization: Bearer abc.def.ghi token=visible"
    )
    assert "sk-abcdefghijklmnopqrstuvwxyz1234" not in output
    assert "abc.def.ghi" not in output
    assert "token=[REDACTED]" in output


def test_terminal_output_masks_opaque_payloads_without_hiding_short_text():
    from lwa_mcp.terminal_protocol import redact_terminal_text

    payload = "A" * 512
    output = redact_terminal_text(f"prefix {payload} suffix short text")
    assert payload not in output
    assert "[OPAQUE PAYLOAD REDACTED]" in output
    assert "short text" in output


def test_terminal_stream_filter_handles_graphics_split_across_reads():
    from lwa_mcp.terminal_protocol import TerminalStreamFilter

    stream = TerminalStreamFilter()
    assert stream.feed("before\x1b_Gf=100;QUJD") == "before"
    assert stream.feed("REVGRw==\x1b\\after") == "after"


def test_terminal_text_buffer_keeps_carriage_return_redraws_on_one_line():
    from lwa_mcp.terminal_protocol import TerminalTextBuffer

    buffer = TerminalTextBuffer()
    buffer.feed("Working")
    buffer.feed("\rWorking")
    assert buffer.lines == ["Working"]
    buffer.feed("\nnext")
    assert buffer.lines == ["Working", "next"]


def test_native_frame_reports_renderer_without_faking_graphical_support(monkeypatch):
    from lwa_mcp import terminal_frame

    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    monkeypatch.delenv("GHOSTTY_RESOURCES_DIR", raising=False)
    assert terminal_frame.renderer_capability() == "curses fallback frame"
    monkeypatch.setenv("TERM_PROGRAM", "Ghostty")
    assert terminal_frame.renderer_capability() == "ghostty-host / Lwa fallback frame"


def test_tab_toggles_between_prompt_surfaces():
    from lwa_mcp.terminal_frame import _toggle_prompt_surface

    assert _toggle_prompt_surface("lwa") == "codex"
    assert _toggle_prompt_surface("codex") == "lwa"


def test_pet_tracks_idle_by_default_and_actions_are_triggerable():
    from lwa_mcp.image_compositor import ImageFrame
    from lwa_mcp.pet_renderer import (
        PetFrame,
        PetSemanticState,
        build_pet_playback_state,
        pet_track_for_state,
    )

    frames = [ImageFrame("image/png", str(index), 1) for index in range(72)]
    pet = PetFrame("dewey", "Dewey", "[dewey]", frames[0], "ghostty", animation=tuple(frames))
    playback = build_pet_playback_state(pet, generation=4)
    assert len(playback.idle) == 6
    assert len(playback.welcome) == 4
    assert [len(track) for track in playback.actions] == [16, 16]
    assert len(playback.completion) == 16
    assert playback.idle[0] is frames[0]
    assert playback.actions[0][0] is frames[8]
    assert playback.actions[1][0] is frames[32]
    assert playback.completion[0] is frames[56]
    assert playback.generation == 4
    assert pet_track_for_state(playback, PetSemanticState.RUNNING)[0] is frames[8]
    assert pet_track_for_state(playback, PetSemanticState.NEEDS_INPUT)[0] is frames[24]
    assert pet_track_for_state(playback, PetSemanticState.READY)[0] is frames[56]
    assert pet_track_for_state(playback, PetSemanticState.BLOCKED)[0] is frames[0]


def test_native_image_placement_is_gated_by_host_renderer(monkeypatch):
    from lwa_mcp import terminal_frame
    from lwa_mcp.image_compositor import ImageFrame

    frame = ImageFrame("image/png", "cG5n", 3)
    writes = []

    class Output:
        def write(self, value):
            writes.append(value)

        def flush(self):
            return None

    monkeypatch.setattr(terminal_frame.sys, "stdout", Output())
    assert terminal_frame._place_native_images([frame], row=3, columns=80, renderer="curses fallback frame") == 0
    assert writes == []
    assert terminal_frame._place_native_images([frame], row=3, columns=80, renderer="kitty-host") == 1
    assert any("a=T" in value for value in writes)


def test_native_image_placement_wraps_kitty_graphics_for_tmux(monkeypatch):
    from lwa_mcp import terminal_frame
    from lwa_mcp.image_compositor import ImageFrame

    frame = ImageFrame("image/png", "cG5n", 3)
    writes = []

    class Output:
        def write(self, value):
            writes.append(value)

        def flush(self):
            return None

    monkeypatch.setenv("TMUX", "/tmp/tmux,1,0")
    monkeypatch.setattr(terminal_frame.sys, "stdout", Output())
    assert terminal_frame._place_native_images([frame], row=3, columns=80, renderer="ghostty-host") == 1
    assert any(value.startswith("\x1bPtmux;\x1b") for value in writes)


def test_native_pet_cleanup_is_one_time_and_separate_from_frame_replacement(monkeypatch):
    from lwa_mcp import terminal_frame
    from lwa_mcp.image_compositor import ImageFrame

    frame = ImageFrame("image/png", "cG5n", 3)
    writes = []

    class Output:
        def write(self, value):
            writes.append(value)

        def flush(self):
            return None

    monkeypatch.setattr(terminal_frame.sys, "stdout", Output())
    assert terminal_frame._place_native_images(
        [frame],
        row=3,
        columns=80,
        renderer="ghostty-host",
        image_id=9001,
        clear_image_ids=[9001, 9002],
    ) == 1
    assert any("a=d,d=I,q=2,i=9001" in value for value in writes)
    assert any("a=d,d=I,q=2,i=9002" in value for value in writes)
    first_frame = next(index for index, value in enumerate(writes) if "a=T" in value)
    assert first_frame > 1

    writes.clear()
    assert terminal_frame._place_native_images(
        [frame],
        row=3,
        columns=80,
        renderer="ghostty-host",
        image_id=9001,
    ) == 1
    assert not any("a=d,d=I" in value for value in writes)
    assert sum("a=T" in value for value in writes) == 1


def test_codex_session_validates_launch_working_directory(tmp_path):
    from lwa_mcp.codex_session import CodexSession

    async def sink(_event):
        return None

    session = CodexSession(sink, executable="/bin/echo", cwd=str(tmp_path))
    assert session.cwd == str(tmp_path.resolve())
    with pytest.raises(ValueError):
        CodexSession(sink, executable="/bin/echo", cwd=str(tmp_path / "missing"))


def test_codex_child_environment_preserves_graphics_host(monkeypatch):
    from lwa_mcp.codex_session import CodexSession

    monkeypatch.setenv("TERM_PROGRAM", "ghostty")
    monkeypatch.setenv("GHOSTTY_RESOURCES_DIR", "/usr/share/ghostty")
    environment = CodexSession._child_environment()
    assert environment["TERM_PROGRAM"] == "ghostty"
    assert environment["GHOSTTY_RESOURCES_DIR"] == "/usr/share/ghostty"


def test_web_child_environment_disables_host_graphics_claim(monkeypatch):
    from lwa_mcp.codex_session import CodexSession

    monkeypatch.setenv("TERM_PROGRAM", "ghostty")
    monkeypatch.setenv("GHOSTTY_RESOURCES_DIR", "/usr/share/ghostty")
    environment = CodexSession._child_environment("web")
    assert environment["TERM"] == "xterm-kitty"
    assert environment["LWA_GRAPHICS_SURFACE"] == "web"
    assert "TERM_PROGRAM" not in environment
    assert "GHOSTTY_RESOURCES_DIR" not in environment


def test_terminal_protocol_preserves_unicode_and_strips_controls():
    from lwa_mcp.terminal_protocol import (
        detect_terminal_capabilities,
        graphics_renderer,
        visible_text,
    )

    fixture = "\x1b[31mπ\x1b[0m \x1b]8;;https://example.test\x07link\x1b]8;;\x07"
    assert visible_text(fixture) == "π link"
    assert visible_text("before\x1b_Gf=100;AAAA\x1b\\after") == "before[graphics omitted]after"
    assert visible_text("before\x1bPq\"1;1;32;32#0;1;1;1$~\x1b\\after") == "before[graphics omitted]after"
    capabilities = detect_terminal_capabilities({"TERM": "xterm-kitty", "KITTY_WINDOW_ID": "7"})
    assert capabilities.kitty_graphics is True
    assert capabilities.sixel_graphics is False
    assert capabilities.public_json()["image_fallback"] == "text-placeholder"
    assert graphics_renderer("web", {"TERM_PROGRAM": "ghostty"}) == "browser-image-gate-pending"
    assert graphics_renderer("native", {"TERM_PROGRAM": "ghostty"}) == "kitty-or-ghostty"


def test_codex_output_can_be_copied_with_available_clipboard_helper(monkeypatch):
    from lwa_mcp import terminal_frame

    monkeypatch.setattr(terminal_frame.shutil, "which", lambda name: "/usr/bin/xclip" if name == "xclip" else None)

    class Completed:
        returncode = 0

    captured = {}

    def run(command, **kwargs):
        captured["command"] = command
        captured["input"] = kwargs["input"]
        return Completed()

    monkeypatch.setattr(terminal_frame.subprocess, "run", run)
    assert terminal_frame._copy_to_clipboard("line one\nline two") == "xclip"
    assert captured == {
        "command": ["xclip", "-selection", "clipboard"],
        "input": "line one\nline two",
    }


@pytest.mark.asyncio
async def test_codex_session_reports_missing_executable():
    from lwa_mcp.codex_session import CodexSession

    events = []

    async def sink(event):
        events.append(event)

    session = CodexSession(sink, executable=None)
    session.executable = None
    await session.start()

    assert events[0]["state"] == "error"


@pytest.mark.asyncio
async def test_codex_session_broker_bounds_and_cleans_up(monkeypatch):
    from lwa_mcp import codex_session

    class FakeSession:
        def __init__(self, sink, executable=None):
            self.sink = sink
            self.executable = executable
            self.process = None
            self.writes = []
            self.closed = False

        async def start(self):
            self.process = object()
            await self.sink({"type": "status", "state": "running", "message": "ready"})

        async def write(self, text):
            self.writes.append(text)

        async def resize(self, columns, rows):
            self.size = (columns, rows)

        async def close(self):
            self.closed = True
            self.process = None

    monkeypatch.setattr(codex_session, "CodexSession", FakeSession)
    broker = codex_session.CodexSessionBroker(max_sessions=1)
    events = []

    async def sink(event):
        events.append(event)

    session_id, state = await broker.create()
    assert state == "created"
    client_id = await broker.attach(session_id, sink)
    await broker.write(session_id, client_id, "hello")
    await broker.resize(session_id, client_id, 80, 24)
    assert events[-2]["state"] == "attached"
    assert events[-1]["state"] == "running"
    assert broker.status()[0]["clients"] == 1
    await broker.detach(session_id, client_id)
    assert broker.status() == []


@pytest.mark.asyncio
async def test_web_prompt_boundary_does_not_emit_raw_prompt(monkeypatch):
    from lwa_mcp import dashboard

    class FakeWebSocket:
        def __init__(self):
            self.query_params = {}
            self.sent = []
            self.messages = [
                json.dumps({"type": "prompt", "mode": "compact", "text": "/literal/path --flag\n\n\nacceptance"}),
                json.dumps({"type": "close"}),
            ]

        async def accept(self):
            return None

        async def receive_text(self):
            return self.messages.pop(0)

        async def send_text(self, value):
            self.sent.append(value)

    class FakeBroker:
        def __init__(self):
            self.writes = []
            self.detached = False

        async def create(self):
            return "session-test", "created"

        async def attach(self, session_id, sink):
            await sink({"type": "session", "state": "attached"})
            return "client-test"

        async def write(self, session_id, client_id, text):
            self.writes.append(text)

        async def resize(self, *args):
            return None

        async def detach(self, session_id, client_id):
            self.detached = True

        async def discard(self, session_id):
            raise AssertionError("attached sessions should detach")

    websocket = FakeWebSocket()
    broker = FakeBroker()
    monkeypatch.setattr(dashboard, "codex_broker", broker)
    await dashboard.codex_socket(websocket)

    payload = "".join(websocket.sent)
    assert "/literal/path" not in payload
    assert broker.writes == ["/literal/path --flag\n\nacceptance\n"]
    assert broker.detached is True
