import asyncio
import json

import pytest


@pytest.mark.asyncio
async def test_bridge_session_routes_commands_and_status(tmp_path):
    from lwa_mcp.codex_session import BridgeCodexSession

    received = []
    events = []

    async def handler(reader, writer):
        for event in ({"type": "status", "state": "running"}, {"type": "terminal", "data": "hello"}):
            writer.write(json.dumps(event).encode() + b"\n")
            await writer.drain()
        while line := await reader.readline():
            message = json.loads(line)
            received.append(message)
            if message["type"] == "close":
                break
        writer.close()
        await writer.wait_closed()

    socket_path = tmp_path / "bridge.sock"
    server = await asyncio.start_unix_server(handler, path=str(socket_path))

    async def sink(event):
        events.append(event)

    session = BridgeCodexSession(sink, str(socket_path), timeout=1)
    await session.start()
    await session.write("hello\n")
    await session.resize(120, 40)
    for _ in range(10):
        if any(event.get("type") == "terminal" for event in events):
            break
        await asyncio.sleep(0.01)
    await session.close()
    server.close()
    await server.wait_closed()

    assert received[:2] == [
        {"type": "write", "text": "hello\n"},
        {"type": "resize", "columns": 120, "rows": 40},
    ]
    assert any(event.get("type") == "status" and event.get("state") == "running" for event in events)
    assert {"type": "terminal", "data": "hello"} in events
    assert session.is_running is False


@pytest.mark.asyncio
async def test_bridge_times_out_when_controller_never_attaches(tmp_path):
    from lwa_mcp.codex_bridge import CodexBridge

    events = []
    bridge = CodexBridge(
        socket_path=str(tmp_path / "bridge.sock"),
        executable="codex-test",
        cwd=str(tmp_path),
        disable_lwa_mcp=True,
    )

    async def broadcast(event):
        events.append(event)

    bridge._broadcast = broadcast
    await bridge._wait_for_client(timeout=0.01)

    assert bridge._shutdown_event.is_set()
    assert events == [
        {
            "type": "status",
            "state": "error",
            "message": "LWA did not attach to the Codex terminal bridge in time.",
        }
    ]


@pytest.mark.asyncio
async def test_native_tmux_session_routes_payload_resize_and_close(monkeypatch):
    from lwa_mcp.codex_session import NativeTmuxCodexSession

    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))

    monkeypatch.setattr("lwa_mcp.codex_session.subprocess.run", fake_run)
    events = []

    async def sink(event):
        events.append(event)

    session = NativeTmuxCodexSession(sink, "%7", tmux="tmux-test")
    await session.start()
    await session.write("\x1b[200~hello\x1b[201~\r")
    await session.resize(120, 40)
    await session.close()

    assert events[0]["native_split"] is True
    assert calls[0][0] == ["tmux-test", "load-buffer", "-b", calls[0][0][3], "-"]
    assert calls[0][1]["input"] == b"\x1b[200~hello\x1b[201~\r"
    assert calls[1][0] == ["tmux-test", "paste-buffer", "-b", calls[0][0][3], "-t", "%7"]
    assert calls[2][0] == ["tmux-test", "resize-pane", "-t", "%7", "-x", "120", "-y", "40"]
    assert calls[-2][0][:3] == ["tmux-test", "delete-buffer", "-b"]
    assert calls[-1][0] == ["tmux-test", "kill-pane", "-t", "%7"]


def test_bridge_main_converts_keyboard_interrupt_to_clean_exit(monkeypatch):
    from lwa_mcp import codex_bridge

    def raise_interrupt(coro):
        coro.close()
        raise KeyboardInterrupt

    monkeypatch.setattr(codex_bridge.asyncio, "run", raise_interrupt)
    monkeypatch.setattr(codex_bridge.sys, "argv", ["lwa-codex-bridge", "--socket", "/tmp/x"])

    with pytest.raises(SystemExit) as exc:
        codex_bridge.main()
    assert exc.value.code == 130
