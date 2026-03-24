"""Tests for pydantic model validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from dodar.models.run import RunConfig, RunResult, RunStatus, RunSummary
from dodar.models.scoring import DimensionScore, ScoreCard, ScoringSession, BlindItem


# ---------------------------------------------------------------------------
# RunConfig
# ---------------------------------------------------------------------------


def test_run_config_valid():
    cfg = RunConfig(
        scenario_ids=["AMB-01"],
        models=["gpt-4o"],
        conditions=["zero_shot"],
    )
    assert cfg.skip_completed is True
    assert cfg.prompt_version == "v1"


def test_run_config_defaults():
    cfg = RunConfig(scenario_ids=[], models=[], conditions=[])
    assert cfg.scenario_ids == []
    assert cfg.skip_completed is True


# ---------------------------------------------------------------------------
# RunResult
# ---------------------------------------------------------------------------


def _make_run_result(**overrides) -> RunResult:
    defaults = dict(
        run_id="AMB-01_gpt-4o_zero_shot",
        scenario_id="AMB-01",
        model="gpt-4o",
        condition="zero_shot",
        prompt_version="v1",
        timestamp=datetime.now(timezone.utc),
        prompt_sent="test prompt",
        response_text="test response",
        input_tokens=100,
        output_tokens=200,
        latency_seconds=1.5,
        cost_usd=0.001,
    )
    defaults.update(overrides)
    return RunResult(**defaults)


def test_run_result_valid():
    result = _make_run_result()
    assert result.scenario_id == "AMB-01"
    assert result.input_tokens == 100


def test_run_result_rejects_missing_fields():
    with pytest.raises(ValidationError):
        RunResult(run_id="x", scenario_id="x")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# RunSummary
# ---------------------------------------------------------------------------


def test_run_summary_valid():
    cfg = RunConfig(scenario_ids=["AMB-01"], models=["gpt-4o"], conditions=["zero_shot"])
    summary = RunSummary(
        run_id="run-123",
        config=cfg,
        status=RunStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        total_items=1,
    )
    assert summary.completed_items == 0
    assert summary.total_cost_usd == 0.0


def test_run_summary_status_enum():
    assert RunStatus.PENDING.value == "pending"
    assert RunStatus.FAILED.value == "failed"


# ---------------------------------------------------------------------------
# DimensionScore
# ---------------------------------------------------------------------------


def test_dimension_score_valid():
    ds = DimensionScore(dimension="Diagnosis Quality", score=3, rationale="Good")
    assert ds.score == 3


def test_dimension_score_allows_boundary_values():
    """Scores 1 and 5 should be accepted (valid range)."""
    ds1 = DimensionScore(dimension="Test", score=1)
    ds5 = DimensionScore(dimension="Test", score=5)
    assert ds1.score == 1
    assert ds5.score == 5


def test_dimension_score_rationale_optional():
    ds = DimensionScore(dimension="Test", score=3)
    assert ds.rationale is None


# ---------------------------------------------------------------------------
# ScoreCard
# ---------------------------------------------------------------------------


def test_score_card_valid():
    sc = ScoreCard(
        item_id="item-1",
        scores=[
            DimensionScore(dimension="Diagnosis Quality", score=4),
            DimensionScore(dimension="Option Breadth", score=3),
        ],
        scored_at=datetime.now(timezone.utc),
    )
    assert len(sc.scores) == 2


# ---------------------------------------------------------------------------
# ScoringSession
# ---------------------------------------------------------------------------


def test_scoring_session_valid():
    now = datetime.now(timezone.utc)
    item = BlindItem(
        item_id="item-1",
        scenario_id="AMB-01",
        model="gpt-4o",
        condition="zero_shot",
        run_result_file="runs/result.json",
    )
    session = ScoringSession(
        session_id="sess-1",
        scorer="human-1",
        run_id="run-1",
        created_at=now,
        seed=42,
        items=[item],
        order=["item-1"],
    )
    assert session.revealed is False
    assert session.scores == {}


def test_scoring_session_defaults():
    now = datetime.now(timezone.utc)
    session = ScoringSession(
        session_id="sess-1",
        scorer="human-1",
        created_at=now,
        seed=42,
        items=[],
        order=[],
    )
    assert session.run_id == ""
    assert session.revealed is False
