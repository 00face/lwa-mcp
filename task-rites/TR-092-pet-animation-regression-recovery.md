# TR-092 — Pet Animation Regression Recovery Rite

Work order: `WO-092-pet-animation-regression-recovery.md`

Status: Ready

## Sequence

### 1. Checkpoint

- Record the current source checksum for the compositor, launcher, and pet
  renderer.
- Record the current LWA/Codex runtime versions and pet frame hashes.
- Do not overwrite the current checkpoint during experiments.

### 2. Establish the historical baseline

- Identify the exact prior behavior described as visibly animated.
- If no source snapshot exists, use the operator’s last known launch behavior
  only as an observational baseline, not as an automatic rollback.
- Record whether the baseline had blinking, cursor movement, or protocol text.

### 3. Isolate the three protocols

Use `scripts/pet-animation-matrix.sh` for the operator comparison. It opens
five labeled panes without attaching to Codex input:

- A — terminal-owned animation;
- B — preloaded frame placement;
- C — client replacement with one image ID;
- D — client replacement with unique image IDs;
- E — text fallback control.

- Test terminal-owned `a=f`/`a=a` playback without curses.
- Test preloaded `a=t` plus `a=p` frame switching without curses.
- Test client-driven replacement at a fixed coordinate without deleting the
  visible frame first.
- Capture protocol metadata only; never record image payloads or prompts.

### 4. Host gate

- Run each surviving protocol through Ghostty 1.3.1 and tmux 3.4.
- Confirm tmux passthrough is enabled before the first frame.
- Query the Codex pane geometry before every placement test.

### 5. Input-isolation gate

- Keep Codex focused and type harmless navigation/input during animation.
- Fail immediately on graphics response text, hashes, base64, or altered prompt
  content.
- Fail immediately if the pet follows the cursor or moves panes.

### 6. Recovery decision

- Select the first protocol that passes animation, position, and input gates.
- If the historical behavior is the only animated option but fails isolation,
  do not regress to it; mark the host unsupported and use text fallback.
- Record the decision before changing implementation again.

### 7. Closeout

- Update `reports/WO-092-pet-animation-regression-evidence.md`.
- Add a regression test for the selected protocol shape and frame progression.
- Run the full test suite and one operator visual acceptance session.
