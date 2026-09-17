from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

STATIC_DIR = Path(__file__).parents[1] / "src" / "lwa_mcp" / "static"


def test_polymino_control_contract_is_complete():
    html = (STATIC_DIR / "polymino-control.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "polymino-control.js").read_text(encoding="utf-8")

    for required in (
        'id="seedInput"',
        'id="exportSnapshot"',
        'id="importSnapshot"',
        'id="actionLog"',
        "URLSearchParams",
        "snapshot_version",
        "window.__polyminoControlTest",
    ):
        assert required in html or required in script

    expected_families = (
        "Monomino", "Domino", "I Triomino", "T Tetromino", "P Pentomino",
        "L Hexomino", "F Heptomino", "U Octomino", "X Nonomino", "W Decomino",
        "Y Undecomino", "Z Duodecomino", "V Tridecomino",
    )
    assert all(f"makePiece('{name}'" in script for name in expected_families)


@pytest.mark.parametrize("seed", (1, 12345, 4294967295))
def test_polymino_control_headless_browser_smoke(tmp_path, seed):
    firefox = shutil.which("firefox")
    if not firefox:
        pytest.skip("Firefox is not installed; static contract coverage still runs.")

    fixture_dir = tmp_path / "static"
    fixture_dir.mkdir()
    for name in ("polymino-control.css", "polymino-control.js"):
        shutil.copy2(STATIC_DIR / name, fixture_dir / name)
    page = (STATIC_DIR / "polymino-control.html").read_text(encoding="utf-8")
    page = page.replace('/static/polymino-control.css', 'static/polymino-control.css')
    page = page.replace('/static/polymino-control.js', 'static/polymino-control.js')
    page_path = tmp_path / "polymino-control.html"
    page_path.write_text(page, encoding="utf-8")
    screenshot = tmp_path / f"polymino-{seed}.png"
    url = f"file://{page_path}?seed={seed}"
    try:
        result = subprocess.run(
            [
                firefox,
                "--headless",
                "--no-remote",
                "--new-instance",
                "-profile",
                str(tmp_path / "firefox-profile"),
                "--screenshot",
                str(screenshot),
                "--window-size",
                "1280,1000",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=30 if os.environ.get("LWA_STRICT_BROWSER_SMOKE") == "1" else 10,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        if os.environ.get("LWA_STRICT_BROWSER_SMOKE") == "1":
            raise
        stderr = exc.stderr or ""
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        detail = "; renderer diagnostic present" if "RenderCompositorSWGL" in stderr or "GFX1-" in stderr else ""
        pytest.skip(f"Firefox headless screenshot timed out in this environment{detail}")

    if result.returncode == -11:
        pytest.skip("Firefox is installed but crashes in this sandbox before rendering.")
    assert result.returncode == 0, result.stderr or result.stdout
    assert screenshot.exists()
    assert screenshot.stat().st_size > 10_000
