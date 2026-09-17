def test_promotion_plan_is_idempotent_and_non_mutating():
    from lwa_mcp.github_promotion import promotion_plan
    result = promotion_plan("owner/repo", "a" * 40, "b" * 64, approved=True)
    assert result["ready"] is True
    assert result["direct_push"] is False
    assert result["auto_merge"] is False
    assert result["key"].endswith("a" * 40 + ":" + "b" * 64)
