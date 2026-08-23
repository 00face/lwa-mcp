# SITREP 043 — LWA selection and cursor diagnostic rite

## Status

WO-117/TR-117 is in progress. The implementation is diagnostic-first because
the same symptom can be produced by four different owners: the LWA editor,
curses mouse decoding, tmux copy mode, or the terminal's redraw behavior.

## Evidence captured

The existing focus log records pane transitions, but it does not record the
cursor owner, normalized navigation keys, mouse press/motion/release phases, or
selection lifecycle. It therefore cannot explain why the left pane's cursor
blinks or why selection is unavailable.

## New measurable signals

The startup log will contain only bounded metadata such as:

```text
cursor owner=lwa row=... column=... visible=true
key raw_class=escape_sequence normalized=shift-left
mouse_event action=press button=left x=... y=...
selection surface=lwa phase=dragging length=...
```

No prompt, selected text, credentials, environment values, or provider output
is recorded.

## Open gates

C01–C07 are automatable in unit tests. C08–C20 remain operator gates because
they require a real terminal, tmux ownership, mouse selection, screen reader,
or resource-pressure observation. The next SITREP should include the actual
metadata trace from a fresh Ghostty session.

