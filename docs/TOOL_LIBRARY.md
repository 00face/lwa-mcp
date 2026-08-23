# Persistent Tool Library Architecture

## Purpose

The Lwa MCP tool library converts stable repeated work into reusable, inspectable workflows without silently introducing unrestricted code execution. Its storage is user-level and cross-project, making tools available to any conversation or agent connected to the same Lwa MCP server.

## Storage contract

Default root:

```text
~/.local/share/lwa-mcp/tool-library
```

Override only when necessary:

```bash
export LWA_MCP_TOOL_LIBRARY=/another/private/path
```

The library contains a machine registry, generated Markdown catalog, and one directory per tool. Every entry has a manifest, README, and entrypoint.

## Tool kinds

### Prompt recipe

A prompt recipe is the safe automatic output of pattern detection. Its `prompt_template` contains `{input}` and is executed as a normal routed task. Consent, cost caps, failover, and usage logging therefore remain intact.

`{input}` is the only public recipe variable. Unknown variables, malformed
braces, empty templates, and the internal `{{CONSENSUS_TRANSCRIPT}}` variable
are rejected before a recipe is written or prepared. The consensus transcript
placeholder is created and filled only by the locked consensus synthesis path.

Recipes also use the canonical task vocabulary and quality values:
`quick_response`, `query`, `conversation_compression`, `token_optimization`,
`document_editing`, `sitrep`, `planning`, `consensus`, `verification`,
`coding_aux`, `image_generation`, and `video_generation`; quality is
`economy`, `balanced`, or `high`.

### Script

A script tool stores explicit source supplied by an operator or trusted agent. It is created with:

- `status: draft`
- `approved: false`
- `metadata.review_required: true`

Execution requires both explicit tool approval and the global `allow_reviewed_script_execution` setting. This two-part gate prevents discovery from becoming execution.

## Pattern evidence

`workflow_patterns` retains:

- Stable signature.
- Routed task category.
- Label and description.
- Normalized keywords.
- Occurrence and success counts.
- Confidence.
- First and last observation time.
- Optional project association.
- Generated tool slug, when applicable.

`workflow_observations` retains a prompt hash rather than raw prompt content.

## Automatic creation threshold

A tool is eligible when:

1. Automatic creation is enabled.
2. Occurrences meet `pattern_min_occurrences`.
3. Successful observations meet the same threshold.
4. No tool is already bound to that pattern.

The default threshold is three successful observations.

## Discovery protocol for agents

Before recreating a workflow that appears repetitive:

1. Call `suggest_library_tools` with concrete current context and the matching task category when known.
2. Inspect candidates with `read_library_tool`.
3. Use `run_library_tool` only when the description and triggers match the current request.
4. Continue with ordinary routing when no candidate is sufficiently relevant.
5. Record a stable repeated workflow with `observe_workflow` after successful validation.

A tool’s evidence and confidence are advisory, not proof of correctness.

## Versioning

Updating an existing pattern-bound recipe increments the patch version while preserving its slug and creation time. Disabling a tool preserves its files and evidence. Deletion is intentionally absent from the baseline MCP interface; archival or manual operator action is safer and auditable.
