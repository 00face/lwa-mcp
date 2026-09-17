from __future__ import annotations

from .openai_compatible import OpenAICompatibleAdapter


class PuterAdapter(OpenAICompatibleAdapter):
    """Puter's OpenAI-compatible completions plus native model discovery."""

    def _models_url(self) -> str:
        # Puter documents this native listing source separately from its
        # OpenAI-compatible completion base URL.
        return "https://api.puter.com/puterai/chat/models/details"
