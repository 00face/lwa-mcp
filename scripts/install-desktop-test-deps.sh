#!/usr/bin/env bash
set -euo pipefail
if command -v apt-get >/dev/null 2>&1; then
  echo "Desktop test dependencies are opt-in; install xvfb and a window manager with your package manager."
else
  echo "No apt-get detected; install xvfb and a window manager manually."
fi
