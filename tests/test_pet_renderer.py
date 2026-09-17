import base64
from pathlib import Path

from lwa_mcp.pet_renderer import (
    PetRenderer,
    _png_has_visible_alpha,
    _png_rgba,
    discover_codex_pet_asset,
    discover_codex_pet_names,
    next_codex_pet_name,
    render_configured_pet,
    resolve_pet_name,
    resolve_pet_selection,
)


def test_transparent_animation_timing_frame_is_detected():
    transparent = _png_rgba(1, 1, b"\x00\x00\x00\x00\x00")
    visible = _png_rgba(1, 1, b"\x00\xff\x00\x00\xff")
    assert not _png_has_visible_alpha(transparent)
    assert _png_has_visible_alpha(visible)


def test_pet_name_resolves_from_codex_tui_config(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text('[tui]\npet = "stacky"\nsecret = "must not be read"\n', encoding="utf-8")
    assert resolve_pet_name(config_path=config) == "stacky"


def test_explicit_pet_override_wins_without_exposing_config():
    assert resolve_pet_name(override="stacky", environ={"CODEX_HOME": "/missing"}) == "stacky"
    assert resolve_pet_name(override="../../secret") is None


def test_configured_pet_renders_a_bounded_png_and_text_fallback(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text('[tui]\npet = "stacky"\n', encoding="utf-8")
    asset_dir = tmp_path / "pets"
    asset_dir.mkdir()
    placeholder = PetRenderer().render("stacky")
    assert placeholder is not None
    (asset_dir / "stacky.png").write_bytes(base64.b64decode(placeholder.image.data_base64))
    pet = render_configured_pet(config_path=config, renderer="browser", low_resource=True, asset_dir=asset_dir)
    assert pet is not None
    assert pet.name == "stacky"
    assert pet.image.mime_type == "image/png"
    assert pet.image.byte_length < 250_000
    assert pet.text_fallback
    assert pet.authoritative is True
    assert pet.source == "codex-compatible-asset"
    assert pet.public_json()["name"] == "stacky"


def test_unknown_pet_fails_closed():
    assert PetRenderer().render("not-in-catalog") is None


def test_discovers_codex_owned_frame_cache(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text('[tui]\npet = "stacky"\n', encoding="utf-8")
    frame_dir = tmp_path / "cache" / "tui-pets" / "frame-cache" / "stacky" / "sha256-test" / "frames"
    frame_dir.mkdir(parents=True)
    fixture = PetRenderer().render("stacky")
    assert fixture is not None
    frame = frame_dir / "frame_000.png"
    frame.write_bytes(base64.b64decode(fixture.image.data_base64))
    (frame_dir / "frame_001.png").write_bytes(frame.read_bytes())
    assert discover_codex_pet_asset("stacky", tmp_path) == frame
    pet = render_configured_pet(config_path=config, renderer="browser")
    assert pet is not None
    assert pet.authoritative is True
    assert pet.source == "codex-tui-pet-cache"
    assert pet.asset_id.startswith("codex:stacky:sha256:")
    assert len(pet.animation) == 2


def test_preserves_long_authoritative_animation_cycle(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text('[tui]\npet = "stacky"\n', encoding="utf-8")
    frame_dir = tmp_path / "cache" / "tui-pets" / "frame-cache" / "stacky" / "sha256-test" / "frames"
    frame_dir.mkdir(parents=True)
    fixture = PetRenderer().render("stacky")
    assert fixture is not None
    frame_bytes = base64.b64decode(fixture.image.data_base64)
    for index in range(15):
        (frame_dir / f"frame_{index:03d}.png").write_bytes(frame_bytes)

    pet = render_configured_pet(config_path=config, renderer="ghostty")
    assert pet is not None
    assert len(pet.animation) == 15


def test_explicit_pet_selection_prefers_codex_cache_over_single_asset_dir(tmp_path: Path, monkeypatch):
    from lwa_mcp.pet_renderer import render_configured_pet

    codex = tmp_path / "codex"
    frame_dir = codex / "cache" / "tui-pets" / "frame-cache" / "dewey" / "run" / "frames"
    frame_dir.mkdir(parents=True)
    frame_dir.joinpath("frame_000.png").write_bytes(_png_rgba(1, 1, b"\x00\xff\x00\x00\xff"))
    asset_dir = tmp_path / "lwa-assets"
    asset_dir.mkdir()
    asset_dir.joinpath("dewey.png").write_bytes(_png_rgba(1, 1, b"\x00\x00\xff\x00\xff"))
    monkeypatch.setenv("CODEX_HOME", str(codex))
    monkeypatch.setenv("LWA_PET_ASSET_DIR", str(asset_dir))

    pet = render_configured_pet(override="dewey")

    assert pet is not None
    assert pet.source == "codex-tui-pet-cache"


def test_next_pet_selection_is_dynamic_and_wraps():
    names = ("dewey", "fireball", "stacky")
    assert next_codex_pet_name("dewey", names) == "fireball"
    assert next_codex_pet_name("stacky", names) == "dewey"
    assert next_codex_pet_name("newly-loaded", names) == "dewey"
    assert next_codex_pet_name(None, ()) is None
    assert resolve_pet_selection("2", None, names) == "fireball"
    assert resolve_pet_selection("next", "fireball", names) == "stacky"
    assert resolve_pet_selection("reload", "fireball", names) is None
    assert resolve_pet_selection("missing", None, names) is None


def test_stack_alias_preserves_configured_identity():
    pet = PetRenderer().render("stack")
    assert pet is not None
    assert pet.name == "stack"


def test_discovers_all_cached_codex_pet_names(tmp_path: Path):
    for name in ("dewey", "fireball", "stacky"):
        frame_dir = tmp_path / "cache" / "tui-pets" / "frame-cache" / name / "sha256-test" / "frames"
        frame_dir.mkdir(parents=True)
        fixture = PetRenderer().render("stacky")
        assert fixture is not None
        (frame_dir / "frame_000.png").write_bytes(base64.b64decode(fixture.image.data_base64))

    assert discover_codex_pet_names(tmp_path) == ("dewey", "fireball", "stacky")


def test_authoritative_cache_accepts_new_codex_pet_identity(tmp_path: Path):
    config = tmp_path / "config.toml"
    config.write_text('[tui]\npet = "dewey"\n', encoding="utf-8")
    asset_dir = tmp_path / "pets"
    asset_dir.mkdir()
    fixture = PetRenderer().render("stacky")
    assert fixture is not None
    (asset_dir / "dewey.png").write_bytes(base64.b64decode(fixture.image.data_base64))

    pet = render_configured_pet(config_path=config, renderer="browser", asset_dir=asset_dir)

    assert pet is not None
    assert pet.name == "dewey"
    assert pet.authoritative is True
    assert pet.source == "codex-compatible-asset"
