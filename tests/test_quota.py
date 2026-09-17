from datetime import UTC, datetime, timedelta

from lwa_mcp.quota import reconcile_quota

NOW = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


def snapshot(**overrides):
    value = {
        "provider": "mock-provider",
        "account_scope": "test-account",
        "available_tokens": 1_000_000,
        "unit": "tokens",
        "captured_at": "2026-08-08T11:30:00Z",
        "reset_at": "2026-08-09T00:00:00Z",
        "source": "provider_header",
        "authoritative": True,
    }
    value.update(overrides)
    return value


def test_authoritative_snapshot_reconciles_reproducibly():
    result = reconcile_quota(snapshot(), 186, now=NOW)

    assert result["valid"] is True
    assert result["overhead_percent"] == 0.0186
    assert result["under_0_1_percent"] is True
    assert result["denominator_definition"]


def test_missing_or_nominal_quota_fails_closed():
    for value in (
        snapshot(authoritative=False),
        snapshot(source="nominal"),
        snapshot(unit="requests"),
        snapshot(available_tokens=0),
        snapshot(captured_at="2026-08-08T08:00:00Z"),
    ):
        result = reconcile_quota(value, 186, now=NOW, max_age_seconds=3600)
        assert result["valid"] is False
        assert result["under_0_1_percent"] is False


def test_expired_reset_and_stale_snapshot_fail_closed():
    result = reconcile_quota(
        snapshot(
            captured_at=(NOW - timedelta(hours=2)).isoformat(),
            reset_at=(NOW - timedelta(minutes=1)).isoformat(),
        ),
        1,
        now=NOW,
    )

    assert result["valid"] is False
    assert "quota_snapshot_stale" in result["errors"]
    assert "quota_reset_window_expired" in result["errors"]
