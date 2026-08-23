#!/usr/bin/env bash
set -euo pipefail

# Validate the cached surface before handing one long-lived MCP process to the host.
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
CACHE="${LWA_MCP_HANDSHAKE_CACHE:-$ROOT/.runtime/mcp-capabilities.json}"
TIMEOUT="${LWA_MCP_HANDSHAKE_TIMEOUT:-8}"

if [[ "${1:-}" == "--" ]]; then
  shift
  TARGET=("$@")
else
  TARGET=("$ROOT/.venv/bin/lwa-mcp")
fi

if [[ "${#TARGET[@]}" -eq 0 ]]; then
  echo "mcp_session_warm.sh: missing MCP command after --" >&2
  exit 2
fi

COMMAND_TEXT="$(printf '%q ' "${TARGET[@]}")"
"$PYTHON_BIN" "$ROOT/scripts/handshake/mcp_capabilities_once.py" \
  --root "$ROOT" --command "$COMMAND_TEXT" --cache "$CACHE" --timeout "$TIMEOUT"

echo "MCP capability cache is valid; host may reuse its existing stdio session." >&2
exec "${TARGET[@]}"
