# WO-102 — Panel renderer boundary

Separate text layout, cursor drawing, pet compositing, modal rendering, and
terminal escape emission. A frame render must be a pure layout result plus a
bounded list of output effects; pet animation must never move the text cursor
or mutate prompt state.

Acceptance: rapid pet animation causes no cursor blink, prompt movement,
scroll reset, modal activation, or leaked graphics acknowledgement.
