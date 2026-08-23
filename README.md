# Lwa MCP — Model Router and Persistent Tool Library v0.4.1

Lwa MCP is a local-first Model Context Protocol server that routes auxiliary work to suitable configured models, bootstraps provider credentials through a protected first-run wizard, enforces spending consent and quotas, detects repeated successful workflows, and turns stable patterns into documented reusable tools. Paid and user-pays routes are disabled by default: a caller must explicitly allow the billing class and local configuration must allow it before preflight can select that route. Confirmation remains a separate execution gate.

It is intended to sit beside Codex, SOL, Terra, Luna, or another primary engineering agent. Lwa MCP handles document editing, SITREP writing, planning, consensus, conversation compression, token optimization, verification, quick queries, coding support, image-generation routing, and recurring workflow automation without requiring the operator to select a provider manually for every call.

## Included provider pipelines

Google Gemini, OpenAI/ChatGPT, OpenRouter, Groq, Mistral, Cloudflare Workers AI, SiliconFlow, Venice, Pollinations, Cohere, Replicate, Stability AI, NVIDIA Build/NIM, Z.AI, Aion Labs, ZenMux, Cerebras, BLACKBOX AI, and Puter.

Most text services share one audited OpenAI-compatible adapter. Official OpenAI image/video generation uses a dedicated media adapter; Gemini, Replicate, and Stability retain dedicated adapters because their request and result formats differ. Image generation is routed by capability, so any configured provider/model pair that advertises `image` remains eligible.

## Core routing behavior

- Scores task affinity, capabilities, context headroom, quality, billing class, local caps, and availability; an explicit `preferred_providers` list is honored in order, skipping ineligible providers.
- Merges live provider catalogs with deliberately scored seed models where compatible model discovery is available.
- Supports three switch-confirmation modes:
  - `always_ask` (`always` alias): require preflight approval for every route.
  - `paid_only`: authorize free and free-quota preflights automatically; paid and Puter user-pays routes require approval.
  - `automatic` (`never` alias): authorize every eligible preflight automatically while continuing to enforce local caps.
- Permits high-quality escalation to premium specialist models when the quality score justifies the additional cost.
- Forbids dynamic failover while Working is active; a failed locked route stops and requires a new preflight.
- Stores route decisions, provider failures, tokens, latency, known cost, quota observations, and workflow evidence in local SQLite.
- Disables seed models for providers whose first live discovery attempt fails, labels those providers experimental, and leaves configured-only providers explicitly unverified rather than treating them as failures.
- Keeps secrets in `~/.local/state/lwa-mcp/lwa.env` and never returns them through MCP or dashboard APIs.

## Persistent tool library

The persistent library was introduced in v0.2.0 and remains outside any single repository:

```text
~/.local/share/lwa-mcp/tool-library/
├── README.md
├── CATALOG.md
├── registry.json
└── tools/
    └── <tool-slug>/
        ├── tool.yaml
        ├── README.md
        └── run.py
```

This XDG user-data location lets later MCP-enabled conversations and projects discover the same tools.

### How pattern detection works

1. Successful routed work is recorded as a privacy-preserving workflow observation. Raw prompts are not stored in the pattern ledger; Lwa MCP retains a hash, task type, normalized keywords, success state, optional project name, and an operator-supplied workflow summary when available.
2. Similar observations are clustered by task and keyword overlap. Supplying `workflow_name` and `workflow_description` creates a stronger deterministic identity.
3. After the configured number of successful observations—three by default—the detector creates a prompt-recipe tool when automatic creation is enabled.
4. The generated tool receives:
   - A versioned manifest.
   - A human-readable README.
   - Trigger phrases, tags, evidence count, confidence, origin, project metadata, and safety status.
   - An executable Python convenience wrapper.
   - A searchable entry in `registry.json` and `CATALOG.md`.
5. Prompt recipes always execute through Lwa MCP’s normal model router, confirmation gates, quotas, and ledger.

Automatically cataloged arbitrary scripts do **not** execute by default. Script entries begin as drafts, require explicit approval, and also require `allow_reviewed_script_execution: true` before Lwa MCP will run them.

### Cross-conversation doctrine

An MCP client can use the library from any conversation by calling:

```text
suggest_library_tools
search_tool_library
read_library_tool
run_library_tool
```

For recurring work, the client can call `observe_workflow`. Lwa MCP also observes work completed through `run_prepared_task` automatically. Providing these optional fields improves specialization:

```text
workflow_name
workflow_description
project
workflow_tags
```

## Strict preflight before “Working…”

### Canonical task and prompt syntax

Every public task boundary uses the exact `TaskKind` values listed by
`syntax_contract_resource` and CLI help. Quality accepts only `economy`,
`balanced`, or `high`; prose labels such as `"provider connectivity smoke
test"` and values such as `low` are rejected before routing. Specialized
consensus, image, and video requests use their dedicated preparation tools.

Text preparation tools also accept the explicit `reasoning_effort` labels
`instant`, `medium`, and `high`. These are Lwa controls, separate from
`quality`: `instant` maps deterministically to the OpenAI-compatible `none`
setting, while `medium` and `high` map to their same-named provider settings.
The request is locked in preflight and is rejected when the selected model does
not advertise that effort. Lwa does not enable provider-side automatic model
switching, and paid/user-pays routes remain governed by the existing consent
and configuration gates.

Public prompt recipes accept `{input}` only. `{{CONSENSUS_TRANSCRIPT}}` is an
internal-only placeholder owned by locked consensus synthesis.

Lwa MCP uses a mandatory two-phase execution contract:

1. `prepare_task`—or any specialized task tool—finalizes the prompt, estimates and locks the token budget, selects all model routes, evaluates quotas and consent, and records the plan. It makes no provider completion call.
2. When `working_may_begin` is `false`, call `approve_preflight` with the returned confirmation token. Approval still does not execute the task.
3. Only after `working_may_begin` is `true` may the client display **Working...** and call `run_prepared_task` with the single-use plan token.

Consensus uses the same contract. `build_consensus` preselects every eligible
free/free-quota voter, the synthesis model, and the synthesis template. Paid and
user-pays models are not consensus voters. A provider failure returns
`repreflight_required`; no new model is chosen while Working is active.

```text
prepare_task → [approve_preflight] → Working... → run_prepared_task
```

A host application may display its own built-in activity spinner while the host is processing a tool call. MCP servers cannot suppress host-owned UI. Lwa guarantees the ordering of its provider calls, lifecycle fields, CLI output, dashboard ledger, and agent-authored **Working...** status.

### Structured terminal feedback

The standalone router CLI now shows the host Codex identity, the locked Lwa route,
the optimization phase, provider usage, and an explicit return to Codex:

```bash
LWA_CODEX_MODEL=gpt-5.6-luna LWA_CODEX_REASONING=medium \
  ./.venv/bin/lwa-router run token_optimization "Condense this prompt"
```

To request provider reasoning effort through the Lwa route:

```bash
./.venv/bin/lwa-router run coding_aux "Review this patch" \
  --reasoning-effort high --allow-paid
```

`LWA_CODEX_REASONING` and `--codex-reasoning` remain display-only host identity
labels. They do not change Codex's host-owned model; use `--reasoning-effort`
or the matching MCP tool argument for the Lwa provider route.

The same identity can be supplied per invocation with `--codex-model` and
`--codex-reasoning`. Use `--json` for the legacy machine-readable output. The
MCP host remains authoritative for its primary model; Lwa cannot discover or
change that host-owned selection unless the host passes these labels in. Every
completed routed result also includes a `display` object with the Lwa provider,
exact model, billing class, task phase, token counts, formatted response, and
the model/control surface that follows it.

### Telemetry view

For the persisted local activity ledger:

```bash
./.venv/bin/lwa-router telemetry \
  --codex-model gpt-5.6-luna \
  --codex-reasoning medium
```

During a routed CLI execution, the terminal shows the same trace inline:
preflight, locked route, provider execution, optimization/compression phase,
completion, token usage, actual and estimated spend, latency, returned quota
headers, and Codex handoff. Optimization telemetry deliberately reports when
reduction measurement is unavailable; it does not claim a token reduction just
because an optimization task was requested.

### Model tiers, subscriptions, and credential pools

Run the ranked model list with:

```bash
./.venv/bin/lwa-router tiers
```

The list is sorted by `free_plan_max_tokens`, descending. Those values are
operator-declared because providers generally do not expose account-plan token
limits through model discovery. Each row also reports `pro_plan_max_tokens`,
the provider subscription plan/status, and the provider's monthly token limit.

Provider plans are configured without storing secrets in YAML:

```yaml
providers:
  gemini:
    subscription_plan: Gemini Pro
    subscription_status: active
    api_key_env: GEMINI_API_KEY
    api_key_envs: [GEMINI_API_KEY_1, GEMINI_API_KEY_2]
    billing_api_key_env: GEMINI_BILLING_API_KEY
```

`api_key_env` and `api_key_envs` form the generation-key pool; Lwa uses the
first configured key. `billing_api_key_env` is reserved for quota/billing
probes. The same configuration works for OpenAI-compatible providers, and the
existing single `api_key_env` configuration remains valid.

## Install

```bash
cd lwa-mcp
./scripts/install.sh
```

The installer accepts `--no-key-wizard` for unattended setup, `--with-dev` to
include test/development dependencies, `--upgrade-pip` when pip itself should
be refreshed, and `--venv PATH` to place the environment elsewhere. On
Windows, run `scripts\\install.bat` with the same options. After installation,
activate the environment and use the launch commands:

```bash
source .venv/bin/activate
lwa
lwa-web
```

`lwa` now follows two terminal conventions only: if the current host can split
or otherwise place a second Codex surface, the bridge runs there; otherwise
LWA opens Codex in a second terminal window and keeps the controller in the
current terminal. The second terminal owns the real, unmodified Codex PTY, so
Codex keeps its own modals, slash-command completion, pets, selection, and
graphics. Supported launchers are detected from the active host and include
Ghostty, Kitty, WezTerm, GNOME Terminal, Konsole, Terminator, Alacritty,
Guake, Tabby, Wave, and generic `x-terminal-emulator`/`xterm` fallbacks where
available. Hosts with neither split nor launcher support are unsupported in
this mode. Use `lwa frame --fallback` only for the explicit compatibility
frame.

On Linux, Ghostty exposes reliable CLI new-window automation but not a stable
external split-pane API. When `tmux` is installed, Lwa therefore bootstraps a
lightweight tmux session inside the current Ghostty terminal and creates the
Codex split there. Set `LWA_GHOSTTY_SPLIT=window` to force the documented
second-window behavior instead.

The installer applies executable permissions to the Linux launchers and keeps
credential/state permissions under Lwa's protected `0700`/`0600` policy. It
does not install a standalone `index.html` entrypoint.

The Observatory remains the dashboard at `/`. The additive graphical Codex
workspace is available at `/codex` or through `lwa-web`. It uses a local PTY,
bounded terminal history, an adaptive canvas renderer, and optional shader
effects; enable Low Resource mode to keep the effects disabled and cap redraw
cost on smaller systems.

The installer creates a virtual environment and initializes:

```text
~/.config/lwa-mcp/router.yaml
~/.local/state/lwa-mcp/lwa.env
~/.local/state/lwa-mcp/lwa.sqlite3
~/.local/share/lwa-mcp/tool-library/
```

The environment file is created atomically with mode `0600`, and its containing state directory is restricted to `0700`. On the first interactive run, the installer launches a credential wizard.

The wizard:

- Checks the current Codex/process environment for recognized provider variables.
- Reads Codex `model_providers.*.env_key` references and recognized MCP environment maps.
- Checks only recognized keys in Codex and current-project `.env` files; it does not recursively search the home directory.
- Shows discovered and newly pasted values in full for confirmation. Input is intentionally echoed rather than hidden.
- Writes the final `~/.local/state/lwa-mcp/lwa.env` atomically without erasing unrelated custom entries.

Because values remain visible in terminal scrollback, do not run the wizard while screen sharing. Re-run it at any time:

```bash
./.venv/bin/lwa-router keys
# or
./scripts/configure-keys.sh
```

Then inspect provider and library readiness:

```bash
./.venv/bin/lwa-router doctor
```

### Migrate the previous Castor & Pollux baseline

The migration script copies existing configuration, secrets, and the SQLite ledger into the Lwa MCP namespace without deleting the old files. Run it before installation when practical:

```bash
./scripts/migrate-from-castor-pollux.sh
./scripts/install.sh
```

When Lwa files already exist, the script preserves them. To replace them while creating timestamped backups first:

```bash
./scripts/migrate-from-castor-pollux.sh --force
```

Review the copied configuration afterward because provider catalogs and free allocations can change.

## Register the MCP server

The MCP process uses standard input/output:

```bash
./.venv/bin/lwa-mcp
```

Example Codex configuration:

```toml
[mcp_servers.lwa]
command = "/absolute/path/lwa-mcp/scripts/codex-mcp-entrypoint.sh"
```

When Codex starts through this launcher, it starts the MCP server without
waiting for the auxiliary dashboard. Set `LWA_MCP_START_DASHBOARD=1` when the
dashboard should be launched by the same process; otherwise use
`./scripts/run-dashboard.sh` separately. This keeps the MCP handshake from
being delayed by dashboard readiness.

For Codex plugin workflows, use `$lwa` or `$lwa-doctor`; these are explicit
skills rather than native slash commands. For the dashboard URL outside Codex,
run `./.venv/bin/lwa-router doctor --show-dashboard-url`.

Restart the client and verify these primary tools are available:

```text
prepare_task
approve_preflight
run_prepared_task
route_task                 # preparation alias
smart_complete             # preparation alias; never executes in v0.4.1
confirm_and_run            # approval alias; never executes in v0.4.1
quick_response
answer_query
verify_work
compress_conversation
optimize_prompt
edit_document
write_sitrep
plan_work
build_consensus
generate_image
set_switch_confirmation
refresh_model_catalog
refresh_provider_quotas
router_status
```

Read-only MCP resources and a host-side preparation prompt are also exposed:

```text
lwa://status
lwa://catalog
preflight_guidance
```

Tool-library interfaces:

```text
list_library_tools
search_tool_library
suggest_library_tools
read_library_tool
run_library_tool
create_library_tool
register_script_tool
approve_library_tool
disable_library_tool
observe_workflow
analyze_repeated_workflows
rebuild_tool_catalog
library_status
```

## CLI library access

```bash
# Browse active tools
./.venv/bin/lwa-router library list --status active

# Search by current work
./.venv/bin/lwa-router library search "normalize liquid glass CSS controls" \
  --task document_editing

# Inspect a tool and its README
./.venv/bin/lwa-router library show normalize-liquid-glass-controls

# Prepare and then execute a prompt recipe; CLI prints preflight before Working...
./.venv/bin/lwa-router library run normalize-liquid-glass-controls \
  --input "Apply the workflow to these files and requirements..."

# Feed a large input through standard input
cat project-notes.md | ./.venv/bin/lwa-router library run project-sitrep --input -

# Explicitly record a recurring workflow
./.venv/bin/lwa-router library observe \
  --name "Project release SITREP" \
  --description "Create an evidence-bound release SITREP from tests, changes, and blockers." \
  --task sitrep \
  --project "My Project" \
  --tag release

# Re-evaluate the pattern ledger
./.venv/bin/lwa-router library analyze
```

## Dashboard

```bash
./scripts/run-dashboard.sh
```

The Codex launcher starts the dashboard automatically and prints the URL on
startup. If you need to start it manually, use:

```bash
./scripts/run-dashboard.sh
```

The dashboard displays provider state, local caps, token and cost usage, observed quotas, route decisions, reusable tools, evidence counts, confidence, and repeated workflow patterns. It can refresh catalogs and trigger pattern analysis.

See [docs/AUTOMATION.md](docs/AUTOMATION.md) for locked local telemetry and
explicit zero-payload provider-probe timers. Live checks remain opt-in.

Keep the dashboard on loopback unless an authenticated reverse proxy is added.

## Library settings

These defaults appear in `router.yaml`:

```yaml
auto_detect_patterns: true
pattern_min_occurrences: 3
pattern_similarity_threshold: 0.68
auto_create_library_tools: true
auto_activate_prompt_tools: true
suggest_library_tools: true
max_library_suggestions: 5
allow_reviewed_script_execution: false
```

Set `auto_activate_prompt_tools: false` to create new recipes as drafts. Set `auto_create_library_tools: false` to retain pattern detection while requiring manual creation. Keep reviewed-script execution disabled unless the script source has been audited.

## Billing doctrine

Lwa MCP distinguishes:

- `free`: the provider reports zero model price.
- `free_quota`: a no-charge developer allocation or promotional quota may apply, but limits can change.
- `user_pays`: Puter shifts model cost to the authenticated Puter user and is not labeled free.
- `paid`: calls may consume API credits or subscription allowance.
- `unknown`: pricing cannot be established safely and confirmation is recommended.

Seed model IDs are starting points, not promises of permanent availability. Run `doctor` and refresh catalogs after installation.

## Important limitations

- No universal provider quota API exists. The dashboard combines local usage, configured caps, provider-returned headers, and supported official balance probes.
- Dollar enforcement is exact only when pricing and usage are available. Conservative request caps remain important for opaque providers.
- Repetition detection is deterministic and local; it does not infer that two semantically unrelated tasks are identical merely because they share a task category.
- Auto-generated recipes are starting tools. Their confidence and evidence remain visible so an agent can choose whether reuse is pragmatic.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/TOOL_LIBRARY.md`](docs/TOOL_LIBRARY.md)
- [`docs/AGENT_INTEGRATION.md`](docs/AGENT_INTEGRATION.md)
- [`docs/PROVIDERS.md`](docs/PROVIDERS.md)
- [`docs/SECURITY.md`](docs/SECURITY.md)
- [`docs/CODEX_SETUP.md`](docs/CODEX_SETUP.md)
- [`projectdoctrine.md`](projectdoctrine.md)
- [`docs/OPERATOR_QUICKSTART.md`](docs/OPERATOR_QUICKSTART.md)
- [`testcase.md`](testcase.md)
- [`sitreps/SITREP_000.md`](sitreps/SITREP_000.md)
- [`sitreps/SITREP_010.md`](sitreps/SITREP_010.md)
- [`workorders/WO-006-integration-failure-inoculation.md`](workorders/WO-006-integration-failure-inoculation.md)
