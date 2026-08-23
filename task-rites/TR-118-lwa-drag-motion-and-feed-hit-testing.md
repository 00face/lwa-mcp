# TR-118 — LWA drag motion and feed hit testing

1. Add a tested helper for the native mouse event mask.
2. Enable position reporting without changing pane bindings.
3. Align selection viewport calculations with `PanelGeometry` feed bounds.
4. Log rejected hit-test phases without content payloads.
5. Run focused selection tests, Ruff, and the full suite.
6. Operator gate: drag across a visible LWA line in Ghostty/tmux and verify
   `press → motion → selected` in `startup.log`.

