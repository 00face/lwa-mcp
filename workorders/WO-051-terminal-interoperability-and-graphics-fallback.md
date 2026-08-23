# WO-051 — Terminal Interoperability and Graphics Fallback

**Status:** Partial — startup, route readiness, MCP/terminal handoff, protocol
fixtures, capability metadata, text fallback, headless browser rendering,
native PTY fallback, non-Ghostty repeat, and installed Kitty/Sixel graphics
checks pass. Direct desktop click/clipboard and assistive-input coverage
remains.
**Latest evidence (2026-08-21):** [WO-051 evidence](../reports/WO-051-terminal-evidence.md)
records 15 focused passes, 169 full non-credential passes, live
`/codex`/capability checks, and successful Kitty/Sixel smoke tests.
**Priority:** P1
**Parent:** WO-048, WO-049, WO-050
**Task rite:** [TR-051](../task-rites/TR-051-terminal-interoperability-and-graphics-fallback.md)
**Handoff:** [WO-051 terminal handshake](../reports/WO-051-terminal-handoff-handshake.md)
**Follow-up:** [WO-052 desktop interaction harness](WO-052-desktop-interaction-test-harness.md)

## Objective

Finish the user-facing terminal acceptance work without making the low-resource
LWA frame depend on Ghostty, WebGL, Kitty graphics, Sixel, or a GPU.

## Contract

- ANSI/VT control sequences do not corrupt visible text or prompt input.
- Unicode and OSC-8 hyperlinks degrade to readable text when unsupported.
- Kitty/Sixel capability is detected and reported honestly; unsupported image
  data becomes a bounded placeholder.
- Low Resource mode disables shader animation and remains keyboard reachable.
- Native Ghostty availability is an adapter hint, not a false claim that LWA
  has replaced Ghostty's renderer.
- Web and native surfaces retain bounded history and redacted telemetry.

## Required Work

1. Add shared protocol fixtures for ANSI/VT, Unicode, OSC-8 hyperlinks, and
   unsupported graphics sequences.
2. Add explicit renderer/capability metadata to the web and native surfaces.
3. Verify keyboard focus, pause/scroll behavior, narrow terminals, long
   output, and Low Resource fallback.
4. Run the rite on the target Linux Mint host and record only redacted evidence.

## Acceptance

- Focused protocol and renderer tests pass.
- `/codex` remains usable with WebGL disabled.
- Bare `lwa` remains usable without Ghostty.
- No raw prompt, credential, or authorization material enters evidence.

## Evidence

Store results under `reports/WO-051-*`.

## Rollback

Disable optional graphics effects and retain the text/curses fallback. Keep the
startup improvements from WO-050.
