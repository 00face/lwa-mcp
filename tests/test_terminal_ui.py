from lwa_mcp.terminal_ui import (
    CodexIdentity,
    render_execution_telemetry,
    render_preflight,
    render_result,
    response_display,
)


def payload():
    return {
        "preflight": {
            "task": "token_optimization",
            "working_may_begin": True,
            "estimated_input_tokens": 42,
            "max_output_tokens": 300,
            "routes": [{"decision": {"candidate": {
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "billing_class": "free_quota",
            }}}],
        }
    }


def test_terminal_ui_shows_codex_and_locked_lwa_route():
    output = render_preflight(payload(), CodexIdentity("gpt-5.6-luna", "medium"))
    assert "CODEX  gpt-5.6-luna · reasoning medium" in output
    assert "TOKEN OPTIMIZATION · READY" in output
    assert "groq / openai/gpt-oss-20b · free quota" in output


def test_terminal_ui_explicitly_returns_to_codex():
    result = payload() | {
        "decision": {"candidate": {"provider": "groq", "model": "openai/gpt-oss-20b", "billing_class": "free_quota"}},
        "result": {"provider": "groq", "model": "openai/gpt-oss-20b", "input_tokens": 10, "output_tokens": 20},
    }
    output = render_result(result, CodexIdentity("gpt-5.6-luna", "medium"))
    assert "LWA RESPONSE" in output
    assert "[LWA] COMPLETE · TOKEN OPTIMIZATION" in output
    assert "[CODEX] ACTIVE · gpt-5.6-luna · reasoning medium" in output


def test_response_display_keeps_raw_text_separate_and_names_route():
    result = payload() | {
        "decision": {"candidate": {"provider": "groq", "model": "openai/gpt-oss-20b", "billing_class": "free_quota"}},
        "result": {"provider": "groq", "model": "openai/gpt-oss-20b", "text": "short answer", "input_tokens": 10, "output_tokens": 20},
    }
    display = response_display(result, CodexIdentity("gpt-5.6-luna", "medium"))
    assert display["surface"] == "LWA"
    assert display["model"] == "openai/gpt-oss-20b"
    assert display["billing_class"] == "free_quota"
    assert "short answer" in display["formatted"]


def test_execution_telemetry_explains_optimization_spend_and_handoff():
    result = payload() | {
        "decision": {
            "estimated_max_cost_usd": 0.12,
            "candidate": {
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "billing_class": "free_quota",
            },
        },
        "result": {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "input_tokens": 10,
            "output_tokens": 20,
            "cost_usd": 0.01,
            "latency_ms": 42,
            "rate_limits": {"x-ratelimit-remaining-tokens": "7000"},
        },
    }
    output = render_execution_telemetry(result, CodexIdentity("gpt-5.6-luna", "medium"))
    assert "TOKEN OPTIMIZATION" in output
    assert "reduction measurement unavailable" in output
    assert "actual $0.010000" in output
    assert "estimated ceiling $0.120000" in output
    assert "x-ratelimit-remaining-tokens=7000" in output
    assert "HANDOFF" in output
