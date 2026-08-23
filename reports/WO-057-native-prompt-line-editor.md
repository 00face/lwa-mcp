# WO-057 SITREP — Native LWA Prompt Line Editor

**Recorded:** 2026-08-21
**Status:** Editor redesign implemented; operator-visible gate remains

## Situation

The native LWA frame is readable and scroll-stable, but its prompt is not yet
a normal terminal editor. Character deletion and arrow navigation do not work
reliably, while Ctrl-J and Shift+Enter display newline representations instead
of producing a true multiline editing experience.

## Impact

Users cannot correct text in place, navigate a prompt, or compose multiline
requests naturally. This affects both direct Codex input and LWA-finalized
prompts.

## Root-cause direction

The current prompt is a single append-oriented string. Terminal key sequences
are partially normalized, but there is no cursor index, logical-line model, or
separate editor action for newline insertion versus submission.

## Required evidence

The task rite must replace ad hoc key handling with a testable editor state and
prove exact payload preservation before the interaction gate can close.

## Remediation evidence

- Added a cursor-aware multiline `PromptEditor` with insertion, left/right and
  up/down movement, Home/End, Delete, and Backspace.
- Ctrl-J and Shift+Enter insert actual newline bytes; normal Return submits.
- Raw and whole-sequence Shift+Enter decoding is covered, as are integer
  Backspace, Delete, and Ctrl-J delivery paths.
- Prompt rendering now uses real two-line input regions; newline content is no
  longer replaced with a `|` display marker.
- Focused editor/frame/Codex tests: `23 passed`.
- Full non-visual application suite: `186 passed, 2 warnings`.
