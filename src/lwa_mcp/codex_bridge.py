"""Own the real Codex PTY inside a second terminal window."""

from __future__ import annotations

import argparse
import asyncio
import codecs
import json
import os
import signal
import subprocess
import sys
from collections.abc import Awaitable, Callable
from contextlib import suppress
from pathlib import Path

from .codex_session import CodexSession
from .image_compositor import ImageCompositor
from .terminal_protocol import TerminalStreamFilter, redact_terminal_text

EventSink = Callable[[dict[str, object]], Awaitable[None]]


async def _noop(_event: dict[str, object]) -> None:
    return None


class CodexBridge:
    """Run Codex in a PTY and publish a clean event stream over a Unix socket."""

    def __init__(
        self,
        *,
        socket_path: str,
        executable: str | None,
        cwd: str | None,
        disable_lwa_mcp: bool,
    ) -> None:
        self.socket_path = Path(socket_path)
        self.session = CodexSession(
            _noop,
            executable=executable,
            cwd=cwd,
            disable_lwa_mcp=disable_lwa_mcp,
        )
        self.server: asyncio.base_events.Server | None = None
        self.clients: set[asyncio.StreamWriter] = set()
        self.history: list[dict[str, object]] = []
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._terminal_filter = TerminalStreamFilter()
        self._image_compositor = ImageCompositor()
        self._reader_task: asyncio.Task[None] | None = None
        self._stdin_task: asyncio.Task[None] | None = None
        self._wait_task: asyncio.Task[int] | None = None
        self._process_task: asyncio.Task[int] | None = None
        self._shutdown_event = asyncio.Event()
        self._client_connected = asyncio.Event()
        self._running = False

    def _record(self, event: dict[str, object]) -> None:
        self.history.append(event)
        if len(self.history) > 800:
            del self.history[:-800]

    async def _broadcast(self, event: dict[str, object]) -> None:
        self._record(event)
        payload = json.dumps(event, separators=(",", ":")).encode("utf-8") + b"\n"
        dead: list[asyncio.StreamWriter] = []
        for writer in tuple(self.clients):
            try:
                writer.write(payload)
                await writer.drain()
            except Exception:  # noqa: BLE001
                dead.append(writer)
        for writer in dead:
            self.clients.discard(writer)

    async def _emit_terminal(self, data: bytes, *, final: bool = False) -> None:
        decoded = self._decoder.decode(data, final=final)
        safe_decoded = redact_terminal_text(decoded)
        frames, graphics_issue = self._image_compositor.feed(decoded)
        for frame in frames:
            await self._broadcast({"type": "graphics", "frame": frame.public_json()})
        if graphics_issue:
            await self._broadcast({"type": "graphics", "state": "fallback", "message": graphics_issue})
        clean = self._terminal_filter.feed(safe_decoded, final=final)
        if clean:
            await self._broadcast({"type": "terminal", "data": clean})

    async def _read_pty(self, master: int) -> None:
        while True:
            try:
                data = await asyncio.to_thread(os.read, master, 65536)
            except OSError:
                break
            if not data:
                break
            try:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            except Exception:  # noqa: BLE001, S110
                pass
            await self._emit_terminal(data)
        await self._emit_terminal(b"", final=True)
        await self._broadcast({"type": "status", "state": "exited", "message": "Codex process exited."})

    async def _forward_stdin(self, master: int) -> None:
        while True:
            try:
                data = await asyncio.to_thread(sys.stdin.buffer.read, 4096)
            except Exception:  # noqa: BLE001
                break
            if not data:
                break
            try:
                await asyncio.to_thread(os.write, master, data)
            except OSError:
                break

    async def _client_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.clients.add(writer)
        self._client_connected.set()
        try:
            for event in self.history:
                writer.write(json.dumps(event, separators=(",", ":")).encode("utf-8") + b"\n")
            await writer.drain()
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    message = json.loads(line.decode("utf-8", "replace"))
                except json.JSONDecodeError:
                    continue
                if not isinstance(message, dict):
                    continue
                kind = str(message.get("type", ""))
                if kind == "write" and isinstance(message.get("text"), str):
                    try:
                        await self.session.write(message["text"])
                    except Exception as exc:  # noqa: BLE001
                        await self._broadcast({"type": "status", "state": "error", "message": str(exc)})
                elif kind == "resize":
                    try:
                        await self.session.resize(
                            int(message.get("columns", 0)),
                            int(message.get("rows", 0)),
                        )
                    except Exception as exc:  # noqa: BLE001
                        await self._broadcast({"type": "status", "state": "error", "message": str(exc)})
                elif kind == "close":
                    self._running = False
                    self._shutdown_event.set()
                    break
        finally:
            self.clients.discard(writer)
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()

    def _set_pty_size(self, master: int) -> None:
        try:
            size = os.get_terminal_size(sys.stdout.fileno())
            columns, rows = size.columns, size.lines
        except OSError:
            rows, columns = 24, 80
        try:
            import termios

            termios.tcsetwinsize(master, (max(1, rows), max(1, columns)))
        except Exception:  # noqa: BLE001, S110
            pass

    async def _wait_process(self) -> int:
        process = self.session.process
        if isinstance(process, asyncio.subprocess.Process):
            return await process.wait()
        if process is not None:
            return await asyncio.to_thread(process.wait)
        return 0

    async def _wait_for_client(self, timeout: float = 30.0) -> None:
        """Prevent an unclaimed bridge from surviving a failed window launch."""
        try:
            await asyncio.wait_for(self._client_connected.wait(), timeout=timeout)
        except TimeoutError:
            await self._broadcast(
                {
                    "type": "status",
                    "state": "error",
                    "message": "LWA did not attach to the Codex terminal bridge in time.",
                }
            )
            self._shutdown_event.set()

    async def run(self) -> int:
        if not self.session.executable:
            print("Codex was not found on PATH.", file=sys.stderr)
            return 127
        if self.socket_path.exists():
            with suppress(OSError):
                self.socket_path.unlink()
        self.socket_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with suppress(OSError):
            self.socket_path.parent.chmod(0o700)
        self.server = await asyncio.start_unix_server(self._client_handler, path=str(self.socket_path))
        with suppress(OSError):
            self.socket_path.chmod(0o600)
        self._running = True
        if os.name == "posix":
            import pty

            master, slave = pty.openpty()
            self.session.master_fd = master
            try:
                self.session.process = await asyncio.to_thread(
                    subprocess.Popen,
                    self.session._command(),
                    stdin=slave,
                    stdout=slave,
                    stderr=slave,
                    cwd=self.session.cwd,
                    env=self.session._child_environment(self.session.graphics_surface),
                    start_new_session=True,
                    close_fds=True,
                )
            finally:
                os.close(slave)
            self._set_pty_size(master)
            self._reader_task = asyncio.create_task(self._read_pty(master))
            self._stdin_task = asyncio.create_task(self._forward_stdin(master))
        else:
            self.session.process = await asyncio.create_subprocess_exec(
                *self.session._command(),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.session.cwd,
                env=self.session._child_environment(self.session.graphics_surface),
            )
            self._reader_task = asyncio.create_task(self._read_pipe())
        self._process_task = asyncio.create_task(self._wait_process())
        client_task = asyncio.create_task(self._wait_for_client())
        shutdown_task = asyncio.create_task(self._shutdown_event.wait())
        await self._broadcast(
            {
                "type": "status",
                "state": "running",
                "message": "Codex bridge connected.",
                "accessible_text": True,
                "graphics": bool(self.session.graphics_surface == "native"),
            }
        )
        if self.server.sockets:
            await self._broadcast(
                {
                    "type": "status",
                    "state": "bridge",
                    "message": f"Codex bridge listening on {self.socket_path}.",
                }
            )
        try:
            done, pending = await asyncio.wait(
                {
                    task
                    for task in (self._process_task, self._reader_task, self._stdin_task, client_task, shutdown_task)
                    if task is not None
                },
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                with suppress(Exception):
                    await task
            returncode = 0
            process = self.session.process
            if isinstance(process, asyncio.subprocess.Process):
                returncode = process.returncode or 0
            elif process is not None:
                returncode = process.poll() or 0
            return returncode
        finally:
            shutdown_task.cancel()
            client_task.cancel()
            with suppress(asyncio.CancelledError):
                await shutdown_task
            with suppress(asyncio.CancelledError):
                await client_task
            await self.close()

    async def _read_pipe(self) -> None:
        process = self.session.process
        if not isinstance(process, asyncio.subprocess.Process) or process.stdout is None:
            return
        while data := await process.stdout.read(65536):
            try:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            except Exception:  # noqa: BLE001, S110
                pass
            await self._emit_terminal(data)
        await self._emit_terminal(b"", final=True)

    async def close(self) -> None:
        self._running = False
        for task in (self._reader_task, self._stdin_task, self._process_task):
            if task is not None and not task.done():
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
        self._reader_task = None
        self._stdin_task = None
        self._process_task = None
        if self.server is not None:
            self.server.close()
            with suppress(Exception):
                await self.server.wait_closed()
            self.server = None
        process = self.session.process
        if isinstance(process, asyncio.subprocess.Process):
            if process.returncode is None:
                process.terminate()
                with suppress(Exception):
                    await asyncio.wait_for(process.wait(), timeout=2)
        elif process is not None and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                await asyncio.to_thread(process.wait, timeout=2)
            except subprocess.TimeoutExpired:
                with suppress(Exception):
                    process.kill()
                with suppress(Exception):
                    await asyncio.to_thread(process.wait, timeout=2)
        self.session.process = None
        if self.session.master_fd is not None:
            with suppress(OSError):
                os.close(self.session.master_fd)
            self.session.master_fd = None
        if self.socket_path.exists():
            with suppress(OSError):
                self.socket_path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lwa-codex-bridge", description="Run Codex in a bridged terminal window.")
    parser.add_argument("--socket", required=True)
    parser.add_argument("--cwd")
    parser.add_argument("--codex")
    parser.add_argument("--disable-lwa-mcp", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    bridge = CodexBridge(
        socket_path=args.socket,
        executable=args.codex,
        cwd=args.cwd,
        disable_lwa_mcp=args.disable_lwa_mcp,
    )
    try:
        raise SystemExit(asyncio.run(bridge.run()))
    except KeyboardInterrupt:
        # SIGINT is an expected terminal action, not an application error.
        # Never print the asyncio runner traceback into a user-owned pane.
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
