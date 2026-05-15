from __future__ import annotations

from typing import Callable

from dodar.config import get_settings
from dodar.runners.anthropic import AnthropicRunner
from dodar.runners.base import ModelRunner
from dodar.runners.google import GoogleRunner
from dodar.runners.ollama import OllamaRunner
from dodar.runners.openai import OpenAIRunner


def _ollama(model: str) -> OllamaRunner:
    return OllamaRunner(model_override=model, base_url=get_settings().ollama_base_url)


# Maps model ID -> factory function that creates the runner
_REGISTRY: dict[str, Callable[[], ModelRunner]] = {
    # Cloud models — frontier
    "claude-opus-4-6": lambda: AnthropicRunner(model_override="claude-opus-4-6"),
    "claude-sonnet-4-5": lambda: AnthropicRunner(model_override="claude-sonnet-4-5"),
    "claude-haiku-4-5": lambda: AnthropicRunner(model_override="claude-haiku-4-5"),
    "gpt-5.4": lambda: OpenAIRunner(model_override="gpt-5.4"),
    "gpt-4o": lambda: OpenAIRunner(model_override="gpt-4o"),
    "gpt-4o-mini": lambda: OpenAIRunner(model_override="gpt-4o-mini"),
    "gpt-4.1": lambda: OpenAIRunner(model_override="gpt-4.1"),
    "gpt-4.1-mini": lambda: OpenAIRunner(model_override="gpt-4.1-mini"),
    "gpt-4.1-nano": lambda: OpenAIRunner(model_override="gpt-4.1-nano"),
    "o4-mini": lambda: OpenAIRunner(model_override="o4-mini"),
    "gemini-2.0-flash": lambda: GoogleRunner(),
    # Local models (Ollama) — base URL from OLLAMA_BASE_URL env var
    "qwen2.5:32b": lambda: _ollama("qwen2.5:32b-instruct-q4_K_M"),
    "qwen2.5:14b": lambda: _ollama("qwen2.5:14b-instruct"),
    "qwen2.5:7b": lambda: _ollama("qwen2.5:7b-instruct"),
    "llama3.1:8b": lambda: _ollama("llama3.1:8b"),
    "phi3:3.8b": lambda: _ollama("phi3:3.8b"),
}

_instances: dict[str, ModelRunner] = {}


def get_runner(model_id: str) -> ModelRunner:
    """Get a runner instance for the given model ID (cached)."""
    if model_id not in _instances:
        factory = _REGISTRY.get(model_id)
        if factory is None:
            raise ValueError(f"Unknown model: {model_id}. Available: {list(_REGISTRY)}")
        _instances[model_id] = factory()
    return _instances[model_id]


def available_models() -> list[str]:
    return list(_REGISTRY.keys())
