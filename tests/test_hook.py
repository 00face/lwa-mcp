import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "compress-tool-output-feedback.py"


def test_post_tool_hook_returns_schema_safe_noop():
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "output": "command output",
    }

    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        check=True,
    )

    assert json.loads(result.stdout) == {}
