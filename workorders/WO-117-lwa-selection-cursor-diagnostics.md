# WO-117 — LWA selection and cursor diagnostics

## Hypothesis

We believe privacy-safe input ownership telemetry will identify whether the
left-pane failure is caused by curses decoding, tmux mouse capture, pane focus,
or redraw contention; confidence requires the log to distinguish those layers
without recording prompt contents or secrets.

## Scope

- Instrument cursor-owner transitions and bounded cursor coordinates.
- Record normalized non-text key classes, including Shift-arrow sequences.
- Record mouse press, motion, and release metadata for LWA selection.
- Record selection phases and character counts, never selected text.
- Keep diagnostics low-volume and safe for an ordinary `debug` review.

## Acceptance criteria

- C01–C07 can distinguish editor/cursor behavior from rendering behavior.
- C08–C12 expose a complete or clearly missing mouse drag lifecycle.
- C13–C16 expose native pane ownership and focus requests.
- No telemetry contains prompt text, selected text, credentials, provider
  payloads, or environment values.
- Diagnostics never change input behavior or make the interactive loop fail.
- Focused tests, Ruff, and the full suite pass.

## Explicit non-goals

This work order does not change key bindings, tmux configuration, cursor
visibility, or selection semantics. Those changes follow the evidence.

