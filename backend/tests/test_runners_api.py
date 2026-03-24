"""Tests for model runner API call methods — all mocked."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from dodar.runners.base import ModelResponse
from dodar.runners.registry import get_runner, available_models


class TestAnthropicRunner:
    @pytest.mark.asyncio
    async def test_call_api(self):
        with patch("dodar.runners.anthropic.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(anthropic_api_key="fake", anthropic_model="claude-sonnet-4-5")
            with patch("dodar.runners.anthropic.anthropic.AsyncAnthropic") as mock_cls:
                mock_response = MagicMock()
                mock_response.content = [MagicMock(type="text", text="Hello")]
                mock_response.usage.input_tokens = 10
                mock_response.usage.output_tokens = 20
                mock_cls.return_value.messages.create = AsyncMock(return_value=mock_response)

                from dodar.runners.anthropic import AnthropicRunner
                runner = AnthropicRunner(model_override="claude-sonnet-4-5")
                result = await runner._call_api("test prompt")
                assert result.text == "Hello"
                assert result.input_tokens == 10
                assert result.output_tokens == 20


class TestOpenAIRunner:
    @pytest.mark.asyncio
    async def test_call_api(self):
        with patch("dodar.runners.openai.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="fake", openai_model="gpt-4o")
            with patch("dodar.runners.openai.openai.AsyncOpenAI") as mock_cls:
                mock_choice = MagicMock()
                mock_choice.message.content = "World"
                mock_response = MagicMock()
                mock_response.choices = [mock_choice]
                mock_response.usage.prompt_tokens = 15
                mock_response.usage.completion_tokens = 25
                mock_cls.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

                from dodar.runners.openai import OpenAIRunner
                runner = OpenAIRunner(model_override="gpt-4o")
                result = await runner._call_api("test prompt")
                assert result.text == "World"
                assert result.input_tokens == 15
                assert result.output_tokens == 25


class TestGoogleRunner:
    @pytest.mark.asyncio
    async def test_call_api(self):
        with patch("dodar.runners.google.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(google_api_key="fake", google_model="gemini-2.0-flash")
            with patch("dodar.runners.google.genai.Client") as mock_cls:
                mock_response = MagicMock()
                mock_response.text = "Google says hi"
                mock_cls.return_value.aio.models.generate_content = AsyncMock(return_value=mock_response)

                from dodar.runners.google import GoogleRunner
                runner = GoogleRunner()
                result = await runner._call_api("test prompt")
                assert result.text == "Google says hi"


class TestOllamaRunner:
    @pytest.mark.asyncio
    async def test_call_api(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": "Ollama response"},
            "prompt_eval_count": 50,
            "eval_count": 100,
        }
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = False

        with patch("dodar.runners.ollama.httpx.AsyncClient", return_value=mock_client):
            from dodar.runners.ollama import OllamaRunner
            runner = OllamaRunner(model_override="llama3.1:8b")
            result = await runner._call_api("test prompt")
            assert result.text == "Ollama response"
            assert result.input_tokens == 50
            assert result.output_tokens == 100


class TestRegistry:
    def test_available_models_returns_list(self):
        models = available_models()
        assert isinstance(models, list)
        assert "gpt-4o" in models
        assert "claude-sonnet-4-5" in models
        assert len(models) > 5
