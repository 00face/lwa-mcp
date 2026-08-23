# TR-099 — Panel controller rite

1. Write state-transition tests before moving code.
2. Define immutable panel state and one reducer for focus, viewport, prompt,
   modal, pet, and lifecycle changes.
3. Add adapters for embedded curses and native tmux.
4. Route every input event through the reducer.
5. Keep current behavior behind the adapter until parity tests pass.
6. Remove duplicate key branches only after native and embedded traces match.
