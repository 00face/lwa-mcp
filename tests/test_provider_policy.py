from datetime import UTC, datetime, timedelta

from lwa_mcp.provider_policy import (
    Availability,
    ProviderRoutingPolicy,
    ProviderState,
    RoutingMode,
    classify_provider_failure,
)


def test_named_modes_define_the_requested_provider_order():
    policy = ProviderRoutingPolicy(
        routes={
            "codex_first": ["codex", "openrouter", "anthropic", "gemini"],
            "third_party_first": ["openrouter", "anthropic", "gemini", "codex"],
        },
        mode=RoutingMode.THIRD_PARTY_FIRST,
    )

    assert policy.provider_order() == ["openrouter", "anthropic", "gemini", "codex"]
    assert policy.with_mode("codex-first").provider_order()[0] == "codex"


def test_only_quota_exhaustion_advances_the_provider_chain():
    policy = ProviderRoutingPolicy(mode=RoutingMode.THIRD_PARTY_FIRST)

    assert policy.fallback_allowed(ProviderState("openrouter", Availability.QUOTA_EXHAUSTED))
    assert not policy.fallback_allowed(ProviderState("openrouter", Availability.AUTHENTICATION_FAILURE))
    assert not policy.fallback_allowed(ProviderState("openrouter", Availability.SECURITY_DENIED))
    assert not policy.fallback_allowed(ProviderState("openrouter", Availability.TEMPORARY_RATE_LIMIT))


def test_failure_normalization_keeps_rate_limits_and_auth_failures_out_of_fallback():
    assert classify_provider_failure(status_code=429) is Availability.TEMPORARY_RATE_LIMIT
    assert classify_provider_failure(status_code=402) is Availability.QUOTA_EXHAUSTED
    assert classify_provider_failure(status_code=429, rate_limit_reached_type="monthly_quota") is Availability.QUOTA_EXHAUSTED
    assert classify_provider_failure(
        status_code=429, rate_limit_reached_type="workspace_member_usage_limit_reached"
    ) is Availability.QUOTA_EXHAUSTED
    assert classify_provider_failure(status_code=401) is Availability.AUTHENTICATION_FAILURE
    assert classify_provider_failure(security_denied=True) is Availability.SECURITY_DENIED


def test_sticky_provider_survives_until_reset_or_manual_switch():
    reset = datetime.now(UTC) + timedelta(minutes=5)
    policy = ProviderRoutingPolicy(mode=RoutingMode.THIRD_PARTY_FIRST)
    policy.stick("codex", reset_at=reset)

    assert policy.provider_order()[0] == "codex"
    assert policy.provider_order(now=reset + timedelta(seconds=1))[0] == "openrouter"

    policy.stick("gemini")
    policy.clear_sticky()
    assert policy.provider_order()[0] == "openrouter"


def test_stickiness_is_scoped_to_a_session():
    policy = ProviderRoutingPolicy(mode=RoutingMode.THIRD_PARTY_FIRST)
    policy.stick("codex", session_id="session-a")

    assert policy.provider_order(session_id="session-a") == ["codex"]
    assert policy.provider_order(session_id="session-b")[0] == "openrouter"
    policy.clear_sticky("session-a")
    assert policy.provider_order(session_id="session-a")[0] == "openrouter"
