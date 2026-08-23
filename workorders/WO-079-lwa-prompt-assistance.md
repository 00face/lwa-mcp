# WO-079 — LWA Prompt Assistance

Status: ready

## Objective

Expand the LWA prompt into a modern, review-first editor with autocomplete,
safe spell correction, prompt templates, history, and visible semantic
finalization metadata.

## Acceptance

- Autocomplete offers LWA concepts, templates, providers, task modes, and
  slash commands in a pane-local accessible listbox.
- Spell correction is opt-in, reversible, and protects code/path/command spans.
- Suggestions never send text automatically or overwrite the draft silently.
- Draft history, undo/redo, multiline editing, paste, and keyboard navigation
  work on low-resource systems.
- Status reports only counts/modes/hashes; never prompt bodies or secrets.

## Validation

Cover code, media, research, and ambiguous prompts; screen reader announcements;
large paste; slash completion; undo; correction opt-out; and provider failure.
