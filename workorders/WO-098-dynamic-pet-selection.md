# WO-098 — Dynamic Codex pet selection through LWA mirror

## Objective

Allow the LWA-owned Codex pet mirror to discover and switch among all valid
Codex cache pets at runtime without restarting Codex, LWA, tmux, or Ghostty.

## Commands

- `/pets` — list currently available assets.
- `/pets <name>` — load one exact asset.
- `/pets next` or `/pets cycle` — advance through the current discovered list.

Discovery runs on every command, so newly cached pets become selectable on the
next invocation.
