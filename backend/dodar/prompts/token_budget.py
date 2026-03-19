"""Token counting for length-matched condition."""

from __future__ import annotations

import tiktoken


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens using tiktoken. Falls back to cl100k_base for unknown models."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))
