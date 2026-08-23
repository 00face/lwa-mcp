# SITREP 045 — LWA selection lifecycle

## Findings

The drag-position mask change succeeded: the trace contains valid LWA anchors
and non-zero selections. Ghostty/tmux is still not emitting explicit motion
records, but release coordinates are sufficient to complete a selection.

The remaining defect is stale-anchor reuse. The implementation intentionally
kept anchors after release to preserve the highlight, but it did not start a
fresh range on the next press.

## Decision

Separate “completed selection remains visible” from “active drag anchor.” A new
press always replaces the anchor; only a press-to-release sequence may produce
the next selected range.

