from lwa_mcp.proof_telemetry import partition_proof_telemetry


def record(session_id="s1", usage_status="reported"):
    return {
        "id": 1,
        "created_at": "2026-08-08T00:00:00Z",
        "task": "query",
        "provider": "zai",
        "model": "model",
        "billing_class": "free_quota",
        "input_tokens": 2,
        "output_tokens": 3,
        "latency_ms": 4,
        "status": "ok",
        "prompt_hash": "hash",
        "session_id": session_id,
        "call_id": "c1",
        "parent_call_id": "c1",
        "tool_name": "run_prepared_task",
        "phase": "provider_execution",
        "cache_hit": 0,
        "redundant_call": 0,
        "usage_status": usage_status,
    }


def test_clean_session_is_proof_eligible():
    result = partition_proof_telemetry(
        {"schema_version": 1, "redacted": True, "records": [record()]}, session_id="s1"
    )

    assert result["proof_valid"] is True
    assert result["eligible_records"] == 1
    assert result["quarantined_records"] == 0


def test_invalid_history_is_quarantined_and_retained():
    result = partition_proof_telemetry(
        {"schema_version": 1, "redacted": True, "records": [record(usage_status="not_reported")]}
    )

    assert result["proof_valid"] is False
    assert result["eligible_records"] == 0
    assert result["quarantined_records"] == 1
    assert result["historical_invalid_records_retained"] is True
    assert any("usage_status" in reason for reason in result["reasons"])


def test_session_scope_mismatch_blocks_proof():
    result = partition_proof_telemetry(
        {"schema_version": 1, "redacted": True, "records": [record()]}, session_id="other"
    )

    assert result["proof_valid"] is False
    assert "session_scope_mismatch" in result["reasons"]
