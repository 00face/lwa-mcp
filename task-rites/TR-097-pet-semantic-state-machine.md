# TR-097 — Semantic pet-state rite

1. Define the five-state enum and a single state-to-track selector.
2. Normalize Codex cache frame ranges into semantic tracks once per pet load.
3. Emit `running` on accepted work and active execution/output.
4. Emit `needs-input` for approval, question, and decision overlays.
5. Emit `ready` on successful completion and `blocked` on errors/failures.
6. Return to `idle` only after the state has been displayed and no work is
   pending.
7. Preserve the state across `/pets` switches and restart the new track at
   frame zero.
8. Add event-to-state and fallback tests before changing visual placement.
