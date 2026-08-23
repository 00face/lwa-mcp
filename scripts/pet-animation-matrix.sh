#!/usr/bin/env bash
set -euo pipefail

session="${LWA_PET_MATRIX_SESSION:-lwa-pet-matrix}"
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${root}/.venv/bin/python"

if [[ ! -x "$python_bin" ]]; then
  printf 'Missing project Python: %s\n' "$python_bin" >&2
  exit 127
fi

if [[ "${TERM_PROGRAM:-}" == "ghostty" || -n "${GHOSTTY_RESOURCES_DIR:-}" ]] && command -v ghostty >/dev/null 2>&1; then
  modes=(
    "terminal A-terminal-animation"
    "preloaded B-preloaded-placement"
    "same-id C-client-same-id"
    "unique-id D-client-unique-id"
    "text E-text-fallback"
  )
  for entry in "${modes[@]}"; do
    read -r mode label <<<"$entry"
    ghostty --working-directory "$root" -e "$python_bin" scripts/pet-animation-matrix.py --mode "$mode" --label "$label" >/dev/null 2>&1 &
  done
  printf 'Opened five independent Ghostty windows for the pet animation matrix.\n'
  exit 0
fi

if tmux has-session -t "$session" 2>/dev/null; then
  printf 'Pet matrix already running: %s\n' "$session"
  exec tmux attach-session -t "$session"
fi

tmux new-session -d -s "$session" -c "$root" \
  "$python_bin scripts/pet-animation-matrix.py --mode terminal --label A-terminal-animation"
tmux set-option -t "$session" -g allow-passthrough on
tmux set-option -t "$session" -g mouse on
tmux set-option -t "$session" -g status off
tmux split-window -t "$session:0" -h -l 50% -c "$root" \
  "$python_bin scripts/pet-animation-matrix.py --mode preloaded --label B-preloaded-placement"
tmux split-window -t "$session:0.0" -v -l 50% -c "$root" \
  "$python_bin scripts/pet-animation-matrix.py --mode same-id --label C-client-same-id"
tmux split-window -t "$session:0.1" -v -l 50% -c "$root" \
  "$python_bin scripts/pet-animation-matrix.py --mode unique-id --label D-client-unique-id"
tmux split-window -t "$session:0.2" -v -l 50% -c "$root" \
  "$python_bin scripts/pet-animation-matrix.py --mode text --label E-text-fallback"
exec tmux attach-session -t "$session"
