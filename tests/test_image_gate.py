def test_image_gate_requires_all_runtime_controls():
    from lwa_mcp.image_gate import evaluate_image_gate
    image = "registry.test/lwa@sha256:" + "a" * 64
    result = evaluate_image_gate(image=image, attestation={"verified": True, "image": image}, runtime={"image": image, "rootless": True, "network_disabled": True, "read_only": True, "no_new_privs": True})
    assert result["passed"] is True

def test_image_gate_fails_closed_with_missing_control():
    from lwa_mcp.image_gate import evaluate_image_gate
    result = evaluate_image_gate(image="registry.test/lwa:latest", attestation={"verified": False, "blockers": ["signature_failed"]}, runtime={})
    assert result["passed"] is False
    assert "image_not_digest_pinned" in result["blockers"]
    assert "signature_failed" in result["blockers"]

def test_image_gate_rejects_evidence_for_different_digest():
    from lwa_mcp.image_gate import evaluate_image_gate
    image = "registry.test/lwa@sha256:" + "a" * 64
    other = "registry.test/lwa@sha256:" + "b" * 64
    result = evaluate_image_gate(image=image, attestation={"verified": True, "image": other}, runtime={"image": other, "rootless": True, "network_disabled": True, "read_only": True, "no_new_privs": True})
    assert result["passed"] is False
    assert "attestation_digest_mismatch" in result["blockers"]
    assert "runtime_digest_mismatch" in result["blockers"]

def test_image_gate_rejects_hashed_evidence_for_different_digest():
    from lwa_mcp.image_gate import evaluate_image_gate
    image = "registry.test/lwa@sha256:" + "a" * 64
    result = evaluate_image_gate(image=image, attestation={"verified": True, "image": image}, runtime={"image": image, "rootless": True, "network_disabled": True, "read_only": True, "no_new_privs": True}, evidence={"image": "registry.test/lwa@sha256:" + "b" * 64})
    assert result["passed"] is False
    assert "evidence_digest_mismatch" in result["blockers"]
