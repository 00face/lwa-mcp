# WO-096 — Codex pet switching and action triggers

## Objective

Make `/pets [name]` replace the currently rendered Codex pet atomically, and
map pet animation tracks to observable LWA/Codex actions without leaking PTY
input or creating a second renderer.

## Acceptance criteria

- `/pets name` validates and loads that exact Codex cache identity, retaining
  the current pet if the requested asset is invalid.
- A successful switch starts the pet's welcome track from frame zero.
- Prompt submission starts an action track; the first visible PTY response
  starts the completion track. LWA consensus completion uses the same track.
- Idle, action, welcome, and completion timing remain independent.
- No pet-control escape sequence is sent to the Codex input PTY.
- A text-only terminal remains functional with the text fallback.

## Verification

Run the focused pet/terminal tests and the full test suite. Manually verify
`/pets <available-name>`, a direct Codex prompt, and an LWA prompt.
