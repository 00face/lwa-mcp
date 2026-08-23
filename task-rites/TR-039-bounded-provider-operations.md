# TR-039 - Bounded Provider Operations Rite

**Entry:** WO-031 observed 1,720 live catalog refreshes.
**Action:** Integrate the catalog guard with doctor, startup, and proof paths.
**Check:** Warm hit is zero network calls; stale cache is scoped and bounded.
**Promote when:** two warm runs show no repeated provider discovery.
**Rollback:** use explicit bounded cold discovery and retain call counts.
