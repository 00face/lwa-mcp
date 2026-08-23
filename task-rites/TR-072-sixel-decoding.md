# TR-072 — Sixel Decoding

Status: complete

1. Establish the bounded Sixel grammar and resource limits.
2. Add parser fixtures for colors, runs, rows, and carriage returns.
3. Convert valid payloads into compositor frames.
4. Add malformed and resource-exhaustion tests.
5. Validate native, web, transcript, and low-resource behavior.

Verification: Sixel fixtures and resource-limit tests pass; graphics remain
separate from accessible text transcripts.
