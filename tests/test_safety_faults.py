from lwa_mcp.safety import default_fault_evidence, validate_fault_evidence


def test_default_fault_evidence_passes_all_rollback_gates():
    result = validate_fault_evidence(default_fault_evidence())

    assert result["valid"] is True
    assert result["scenarios"] == 6
    assert result["provider_calls"] == 1
    assert result["promotion_blocked"] is False


def test_fault_evidence_rejects_reroute_and_unsafe_rollback():
    evidence = default_fault_evidence()
    evidence["provider_failure"]["followup_routes"] = 1
    evidence["rollback"]["response_detail"] = "compact"

    result = validate_fault_evidence(evidence)

    assert result["valid"] is False
    assert "provider_failure:rerouted_after_failure" in result["errors"]
    assert "rollback:unsafe_state" in result["errors"]


def test_fault_evidence_requires_every_scenario():
    evidence = default_fault_evidence()
    del evidence["missing_quota"]

    result = validate_fault_evidence(evidence)

    assert result["valid"] is False
    assert "missing_scenario:missing_quota" in result["errors"]
