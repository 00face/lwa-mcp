# TR-024B - Cached Handshake Rite

**Entry:** WO-024A provides event correlation, and the full handshake probe is
available.  
**Action:** Review and implement `scripts/handshake/`; capture cold/warm
timings; validate required tools, resources, and prompts.  
**Check:** Run the full diagnostic and cached smoke paths in isolated temp
profiles.  
**Promote when:** warm sessions reuse a matching manifest and stale/mismatched
caches fail closed.  
**Rollback:** remove only the warm-session adapter; retain the full diagnostic
script as the supported path.

**Result - 2026-08-08:** Partial. Cache identity, fail-closed validation,
provider-free reporting, and reviewed wrappers are complete. Live MCP discovery
still times out, so warm-session acceptance remains open.
