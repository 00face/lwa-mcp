#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
KEEP_ENV=0
VERIFY_ENV_DIR="${LWA_VERIFY_ENV_DIR:-}"

usage() {
  cat <<'EOF'
Usage: scripts/verify-offline.sh [--keep-env]

Creates an isolated verification environment, installs the declared development
dependencies, and runs compilation, pytest, Ruff, and a dependency-free wheel
build. No provider completion or live network check is performed by the script.

Environment:
  PYTHON_BIN         Python executable used to create the virtual environment.
  LWA_VERIFY_ENV_DIR Reusable environment directory; otherwise a temporary one.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-env) KEEP_ENV=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

TEMP_ENV=0
if [[ -z "$VERIFY_ENV_DIR" ]]; then
  VERIFY_ENV_DIR="$(mktemp -d "${TMPDIR:-/tmp}/lwa-mcp-verify.XXXXXX")"
  TEMP_ENV=1
fi

cleanup() {
  if [[ "$TEMP_ENV" -eq 1 && "$KEEP_ENV" -eq 0 ]]; then
    rm -rf -- "$VERIFY_ENV_DIR"
  fi
}
trap cleanup EXIT

if [[ ! -x "$VERIFY_ENV_DIR/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$VERIFY_ENV_DIR"
fi

PY="$VERIFY_ENV_DIR/bin/python"
"$PY" -m pip install "setuptools>=68" wheel
# Reuse the prepared verification environment so this step remains usable
# when package indexes are unavailable after the declared dependencies are
# already installed.
"$PY" -m pip install -e "$ROOT[dev]" --no-build-isolation
cd "$ROOT"
PYTHONPATH=src "$PY" -m py_compile $(find src tests -name '*.py' -type f -print)
PYTHONPATH=src "$PY" -m pytest -q
"$VERIFY_ENV_DIR/bin/ruff" check src tests
"$PY" -m pip wheel . --no-deps --no-build-isolation --wheel-dir "$VERIFY_ENV_DIR/wheelhouse"

echo "Offline verification passed. Environment: $VERIFY_ENV_DIR"
