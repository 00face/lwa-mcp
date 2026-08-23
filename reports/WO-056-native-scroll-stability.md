# WO-056 SITREP — Native LWA Scroll Stability

**Recorded:** 2026-08-21
**Status:** Remediation implemented; operator-visible gate remains

## Situation

Native `lwa` now renders readable Codex output and the ASCII LWA frame, but
the user reports an immediate crash when scrolling.

## Impact

The terminal cannot be safely inspected once output exceeds the visible feed,
which blocks practical use even though startup and prompt rendering succeed.

## Working hypotheses

- Curses mouse-wheel events may arrive as integer key codes and enter an
  unhandled path.
- Scroll-related terminal events may coincide with PTY resize or child EOF.
- The frame may be repainting against stale geometry or a closed PTY.

## Required evidence

The task rite must establish the exact event sequence with deterministic fake
screen tests before claiming the crash is fixed, then confirm behavior in a
real terminal.

## Remediation evidence

- Mouse-wheel and navigation keys now scroll bounded Codex history locally and
  never write to or resize the PTY.
- Unsupported curses integer keys are ignored safely.
- Raw mouse escape sequences are consumed instead of being interpreted as the
  LWA exit key.
- Raw arrow, PageUp/PageDown, and Delete sequences are decoded explicitly;
  Backspace and Delete both remove prompt characters.
- Focused terminal/Codex tests: `19 passed`.
- Full non-visual application suite: `182 passed, 2 warnings`.
