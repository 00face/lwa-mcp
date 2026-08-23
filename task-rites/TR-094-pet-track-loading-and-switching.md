# TR-094 — Pet Track Loading and Switching Rite

Work order: `WO-094-pet-track-loading-and-switching.md`

Status: Automated rites complete; visual acceptance open

## Sequence

### 1. Asset inventory

- Enumerate every configured Codex pet and its authoritative frame cache.
- Record frame count, dimensions, visible/transparent frames, and hashes.
- Search for any companion timing, state, or trigger metadata.
- Do not infer that all frame ranges share the same semantic state without
  recording the evidence.

### 2. Track contract

- Define the playback-state schema.
- Define idle, welcome, action, and completion track contracts.
- Define fallback behavior when metadata or a track is unavailable.
- Add unit fixtures for short, long, transparent, corrupt, and missing caches.

### 3. Loader implementation

- Normalize authoritative frames once.
- Preserve source order and hold the last visible frame over transparent timing
  frames.
- Produce an immutable candidate playback state.
- Keep terminal rendering unaware of cache-specific frame partition rules.

### 4. Event scheduler

- Implement explicit event-to-track mapping.
- Add one active action at a time, cooldown, cancellation, and return-to-idle.
- Verify inactivity never advances into action, welcome, or completion tracks.

### 5. Atomic switch

- Load and validate the candidate before mutating active state.
- Swap the generation atomically.
- Cancel old callbacks and reject stale generation updates.
- Clean only the previous LWA-owned image identity.
- Place the candidate’s first frame and resume its idle scheduler.

### 6. Crash and fallback tests

- Switch through every available pet repeatedly.
- Switch to invalid, corrupt, missing, and partially readable assets.
- Switch during action playback, resize, prompt submission, and Codex output.
- Confirm the current pet remains visible when a candidate fails.
- Confirm text fallback on unsupported hosts.

### 7. Operator visual rite

- Launch a fresh `lwa` session in Ghostty.
- Confirm welcome plays once, then short idle only.
- Submit a harmless prompt and confirm exactly one action track plays.
- Complete a task and confirm completion plays once, then idle resumes.
- Switch among at least three configured pets five times.
- Confirm no duplicate, blink, crash, prompt leakage, or stale pet remains.

### 8. Closeout

- Record asset inventory and trigger limitations.
- Record automated and operator evidence in a WO-094 report.
- Run the full test suite.
- Close only gates supported by evidence; leave native visual gates open when
  they require operator observation.
