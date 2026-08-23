# WO-048 / TR-048 Evidence

**Recorded:** 2026-08-21  
**Result:** Partial promotion; implementation checks pass, full browser and
resource rite remains open.

## Redacted checks

- `/` and `/codex` remain separate routes; `/ws/codex` and
  `/api/codex/sessions` are registered.
- Focused verification: `6 passed` for the Codex workspace, broker lifecycle,
  prompt boundary, and missing-executable fixture.
- Launch/dashboard verification: `14 passed` across Codex frame, dashboard,
  and launcher tests.
- The broker enforces a bounded session count, issues opaque session/client
  identifiers, validates terminal dimensions, and closes an unattached or
  disconnected session.
- LWA Prompt input crosses `finalize_prompt()` before PTY write. Evidence
  contains only mode, status, character counts, and a SHA-256 prompt hash;
  fixture bodies are not emitted.
- Compact mode preserves literal text while removing only trailing whitespace
  and runs of more than two newlines. Semantic mode is visibly reported as
  `semantic_unavailable_bypass` until a governed compressor route is supplied.
- Renderer contract is present: canvas terminal, optional WebGL shader, device
  scale cap, bounded 3,000-line history, and Low Resource mode that disables
  shader animation and uses a scale factor of one.

## Outstanding rite checks

- Browser-driven PTY reconnect, Ctrl-C, clipboard, and process inspection on
  the target Linux Mint desktop.
- ANSI/VT cursor behavior, Unicode edge cases, OSC hyperlinks, Kitty/Sixel
  capability detection, and image fallback fixtures.
- Startup, idle-memory, redraw, scrollback, and shader-on measurements.

The full suite was also run. It reported `169 passed`, `3 skipped`, and one
unrelated credential-wizard failure caused by a host `GEMINI_API_KEY` value
being auto-discovered instead of consuming the test fixture. No LWA web test
failed.
