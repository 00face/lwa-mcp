# TR-091 — Native Pet Animation Diagnostic Rite

Work order: `WO-091-native-pet-animation-protocol.md`

Status: Ready to execute

## Rite sequence

### 1. Freeze the baseline

- Close the active LWA/tmux session.
- Record Ghostty version, tmux version, terminal dimensions, and configured
  pet name.
- Do not modify Codex configuration or cached assets.

### 2. Prove the asset layer

- Enumerate the selected pet’s cached frames.
- Hash the first, middle, and last frame.
- Confirm the hashes differ and each frame passes PNG validation.

### 3. Prove protocol support outside curses

- Run a minimal isolated Kitty protocol probe in a temporary tmux session.
- Test one static image, one preloaded `a=p` switch, and one terminal-driven
  animation only if the host reports support.
- Capture stdout/stderr separately; never attach the probe to Codex input.

### 4. Prove pane geometry

- Query the Codex pane’s left, top, width, and height.
- Place a single test marker at the calculated bottom-right coordinate.
- Resize the Ghostty window and repeat once.

### 5. Prove input isolation

- Run Codex with an empty prompt.
- Animate for five seconds while typing harmless navigation keys.
- Assert the prompt contains no `Gi=`, `OK`, base64 fragments, frame IDs, or
  graphics control text.

### 6. Select one protocol

- If terminal-owned animation passes, use it and stop.
- Otherwise, if preloaded frame placement passes, use it with a bounded client
  timer and stable coordinates.
- Otherwise, mark native animation unsupported and use the text fallback.

### 7. Acceptance observation

- Visually confirm three or more distinct frames.
- Confirm no blink, jump, cursor-following, prompt corruption, or pane drift.
- Record the result in a WO-091 evidence report before further code changes.

## Evidence artifacts

- `reports/WO-091-native-pet-animation-evidence.md`
- Redacted protocol trace with payload data removed.
- Frame hash summary.
- Host capability and pane geometry summary.
- Pass/fail result for each gate.

## Rite failure policy

One failed gate identifies the next investigation layer. It does not authorize
another compositor rewrite. Three consecutive failures at the same host gate
close native animation for that host and activate the documented fallback.
