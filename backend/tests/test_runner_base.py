"""Tests for ModelRunner retry logic."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from dodar.runners.base import ModelResponse, ModelRunner


class FlakyRunner(ModelRunner):
    """A mock runner that fails N times with a retryable error, then succeeds."""

    model_id = "test-model"

    def __init__(self, fail_count: int):
        self.fail_count = fail_count
        self.attempt = 0

    async def _call_api(
        self, prompt: str, *, system_prompt: str | None = None
    ) -> ModelResponse:
        self.attempt += 1
        if self.attempt <= self.fail_count:
            raise RuntimeError("rate limit exceeded (429)")
        return ModelResponse(
            text=f"response to: {prompt}",
            input_tokens=10,
            output_tokens=20,
            latency_seconds=0.1,
        )


class NonRetryableRunner(ModelRunner):
    """A mock runner that fails with a non-retryable error."""

    model_id = "test-model"

    async def _call_api(
        self, prompt: str, *, system_prompt: str | None = None
    ) -> ModelResponse:
        raise ValueError("Invalid prompt format")


def _mock_settings(max_retries: int = 3):
    """Create a mock settings object with configurable max_retries."""
    from unittest.mock import MagicMock

    s = MagicMock()
    s.max_retries = max_retries
    return s


@pytest.mark.asyncio
async def test_runner_succeeds_first_try():
    """Runner returns response when API call succeeds immediately."""
    runner = FlakyRunner(fail_count=0)
    with patch("dodar.runners.base.get_settings", return_value=_mock_settings()):
        resp = await runner.run("hello")
    assert resp.text == "response to: hello"
    assert runner.attempt == 1


@pytest.mark.asyncio
async def test_runner_retries_on_rate_limit():
    """Runner retries on rate-limit errors and eventually succeeds."""
    runner = FlakyRunner(fail_count=2)
    with patch("dodar.runners.base.get_settings", return_value=_mock_settings(max_retries=3)):
        with patch("asyncio.sleep", return_value=None):  # skip actual sleep
            resp = await runner.run("hello")
    assert resp.text == "response to: hello"
    assert runner.attempt == 3  # 2 failures + 1 success


@pytest.mark.asyncio
async def test_runner_exhausts_retries():
    """Runner raises after exhausting all retries."""
    runner = FlakyRunner(fail_count=10)  # more failures than retries
    with patch("dodar.runners.base.get_settings", return_value=_mock_settings(max_retries=3)):
        with patch("asyncio.sleep", return_value=None):
            with pytest.raises(RuntimeError, match="rate limit"):
                await runner.run("hello")
    assert runner.attempt == 4  # initial + 3 retries


@pytest.mark.asyncio
async def test_runner_does_not_retry_non_retryable_error():
    """Runner raises immediately on non-retryable errors (no retry)."""
    runner = NonRetryableRunner()
    with patch("dodar.runners.base.get_settings", return_value=_mock_settings(max_retries=3)):
        with pytest.raises(ValueError, match="Invalid prompt format"):
            await runner.run("hello")
