# BP-001: v0.4.1 Release Baseline

This battleplan coordinates WO-001 through WO-005. The release is a
compatibility-hardening release, not a provider redesign.

1. Complete lifecycle, consent, and tool-library metadata tests.
2. Run static checks and the full test suite in an environment containing the
   declared development dependencies.
3. Resolve P1 provider, security, storage, dashboard, and MCP findings with
   mocked/offline tests first.
4. Refresh operator documentation and the current SITREP from actual results.
5. Build and inspect wheel, source directory, ZIP, TAR.GZ, and SHA-256 files in
   a clean temporary home.

The release cannot be called production-verified while dependency installation,
full tests, or clean-home packaging remain unexecuted.
