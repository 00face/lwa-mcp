#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${LWA_MCP_DASHBOARD_HOST:-127.0.0.1}"
PORT="${LWA_MCP_DASHBOARD_PORT:-8766}"
URL="http://${HOST}:${PORT}"
# The dashboard is auxiliary to the MCP protocol. Keep it opt-in for Codex
# startup so the stdio handshake is not blocked by dashboard readiness.
START_DASHBOARD="${LWA_MCP_START_DASHBOARD:-0}"
RUNTIME_ROOT="${LWA_MCP_RUNTIME_ROOT:-/tmp/lwa-mcp-codex}"
LOG_DIR="${RUNTIME_ROOT}/logs"

mkdir -p "${RUNTIME_ROOT}/state" "${RUNTIME_ROOT}/config" "${RUNTIME_ROOT}/data" "${LOG_DIR}"
: >>"${LOG_DIR}/mcp-stderr.log"

export XDG_STATE_HOME="${XDG_STATE_HOME:-${RUNTIME_ROOT}/state}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-${RUNTIME_ROOT}/config}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-${RUNTIME_ROOT}/data}"
export LWA_MCP_CONFIG="${LWA_MCP_CONFIG:-${HOME}/.config/lwa-mcp/router.yaml}"
export LWA_MCP_ENV_FILE="${LWA_MCP_ENV_FILE:-${HOME}/.local/state/lwa-mcp/lwa.env}"
export LWA_MCP_DB="${LWA_MCP_DB:-${XDG_STATE_HOME}/lwa.sqlite3}"
export LWA_MCP_TOOL_LIBRARY="${LWA_MCP_TOOL_LIBRARY:-${XDG_DATA_HOME}/tool-library}"

dashboard_pid=""
dashboard_started=""

announce() {
  printf '%s\n' "$1" >&2
  if tty -s >/dev/null 2>&1; then
    printf '%s\n' "$1" >/dev/tty || true
  fi
}

port_open() {
  (exec 3<>"/dev/tcp/${HOST}/${PORT}") >/dev/null 2>&1
}

dashboard_running() {
  port_open
}

cleanup() {
  if [[ -n "${dashboard_pid}" ]]; then
    kill "${dashboard_pid}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

if [[ "${START_DASHBOARD}" != "1" ]]; then
  announce "Lwa dashboard startup skipped (set LWA_MCP_START_DASHBOARD=1 to enable)"
elif dashboard_running; then
  announce "Lwa dashboard already available at ${URL}"
else
  announce "Starting Lwa dashboard at ${URL}"
  "${ROOT}/.venv/bin/lwa-dashboard" >>"${LOG_DIR}/dashboard.log" 2>&1 &
  dashboard_pid="$!"

  for _ in $(seq 1 100); do
    if dashboard_running; then
      dashboard_started="yes"
      break
    fi
    sleep 0.1
  done

  if [[ -z "${dashboard_started}" ]]; then
    announce "Lwa dashboard did not become reachable at ${URL}; see ${LOG_DIR}/dashboard.log"
    exit 1
  fi
fi

announce "Lwa dashboard URL: ${URL}"

MCP_BIN="${LWA_MCP_BIN:-${ROOT}/.venv/bin/lwa-mcp}"
if [[ ! -x "${MCP_BIN}" ]]; then
  if command -v lwa-mcp >/dev/null 2>&1; then
    MCP_BIN="$(command -v lwa-mcp)"
  else
    announce "Lwa MCP executable not found. Install the project environment or set LWA_MCP_BIN."
    exit 127
  fi
fi
# Keep protocol stdout untouched. Duplicate stderr into a local, mode-restricted
# diagnostic file so Codex startup failures remain inspectable after the pane
# exits while still being visible to the operator.
exec "${MCP_BIN}" 2> >(tee -a "${LOG_DIR}/mcp-stderr.log" >&2)
