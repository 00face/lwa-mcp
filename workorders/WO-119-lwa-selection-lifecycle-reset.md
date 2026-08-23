# WO-119 — LWA selection lifecycle reset

## Evidence

The latest Ghostty trace proves feed hit-testing works: selections of length
63, 7, 54, and other non-zero lengths are recorded. It also shows a release
with length 0 followed by later selections that reuse the previous range.

## Hypothesis

We believe preserving the anchor after release makes the next mouse press
reuse stale selection state. Resetting the anchor on every new press while
keeping the completed range visible will make each selection independent.

## Acceptance criteria

- Every left-button press inside visible LWA feed content starts a new anchor.
- Motion and release update only that active selection.
- Completed selection remains visible until the next press.
- A click without drag produces an intentional zero-length selection, never a
  range from a prior interaction.
- Feed selection does not alter prompt text or focus ownership.
- Keyboard selection and clipboard behavior remain unchanged.

