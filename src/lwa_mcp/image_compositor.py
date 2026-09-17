"""Bounded extraction, decoding, assembly, and placement of terminal images."""

from __future__ import annotations

import base64
import binascii
import re
import struct
import zlib
from dataclasses import dataclass

_KITTY_START = "\x1b_G"
_GRAPHICS_END = "\x1b\\"


@dataclass(frozen=True, slots=True)
class ImageFrame:
    mime_type: str
    data_base64: str
    byte_length: int
    width: int | None = None
    height: int | None = None

    def public_json(self) -> dict[str, object]:
        return {"mime_type": self.mime_type, "data_base64": self.data_base64, "byte_length": self.byte_length, "width": self.width, "height": self.height}


def kitty_graphics_sequence(frame: ImageFrame, *, columns: int = 0, rows: int = 0, image_id: int | None = None) -> str:
    """Encode a validated PNG frame for a Kitty-compatible native host."""
    # q=2 suppresses terminal acknowledgements. Without it, Ghostty/tmux can
    # route responses such as `Gi=9001;OK` back through the pane as visible
    # text or input while an animation is being refreshed.
    params = "a=T,f=100,q=2"
    if image_id is not None:
        params += f",i={max(1, image_id)}"
    if columns > 0:
        params += f",c={columns}"
    if rows > 0:
        params += f",r={rows}"
    return f"\x1b_G{params};{frame.data_base64}\x1b\\"


def kitty_delete_sequence(image_id: int) -> str:
    """Delete a previously placed Kitty image by stable image id."""
    # q=2 prevents a delete acknowledgement from being interpreted as PTY
    # input by the parent terminal frame.
    return f"\x1b_Ga=d,d=I,q=2,i={max(1, image_id)};\x1b\\"


def kitty_animation_frame_sequence(
    frame: ImageFrame,
    *,
    image_id: int,
    columns: int = 0,
    rows: int = 0,
    gap_ms: int = 120,
) -> str:
    """Encode one terminal-driven animation frame for an existing image."""
    params = f"a=f,f=100,q=2,i={max(1, image_id)},z={max(1, gap_ms)}"
    if columns > 0:
        params += f",c={columns}"
    if rows > 0:
        params += f",r={rows}"
    return f"\x1b_G{params};{frame.data_base64}\x1b\\"


def kitty_animation_control_sequence(*, image_id: int, play: bool = True) -> str:
    """Start or stop terminal-driven playback for an image animation."""
    state = 3 if play else 1
    return f"\x1b_Ga=a,q=2,i={max(1, image_id)},s={state},v=1\x1b\\"


def kitty_transmit_sequence(frame: ImageFrame, *, image_id: int) -> str:
    """Transmit an image without placing it on screen."""
    return f"\x1b_Ga=t,f=100,q=2,i={max(1, image_id)};{frame.data_base64}\x1b\\"


def kitty_put_sequence(*, image_id: int, columns: int = 0, rows: int = 0) -> str:
    """Place a previously transmitted image without retransmitting data."""
    params = f"a=p,q=2,i={max(1, image_id)}"
    if columns > 0:
        params += f",c={columns}"
    if rows > 0:
        params += f",r={rows}"
    return f"\x1b_G{params};\x1b\\"


def _png_rgba(width: int, height: int, scanlines: bytes) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(scanlines, 6)) + chunk(b"IEND", b"")


class SixelDecoder:
    """Decode the bounded, commonly emitted subset of Sixel into PNG."""

    def __init__(self, *, max_width: int = 2048, max_height: int = 2048, max_pixels: int = 2_000_000) -> None:
        self.max_width = max_width
        self.max_height = max_height
        self.max_pixels = max_pixels

    def decode(self, body: str) -> ImageFrame:
        body = body.removeprefix("q")
        declared_width = declared_height = None
        if body.startswith('"'):
            end = body.find(";")
            attrs = body[1:] if end < 0 else body[1:end]
            body = "" if end < 0 else body[end + 1 :]
            values = attrs.split(";")
            if len(values) >= 4:
                declared_width = self._positive(values[2])
                declared_height = self._positive(values[3])
        palette: dict[int, tuple[int, int, int]] = {0: (0, 0, 0)}
        pixels: dict[tuple[int, int], tuple[int, int, int]] = {}
        color = 0
        x = y = 0
        index = 0
        while index < len(body):
            char = body[index]
            if char == "#":
                index, color = self._color(body, index + 1, palette)
                continue
            if char == "!":
                index += 1
                start = index
                while index < len(body) and body[index].isdigit():
                    index += 1
                count = int(body[start:index] or "0")
                if count > self.max_width:
                    raise ValueError("Sixel width exceeds compositor limit")
                if index >= len(body) or not 63 <= ord(body[index]) <= 126:
                    raise ValueError("malformed or oversized Sixel repeat")
                char = body[index]
                index += 1
                for _ in range(count):
                    x = self._paint(char, x, y, color, palette, pixels)
                continue
            if char == "$":
                x = 0
                index += 1
                continue
            if char == "-":
                x = 0
                y += 6
                if y > self.max_height:
                    raise ValueError("Sixel height exceeds compositor limit")
                index += 1
                continue
            if 63 <= ord(char) <= 126:
                x = self._paint(char, x, y, color, palette, pixels)
                index += 1
                continue
            raise ValueError("unsupported Sixel control")
        width = min(declared_width or (max((point[0] for point in pixels), default=-1) + 1), self.max_width)
        height = min(declared_height or (max((point[1] for point in pixels), default=-1) + 1), self.max_height)
        if width <= 0 or height <= 0 or width * height > self.max_pixels:
            raise ValueError("Sixel dimensions exceed compositor limit")
        scanlines = bytearray()
        for row in range(height):
            scanlines.append(0)
            for column in range(width):
                scanlines.extend((*pixels.get((column, row), (0, 0, 0)), 255))
        png = _png_rgba(width, height, bytes(scanlines))
        return ImageFrame("image/png", base64.b64encode(png).decode("ascii"), len(png), width, height)

    @staticmethod
    def _positive(value: str) -> int | None:
        return int(value) if value.isdigit() and int(value) > 0 else None

    def _color(self, body: str, index: int, palette: dict[int, tuple[int, int, int]]) -> tuple[int, int]:
        start = index
        while index < len(body) and body[index].isdigit():
            index += 1
        number = int(body[start:index] or "0")
        if index < len(body):
            match = re.match(r";2;(\d+);(\d+);(\d+)", body[index:])
            if match:
                rgb = tuple(min(100, int(value)) * 255 // 100 for value in match.groups())
                palette[number] = rgb  # type: ignore[assignment]
                return index + match.end(), number
        return index, number

    def _paint(self, char: str, x: int, y: int, color: int, palette: dict[int, tuple[int, int, int]], pixels: dict[tuple[int, int], tuple[int, int, int]]) -> int:
        if x >= self.max_width:
            raise ValueError("Sixel width exceeds compositor limit")
        mask = ord(char) - 63
        rgb = palette.get(color, (0, 0, 0))
        for bit in range(6):
            if mask & (1 << bit) and y + bit < self.max_height:
                pixels[(x, y + bit)] = rgb
        return x + 1


class ImageCompositor:
    """Extract bounded Kitty/Sixel frames and assemble split Kitty payloads."""

    def __init__(self, *, max_bytes: int = 4_000_000, max_frames: int = 16, max_pending_bytes: int = 8_000_000) -> None:
        self.max_bytes = max_bytes
        self.max_frames = max_frames
        self.max_pending_bytes = max_pending_bytes
        self.frames_seen = 0
        self._pending = ""
        self._kitty_parts: dict[str, bytearray] = {}
        self._kitty_meta: dict[str, dict[str, str]] = {}
        self._sixel = SixelDecoder()

    def extract_kitty(self, data: str) -> tuple[list[ImageFrame], str | None]:
        return self.feed(data)

    def feed(self, data: str) -> tuple[list[ImageFrame], str | None]:
        """Consume split Kitty/Sixel sequences and emit only complete frames."""
        frames: list[ImageFrame] = []
        issues: list[str] = []
        self._pending += data
        while True:
            starts = [index for index in (self._pending.find(_KITTY_START), self._pending.find("\x1bP")) if index >= 0]
            if not starts:
                if len(self._pending) > 64_000:
                    self._pending = self._pending[-64_000:]
                break
            start = min(starts)
            if start:
                self._pending = self._pending[start:]
            end = self._pending.find(_GRAPHICS_END, 3)
            if end < 0:
                break
            sequence = self._pending[1:end]
            self._pending = self._pending[end + 2 :]
            frame: ImageFrame | None = None
            issue: str | None = None
            if sequence.startswith("_G"):
                frame, issue = self._kitty(sequence[2:])
            elif sequence.startswith("Pq"):
                try:
                    frame = self._sixel.decode(sequence[1:])
                except (ValueError, OverflowError):
                    issue = "malformed or oversized Sixel image payload"
            if issue:
                issues.append(issue)
            if frame is not None and self.frames_seen < self.max_frames:
                frames.append(frame)
                self.frames_seen += 1
        return frames, (issues[0] if issues else None)

    def _kitty(self, payload: str) -> tuple[ImageFrame | None, str | None]:
        params, encoded = (payload.split(";", 1) + [""])[:2]
        values = dict(item.split("=", 1) for item in params.split(",") if "=" in item)
        image_id = values.get("i", "default")
        # Kitty may send a transmit command followed by a separate placement
        # command. Keep dimensions/format metadata across multipart chunks.
        metadata = self._kitty_meta.setdefault(image_id, {})
        metadata.update(values)
        if values.get("a") == "p" and not encoded:
            return None, None
        try:
            decoded = base64.b64decode(encoded, validate=True)
            if values.get("o") == "z":
                decoded = zlib.decompress(decoded)
        except (binascii.Error, ValueError, zlib.error):
            return None, "malformed Kitty image payload"
        pending = self._kitty_parts.setdefault(image_id, bytearray())
        pending.extend(decoded)
        if sum(len(part) for part in self._kitty_parts.values()) > self.max_pending_bytes:
            self._kitty_parts.clear()
            return None, "pending Kitty image limit reached"
        if values.get("m", "0") == "1":
            return None, None
        decoded = bytes(self._kitty_parts.pop(image_id, pending))
        if len(decoded) > self.max_bytes:
            return None, "image payload exceeds compositor limit"
        values = metadata
        self._kitty_meta.pop(image_id, None)
        format_id = values.get("f", "100")
        if format_id in {"24", "32"}:
            try:
                width = int(values["s"])
                height = int(values["v"])
            except (KeyError, ValueError):
                return None, "raw Kitty image is missing dimensions"
            channels = int(format_id) // 8
            if width <= 0 or height <= 0 or width > 2048 or height > 2048 or width * height > 2_000_000:
                return None, "raw Kitty image dimensions exceed compositor limit"
            if len(decoded) != width * height * channels:
                return None, "raw Kitty image length is incompatible with dimensions"
            scanlines = bytearray()
            for row in range(height):
                scanlines.append(0)
                start = row * width * channels
                line = decoded[start : start + width * channels]
                if channels == 3:
                    for offset in range(0, len(line), 3):
                        scanlines.extend(line[offset : offset + 3])
                        scanlines.append(255)
                else:
                    scanlines.extend(line)
            decoded = _png_rgba(width, height, bytes(scanlines))
            return ImageFrame("image/png", base64.b64encode(decoded).decode("ascii"), len(decoded), width, height), None
        return ImageFrame("image/png", base64.b64encode(decoded).decode("ascii"), len(decoded)), None
