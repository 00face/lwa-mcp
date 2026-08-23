#!/usr/bin/env bash
set -euo pipefail

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
elif [[ $# -gt 0 ]]; then
  printf 'Usage: %s [--force]\n' "$0" >&2
  exit 2
fi

OLD_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/castor-pollux/router.yaml"
OLD_STATE="${XDG_STATE_HOME:-$HOME/.local/state}/castor-pollux"
NEW_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/lwa-mcp"
NEW_STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/lwa-mcp"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$NEW_CONFIG_DIR" "$NEW_STATE_DIR"
chmod 700 "$NEW_CONFIG_DIR" "$NEW_STATE_DIR"

copy_preserving_destination() {
  local source="$1" destination="$2"
  if [[ ! -f "$source" ]]; then
    printf 'Not found: %s\n' "$source"
    return 0
  fi
  if [[ -e "$destination" && "$FORCE" -ne 1 ]]; then
    printf 'Preserved existing Lwa file: %s\n' "$destination"
    printf 'Use --force to back it up and replace it with the previous baseline file.\n'
    return 0
  fi
  if [[ -e "$destination" ]]; then
    cp -a -- "$destination" "$destination.pre-migration-$STAMP"
    printf 'Backed up: %s\n' "$destination.pre-migration-$STAMP"
  fi
  cp -a -- "$source" "$destination"
  printf 'Copied: %s -> %s\n' "$source" "$destination"
}

copy_preserving_destination "$OLD_CONFIG" "$NEW_CONFIG_DIR/router.yaml"
copy_preserving_destination "$OLD_STATE/twins.env" "$NEW_STATE_DIR/lwa.env"
copy_preserving_destination "$OLD_STATE/router.sqlite3" "$NEW_STATE_DIR/lwa.sqlite3"

if [[ -f "$NEW_STATE_DIR/lwa.env" ]]; then
  chmod 600 "$NEW_STATE_DIR/lwa.env"
fi

cat <<EOF

Migration is non-destructive; previous baseline files remain untouched.
Any replaced Lwa file was backed up with a .pre-migration-$STAMP suffix.
Review:
  $NEW_CONFIG_DIR/router.yaml
  $NEW_STATE_DIR/lwa.env
Then run:
  lwa-router init
  lwa-router doctor
EOF
