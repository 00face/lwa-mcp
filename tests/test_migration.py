import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path("scripts/migrate-from-castor-pollux.sh").resolve()


def _run_migration(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    config_home = tmp_path / "config"
    state_home = tmp_path / "state"
    env = {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        "XDG_CONFIG_HOME": str(config_home),
        "XDG_STATE_HOME": str(state_home),
    }
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def test_migration_preserves_sources_and_protects_destinations(tmp_path):
    old_config = tmp_path / "config" / "castor-pollux" / "router.yaml"
    old_state = tmp_path / "state" / "castor-pollux"
    old_config.parent.mkdir(parents=True)
    old_state.mkdir(parents=True)
    old_config.write_text("consent_mode: paid_only\n", encoding="utf-8")
    (old_state / "twins.env").write_text("OPENROUTER_API_KEY='old'\n", encoding="utf-8")
    (old_state / "router.sqlite3").write_bytes(b"sqlite-placeholder")

    _run_migration(tmp_path)

    new_config_dir = tmp_path / "config" / "lwa-mcp"
    new_state_dir = tmp_path / "state" / "lwa-mcp"
    assert (new_config_dir / "router.yaml").exists()
    assert (new_state_dir / "lwa.env").exists()
    assert (new_state_dir / "lwa.sqlite3").exists()
    assert stat.S_IMODE(new_config_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(new_state_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE((new_state_dir / "lwa.env").stat().st_mode) == 0o600
    assert old_config.exists()
    assert old_state.exists()


def test_forced_migration_creates_replacement_backups(tmp_path):
    old_config = tmp_path / "config" / "castor-pollux" / "router.yaml"
    old_state = tmp_path / "state" / "castor-pollux"
    old_config.parent.mkdir(parents=True)
    old_state.mkdir(parents=True)
    old_config.write_text("consent_mode: paid_only\n", encoding="utf-8")
    (old_state / "twins.env").write_text("OPENROUTER_API_KEY='old'\n", encoding="utf-8")
    (old_state / "router.sqlite3").write_bytes(b"old-db")

    _run_migration(tmp_path)
    (tmp_path / "config" / "lwa-mcp" / "router.yaml").write_text("new\n", encoding="utf-8")
    (tmp_path / "state" / "lwa-mcp" / "lwa.env").write_text("new\n", encoding="utf-8")
    (tmp_path / "state" / "lwa-mcp" / "lwa.sqlite3").write_bytes(b"new-db")

    _run_migration(tmp_path, "--force")

    assert list((tmp_path / "config" / "lwa-mcp").glob("router.yaml.pre-migration-*"))
    assert list((tmp_path / "state" / "lwa-mcp").glob("lwa.env.pre-migration-*"))
    assert list((tmp_path / "state" / "lwa-mcp").glob("lwa.sqlite3.pre-migration-*"))
