# TR-108 — Native focus authority

1. Reproduce the direction-dependent behavior from the launch log.
2. Replace reverse-direction synthetic `send-keys` with direct `select-pane`.
3. Keep exact pane IDs; do not use tmux last-pane history.
4. Add regression assertions for both directions and all supported Tab forms.
5. Run focused tests, lint, and the full suite.
6. Mark the gate complete only after a real Ghostty/tmux operator check confirms
   both directions.

