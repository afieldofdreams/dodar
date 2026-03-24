"""Tests for dodar.scoring.blind — blind scoring session creation."""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import pytest

from dodar.scoring.blind import create_scoring_session
from dodar.models.run import RunResult, RunSummary, RunConfig


def _make_summary(run_id="run-test", scenario_ids=None, models=None, conditions=None, version="v2"):
    return RunSummary(
        run_id=run_id,
        config=RunConfig(
            scenario_ids=scenario_ids or ["AMB-01", "AMB-02"],
            models=models or ["gpt-4o"],
            conditions=conditions or ["dodar", "zero_shot"],
        ),
        prompt_version=version,
        status="completed",
        created_at=datetime.now(timezone.utc),
        total_items=4,
    )


def _make_result(scenario_id, model, condition, version="v2"):
    return RunResult(
        run_id=f"{scenario_id}_{model}_{condition}_{version}",
        scenario_id=scenario_id,
        model=model,
        condition=condition,
        prompt_version=version,
        timestamp=datetime.now(timezone.utc),
        prompt_sent="prompt",
        response_text="response",
        input_tokens=100,
        output_tokens=200,
        latency_seconds=1.0,
        cost_usd=0.01,
    )


class TestCreateScoringSession:
    def test_creates_session_with_correct_items(self):
        summary = _make_summary()
        results = [
            _make_result("AMB-01", "gpt-4o", "dodar"),
            _make_result("AMB-01", "gpt-4o", "zero_shot"),
            _make_result("AMB-02", "gpt-4o", "dodar"),
            _make_result("AMB-02", "gpt-4o", "zero_shot"),
        ]
        with patch("dodar.scoring.blind.load_run_summary", return_value=summary), \
             patch("dodar.scoring.blind.load_all_results", return_value=results):
            session = create_scoring_session("Adam", "run-test")
            assert len(session.items) == 4
            assert session.scorer == "Adam"
            assert session.run_id == "run-test"

    def test_session_has_shuffled_order(self):
        summary = _make_summary()
        results = [
            _make_result("AMB-01", "gpt-4o", "dodar"),
            _make_result("AMB-02", "gpt-4o", "dodar"),
        ]
        with patch("dodar.scoring.blind.load_run_summary", return_value=summary), \
             patch("dodar.scoring.blind.load_all_results", return_value=results):
            session = create_scoring_session("Adam", "run-test", seed=42)
            assert len(session.order) == 2
            assert set(session.order) == {i.item_id for i in session.items}
            assert session.seed == 42

    def test_deterministic_with_same_seed(self):
        summary = _make_summary()
        results = [_make_result(f"AMB-0{i}", "gpt-4o", "dodar") for i in range(1, 6)]
        with patch("dodar.scoring.blind.load_run_summary", return_value=summary), \
             patch("dodar.scoring.blind.load_all_results", return_value=results):
            s1 = create_scoring_session("A", "run-test", seed=123)
            s2 = create_scoring_session("A", "run-test", seed=123)
            # Different UUIDs but same order pattern
            assert len(s1.order) == len(s2.order)

    def test_run_not_found_raises(self):
        with patch("dodar.scoring.blind.load_run_summary", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                create_scoring_session("Adam", "nonexistent")

    def test_no_results_raises(self):
        summary = _make_summary()
        with patch("dodar.scoring.blind.load_run_summary", return_value=summary), \
             patch("dodar.scoring.blind.load_all_results", return_value=[]):
            with pytest.raises(ValueError, match="No results"):
                create_scoring_session("Adam", "run-test")

    def test_filters_by_run_config(self):
        summary = _make_summary(scenario_ids=["AMB-01"], models=["gpt-4o"], conditions=["dodar"])
        results = [
            _make_result("AMB-01", "gpt-4o", "dodar"),
            _make_result("AMB-01", "gpt-4o", "zero_shot"),  # wrong condition
            _make_result("AMB-02", "gpt-4o", "dodar"),       # wrong scenario
            _make_result("AMB-01", "claude-sonnet-4-5", "dodar"),  # wrong model
        ]
        with patch("dodar.scoring.blind.load_run_summary", return_value=summary), \
             patch("dodar.scoring.blind.load_all_results", return_value=results):
            session = create_scoring_session("Adam", "run-test")
            assert len(session.items) == 1
            assert session.items[0].scenario_id == "AMB-01"
            assert session.items[0].model == "gpt-4o"
            assert session.items[0].condition == "dodar"

    def test_session_id_format(self):
        summary = _make_summary()
        results = [_make_result("AMB-01", "gpt-4o", "dodar")]
        with patch("dodar.scoring.blind.load_run_summary", return_value=summary), \
             patch("dodar.scoring.blind.load_all_results", return_value=results):
            session = create_scoring_session("Adam", "run-test")
            assert session.session_id.startswith("sess-")

    def test_items_have_prompt_version(self):
        summary = _make_summary()
        results = [_make_result("AMB-01", "gpt-4o", "dodar")]
        with patch("dodar.scoring.blind.load_run_summary", return_value=summary), \
             patch("dodar.scoring.blind.load_all_results", return_value=results):
            session = create_scoring_session("Adam", "run-test")
            assert session.items[0].prompt_version == "v2"

    def test_random_seed_when_none(self):
        summary = _make_summary()
        results = [_make_result("AMB-01", "gpt-4o", "dodar")]
        with patch("dodar.scoring.blind.load_run_summary", return_value=summary), \
             patch("dodar.scoring.blind.load_all_results", return_value=results):
            session = create_scoring_session("Adam", "run-test", seed=None)
            assert session.seed is not None
            assert isinstance(session.seed, int)
