"""Abstract model runner with retry and backoff."""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from dodar.config import get_settings


@dataclass
class ModelResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float


class ModelRunner(ABC):
    """Abstract base class for model API runners."""

    model_id: str  # canonical model ID (e.g., "claude-sonnet-4-5")

    @abstractmethod
    async def _call_api(
        self, prompt: str, *, system_prompt: str | None = None
    ) -> ModelResponse:
        """Make the actual API call. Subclasses implement this.

        Args:
            prompt: The user message content.
            system_prompt: Optional system message (separate from user content).
        """
        ...

    async def run(
        self, prompt: str, *, system_prompt: str | None = None
    ) -> ModelResponse:
        """Run with retry and exponential backoff."""
        settings = get_settings()
        delays = [1, 2, 4]  # seconds between retries

        for attempt in range(settings.max_retries + 1):
            try:
                return await self._call_api(prompt, system_prompt=system_prompt)
            except Exception as e:
                if attempt == settings.max_retries:
                    raise
                error_str = str(e).lower()
                # Retry on rate limits and transient errors
                if any(kw in error_str for kw in ["rate", "429", "500", "503", "timeout"]):
                    delay = delays[min(attempt, len(delays) - 1)]
                    await asyncio.sleep(delay)
                else:
                    raise

        raise RuntimeError("Exhausted retries")  # unreachable but satisfies type checker
