# SITREP 044 — LWA drag motion and feed hit testing

## Result

WO-118/TR-118 implementation is complete. Native curses now requests
`REPORT_MOUSE_POSITION` in addition to button events, and LWA selection uses
the same feed viewport geometry as the renderer.

## Automated evidence

- Focused terminal/editor tests: 35 passed.
- Full suite: 288 passed, 3 skipped, 2 warnings.
- Ruff and diff checks: clean.

## Operator gate

Start a fresh LWA session in Ghostty/tmux and drag across visible LWA feed
text. The log should now show:

```text
mouse_event action=press ...
mouse_event action=motion ...
selection surface=lwa phase=anchor length=0
selection surface=lwa phase=dragging ...
selection surface=lwa phase=selected length=...
```

If motion still does not appear, the remaining owner is terminal/tmux mouse
forwarding rather than LWA's curses mask. If `reason=outside-feed` or
`reason=no-visible-line` appears, the next fix is coordinate/layout-specific.

