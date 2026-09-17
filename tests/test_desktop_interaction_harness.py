from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_desktop_harness_scripts_are_shell_valid_and_scoped():
    scripts = (
        ROOT / "scripts/install-desktop-test-deps.sh",
        ROOT / "scripts/desktop-interaction-smoke.sh",
    )
    for script in scripts:
        result = subprocess.run(
            ["bash", "-n", str(script)], capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stderr
        text = script.read_text(encoding="utf-8")
        assert "mktemp" in text or "apt-get" in text
        assert "xvfb" in text.lower()


def test_desktop_harness_check_reports_missing_window_manager_or_readiness():
    script = ROOT / "scripts/desktop-interaction-smoke.sh"
    result = subprocess.run(
        ["bash", str(script), "--check"], capture_output=True, text=True, check=False
    )
    assert result.returncode in {0, 1, 2}
    payload = json.loads(result.stdout)
    assert payload["status"] in {"ready", "blocked", "skipped"}
    if payload["status"] == "skipped":
        assert "install" in payload


def test_work_order_explains_assistive_technology_boundary():
    rite = (ROOT / "task-rites/TR-052-desktop-interaction-test-harness.md").read_text(
        encoding="utf-8"
    )
    assert "screen-reader" in rite
    assert "deferred" in rite
    assert "window" in rite and "manager" in rite
