# TR-041 - Pipeline Manager and Data-Free Pipeline Intern Rite

**Entry:** A route may be selected before endpoint accessibility is known.
**Action:** Inspect local configuration first; optionally probe only provider
health/model metadata, never task prompts.
**Check:** Verify no `RouteRequest` is created by status checks, secrets are
redacted, and obvious inaccessible routes are blocked before completion.
**Promote when:** all configured services have provider-specific zero-payload
probe fixtures and bounded cached status evidence.
**Rollback:** disable automatic probing for the affected provider and retain
the last known status; never fall back to sending task data as a probe.
