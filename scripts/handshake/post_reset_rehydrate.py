#!/usr/bin/env python3
"""Rehydrate a clean Lwa checkout without exposing or replacing .env."""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
VENV = ROOT / ".venv"
OPTIONAL = ("podman", "cosign", "syft", "grype")


def run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    print("$", " ".join(command), flush=True)
    return subprocess.run(command, cwd=cwd, text=True, check=False)


def protect_env() -> None:
    if not ENV_FILE.is_file() or ENV_FILE.is_symlink():
        raise RuntimeError(".env is missing or is not a regular file")
    if ENV_FILE.stat().st_uid != os.getuid():
        raise RuntimeError(".env is not owned by the current user")
    if stat.S_IMODE(ENV_FILE.stat().st_mode) != 0o600:
        raise RuntimeError(".env must have mode 600")
    gitignore = ROOT / ".gitignore"
    lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    if ".env" not in lines:
        with gitignore.open("a", encoding="utf-8") as stream:
            if lines and not gitignore.read_bytes().endswith(b"\n"):
                stream.write("\n")
            stream.write(".env\n")


def main() -> int:
    protect_env()
    VENV.mkdir(exist_ok=True)
    python = VENV / "bin" / "python"
    if not python.exists():
        result = run([sys.executable, "-m", "venv", str(VENV)])
        if result.returncode:
            return result.returncode
    pip = VENV / "bin" / "pip"
    for command in ([str(pip), "install", "--upgrade", "pip"], [str(pip), "install", "-e", ".[dev]"]):
        result = run(command)
        if result.returncode:
            return result.returncode
    smoke_tests = [str(ROOT / path) for path in ("tests/test_config.py", "tests/test_credentials.py", "tests/test_preflight.py")]
    result = run([str(python), "-m", "pytest", "-q", *smoke_tests], cwd=Path("/tmp"))
    if result.returncode:
        return result.returncode
    missing = [tool for tool in OPTIONAL if subprocess.run(["sh", "-c", f"command -v {tool}"], capture_output=True, check=False).returncode]
    print("optional_tools=" + ",".join(f"{tool}:present" if tool not in missing else f"{tool}:missing" for tool in OPTIONAL))
    if missing:
        print("Missing optional tools require operator-approved system installation: " + ", ".join(missing), file=sys.stderr)
        return 2
    if stat.S_IMODE(ENV_FILE.stat().st_mode) != 0o600:
        raise RuntimeError(".env permissions changed unexpectedly")
    print("rehydration=complete env_preserved=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
