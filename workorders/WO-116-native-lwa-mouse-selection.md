# WO-116 — Native LWA mouse selection

## Hypothesis

We believe a selection controller that consumes press, drag-motion, and
release events consistently will make LWA feed selection as predictable as
ordinary terminal selection; confidence requires successful copy of short
lines, wrapped lines, multiline ranges, and scrolled content in Ghostty/tmux.

## Findings being remedied

- SGR drag-motion codes are parsed but ignored by the native selection path.
- Selection highlight is cleared immediately after release, so the operator
  cannot verify the selected range.
- Wrapped display rows are mapped to source lines, but the mapping is not
  tested across horizontal and vertical drag movement.
- tmux mouse ownership and curses mouse ownership are not explicitly exposed
  in diagnostics.
- The LWA prompt is intentionally outside feed selection, but the boundary is
  not clearly communicated or tested.

## Acceptance criteria

- Button press creates an anchor in the LWA feed.
- Left-button motion updates the focus point continuously, including SGR motion
  codes 32/33 and their terminal variants.
- Release preserves a visible highlight until the next selection or explicit
  copy completion.
- Copy output is correct for same-line, wrapped-line, multiline, and scrolled
  selections.
- Feed selection never changes prompt text, prompt cursor, or pane focus.
- Prompt selection behavior is explicitly documented; clicking the prompt
  focuses it without starting feed selection.
- Native diagnostics report mouse event class and selection state without
  recording selected text.
- tmux/curses integration tests and a real Ghostty operator test pass.

## Accessibility gate

Selection must not depend on pixel-perfect dragging. Provide keyboard copy and
an explicit non-dragging selection path while preserving mouse selection.

