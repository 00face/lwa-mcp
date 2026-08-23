# WO-076 — Split-Pane Codex and LWA Workspace

Status: complete — web smoke and native conformance passed

## Dependency

Execute after [WO-075](WO-075-codex-pet-parity.md). The layout must consume the
authoritative pet/status contract and must not reintroduce an ASCII substitute.

## Objective

Refactor the workspace so Codex owns a dedicated right-side pane containing its
feed, prompt, slash-command autocomplete, and follow-up controls, while LWA
owns a dedicated left-side pane containing its prompt, pipeline state, and LWA
responses.

## Hypothesis

We believe separating Codex and LWA into stable left/right interaction domains
will prevent prompt/event overlap and let Codex display its native slash-command
follow-ups without LWA overlays hiding them; confidence requires independent
keyboard/mouse focus, clean pane-local scrolling, and successful end-to-end
prompt routing in both surfaces.

## Scope

- Replace the current stacked web layout with a responsive two-pane workspace:
  LWA on the left, Codex on the right.
- Give Codex an isolated terminal viewport, prompt, autocomplete/listbox/modal,
  transcript, and graphics layer that cannot be covered by LWA controls.
- Give LWA an isolated prompt, pipeline/provider status, consensus output, and
  response-transfer controls that cannot write directly into Codex input.
- Preserve tabs, resize, low-resource mode, graphics, pet status, copy/select,
  and accessible transcript behavior.
- Refactor native curses geometry into two pane regions with explicit active
  surface focus, pane-local scroll, mouse selection, and Tab navigation.
- Keep Codex slash commands on the Codex side. LWA may observe status and offer
  transfer actions, but must not intercept or rewrite Codex command follow-ups.
- Collapse to a clearly labeled vertical layout below the responsive width
  threshold without changing ownership or keyboard semantics.

## Accessibility and safety gates

- Each pane has a semantic landmark, accessible name, visible focus state, and
  predictable Tab order: LWA prompt → LWA output → Codex prompt → Codex output.
- Autocomplete and follow-up dialogs stay inside the Codex pane stacking context
  and expose `listbox`/`option` relationships with Escape cancellation.
- Pane-local scroll cannot inject arrow/page keys into the other pane's PTY.
- Screen readers receive pane status and command suggestions, not binary graphics,
  provider secrets, or raw terminal control sequences.
- Resizing, reconnecting, closing tabs, and terminal exit restore focus and do
  not duplicate events or orphan sessions.

## Acceptance

- On wide screens, LWA is visibly and interactively on the left; Codex is on the
  right with its own prompt and slash-command UI unobscured.
- `/pets`, `/permissions`, and every other Codex slash command show follow-up
  input/options inside the Codex pane, without appearing under LWA elements.
- LWA submission runs its pipeline and only transfers the finalized result to
  Codex after explicit user review/send.
- Native and web panes preserve copy/select, mouse interaction, keyboard focus,
  graphics/pets, low-resource behavior, and terminal restoration.
- Narrow layouts remain usable and accessible through a deterministic stacked
  fallback.

## Validation signal

The split-pane smoke matrix records pane ownership, focus transitions, command
menu visibility, independent scroll positions, prompt routing, and session
cleanup. Success requires zero cross-pane key leakage and zero hidden command
menus across web, native, resize, tab, and low-resource cases.

## Execution evidence

- Web CSS now uses a responsive grid: LWA feed/prompt on the left and Codex
  feed/prompt/graphics/autocomplete on the right; narrow screens collapse in a
  deterministic Codex → LWA order.
- Native curses now renders the same left/right ownership model, with pane-local
  cursor placement, mouse focus, Codex selection, and Codex-only scrolling.
- Existing tabs, graphics, pet status, transfer, prompt routing, and slash
  follow-up behavior remain additive.
- Automated result: full suite passes (`234 passed, 3 skipped`); Ruff and
  JavaScript syntax checks pass.
- Browser smoke result: desktop dependency check passed and the headless
  interaction smoke passed with clipboard, pointer, keyboard, and screenshot
  evidence. The screenshot confirmed the wide left/right layout and visible
  accessible controls.
- Native conformance result: Kitty/Ghostty placement was exercised with the
  authoritative Stacky frame and produced a valid Kitty transmit sequence.
  Human visual inspection remains useful for terminal-specific font/theme
  preferences, but no implementation gate remains open.
- Native Codex slash suggestions now occupy a dedicated right-pane region
  directly below the Codex prompt; they no longer pollute the LWA feed.
