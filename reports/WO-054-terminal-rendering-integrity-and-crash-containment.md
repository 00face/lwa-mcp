# WO-054 SITREP — Terminal Rendering Integrity and Crash Containment

**Recorded:** 2026-08-21
**Status:** Remediation implemented; visual restart gate remains

## Situation

The native LWA frame is launching, but the Codex feed is unreadable. The
observed output contains repeated `[graphics omitted]` markers and previously
contained long encoded-looking payloads. The user also reports crashes in both
`lwa` and `lwa-web`.

## Impact

- Codex responses cannot be reliably read in native LWA.
- LWA-Web terminal sessions are not dependable.
- A raw graphics fallback can overwhelm the low-resource display and transcript.
- PTY/process teardown errors can surface as application crashes.

## Initial hypothesis

Codex emits terminal graphics/control sequences in chunks. A stateless
per-chunk sanitizer can lose the beginning or end of a sequence and expose its
payload as ordinary text. Separately, writes or resizes after child exit can
raise transport errors that are not consistently contained.

## Current controls

- Embedded Codex sessions disable the LWA Codex plugin to avoid MCP startup
  deadlock while leaving the LWA dashboard available.
- UTF-8 decoding is incremental.
- Credential-shaped terminal values are redacted before rendering.
- Output history is bounded.

## Remediation evidence

- Added a stateful PTY filter that handles split UTF-8, ANSI, OSC, Kitty, and
  Sixel sequences without exposing graphics payloads.
- Embedded Codex now receives a conservative text-terminal environment and no
  longer inherits Ghostty/Kitty capability variables.
- Repeated graphics placeholders were removed from the text fallback.
- PTY EOF, broken writes, resize failures, and websocket errors are contained
  and represented as session status events.
- Focused Codex/native frame tests: `13 passed`.
- Full non-visual application suite: `176 passed, 2 warnings`.

## Required next evidence

- Stateful parser tests for split graphics and control sequences.
- Session lifecycle tests for EOF, broken pipe, and resize-after-exit.
- Focused native/web regression suite.
- Operator-visible confirmation that both surfaces show readable Codex text
  and remain open after startup and child termination.

## Gate status

The automated gates pass. The incident remains partially open until the
operator restarts the dashboard and confirms readable text in both `lwa` and
`lwa-web`; automated green tests alone do not close the visual gate.
