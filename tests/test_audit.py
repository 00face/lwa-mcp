from lwa_mcp.audit import audit_near_zero_proof


def bundle(**overrides):
    value = {
        "telemetry": {"valid": True},
        "quota": {"valid": True},
        "benchmark": {"valid": True},
        "handshake": {"status": "passed"},
        "safety": {"valid": True},
        "predictive_reuse": True,
        "stale_result_safeguards": True,
        "independent_reproduction": True,
    }
    value.update(overrides)
    return value


def test_complete_bundle_passes_ten_and_eleven_gates():
    result = audit_near_zero_proof(bundle())

    assert result["ten_of_ten"] is True
    assert result["eleven_of_ten"] is True
    assert result["blockers"] == []


def test_current_style_telemetry_blocks_ten_of_ten():
    result = audit_near_zero_proof(bundle(telemetry={"valid": False}))

    assert result["ten_of_ten"] is False
    assert result["eleven_of_ten"] is False
    assert "telemetry_gate_failed" in result["blockers"]


def test_missing_stretch_evidence_does_not_block_ten_if_mandatory_gates_pass():
    result = audit_near_zero_proof(
        bundle(predictive_reuse=False, stale_result_safeguards=False, independent_reproduction=False)
    )

    assert result["ten_of_ten"] is True
    assert result["eleven_of_ten"] is False
    assert "predictive_reuse_unproven" in result["blockers"]
