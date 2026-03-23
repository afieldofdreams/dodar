from __future__ import annotations

import time

import anthropic

from dodar.config import get_settings
from dodar.runners.base import ModelResponse, ModelRunner


class AnthropicRunner(ModelRunner):
    model_id = "claude-sonnet-4-5"

    def __init__(self, model_override: str | None = None) -> None:
        settings = get_settings()
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = model_override or settings.anthropic_model

    async def _call_api(self, prompt: str) -> ModelResponse:
        start = time.monotonic()
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        latency = time.monotonic() - start

        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        return ModelResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_seconds=latency,
        )
