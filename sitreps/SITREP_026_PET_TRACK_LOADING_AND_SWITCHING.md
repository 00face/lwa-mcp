# SITREP 026 — Pet Track Loading, Action Triggers, and Switch Stability

Date: 2026-08-22
Status: Analysis complete; implementation gates open
Scope: Native LWA terminal pet renderer

## Situation

The authoritative Codex cache is available and healthy. The current Dewey
cache contains 72 ordered PNG frames. LWA now loads the complete bounded
sequence and holds the previous visible frame over fully transparent timing
frames. This removed the visible blink, but two regressions remain:

1. Idle playback is longer than intended.
2. Switching pets can terminate the terminal frame instead of completing a
   safe pet transition.

## Evidence

| Observation | Finding |
|---|---|
| Authoritative cache | 72 frames are available for each locally cached pet examined. |
| Current idle partition | `frames[0:6] + frames[24:28] + frames[48:54]` produces 16 idle frames. |
| Current action partition | Three inferred 16-frame tracks are selected only after prompt submission. |
| Trigger metadata | No action/idle manifest or timing metadata exists beside the cached PNGs. |
| Switch path | `/pets` calls `refresh_independent_pet()` synchronously from the input loop. |
| Reload mutation | The active frame lists and placement state are mutated during reload rather than swapped atomically. |
| Error containment | Pet loading/rendering errors are not fully isolated from the curses interaction loop. |
| Regression tests | Pet and native-frame focused tests pass; no end-to-end `/pets` switch test currently exercises a running curses session. |

## Assessment

### Idle duration

The current partition treats three separated regions as idle. That is an
incorrect assumption for the cache: the first region is the safe base idle
track, while later regions are alternate poses or transition frames associated
with action sequences. The default idle track should be the shortest stable
front-facing loop (`frames[0:6]`) until authoritative trigger metadata exists.

### Switching crash

Pet switching currently performs asset discovery, PNG validation, animation
partitioning, state replacement, and native image cleanup in the synchronous
input path. A failure at any point can leave `native_pet_frames`,
`native_pet_track`, `native_pet_index`, and `native_pet_placed` describing
different pets. The next render tick then indexes or places inconsistent state.

The safe design is a transaction:

```text
/pets request
    -> validate and fully prepare candidate off the active state
    -> if preparation fails: retain current pet and report the error
    -> atomically swap one immutable PetPlaybackState
    -> clear only the previous LWA-owned image IDs
    -> place candidate frame 0
    -> resume idle playback
```

## Recommended architecture

1. Introduce an immutable `PetPlaybackState` containing identity, all visible
   frames, idle frames, action tracks, current track, index, generation, and
   placement signature.
2. Move cache parsing and transparent-frame normalization into the pet
   renderer. The terminal frame should consume a validated state, not infer
   track boundaries itself.
3. Default idle to the six-frame base loop. Keep inferred action tracks
   disabled unless a trigger selects them.
4. Add a small action event queue with explicit events: prompt submitted,
   Codex response received, tool activity, approval interaction, and idle
   timeout. Apply a cooldown so one event cannot restart an action repeatedly.
5. Switch pets by candidate-state preparation followed by one atomic swap.
   Never clear the active state before the candidate has loaded successfully.
6. Catch and redact pet-load failures at the command boundary; log the
   exception to the existing LWA debug log while retaining the old pet.
7. Add a running-session switch harness covering valid switch, invalid pet,
   missing frame, resize during switch, and switch during an active action.

## Gates

| Gate | Status | Required evidence |
|---|---|---|
| Correct short idle loop | Open | Idle uses only the intended base frames and does not enter action tracks automatically. |
| Triggered action playback | Open | Each explicit event selects one action track, then returns to idle. |
| Atomic pet switch | Open | Valid switch never crashes and leaves exactly one visible pet. |
| Invalid switch containment | Open | Missing/invalid pet reports an error while the current pet continues. |
| Resize/switch race safety | Open | Resize during loading does not index stale state or duplicate image IDs. |
| Prompt isolation | Green baseline | Existing graphics-response filtering and stale-ID cleanup remain intact. |

## Decision

Do not add more timing constants or animation protocols in the terminal loop.
The next work order should implement `PetPlaybackState` and atomic switching,
then set the six-frame idle loop and add the event queue. This addresses the
two reported failures at their source and prevents further animation changes
from destabilizing pet switching.
