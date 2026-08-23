# TR-119 — LWA selection lifecycle reset

1. Add regression coverage for two consecutive selections.
2. Reset the LWA feed anchor on every new left-button press.
3. Preserve the completed range for visual verification after release.
4. Verify press/release without motion produces no stale range.
5. Run focused tests, Ruff, and the full suite.
6. Operator gate: perform two separate drags and confirm each
   `phase=anchor` follows the latest press coordinates.

