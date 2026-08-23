#!/usr/bin/env bash
set -euo pipefail

# User-facing Lwa installer. It writes the checked-out project, its virtual
# environment, and the normal Lwa XDG state created by lwa-router.

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${LWA_VENV_DIR:-${ROOT}/.venv}"
WITH_DEV=0
UPGRADE_PIP=0
RUN_WIZARD=1
INSTALL_USER_BIN=1
INSTALL_SHELL_PATH=1

usage() {
  cat <<'EOF'
Usage: ./scripts/install.sh [options]

Options:
  --python PATH       Python interpreter to use (default: python3)
  --venv PATH         Virtual environment location (default: ./.venv)
  --with-dev          Install test and development dependencies too
  --upgrade-pip       Upgrade pip before installing Lwa
  --no-key-wizard     Create config/state but skip interactive credential setup
  --no-user-bin       Do not install lwa/lwa-web launch links in ~/.local/bin
  --no-shell-path     Do not add the user launch directory to shell startup files
  -h, --help          Show this help
EOF
}

while (($#)); do
  case "$1" in
    --python)
      [[ $# -ge 2 ]] || { echo "--python requires a path" >&2; exit 2; }
      PYTHON_BIN="$2"
      shift 2
      ;;
    --venv)
      [[ $# -ge 2 ]] || { echo "--venv requires a path" >&2; exit 2; }
      VENV_DIR="$2"
      shift 2
      ;;
    --with-dev)
      WITH_DEV=1
      shift
      ;;
    --upgrade-pip)
      UPGRADE_PIP=1
      shift
      ;;
    --no-key-wizard)
      RUN_WIZARD=0
      shift
      ;;
    --no-user-bin)
      INSTALL_USER_BIN=0
      shift
      ;;
    --no-shell-path)
      INSTALL_SHELL_PATH=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

die() {
  echo "Lwa installer: $*" >&2
  exit 1
}

command -v "$PYTHON_BIN" >/dev/null 2>&1 || die "Python interpreter not found: $PYTHON_BIN"
[[ -f "$ROOT/pyproject.toml" ]] || die "pyproject.toml not found under $ROOT"

"$PYTHON_BIN" - "$ROOT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
version = sys.version_info[:2]
if version < (3, 11):
    raise SystemExit(f"Python 3.11 or newer is required; found {version[0]}.{version[1]}")
if not (root / "src" / "lwa_mcp").is_dir():
    raise SystemExit(f"Lwa source package is missing under {root / 'src'}")
PY

mkdir -p "$(dirname -- "$VENV_DIR")"
VENV_DIR="$(cd -- "$(dirname -- "$VENV_DIR")" && pwd)/$(basename -- "$VENV_DIR")"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Creating virtual environment: $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
[[ -x "$VENV_PYTHON" ]] || die "Virtual environment Python is unavailable: $VENV_PYTHON"

if ((UPGRADE_PIP)); then
  "$VENV_PYTHON" -m pip install --upgrade pip
fi

if ((WITH_DEV)); then
  "$VENV_PYTHON" -m pip install -e "$ROOT[dev]"
else
  "$VENV_PYTHON" -m pip install -e "$ROOT"
fi

# Keep launchers executable after extraction or mode-preserving archive restore.
chmod 0755 \
  "$ROOT/scripts/install.sh" \
  "$ROOT/scripts/lwa.sh" \
  "$ROOT/scripts/lwa-web.sh" \
  "$ROOT/scripts/codex-mcp-entrypoint.sh" \
  "$ROOT/scripts/run-dashboard.sh" \
  "$ROOT/scripts/terminal-path-handshake.sh"

USER_BIN_DIR="${LWA_USER_BIN_DIR:-${HOME:-$ROOT}/.local/bin}"
if ((INSTALL_USER_BIN)); then
  mkdir -p "$USER_BIN_DIR"
  ln -sfn "$VENV_DIR/bin/lwa" "$USER_BIN_DIR/lwa"
  ln -sfn "$VENV_DIR/bin/lwa-web" "$USER_BIN_DIR/lwa-web"
fi
if ((INSTALL_SHELL_PATH)) && [[ -x "$ROOT/scripts/terminal-path-handshake.sh" ]]; then
  bash "$ROOT/scripts/terminal-path-handshake.sh" --install
fi
if ((INSTALL_USER_BIN && INSTALL_SHELL_PATH)) && [[ -n "${HOME:-}" ]]; then
  for shell_file in "$HOME/.profile" "$HOME/.zshrc"; do
    touch "$shell_file"
    if ! grep -Fq '# Lwa user launchers' "$shell_file"; then
      printf '\n# Lwa user launchers\nexport PATH="%s:$PATH"\n' "$USER_BIN_DIR" >> "$shell_file"
    fi
  done
fi
if ((INSTALL_SHELL_PATH)) && [[ -n "${HOME:-}" ]]; then
  zshrc="$HOME/.zshrc"
  touch "$zshrc"
  if ! grep -Fq 'source "$HOME/.config/lwa-mcp/terminal-path.sh"' "$zshrc"; then
    printf '\nsource "$HOME/.config/lwa-mcp/terminal-path.sh"\n' >> "$zshrc"
  fi
fi

if ((RUN_WIZARD)); then
  "$VENV_DIR/bin/lwa-router" init
else
  "$VENV_DIR/bin/lwa-router" init --no-key-wizard
fi

cat <<EOF

Installed Lwa MCP successfully.

Activate the environment:
  source "$VENV_DIR/bin/activate"

Launch:
  lwa
  lwa-web

User launch links: $USER_BIN_DIR/lwa and $USER_BIN_DIR/lwa-web

Diagnostics:
  "$VENV_DIR/bin/lwa-router" doctor
  "$ROOT/scripts/run-dashboard.sh"

Credential setup:
  "$VENV_DIR/bin/lwa-router" keys
EOF

case ":${PATH:-}:" in
  *":$USER_BIN_DIR:"*) ;;
  *) printf 'Add this directory to PATH for any terminal: export PATH="%s:$PATH"\n' "$USER_BIN_DIR" ;;
esac

if [[ -d "${HOME:-}/.config/castor-pollux" || -d "${HOME:-}/.local/state/castor-pollux" ]]; then
  printf '\nPrevious Castor & Pollux state detected. Optional non-destructive migration:\n  %s\n' \
    "$ROOT/scripts/migrate-from-castor-pollux.sh"
fi
