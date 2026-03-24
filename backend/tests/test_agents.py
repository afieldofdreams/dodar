"""Tests for dodar.agents — DODARPipeline and PipelineResult."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dodar.agents import (
    DODARPipeline,
    PipelinePhaseResult,
    PipelineResult,
    PHASE_CONFIGS,
)
from dodar.runners.base import ModelResponse


# =========================================================================== #
# Helpers
# =========================================================================== #

PHASE_NAMES = ["diagnose", "options", "decide", "action", "review"]

FAKE_RESPONSES = {
    "diagnose": "Diagnosis: 1. Hypo A\n2. Hypo B\n3. Hypo C",
    "options": "Options: 1. Opt A\n2. Opt B\n3. Opt C\n4. Opt D",
    "decide": "Decision: Go with Opt A. Confidence: High.",
    "action": "Action: 1. Step 1\n2. Step 2\n3. Step 3",
    "review": "Review: 1. Failure mode A\n2. Failure mode B\n3. Failure mode C",
}


def _make_response(phase_name: str) -> ModelResponse:
    return ModelResponse(
        text=FAKE_RESPONSES[phase_name],
        input_tokens=50,
        output_tokens=100,
        latency_seconds=0.5,
    )


def _make_mock_runner(call_count_tracker: list | None = None) -> AsyncMock:
    """Create a mock runner that returns phase-appropriate responses in order."""
    mock = AsyncMock()
    call_index = [0]

    async def side_effect(prompt: str) -> ModelResponse:
        idx = call_index[0]
        phase = PHASE_NAMES[idx] if idx < len(PHASE_NAMES) else "review"
        call_index[0] += 1
        if call_count_tracker is not None:
            call_count_tracker.append(phase)
        return _make_response(phase)

    mock.run.side_effect = side_effect
    return mock


# =========================================================================== #
# PipelineResult / PipelinePhaseResult dataclasses
# =========================================================================== #

class TestPipelineDataclasses:
    def test_pipeline_result_defaults(self):
        r = PipelineResult()
        assert r.phases == {}
        assert r.phase_results == []
        assert r.text == ""
        assert r.total_tokens == 0
        assert r.total_input_tokens == 0
        assert r.total_output_tokens == 0
        assert r.total_latency_seconds == 0.0
        assert r.total_cost_usd == 0.0
        assert r.model == ""

    def test_pipeline_phase_result_defaults(self):
        r = PipelinePhaseResult(phase="diagnose", text="some text")
        assert r.phase == "diagnose"
        assert r.text == "some text"
        assert r.input_tokens == 0
        assert r.output_tokens == 0
        assert r.latency_seconds == 0.0


# =========================================================================== #
# PHASE_CONFIGS
# =========================================================================== #

class TestPhaseConfigs:
    def test_has_five_phases(self):
        assert len(PHASE_CONFIGS) == 5

    def test_phase_names_match(self):
        names = [name for name, _ in PHASE_CONFIGS]
        assert names == PHASE_NAMES

    def test_each_phase_has_system_prompt(self):
        for name, prompt in PHASE_CONFIGS:
            assert isinstance(prompt, str)
            assert len(prompt) > 50  # Non-trivial prompts


# =========================================================================== #
# DODARPipeline — init
# =========================================================================== #

class TestPipelineInit:
    @patch("dodar.agents.get_runner")
    def test_default_model(self, mock_get_runner):
        mock_get_runner.return_value = MagicMock()
        pipeline = DODARPipeline(model="gpt-4.1-nano")
        assert pipeline._default_model == "gpt-4.1-nano"
        # All phases should use the default model
        for phase in PHASE_NAMES:
            assert pipeline._phase_models[phase] == "gpt-4.1-nano"

    @patch("dodar.agents.get_runner")
    def test_per_phase_model_override(self, mock_get_runner):
        mock_get_runner.return_value = MagicMock()
        pipeline = DODARPipeline(
            model="gpt-4.1-nano",
            diagnose_model="gpt-4o",
            review_model="gpt-4o",
        )
        assert pipeline._phase_models["diagnose"] == "gpt-4o"
        assert pipeline._phase_models["options"] == "gpt-4.1-nano"
        assert pipeline._phase_models["decide"] == "gpt-4.1-nano"
        assert pipeline._phase_models["action"] == "gpt-4.1-nano"
        assert pipeline._phase_models["review"] == "gpt-4o"

    @patch("dodar.agents.get_runner", side_effect=ValueError("Unknown model"))
    def test_invalid_model_raises_on_init(self, mock_get_runner):
        with pytest.raises(ValueError, match="Unknown model"):
            DODARPipeline(model="nonexistent-model")

    @patch("dodar.agents.get_runner")
    def test_repr_single_model(self, mock_get_runner):
        mock_get_runner.return_value = MagicMock()
        pipeline = DODARPipeline(model="gpt-4.1-nano")
        assert repr(pipeline) == "DODARPipeline(model='gpt-4.1-nano')"

    @patch("dodar.agents.get_runner")
    def test_repr_mixed_models(self, mock_get_runner):
        mock_get_runner.return_value = MagicMock()
        pipeline = DODARPipeline(model="gpt-4.1-nano", diagnose_model="gpt-4o")
        r = repr(pipeline)
        assert "DODARPipeline(models=" in r
        assert "gpt-4o" in r


# =========================================================================== #
# DODARPipeline.run — full pipeline execution
# =========================================================================== #

class TestPipelineRun:
    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_runs_all_five_phases(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.10, "output": 0.40}}
        )
        call_tracker = []
        mock_runner = _make_mock_runner(call_tracker)
        mock_get_runner.return_value = mock_runner

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Test scenario")

        assert call_tracker == PHASE_NAMES
        assert len(result.phase_results) == 5

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_phases_dict_populated(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.10, "output": 0.40}}
        )
        mock_get_runner.return_value = _make_mock_runner()

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Test scenario")

        assert set(result.phases.keys()) == set(PHASE_NAMES)
        assert result.phases["diagnose"] == FAKE_RESPONSES["diagnose"]
        assert result.phases["options"] == FAKE_RESPONSES["options"]

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_token_accumulation(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.10, "output": 0.40}}
        )
        mock_get_runner.return_value = _make_mock_runner()

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Test scenario")

        # 5 phases * 50 input + 100 output = 750 total
        assert result.total_input_tokens == 5 * 50
        assert result.total_output_tokens == 5 * 100
        assert result.total_tokens == 5 * (50 + 100)

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_latency_accumulation(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.10, "output": 0.40}}
        )
        mock_get_runner.return_value = _make_mock_runner()

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Test scenario")

        assert result.total_latency_seconds == pytest.approx(5 * 0.5)

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_cost_calculation(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.10, "output": 0.40}}
        )
        mock_get_runner.return_value = _make_mock_runner()

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Test scenario")

        # Per phase: 50/1M * 0.10 + 100/1M * 0.40 = 0.000005 + 0.00004 = 0.000045
        # 5 phases: 0.000225
        expected = round(5 * (50 / 1_000_000 * 0.10 + 100 / 1_000_000 * 0.40), 6)
        assert result.total_cost_usd == expected

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_cost_zero_for_free_model(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.0, "output": 0.0}}
        )
        mock_get_runner.return_value = _make_mock_runner()

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Test scenario")

        assert result.total_cost_usd == 0.0

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_cost_zero_for_unknown_pricing(self, mock_get_runner, mock_get_settings):
        """If model not in pricing dict, cost defaults to 0."""
        mock_get_settings.return_value = MagicMock(
            model_pricing={}  # empty pricing
        )
        mock_get_runner.return_value = _make_mock_runner()

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Test scenario")

        assert result.total_cost_usd == 0.0

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_full_text_concatenation(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.0, "output": 0.0}}
        )
        mock_get_runner.return_value = _make_mock_runner()

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Test scenario")

        assert "## Phase: DIAGNOSE" in result.text
        assert "## Phase: OPTIONS" in result.text
        assert "## Phase: DECIDE" in result.text
        assert "## Phase: ACTION" in result.text
        assert "## Phase: REVIEW" in result.text

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_model_stored_in_result(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.0, "output": 0.0}}
        )
        mock_get_runner.return_value = _make_mock_runner()

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Scenario")

        assert result.model == "gpt-4.1-nano"

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_phase_results_have_correct_metadata(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.0, "output": 0.0}}
        )
        mock_get_runner.return_value = _make_mock_runner()

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = await pipeline.run("Scenario")

        for i, pr in enumerate(result.phase_results):
            assert pr.phase == PHASE_NAMES[i]
            assert pr.input_tokens == 50
            assert pr.output_tokens == 100
            assert pr.latency_seconds == 0.5


# =========================================================================== #
# Context accumulation — each phase sees previous outputs
# =========================================================================== #

class TestContextAccumulation:
    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_later_phases_receive_earlier_output(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.0, "output": 0.0}}
        )
        prompts_received = []
        call_index = [0]

        async def capture_prompt(prompt: str) -> ModelResponse:
            idx = call_index[0]
            phase = PHASE_NAMES[idx]
            call_index[0] += 1
            prompts_received.append(prompt)
            return _make_response(phase)

        mock_runner = AsyncMock()
        mock_runner.run.side_effect = capture_prompt
        mock_get_runner.return_value = mock_runner

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        await pipeline.run("Original scenario")

        # First call (diagnose) should have the scenario
        assert "Original scenario" in prompts_received[0]

        # Second call (options) should have diagnose output
        assert FAKE_RESPONSES["diagnose"] in prompts_received[1]

        # Third call (decide) should have diagnose + options output
        assert FAKE_RESPONSES["diagnose"] in prompts_received[2]
        assert FAKE_RESPONSES["options"] in prompts_received[2]

        # Fourth call (action) should have diagnose + options + decide
        assert FAKE_RESPONSES["decide"] in prompts_received[3]

        # Fifth call (review) should have all four previous phases
        assert FAKE_RESPONSES["diagnose"] in prompts_received[4]
        assert FAKE_RESPONSES["options"] in prompts_received[4]
        assert FAKE_RESPONSES["decide"] in prompts_received[4]
        assert FAKE_RESPONSES["action"] in prompts_received[4]

    @pytest.mark.asyncio
    @patch("dodar.agents.get_settings")
    @patch("dodar.agents.get_runner")
    async def test_prompts_include_system_prompt(self, mock_get_runner, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            model_pricing={"gpt-4.1-nano": {"input": 0.0, "output": 0.0}}
        )
        prompts_received = []
        call_index = [0]

        async def capture_prompt(prompt: str) -> ModelResponse:
            idx = call_index[0]
            phase = PHASE_NAMES[idx]
            call_index[0] += 1
            prompts_received.append(prompt)
            return _make_response(phase)

        mock_runner = AsyncMock()
        mock_runner.run.side_effect = capture_prompt
        mock_get_runner.return_value = mock_runner

        pipeline = DODARPipeline(model="gpt-4.1-nano")
        await pipeline.run("Test")

        # Diagnose prompt should include the diagnose system prompt content
        assert "diagnostic reasoning specialist" in prompts_received[0].lower()
        # Options prompt should include options system prompt
        assert "strategic options analyst" in prompts_received[1].lower()
        # Decide prompt should include decide system prompt
        assert "decision-making specialist" in prompts_received[2].lower()
        # Action prompt should include action system prompt
        assert "implementation planning specialist" in prompts_received[3].lower()
        # Review prompt should include review system prompt
        assert "critical review specialist" in prompts_received[4].lower()


# =========================================================================== #
# _format_prompt
# =========================================================================== #

class TestFormatPrompt:
    @patch("dodar.agents.get_runner")
    def test_format_combines_system_and_user(self, mock_get_runner):
        mock_get_runner.return_value = MagicMock()
        pipeline = DODARPipeline(model="gpt-4.1-nano")
        result = pipeline._format_prompt("System instructions", "User message")
        assert "System instructions" in result
        assert "User message" in result
        assert "---" in result  # separator
