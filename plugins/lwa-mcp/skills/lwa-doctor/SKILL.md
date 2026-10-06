---
name: lwa-doctor
description: Diagnose Lwa MCP configuration, MCP startup, provider availability, quota, cost controls, and tool-library health without exposing secrets.
---

Use `$lwa-doctor` followed by the diagnostic scope. Call `router_status`,
`refresh_model_catalog`, `refresh_provider_quotas`, `set_routing_mode`, or the
repository's deterministic doctor commands as appropriate. Report missing
providers separately from total server failure, distinguish quota exhaustion
from configuration and transport failures, and redact secret values.
