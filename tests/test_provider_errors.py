from lwa_mcp.provider_policy import Availability, classify_exception
from lwa_mcp.providers.base import ProviderError


def test_structured_provider_error_classification_preserves_quota_boundary():
    assert classify_exception(ProviderError("429", status_code=429)) is Availability.TEMPORARY_RATE_LIMIT
    assert classify_exception(ProviderError("credits", status_code=402, quota_exhausted=True)) is Availability.QUOTA_EXHAUSTED
    assert classify_exception(ProviderError("bad key", status_code=401)) is Availability.AUTHENTICATION_FAILURE
    assert classify_exception(ProviderError("content_policy", status_code=403, security_denied=True)) is Availability.SECURITY_DENIED
