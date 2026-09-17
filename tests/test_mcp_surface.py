import ast
import json
from pathlib import Path

import pytest

SERVER = Path("src/lwa_mcp/server.py")


def _decorated_names(tree: ast.Module, decorator_name: str) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == decorator_name
            ):
                names.add(node.name)
    return names


def test_mcp_exposes_tools_resources_and_prompts():
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))
    resources = _decorated_names(tree, "resource")
    prompts = _decorated_names(tree, "prompt")
    tools = _decorated_names(tree, "tool")

    assert {"status_resource", "catalog_resource", "model_tiers_resource"} <= resources
    assert "preflight_guidance" in prompts
    assert {
        "prepare_task",
        "approve_preflight",
        "run_prepared_task",
        "set_tier_guidance",
        "router_status",
        "pipeline_status",
        "mark_pipeline",
        "invalidate_pipeline_probe_cache",
        "model_tiers",
        "generate_video",
        "syntax_contract_resource",
    } <= tools


def test_legacy_aliases_do_not_execute_provider_work():
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for alias in ("smart_complete", "confirm_and_run"):
        calls = [
            node.func.attr
            for node in ast.walk(functions[alias])
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        ]
        assert "run_prepared_task" not in calls


def test_mcp_starts_stdio_handshake_before_router_warmup(monkeypatch):
    from lwa_mcp import server

    calls = []
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: calls.append(kwargs))

    server.main()

    assert calls == [{"transport": "stdio"}]


def test_response_detail_modes_are_schema_equivalent():
    from lwa_mcp import server

    payload = {"b": 1, "a": ["stable", {"nested": True}]}
    responses = [json.loads(server._json(payload, detail)) for detail in ("compact", "standard", "debug")]

    assert responses == [payload, payload, payload]
    assert len(server._json(payload, "compact")) < len(server._json(payload, "standard"))
    with pytest.raises(ValueError, match="response_detail"):
        server._json(payload, "invalid")
