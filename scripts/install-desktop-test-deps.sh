#!/usr/bin/env bash
set -euo pipefail

packages=(xvfb openbox firefox xdotool xclip orca at-spi2-core imagemagick)
commands=(Xvfb openbox firefox xdotool xclip orca /usr/libexec/at-spi-bus-launcher convert)

if [[ "${1:-}" == "--check" ]]; then
  missing=()
  for command_name in "${commands[@]}"; do
    command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
  done
  if ((${#missing[@]})); then
    missing_json=""
    for package in "${missing[@]}"; do
      missing_json="${missing_json:+$missing_json,}\"$package\""
    done
    printf '{"status":"skipped","missing":[%s],"install":"sudo apt-get install -y xvfb openbox firefox xdotool xclip orca at-spi2-core imagemagick"}\n' "$missing_json"
    exit 2
  fi
  printf '{"status":"ready","packages":["xvfb","openbox","firefox","xdotool","xclip","orca","at-spi2-core","imagemagick"]}\n'
  exit 0
fi

if [[ "${1:-}" != "--install" ]]; then
  printf '%s\n' 'Usage: scripts/install-desktop-test-deps.sh --check|--install' >&2
  exit 64
fi

sudo apt-get install -y "${packages[@]}"
"$0" --check
