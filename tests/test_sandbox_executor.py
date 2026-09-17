from unittest.mock import patch

import pytest


def test_sandbox_command_has_hard_runtime_limits(tmp_path):
    from lwa_mcp.sandbox_executor import sandbox_command

    with patch("lwa_mcp.sandbox_executor.shutil.which", side_effect=lambda name: "/usr/bin/podman" if name == "podman" else None):
        command = sandbox_command(tmp_path, ["pytest", "-q"])
    assert "--network=none" in command
    assert "--memory" in command and "512m" in command
    assert "--cap-drop=ALL" in command
    assert "--security-opt=no-new-privileges" in command
    assert "--read-only" in command and "--pids-limit=256" in command


def test_sandbox_requires_supported_runtime(tmp_path):
    from lwa_mcp.sandbox_executor import SandboxUnavailable, sandbox_command

    with patch("lwa_mcp.sandbox_executor.shutil.which", return_value=None):
        with pytest.raises(SandboxUnavailable):
            sandbox_command(tmp_path, ["true"])
