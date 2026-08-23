# TR-046 — Cross-project varied-prompt parity rite

**Purpose:** exercise the shared LWA lifecycle with varied prompts from at least
two project roots while keeping provider spend and claims bounded.

## Preparation matrix

Use these canonical fixtures. They are contract inputs, not product evidence:

| Task | Prompt fixture | Assertion |
|---|---|---|
| `quick_response` | `Reply with exactly READY.` | Response is exactly `READY` when executed |
| `query` | `Name the primary color in: blue.` | Response contains `blue` |
| `conversation_compression` | `Compress this to one sentence: The cat sat on the mat.` | Non-empty, shorter result |
| `token_optimization` | `Shorten this instruction while preserving the literal API name: LWA MCP.` | `LWA MCP` remains present |
| `document_editing` | `Rewrite for clarity without changing the path: /tmp/example.` | Path literal remains present |
| `sitrep` | `Write a two-line status report for: catalog pass; handshake pass.` | Both facts remain present |
| `planning` | `Give exactly three ordered steps for checking a provider connection.` | Three ordered steps |
| `verification` | `Verify this claim: 2 + 2 = 4.` | Claim is classified correctly |
| `coding_aux` | `Review this pseudocode for a missing null check: value.name.` | Review identifies the risk or states why it is safe |

Run `consensus`, `image_generation`, and `video_generation` as prepare-only
cases unless the operator explicitly authorizes their required route and
capability. Do not use the prompt matrix to authorize paid or user-pays work.

## Procedure

1. Run TR-045 from the LWA root and record a host-level metadata PASS or a
   typed restricted-boundary result.
2. For each project root, call the corresponding public preparation tool with
   the task and fixture. Record status, phase, selected provider/model,
   billing class, plan token presence (never the token), and
   `working_may_begin`.
3. Assert that preparation makes zero completion calls.
4. Execute only the approved free/free-quota subset. Record actual provider,
   model, usage, response presence, and provenance.
5. Repeat the same matrix from a second project root. Compare lifecycle and
   schema fields, not exact prose.
6. Inject one safe failure: use an unsupported structured-output request or a
   deliberately unavailable provider. Confirm a bounded failure and no hidden
   reroute.
7. Redact and save the evidence bundle.

## Acceptance

- Every public text task kind is prepared successfully or fails with a typed,
  actionable contract error.
- At least one free/free-quota execution completes from each of two projects.
- The exact-provider/model/billing result is recorded for every completion.
- No prompt, credential, authorization header, or plan token is written to the
  evidence artifact.
- A provider failure stops the locked run and requires repreflight.
- Media and consensus checks remain preparation-only unless separately approved.

## Evidence artifact

`cross-project-prompt-parity.json` containing project root, task, fixture ID,
prepare status, execution status, route/provenance metadata, structural
assertions, and redacted failure classification.

