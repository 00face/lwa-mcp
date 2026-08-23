"""Small PTY bridge used by the local graphical Codex workspace."""

from __future__ import annotations

import asyncio
import codecs
import json
import os
import secrets
import shutil
import signal
import subprocess
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path

from .image_compositor import ImageCompositor
from .terminal_protocol import (
    TerminalStreamFilter,
    detect_terminal_capabilities,
    redact_terminal_text,
)

if os.name == "posix":
    import termios
else:  # pragma: no cover - exercised on Windows
    termios = None

EventSink = Callable[[dict[str, object]], Awaitable[None]]


class CodexSession:
    """Own one local Codex process and expose its terminal byte stream."""

    def __init__(self, sink: EventSink, executable: str | None = None, cwd: str | None = None, *, disable_lwa_mcp: bool = False, graphics_surface: str = "native") -> None:
        self.sink = sink
        self.executable = executable or shutil.which("codex")
        self.cwd = str(Path(cwd).expanduser().resolve()) if cwd else None
        self.disable_lwa_mcp = disable_lwa_mcp
        self.graphics_surface = graphics_surface
        if self.cwd and not Path(self.cwd).is_dir():
            raise ValueError("Codex working directory is not a directory")
        self.process: subprocess.Popen[bytes] | asyncio.subprocess.Process | None = None
        self.master_fd: int | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._terminal_filter = TerminalStreamFilter()
        self._image_compositor = ImageCompositor()

    async def _emit_terminal(self, data: bytes, *, final: bool = False) -> None:
        decoded = self._decoder.decode(data, final=final)
        # Decode graphics from the original PTY stream. Redaction is applied
        # only to text/transcript output; altering a base64 payload can corrupt
        # an otherwise valid image.
        safe_decoded = redact_terminal_text(decoded)
        frames, graphics_issue = self._image_compositor.feed(decoded)
        for frame in frames:
            await self.sink({"type": "graphics", "frame": frame.public_json()})
        if graphics_issue:
            await self.sink({"type": "graphics", "state": "fallback", "message": graphics_issue})
        clean = self._terminal_filter.feed(safe_decoded, final=final)
        if clean:
            await self.sink({"type": "terminal", "data": clean})

    def _command(self) -> list[str]:
        command = [self.executable or "codex", "--no-alt-screen"]
        if self.disable_lwa_mcp:
            command.extend(["-c", 'plugins."lwa-mcp@armando-local".enabled=false'])
        return command

    @staticmethod
    def _child_environment(graphics_surface: str = "native") -> dict[str, str]:
        """Give Codex an honest native or virtual browser graphics profile."""
        environment = os.environ.copy()
        original_term = environment.get("TERM", "")
        capabilities = detect_terminal_capabilities(environment)
        ghostty = environment.get("TERM_PROGRAM", "").lower() == "ghostty" or bool(
            environment.get("GHOSTTY_RESOURCES_DIR")
        )
        native_graphics = ghostty or capabilities.kitty_graphics or capabilities.sixel_graphics
        if graphics_surface == "web":
            # The browser compositor consumes Kitty frames from the PTY. It is
            # a virtual graphics sink, not a claim that the browser is Kitty.
            environment["TERM"] = "xterm-kitty"
            environment["LWA_GRAPHICS_SURFACE"] = "web"
            for key in ("TERM_PROGRAM", "GHOSTTY_RESOURCES_DIR", "KITTY_WINDOW_ID", "COLORTERM"):
                environment.pop(key, None)
        elif native_graphics:
            environment["TERM"] = original_term or ("xterm-ghostty" if ghostty else "xterm-kitty")
        else:
            environment["TERM"] = "xterm-256color"
            for key in ("TERM_PROGRAM", "GHOSTTY_RESOURCES_DIR", "KITTY_WINDOW_ID", "COLORTERM"):
                environment.pop(key, None)
        return environment

    async def start(self) -> None:
        if not self.executable:
            await self.sink({"type": "status", "state": "error", "message": "Codex was not found on PATH."})
            return
        if os.name == "posix":
            import pty

            master, slave = pty.openpty()
            self.master_fd = master
            try:
                self.process = await asyncio.to_thread(
                    subprocess.Popen,
                    self._command(),
                    stdin=slave,
                    stdout=slave,
                    stderr=slave,
                    cwd=self.cwd,
                    env=self._child_environment(self.graphics_surface),
                    start_new_session=True,
                    close_fds=True,
                )
            finally:
                os.close(slave)
            self._reader_task = asyncio.create_task(self._read_pty(master))
        else:
            self.process = await asyncio.create_subprocess_exec(
                *self._command(),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.cwd,
                env=self._child_environment(self.graphics_surface),
            )
            self._reader_task = asyncio.create_task(self._read_pipe())
        await self.sink({"type": "status", "state": "running", "message": "Codex session connected."})

    async def _read_pty(self, master: int) -> None:
        while True:
            try:
                data = await asyncio.to_thread(os.read, master, 65536)
            except OSError:
                return
            if not data:
                return
            await self._emit_terminal(data)
        await self._emit_terminal(b"", final=True)
        await self.sink({"type": "status", "state": "exited", "message": "Codex process exited."})

    async def _read_pipe(self) -> None:
        process = self.process
        if not isinstance(process, asyncio.subprocess.Process) or process.stdout is None:
            return
        while data := await process.stdout.read(65536):
            await self._emit_terminal(data)
        await self._emit_terminal(b"", final=True)
        await self.sink({"type": "status", "state": "exited", "message": "Codex process exited."})

    async def write(self, text: str) -> None:
        data = text.encode("utf-8", "replace")
        if self.master_fd is not None:
            try:
                await asyncio.to_thread(os.write, self.master_fd, data)
            except OSError as exc:
                raise RuntimeError("Codex PTY is no longer available") from exc
        elif isinstance(self.process, asyncio.subprocess.Process) and self.process.stdin:
            self.process.stdin.write(data)
            await self.process.stdin.drain()

    async def resize(self, columns: int, rows: int) -> None:
        if self.master_fd is not None and os.name == "posix" and termios is not None:
            try:
                termios.tcsetwinsize(self.master_fd, (max(1, rows), max(1, columns)))
            except OSError as exc:
                raise RuntimeError("Codex PTY is no longer available") from exc

    async def close(self) -> None:
        reader_task = self._reader_task
        self._reader_task = None
        if reader_task:
            reader_task.cancel()
            with suppress(asyncio.CancelledError):
                await reader_task
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None
        process = self.process
        if isinstance(process, asyncio.subprocess.Process):
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=2)
                except TimeoutError:
                    process.kill()
        elif process is not None and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        self.process = None


class NativeTmuxCodexSession:
    """Control a Codex process that is visibly owned by a tmux pane.

    Unlike ``BridgeCodexSession``, this session deliberately does not mirror
    Codex output into LWA. Codex keeps its own native screen, prompt, modal,
    graphics, and selection behavior in the target pane.
    """

    def __init__(self, sink: EventSink, pane_id: str, *, tmux: str = "tmux") -> None:
        self.sink = sink
        self.pane_id = pane_id
        self.tmux = tmux
        self.is_running = False
        self._buffer_name = f"lwa-codex-{os.getpid()}"

    async def start(self) -> None:
        self.is_running = True
        await self.sink(
            {
                "type": "status",
                "state": "running",
                "message": f"Native Codex pane connected ({self.pane_id}).",
                "native_split": True,
            }
        )

    async def write(self, text: str) -> None:
        if not self.is_running:
            raise RuntimeError("Native Codex pane is no longer available")
        payload = text.encode("utf-8", "replace")
        try:
            await asyncio.to_thread(
                subprocess.run,
                [self.tmux, "load-buffer", "-b", self._buffer_name, "-"],
                input=payload,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=True,
            )
            await asyncio.to_thread(
                subprocess.run,
                [self.tmux, "paste-buffer", "-b", self._buffer_name, "-t", self.pane_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            self.is_running = False
            raise RuntimeError("Native Codex pane is no longer available") from exc

    async def resize(self, columns: int, rows: int) -> None:
        if not self.is_running:
            return
        try:
            await asyncio.to_thread(
                subprocess.run,
                [
                    self.tmux,
                    "resize-pane",
                    "-t",
                    self.pane_id,
                    "-x",
                    str(max(1, columns)),
                    "-y",
                    str(max(1, rows)),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            self.is_running = False
            raise RuntimeError("Native Codex pane is no longer available") from exc

    async def close(self) -> None:
        if not self.is_running:
            return
        self.is_running = False
        with suppress(OSError, subprocess.CalledProcessError):
            await asyncio.to_thread(
                subprocess.run,
                [self.tmux, "delete-buffer", "-b", self._buffer_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        with suppress(OSError, subprocess.CalledProcessError):
            await asyncio.to_thread(
                subprocess.run,
                [self.tmux, "kill-pane", "-t", self.pane_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
class BridgeCodexSession:
    """Attach to a Codex bridge process that owns the real PTY."""

    def __init__(self, sink: EventSink, socket_path: str, *, timeout: float = 15.0) -> None:
        self.sink = sink
        self.socket_path = socket_path
        self.timeout = timeout
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._ready = False
        self.process = None

    @property
    def is_running(self) -> bool:
        return self._ready and self.writer is not None

    async def _connect(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        deadline = asyncio.get_running_loop().time() + self.timeout
        while True:
            try:
                return await asyncio.open_unix_connection(self.socket_path)
            except (FileNotFoundError, ConnectionRefusedError, OSError):
                if asyncio.get_running_loop().time() >= deadline:
                    raise RuntimeError(f"Codex bridge was not reachable at {self.socket_path}")
                await asyncio.sleep(0.1)

    async def start(self) -> None:
        self.reader, self.writer = await self._connect()
        self._ready = True
        self._reader_task = asyncio.create_task(self._read())
        await self.sink(
            {
                "type": "status",
                "state": "running",
                "message": f"Codex bridge connected at {self.socket_path}.",
            }
        )

    async def _read(self) -> None:
        reader = self.reader
        if reader is None:
            return
        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                event = json.loads(line.decode("utf-8", "replace"))
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                await self.sink(event)
        self._ready = False
        await self.sink({"type": "status", "state": "exited", "message": "Codex bridge disconnected."})

    async def _send(self, payload: dict[str, object]) -> None:
        writer = self.writer
        if writer is None:
            raise RuntimeError("Codex bridge is not connected")
        writer.write(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")
        await writer.drain()

    async def write(self, text: str) -> None:
        await self._send({"type": "write", "text": text})

    async def resize(self, columns: int, rows: int) -> None:
        await self._send({"type": "resize", "columns": max(1, columns), "rows": max(1, rows)})

    async def close(self) -> None:
        reader_task = self._reader_task
        self._reader_task = None
        if reader_task:
            reader_task.cancel()
            with suppress(asyncio.CancelledError):
                await reader_task
        if self.writer is not None:
            try:
                await self._send({"type": "close"})
            except Exception:  # noqa: BLE001, S110
                pass
            self.writer.close()
            with suppress(Exception):
                await self.writer.wait_closed()
        self.writer = None
        self.reader = None
        self._ready = False


@dataclass(slots=True)
class _BrokerEntry:
    session: CodexSession
    sinks: dict[str, EventSink] = field(default_factory=dict)


class CodexSessionBroker:
    """Bounded local broker for attaching multiple LWA surfaces to a session."""

    def __init__(self, *, max_sessions: int = 2) -> None:
        self.max_sessions = max_sessions
        self.sessions: dict[str, _BrokerEntry] = {}
        self._lock = asyncio.Lock()

    async def _broadcast(self, session_id: str, event: dict[str, object]) -> None:
        entry = self.sessions.get(session_id)
        if entry is None:
            return
        payload = {"session_id": session_id, **event}
        for sink in tuple(entry.sinks.values()):
            try:
                await sink(payload)
            except RuntimeError:
                pass

    async def create(self, executable: str | None = None, cwd: str | None = None, *, disable_lwa_mcp: bool = True, graphics_surface: str = "native") -> tuple[str, str]:
        async with self._lock:
            if len(self.sessions) >= self.max_sessions:
                raise RuntimeError("The Lwa Codex session limit has been reached.")
            session_id = secrets.token_urlsafe(12)
            sink = lambda event: self._broadcast(session_id, event)
            try:
                session = CodexSession(sink, executable, cwd, disable_lwa_mcp=disable_lwa_mcp, graphics_surface=graphics_surface)
            except TypeError as exc:
                # Preserve compatibility with lightweight test/integration doubles.
                if "disable_lwa_mcp" not in str(exc):
                    raise
                session = CodexSession(sink, executable, cwd) if cwd else CodexSession(sink, executable)
            self.sessions[session_id] = _BrokerEntry(session)
        try:
            await session.start()
        except BaseException:
            self.sessions.pop(session_id, None)
            await session.close()
            raise
        return session_id, "created"

    async def discard(self, session_id: str) -> None:
        """Close a session that was created but never successfully attached."""
        entry = self.sessions.pop(session_id, None)
        if entry is not None:
            await entry.session.close()

    async def attach(self, session_id: str, sink: EventSink) -> str:
        entry = self.sessions.get(session_id)
        if entry is None:
            raise ValueError("Unknown or expired Codex session")
        client_id = secrets.token_urlsafe(9)
        entry.sinks[client_id] = sink
        await sink({"session_id": session_id, "type": "session", "state": "attached"})
        if entry.session.process is not None:
            await sink(
                {
                    "session_id": session_id,
                    "type": "status",
                    "state": "running",
                    "message": "Codex session connected.",
                }
            )
        else:
            await sink(
                {
                    "session_id": session_id,
                    "type": "status",
                    "state": "error",
                    "message": "Codex was not found on PATH or exited during startup.",
                }
            )
        return client_id

    async def detach(self, session_id: str, client_id: str) -> None:
        entry = self.sessions.get(session_id)
        if entry is None:
            return
        entry.sinks.pop(client_id, None)
        if not entry.sinks:
            await entry.session.close()
            self.sessions.pop(session_id, None)

    async def write(self, session_id: str, client_id: str, text: str) -> None:
        entry = self.sessions.get(session_id)
        if entry is None or client_id not in entry.sinks:
            raise ValueError("Unknown or detached Codex session")
        await entry.session.write(text)

    async def resize(self, session_id: str, client_id: str, columns: int, rows: int) -> None:
        if not 20 <= columns <= 400 or not 8 <= rows <= 200:
            raise ValueError("Terminal dimensions are outside the safe range")
        entry = self.sessions.get(session_id)
        if entry is None or client_id not in entry.sinks:
            raise ValueError("Unknown or detached Codex session")
        await entry.session.resize(columns, rows)

    def status(self) -> list[dict[str, object]]:
        return [
            {"session_id": session_id, "clients": len(entry.sinks), "active": entry.session.process is not None}
            for session_id, entry in self.sessions.items()
        ]
