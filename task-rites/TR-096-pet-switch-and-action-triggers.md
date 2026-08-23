# TR-096 — Pet switch and action-trigger rite

1. Resolve the requested pet name and load only its validated Codex asset.
2. Build immutable playback tracks before mutating the active renderer state.
3. Reset generation, placement, welcome frame, and action sequencing together.
4. Trigger action on prompt submission and completion on the first visible PTY
   response (or LWA consensus completion).
5. Keep fallback text available when Kitty/Ghostty graphics are unavailable.
6. Run Ruff, focused tests, and the full suite; record the result.
