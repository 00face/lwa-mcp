from lwa_mcp.codex_app_server import normalize_rate_limits


def test_codex_rate_limit_snapshot_normalizes_quota_and_reset():
    result = normalize_rate_limits({
        "planType": "plus",
        "rateLimitReachedType": None,
        "primary": {"usedPercent": 63, "resetsAt": 1730947200},
    })
    assert result["provider"] == "codex"
    assert result["quota_exhausted"] is False
    assert result["reset_at"] == 1730947200


def test_codex_rate_limit_snapshot_marks_reached_limit():
    result = normalize_rate_limits({
        "rateLimitReachedType": "workspace_member_usage_limit_reached",
        "primary": {"usedPercent": 100},
    })
    assert result["quota_exhausted"] is True
