from __future__ import annotations

import json
import os
import sys
from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP

from .models import Capability, TaskKind, parse_consent_mode
from .syntax import parse_task_kind, syntax_contract

if TYPE_CHECKING:
    from .service import RouterService

mcp = FastMCP("Lwa MCP")
service: RouterService | None = None

RESPONSE_DETAILS = {"compact", "standard", "debug"}


def _json(payload: object, detail: str | None = None) -> str:
    mode = (detail or os.getenv("LWA_MCP_RESPONSE_DETAIL", "compact")).lower()
    if mode not in RESPONSE_DETAILS:
        raise ValueError(f"response_detail must be one of {sorted(RESPONSE_DETAILS)}")
    if mode == "compact":
        return json.dumps(payload, separators=(",", ":"))
    return json.dumps(payload, indent=2)


def get_service() -> RouterService:
    global service
    if service is None:
        from .service import RouterService

        service = RouterService()
    return service


@mcp.resource("lwa://status")
def status_resource() -> str:
    """Read-only operational status without credentials or raw prompts."""
    return _json(get_service().status())


@mcp.resource("lwa://catalog")
def catalog_resource() -> str:
    """Read-only provider/model catalog with fallback/live source metadata."""
    return _json(get_service().catalog_json())


@mcp.resource("lwa://model-tiers")
def model_tiers_resource() -> str:
    """Configured model tiers ranked by declared free-plan token capacity."""
    return _json(get_service().model_tiers())


@mcp.prompt()
def preflight_guidance(task: str, objective: str, allow_paid: bool = False) -> str:
    """Provide a concise host-side checklist for strict Lwa task execution."""
    spending = "paid routes are allowed only when justified" if allow_paid else "keep paid routes disabled"
    return (
        f"Prepare a Lwa MCP task of type '{task}' for this objective:\n{objective}\n\n"
        "Before Working, call prepare_task, inspect the locked provider/model, token budget, "
        f"consent, and routes, and {spending}. If approval is required, call approve_preflight; "
        "only then call run_prepared_task. If execution fails, stop and repreflight."
    )


@mcp.tool()
async def route_task(
    task: str,
    prompt: str,
    quality: str = "balanced",
    reasoning_effort: str | None = None,
    allow_paid: bool = False,
    allow_user_pays: bool = False,
    max_output_tokens: int = 1200,
    preferred_providers: list[str] | None = None,
    excluded_providers: list[str] | None = None,
    response_detail: str | None = None,
) -> str:
    """Prepare and lock the selected provider/model before Working may begin."""
    svc = get_service()
    request = svc.build_request(
        parse_task_kind(task),
        prompt,
        quality=quality,
        reasoning_effort=reasoning_effort,
        allow_paid=allow_paid,
        allow_user_pays=allow_user_pays,
        max_output_tokens=max_output_tokens,
        preferred_providers=preferred_providers,
        excluded_providers=excluded_providers,
        tool_name="route_task",
    )
    return _json(await svc.prepare_task(request), response_detail)


@mcp.tool()
async def prepare_task(
    task: str,
    prompt: str,
    quality: str = "balanced",
    reasoning_effort: str | None = None,
    allow_paid: bool = False,
    allow_user_pays: bool = False,
    max_output_tokens: int = 1200,
    preferred_providers: list[str] | None = None,
    excluded_providers: list[str] | None = None,
    response_detail: str | None = None,
) -> str:
    """Complete silent preflight. Do not show Working until working_may_begin is true."""
    svc = get_service()
    request = svc.build_request(
        parse_task_kind(task),
        prompt,
        quality=quality,
        reasoning_effort=reasoning_effort,
        allow_paid=allow_paid,
        allow_user_pays=allow_user_pays,
        max_output_tokens=max_output_tokens,
        preferred_providers=preferred_providers,
        excluded_providers=excluded_providers,
        tool_name="prepare_task",
    )
    return _json(await svc.prepare_task(request), response_detail)


@mcp.tool()
def approve_preflight(confirmation_token: str, response_detail: str | None = None) -> str:
    """Approve a locked preflight. This does not begin provider work."""
    return _json(get_service().approve_preflight(confirmation_token), response_detail)


@mcp.tool()
async def run_prepared_task(
    plan_token: str,
    response_detail: str | None = None,
    next_tier_suggestion: str | None = None,
) -> str:
    """Begin provider work for one approved plan. Never routes or switches models."""
    return _json(
        await get_service().run_prepared_task(plan_token, next_tier_suggestion),
        response_detail,
    )


@mcp.tool()
def set_tier_guidance(enabled: bool = True, mode: str = "local") -> str:
    """Enable compact post-response tier guidance: local or codex_request."""
    return _json(get_service().set_tier_guidance(enabled, mode))


@mcp.tool()
async def smart_complete(
    task: str,
    prompt: str,
    quality: str = "balanced",
    reasoning_effort: str | None = None,
    allow_paid: bool = False,
    allow_user_pays: bool = False,
    max_output_tokens: int = 1200,
    preferred_providers: list[str] | None = None,
    excluded_providers: list[str] | None = None,
    workflow_name: str | None = None,
    workflow_description: str | None = None,
    project: str | None = None,
    workflow_tags: list[str] | None = None,
    response_detail: str | None = None,
) -> str:
    """Prepare a locked task. Despite the legacy name, this never begins provider work."""
    svc = get_service()
    request = svc.build_request(
        parse_task_kind(task),
        prompt,
        quality=quality,
        reasoning_effort=reasoning_effort,
        allow_paid=allow_paid,
        allow_user_pays=allow_user_pays,
        max_output_tokens=max_output_tokens,
        preferred_providers=preferred_providers,
        excluded_providers=excluded_providers,
        tool_name="smart_complete",
        metadata={
            "workflow_name": workflow_name,
            "workflow_description": workflow_description,
            "project": project,
            "workflow_tags": workflow_tags or [],
        },
    )
    return _json(await svc.prepare_task(request), response_detail)


@mcp.tool()
def confirm_and_run(confirmation_token: str) -> str:
    """Deprecated compatibility alias: approve preflight only, then call run_prepared_task."""
    return _json(get_service().approve_preflight(confirmation_token))


@mcp.tool()
async def quick_response(prompt: str, quality: str = "economy", reasoning_effort: str | None = None) -> str:
    """Prepare a low-latency auxiliary response; execution requires run_prepared_task."""
    svc = get_service()
    request = svc.build_request(TaskKind.QUICK_RESPONSE, prompt, quality=quality, reasoning_effort=reasoning_effort, max_output_tokens=700, tool_name="quick_response")
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def answer_query(prompt: str, quality: str = "balanced", reasoning_effort: str | None = None) -> str:
    """Prepare a routed query; execution requires run_prepared_task."""
    svc = get_service()
    request = svc.build_request(TaskKind.QUERY, prompt, quality=quality, reasoning_effort=reasoning_effort, max_output_tokens=1400, tool_name="answer_query")
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def verify_work(material: str, quality: str = "balanced", reasoning_effort: str | None = None) -> str:
    """Prepare a verification route; execution requires run_prepared_task."""
    svc = get_service()
    request = svc.build_request(TaskKind.VERIFICATION, material, quality=quality, reasoning_effort=reasoning_effort, max_output_tokens=1800, tool_name="verify_work")
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    output_format: str = "png",
    quality: str = "balanced",
    allow_paid: bool = False,
) -> str:
    """Prepare and lock an image-generation route before execution."""
    svc = get_service()
    request = svc.build_request(
        TaskKind.IMAGE_GENERATION,
        prompt,
        quality=quality,
        allow_paid=allow_paid,
        max_output_tokens=1,
        required_capabilities={Capability.IMAGE},
        metadata={"aspect_ratio": aspect_ratio, "output_format": output_format},
        tool_name="generate_image",
    )
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def generate_video(
    prompt: str,
    seconds: str = "4",
    size: str = "1280x720",
    quality: str = "balanced",
    allow_paid: bool = False,
) -> str:
    """Prepare and lock an official video-generation route before execution."""
    svc = get_service()
    request = svc.build_request(
        TaskKind.VIDEO_GENERATION,
        prompt,
        quality=quality,
        allow_paid=allow_paid,
        max_output_tokens=1,
        required_capabilities={Capability.VIDEO},
        metadata={"seconds": seconds, "size": size},
        tool_name="generate_video",
    )
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def compress_conversation(conversation: str, quality: str = "economy", reasoning_effort: str | None = None) -> str:
    """Prepare conversation compression while preserving required context."""
    svc = get_service()
    request = svc.build_request(TaskKind.CONVERSATION_COMPRESSION, conversation, quality=quality, reasoning_effort=reasoning_effort, tool_name="compress_conversation")
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def optimize_prompt(prompt: str, quality: str = "economy", reasoning_effort: str | None = None) -> str:
    """Prepare token optimization while preserving binding requirements and literals."""
    svc = get_service()
    request = svc.build_request(TaskKind.TOKEN_OPTIMIZATION, prompt, quality=quality, reasoning_effort=reasoning_effort, tool_name="optimize_prompt")
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def edit_document(document: str, instructions: str, quality: str = "balanced", reasoning_effort: str | None = None) -> str:
    """Prepare conservative document editing; execution requires run_prepared_task."""
    svc = get_service()
    prompt = f"EDITING INSTRUCTIONS:\n{instructions}\n\nDOCUMENT:\n{document}"
    request = svc.build_request(TaskKind.DOCUMENT_EDITING, prompt, quality=quality, reasoning_effort=reasoning_effort, max_output_tokens=5000, tool_name="edit_document")
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def write_sitrep(project_material: str, quality: str = "balanced", reasoning_effort: str | None = None) -> str:
    """Prepare an evidence-bound SITREP route before Working begins."""
    svc = get_service()
    request = svc.build_request(TaskKind.SITREP, project_material, quality=quality, reasoning_effort=reasoning_effort, max_output_tokens=2400, tool_name="write_sitrep")
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def plan_work(objective: str, quality: str = "balanced", reasoning_effort: str | None = None) -> str:
    """Prepare project planning with its prompt, budget, and model locked."""
    svc = get_service()
    request = svc.build_request(TaskKind.PLANNING, objective, quality=quality, reasoning_effort=reasoning_effort, max_output_tokens=2600, tool_name="plan_work")
    return _json(await svc.prepare_task(request))


@mcp.tool()
async def build_consensus(
    question: str,
    voters: int = 3,
    quality: str = "balanced",
    reasoning_effort: str | None = None,
    allow_paid: bool = False,
    excluded_providers: list[str] | None = None,
) -> str:
    """Prepare all eligible free-model voters and a synthesis route before Working."""
    return _json(
        await get_service().prepare_consensus(
            question, voters, quality, allow_paid, excluded_providers, reasoning_effort
        ),
    )


@mcp.tool()
def set_switch_confirmation(mode: str) -> str:
    """Set model-switch prompting: always_ask, paid_only, or automatic."""
    value = get_service().set_consent_mode(parse_consent_mode(mode))
    return _json({"consent_mode": value})


@mcp.tool()
async def refresh_model_catalog(force: bool = True) -> str:
    """Refresh live model catalogs and provider health without exposing API keys."""
    result = await get_service().catalog.refresh(force=force)
    return _json(result)


@mcp.tool()
async def refresh_provider_quotas() -> str:
    """Fetch official remote balance/quota data for providers with configured management endpoints."""
    return _json(await get_service().refresh_provider_quotas())


@mcp.tool()
def router_status() -> str:
    """Return local usage, latest quota headers, provider health, and consent mode."""
    return _json(get_service().status())


@mcp.tool()
async def pipeline_status(provider: str = "", probe: bool = False) -> str:
    """Check pipeline readiness without sending a user prompt.

    The default check is local-only. ``probe=True`` permits only a provider
    health/model-metadata request and never sends task data.
    """
    return _json(await get_service().pipeline_status(provider or None, probe=probe))


@mcp.tool()
def mark_pipeline(provider: str, status: str, detail: str = "") -> str:
    """Record an operator pipeline mark: ready, degraded, blocked, or maintenance."""
    return _json(get_service().mark_pipeline(provider, status, detail))


@mcp.tool()
def invalidate_pipeline_probe_cache(provider: str = "") -> str:
    """Invalidate cached zero-payload pipeline probes without provider I/O."""
    count = get_service().invalidate_pipeline_probe_cache(provider or None)
    return _json({"invalidated": count})


@mcp.tool()
def model_tiers(limit: int = 100) -> str:
    """List model tiers sorted by maximum declared free-plan token usage."""
    return _json(get_service().model_tiers(limit))


@mcp.tool()
def syntax_contract_resource() -> str:
    """Return canonical task, quality, and prompt-variable syntax."""
    return _json(syntax_contract())


@mcp.tool()
def list_library_tools(status: str = "") -> str:
    """List persistent reusable tools. Status may be active, draft, disabled, or archived."""
    return _json(get_service().list_library_tools(status or None))


@mcp.tool()
def search_tool_library(query: str, task: str = "", limit: int = 10) -> str:
    """Search reusable cross-project tools by task, words, tags, and trigger descriptions."""
    parsed_task = parse_task_kind(task) if task else None
    return _json(
        get_service().library.search(query, task=parsed_task, limit=limit, active_only=False),
    )


@mcp.tool()
def suggest_library_tools(context: str, task: str = "", limit: int = 5) -> str:
    """Find active library tools that are pragmatic and relevant to the current work."""
    parsed_task = parse_task_kind(task) if task else None
    return _json(
        get_service().suggest_library_tools(context, task=parsed_task, limit=limit)
    )


@mcp.tool()
def read_library_tool(slug: str) -> str:
    """Read a reusable tool's manifest, README, path, origin, evidence, and usage instructions."""
    return _json(get_service().read_library_tool(slug))


@mcp.tool()
async def run_library_tool(
    slug: str,
    input_text: str,
    quality: str = "balanced",
    reasoning_effort: str | None = None,
    allow_paid: bool = False,
    allow_user_pays: bool = False,
) -> str:
    """Prepare an active prompt recipe; approved script tools remain separately executable."""
    result = await get_service().run_library_tool(
        slug,
        input_text,
        quality=quality,
        reasoning_effort=reasoning_effort,
        allow_paid=allow_paid,
        allow_user_pays=allow_user_pays,
    )
    return _json(result)


@mcp.tool()
def create_library_tool(
    name: str,
    description: str,
    task: str,
    prompt_template: str,
    tags: list[str] | None = None,
    triggers: list[str] | None = None,
    activate: bool = True,
) -> str:
    """Create a documented reusable prompt tool with a manifest, README, and launcher script."""
    result = get_service().create_library_tool(
        name=name,
        description=description,
        task=parse_task_kind(task),
        prompt_template=prompt_template,
        tags=tags,
        triggers=triggers,
        activate=activate,
    )
    return _json(result)


@mcp.tool()
def register_script_tool(
    name: str,
    description: str,
    task: str,
    source: str,
    filename: str = "tool.py",
    tags: list[str] | None = None,
    triggers: list[str] | None = None,
) -> str:
    """Catalog a script as a draft tool. It cannot execute until separately reviewed and enabled."""
    result = get_service().register_script_tool(
        name=name,
        description=description,
        task=parse_task_kind(task),
        source=source,
        filename=filename,
        tags=tags,
        triggers=triggers,
    )
    return _json(result)


@mcp.tool()
def approve_library_tool(slug: str) -> str:
    """Mark a reviewed tool active and approved. Script execution still obeys global configuration."""
    return _json(get_service().set_library_tool_status(slug, "active", approved=True))


@mcp.tool()
def disable_library_tool(slug: str) -> str:
    """Disable a reusable tool without deleting its evidence, README, or version history."""
    return _json(get_service().set_library_tool_status(slug, "disabled"))


@mcp.tool()
def observe_workflow(
    workflow_name: str,
    description: str,
    task: str,
    sample: str = "",
    project: str = "",
    success: bool = True,
    tags: list[str] | None = None,
) -> str:
    """Record one workflow occurrence; repeated successful patterns may create a library tool."""
    result = get_service().observe_workflow(
        workflow_name=workflow_name,
        description=description,
        task=parse_task_kind(task),
        sample=sample,
        project=project or None,
        success=success,
        tags=tags,
    )
    return _json(result)


@mcp.tool()
def analyze_repeated_workflows(limit: int = 100) -> str:
    """Review the repetition ledger and scaffold any eligible reusable tools not yet created."""
    return _json(get_service().analyze_workflow_patterns(limit))


@mcp.tool()
def rebuild_tool_catalog() -> str:
    """Regenerate the human-readable CATALOG.md for cross-conversation tool discovery."""
    path = get_service().library.rebuild_catalog()
    return _json({"status": "completed", "catalog": str(path)})


@mcp.tool()
def library_status() -> str:
    """Return persistent tool-library paths, counts, and recent detected patterns."""
    svc = get_service()
    return _json(
        {
            "library": svc.library.summary(),
            "patterns": svc.db.list_workflow_patterns(30),
        },
    )


def main() -> None:
    # Begin the stdio handshake immediately. Router/catalog state is local and
    # lazy: the first router-backed request constructs and warms the service.
    print("Lwa MCP stdio transport starting", file=sys.stderr, flush=True)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
