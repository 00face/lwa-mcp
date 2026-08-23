# WO-093 Smooth Single-Pet Animation Loop Evidence

Date: 2026-08-22
Host: Linux Mint / Ghostty / tmux

## Implementation checkpoint

The native path uses the verified Ghostty/tmux same-ID replacement path: one
stable Kitty image identity (`9001`) is updated frame-by-frame. LWA clears only
its owned stale IDs (`9001`–`9012`) once before the first placement for a
session or pet reload. It never deletes or clears the image at a loop boundary.

Delete acknowledgements use `q=2`, preventing terminal protocol responses from
reaching the PTY or appearing in either prompt.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Single-instance lifecycle | PASS (automated) | Cleanup is one-time and limited to LWA-owned IDs; regression test verifies no delete on later replacement. |
| Stable image identity | PASS | Native frame placement continues to use image ID `9001`. |
| Loop transition protocol | PASS (automated) | Same-ID frame replacement emits no delete/clear operation; frame 0 is not reintroduced at the tmux loop boundary. |
| Input isolation | PASS | Quiet graphics transmit/delete sequences and existing graphics-response filtering; full suite remains green. |
| Fallback host | PASS | Existing text fallback path is unchanged. |
| Live visual loop | OPEN | Requires operator observation in the actual Ghostty window for duplicate/blink confirmation. |

## Verification

```text
.venv/bin/ruff check ...                         PASS
PYTHONPATH=. .venv/bin/pytest -q                 260 passed, 3 skipped
focused native/pet suite                         62 passed
```

## Operator closeout

Start a fresh `lwa` session in Ghostty and observe the Codex pane for two full
pet cycles. Confirm one pet remains bottom-right, no duplicate is visible, the
loop has no blank/restart blink, and no graphics protocol text enters either
prompt. If the visual gate still fails, capture the result after this fresh
session; do not add another animation protocol before reviewing the lifecycle.
