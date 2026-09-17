from __future__ import annotations

from ..models import ProviderConfig
from .base import ProviderAdapter
from .gemini import GeminiAdapter
from .openai_compatible import OpenAICompatibleAdapter
from .openai_media import OpenAIMediaAdapter
from .puter import PuterAdapter
from .replicate import ReplicateAdapter
from .stability import StabilityAdapter


def build_adapter(config: ProviderConfig) -> ProviderAdapter:
    if config.adapter == "openai":
        return OpenAICompatibleAdapter(config)
    if config.adapter == "openai_media":
        return OpenAIMediaAdapter(config)
    if config.adapter == "puter":
        return PuterAdapter(config)
    if config.adapter == "gemini":
        return GeminiAdapter(config)
    if config.adapter == "replicate":
        return ReplicateAdapter(config)
    if config.adapter == "stability":
        return StabilityAdapter(config)
    raise ValueError(f"Unknown adapter: {config.adapter}")
