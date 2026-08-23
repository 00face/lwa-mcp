# SITREP 033 — Pet playback order

The authoritative lifecycle is now:

```text
load/switch → welcome (greet) → idle → action/state track → idle
```

- `welcome` plays once when a pet is loaded or switched.
- `idle` is the resting loop after greeting and after transient actions.
- Prompt submission selects the running/action track.
- Successful completion selects the ready/completion track.
- Approval or question events select needs-input.
- Errors select blocked.
- Transient running/ready tracks return to idle when their display cycle ends.

The timer advances frames only; it does not invent semantic transitions.
