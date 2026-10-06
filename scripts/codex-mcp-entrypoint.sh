#!/usr/bin/env bash
# Stable absolute-path launcher for the Codex Lwa MCP plugin.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${LWA_MCP_PYTHON:-${ROOT}/.venv/bin/python}"

if [[ ! -x "$PYTHON" ]]; then
  echo "Lwa MCP Python runtime not found: $PYTHON" >&2
  exit 127
fi

exec "$PYTHON" -m lwa_mcp.server "$@"
