# SITREP 028 — Codex pet animation triggers

## Current contract

The pet is independently rendered by LWA. Its Codex cache is partitioned into
welcome, idle, action, and completion tracks before the terminal loop sees it.
Idle frames use 360 ms per frame; welcome, action, and completion frames use
120 ms per frame.

| Event | Track | Signal |
|---|---|---|
| LWA starts or `/pets name` succeeds | welcome | validated asset switch |
| User submits a Codex prompt | action | write to the Codex PTY |
| First visible Codex response bytes | completion | terminal event after submission |
| LWA consensus completes | completion | synthesized prompt/response completion |
| No active event | idle | timer loop |

## Why this is pragmatic

PTYs do not expose one portable “response complete” event across Ghostty,
Kitty, tmux, and fallback terminals. The first visible output after a tracked
submission is therefore the reliable cross-terminal boundary. Pet control is
kept outside the Codex input stream, so graphics cannot become typed commands.

## Remaining operator check

The authoritative Codex asset cache must contain the selected pet's frames.
On a text-only terminal, the same state is represented by the safe ASCII
fallback; graphical placement is intentionally unavailable there.
