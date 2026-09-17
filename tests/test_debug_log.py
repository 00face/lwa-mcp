from lwa_mcp.debug_log import collect_debug_snapshot, format_debug_snapshot


def test_debug_snapshot_excludes_sensitive_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    snapshot = collect_debug_snapshot(
        executable=None,
        session_active=True,
        pipeline_busy=False,
        scroll_offset=2,
        rows=24,
        columns=80,
    )
    assert snapshot["privacy"] == {
        "prompts_recorded": False,
        "environment_values_recorded": False,
        "credentials_recorded": False,
    }
    assert snapshot["privacy"]["prompts_recorded"] is False
    assert any("DEBUG SNAPSHOT" in line for line in format_debug_snapshot(snapshot, tmp_path / "debug.log"))
