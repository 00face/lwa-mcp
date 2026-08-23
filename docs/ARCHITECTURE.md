# Architecture

## Components

```text
Codex / MCP client
       │ stdio
       ▼
FastMCP server (`server.py`)
       │
       ├── task doctrine (`prompts.py`)
       ├── provider catalog (`catalog.py`)
       ├── router and consent (`routing.py`, `consent.py`)
       ├── provider adapters (`providers/`)
       ├── workflow detector (`patterns.py`)
       ├── persistent tool library (`tool_library.py`)
       └── SQLite usage and pattern ledger (`db.py`)
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
FastAPI dashboard          XDG tool-library files
(`dashboard.py`)           (`~/.local/share/lwa-mcp/`)
```

## Routing sequence

1. `RouterService.build_request` binds task doctrine and workflow metadata.
2. `prepare_task` normalizes line endings without changing prompt semantics and locks the final prompt hash. It uses the configured seed/live catalog already in memory; live catalog discovery is an explicit control-plane operation, not hidden preflight work.
3. Catalog, credential, quota, capability, context, cost, quality, and consent evaluation occurs during preflight. If no candidate survives, the bounded error identifies the blocking gates without exposing prompt or credential values.
4. `Router._score` selects the exact provider and model; consensus preflight selects all voters and the synthesis route.
5. `PreflightStore` creates single-use execution and optional confirmation tokens. The dashboard records the token budget, route roles, and lock state without storing raw prompts or tokens.
6. The client may announce `Working...` only when `working_may_begin=true`.
7. `run_prepared_task` consumes the plan and executes only its locked route or consensus graph. It performs no catalog refresh, prompt optimization, consensus planning, or model selection.
8. A provider failure returns `repreflight_required`. No dynamic fallback or model switch occurs during the active Working phase.
9. The request ledger stores a prompt hash, provider result, tokens, latency, and known cost.
10. Completed work enters the pattern detector unless it came from a library tool.

Live catalog refresh is bounded per provider by page and model limits. An
offline pipeline status check never performs network I/O, and normal preflight
does not refresh the catalog implicitly.

The host application's own generic spinner is outside MCP protocol control; the contract governs Lwa provider calls, lifecycle responses, CLI output, dashboard state, and agent-authored status text.

## Tool-library sequence

1. `PatternDetector` normalizes workflow keywords and creates or matches a stable signature.
2. `UsageDB` updates occurrence, success, confidence, project, and tool-binding evidence.
3. When thresholds are satisfied, `ToolLibrary.create_prompt_tool` creates a safe routed recipe.
4. `suggest_library_tools` ranks active entries by task, token overlap, trigger text, evidence, and confidence.
5. `run_library_tool` expands `{input}` and submits the resulting prompt through ordinary routing and consent.
6. Script entries are treated separately and cannot execute until approved and globally enabled.

## Why preflight routes are announced

Every selected model is reported before provider execution. `always_ask` requires approval for all plans; `paid_only` requires approval for paid and user-pays plans; `automatic` authorizes preflight automatically while retaining caps. The legacy `always` and `never` inputs remain accepted as aliases. None of these modes permits a new routing decision after Working begins.

Codex users reach Lwa through explicit skills such as `$lwa` and `$lwa-doctor`.
The dashboard URL remains a CLI operation via `lwa-router doctor
--show-dashboard-url`; it is not registered as a plugin slash command.

## Consensus

`build_consensus` chooses independent providers by excluding each earlier provider, gathers reviews, and routes a synthesis pass. Doctrine requires dissent and uncertainty to remain visible. Paid consensus is disabled unless the caller allows it.

## Extension points

Add an OpenAI-compatible provider in YAML without Python changes. Add a specialized provider by implementing `ProviderAdapter.complete`, optionally `list_models`, and registering it in `providers/__init__.py` and the adapter literal.

Add new library tool kinds only with explicit lifecycle, review, and execution controls. Automatic pattern detection should continue producing prompt recipes rather than arbitrary executable code.
## Credential bootstrap

`lwa-router init` creates the protected environment template and, when attached to an interactive terminal, invokes the visible-input credential wizard. Discovery is deliberately bounded to recognized variables in the current process, Codex provider `env_key` references, Codex MCP environment maps, and fixed Codex/project `.env` locations. The wizard never writes to MCP stdout because it runs before server registration or through the independent `lwa-router keys` command.

The final file is replaced atomically at `~/.local/state/lwa-mcp/lwa.env` with mode `0600`; state and config directories use mode `0700`. Runtime loading disables dotenv interpolation so credential bytes are preserved exactly.
