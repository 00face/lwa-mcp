"""Package entry point for the Textual controller acceptance command."""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    """Run the repository-local TUI acceptance runner."""
    runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts" / "lwa-tui-test"), run_name="__main__")
