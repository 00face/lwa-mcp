# Reproducible Lwa sandbox release

Use Linux Mint/Ubuntu with rootless Podman. Keep Docker Hub and Cosign credentials outside the repository.

1. Install `podman uidmap slirp4netns fuse-overlayfs`, then confirm `podman info` reports rootless, cgroup v2, and seccomp.
2. Copy `config/sandbox.example.yaml` to a private deployment path and replace the image with the approved full digest.
3. Set `LWA_COSIGN_IDENTITY` and `LWA_COSIGN_ISSUER` to the approved signer values. Never use wildcards.
4. Pull the exact digest, verify it with Cosign, generate Syft SBOM and structured Grype JSON, and run the constrained Podman probe.
5. Set `LWA_EVIDENCE_DIR` to durable storage with restricted permissions. The rite pipeline writes an atomic, mode-0600 evidence manifest there.
6. Run the rite with `policy_path`; it will bootstrap the signer policy, probe, and evidence collector before the agent starts.
7. Promote only through an approved pull request. Direct pushes and automatic merges remain disabled.

Record the image digest, tool versions, UTC timestamps, command exit codes, evidence hashes, scanner database version, and the final verification result. Rehearse these steps on a clean machine before changing the approved digest.
