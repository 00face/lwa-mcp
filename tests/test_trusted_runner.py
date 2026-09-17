import pytest

def test_trusted_runner_rejects_unallowlisted_command():
    from lwa_mcp.trusted_runner import trusted_run
    with pytest.raises(ValueError):
        trusted_run(["sh", "-c", "true"], timeout=1)
