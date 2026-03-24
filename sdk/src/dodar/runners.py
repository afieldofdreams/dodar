"""Model runners for DODAR — thin wrappers around provider SDKs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
import time


@dataclass
class RunnerResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_seconds: float = 0.0


def _detect_provider(model: str) -> str:
    if model.startswith("claude"):
        return "anthropic"
    elif model.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    elif model.startswith("gemini"):
        return "google"
    else:
        return "ollama"


# ---- Anthropic ---- #

async def _run_anthropic(model: str, prompt: str, system: str | None = None, max_tokens: int = 4096) -> RunnerResponse:
    import anthropic
    client = anthropic.AsyncAnthropic()
    messages = [{"role": "user", "content": prompt}]
    kwargs: dict = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if system:
        kwargs["system"] = system

    t0 = time.monotonic()
    response = await client.messages.create(**kwargs)
    latency = time.monotonic() - t0

    return RunnerResponse(
        text=response.content[0].text,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_seconds=latency,
    )


# ---- OpenAI ---- #

async def _run_openai(model: str, prompt: str, system: str | None = None, max_tokens: int = 4096) -> RunnerResponse:
    import openai
    client = openai.AsyncOpenAI()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    # Newer models use max_completion_tokens
    use_new_param = model.startswith(("gpt-5", "o3", "o4"))
    kwargs: dict = {"model": model, "messages": messages}
    if use_new_param:
        kwargs["max_completion_tokens"] = max_tokens
    else:
        kwargs["max_tokens"] = max_tokens

    t0 = time.monotonic()
    response = await client.chat.completions.create(**kwargs)
    latency = time.monotonic() - t0

    usage = response.usage
    return RunnerResponse(
        text=response.choices[0].message.content or "",
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
        latency_seconds=latency,
    )


# ---- Google ---- #

async def _run_google(model: str, prompt: str, system: str | None = None, max_tokens: int = 4096) -> RunnerResponse:
    from google import genai
    client = genai.Client()
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    t0 = time.monotonic()
    response = await client.aio.models.generate_content(
        model=model,
        contents=full_prompt,
    )
    latency = time.monotonic() - t0

    return RunnerResponse(
        text=response.text or "",
        latency_seconds=latency,
    )


# ---- Ollama ---- #

async def _run_ollama(model: str, prompt: str, system: str | None = None, max_tokens: int = 4096) -> RunnerResponse:
    import httpx
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    t0 = time.monotonic()
    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(
            "http://localhost:11434/api/chat",
            json={"model": model, "messages": messages, "stream": False},
        )
        resp.raise_for_status()
        data = resp.json()
    latency = time.monotonic() - t0

    return RunnerResponse(
        text=data.get("message", {}).get("content", ""),
        input_tokens=data.get("prompt_eval_count", 0),
        output_tokens=data.get("eval_count", 0),
        latency_seconds=latency,
    )


# ---- Registry ---- #

_MODELS = {
    "claude-opus-4-6", "claude-sonnet-4-5", "claude-haiku-4-5",
    "gpt-5.4", "gpt-4o", "gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1-nano",
    "gemini-2.0-flash",
}


def available_models() -> list[str]:
    """List all known model IDs."""
    return sorted(_MODELS)


async def run_model(model: str, prompt: str, system: str | None = None, max_tokens: int = 4096) -> RunnerResponse:
    """Run a prompt against any supported model."""
    provider = _detect_provider(model)
    match provider:
        case "anthropic":
            return await _run_anthropic(model, prompt, system, max_tokens)
        case "openai":
            return await _run_openai(model, prompt, system, max_tokens)
        case "google":
            return await _run_google(model, prompt, system, max_tokens)
        case "ollama":
            return await _run_ollama(model, prompt, system, max_tokens)
        case _:
            raise ValueError(f"Unknown provider for model: {model}")
