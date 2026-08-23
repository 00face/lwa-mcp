#!/usr/bin/env python3
"""Visual pet animation protocol matrix; never writes to a Codex PTY."""

from __future__ import annotations

import argparse
import os
import sys
import time

from lwa_mcp.image_compositor import (
    kitty_animation_control_sequence,
    kitty_animation_frame_sequence,
    kitty_graphics_sequence,
    kitty_put_sequence,
    kitty_transmit_sequence,
)
from lwa_mcp.pet_renderer import render_configured_pet


def passthrough(sequence: str) -> str:
    if not os.environ.get("TMUX"):
        return sequence
    return "\x1bPtmux;\x1b" + sequence.replace("\x1b", "\x1b\x1b") + "\x1b\\"


def pane_bottom_right() -> str:
    """Return a safe image anchor near this pane's bottom-right corner."""
    try:
        size = os.get_terminal_size(1)
        row = max(5, size.lines - 8)
        column = max(3, size.columns - 11)
    except OSError:
        row, column = 5, 3
    return f"\x1b[{row};{column}H"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("terminal", "preloaded", "same-id", "unique-id", "text"))
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    pet = render_configured_pet(renderer="ghostty")
    if pet is None:
        print(f"{args.label}: configured pet unavailable", flush=True)
        return 1
    frames = list(pet.animation or (pet.image,))[:12]
    sys.stdout.write("\x1b[2J\x1b[H\x1b[?25l")
    sys.stdout.write(f"{args.label} · {pet.name} · {len(frames)} frames\n")
    sys.stdout.write("Protocol: " + args.mode + "\n")
    sys.stdout.flush()
    if args.mode == "text":
        while True:
            for line in pet.text_fallback.splitlines():
                sys.stdout.write(pane_bottom_right() + line + "\n")
                sys.stdout.flush()
            time.sleep(0.5)

    image_base = 9300
    if args.mode == "preloaded":
        for index, frame in enumerate(frames):
            sys.stdout.write(passthrough(kitty_transmit_sequence(frame, image_id=image_base + index)))
        sys.stdout.flush()
    elif args.mode == "terminal":
        sys.stdout.write(passthrough(pane_bottom_right() + kitty_graphics_sequence(frames[0], columns=8, rows=6, image_id=image_base)))
        for frame in frames[1:]:
            sys.stdout.write(passthrough(pane_bottom_right() + kitty_animation_frame_sequence(frame, image_id=image_base, columns=8, rows=6, gap_ms=160)))
        sys.stdout.write(passthrough(kitty_animation_control_sequence(image_id=image_base)))
        sys.stdout.flush()

    index = 0
    while True:
        frame = frames[index]
        if args.mode == "preloaded":
            sequence = kitty_put_sequence(image_id=image_base + index, columns=8, rows=6)
        elif args.mode == "same-id":
            sequence = kitty_graphics_sequence(frame, columns=8, rows=6, image_id=image_base)
        elif args.mode == "unique-id":
            sequence = kitty_graphics_sequence(frame, columns=8, rows=6, image_id=image_base + index)
        elif args.mode == "terminal":
            sequence = ""
        else:
            sequence = ""
        if sequence:
            sys.stdout.write(passthrough(pane_bottom_right() + sequence))
            sys.stdout.flush()
        index = (index + 1) % len(frames)
        time.sleep(0.16)


if __name__ == "__main__":
    raise SystemExit(main())
