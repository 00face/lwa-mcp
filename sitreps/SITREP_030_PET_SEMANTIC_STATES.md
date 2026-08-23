# SITREP 030 — Authoritative Codex pet animation states

The pet should communicate workflow state, not merely activity. The semantic
contract is:

- **Idle:** waiting with no active task.
- **Running / Active Processing:** Codex is reasoning, executing commands, or
  writing code. The developer should remain in the active workspace.
- **Needs Input / Waiting:** Codex has paused for approval, an answer, or a
  decision.
- **Ready / Review:** the task completed successfully and unread output is
  ready for developer review.
- **Blocked / Error:** execution failed, was interrupted, or encountered an
  application/provider error.

The current implementation has idle, welcome, action, and completion tracks.
Those are transport-level tracks, not sufficient semantic states. WO-097
therefore introduces a state layer above the frame ranges. Missing tracks must
fall back deterministically (for example, running → action, ready →
completion, needs-input/blocked → idle or text status) instead of looping all
animations indiscriminately.

The critical design boundary is event ownership: Codex/LWA status and PTY
events select the state; the timer only advances frames within the selected
track.
