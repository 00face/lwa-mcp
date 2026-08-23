#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"

if [[ "${LWA_LIVE_PROVIDER_CHECK:-}" != "1" ]]; then
  echo "Refusing live provider checks. Re-run with LWA_LIVE_PROVIDER_CHECK=1." >&2
  exit 2
fi
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python runtime not found: $PYTHON_BIN" >&2
  echo "Run scripts/verify-offline.sh first or set PYTHON_BIN." >&2
  exit 2
fi

cd "$ROOT"
PYTHONPATH=src "$PYTHON_BIN" scripts/check-live-providers.py "$@"
