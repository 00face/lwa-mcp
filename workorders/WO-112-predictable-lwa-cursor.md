# WO-112 — Predictable LWA cursor

## Hypothesis

We believe a single cursor-owner contract for the LWA pane will make typing,
mouse focus, Alt-arrow pane movement, multiline prompts, and redraws feel
stable; confidence requires zero unexpected focus transitions in a scripted
native key trace and a visible cursor that remains inside the active LWA prompt
row.

## Scope

- Separate logical prompt focus from tmux pane focus.
- Make cursor placement derive from the active editor after every input event.
- Clamp cursor coordinates to the LWA prompt viewport after resize, scroll, and
  multiline edits.
- Treat native Tab/BackTab as five-space insertion and Alt arrows as pane-only
  commands.
- Add diagnostics for cursor owner, active surface, key class, and transition
  result without recording prompt contents.

## Acceptance gates

- LWA typing never moves the cursor into the Codex pane.
- Mouse focus and Alt-arrow focus agree with the active pane.
- Cursor remains visible and bounded after resize, paste, delete, newline, and
  scroll.
- Native traces contain no `focus_next` event for Tab or BackTab.

