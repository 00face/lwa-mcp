# SITREP 032 — Codex and LWA pet ownership boundary

## Decision

Codex pets belong exclusively to the native Codex pane. LWA must not forward
LWA-side `/pets` commands into Codex or mutate Codex's native pet state.

Codex-side `/pets` is now allowed to pass through the normal Codex prompt path.
In native split mode, that means the real Codex pane receives and renders its
own slash-command menu and selected pet.

LWA-side pet rendering is intentionally separate and currently reports that
its independent catalog is not loaded. A future LWA pet engine may use its own
asset namespace, state machine, and commands without sharing Codex cache state
or graphics IDs.

## Amendment

The operator selected the reliable compatibility path: LWA now renders a
Codex-compatible pet mirror at the Codex-side coordinates. This is explicitly
an LWA-owned display mirror, not native Codex graphics passthrough. `/pets` in
the LWA prompt selects the mirror; it does not send a pet command into the
Codex PTY.
