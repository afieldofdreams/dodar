from __future__ import annotations

from dodar.runners.anthropic import AnthropicRunner
from dodar.runners.base import ModelRunner
from dodar.runners.google import GoogleRunner
from dodar.runners.openai import OpenAIRunner

_REGISTRY: dict[str, type[ModelRunner]] = {
    "claude-sonnet-4-5": AnthropicRunner,
    "gpt-4o": OpenAIRunner,
    "gemini-2.0-flash": GoogleRunner,
}

_instances: dict[str, ModelRunner] = {}


def get_runner(model_id: str) -> ModelRunner:
    """Get a runner instance for the given model ID (cached)."""
    if model_id not in _instances:
        cls = _REGISTRY.get(model_id)
        if cls is None:
            raise ValueError(f"Unknown model: {model_id}. Available: {list(_REGISTRY)}")
        _instances[model_id] = cls()
    return _instances[model_id]


def available_models() -> list[str]:
    return list(_REGISTRY.keys())
