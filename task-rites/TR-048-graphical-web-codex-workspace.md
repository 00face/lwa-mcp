# TR-048 — Graphical Web Codex Workspace Rite

**Purpose:** prove that the additive `/codex` web workspace is a bounded,
accessible, low-resource terminal rather than a replacement dashboard or an
unbounded remote shell.

**Current result (2026-08-21):** Partial promotion. Structural and redacted
broker/prompt checks pass; desktop renderer, graphics-protocol, and resource
measurements remain to be performed.

## Entry

The Observatory is healthy, `/codex` is served, and a local Codex executable is
available or a typed unavailable-Codex fixture is selected. Record the host,
renderer capabilities, browser, and configured resource mode without storing
credentials or raw prompt text.

## Action

1. Open `/` and `/codex`; confirm both are distinct and the Observatory remains
   functional.
2. Start, resize, use, pause, and stop one PTY session. Exercise reconnect and
   browser-close cleanup.
3. Submit direct Codex input and LWA Prompt input using fixtures containing a
   path, command, identifier, acceptance criterion, and unresolved item.
4. Exercise ANSI color, cursor movement, Unicode, hyperlinks, image/graphics
   capability detection, shader toggle, WebGL-off fallback, and Low Resource
   mode.
5. Capture only redacted lifecycle/renderer/resource metadata.

## Check

- `/` and `/codex` return the expected HTML surfaces.
- WebSocket/session events are typed and bounded; disconnect leaves no orphan
  Codex process.
- The terminal remains keyboard reachable with visible focus and a live status
  region that does not announce every output byte.
- Low Resource mode disables animation, caps device scale, bounds scrollback,
  and remains usable without WebGL.
- Prompt-finalization evidence proves protected literals survive; if the
  compression route is unavailable, the UI reports an explicit bypass.
- Unsupported graphics protocols degrade without corrupting the terminal or
  claiming unsupported capability.

## Promote when

The session lifecycle, accessibility, renderer fallback, prompt-preservation,
and resource-budget checks pass on Linux Mint-class hardware in repeated runs,
with no secret or raw-prompt leakage.

## Rollback

Disable the `/codex` route or session start control, retain the Observatory,
and terminate only the LWA-owned PTY child. Keep the failure classification and
renderer evidence; do not delete credentials, ledger data, or user work.
