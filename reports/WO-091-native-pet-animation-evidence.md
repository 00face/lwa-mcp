# WO-091 Native Pet Animation Evidence

Date: 2026-08-22
Host: Linux Mint / Ghostty 1.3.1 / tmux 3.4
Configured pet: `dewey`

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Baseline | PASS | Ghostty 1.3.1, tmux 3.4, configured pet `dewey`. |
| Asset | PASS | 72 cached PNG frames found across cache variants; LWA selected a bounded 12-frame animation with 11 distinct payloads. Primary frame validates as PNG. |
| Protocol shape | PASS | `a=t` transmit and `a=p` placement sequences are correctly formed, quiet, and terminated. |
| Host passthrough | PARTIAL | Native launcher enables tmux `allow-passthrough`, mouse, and status-off before Codex starts. Detached non-GUI tmux probe cannot prove Ghostty’s visual handling. |
| Pane geometry | PARTIAL | The native path queries the Codex pane geometry and computes bottom-right placement. A real Ghostty resize observation remains required. |
| Input isolation | OPEN | Automated terminal input isolation has not yet proven that every host path remains free of graphics leakage during animation. |
| Temporal animation | FAIL | Live observation reports the pet remains static; frame switching is not visible in Ghostty/tmux. |
| Fallback | PASS | Text fallback remains available when native graphics are unavailable. |

## Current conclusion

The asset layer is not the blocker. The current failure is specifically the
Ghostty-through-tmux rendering behavior: preloaded `a=p` placement does not
produce visible frame changes on this host. No further compositor protocol
should be introduced until an isolated host probe determines whether Ghostty
or tmux is dropping the frame switch.

## Required operator observation

Launch `lwa` in Ghostty and observe:

1. Pet remains bottom-right of the Codex pane after typing.
2. Pet visibly changes through at least three frames in five seconds.
3. No `Gi=`, `OK`, base64, hashes, or graphics text reaches either prompt.
4. Resize Ghostty once and repeat the three checks.

The temporal gate has now failed. Capture the exact host probe output next;
do not switch protocols again without recording that evidence.
