# TR-107 — Native binding cleanup rite

1. Snapshot only the keys LWA owns.
2. Register cleanup with an idempotent guard.
3. Restore prior bindings or unbind keys created by LWA.
4. Kill only the Codex pane created by the current launch.
5. Test normal, error, interrupt, and partial-startup exits.
