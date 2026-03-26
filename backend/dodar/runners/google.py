from __future__ import annotations

import time

from google import genai
from google.genai import types

from dodar.config import get_settings
from dodar.runners.base import ModelResponse, ModelRunner


class GoogleRunner(ModelRunner):
    model_id = "gemini-2.0-flash"

    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.google_api_key)
        self._model = settings.google_model

    async def _call_api(
        self, prompt: str, *, system_prompt: str | None = None
    ) -> ModelResponse:
        start = time.monotonic()
        config = types.GenerateContentConfig(max_output_tokens=4096)
        if system_prompt:
            config.system_instruction = system_prompt

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=config,
        )
        latency = time.monotonic() - start

        text = response.text or ""
        usage = response.usage_metadata

        return ModelResponse(
            text=text,
            input_tokens=usage.prompt_token_count if usage else 0,
            output_tokens=usage.candidates_token_count if usage else 0,
            latency_seconds=latency,
        )
