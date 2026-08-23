# WO-103 — Pane-local scroll and selection model

Give LWA and Codex independent viewport models with explicit feed, prompt,
selection, and scrollbar ownership. Native Codex scrolling remains Codex-owned;
LWA must not enter tmux copy mode while drawing or switching pets.

Acceptance: scrolling one pane cannot change the other pane's offset; mouse
selection is stable across wrapped lines; focus returns to the prompt at the
current logical cursor without requiring manual scroll recovery.
