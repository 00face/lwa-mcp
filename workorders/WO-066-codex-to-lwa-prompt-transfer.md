# WO-066 — Codex Response to LWA Prompt Transfer

## Objective

Allow the operator to transfer selected Codex output, or the most recent Codex response when no selection exists, into the LWA Prompt using `Alt+Shift+Enter`.

## Interaction contract

- `Alt+Shift+Enter` is intercepted by the LWA frame and never submitted to Codex.
- If Codex output is selected, copy only the selected range.
- If no selection exists, copy the latest complete Codex response block.
- Insert the text into the LWA Prompt without submitting it.
- Preserve line breaks, code blocks, paths, and literal identifiers.
- Show a LWA Feed confirmation with the transferred character count.

## Safety and accessibility

- Never transfer redacted credential-shaped output in plain form.
- Keep focus on the LWA Prompt after transfer.
- Provide an equivalent visible button and keyboard-accessible action in LWA-Web.

## Acceptance

- Selection transfer works for one line and multiline output.
- No-selection transfer uses the latest response only.
- The LWA Prompt remains editable and reviewable before submission.
- Native and web behavior agree.
