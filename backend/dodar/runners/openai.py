from __future__ import annotations

import time

import openai

from dodar.config import get_settings
from dodar.runners.base import ModelResponse, ModelRunner


class OpenAIRunner(ModelRunner):
    model_id = "gpt-4o"

    def __init__(self, model_override: str | None = None) -> None:
        settings = get_settings()
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = model_override or settings.openai_model

    async def _call_api(self, prompt: str) -> ModelResponse:
        start = time.monotonic()
        # GPT-5.x and o-series models require max_completion_tokens instead of max_tokens
        use_completion_tokens = any(
            self._model.startswith(p) for p in ("gpt-5", "o1", "o3", "o4")
        )
        token_param = (
            {"max_completion_tokens": 4096}
            if use_completion_tokens
            else {"max_tokens": 4096}
        )
        response = await self._client.chat.completions.create(
            model=self._model,
            **token_param,
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
