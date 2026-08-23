#!/usr/bin/env bash
set -euo pipefail

mode="${1:---check}"
if [[ "$mode" != "--check" && "$mode" != "--install" ]]; then
  printf 'Usage: %s --check|--install\n' "$0" >&2
  exit 64
fi

user_home=$(getent passwd "$(id -u)" | cut -d: -f6)
user_bin="$user_home/.local/bin"
helper_dir="$user_home/.config/lwa-mcp"
helper="$helper_dir/terminal-path.sh"

declare -A candidates=(
  [tabby]="/opt/Tabby/tabby"
  [wave]="/opt/Wave/waveterm"
  [wezterm]="/opt/WezTerm/wezterm"
  [rio]="/opt/Rio/rio"
  [blackbox]="/usr/bin/blackbox"
  [ptyxis]="/usr/bin/ptyxis"
)

declare -A flatpak_ids=(
  [rio]="com.rioterm.Rio"
  [blackbox]="com.raggesilver.BlackBox"
  [ptyxis]="app.devsuite.Ptyxis"
  [wezterm]="org.wezfurlong.wezterm"
)

if [[ "$mode" == "--install" ]]; then
  install -d -m 0700 "$user_bin" "$helper_dir"
  : > "$helper"
  chmod 0600 "$helper"
  printf '%s\n' '# LWA terminal PATH handshake; source this file in each shell.' >> "$helper"
  printf '%s\n' "export PATH=\"$user_bin:\$PATH\"" >> "$helper"

  for name in "${!candidates[@]}"; do
    target="${candidates[$name]}"
    link="$user_bin/$name"
    if [[ ! -x "$target" ]]; then
      app_id="${flatpak_ids[$name]-}"
      if [[ -n "$app_id" ]] && command -v flatpak >/dev/null 2>&1 && flatpak info "$app_id" >/dev/null 2>&1; then
        if [[ -e "$link" && ! -L "$link" ]]; then
          printf '{"terminal":"%s","status":"conflict","path":"%s"}\n' "$name" "$link"
          continue
        fi
        printf '#!/usr/bin/env bash\nexec flatpak run %q "$@"\n' "$app_id" > "$link"
        chmod 0700 "$link"
        printf '{"terminal":"%s","status":"flatpak-wrapper","app":"%s","path":"%s"}\n' "$name" "$app_id" "$link"
        continue
      fi
      printf '{"terminal":"%s","status":"unresolved","expected":"%s"}\n' "$name" "$target"
      continue
    fi
    if [[ -e "$link" && ! -L "$link" ]]; then
      printf '{"terminal":"%s","status":"conflict","path":"%s"}\n' "$name" "$link"
      continue
    fi
    ln -sfn "$target" "$link"
    printf '{"terminal":"%s","status":"linked","path":"%s"}\n' "$name" "$link"
  done
fi

printf '%s\n' '{"terminals":['
first=1
for name in wezterm tabby wave rio blackbox ptyxis; do
  if command -v "$name" >/dev/null 2>&1; then
    path=$(command -v "$name")
    [[ $first -eq 1 ]] || printf ',\n'
    printf '  {"name":"%s","status":"ready","path":"%s"}' "$name" "$path"
    first=0
  else
    [[ $first -eq 1 ]] || printf ',\n'
    printf '  {"name":"%s","status":"missing"}' "$name"
    first=0
  fi
done
printf '%s\n' ']}'

if [[ "$mode" == "--install" ]]; then
  printf '\nSource the helper now with:\n  source %q\n' "$helper"
  printf 'Then verify with:\n  command -v tabby wave wezterm rio blackbox ptyxis\n'
fi
