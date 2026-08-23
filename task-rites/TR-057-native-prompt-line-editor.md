# TR-057 — Native LWA Prompt Line Editor Rite

**Work order:** [WO-057](../workorders/WO-057-native-prompt-line-editor.md)
**Mode:** deterministic editor model, terminal-key normalization, and visual verification

**Current result:** A cursor-aware multiline editor now handles insertion,
navigation, deletion, Ctrl-J, Shift+Enter, and normal submission. Focused and
full application gates pass; the final normal-terminal interaction check is
operator-visible.

Raw and whole-sequence CSI/CSI-u variants are covered, including integer
Backspace, Delete, and Ctrl-J delivery.

## Sequence

1. Capture the current prompt failure with deterministic key streams, including
   arrow, Delete, Backspace, Ctrl-J, Shift+Enter, and normal Enter.
2. Introduce a small testable editor state containing text, cursor index, and
   preferred column for vertical movement.
3. Normalize raw curses codes, CSI sequences, CSI-u sequences, and control
   bytes into editor actions.
4. Implement insertion, cursor movement, deletion, Home/End, and newline
   insertion independently of PTY writes.
5. Submit the editor’s exact multiline payload through the existing Codex or
   LWA route only on normal Enter.
6. Render the active line and cursor without placing literal escape text or
   newline markers into the prompt buffer.
7. Test resize, narrow terminals, scroll state, Codex EOF, and prompt focus
   transitions.
8. Run focused editor/frame tests and the full application suite.
9. Perform the operator-visible normal-terminal editing check.

## Evidence required

- Before/after key-to-action table.
- Exact submitted payload for a multiline prompt.
- Cursor positions before and after navigation/deletion.
- Proof that Ctrl-J and Shift+Enter do not submit early.
- Test totals and visual-gate status.

## Promotion rule

This rite remains open if any key inserts a literal control representation,
acts only at the end of the buffer, submits prematurely, or moves the cursor
visually without changing the editor state.
