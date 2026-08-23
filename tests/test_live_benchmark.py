from lwa_mcp.live_benchmark import expected_fixture_manifest, validate_repeated_runs


def valid_run(*, provider_executions=1):
    return {
        "fixture_manifest": expected_fixture_manifest(),
        "quality_delta_percentage_points": 0.0,
        "telemetry_valid": True,
        "quota_valid": True,
        "duplicate_provider_executions": 0,
        "provider_executions": provider_executions,
        "billing_classes": ["free_quota"],
        "telemetry_records": [
            {
                "usage_status": "reported",
                "session_id": "session-1",
                "call_id": "call-1",
                "parent_call_id": "call-1",
                "tool_name": "run_prepared_task",
                "phase": "provider_execution",
            }
        ],
        "metrics": {
            "input_tokens": 100,
            "output_tokens": 50,
            "tool_calls": 2,
            "retries": 0,
            "cache_hits": 1,
            "p50_latency_ms": 20,
            "p95_latency_ms": 40,
        },
    }


def test_two_valid_live_runs_pass():
    result = validate_repeated_runs({"runs": [valid_run(), valid_run()]})

    assert result == {
        "valid": True,
        "mode": "live_required",
        "runs": 2,
        "cases": 7,
        "errors": [],
        "promotion_blocked": False,
    }


def test_offline_fixture_is_not_live_proof():
    result = validate_repeated_runs(
        {"runs": [valid_run(provider_executions=0), valid_run(provider_executions=0)]}
    )

    assert result["valid"] is False
    assert "run_0_not_live" in result["errors"]
    assert "run_1_not_live" in result["errors"]
    assert result["promotion_blocked"] is True


def test_quality_and_telemetry_failures_block_promotion():
    run = valid_run()
    run["quality_delta_percentage_points"] = 1.1
    run["telemetry_records"][0]["usage_status"] = "not_reported"
    result = validate_repeated_runs({"runs": [run, valid_run()]})

    assert result["valid"] is False
    assert "run_0_quality_regression" in result["errors"]
    assert "run_0_record_0_usage_not_reported" in result["errors"]
