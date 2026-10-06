#!/usr/bin/env bash
set -euo pipefail
# A real run should allocate its isolated display with mktemp-backed state.
if [[ "${1:-}" == "--check" ]]; then
  if command -v Xvfb >/dev/null 2>&1 && (command -v xfwm4 >/dev/null 2>&1 || command -v openbox >/dev/null 2>&1); then
    printf '{"status":"ready","xvfb":true,"window_manager":true}\n'
  else
    printf '{"status":"skipped","reason":"install xvfb and a window manager first","xvfb":false,"window_manager":false}\n'
  fi
  exit 0
fi
echo "Run with --check for non-mutating readiness diagnostics."
