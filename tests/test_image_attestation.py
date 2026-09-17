from unittest.mock import patch

def test_attestation_fails_closed_when_tools_are_missing():
    from lwa_mcp.image_attestation import verify_image_attestation
    with patch("lwa_mcp.image_attestation.shutil.which", return_value=None):
        result = verify_image_attestation("docker.io/library/alpine@sha256:" + "a" * 64)
    assert result["verified"] is False
    assert "cosign_unavailable" in result["blockers"]
    assert "sbom_tool_unavailable" in result["blockers"]
    assert "vulnerability_scanner_unavailable" in result["blockers"]

def test_grype_json_enforces_thresholds_and_eol():
    from lwa_mcp.image_attestation import evaluate_grype_json
    payload = '{"distro":{"name":"Alpine","eol":true},"matches":[{"vulnerability":{"severity":"Critical"}}]}'
    result = evaluate_grype_json(payload)
    assert result["verified"] is False
    assert "eol_distribution" in result["blockers"]
    assert "critical_threshold_exceeded" in result["blockers"]

def test_grype_json_rejects_malformed_output():
    from lwa_mcp.image_attestation import evaluate_grype_json
    assert evaluate_grype_json("not-json")["verified"] is False

def test_attestation_requires_digest():
    from lwa_mcp.image_attestation import verify_image_attestation
    result = verify_image_attestation("docker.io/library/alpine:3.20", cosign_path="cosign", sbom_path="syft")
    assert result["verified"] is False
    assert "image_not_digest_pinned" in result["blockers"]

def test_attestation_accepts_successful_tools():
    from lwa_mcp.image_attestation import verify_image_attestation
    class Completed:
        returncode = 0
        stdout = '{"distro":{"name":"Minimus","eol":false},"matches":[]}'
    with patch("lwa_mcp.image_attestation.subprocess.run", return_value=Completed()):
        result = verify_image_attestation("docker.io/library/alpine@sha256:" + "a" * 64, cosign_path="cosign", sbom_path="syft", grype_path="grype", expected_identity="alpine@official.invalid", oidc_issuer="https://token.actions.githubusercontent.com")
    assert result["verified"] is True
