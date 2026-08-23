#!/usr/bin/env python3
"""Shared implementation for bounded, provider-free MCP capability checks."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import time
from pathlib import Path
from typing import Any

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REQUIRED_TOOLS = {"prepare_task", "approve_preflight", "run_prepared_task", "router_status"}
REQUIRED_RESOURCES = {"lwa://status", "lwa://catalog"}
REQUIRED_PROMPTS = {"preflight_guidance"}


def command_from_text(root: Path, command_text: str | None) -> list[str]:
    if command_text:
        return shlex.split(command_text)
    installed = root / ".venv/bin/lwa-mcp"
    return [str(installed if installed.exists() else "lwa-mcp")]


def config_fingerprint() -> str:
    path_text = os.environ.get("LWA_MCP_CONFIG", "")
    if not path_text:
        return "unset"
    path = Path(path_text)
    try:
        content = path.read_bytes()
    except OSError:
        return f"missing:{path}"
    return f"{path.resolve()}:{hashlib.sha256(content).hexdigest()}"


def server_fingerprint(command: list[str]) -> str:
    try:
        stat = Path(command[0]).stat()
    except OSError:
        return f"unresolved:{command[0]}"
    return f"{Path(command[0]).resolve()}:{stat.st_size}:{stat.st_mtime_ns}"


def base_identity(command: list[str], root: Path) -> dict[str, Any]:
    return {
        "command": command,
        "server_fingerprint": server_fingerprint(command),
        "root": str(root.resolve()),
        "config_fingerprint": config_fingerprint(),
    }


def manifest_is_complete(manifest: dict[str, Any]) -> bool:
    return (
        REQUIRED_TOOLS <= set(manifest.get("tools", []))
        and REQUIRED_RESOURCES <= set(manifest.get("resources", []))
        and REQUIRED_PROMPTS <= set(manifest.get("prompts", []))
    )


def cache_key(identity: dict[str, Any], protocol_version: str) -> str:
    payload = json.dumps({**identity, "protocol_version": protocol_version}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_cache(path: Path, identity: dict[str, Any]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("identity") != identity or not manifest_is_complete(payload.get("manifest", {})):
            return None
        return payload
    except (OSError, ValueError, TypeError):
        return None


def save_cache(path: Path, identity: dict[str, Any], manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "identity": identity,
        "manifest": manifest,
        "cache_key": cache_key(identity, manifest["protocol_version"]),
        "saved_at": time.time(),
    }
    temporary = path.with_suffix(f"{path.suffix}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    temporary.replace(path)


async def discover(command: list[str], root: Path, timeout: float) -> dict[str, Any]:
    started = time.monotonic()
    params = StdioServerParameters(command=command[0], args=command[1:], cwd=root)
    with anyio.fail_after(timeout):
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                initialized = await session.initialize()
                tools = sorted(item.name for item in (await session.list_tools()).tools)
                resources = sorted(str(item.uri) for item in (await session.list_resources()).resources)
                prompts = sorted(item.name for item in (await session.list_prompts()).prompts)
    manifest = {
        "protocol_version": initialized.protocolVersion,
        "tools": tools,
        "resources": resources,
        "prompts": prompts,
        "elapsed_ms": round((time.monotonic() - started) * 1000),
    }
    if not manifest_is_complete(manifest):
        raise RuntimeError(
            "MCP surface incomplete: "
            f"tools={sorted(REQUIRED_TOOLS - set(tools))}, "
            f"resources={sorted(REQUIRED_RESOURCES - set(resources))}, "
            f"prompts={sorted(REQUIRED_PROMPTS - set(prompts))}"
        )
    return manifest
