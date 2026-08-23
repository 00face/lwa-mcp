# WO-092 — Pet Animation Regression Recovery

Status: Open — regression isolation and controlled recovery

## Problem

The configured Codex pet has valid authoritative animation frames, but the
current Ghostty/tmux native split displays only a static frame. Earlier
operator reports observed visible animation, although it was accompanied by
cursor coupling, flashing, or graphics text leakage.

## Objective

Recover reliable animation without reintroducing prompt corruption, cursor
coupling, pane drift, or uncontrolled redraw loops.

## Required strategy

1. Preserve the current implementation as a diagnostic checkpoint.
2. Reproduce three isolated animation variants:
   - terminal-owned Kitty animation;
   - preloaded frame placement;
   - client-driven frame replacement.
3. Test each variant outside curses, then through the native split.
4. Compare visible frame changes, protocol leakage, and input isolation.
5. Regress only to the last variant that visibly animated if it passes the
   input-isolation and fixed-position gates.

## Rollback decision

A rollback is justified only when:

- the older behavior is reproducibly shown to animate;
- its exact protocol sequence is captured;
- prompt/input leakage is absent or has a contained fix;
- the rollback is isolated to the pet compositor and does not revert pane,
  launcher, or shutdown fixes.

If the earlier behavior animated only by leaking graphics into the active
cursor or prompt, it is not an acceptable rollback target. Recover the
animation mechanism, not its known corruption.

## Acceptance criteria

- At least three visibly distinct frames over five seconds.
- Fixed bottom-right placement in the Codex pane.
- No flashing blank interval or cursor-following.
- No `Gi=`, `OK`, base64, hashes, or graphics protocol text in prompts.
- Codex slash commands, typing, selection, and interruption remain usable.
- Non-graphics terminals retain a stable text fallback.
