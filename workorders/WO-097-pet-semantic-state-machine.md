# WO-097 — Semantic Codex pet state machine

## Objective

Make pet animation communicate Codex's actual work state instead of treating
all non-idle frames as a generic action loop.

## Required states

| State | Meaning | Trigger |
|---|---|---|
| `idle` | No active work | No task, response, or overlay is pending |
| `running` | Codex is reasoning, executing, or writing | Prompt accepted; working/status/output event |
| `needs-input` | Codex is waiting for approval, an answer, or a decision | Approval/question/input-required event |
| `ready` | Work completed and output awaits review | Successful completion event |
| `blocked` | Work failed or hit an application error | Error, provider failure, or interrupted task |

## Acceptance criteria

- Exactly one semantic state owns the visible pet track at a time.
- State changes are driven by Codex/LWA events, not timer rotation.
- Every state has a stable fallback when its authoritative track is absent.
- Switching pets preserves the current semantic state and restarts only the
  selected pet's frame sequence.
- No pet graphics or state escape sequences enter the Codex input stream.
- Text-only terminals expose the same state through safe text labels.
