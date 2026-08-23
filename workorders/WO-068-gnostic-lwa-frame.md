# WO-068 — Gnostic LWA Frame

## Objective

Give the LWA frame a more gnostic visual identity: an observatory-like interface that communicates attention, transformation, consensus, and passage between LWA and Codex without reducing clarity.

## Visual direction

- Use a restrained celestial palette: midnight, bronze, muted teal, and warm signal accents.
- Frame the Codex Feed as the witnessed working surface.
- Frame the LWA Feed as the interpretive/consensus channel.
- Use subtle geometric sigils, orbital separators, or constellation motifs as non-semantic decoration.
- Make active focus, processing, approval, failure, and ready states visually distinct.
- Keep decorative shaders optional and disabled in low-resource mode.

## Accessibility and performance gates

- Decorative art must be `aria-hidden` and never carry required meaning.
- Text contrast must meet WCAG AA targets.
- Every state must remain understandable in monochrome and screen-reader modes.
- Native fallback must remain legible in plain curses terminals.
- No animation may block input, PTY reads, or transcript updates.

## Acceptance

- A visual review confirms the new identity without reducing terminal readability.
- Native and web frames share the same state vocabulary.
- Low-resource mode removes shaders and retains the complete functional layout.
- Snapshot/visual tests cover ready, processing, consensus, copied, error, and disconnected states.
