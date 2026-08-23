# WO-113 — Resource budget and graceful degradation

## Hypothesis

We believe explicit budgets for redraw frequency, retained transcript lines,
PTY reads, image frames, and background tasks will keep LWA usable on a 3–4 GiB
system; confidence requires a sustained native session staying within the
declared memory/CPU envelopes while output, pets, and resize events are active.

## Scope

- Define low-resource defaults and configurable ceilings.
- Bound Codex/LWA transcript buffers and discard only the oldest display data.
- Coalesce redraw requests and avoid repainting when no visible state changed.
- Ensure pet/image work is cancellable and never blocks input handling.
- Cancel and await background tasks during shutdown.
- Add a diagnostic snapshot showing counts, queue sizes, frame rate, and memory
  without exposing prompts, environment values, or credentials.

## Acceptance gates

- No unbounded list, queue, task, or image-frame growth in a long session.
- Input latency remains bounded while Codex streams output.
- Optional graphics disable cleanly under pressure; text mode remains usable.
- Resource-limit tests pass without requiring a graphical desktop.

