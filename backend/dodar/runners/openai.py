from __future__ import annotations

import time

import openai

from dodar.config import get_settings
from dodar.runners.base import ModelResponse, ModelRunner


class OpenAIRunner(ModelRunner):
    model_id = "gpt-4o"

    def __init__(self) -> None:
        settings = get_settings()
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def _call_api(self, prompt: str) -> ModelResponse:
        start = time.monotonic()
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        latency = time.monotonic() - start

        text = response.choices[0].message.content or ""
        usage = response.usage

        return ModelResponse(
            text=text,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency_seconds=latency,
        )
