---
name: lwa-optimize
description: Optimize a prompt or conversation through Lwa MCP without weakening task constraints or exposing secrets.
---

Use `$lwa-optimize` followed by the prompt or conversation and its constraints.
Call `optimize_prompt` or `compress_conversation`; preserve the original
objective, token and cost controls, and secret-redaction rules.
