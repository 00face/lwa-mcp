import pytest

from lwa_mcp.command_prefix import PrefixError, parse_command


@pytest.mark.parametrize("prefix", ["!lwa", "$lwa"])
@pytest.mark.parametrize("state", ["on", "off"])
def test_lwa_consensus_toggle_is_parsed_for_both_prefixes(prefix, state):
    parsed = parse_command(f"{prefix} c {state}")

    assert parsed.mode == "skill"
    assert parsed.controls["consensus"] == state
    assert parsed.command == "consensus"


def test_lwa_consensus_toggle_rejects_unknown_state():
    with pytest.raises(PrefixError, match="consensus toggle"):
        parse_command("$lwa c maybe")
