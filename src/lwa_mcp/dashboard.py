from __future__ import annotations

import json
from importlib.resources import files

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, SecretStr, field_validator

from .codex_session import CodexSessionBroker
from .config import load_config
from .credentials import managed_credentials, update_managed_credential
from .models import ConsentMode, parse_consent_mode
from .pet_renderer import render_configured_pet
from .prompt_finalizer import finalize_prompt
from .service import RouterService
from .terminal_protocol import detect_terminal_capabilities

app = FastAPI(title="Lwa MCP Dashboard", version="0.4.1")
service: RouterService | None = None
codex_broker = CodexSessionBroker(max_sessions=8)
static_dir = files("lwa_mcp").joinpath("static")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def get_service() -> RouterService:
    """Construct the router only when an API operation actually needs it."""
    global service
    if service is None:
        service = RouterService()
    return service


class ConsentUpdate(BaseModel):
    mode: ConsentMode

    @field_validator("mode", mode="before")
    @classmethod
    def _parse_mode(cls, value):
        return parse_consent_mode(value)


class CredentialUpdate(BaseModel):
    value: SecretStr | None = None
    confirm: bool = False


@app.on_event("startup")
async def startup() -> None:
    # Static pages and the Codex workspace must not wait on catalog warming.
    # The first router-backed API call performs the existing local-only setup.
    return None


@app.get("/")
def index():
    return FileResponse(str(static_dir.joinpath("index.html")))


@app.get("/codex")
def codex_workspace():
    """Serve the additive graphical Codex workspace."""
    return FileResponse(str(static_dir.joinpath("codex.html")))


@app.websocket("/ws/codex")
async def codex_socket(websocket: WebSocket):
    """Attach one browser workspace to a bounded local Codex PTY session."""
    await websocket.accept()

    async def emit(event: dict[str, object]) -> None:
        try:
            await websocket.send_text(json.dumps(event, separators=(",", ":")))
        except RuntimeError:
            pass

    session_id = websocket.query_params.get("session_id")
    client_id = None
    try:
        if session_id is None:
            cwd = websocket.query_params.get("cwd")
            if cwd:
                try:
                    session_id, _ = await codex_broker.create(cwd=cwd, graphics_surface="web")
                except TypeError as exc:
                    if "graphics_surface" not in str(exc):
                        raise
                    session_id, _ = await codex_broker.create(cwd=cwd)
            else:
                try:
                    session_id, _ = await codex_broker.create(graphics_surface="web")
                except TypeError as exc:
                    if "graphics_surface" not in str(exc):
                        raise
                    session_id, _ = await codex_broker.create()
        client_id = await codex_broker.attach(session_id, emit)
        pet = render_configured_pet(renderer="browser", low_resource=True)
        if pet is not None:
            await emit({"type": "pet", **pet.public_json()})
        while True:
            message = json.loads(await websocket.receive_text())
            kind = message.get("type")
            if kind == "pet":
                pet = render_configured_pet(
                    override=str(message.get("name", "")) or None,
                    renderer="browser",
                    low_resource=bool(message.get("low_resource", True)),
                )
                if pet is None:
                    await emit({"type": "pet", "state": "fallback", "message": "Configured LWA pet is unavailable."})
                else:
                    await emit({"type": "pet", **pet.public_json()})
            elif kind in {"input", "prompt"}:
                text = str(message.get("text", ""))
                if kind == "prompt":
                    finalized = finalize_prompt(text, mode=str(message.get("mode", "semantic")))
                    text = finalized.text
                    await emit({"type": "finalization", **finalized.public_json()})
                    await emit(
                        {
                            "type": "lwa",
                            "message": (
                                f"LWA prompt finalized ({finalized.status}); "
                                f"{finalized.input_chars} → {finalized.output_chars} chars."
                            ),
                        }
                    )
                    if text and not text.endswith("\n"):
                        text += "\n"
                await codex_broker.write(session_id, client_id, text)
            elif kind == "resize":
                await codex_broker.resize(
                    session_id,
                    client_id,
                    int(message.get("columns", 80)),
                    int(message.get("rows", 24)),
                )
            elif kind == "close":
                break
    except (WebSocketDisconnect, ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        if not isinstance(exc, WebSocketDisconnect):
            await emit({"type": "status", "state": "error", "message": str(exc)})
    finally:
        if session_id is not None and client_id is not None:
            await codex_broker.detach(session_id, client_id)
        elif session_id is not None:
            await codex_broker.discard(session_id)


@app.get("/api/codex/sessions")
def codex_sessions():
    """Return non-sensitive metadata for active local Codex sessions."""
    return codex_broker.status()


@app.get("/api/codex/capabilities")
def codex_capabilities():
    """Return honest host terminal capability metadata without secrets."""
    return detect_terminal_capabilities().public_json()


@app.get("/api/status")
def status():
    return get_service().status()


@app.get("/api/catalog")
def catalog():
    return get_service().catalog_json()


@app.get("/api/model-tiers")
def model_tiers():
    return get_service().model_tiers()


@app.get("/api/providers")
def providers():
    return get_service().providers_json()


@app.get("/api/credentials")
def credentials():
    svc = get_service()
    return managed_credentials(svc.config.env_path)


@app.put("/api/credentials/{env_name}")
def replace_credential(env_name: str, update: CredentialUpdate):
    if not update.confirm:
        raise HTTPException(status_code=400, detail="Credential changes require confirmation.")
    try:
        value = update.value.get_secret_value() if update.value is not None else None
        svc = get_service()
        return {"status": "updated", "credential": update_managed_credential(env_name, value, svc.config.env_path)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/credentials/{env_name}")
def delete_credential(env_name: str, update: CredentialUpdate):
    if not update.confirm:
        raise HTTPException(status_code=400, detail="Credential deletion requires confirmation.")
    try:
        svc = get_service()
        return {"status": "deleted", "credential": update_managed_credential(env_name, None, svc.config.env_path)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/library")
def library():
    return get_service().list_library_tools()


@app.get("/api/patterns")
def patterns():
    return get_service().db.list_workflow_patterns(100)


@app.post("/api/catalog/refresh")
async def refresh():
    return await get_service().catalog.refresh(force=True)


@app.post("/api/quotas/refresh")
async def refresh_quotas():
    return await get_service().refresh_provider_quotas()


@app.post("/api/library/analyze")
def analyze_patterns():
    return get_service().analyze_workflow_patterns(100)


@app.post("/api/library/catalog")
def rebuild_library_catalog():
    return {"catalog": str(get_service().library.rebuild_catalog())}


@app.post("/api/consent")
def set_consent(update: ConsentUpdate):
    return {"mode": get_service().set_consent_mode(update.mode)}


def main() -> None:
    import uvicorn

    cfg = load_config().settings
    uvicorn.run(app, host=cfg.dashboard_host, port=cfg.dashboard_port)


if __name__ == "__main__":
    main()
