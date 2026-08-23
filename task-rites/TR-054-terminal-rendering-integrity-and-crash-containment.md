# TR-054 — Terminal Rendering Integrity and Crash Containment Rite

**Work order:** [WO-054](../workorders/WO-054-terminal-rendering-integrity-and-crash-containment.md)
**Mode:** recovery and evidence-first verification

**Current result:** The stateful PTY normalizer, conservative embedded text
profile, secret redaction, and lifecycle containment gates pass. Native and
web visual confirmation after restarting the dashboard remains operator-
verified.

## Sequence

1. Capture a non-secret SITREP describing the observed native and web failures.
2. Reproduce the stream failure with deterministic mixed PTY fixtures rather
   than relying on a screenshot alone.
3. Normalize the stream once at the PTY boundary using incremental UTF-8 and a
   stateful control/graphics parser.
4. Make native and web consumers render only normalized events.
5. Contain EOF, broken-pipe, resize, websocket, and browser disconnect paths.
6. Bound transcript/history updates and preserve screen-reader-readable text.
7. Run focused parser/session tests, then the full non-visual application suite.
8. Run the operator-visible desktop check when a display is available and
   record any remaining visual gate explicitly.

## Evidence required

- No base64-like graphics payload in normalized output.
- No uncaught exception from Codex EOF or PTY write/resize failure.
- Native and web status transitions include `connected`, `exited`, and `error`.
- Secret-shaped values are absent from transcript events.
- Test totals and any intentionally skipped visual checks are recorded.

## Gate policy

The work order remains open if either surface still crashes or if output is
only technically present but unreadable. A visual check may remain operator-
verified, but it cannot be represented as an automated pass without evidence.
