from __future__ import annotations

import time

import httpx

from dodar.runners.base import ModelResponse, ModelRunner


class OllamaRunner(ModelRunner):
    model_id = "ollama"

    def __init__(self, model_override: str = "llama3.1:8b", base_url: str = "http://localhost:11434") -> None:
        self._model = model_override
        self._base_url = base_url

    async def _call_api(self, prompt: str) -> ModelResponse:
        start = time.monotonic()

        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "num_predict": 4096,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

        latency = time.monotonic() - start
        text = data.get("message", {}).get("content", "")

        # Ollama returns token counts in eval_count / prompt_eval_count
        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        return ModelResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_seconds=latency,
        )
