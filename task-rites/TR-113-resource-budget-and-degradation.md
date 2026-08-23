# TR-113 — Resource budget and graceful degradation

1. Measure baseline CPU, RSS, redraw rate, retained lines, tasks, and image
   frames during idle and streaming sessions.
2. Set low-resource defaults and explicit upper bounds.
3. Add coalesced redraw, bounded retention, and cancellation guards.
4. Exercise output floods, pet animation, resize storms, and shutdown.
5. Verify text-only fallback and record before/after measurements.

