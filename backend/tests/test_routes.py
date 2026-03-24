"""Tests for all API routes: scenarios, runs, scoring, reports, playground."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from dodar.main import app
from dodar.models.scenario import Discriminator, Scenario
from dodar.models.run import RunConfig, RunResult, RunStatus, RunSummary
from dodar.models.scoring import (
    BlindItem,
    DimensionScore,
    ScoreCard,
    ScoringSession,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


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


def _make_run_summary(run_id: str = "run-abc12345") -> RunSummary:
    return RunSummary(
        run_id=run_id,
        config=RunConfig(
            scenario_ids=["TEST-01"],
            models=["gpt-4o"],
            conditions=["zero_shot"],
        ),
        status=RunStatus.COMPLETED,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        prompt_version="v1",
        total_items=1,
        completed_items=1,
    )


def _make_run_result() -> RunResult:
    return RunResult(
        run_id="TEST-01_gpt-4o_zero_shot",
        scenario_id="TEST-01",
        model="gpt-4o",
        condition="zero_shot",
        prompt_version="v1",
        timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        prompt_sent="prompt",
        response_text="response",
        input_tokens=100,
        output_tokens=200,
        latency_seconds=1.5,
        cost_usd=0.001,
    )


def _make_scoring_session(session_id: str = "sess-abc123") -> ScoringSession:
    return ScoringSession(
        session_id=session_id,
        scorer="tester",
        run_id="run-abc12345",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        seed=42,
        items=[
            BlindItem(
                item_id="item001",
                scenario_id="TEST-01",
                model="gpt-4o",
                condition="zero_shot",
                prompt_version="v1",
                run_result_file="TEST-01_gpt-4o_zero_shot.json",
            ),
        ],
        order=["item001"],
    )


# ===========================================================================
# Scenarios routes
# ===========================================================================

class TestScenariosRoutes:

    @patch("dodar.routes.scenarios.load_scenarios_filtered")
    def test_list_scenarios_returns_200(self, mock_load, client):
        mock_load.return_value = [_make_scenario()]
        resp = client.get("/api/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "TEST-01"

    @patch("dodar.routes.scenarios.load_scenarios_filtered")
    def test_list_scenarios_empty(self, mock_load, client):
        mock_load.return_value = []
        resp = client.get("/api/scenarios")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("dodar.routes.scenarios.load_scenarios_filtered")
    def test_list_scenarios_with_filters(self, mock_load, client):
        mock_load.return_value = [_make_scenario()]
        resp = client.get("/api/scenarios?category=TEST&difficulty=medium")
        assert resp.status_code == 200
        mock_load.assert_called_once_with(
            category="TEST", difficulty="medium", domain=None, search=None,
        )

    @patch("dodar.routes.scenarios.load_all_results")
    @patch("dodar.routes.scenarios.get_scenario_by_id")
    def test_get_scenario_found(self, mock_get, mock_results, client):
        mock_get.return_value = _make_scenario()
        mock_results.return_value = [_make_run_result()]
        resp = client.get("/api/scenarios/TEST-01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "TEST-01"
        assert "run_matrix" in data

    @patch("dodar.routes.scenarios.get_scenario_by_id")
    def test_get_scenario_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/scenarios/NONEXISTENT")
        assert resp.status_code == 404

    @patch("dodar.routes.scenarios.load_all_results")
    @patch("dodar.routes.scenarios.get_scenario_by_id")
    def test_get_scenario_run_matrix_populated(self, mock_get, mock_results, client):
        mock_get.return_value = _make_scenario()
        mock_results.return_value = [_make_run_result()]
        resp = client.get("/api/scenarios/TEST-01")
        data = resp.json()
        assert "gpt-4o" in data["run_matrix"]
        assert data["run_matrix"]["gpt-4o"]["zero_shot"] == "completed"


# ===========================================================================
# Runs routes
# ===========================================================================

class TestRunsRoutes:

    @patch("dodar.routes.runs.load_all_run_summaries")
    def test_list_runs(self, mock_load, client):
        mock_load.return_value = [_make_run_summary()]
        resp = client.get("/api/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["run_id"] == "run-abc12345"

    @patch("dodar.routes.runs.load_all_run_summaries")
    def test_list_runs_empty(self, mock_load, client):
        mock_load.return_value = []
        resp = client.get("/api/runs")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("dodar.routes.runs.load_run_summary")
    def test_get_run_found(self, mock_load, client):
        mock_load.return_value = _make_run_summary()
        resp = client.get("/api/runs/run-abc12345")
        assert resp.status_code == 200
        assert resp.json()["run_id"] == "run-abc12345"

    @patch("dodar.routes.runs.load_run_summary")
    def test_get_run_not_found(self, mock_load, client):
        mock_load.return_value = None
        resp = client.get("/api/runs/nonexistent")
        assert resp.status_code == 404

    @patch("dodar.routes.runs.load_all_results")
    @patch("dodar.routes.runs.load_run_summary")
    def test_get_run_results(self, mock_summary, mock_results, client):
        mock_summary.return_value = _make_run_summary()
        mock_results.return_value = [_make_run_result()]
        resp = client.get("/api/runs/run-abc12345/results")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["scenario_id"] == "TEST-01"

    @patch("dodar.routes.runs.load_run_summary")
    def test_get_run_results_not_found(self, mock_summary, client):
        mock_summary.return_value = None
        resp = client.get("/api/runs/nonexistent/results")
        assert resp.status_code == 404

    @patch("dodar.routes.runs.execute_benchmark", new_callable=AsyncMock)
    @patch("dodar.routes.runs.load_scenarios_filtered")
    @patch("dodar.routes.runs.available_models")
    def test_start_run(self, mock_models, mock_scenarios, mock_exec, client):
        mock_models.return_value = ["gpt-4o"]
        mock_scenarios.return_value = [_make_scenario()]
        resp = client.post("/api/runs", json={
            "scenario_ids": ["TEST-01"],
            "models": ["gpt-4o"],
            "conditions": ["zero_shot"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "run_id" in data
        assert data["total_items"] == 1

    @patch("dodar.routes.runs.load_scenarios_filtered")
    def test_start_run_no_scenarios(self, mock_scenarios, client):
        mock_scenarios.return_value = []
        resp = client.post("/api/runs", json={"scenario_ids": ["NOPE"]})
        assert resp.status_code == 400

    @patch("dodar.routes.runs.delete_run")
    def test_delete_run_found(self, mock_delete, client):
        mock_delete.return_value = 3
        resp = client.delete("/api/runs/run-abc12345")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"
        assert resp.json()["files_removed"] == 3

    @patch("dodar.routes.runs.delete_run")
    def test_delete_run_not_found(self, mock_delete, client):
        mock_delete.return_value = 0
        resp = client.delete("/api/runs/nonexistent")
        assert resp.status_code == 404

    @patch("dodar.routes.runs.estimate_run_cost")
    @patch("dodar.routes.runs.load_scenarios_filtered")
    @patch("dodar.routes.runs.available_models")
    def test_estimate_cost(self, mock_models, mock_scenarios, mock_estimate, client):
        from dodar.engine.cost import CostEstimate
        mock_models.return_value = ["gpt-4o"]
        mock_scenarios.return_value = [_make_scenario()]
        mock_estimate.return_value = [
            CostEstimate(
                model="gpt-4o",
                condition="zero_shot",
                scenario_count=1,
                estimated_input_tokens=500,
                estimated_output_tokens=2000,
                estimated_cost_usd=0.0012,
            )
        ]
        resp = client.post("/api/runs/estimate", json={
            "scenario_ids": ["TEST-01"],
            "models": ["gpt-4o"],
            "conditions": ["zero_shot"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["model"] == "gpt-4o"
        assert data[0]["estimated_cost_usd"] == 0.0012

    @patch("dodar.routes.runs.load_scenarios_filtered")
    def test_estimate_cost_no_scenarios(self, mock_scenarios, client):
        mock_scenarios.return_value = []
        resp = client.post("/api/runs/estimate", json={"scenario_ids": ["NOPE"]})
        assert resp.status_code == 400


# ===========================================================================
# Scoring routes
# ===========================================================================

class TestScoringRoutes:

    @patch("dodar.routes.scoring.save_session")
    @patch("dodar.routes.scoring.create_scoring_session")
    def test_create_session(self, mock_create, mock_save, client):
        session = _make_scoring_session()
        mock_create.return_value = session
        resp = client.post("/api/scoring/sessions", json={
            "scorer": "tester",
            "run_id": "run-abc12345",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "sess-abc123"
        assert data["total_items"] == 1

    def test_get_scorer_models(self, client):
        resp = client.get("/api/scoring/scorer-models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "claude-opus-4-6" in data["models"]

    @patch("dodar.routes.scoring.load_all_sessions")
    def test_list_sessions(self, mock_load, client):
        mock_load.return_value = [_make_scoring_session()]
        resp = client.get("/api/scoring/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["session_id"] == "sess-abc123"

    @patch("dodar.routes.scoring.load_all_sessions")
    def test_list_sessions_empty(self, mock_load, client):
        mock_load.return_value = []
        resp = client.get("/api/scoring/sessions")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("dodar.routes.scoring.load_result")
    @patch("dodar.routes.scoring.load_session")
    def test_get_next_item(self, mock_session, mock_result, client):
        mock_session.return_value = _make_scoring_session()
        mock_result.return_value = _make_run_result()
        resp = client.get("/api/scoring/sessions/sess-abc123/next")
        assert resp.status_code == 200
        data = resp.json()
        assert data["item_id"] == "item001"
        assert data["position"] == 1
        assert "dimensions" in data

    @patch("dodar.routes.scoring.load_session")
    def test_get_next_item_session_not_found(self, mock_session, client):
        mock_session.return_value = None
        resp = client.get("/api/scoring/sessions/nonexistent/next")
        assert resp.status_code == 404

    @patch("dodar.routes.scoring.load_result")
    @patch("dodar.routes.scoring.load_session")
    def test_get_next_item_all_scored(self, mock_session, mock_result, client):
        session = _make_scoring_session()
        session.scores["item001"] = ScoreCard(
            item_id="item001",
            scores=[DimensionScore(dimension="Diagnosis Quality", score=4)],
            scored_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        mock_session.return_value = session
        resp = client.get("/api/scoring/sessions/sess-abc123/next")
        assert resp.status_code == 200
        data = resp.json()
        assert data["complete"] is True

    @patch("dodar.routes.scoring.save_session")
    @patch("dodar.routes.scoring.load_session")
    def test_submit_score(self, mock_session, mock_save, client):
        mock_session.return_value = _make_scoring_session()
        from dodar.config import SCORING_DIMENSIONS
        scores = [{"dimension": d, "score": 4, "rationale": "Good"} for d in SCORING_DIMENSIONS]
        resp = client.post(
            "/api/scoring/sessions/sess-abc123/items/item001/score",
            json={"scores": scores},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["scored"] == 1

    @patch("dodar.routes.scoring.load_session")
    def test_submit_score_session_not_found(self, mock_session, client):
        mock_session.return_value = None
        resp = client.post(
            "/api/scoring/sessions/nonexistent/items/item001/score",
            json={"scores": []},
        )
        assert resp.status_code == 404

    @patch("dodar.routes.scoring.load_session")
    def test_submit_score_already_scored(self, mock_session, client):
        session = _make_scoring_session()
        session.scores["item001"] = ScoreCard(
            item_id="item001",
            scores=[DimensionScore(dimension="Diagnosis Quality", score=4)],
            scored_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        mock_session.return_value = session
        resp = client.post(
            "/api/scoring/sessions/sess-abc123/items/item001/score",
            json={"scores": [{"dimension": "Diagnosis Quality", "score": 4}]},
        )
        assert resp.status_code == 400

    @patch("dodar.routes.scoring.load_session")
    def test_submit_score_missing_dimensions(self, mock_session, client):
        mock_session.return_value = _make_scoring_session()
        resp = client.post(
            "/api/scoring/sessions/sess-abc123/items/item001/score",
            json={"scores": [{"dimension": "Diagnosis Quality", "score": 4}]},
        )
        assert resp.status_code == 400
        assert "Must provide scores for all dimensions" in resp.json()["detail"]

    @patch("dodar.routes.scoring.load_session")
    def test_get_progress(self, mock_session, client):
        mock_session.return_value = _make_scoring_session()
        resp = client.get("/api/scoring/sessions/sess-abc123/progress")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scored"] == 0
        assert data["total"] == 1

    @patch("dodar.routes.scoring.load_session")
    def test_get_progress_not_found(self, mock_session, client):
        mock_session.return_value = None
        resp = client.get("/api/scoring/sessions/nonexistent/progress")
        assert resp.status_code == 404

    @patch("dodar.routes.scoring.delete_session")
    def test_delete_session(self, mock_delete, client):
        mock_delete.return_value = True
        resp = client.delete("/api/scoring/sessions/sess-abc123")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    @patch("dodar.routes.scoring.delete_session")
    def test_delete_session_not_found(self, mock_delete, client):
        mock_delete.return_value = False
        resp = client.delete("/api/scoring/sessions/nonexistent")
        assert resp.status_code == 404

    @patch("dodar.routes.scoring.save_session")
    @patch("dodar.routes.scoring.load_session")
    def test_reveal_session_all_scored(self, mock_session, mock_save, client):
        session = _make_scoring_session()
        session.scores["item001"] = ScoreCard(
            item_id="item001",
            scores=[DimensionScore(dimension="Diagnosis Quality", score=4)],
            scored_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        mock_session.return_value = session
        resp = client.post("/api/scoring/sessions/sess-abc123/reveal")
        assert resp.status_code == 200
        data = resp.json()
        assert data["revealed"] is True
        assert len(data["items"]) == 1
        assert data["items"][0]["model"] == "gpt-4o"

    @patch("dodar.routes.scoring.load_session")
    def test_reveal_session_not_all_scored(self, mock_session, client):
        mock_session.return_value = _make_scoring_session()  # 0 scores, 1 item
        resp = client.post("/api/scoring/sessions/sess-abc123/reveal")
        assert resp.status_code == 400
        assert "Cannot reveal" in resp.json()["detail"]

    @patch("dodar.routes.scoring.load_session")
    def test_reveal_session_not_found(self, mock_session, client):
        mock_session.return_value = None
        resp = client.post("/api/scoring/sessions/nonexistent/reveal")
        assert resp.status_code == 404

    def test_stop_session_not_running(self, client):
        resp = client.post("/api/scoring/sessions/nonexistent/stop")
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_running"


# ===========================================================================
# Reports routes
# ===========================================================================

class TestReportsRoutes:

    @patch("dodar.routes.reports.load_all_run_summaries")
    def test_list_versions(self, mock_summaries, client):
        mock_summaries.return_value = [_make_run_summary()]
        resp = client.get("/api/reports/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert "v1" in data

    @patch("dodar.routes.reports.load_all_run_summaries")
    def test_list_versions_empty(self, mock_summaries, client):
        mock_summaries.return_value = []
        resp = client.get("/api/reports/versions")
        assert resp.status_code == 200
        assert resp.json() == ["v1"]  # default fallback

    @patch("dodar.routes.reports.compute_effect_sizes")
    @patch("dodar.routes.reports.aggregate_scores")
    @patch("dodar.routes.reports.load_all_sessions")
    def test_dashboard_empty(self, mock_sessions, mock_agg, mock_effects, client):
        mock_sessions.return_value = []
        resp = client.get("/api/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total_sessions"] == 0

    @patch("dodar.routes.reports.compute_effect_sizes")
    @patch("dodar.routes.reports.aggregate_scores")
    @patch("dodar.routes.reports.load_all_sessions")
    def test_dashboard_with_data(self, mock_sessions, mock_agg, mock_effects, client):
        mock_sessions.return_value = [_make_scoring_session()]
        mock_agg.return_value = []
        mock_effects.return_value = []
        resp = client.get("/api/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total_sessions"] == 1

    @patch("dodar.routes.reports.compute_effect_sizes")
    @patch("dodar.routes.reports.aggregate_scores")
    @patch("dodar.routes.reports.load_all_sessions")
    def test_comparison(self, mock_sessions, mock_agg, mock_effects, client):
        mock_sessions.return_value = []
        mock_agg.return_value = []
        mock_effects.return_value = []
        resp = client.get("/api/reports/comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert "pivot" in data
        assert "dimensions" in data

    @patch("dodar.routes.reports.compute_effect_sizes")
    @patch("dodar.routes.reports.aggregate_scores")
    @patch("dodar.routes.reports.load_all_sessions")
    def test_stats(self, mock_sessions, mock_agg, mock_effects, client):
        mock_sessions.return_value = []
        mock_agg.return_value = []
        mock_effects.return_value = []
        resp = client.get("/api/reports/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "effect_sizes" in data

    @patch("dodar.routes.reports.load_all_results")
    @patch("dodar.routes.reports.load_all_scenarios")
    @patch("dodar.routes.reports.compute_effect_sizes")
    @patch("dodar.routes.reports.aggregate_scores")
    @patch("dodar.routes.reports.load_all_sessions")
    def test_export_json(self, mock_sessions, mock_agg, mock_effects, mock_scenarios, mock_results, client):
        mock_sessions.return_value = []
        mock_agg.return_value = []
        mock_effects.return_value = []
        mock_scenarios.return_value = [_make_scenario()]
        mock_results.return_value = [_make_run_result()]
        resp = client.get("/api/reports/export?format=json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]

    @patch("dodar.routes.reports.load_all_results")
    @patch("dodar.routes.reports.load_all_scenarios")
    @patch("dodar.routes.reports.compute_effect_sizes")
    @patch("dodar.routes.reports.aggregate_scores")
    @patch("dodar.routes.reports.load_all_sessions")
    def test_export_csv(self, mock_sessions, mock_agg, mock_effects, mock_scenarios, mock_results, client):
        mock_sessions.return_value = []
        mock_agg.return_value = []
        mock_effects.return_value = []
        mock_scenarios.return_value = [_make_scenario()]
        mock_results.return_value = [_make_run_result()]
        resp = client.get("/api/reports/export?format=csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]


# ===========================================================================
# Playground routes
# ===========================================================================

class TestPlaygroundRoutes:

    @patch("dodar.routes.playground.get_runner")
    def test_analyze_dodar(self, mock_get_runner, client):
        from dodar.runners.base import ModelResponse
        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=ModelResponse(
            text="## DIAGNOSE\nSome diagnosis\n## OPTIONS\nOpt1\n## DECIDE\nDecision\n## ACTION\nDo it\n## REVIEW\nLGTM",
            input_tokens=100,
            output_tokens=300,
            latency_seconds=2.5,
        ))
        mock_get_runner.return_value = mock_runner
        resp = client.post("/api/analyze", json={
            "scenario": "A complex scenario",
            "model": "gpt-4o",
            "mode": "dodar",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["model"] == "gpt-4o"
        assert data["mode"] == "dodar"
        assert data["input_tokens"] == 100
        assert data["output_tokens"] == 300

    @patch("dodar.routes.playground.get_runner")
    def test_analyze_zero_shot(self, mock_get_runner, client):
        from dodar.runners.base import ModelResponse
        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=ModelResponse(
            text="A simple response",
            input_tokens=50,
            output_tokens=100,
            latency_seconds=1.0,
        ))
        mock_get_runner.return_value = mock_runner
        resp = client.post("/api/analyze", json={
            "scenario": "Something",
            "model": "gpt-4o",
            "mode": "zero_shot",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["phases"] is None  # not dodar mode

    @patch("dodar.routes.playground.get_runner")
    def test_analyze_cot(self, mock_get_runner, client):
        from dodar.runners.base import ModelResponse
        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=ModelResponse(
            text="Step by step reasoning",
            input_tokens=50,
            output_tokens=100,
            latency_seconds=1.0,
        ))
        mock_get_runner.return_value = mock_runner
        resp = client.post("/api/analyze", json={
            "scenario": "Something",
            "model": "gpt-4o",
            "mode": "cot",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "cot"
