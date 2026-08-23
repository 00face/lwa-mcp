# WO-078 — Predictable LWA and Codex Selection

Status: complete — explicit selection and copy controls implemented

## Objective

Make mouse selection and copying deterministic on both sides of the split
workspace while preserving keyboard and screen-reader workflows.

## Acceptance

- LWA feed and Codex transcript expose explicit Select and Copy actions.
- Selecting output never focuses or writes into either prompt.
- Copy uses clipboard APIs when available and leaves a visible manual-selection
  fallback when unavailable.
- Codex canvas remains a display surface; accessible transcript is the stable
  selectable source of truth.
- Native selection remains pane-local and does not alter Codex PTY input.

## Validation

Test empty feed, multiline output, long lines, active scrolling, clipboard
failure, keyboard activation, screen-reader labels, and cross-pane focus.

## Evidence

Web LWA feed and Codex transcript now expose explicit Select and Copy controls.
Clipboard failure selects the relevant text for manual copying. Existing
native pane-local selection remains unchanged and does not write into prompts.
