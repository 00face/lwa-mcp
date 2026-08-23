# WO-115 — LWA prompt and response separation

## Hypothesis

We believe distinct bounded regions for LWA transcript, prompt editor, status,
and command suggestions will prevent response text from appearing in the input
area and make multiline review predictable; confidence requires prompt text to
remain unchanged while responses stream, resize, scroll, or render graphics.

## Scope

- Establish explicit LWA regions: feed, status, prompt editor, suggestions,
  and footer.
- Keep pipeline/provider responses in the LWA feed only.
- Keep the editable prompt isolated until submission/finalization.
- Make prompt and feed scrolling independent and preserve cursor visibility.
- Reserve modal/suggestion rows so they cannot overwrite prompt rows.
- Define behavior for long lines, multiline paste, resize, and empty responses.

## Acceptance gates

- Streaming output never mutates the LWA prompt buffer or cursor.
- Prompt submission creates a visible, bounded feed event and clears only the
  intended editor state.
- Suggestions and modals never cover the active prompt.
- Selection/copy remains local to the LWA feed or LWA prompt region.

