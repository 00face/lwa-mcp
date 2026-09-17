def test_bootstrap_requires_explicit_signer_and_loads_policy(tmp_path, monkeypatch):
    from lwa_mcp.policy_bootstrap import build_evidence_collector
    policy = tmp_path / "sandbox.yaml"
    policy.write_text("version: 1\nruntime: podman\nimage: registry.test/lwa@sha256:" + "a" * 64 + "\n", encoding="utf-8")
    monkeypatch.setenv("LWA_COSIGN_IDENTITY", "release@example.invalid")
    monkeypatch.setenv("LWA_COSIGN_ISSUER", "https://token.actions.githubusercontent.com")
    collector = build_evidence_collector(policy, lambda: {})
    assert callable(collector)

def test_bootstrap_default_probe_uses_pinned_policy(tmp_path, monkeypatch):
    from lwa_mcp.policy_bootstrap import build_evidence_collector
    policy = tmp_path / "sandbox.yaml"
    image = "registry.test/lwa@sha256:" + "a" * 64
    policy.write_text("version: 1\nruntime: podman\nimage: " + image + "\n", encoding="utf-8")
    monkeypatch.setenv("LWA_COSIGN_IDENTITY", "release@example.invalid")
    monkeypatch.setenv("LWA_COSIGN_ISSUER", "https://token.actions.githubusercontent.com")
    with monkeypatch.context() as context:
        context.setattr("lwa_mcp.policy_bootstrap.probe_sandbox", lambda path, **kwargs: {"verified": True})
        assert callable(build_evidence_collector(policy))
