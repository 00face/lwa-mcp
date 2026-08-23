# TR-093 — Smooth Single-Pet Animation Loop Rite

Work order: `WO-093-smooth-pet-animation-loop.md`

Status: Automated rites complete; visual acceptance open

## Sequence

### 1. Fresh-session cleanup

- Close the current LWA/tmux session.
- Start a new session with a unique image namespace.
- Delete only LWA-owned stale test IDs from the prior matrix runs.
- Confirm one initial pet placement.

### 2. Lifecycle inspection

- Trace image IDs emitted during startup, `/pets`, resize, and frame changes.
- Confirm the active C path uses one ID only.
- Confirm no preloaded IDs remain visible from B or D matrix tests.

### 3. Loop timing test

- Record frame index and timestamp for two complete cycles.
- Require monotonically advancing frames.
- Require the transition from the final frame to the first playback frame to
  contain no delete, clear, or re-place operation.

### 4. Visual test

- Observe the Codex pane for ten seconds.
- Confirm one pet, fixed bottom-right placement, no duplication, and no blink at
  the loop boundary.

### 5. Input-isolation test

- Type harmless navigation and prompt text while the loop runs.
- Confirm no `Gi=`, `OK`, image IDs, base64 text, or hashes enter the prompt.

### 6. Closeout

- Record evidence in `reports/WO-093-smooth-pet-animation-loop.md`.
- Add a regression test for stale-ID cleanup and loop-boundary sequencing.
- Run the full test suite before marking the rite complete.
