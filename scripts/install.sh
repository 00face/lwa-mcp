#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT_DIR}/.venv"
USER_BIN_DIR="${HOME}/.local/bin"
NO_KEY_WIZARD=0
NO_USER_BIN=0
WITH_DEV=0

usage() {
  cat <<'EOF'
Usage: scripts/install.sh [options]
  --no-key-wizard  Install without opening the credential wizard
  --with-dev       Install development and test dependencies
  --venv PATH      Choose the virtual environment path
  --no-user-bin    Do not create user-bin launcher links
  --upgrade-pip    Upgrade pip before installing
EOF
}

UPGRADE_PIP=0
while (($#)); do
  case "$1" in
    --no-key-wizard) NO_KEY_WIZARD=1 ;;
    --with-dev) WITH_DEV=1 ;;
    --no-user-bin) NO_USER_BIN=1 ;;
    --upgrade-pip) UPGRADE_PIP=1 ;;
    --venv) shift; VENV="${1:?--venv requires PATH}" ;;
    --help|-h) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

python3 -m venv "$VENV"
if (( UPGRADE_PIP )); then "$VENV/bin/python" -m pip install --upgrade pip; fi
extras=()
if (( WITH_DEV )); then extras+=(dev); fi
spec="${ROOT_DIR}"
if ((${#extras[@]})); then spec+="[${extras[*]}]"; fi
"$VENV/bin/python" -m pip install -e "$spec"
if (( ! NO_USER_BIN )); then
  mkdir -p "$USER_BIN_DIR"
  ln -sfn "$VENV/bin/lwa" "$USER_BIN_DIR/lwa"
  ln -sfn "$VENV/bin/lwa-router" "$USER_BIN_DIR/lwa-router"
fi
if (( ! NO_KEY_WIZARD )); then "$VENV/bin/lwa-router" init; else "$VENV/bin/lwa-router" init --no-key-wizard; fi
