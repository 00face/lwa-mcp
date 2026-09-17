"""Independent, bounded LWA pet catalog and renderer."""

from __future__ import annotations

import base64
import hashlib
import os
import re
import struct
import zlib
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .image_compositor import ImageFrame

_PET_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
_MAX_PET_ANIMATION_FRAMES = 96
_STACKY = (
    "................",
    "....oo....oo....",
    "...o##o..o##o...",
    "..o##########o..",
    ".o##@######@##o.",
    ".o############o.",
    ".o############o.",
    "..o##########o..",
    "...o########o...",
    "....o######o....",
    "....o##oo##o....",
    "...o##....##o...",
    "..o##......##o..",
    ".o##........##o.",
    "................",
    "................",
    "................",
)


@dataclass(frozen=True, slots=True)
class PetDefinition:
    name: str
    alt: str
    sprite: tuple[str, ...]
    palette: Mapping[str, tuple[int, int, int, int]]
    text_fallback: str


@dataclass(frozen=True, slots=True)
class PetFrame:
    name: str
    alt: str
    text_fallback: str
    image: ImageFrame
    renderer: str
    source: str = "lwa-catalog-placeholder"
    asset_id: str = ""
    authoritative: bool = False
    animation: tuple[ImageFrame, ...] = ()

    def public_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "alt": self.alt,
            "text_fallback": self.text_fallback,
            "renderer": self.renderer,
            "source": self.source,
            "asset_id": self.asset_id,
            "authoritative": self.authoritative,
            "frame": self.image.public_json(),
            "animation": [frame.public_json() for frame in self.animation],
        }


class PetSemanticState(StrEnum):
    """User-facing work state represented by a Codex pet."""

    IDLE = "idle"
    RUNNING = "running"
    NEEDS_INPUT = "needs-input"
    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class PetPlaybackState:
    """Validated, immutable playback tracks for one authoritative pet."""

    name: str
    frames: tuple[ImageFrame, ...]
    idle: tuple[ImageFrame, ...]
    welcome: tuple[ImageFrame, ...]
    actions: tuple[tuple[ImageFrame, ...], ...]
    completion: tuple[ImageFrame, ...]
    needs_input: tuple[ImageFrame, ...]
    blocked: tuple[ImageFrame, ...]
    generation: int = 0


def build_pet_playback_state(pet: PetFrame, *, generation: int = 0) -> PetPlaybackState:
    """Normalize one pet into stable tracks before it reaches the TUI."""
    frames = tuple(pet.animation or (pet.image,))
    if len(frames) >= 72:
        # The Codex cache has no manifest. These ranges are isolated here so
        # the terminal loop never has to infer semantic tracks.
        idle = frames[0:6]
        welcome = frames[24:28]
        actions = (frames[8:24], frames[32:48])
        completion = frames[56:72]
    else:
        idle = frames
        welcome = ()
        actions = ()
        completion = ()
    return PetPlaybackState(
        pet.name,
        frames,
        idle or frames,
        welcome,
        actions,
        completion,
        welcome,
        (),
        generation,
    )


def pet_track_for_state(playback: PetPlaybackState, state: PetSemanticState) -> tuple[ImageFrame, ...]:
    """Select one semantic track with deterministic safe fallbacks."""
    if state is PetSemanticState.RUNNING:
        return playback.actions[0] if playback.actions else playback.idle
    if state is PetSemanticState.NEEDS_INPUT:
        return playback.needs_input or playback.welcome or playback.idle
    if state is PetSemanticState.READY:
        return playback.completion or playback.welcome or playback.idle
    if state is PetSemanticState.BLOCKED:
        return playback.blocked or playback.idle
    return playback.idle


PET_CATALOG: dict[str, PetDefinition] = {
    "stacky": PetDefinition(
        name="stacky",
        alt="Stacky, the configured Codex pet",
        sprite=_STACKY,
        palette={
            ".": (0, 0, 0, 0),
            "o": (37, 74, 52, 255),
            "#": (121, 210, 143, 255),
            "@": (8, 18, 12, 255),
        },
        text_fallback=" /\\_/\\\n( o.o )\n > ^ < ",
    ),
}

# Codex installations have used both names for this pet family. They share
# the same LWA-owned asset while preserving the configured public identity.
PET_CATALOG["stack"] = PetDefinition(
    name="stack",
    alt="Stack, the configured Codex pet",
    sprite=_STACKY,
    palette=PET_CATALOG["stacky"].palette,
    text_fallback=PET_CATALOG["stacky"].text_fallback,
)


def _safe_pet_name(value: object) -> str | None:
    name = str(value).strip().lower()
    return name if _PET_NAME.fullmatch(name) else None


def resolve_pet_name(*, config_path: str | Path | None = None, override: str | None = None, environ: Mapping[str, str] | None = None) -> str | None:
    """Resolve only the pet key; never expose or parse unrelated config data."""
    values = environ if environ is not None else os.environ
    raw_override = override if override is not None else values.get("LWA_PET")
    if raw_override:
        return _safe_pet_name(raw_override)
    root = Path(config_path).expanduser() if config_path else Path(values.get("CODEX_HOME", "~/.codex")).expanduser() / "config.toml"
    try:
        import tomllib

        with root.open("rb") as stream:
            config = tomllib.load(stream)
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return None
    return _safe_pet_name(config.get("tui", {}).get("pet"))


def _png_rgba(width: int, height: int, scanlines: bytes) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(scanlines, 6)) + chunk(b"IEND", b"")


def _png_has_visible_alpha(data: bytes) -> bool:
    """Detect fully transparent RGBA cache frames without third-party imaging.

    For an all-zero alpha channel, PNG filtering leaves every alpha residual
    byte at zero. This lets us reject blank timing frames without reconstructing
    every RGB pixel, which matters when loading a long pet cycle on low-memory
    systems.
    """
    if len(data) < 26 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    if depth != 8 or color_type != 6:
        return True
    idat = bytearray()
    offset = 8
    while offset + 12 <= len(data):
        size = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + size]
        if kind == b"IDAT":
            idat.extend(payload)
        offset += size + 12
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error:
        return True
    stride = width * 4
    if len(raw) < height * (stride + 1):
        return True
    cursor = 0
    for _ in range(height):
        cursor += 1
        alpha_residuals = raw[cursor + 3 : cursor + stride : 4]
        if any(alpha_residuals):
            return True
        cursor += stride
    return False


def discover_codex_pet_asset(name: str | None, codex_home: str | Path | None = None) -> Path | None:
    """Find a Codex-owned cached pet frame without reading unrelated config."""
    safe_name = _safe_pet_name(name)
    if not safe_name:
        return None
    root = Path(codex_home or os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    cache = root / "cache" / "tui-pets" / "frame-cache" / safe_name
    try:
        candidates = sorted(cache.glob("*/frames/frame_000.png"))
    except OSError:
        return None
    for candidate in candidates:
        try:
            if candidate.is_file() and candidate.stat().st_size <= 250_000:
                return candidate
        except OSError:
            continue
    return None


def discover_codex_pet_names(codex_home: str | Path | None = None) -> tuple[str, ...]:
    """List cached Codex pet identities that have at least one valid frame."""
    root = Path(codex_home or os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    cache = root / "cache" / "tui-pets" / "frame-cache"
    try:
        candidates = sorted(cache.iterdir())
    except OSError:
        return ()
    names: list[str] = []
    for candidate in candidates:
        name = _safe_pet_name(candidate.name)
        if name and discover_codex_pet_asset(name, root) is not None:
            names.append(name)
    return tuple(names)


def next_codex_pet_name(current: str | None, names: tuple[str, ...]) -> str | None:
    """Return the next currently available pet, wrapping at the end."""
    if not names:
        return None
    if not current or current not in names:
        return names[0]
    return names[(names.index(current) + 1) % len(names)]


def resolve_pet_selection(selection: str | None, current: str | None, names: tuple[str, ...]) -> str | None:
    """Resolve a human pet selection without touching the active asset."""
    value = (selection or "next").strip().lower()
    if value in {"next", "cycle"}:
        return next_codex_pet_name(current, names)
    if value in {"list", "reload", "refresh"}:
        return None
    if value.isdigit():
        index = int(value) - 1
        return names[index] if 0 <= index < len(names) else None
    return value if value in names else None


class PetRenderer:
    """Render catalog pets without depending on Codex PTY graphics output."""

    def __init__(self, *, max_bytes: int = 250_000, scale: int = 6) -> None:
        self.max_bytes = max_bytes
        self.scale = max(1, min(scale, 12))

    def render(self, name: str | None, *, renderer: str = "text-fallback", low_resource: bool = False) -> PetFrame | None:
        definition = PET_CATALOG.get(_safe_pet_name(name) or "")
        if definition is None:
            return None
        scale = 2 if low_resource else self.scale
        png, width, height = self._sprite_png(definition, scale)
        if len(png) > self.max_bytes:
            return None
        image = ImageFrame("image/png", base64.b64encode(png).decode("ascii"), len(png), width, height)
        return PetFrame(definition.name, definition.alt, definition.text_fallback, image, renderer)

    def render_authoritative(self, name: str | None, asset_dir: str | Path, *, renderer: str = "text-fallback") -> PetFrame | None:
        """Load an explicitly supplied Codex-compatible asset; never guess."""
        safe_name = _safe_pet_name(name)
        if not safe_name:
            return None
        path = Path(asset_dir).expanduser() / f"{safe_name}.png"
        return self.render_authoritative_path(safe_name, path, renderer=renderer, source="codex-compatible-asset")

    def render_authoritative_path(
        self,
        name: str | None,
        path: str | Path,
        *,
        renderer: str = "text-fallback",
        source: str = "codex-tui-pet-cache",
    ) -> PetFrame | None:
        """Render one validated Codex-owned frame and expose stable identity."""
        safe_name = _safe_pet_name(name)
        if not safe_name:
            return None
        path = Path(path).expanduser()
        primary = self._read_png(path)
        if primary is None:
            return None
        data, width, height = primary
        if not _png_has_visible_alpha(data):
            return None
        # Codex can add pet identities independently of LWA's optional
        # fallback catalog. For authoritative cached assets, preserve the
        # configured identity and use the actual PNG frames; never substitute
        # a different sprite merely because the name is new to LWA.
        definition = PET_CATALOG.get(
            safe_name,
            PetDefinition(
                name=safe_name,
                alt=f"{safe_name.replace('-', ' ').title()}, the configured Codex pet",
                sprite=(),
                palette={},
                text_fallback=f"[{safe_name} pet]",
            ),
        )
        image = ImageFrame("image/png", base64.b64encode(data).decode("ascii"), len(data), width, height)
        digest = hashlib.sha256(data).hexdigest()[:16]
        animation = [image]
        if source == "codex-tui-pet-cache":
            try:
                # Preserve the complete bounded Codex cycle. The cache can
                # contain action and idle phases well beyond the first dozen
                # frames; truncating it makes every pet appear to have only
                # one short animation.
                paths = sorted(path.parent.glob("frame_*.png"))[:_MAX_PET_ANIMATION_FRAMES]
            except OSError:
                paths = []
            for frame_path in paths:
                if frame_path == path:
                    continue
                frame_data = self._read_png(frame_path)
                if frame_data is None:
                    continue
                frame_bytes, frame_width, frame_height = frame_data
                if not _png_has_visible_alpha(frame_bytes):
                    # Preserve the source timing while holding the last
                    # visible frame instead of replacing it with a blank.
                    animation.append(animation[-1])
                    continue
                animation.append(
                    ImageFrame(
                        "image/png",
                        base64.b64encode(frame_bytes).decode("ascii"),
                        len(frame_bytes),
                        frame_width,
                        frame_height,
                    )
                )
        frames = tuple(animation) if len(animation) > 1 else ()
        return PetFrame(definition.name, definition.alt, definition.text_fallback, image, renderer, source, f"codex:{safe_name}:sha256:{digest}", True, frames)

    def _read_png(self, path: Path) -> tuple[bytes, int, int] | None:
        try:
            data = path.read_bytes()
        except OSError:
            return None
        if len(data) > self.max_bytes or not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return None
        if len(data) < 24:
            return None
        width, height = struct.unpack(">II", data[16:24])
        if not width or not height or width > 2048 or height > 2048 or width * height > 2_000_000:
            return None
        return data, width, height

    @staticmethod
    def _sprite_png(definition: PetDefinition, scale: int) -> tuple[bytes, int, int]:
        source_height = len(definition.sprite)
        source_width = max(len(row) for row in definition.sprite)
        width, height = source_width * scale, source_height * scale
        pixels = bytearray()
        for row in definition.sprite:
            padded = row.ljust(source_width, ".")
            expanded = [definition.palette.get(char, (0, 0, 0, 0)) for char in padded for _ in range(scale)]
            line = b"".join(bytes(pixel) for pixel in expanded)
            for _ in range(scale):
                pixels.append(0)
                pixels.extend(line)
        return _png_rgba(width, height, bytes(pixels)), width, height


def render_configured_pet(*, config_path: str | Path | None = None, override: str | None = None, renderer: str = "text-fallback", low_resource: bool = False, asset_dir: str | Path | None = None) -> PetFrame | None:
    name = resolve_pet_name(config_path=config_path, override=override)
    # An explicit `/pets <name>` selection means “use that Codex pet”. Do not
    # let a one-file LWA asset directory shadow the Codex cache and make every
    # selection appear to load the same sprite.
    if override:
        codex_home = Path(config_path).expanduser().parent if config_path else None
        path = discover_codex_pet_asset(name, codex_home)
        if path is not None:
            return PetRenderer().render_authoritative_path(name, path, renderer=renderer)
    source_dir = asset_dir or os.environ.get("LWA_PET_ASSET_DIR")
    renderer_impl = PetRenderer()
    if source_dir:
        return renderer_impl.render_authoritative(name, source_dir, renderer=renderer)
    codex_home = Path(config_path).expanduser().parent if config_path else None
    path = discover_codex_pet_asset(name, codex_home)
    if path is None:
        return None
    return renderer_impl.render_authoritative_path(name, path, renderer=renderer)
