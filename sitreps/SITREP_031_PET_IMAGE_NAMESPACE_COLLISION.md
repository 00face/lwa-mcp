# SITREP 031 — Selected pet hidden by shared graphics namespace

## Finding

Codex and LWA run in separate tmux panes, but Kitty/Ghostty graphics image IDs
are global to the terminal display rather than isolated per pane. LWA reused
image ID `9001`, which is also used by Codex's native pet renderer. Codex could
therefore overwrite the LWA image immediately after `/pets` successfully
loaded a different asset, making the switch appear ineffective.

## Remediation

LWA now owns the reserved image namespace beginning at `19001`, including its
cleanup range. The selected Codex pet is still loaded from the requested cache
identity, but its display ID cannot collide with Codex's native pet.

Validation: Ruff passed and 59 focused tests passed.
