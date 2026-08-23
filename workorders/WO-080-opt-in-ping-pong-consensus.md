# WO-080 — Opt-In Ping-Pong Consensus

Status: ready

## Objective

Add a user-enabled loop in which LWA consensus improves a draft, sends the
reviewed result to Codex, then returns the Codex response to LWA for a bounded
second consensus pass and review.

## Acceptance

- Enabled explicitly from the LWA prompt; default remains one-pass behavior.
- State machine is visible: draft → LWA consensus → Codex → LWA review.
- Maximum turns, timeout, token/cost budget, and cancellation are enforced.
- The returned LWA review appears in the LWA prompt/editor for user approval;
  it is never sent onward automatically.
- Codex output and provider payloads remain redacted in status/transcript.
- Any provider error stops safely with retry/resume controls and no duplicate
  Codex submission.

## Validation

Test success, timeout, quota/provider failure, cancellation, reconnect, tab
close, duplicate delivery, and budget exhaustion.
