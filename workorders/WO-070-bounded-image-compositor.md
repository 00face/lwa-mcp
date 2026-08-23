# WO-070 — Bounded Image Compositor

## Objective

Provide a dedicated, bounded image path for Codex graphics without allowing image payloads to corrupt terminal text, block PTY reads, or claim unsupported rendering.

## Scope

- Decode safe Kitty image payloads into browser-displayable frames.
- Bound image bytes, frame count, and metadata.
- Emit graphics as separate events from text transcripts.
- Keep native curses on an explicit fallback path until host placement is safe.

## Acceptance

- Supported PNG/JPEG/GIF/WebP Kitty payloads become image events.
- Oversized or malformed payloads become safe diagnostics.
- Image data never enters the accessible text transcript.
- Web displays bounded image frames without blocking terminal input.
- Native LWA reports graphics received and remains readable.
