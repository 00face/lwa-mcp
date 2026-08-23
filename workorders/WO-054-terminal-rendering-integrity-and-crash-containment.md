# WO-054 — Terminal Rendering Integrity and Crash Containment

**Status:** Partial promotion — parser, text profile, and crash containment implemented; operator visual gate remains
**Parent:** WO-051, WO-052, WO-053
**Task rite:** [TR-054](../task-rites/TR-054-terminal-rendering-integrity-and-crash-containment.md)
**SITREP:** [WO-054 SITREP](../reports/WO-054-terminal-rendering-integrity-and-crash-containment.md)

## Objective

Restore readable, stable Codex output in both `lwa` and `lwa-web`. No terminal
surface may display binary graphics payloads as text, leak raw control data, or
crash when Codex exits, the PTY closes, or a browser disconnects.

## Scope

- PTY byte decoding and terminal-control parsing.
- Kitty graphics/Sixel/OSC/CSI suppression or explicit safe fallback.
- Native curses frame rendering and input lifecycle.
- WebSocket session lifecycle, resize/write failures, and browser reconnect state.
- Bounded output history and accessible transcript safety.

## Invariants

- Printable Unicode remains intact, including characters split across reads.
- Non-text graphics payloads never appear in the visible transcript.
- Credentials remain redacted before native or browser rendering.
- A Codex child exit becomes a visible status, not an uncaught exception.
- Native and web surfaces use the same normalized terminal stream.
- Existing LWA dashboard tools remain available independently of embedded Codex.

## Acceptance gates

1. Unit tests cover split UTF-8, split ANSI, split Kitty/Sixel payloads, OSC,
   cursor controls, PTY EOF, write-after-exit, resize-after-exit, and redaction.
2. A fake PTY fixture containing mixed text, ANSI, and graphics produces only
   readable normalized text and bounded placeholders.
3. Native `lwa` remains alive through startup, child exit, and terminal restore.
4. LWA-Web remains responsive through startup, child exit, websocket close, and
   repeated resize events.
5. The accessible transcript contains normalized non-secret text only.
6. Full application tests pass; visual desktop checks are recorded separately
   when an operator can inspect the screen.

## Rollback

Retain the existing dashboard and launcher contracts, but disable embedded
graphics rendering and fall back to a plain bounded text stream until the
terminal parser is repaired.
