"""Explicit token-counting boundary for benchmark promotion."""

from __future__ import annotations


class TokenizerUnavailable(RuntimeError):
    """Raised when an exact tokenizer is not installed locally."""


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens with tiktoken, refusing to disguise an estimate as exact."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    try:
        import tiktoken
    except ImportError as exc:
        raise TokenizerUnavailable(
            "exact token counting requires tiktoken; install it before promotion"
        ) from exc
    try:
        encoding = tiktoken.get_encoding(encoding_name)
    except Exception as exc:
        raise TokenizerUnavailable(f"tokenizer encoding unavailable: {encoding_name}") from exc
    return len(encoding.encode(text))
