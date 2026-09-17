#!/usr/bin/env python3
"""Schema-safe no-op for the workspace post-tool hook.

The host does not accept PostToolUse event fields echoed as a hook response.
Until a host-specific compressor is available, consume the event and return an
empty response so the original tool result continues normally.
"""

from __future__ import annotations

import sys


def main() -> int:
    # Event fields are input-only. Returning them causes the host to reject the
    # response as invalid PostToolUse JSON.
    sys.stdin.buffer.read()
    sys.stdout.write("{}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
