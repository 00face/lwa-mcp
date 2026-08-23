#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${LWA_PYTHON:-${ROOT}/.venv/bin/python}"
exec "${PYTHON}" -m lwa_mcp.launch "$@"
