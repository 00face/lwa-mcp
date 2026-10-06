#!/usr/bin/env bash
set -euo pipefail

FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1
CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME}/.config}"
STATE_HOME="${XDG_STATE_HOME:-${HOME}/.local/state}"
OLD_CONFIG="${CONFIG_HOME}/castor-pollux/router.yaml"
OLD_STATE="${STATE_HOME}/castor-pollux"
NEW_CONFIG="${CONFIG_HOME}/lwa-mcp"
NEW_STATE="${STATE_HOME}/lwa-mcp"
mkdir -p "$NEW_CONFIG" "$NEW_STATE"
chmod 700 "$NEW_CONFIG" "$NEW_STATE"

copy_or_template() {
  local source="$1" target="$2"
  if [[ -e "$target" && $FORCE -eq 1 ]]; then
    mv "$target" "${target}.pre-migration-$(date -u +%Y%m%dT%H%M%SZ)"
  fi
  [[ -e "$target" ]] && return
  if [[ -f "$source" ]]; then cp -p "$source" "$target"; else printf 'consent_mode: paid_only\n' > "$target"; fi
}

copy_or_template "$OLD_CONFIG" "$NEW_CONFIG/router.yaml"
copy_or_template "$OLD_STATE/twins.env" "$NEW_STATE/lwa.env"
if [[ -f "$OLD_STATE/router.sqlite3" ]]; then
  if [[ -e "$NEW_STATE/lwa.sqlite3" && $FORCE -eq 1 ]]; then mv "$NEW_STATE/lwa.sqlite3" "$NEW_STATE/lwa.sqlite3.pre-migration-$(date -u +%Y%m%dT%H%M%SZ)"; fi
  [[ -e "$NEW_STATE/lwa.sqlite3" ]] || cp -p "$OLD_STATE/router.sqlite3" "$NEW_STATE/lwa.sqlite3"
else
  : > "$NEW_STATE/lwa.sqlite3"
fi
chmod 600 "$NEW_STATE/lwa.env" "$NEW_STATE/lwa.sqlite3"
echo "Migrated castor-pollux state to lwa-mcp without removing the source."
