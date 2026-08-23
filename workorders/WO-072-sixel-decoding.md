# WO-072 — Sixel Decoding

Status: complete

## Objective

Decode supported Sixel image payloads into bounded image frames for native and web compositor paths.

## Scope

- Parse Sixel introducers, raster attributes, color definitions, repeat runs, carriage returns, and line advances.
- Convert decoded pixels into a bounded PNG or RGBA frame.
- Reject malformed, oversized, high-color-count, and resource-exhausting payloads.
- Preserve text fallback for unsupported Sixel variants.

## Safety and performance

- Use strict maximum width, height, pixel count, and decoded byte limits.
- Avoid unbounded repeat-run expansion.
- Enforce a decode time budget or run decoding off the PTY reader.
- Do not place credentials or raw escape sequences in accessible transcripts.

## Acceptance

- Known-good Sixel fixtures decode deterministically.
- Malformed and adversarial fixtures fail safely.
- Decoded frames enter the shared compositor event path.
- Low-resource mode can disable Sixel decoding without affecting text output.

Evidence: bounded Sixel decoding, palette handling, repeat runs, row movement,
PNG conversion, and malformed-payload fallback are implemented in
`image_compositor.py`.
