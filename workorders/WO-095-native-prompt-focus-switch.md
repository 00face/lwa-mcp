# WO-095 — Native Prompt Focus Switching

Status: Implementation complete; native visual acceptance open
Priority: High

## Problem

In the native split layout, pressing Tab does not reliably switch between the
LWA and Codex prompt surfaces. Instead, the terminal cursor can move to a
previous cursor location associated with the old shared frame, or Tab can be
forwarded to tmux/Codex.

## Objective

Make LWA the authoritative keyboard-focus owner for the controller pane. Tab
must switch the active prompt between LWA and Codex deterministically, update
the visible cursor immediately, and never inject a Tab byte into the Codex PTY
or restore stale terminal cursor coordinates.

## Required invariants

- LWA controller owns Tab while its pane is focused.
- Native tmux pane focus cannot steal or reinterpret the controller's Tab.
- Tab changes `active_surface` exactly once per key press.
- The newly active editor receives the cursor; the old editor loses it.
- Cursor placement is derived from the active editor and current geometry only.
- No `\x09` is written to the Codex PTY for a focus-switch Tab.
- Suggestions and slash-command completion do not consume the focus-switch key.
- Mouse focus and Tab focus produce the same active-surface state.
- Focus remains stable through redraw, resize, pet placement, and Codex output.

## Acceptance gates

1. **Controller gate:** five Tab presses alternate LWA → Codex → LWA → Codex → LWA.
2. **PTY gate:** a focus Tab produces no child-PTY input.
3. **Cursor gate:** after each switch, the cursor is visible in the selected
   prompt and never appears at the previous shared-frame location.
4. **Suggestion gate:** Tab still switches focus when either pane has slash
   suggestions; completion uses a separate explicit interaction.
5. **Mouse parity gate:** clicking each prompt and pressing Tab yields the same
   focus sequence.
6. **Resize gate:** switch focus before and after a Ghostty/tmux resize without
   cursor drift.
7. **Output gate:** Codex output and pet graphics do not change focus.
8. **Legacy gate:** the same controller behavior works without tmux or graphics.

## Stop condition

Do not fix this by sending cursor movement or Tab sequences into Codex. The
controller must consume the key locally and redraw its own cursor from state.
