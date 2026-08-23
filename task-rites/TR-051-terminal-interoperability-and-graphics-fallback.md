# TR-051 — Terminal Interoperability and Graphics Fallback Rite

**Purpose:** prove that LWA's framed Codex surfaces remain useful on a
low-resource Linux system when advanced terminal graphics are unavailable.

**Handoff handshake:** [WO-051 terminal handshake](../reports/WO-051-terminal-handoff-handshake.md)

**Current result (2026-08-21):** Partial promotion. Protocol fixtures,
capability reporting, text fallback, live route checks, headless browser
rendering, native PTY fallback exit checks, and installed Kitty/Sixel graphics
tests pass; direct click/clipboard and assistive-input checks remain. The live WebSocket
lifecycle now passes with ordered attach, running, and terminal events.
Kitty/Sixel installation and smoke tests now pass as well.
The installed-host ANSI/OSC and capability branches also pass. Static DOM
accessibility checks now cover label associations, keyboard focus, live-region
behavior, and prompt hints; direct click/clipboard and assistive-input
interaction remain open.
The MCP and terminal handoff handshake is accepted; the non-Ghostty native
repeat and post-disconnect session cleanup gates are closed.

## Entry

Use the restarted dashboard and project virtual environment. Record renderer
capability names, route status, test outcomes, and resource mode only.

## Action

1. Exercise ANSI/VT color, cursor movement, Unicode, OSC-8 hyperlinks, and
   unsupported Kitty/Sixel sequences.
2. Toggle WebGL/shaders and Low Resource mode; resize to a narrow terminal.
3. Verify keyboard focus, prompt separation, bounded history, and visible
   connection errors.
4. Repeat the native frame with and without a Ghostty host.

## Check

- Text remains readable and graphics degrade to a bounded fallback.
- No animation is required in Low Resource mode.
- Prompt literals and constraints remain intact at the LWA boundary.
- No orphan process or sensitive evidence is produced.

## Promote when

Repeated focused checks and one Linux Mint desktop run pass.

## Rollback

Turn off optional graphics and use the existing text/curses frame while keeping
WO-050 startup behavior.
