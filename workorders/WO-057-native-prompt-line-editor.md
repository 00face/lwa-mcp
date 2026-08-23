# WO-057 — Native LWA Prompt Line Editor

**Status:** Implemented — automated key-dispatch gates pass; operator-visible editor gate remains
**Parent:** WO-056
**Task rite:** [TR-057](../task-rites/TR-057-native-prompt-line-editor.md)
**SITREP:** [WO-057 SITREP](../reports/WO-057-native-prompt-line-editor.md)

## Objective

Make the native LWA Codex and LWA prompts behave like a normal terminal line
editor while preserving semantic finalization for LWA prompts.

## Required behavior

- Printable text inserts at the cursor, not only at the end.
- Left/right arrows move the cursor across lines and columns.
- Up/down arrows navigate visual or logical prompt lines.
- Backspace deletes the character before the cursor.
- Delete removes the character at the cursor.
- Home/End move to the logical line boundaries.
- Ctrl-J inserts a real newline into the prompt buffer.
- Shift+Enter inserts a real newline into the prompt buffer.
- Normal Enter submits the complete multiline prompt.
- Newline characters are sent as newline bytes, never as a literal `\\n` or
  display marker.
- Codex direct input and LWA-finalized input retain their separate routes.
- The cursor is visibly placed at the true editing location.

## Safety and accessibility

- Prompt editing never writes to the PTY until submission or direct-input
  action requires it.
- The accessible transcript and prompt labels expose multiline content without
  leaking secrets.
- The editor remains usable when colors and Unicode box glyphs are unavailable.
- Terminal resize does not corrupt the buffer or cursor index.

## Acceptance gates

1. Unit tests cover insertion, cursor movement, multiline insertion, Delete,
   Backspace, Home, End, arrows, and submission.
2. Raw CSI, CSI-u, and control-byte variants map to the same editor actions.
3. The submitted payload exactly preserves intended newlines.
4. Fake-screen tests verify visible cursor placement across multiple lines.
5. Existing PTY, scrolling, frame, accessibility, and crash tests remain
   green.
6. An operator-visible check confirms normal terminal editing in both prompt
   surfaces.

## Non-goals

- Full shell/readline emulation, history search, or completion menus.
- Changes to Codex’s internal TUI.
- Changes to the LWA-Web browser editor unless shared protocol behavior requires
  it.

## Rollback

Retain the current bounded prompt buffer and disable unsupported editing keys,
while preserving safe PTY lifecycle handling.
