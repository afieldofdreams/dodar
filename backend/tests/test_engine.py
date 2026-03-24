"""Tests for engine modules: cost estimation, progress tracking, executor."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dodar.engine.progress import EventType, ProgressEvent, ProgressTracker
from dodar.models.run import RunConfig, RunStatus, RunSummary
from dodar.models.scenario import Discriminator, Scenario


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scenario(id_: str = "TEST-01") -> Scenario:
    return Scenario(
        id=id_,
        category="TEST",
        title="Test Scenario",
        domain="business",
        difficulty="medium",
        prompt_text="You face a complex decision. What do you do?",
        expected_pitfalls=["Anchors on the obvious answer"],
        gold_standard_elements=["Considers multiple hypotheses"],
        discriminators=[
            Discriminator(dimension="Diagnosis Quality", description="Holds diagnosis open"),
        ],
    )


# ===========================================================================
# ProgressEvent
# ===========================================================================

class TestProgressEvent:

    def test_to_dict_item_complete(self):
        event = ProgressEvent(
            type=EventType.ITEM_COMPLETE,
            scenario_id="TEST-01",
            model="gpt-4o",
            condition="zero_shot",
            completed=3,
            total=10,
            tokens_used=500,
            cost_usd=0.005,
        )
        d = event.to_dict()
        assert d["type"] == "item_complete"
        assert d["scenario_id"] == "TEST-01"
        assert d["model"] == "gpt-4o"
        assert d["condition"] == "zero_shot"
        assert d["progress"]["completed"] == 3
        assert d["progress"]["total"] == 10
        assert d["tokens_used"] == 500
        assert d["cost_usd"] == 0.005
        assert "timestamp" in d

    def test_to_dict_item_start_minimal(self):
        event = ProgressEvent(
            type=EventType.ITEM_START,
            scenario_id="TEST-01",
            model="gpt-4o",
            condition="dodar",
            completed=0,
            total=5,
        )
        d = event.to_dict()
        assert d["type"] == "item_start"
        assert "tokens_used" not in d  # 0 tokens -> not included
        assert "cost_usd" not in d
        assert "error" not in d
        assert "summary" not in d

    def test_to_dict_item_error(self):
        event = ProgressEvent(
            type=EventType.ITEM_ERROR,
            scenario_id="TEST-01",
            model="gpt-4o",
            condition="zero_shot",
            completed=1,
            total=5,
            error="API timeout",
        )
        d = event.to_dict()
        assert d["type"] == "item_error"
        assert d["error"] == "API timeout"

    def test_to_dict_run_complete_with_summary(self):
        event = ProgressEvent(
            type=EventType.RUN_COMPLETE,
            completed=10,
            total=10,
            summary={"total_cost_usd": 0.05, "total_tokens": 5000},
        )
        d = event.to_dict()
        assert d["type"] == "run_complete"
        assert d["summary"]["total_cost_usd"] == 0.05
        assert d["progress"]["completed"] == 10

    def test_to_dict_omits_empty_scenario_id(self):
        event = ProgressEvent(type=EventType.RUN_COMPLETE, completed=0, total=0)
        d = event.to_dict()
        assert "scenario_id" not in d
        assert "model" not in d
        assert "condition" not in d


# ===========================================================================
# ProgressTracker
# ===========================================================================

class TestProgressTracker:

    def test_add_and_emit(self):
        tracker = ProgressTracker()
        received = []
        tracker.add_listener(lambda e: received.append(e))

        event = ProgressEvent(type=EventType.ITEM_START, completed=0, total=1)
        tracker.emit(event)

        assert len(received) == 1
        assert received[0] is event

    def test_multiple_listeners(self):
        tracker = ProgressTracker()
        received_a = []
        received_b = []
        tracker.add_listener(lambda e: received_a.append(e))
        tracker.add_listener(lambda e: received_b.append(e))

        tracker.emit(ProgressEvent(type=EventType.ITEM_START, completed=0, total=1))

        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_remove_listener(self):
        tracker = ProgressTracker()
        received = []
        cb = lambda e: received.append(e)
        tracker.add_listener(cb)
        tracker.remove_listener(cb)

        tracker.emit(ProgressEvent(type=EventType.ITEM_START, completed=0, total=1))

        assert len(received) == 0

    def test_bad_listener_does_not_break_others(self):
        tracker = ProgressTracker()
        received = []

        def bad_listener(e):
            raise RuntimeError("I break things")

        tracker.add_listener(bad_listener)
        tracker.add_listener(lambda e: received.append(e))

        tracker.emit(ProgressEvent(type=EventType.ITEM_START, completed=0, total=1))

        # Second listener still received the event
        assert len(received) == 1


# ===========================================================================
# Cost estimation
# ===========================================================================

class TestCostEstimation:

    @patch("dodar.engine.cost.count_tokens")
    @patch("dodar.engine.cost.build_prompt")
    def test_estimate_run_cost_single(self, mock_build, mock_count):
        from dodar.engine.cost import estimate_run_cost

        mock_build.return_value = "fake prompt"
        mock_count.return_value = 1000

        scenarios = [_make_scenario()]
        estimates = estimate_run_cost(scenarios, ["gpt-4o"], ["zero_shot"])

        assert len(estimates) == 1
        est = estimates[0]
        assert est.model == "gpt-4o"
        assert est.condition == "zero_shot"
        assert est.scenario_count == 1
        assert est.estimated_input_tokens == 1000
        assert est.estimated_output_tokens == 2000  # 1 scenario * 2000

        # Cost: (1000 / 1M * 2.5) + (2000 / 1M * 10.0) = 0.0025 + 0.02 = 0.0225
        assert est.estimated_cost_usd == pytest.approx(0.0225, abs=0.001)

    @patch("dodar.engine.cost.count_tokens")
    @patch("dodar.engine.cost.build_prompt")
    def test_estimate_run_cost_multiple_models_conditions(self, mock_build, mock_count):
        from dodar.engine.cost import estimate_run_cost

        mock_build.return_value = "fake prompt"
        mock_count.return_value = 500

        scenarios = [_make_scenario()]
        estimates = estimate_run_cost(
            scenarios,
            ["gpt-4o", "claude-sonnet-4-5"],
            ["zero_shot", "dodar"],
        )

        assert len(estimates) == 4  # 2 models * 2 conditions
        models = {e.model for e in estimates}
        assert models == {"gpt-4o", "claude-sonnet-4-5"}

    @patch("dodar.engine.cost.count_tokens")
    @patch("dodar.engine.cost.build_prompt")
    def test_estimate_free_model(self, mock_build, mock_count):
        from dodar.engine.cost import estimate_run_cost

        mock_build.return_value = "fake prompt"
        mock_count.return_value = 1000

        scenarios = [_make_scenario()]
        estimates = estimate_run_cost(scenarios, ["qwen2.5:7b"], ["zero_shot"])

        assert len(estimates) == 1
        assert estimates[0].estimated_cost_usd == 0.0  # local model = free

    @patch("dodar.engine.cost.count_tokens")
    @patch("dodar.engine.cost.build_prompt")
    def test_estimate_multiple_scenarios(self, mock_build, mock_count):
        from dodar.engine.cost import estimate_run_cost

        mock_build.return_value = "fake prompt"
        mock_count.return_value = 800

        scenarios = [_make_scenario("S1"), _make_scenario("S2"), _make_scenario("S3")]
        estimates = estimate_run_cost(scenarios, ["gpt-4o"], ["zero_shot"])

        assert estimates[0].scenario_count == 3
        assert estimates[0].estimated_input_tokens == 2400  # 800 * 3
        assert estimates[0].estimated_output_tokens == 6000  # 3 * 2000


# ===========================================================================
# Executor
# ===========================================================================

class TestExecutor:

    @pytest.mark.asyncio
    @patch("dodar.engine.executor.save_run_summary")
    @patch("dodar.engine.executor.save_result")
    @patch("dodar.engine.executor.result_exists", return_value=False)
    @patch("dodar.engine.executor.build_prompt", return_value="test prompt")
    @patch("dodar.engine.executor.get_runner")
    async def test_execute_benchmark_single_item(
        self, mock_get_runner, mock_build, mock_exists, mock_save_result, mock_save_summary
    ):
        from dodar.engine.executor import execute_benchmark
        from dodar.runners.base import ModelResponse

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=ModelResponse(
            text="Model response",
            input_tokens=100,
            output_tokens=200,
            latency_seconds=1.0,
        ))
        mock_get_runner.return_value = mock_runner

        config = RunConfig(
            scenario_ids=["TEST-01"],
            models=["gpt-4o"],
            conditions=["zero_shot"],
        )
        scenarios = [_make_scenario()]

        summary = await execute_benchmark("run-test", scenarios, config)

        assert summary.status == RunStatus.COMPLETED
        assert summary.completed_items == 1
        assert summary.total_tokens == 300  # 100 + 200
        mock_save_result.assert_called_once()

    @pytest.mark.asyncio
    @patch("dodar.engine.executor.save_run_summary")
    @patch("dodar.engine.executor.save_result")
    @patch("dodar.engine.executor.result_exists", return_value=False)
    @patch("dodar.engine.executor.build_prompt", return_value="test prompt")
    @patch("dodar.engine.executor.get_runner")
    async def test_execute_benchmark_emits_progress(
        self, mock_get_runner, mock_build, mock_exists, mock_save_result, mock_save_summary
    ):
        from dodar.engine.executor import execute_benchmark
        from dodar.runners.base import ModelResponse

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=ModelResponse(
            text="Response", input_tokens=50, output_tokens=100, latency_seconds=0.5,
        ))
        mock_get_runner.return_value = mock_runner

        config = RunConfig(
            scenario_ids=["TEST-01"],
            models=["gpt-4o"],
            conditions=["zero_shot"],
        )
        tracker = ProgressTracker()
        events = []
        tracker.add_listener(lambda e: events.append(e))

        await execute_benchmark("run-test", [_make_scenario()], config, tracker)

        event_types = [e.type for e in events]
        assert EventType.ITEM_START in event_types
        assert EventType.ITEM_COMPLETE in event_types
        assert EventType.RUN_COMPLETE in event_types

    @pytest.mark.asyncio
    @patch("dodar.engine.executor.save_run_summary")
    @patch("dodar.engine.executor.save_result")
    @patch("dodar.engine.executor.result_exists", return_value=False)
    @patch("dodar.engine.executor.build_prompt", return_value="test prompt")
    @patch("dodar.engine.executor.get_runner")
    async def test_execute_benchmark_handles_error(
        self, mock_get_runner, mock_build, mock_exists, mock_save_result, mock_save_summary
    ):
        from dodar.engine.executor import execute_benchmark
        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(side_effect=RuntimeError("API exploded"))
        mock_get_runner.return_value = mock_runner

        config = RunConfig(
            scenario_ids=["TEST-01"],
            models=["gpt-4o"],
            conditions=["zero_shot"],
        )
        tracker = ProgressTracker()
        events = []
        tracker.add_listener(lambda e: events.append(e))

        summary = await execute_benchmark("run-err", [_make_scenario()], config, tracker)

        assert summary.status == RunStatus.COMPLETED  # run itself completes
        error_events = [e for e in events if e.type == EventType.ITEM_ERROR]
        assert len(error_events) == 1
        assert "API exploded" in error_events[0].error

    @pytest.mark.asyncio
    @patch("dodar.engine.executor.save_run_summary")
    @patch("dodar.engine.executor.result_exists", return_value=True)
    async def test_execute_benchmark_skips_completed(self, mock_exists, mock_save_summary):
        from dodar.engine.executor import execute_benchmark

        config = RunConfig(
            scenario_ids=["TEST-01"],
            models=["gpt-4o"],
            conditions=["zero_shot"],
            skip_completed=True,
        )

        summary = await execute_benchmark("run-skip", [_make_scenario()], config)

        assert summary.total_items == 0  # all skipped
        assert summary.status == RunStatus.COMPLETED

    @pytest.mark.asyncio
    @patch("dodar.engine.executor.save_run_summary")
    @patch("dodar.engine.executor.save_result")
    @patch("dodar.engine.executor.result_exists", return_value=False)
    @patch("dodar.engine.executor.build_prompt", return_value="test prompt")
    @patch("dodar.engine.executor.get_runner")
    async def test_execute_benchmark_multiple_items(
        self, mock_get_runner, mock_build, mock_exists, mock_save_result, mock_save_summary
    ):
        from dodar.engine.executor import execute_benchmark
        from dodar.runners.base import ModelResponse

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=ModelResponse(
            text="Response", input_tokens=100, output_tokens=200, latency_seconds=1.0,
        ))
        mock_get_runner.return_value = mock_runner

        config = RunConfig(
            scenario_ids=["S1", "S2"],
            models=["gpt-4o"],
            conditions=["zero_shot", "dodar"],
        )
        scenarios = [_make_scenario("S1"), _make_scenario("S2")]

        summary = await execute_benchmark("run-multi", scenarios, config)

        assert summary.completed_items == 4  # 2 scenarios * 2 conditions
        assert mock_save_result.call_count == 4

    @pytest.mark.asyncio
    @patch("dodar.engine.executor.save_run_summary")
    @patch("dodar.engine.executor.save_result")
    @patch("dodar.engine.executor.result_exists", return_value=False)
    @patch("dodar.engine.executor.DODARPipeline")
    async def test_execute_benchmark_pipeline_condition(
        self, mock_pipeline_cls, mock_save_result, mock_exists, mock_save_summary
    ):
        from dodar.engine.executor import execute_benchmark
        from dodar.agents import PipelineResult

        mock_pipeline = MagicMock()
        mock_pipeline.run = AsyncMock(return_value=PipelineResult(
            text="Pipeline output",
            total_input_tokens=500,
            total_output_tokens=1000,
            total_latency_seconds=5.0,
            total_cost_usd=0.01,
        ))
        mock_pipeline_cls.return_value = mock_pipeline

        config = RunConfig(
            scenario_ids=["TEST-01"],
            models=["gpt-4o"],
            conditions=["dodar_pipeline"],
        )

        summary = await execute_benchmark("run-pipe", [_make_scenario()], config)

        assert summary.completed_items == 1
        mock_pipeline.run.assert_called_once()
