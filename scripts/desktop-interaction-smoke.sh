#!/usr/bin/env bash
set -euo pipefail

mode="${1:---check}"
url="${LWA_DESKTOP_TEST_URL:-http://127.0.0.1:8766/codex}"
missing=()
for command_name in Xvfb openbox firefox xdotool xclip curl xwd; do
  command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
done

if ((${#missing[@]})); then
  missing_json=""
  for command_name in "${missing[@]}"; do
    missing_json="${missing_json:+$missing_json,}\"$command_name\""
  done
  printf '{"status":"skipped","missing":[%s],"install":"sudo apt-get install -y xvfb openbox firefox xdotool xclip orca at-spi2-core imagemagick"}\n' "$missing_json"
  exit 2
fi

if [[ "$mode" == "--check" ]]; then
  if curl -fsS -o /dev/null "$url"; then
    printf '{"status":"ready","url":"%s","display_manager":"openbox"}\n' "$url"
    exit 0
  fi
  printf '{"status":"blocked","reason":"dashboard_unreachable","url":"%s"}\n' "$url"
  exit 1
fi

if [[ "$mode" != "--run" ]]; then
  printf '%s\n' 'Usage: scripts/desktop-interaction-smoke.sh --check|--run' >&2
  exit 64
fi

runtime_dir=$(mktemp -d /tmp/lwa-desktop-smoke.XXXXXX)
evidence_path="${LWA_DESKTOP_EVIDENCE:-/tmp/lwa-desktop-interaction-$$.xwd}"
display_file="$runtime_dir/display"
xvfb_pid=""
wm_pid=""
firefox_pid=""
clipboard_pid=""

cleanup() {
  set +e
  [[ -n "$firefox_pid" ]] && kill "$firefox_pid" 2>/dev/null
  [[ -n "$clipboard_pid" ]] && kill "$clipboard_pid" 2>/dev/null
  [[ -n "$wm_pid" ]] && kill "$wm_pid" 2>/dev/null
  [[ -n "$xvfb_pid" ]] && kill "$xvfb_pid" 2>/dev/null
  [[ -n "$firefox_pid" ]] && wait "$firefox_pid" 2>/dev/null
  [[ -n "$clipboard_pid" ]] && wait "$clipboard_pid" 2>/dev/null
  [[ -n "$wm_pid" ]] && wait "$wm_pid" 2>/dev/null
  [[ -n "$xvfb_pid" ]] && wait "$xvfb_pid" 2>/dev/null
  rm -rf "$runtime_dir"
}
trap cleanup EXIT

Xvfb -displayfd 3 -screen 0 1280x900x24 -ac >"$runtime_dir/xvfb.log" 2>&1 3>"$display_file" &
xvfb_pid=$!
for _ in {1..50}; do
  [[ -s "$display_file" ]] && break
  sleep 0.1
done
if [[ ! -s "$display_file" ]]; then
  printf '{"status":"failed","reason":"xvfb_start_timeout"}\n'
  exit 1
fi
display_number=$(head -n 1 "$display_file")
export DISPLAY=":$display_number"

openbox --sm-disable >"$runtime_dir/openbox.log" 2>&1 &
wm_pid=$!
profile_dir="$runtime_dir/firefox-profile"
mkdir -p "$profile_dir"
firefox --no-remote --profile "$profile_dir" --new-instance -width 1280 -height 900 "$url" >"$runtime_dir/firefox.log" 2>&1 &
firefox_pid=$!

window_id=$(timeout 20s xdotool search --sync --onlyvisible --name 'Codex' 2>/dev/null | head -n 1 || true)
if [[ -z "$window_id" ]]; then
  printf '{"status":"failed","reason":"browser_window_not_visible","display":"%s"}\n' "$DISPLAY"
  exit 1
fi
xdotool windowactivate --sync "$window_id"
sleep "${LWA_DESKTOP_STARTUP_WAIT:-30}"

sentinel="LWA_DESKTOP_SENTINEL_20260821"
printf '%s' "$sentinel" | xclip -selection clipboard -in -loops 1 &
clipboard_pid=$!
sleep 0.2
clipboard_value=$(xclip -selection clipboard -out)
if [[ "$clipboard_value" != "$sentinel" ]]; then
  printf '{"status":"failed","reason":"clipboard_roundtrip_failed"}\n'
  exit 1
fi

# Fixed viewport keeps these coordinates stable while exercising pointer focus
# and paste. Scroll over the page so the LWA prompt is visible below the
# bounded Codex feed; the screenshot is retained outside the runtime directory.
xdotool mousemove --sync 1200 800
xdotool click --repeat 8 --delay 100 5
xdotool mousemove --sync 360 790 click 1
xdotool key --clearmodifiers ctrl+v
xdotool mousemove --sync 1120 785 click 1
sleep 2
xdotool mousemove --sync 1080 610 click 1
xwd -root -silent -out "$evidence_path"

printf '{"status":"passed","window":"%s","clipboard":"roundtrip","pointer":"exercised","keyboard":"exercised","screenshot":"%s"}\n' "$window_id" "$evidence_path"
