# TR-078 — Predictable LWA and Codex Selection

Status: complete

1. Define pane ownership and selection source-of-truth.
2. Add explicit Select/Copy controls with accessible names.
3. Preserve normal text selection and prevent prompt mutation.
4. Add clipboard failure and manual-selection fallback.
5. Verify web and native focus, scroll, multiline, and empty-state behavior.

## Result

Steps 1–5 are implemented. Full automated verification passed with 235 tests
passing and the accessible control contract intact.
