# WO-067 — Codex Output Color and Syntax Theme

## Objective

Improve Codex output readability with stable semantic colors and optional syntax-aware highlighting.

## Scope

- Preserve ANSI colors where they are safe and meaningful.
- Add semantic colors for headings, status, errors, warnings, tool calls, paths, and code fences.
- Detect common code fences and apply lightweight language-aware highlighting where feasible.
- Keep a plain-text fallback for unsupported syntax, narrow terminals, screen readers, and low-resource mode.

## Constraints

- Color must never be the only signal; use labels, symbols, or structure too.
- Do not interpret arbitrary output as executable code.
- Do not expose secrets through highlighted or copied output.
- Avoid a heavyweight parser dependency for the native terminal.

## Acceptance

- ANSI output remains readable when color is disabled.
- Common Python, JavaScript/TypeScript, JSON, YAML, shell, and Markdown blocks receive useful highlighting when supported.
- Copying output returns clean text without escape sequences.
- Reduced-motion, high-contrast, and screen-reader paths remain usable.
