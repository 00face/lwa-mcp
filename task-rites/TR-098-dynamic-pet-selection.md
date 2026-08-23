# TR-098 — Dynamic pet selection rite

1. Rediscover valid Codex cache identities for every `/pets` command.
2. Keep selection by safe pet name; never read unrelated configuration data.
3. Build and validate the replacement playback state before mutating display
   state.
4. Clear the LWA-owned image namespace once per replacement and place the new
   pet at the Codex-side coordinates.
5. Preserve the current semantic animation state across the switch.
6. Support explicit names and deterministic wrapping `next` selection.
7. Verify direct selection, cycling, newly discovered assets, and empty cache.
