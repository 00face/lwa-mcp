from __future__ import annotations

import pytest

from lwa_mcp.models import CompletionResult
from lwa_mcp.prompt_finalizer import finalize_prompt
from lwa_mcp.service import RouterService
from tests.test_preflight import disable_refresh, make_config

WORKFLOW_CASES = (
    (
        "coding",
        (
            "Build a Pac-Man clone with Three.js. Include keyboard controls, collision rules, scoring, "
            "responsive rendering, and a local run command."
        ),
        ("Pac-Man", "Three.js", "collision", "scoring"),
    ),
    (
        "media",
        (
            "Generate a 16:9 media asset of a neon arcade cabinet. Preserve the palette, exclude logos, "
            "and return the requested format."
        ),
        ("16:9", "neon arcade cabinet", "exclude logos"),
    ),
    (
        "research",
        (
            "Research the current browser support for WebGPU. Cite primary sources, include dates, "
            "separate facts from inference, and identify unresolved risks."
        ),
        ("WebGPU", "primary sources", "unresolved risks"),
    ),
)


@pytest.mark.parametrize("kind,prompt,anchors", WORKFLOW_CASES)
def test_workflow_prompt_compaction_preserves_binding_requirements(kind, prompt, anchors):
    finalized = finalize_prompt(prompt, mode="compact")

    assert finalized.status == "deterministic_compact"
    assert all(anchor in finalized.text for anchor in anchors), kind
    assert "\n\n\n" not in finalized.text


@pytest.mark.asyncio
@pytest.mark.parametrize("kind,prompt,_anchors", WORKFLOW_CASES)
async def test_workflow_prompt_can_complete_lwa_consensus(kind, prompt, _anchors, tmp_path, monkeypatch):
    service = RouterService(make_config(tmp_path))
    await disable_refresh(service, monkeypatch)

    class WorkflowAdapter:
        async def complete(self, candidate, request):
            return CompletionResult(
                provider=candidate.provider,
                model=candidate.model,
                text=f"LWA review for {kind}: {request.prompt[:240]}",
                input_tokens=0,
                output_tokens=0,
            )

    monkeypatch.setattr("lwa_mcp.service.build_adapter", lambda _config: WorkflowAdapter())
    prepared = await service.prepare_consensus(finalize_prompt(prompt, mode="compact").text)
    result = await service.run_prepared_task(prepared["preflight"]["plan_token"])

    assert result["status"] == "completed"
    assert result["reviews"]
    assert result["synthesis"]["text"].startswith("LWA review")
