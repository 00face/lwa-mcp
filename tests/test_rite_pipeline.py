def test_rite_pipeline_skips_without_delta(tmp_path):
    from lwa_mcp.rite_pipeline import run_rite
    from lwa_mcp.rites import Agent, RiteManifest, Trigger, Workspace
    from lwa_mcp.rite_state import RiteState

    rite = RiteManifest("health", Trigger("cron", "0 3 * * *"), Workspace(), Agent("health"), (), (), "report", False)
    state = RiteState(tmp_path / "state.json")
    state.record("same", success=True, metrics={}, findings=[])
    result = run_rite(rite, tmp_path, "same", state)
    assert result["status"] == "skipped"
    assert result["blockers"] == []


def test_rite_pipeline_reports_missing_agent_and_never_auto_promotes(tmp_path):
    from lwa_mcp.rite_pipeline import run_rite
    from lwa_mcp.rites import Agent, RiteManifest, Trigger, Workspace
    from lwa_mcp.rite_state import RiteState

    rite = RiteManifest("health", Trigger("cron", "0 3 * * *"), Workspace(), Agent("health"), (), (), "commit", True)
    result = run_rite(rite, tmp_path, "new", RiteState(tmp_path / "state.json"))
    assert result["status"] == "blocked"
    assert "agent_runner_not_configured" in result["blockers"]
    assert result["promoted"] is False


def test_rite_pipeline_runs_in_worktree_and_verifies_before_promotion(tmp_path):
    from lwa_mcp.constraints import ConstraintKernel
    from lwa_mcp.rite_pipeline import run_rite
    from lwa_mcp.rites import Agent, RiteManifest, Trigger, Workspace
    from lwa_mcp.rite_state import RiteState

    rite = RiteManifest("health", Trigger("event"), Workspace(), Agent("health"), (), (), "commit", False)
    seen = {}

    def runner(worktree, _rite):
        seen["worktree"] = worktree
        return {"changed_paths": ["README.md"], "files": {"README.md": "safe"}, "terminal": {"tests": True, "lint": True}}

    # A real repository is required by the worktree boundary; initialize only
    # this isolated fixture.
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], cwd=tmp_path, check=True)
    result = run_rite(rite, tmp_path, "new", RiteState(tmp_path / "state.json"),
                      agent_runner=runner, kernel=ConstraintKernel({"version": 1, "hard": {}}), approved=True,
                      attestation={"verified": True, "image": "registry.test/lwa@sha256:" + "a" * 64}, image="registry.test/lwa@sha256:" + "a" * 64,
                      runtime_evidence={"image": "registry.test/lwa@sha256:" + "a" * 64, "rootless": True, "network_disabled": True, "read_only": True, "no_new_privs": True},
                      evidence={"image": "registry.test/lwa@sha256:" + "a" * 64, "attestation": {"sha256": "a" * 64}, "sbom": {"sha256": "b" * 64}, "vulnerabilities": {"sha256": "c" * 64}, "runtime": {"sha256": "d" * 64}})
    assert result["status"] in {"ready", "blocked"}
    assert "image_gate" not in result or result["image_gate"]["passed"] is True
    assert result["promoted"] is False
    assert not seen["worktree"].exists()


def test_rite_pipeline_requires_image_attestation(tmp_path):
    from lwa_mcp.constraints import ConstraintKernel
    from lwa_mcp.rite_pipeline import run_rite
    from lwa_mcp.rites import Agent, RiteManifest, Trigger, Workspace
    from lwa_mcp.rite_state import RiteState

    rite = RiteManifest("health", Trigger("event"), Workspace(), Agent("health"), (), (), "report", False)
    result = run_rite(rite, tmp_path, "new", RiteState(tmp_path / "state.json"),
                      agent_runner=lambda *_: {}, kernel=ConstraintKernel({"version": 1, "hard": {}}))
    assert result["status"] == "blocked"
    assert "image_attestation_required" in result["blockers"]

def test_rite_pipeline_collects_evidence_before_running_agent(tmp_path):
    from lwa_mcp.constraints import ConstraintKernel
    from lwa_mcp.rite_pipeline import run_rite
    from lwa_mcp.rites import Agent, RiteManifest, Trigger, Workspace
    from lwa_mcp.rite_state import RiteState
    rite = RiteManifest("health", Trigger("event"), Workspace(), Agent("health"), (), (), "report", False)
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], cwd=tmp_path, check=True)
    image = "registry.test/lwa@sha256:" + "a" * 64
    calls = []
    def collect(actual_image, _path):
        calls.append(actual_image)
        item = {"sha256": "a" * 64}
        return {"image": actual_image, "attestation": item, "sbom": item, "vulnerabilities": item, "runtime": item}
    result = run_rite(rite, tmp_path, "new", RiteState(tmp_path / "state.json"), agent_runner=lambda *_: {"changed_paths": ["README.md"], "files": {"README.md": "updated\n"}, "terminal": {"tests": True, "lint": True, "git_diff_check": True, "secret_scan": True, "protected_files_unchanged": True}}, kernel=ConstraintKernel({"version": 1, "hard": {}}), attestation={"verified": True, "image": image}, image=image, runtime_evidence={"image": image, "rootless": True, "network_disabled": True, "read_only": True, "no_new_privs": True}, evidence_collector=collect)
    assert calls == [image]
    assert result["status"] in {"ready", "blocked"}
    assert "image_gate" not in result or result["image_gate"]["passed"] is True
