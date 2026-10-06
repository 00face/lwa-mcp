"""Small stdio JSON-RPC client for the local Codex app-server."""

from __future__ import annotations

import asyncio
import json
import shutil
from typing import Any


class CodexAppServerError(RuntimeError):
    pass


def normalize_rate_limits(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep the quota fields needed by Lwa without exposing account secrets."""
    primary = payload.get("primary") or {}
    reached = bool(payload.get("rateLimitReachedType"))
    return {
        "provider": "codex",
        "source": "codex_app_server",
        "authoritative": True,
        "rate_limit_reached_type": payload.get("rateLimitReachedType"),
        "plan_type": payload.get("planType"),
        "primary": primary,
        "secondary": payload.get("secondary"),
        "spend_control_reached": payload.get("spendControlReached"),
        "quota_exhausted": reached or primary.get("usedPercent") == 100,
        "reset_at": primary.get("resetsAt"),
    }


class CodexAppServerClient:
    def __init__(self, executable: str | None = None, *, timeout_seconds: float = 30.0):
        self.executable = executable or shutil.which("codex") or "codex"
        self.timeout_seconds = timeout_seconds

    async def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        process = await asyncio.create_subprocess_exec(
            self.executable, "app-server", "--listen", "stdio://",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await self._send(process, 1, "initialize", {
                "clientInfo": {"name": "lwa-mcp", "title": "Lwa MCP", "version": "0.4.2"},
            })
            await self._response(process, 1)
            await self._send_notification(process, "initialized", {})
            await self._send(process, 2, method, params or {})
            return await self._response(process, 2)
        finally:
            if process.returncode is None:
                process.terminate()
            await process.wait()

    async def read_rate_limits(self) -> dict[str, Any]:
        return await self.request("account/rateLimits/read")

    async def read_usage(self) -> dict[str, Any]:
        return await self.request("account/usage/read")

    async def complete(
        self, *, model: str, prompt: str, system_prompt: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        """Run one isolated Codex thread and collect its agent-message stream."""
        process = await asyncio.create_subprocess_exec(
            self.executable, "app-server", "--listen", "stdio://",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await self._send(process, 1, "initialize", {
                "clientInfo": {"name": "lwa-mcp", "title": "Lwa MCP", "version": "0.4.2"},
            })
            await self._response(process, 1)
            await self._send_notification(process, "initialized", {})
            await self._send(process, 2, "thread/start", {"model": model, "ephemeral": True})
            thread = await self._response(process, 2)
            thread_id = str((thread.get("thread") or {}).get("id") or "")
            if not thread_id:
                raise CodexAppServerError("Codex app-server did not return a thread id")
            prompt_text = prompt if not system_prompt else f"{system_prompt}\n\n{prompt}"
            await self._send(process, 3, "turn/start", {
                "threadId": thread_id,
                "input": [{"type": "text", "text": prompt_text}],
                "model": model,
            })
            await self._response(process, 3)
            deltas: list[str] = []
            completed: dict[str, Any] = {}
            if process.stdout is None:
                raise CodexAppServerError("Codex app-server stdout is unavailable")
            while True:
                raw = await asyncio.wait_for(process.stdout.readline(), self.timeout_seconds)
                if not raw:
                    raise CodexAppServerError("Codex app-server exited during turn")
                message = json.loads(raw)
                method = message.get("method")
                params = message.get("params") or {}
                if method == "item/agentMessage/delta":
                    deltas.append(str(params.get("delta") or ""))
                elif method == "turn/completed":
                    completed = params.get("turn") or params
                    if completed.get("status") != "completed":
                        raise CodexAppServerError(f"Codex turn ended with status {completed.get('status')}")
                    return "".join(deltas), completed
        finally:
            if process.returncode is None:
                process.terminate()
            await process.wait()

    async def _send(self, process, request_id: int, method: str, params: dict[str, Any]) -> None:
        await self._send_raw(process, {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})

    async def _send_notification(self, process, method: str, params: dict[str, Any]) -> None:
        await self._send_raw(process, {"jsonrpc": "2.0", "method": method, "params": params})

    async def _send_raw(self, process, payload: dict[str, Any]) -> None:
        if process.stdin is None:
            raise CodexAppServerError("Codex app-server stdin is unavailable")
        process.stdin.write((json.dumps(payload, separators=(",", ":")) + "\n").encode())
        await process.stdin.drain()

    async def _response(self, process, request_id: int) -> dict[str, Any]:
        if process.stdout is None:
            raise CodexAppServerError("Codex app-server stdout is unavailable")
        while True:
            raw = await asyncio.wait_for(process.stdout.readline(), self.timeout_seconds)
            if not raw:
                raise CodexAppServerError("Codex app-server exited before responding")
            message = json.loads(raw)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise CodexAppServerError(str(message["error"]))
            result = message.get("result")
            if not isinstance(result, dict):
                raise CodexAppServerError("Codex app-server returned a non-object result")
            return result
