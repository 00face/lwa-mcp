#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_ROOT="${LWA_MCP_MAINTENANCE_ROOT:-${XDG_STATE_HOME:-$HOME/.local/state}/lwa-mcp/maintenance}"
LOCK_PATH="${STATE_ROOT}/maintenance.lock"

mkdir -p -- "$STATE_ROOT"
chmod 700 -- "$STATE_ROOT"
exec 9>"$LOCK_PATH"
if ! flock -n 9; then
  printf 'Lwa maintenance is already running: %s\n' "$LOCK_PATH" >&2
  exit 75
fi

export LWA_MCP_CONFIG="${LWA_MCP_CONFIG:-$HOME/.config/lwa-mcp/router.yaml}"
export LWA_MCP_ENV_FILE="${LWA_MCP_ENV_FILE:-$HOME/.local/state/lwa-mcp/lwa.env}"
export LWA_MCP_DB="${LWA_MCP_DB:-${XDG_STATE_HOME:-$HOME/.local/state}/lwa-mcp/lwa.sqlite3}"
export LWA_MCP_TOOL_LIBRARY="${LWA_MCP_TOOL_LIBRARY:-${XDG_DATA_HOME:-$HOME/.local/share}/lwa-mcp/tool-library}"

PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
ROUTER_BIN="${LWA_ROUTER_BIN:-$ROOT/.venv/bin/lwa-router}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi
if [[ ! -x "$ROUTER_BIN" ]]; then
  ROUTER_BIN="$(command -v lwa-router || true)"
fi

usage() {
  cat >&2 <<'EOF'
Usage: scripts/lwa-maintenance.sh <telemetry|live-probe|offline-verify>

live-probe requires LWA_LIVE_PROVIDER_CHECK=1 and performs only catalog,
health, and optional quota probes; it never submits a completion prompt.
EOF
}

case "${1:-}" in
  telemetry)
    [[ -n "$ROUTER_BIN" ]] || { printf 'lwa-router not found\n' >&2; exit 127; }
    exec "$ROUTER_BIN" telemetry
    ;;
  live-probe)
    [[ "${LWA_LIVE_PROVIDER_CHECK:-0}" == "1" ]] || {
      printf 'Refusing live probe; set LWA_LIVE_PROVIDER_CHECK=1 explicitly.\n' >&2
      exit 2
    }
    [[ -n "$PYTHON_BIN" && -x "$PYTHON_BIN" ]] || {
      printf 'Python runtime not found for Lwa live probe.\n' >&2
      exit 127
    }
    probe_args=()
    if [[ "${LWA_LIVE_INCLUDE_QUOTA:-0}" == "1" ]]; then
      probe_args+=(--quota)
    fi
    exec "$PYTHON_BIN" "$ROOT/scripts/check-live-providers.py" "${probe_args[@]}"
    ;;
  offline-verify)
    exec "$ROOT/scripts/verify-offline.sh"
    ;;
  *)
    usage
    exit 2
    ;;
esac
