# Agent and Conversation Integration

## Objective

Make the Lwa MCP library available in every compatible conversation without copying scripts into each project.

## MCP registration

Register one user-level MCP server:

```toml
[mcp_servers.lwa]
command = "/absolute/path/lwa-mcp/.venv/bin/lwa-mcp"
```

Every conversation launched by that client can then search and run the same persistent library.

Codex-facing workflows use explicit skills: `$lwa` for orchestration and
`$lwa-doctor` for diagnostics. The native `/skills` command remains distinct.
For a dashboard URL outside Codex skill invocation, run
`./.venv/bin/lwa-router doctor --show-dashboard-url` in the repository.

## Recommended agent instruction

Add this doctrine to the client or project instructions where appropriate:

```text
Use Lwa MCP for auxiliary routing and reusable workflows. When a task resembles repeated prior work, call suggest_library_tools before rebuilding it. Inspect a candidate with read_library_tool and run it only when its description, task, and triggers match. After a recurring workflow succeeds and is validated, call observe_workflow with a stable name and concrete description. Never approve or execute a script tool without reviewing its source.
```

## Pragmatic relevance standard

Reuse a tool when it meaningfully reduces repeated reasoning or mechanical editing while preserving current project constraints. Do not force a library tool onto a task merely because a keyword matches. File paths, versions, exact user decisions, current requirements, and tests always override a generic recipe.

## Manual discovery outside MCP

The generated catalog can be inspected directly:

```bash
less ~/.local/share/lwa-mcp/tool-library/CATALOG.md
```

The CLI provides the same persistent view:

```bash
lwa-router library search "current task description"
```
