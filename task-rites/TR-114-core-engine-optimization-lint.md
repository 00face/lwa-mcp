# TR-114 — Core-engine optimization lint

1. Run Ruff and complexity/static checks over the core engine allowlist.
2. Classify findings as correctness, allocation, blocking-I/O, duplication, or
   intentional compatibility behavior.
3. Write characterization tests for each risky hot path.
4. Apply measured, small refactors one engine at a time.
5. Re-run lint, focused tests, benchmarks, and the full suite.

