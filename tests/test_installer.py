from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_linux_installer_has_valid_shell_syntax_and_help():
    script = ROOT / "scripts" / "install.sh"
    subprocess.run(["bash", "-n", str(script)], check=True)
    result = subprocess.run(["bash", str(script), "--help"], check=True, text=True, capture_output=True)
    assert "--no-key-wizard" in result.stdout
    assert "--venv PATH" in result.stdout
    assert "--no-user-bin" in result.stdout
    assert "USER_BIN_DIR" in script.read_text(encoding="utf-8")
    assert "ln -sfn" in script.read_text(encoding="utf-8")


def test_linux_installer_and_runtime_launchers_are_executable():
    for name in ("install.sh", "lwa.sh", "lwa-web.sh", "codex-mcp-entrypoint.sh", "run-dashboard.sh"):
        path = ROOT / "scripts" / name
        assert path.stat().st_mode & 0o111, f"{path} is not executable"


def test_windows_installer_contains_noninteractive_option():
    script = (ROOT / "scripts" / "install.bat").read_text(encoding="utf-8")
    assert "--no-key-wizard" in script
    assert "lwa-web.exe" in script
