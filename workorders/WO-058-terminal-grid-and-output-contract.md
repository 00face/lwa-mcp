# WO-058 — Terminal Grid and Output Contract

## Objective

Make native LWA and LWA-Web preserve the same core PTY text behavior: carriage returns, line feeds, backspace, tabs, bounded history, and responsive redraws.

## Scope

- Native text buffer remains the canonical low-resource behavior reference.
- Web renderer preserves control-character semantics and wraps long lines to the available viewport.
- Accessible transcript remains selectable and copyable.

## Acceptance

- Multiline output remains ordered and readable.
- Carriage-return redraws do not become fragmented lines.
- Long lines wrap instead of being silently truncated.
- Copy and download controls expose the current transcript.

## Status

Implemented in the current rite; browser and native visual review remain open gates.
