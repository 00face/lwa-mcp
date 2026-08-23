# TR-055 — Native ASCII Codex Frame Rite

**Work order:** [WO-055](../workorders/WO-055-native-ascii-codex-frame.md)
**Mode:** wireframe implementation and terminal-safe verification

**Current result:** The native ASCII frame regions, bounded layout, narrow
fallback, and fake-screen geometry gates are implemented. Full application
verification passes; the final wireframe comparison is operator-visible.

## Sequence

1. Translate the supplied wireframe into named native regions:
   `LWA Frame`, `Codex Feed`, `Codex Prompt`, `LWA Feed`, and `LWA Prompt`.
2. Define minimum dimensions and a narrow-terminal fallback before editing the
   renderer.
3. Draw borders using safe ASCII characters first, with Unicode box drawing
   only when the terminal advertises Unicode support.
4. Keep Codex output, LWA status, and prompt input as separate bounded buffers.
5. Verify cursor placement and clipping after every resize.
6. Verify Tab, Enter, Ctrl-C, Backspace, and Esc behavior through fake-screen
   tests.
7. Run focused terminal-frame tests and the full non-visual application suite.
8. Perform an operator-visible comparison against the supplied wireframe.

## Evidence required

- Region geometry at normal and narrow sizes.
- No PTY bytes caused by border repainting.
- Prompt routing remains unchanged.
- Output is readable with colors disabled and by screen-reader transcript.
- Test totals and any visual-only gates are recorded.

## Rollback

Restore the current simple curses headings while retaining the normalized PTY
stream and crash containment from WO-054.
