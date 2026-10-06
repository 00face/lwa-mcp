import pytest

from lwa_mcp.server import _prepare_default_prompt
from lwa_mcp.service import RouterService
from tests.test_quota_fallback import make_config


@pytest.mark.asyncio
async def test_consensus_toggle_changes_default_prompt_preflight(tmp_path):
    service = RouterService(make_config(tmp_path))
    request = service.build_request("query", "toggle this session")

    service.set_consensus_default(True)
    consensus = await _prepare_default_prompt(service, request)
    assert consensus["preflight"]["mode"] == "consensus"

    service.set_consensus_default(False)
    single = await _prepare_default_prompt(service, request)
    assert single["preflight"]["mode"] == "single"
