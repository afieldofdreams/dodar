"""Tests for dodar.scoring.autoscore — prompt building, parsing, and scoring flow."""

import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import pytest

from dodar.scoring.autoscore import (
    _build_scoring_prompt,
    _parse_scores,
    _is_openai_model,
    _get_autoscore_model,
    autoscore_item,
    autoscore_session,
    SCORING_DIMENSIONS,
)
from dodar.models.scoring import (
    BlindItem, ScoreCard, ScoringSession, DimensionScore,
)
from dodar.models.scenario import Scenario, Discriminator


# --------------------------------------------------------------------------- #
# _build_scoring_prompt
# --------------------------------------------------------------------------- #

class TestBuildScoringPrompt:
    def test_includes_scenario(self):
        prompt = _build_scoring_prompt("My scenario", "My response", ["p1"], ["g1"], [])
        assert "My scenario" in prompt

    def test_includes_response(self):
        prompt = _build_scoring_prompt("sc", "The model said X", [], [], [])
        assert "The model said X" in prompt

    def test_includes_pitfalls(self):
        prompt = _build_scoring_prompt("sc", "resp", ["anchors on price", "ignores timing"], [], [])
        assert "anchors on price" in prompt
        assert "ignores timing" in prompt

    def test_includes_gold_standard(self):
        prompt = _build_scoring_prompt("sc", "resp", [], ["enumerates causes", "proposes tests"], [])
        assert "enumerates causes" in prompt

    def test_includes_discriminators(self):
        discs = [{"dimension": "Diagnosis Quality", "description": "Holds diagnosis open"}]
        prompt = _build_scoring_prompt("sc", "resp", [], [], discs)
        assert "Holds diagnosis open" in prompt
        assert "Diagnosis Quality" in prompt


# --------------------------------------------------------------------------- #
# _parse_scores
# --------------------------------------------------------------------------- #

class TestParseScores:
    def test_valid_json(self):
        raw = json.dumps({
            "Diagnosis Quality": {"score": 4, "rationale": "Good"},
            "Option Breadth": {"score": 3, "rationale": "OK"},
        })
        result = _parse_scores(raw)
        assert result["Diagnosis Quality"]["score"] == 4

    def test_json_with_code_fences(self):
        raw = '```json\n{"Diagnosis Quality": {"score": 5, "rationale": "x"}}\n```'
        result = _parse_scores(raw)
        assert result["Diagnosis Quality"]["score"] == 5

    def test_json_with_surrounding_text(self):
        raw = 'Here are the scores:\n{"Diagnosis Quality": {"score": 3, "rationale": "y"}}\nDone.'
        result = _parse_scores(raw)
        assert result["Diagnosis Quality"]["score"] == 3

    def test_json_with_trailing_commas(self):
        raw = '{"Diagnosis Quality": {"score": 4, "rationale": "z",},}'
        result = _parse_scores(raw)
        assert result["Diagnosis Quality"]["score"] == 4

    def test_regex_fallback(self):
        raw = '"Diagnosis Quality": {"score": 4, "rationale": "ok"}\n"Option Breadth": {"score": 3, "rationale": "meh"}'
        result = _parse_scores(raw)
        assert result["Diagnosis Quality"]["score"] == 4
        assert result["Option Breadth"]["score"] == 3

    def test_unparseable_raises(self):
        with pytest.raises(ValueError, match="Could not parse"):
            _parse_scores("totally invalid garbage with no scores")

    def test_all_six_dimensions(self):
        data = {}
        for dim in SCORING_DIMENSIONS:
            data[dim] = {"score": 4, "rationale": f"test {dim}"}
        result = _parse_scores(json.dumps(data))
        assert len(result) == 6


# --------------------------------------------------------------------------- #
# _is_openai_model
# --------------------------------------------------------------------------- #

class TestIsOpenAIModel:
    def test_gpt_models(self):
        assert _is_openai_model("gpt-4o") is True
        assert _is_openai_model("gpt-5.4") is True
        assert _is_openai_model("gpt-4.1-mini") is True

    def test_o_models(self):
        assert _is_openai_model("o1-preview") is True
        assert _is_openai_model("o3-mini") is True
        assert _is_openai_model("o4-mini") is True

    def test_anthropic_models(self):
        assert _is_openai_model("claude-opus-4-6") is False
        assert _is_openai_model("claude-sonnet-4-5") is False

    def test_other_models(self):
        assert _is_openai_model("gemini-2.0-flash") is False


# --------------------------------------------------------------------------- #
# autoscore_item
# --------------------------------------------------------------------------- #

class TestAutoscoreItem:
    @pytest.fixture
    def mock_scenario(self):
        return Scenario(
            id="AMB-01",
            category="AMB",
            title="Test",
            domain="business",
            difficulty="medium",
            prompt_text="Scenario text",
            expected_pitfalls=["p1"],
            gold_standard_elements=["g1"],
            discriminators=[Discriminator(dimension="Diagnosis Quality", description="test")],
        )

    @pytest.fixture
    def mock_scores_json(self):
        data = {}
        for dim in SCORING_DIMENSIONS:
            data[dim] = {"score": 4, "rationale": f"Good {dim}"}
        return json.dumps(data)

    @pytest.mark.asyncio
    async def test_autoscore_item_anthropic(self, mock_scenario, mock_scores_json):
        with patch("dodar.scoring.autoscore.get_scenario_by_id", return_value=mock_scenario), \
             patch("dodar.scoring.autoscore._call_anthropic", new_callable=AsyncMock, return_value=mock_scores_json):
            scores = await autoscore_item("AMB-01", "response text", "prompt", "claude-opus-4-6")
            assert len(scores) == 6
            assert all(s.score == 4 for s in scores)

    @pytest.mark.asyncio
    async def test_autoscore_item_openai(self, mock_scenario, mock_scores_json):
        with patch("dodar.scoring.autoscore.get_scenario_by_id", return_value=mock_scenario), \
             patch("dodar.scoring.autoscore._call_openai", new_callable=AsyncMock, return_value=mock_scores_json):
            scores = await autoscore_item("AMB-01", "response text", "prompt", "gpt-5.4")
            assert len(scores) == 6

    @pytest.mark.asyncio
    async def test_autoscore_item_missing_scenario(self):
        with patch("dodar.scoring.autoscore.get_scenario_by_id", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                await autoscore_item("MISSING-01", "text", "prompt")

    @pytest.mark.asyncio
    async def test_autoscore_item_clamps_scores(self, mock_scenario):
        bad_json = json.dumps({dim: {"score": 10, "rationale": "x"} for dim in SCORING_DIMENSIONS})
        with patch("dodar.scoring.autoscore.get_scenario_by_id", return_value=mock_scenario), \
             patch("dodar.scoring.autoscore._call_anthropic", new_callable=AsyncMock, return_value=bad_json):
            scores = await autoscore_item("AMB-01", "resp", "prompt", "claude-opus-4-6")
            assert all(s.score == 5 for s in scores)  # Clamped to max 5

    @pytest.mark.asyncio
    async def test_autoscore_item_default_score_on_missing_dimension(self, mock_scenario):
        partial = json.dumps({"Diagnosis Quality": {"score": 5, "rationale": "great"}})
        with patch("dodar.scoring.autoscore.get_scenario_by_id", return_value=mock_scenario), \
             patch("dodar.scoring.autoscore._call_anthropic", new_callable=AsyncMock, return_value=partial):
            scores = await autoscore_item("AMB-01", "resp", "prompt", "claude-opus-4-6")
            assert scores[0].score == 5  # Diagnosis Quality
            assert scores[1].score == 3  # Default for missing


# --------------------------------------------------------------------------- #
# autoscore_session
# --------------------------------------------------------------------------- #

class TestAutoscoreSession:
    def _make_session(self, n_items=2) -> ScoringSession:
        items = []
        for i in range(n_items):
            items.append(BlindItem(
                item_id=f"item-{i}",
                scenario_id=f"AMB-0{i+1}",
                model="gpt-4o",
                condition="dodar",
                prompt_version="v2",
                run_result_file=f"AMB-0{i+1}_gpt-4o_dodar_v2.json",
            ))
        return ScoringSession(
            session_id="sess-test",
            scorer="test",
            run_id="run-test",
            created_at=datetime.now(timezone.utc),
            seed=42,
            items=items,
            order=[it.item_id for it in items],
        )

    @pytest.mark.asyncio
    async def test_scores_all_items(self):
        session = self._make_session(2)
        mock_result = MagicMock()
        mock_result.response_text = "response"
        mock_result.prompt_sent = "prompt"

        mock_scores = [DimensionScore(dimension=d, score=4) for d in SCORING_DIMENSIONS]

        with patch("dodar.scoring.autoscore.load_result", return_value=mock_result), \
             patch("dodar.scoring.autoscore.autoscore_item", new_callable=AsyncMock, return_value=mock_scores), \
             patch("dodar.scoring.autoscore.save_session"):
            result = await autoscore_session(session, concurrency=1)
            assert len(result.scores) == 2

    @pytest.mark.asyncio
    async def test_skips_already_scored(self):
        session = self._make_session(2)
        session.scores["item-0"] = ScoreCard(
            item_id="item-0",
            scores=[DimensionScore(dimension=d, score=4) for d in SCORING_DIMENSIONS],
            scored_at=datetime.now(timezone.utc),
        )

        mock_result = MagicMock()
        mock_result.response_text = "resp"
        mock_result.prompt_sent = "prompt"
        mock_scores = [DimensionScore(dimension=d, score=4) for d in SCORING_DIMENSIONS]

        with patch("dodar.scoring.autoscore.load_result", return_value=mock_result), \
             patch("dodar.scoring.autoscore.autoscore_item", new_callable=AsyncMock, return_value=mock_scores) as mock_auto, \
             patch("dodar.scoring.autoscore.save_session"):
            result = await autoscore_session(session, concurrency=1)
            assert len(result.scores) == 2
            # autoscore_item only called once (for item-1, not item-0)
            assert mock_auto.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_missing_result_file(self):
        session = self._make_session(1)
        with patch("dodar.scoring.autoscore.load_result", return_value=None), \
             patch("dodar.scoring.autoscore.save_session"):
            result = await autoscore_session(session, concurrency=1)
            assert len(result.scores) == 0

    @pytest.mark.asyncio
    async def test_handles_scoring_error(self):
        session = self._make_session(1)
        mock_result = MagicMock()
        mock_result.response_text = "resp"
        mock_result.prompt_sent = "prompt"

        with patch("dodar.scoring.autoscore.load_result", return_value=mock_result), \
             patch("dodar.scoring.autoscore.autoscore_item", new_callable=AsyncMock, side_effect=Exception("API fail")), \
             patch("dodar.scoring.autoscore.save_session"):
            result = await autoscore_session(session, concurrency=1)
            assert len(result.scores) == 0  # Failed, not scored

    @pytest.mark.asyncio
    async def test_cancel_event_stops_scoring(self):
        session = self._make_session(3)
        cancel = asyncio.Event()
        cancel.set()  # Already cancelled

        with patch("dodar.scoring.autoscore.load_result"), \
             patch("dodar.scoring.autoscore.save_session"):
            result = await autoscore_session(session, cancel_event=cancel)
            assert len(result.scores) == 0

    @pytest.mark.asyncio
    async def test_progress_callback(self):
        session = self._make_session(1)
        mock_result = MagicMock()
        mock_result.response_text = "resp"
        mock_result.prompt_sent = "prompt"
        mock_scores = [DimensionScore(dimension=d, score=4) for d in SCORING_DIMENSIONS]

        progress_calls = []
        def on_progress(completed, total):
            progress_calls.append((completed, total))

        with patch("dodar.scoring.autoscore.load_result", return_value=mock_result), \
             patch("dodar.scoring.autoscore.autoscore_item", new_callable=AsyncMock, return_value=mock_scores), \
             patch("dodar.scoring.autoscore.save_session"):
            await autoscore_session(session, concurrency=1, on_progress=on_progress)
            assert len(progress_calls) >= 1
