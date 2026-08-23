# WO-051 Terminal Handoff Handshake

**Recorded:** 2026-08-21  
**Owner:** LWA terminal/web surfaces  
**Receiver:** Codex PTY and MCP control plane  
**State:** Accepted with explicitly open desktop-interaction gates

## Handshake contract

1. The MCP control plane must initialize independently of provider completion.
2. The web frame must expose `/codex` and capability metadata before a prompt
   is sent.
3. The native frame must select an honest host renderer and restore the PTY on
   exit.
4. Unsupported graphics must reduce to bounded text, never raw control data.
5. Prompt text must cross the LWA finalization boundary before the LWA prompt
   writes to Codex.

## Accepted evidence

- MCP stdio handshake: passed; protocol `2025-11-25`, 40 tools, 3 resources,
  and 1 prompt. No provider completion or quota call was made.
- Live dashboard handshake: `/codex` and `/api/codex/capabilities` both
  returned HTTP 200.
- WebSocket lifecycle: ordered `attached`, `running`, and `terminal` events;
  PTY reaped after disconnect.
- Native non-Ghostty handshake: a real PTY selected `curses fallback frame`,
  connected to the explicit echo executable, accepted Esc, and exited zero.
- Graphics handshake: Kitty and Sixel capability branches passed; unsupported
  payloads became `[graphics omitted]` placeholders.
- Regression handshake: focused suite 15 passed; full suite excluding the
  host-sensitive credential fixture 169 passed and 3 skipped.

## Open gates and reasons

- **Direct browser click/clipboard:** open because the isolated Xvfb display
  had no window manager, so xdotool could not obtain a visible Firefox window.
  Headless rendering and route checks are valid, but they do not prove desktop
  pointer or clipboard behavior.
- **Assistive technology interaction:** open because no screen reader was
  attached to this session. Static label, focus, hint, and live-region checks
  pass, but they are not a substitute for a screen-reader run.
- **Physical-terminal cursor/OSC-8 behavior:** open because the PTY smoke test
  proves frame lifecycle and fallback selection, not a terminal emulator's
  cursor rasterization or hyperlink click target behavior.

These gates remain partial to avoid claiming evidence that was not collected;
they do not block the provider-free startup, web route, native fallback, or
graphics-fallback handoff.
