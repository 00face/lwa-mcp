# WO-055 — Native ASCII Codex Frame

**Status:** Implemented — automated gates pass; operator visual comparison remains
**Parent:** WO-049, WO-054
**Task rite:** [TR-055](../task-rites/TR-055-native-ascii-codex-frame.md)

## Objective

Give native `lwa` a deliberate ASCII terminal frame based on the supplied
wireframe: an outer LWA frame, a contained Codex Feed, a Codex Prompt area, an
LWA Feed band, and an LWA Prompt area.

## Design contract

- The outer frame visibly belongs to LWA and contains the Codex surface.
- Codex output remains the largest region and scrolls within its bounds.
- Codex Prompt is visually distinct from LWA Prompt.
- LWA Feed is a bounded status band and never replaces Codex output.
- The frame degrades cleanly at small terminal sizes without corrupting text.
- Border drawing never injects bytes into the Codex PTY.
- Prompt focus, Tab switching, Enter submission, Ctrl-C, and Esc exit retain
  their current behavior.
- The accessible/plain-text content remains readable without relying on border
  glyphs or color.

## Acceptance gates

1. A fixed-size fake curses screen verifies the complete outer and inner frame.
2. Narrow terminals produce a readable fallback layout rather than exceptions.
3. Codex output is clipped to the feed region and never overwrites prompts.
4. LWA status messages remain bounded and visually separated.
5. Existing prompt-routing and PTY lifecycle tests remain green.
6. A visible operator check confirms parity with the supplied wireframe.

## Non-goals

- No change to Codex’s own rendering or model configuration.
- No graphics protocol support inside the native ASCII frame.
- No replacement of the LWA dashboard or web terminal.
