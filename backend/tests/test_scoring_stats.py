"""Tests for dodar.scoring.stats — aggregate_scores and compute_effect_sizes."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

from dodar.models.scoring import (
    BlindItem,
    DimensionScore,
    ScoreCard,
    ScoringSession,
)
from dodar.scoring.stats import (
    DimensionStats,
    EffectSize,
    aggregate_scores,
    compute_effect_sizes,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _blind_item(
    item_id: str,
    model: str = "gpt-4",
    condition: str = "dodar",
    prompt_version: str = "v1",
) -> BlindItem:
    return BlindItem(
        item_id=item_id,
        scenario_id="scenario-1",
        model=model,
        condition=condition,
        prompt_version=prompt_version,
        run_result_file="run-001.json",
    )


def _score_card(item_id: str, dim_scores: dict[str, int]) -> ScoreCard:
    """Build a ScoreCard from {dimension: score} mapping."""
    return ScoreCard(
        item_id=item_id,
        scores=[
            DimensionScore(dimension=dim, score=score)
            for dim, score in dim_scores.items()
        ],
        scored_at=datetime.now(timezone.utc),
    )


def _session(
    items: list[BlindItem],
    scores: dict[str, ScoreCard],
    session_id: str = "sess-test",
) -> ScoringSession:
    return ScoringSession(
        session_id=session_id,
        scorer="tester",
        run_id="run-001",
        created_at=datetime.now(timezone.utc),
        seed=42,
        items=items,
        order=[i.item_id for i in items],
        scores=scores,
    )


# ---------------------------------------------------------------------------
# aggregate_scores tests
# ---------------------------------------------------------------------------

class TestAggregateScores:
    """Tests for aggregate_scores."""

    def test_basic_mean_and_std(self):
        """Verify mean/std with manually computed values.

        Scores for (gpt-4, dodar, Diagnosis Quality): [3, 5, 4]
        Mean  = 12/3 = 4.0
        Population variance = ((3-4)^2 + (5-4)^2 + (4-4)^2) / 3 = 2/3
        Std = sqrt(2/3) ~ 0.82
        """
        items = [
            _blind_item("a", model="gpt-4", condition="dodar"),
            _blind_item("b", model="gpt-4", condition="dodar"),
            _blind_item("c", model="gpt-4", condition="dodar"),
        ]
        scores = {
            "a": _score_card("a", {"Diagnosis Quality": 3}),
            "b": _score_card("b", {"Diagnosis Quality": 5}),
            "c": _score_card("c", {"Diagnosis Quality": 4}),
        }
        session = _session(items, scores)

        result = aggregate_scores([session])

        assert len(result) == 1
        stat = result[0]
        assert stat.dimension == "Diagnosis Quality"
        assert stat.model == "gpt-4"
        assert stat.condition == "dodar"
        assert stat.count == 3
        assert stat.mean == 4.0
        expected_std = round(math.sqrt(2 / 3), 2)
        assert stat.std == expected_std

    def test_second_manual_verification(self):
        """Second manual math check.

        Scores: [2, 2, 4, 4]
        Mean = 12/4 = 3.0
        Pop variance = ((2-3)^2 + (2-3)^2 + (4-3)^2 + (4-3)^2) / 4 = 4/4 = 1
        Std = 1.0
        """
        items = [
            _blind_item(f"i{n}", model="claude-3", condition="cot")
            for n in range(4)
        ]
        scores = {
            f"i{n}": _score_card(f"i{n}", {"Option Breadth": s})
            for n, s in enumerate([2, 2, 4, 4])
        }
        session = _session(items, scores)

        result = aggregate_scores([session])

        assert len(result) == 1
        stat = result[0]
        assert stat.mean == 3.0
        assert stat.std == 1.0
        assert stat.count == 4

    def test_multiple_dimensions(self):
        """Each dimension produces its own DimensionStats entry."""
        items = [_blind_item("x", model="gpt-4", condition="dodar")]
        scores = {
            "x": _score_card("x", {
                "Diagnosis Quality": 4,
                "Option Breadth": 2,
            }),
        }
        session = _session(items, scores)

        result = aggregate_scores([session])

        dims = {s.dimension for s in result}
        assert dims == {"Diagnosis Quality", "Option Breadth"}

    def test_multiple_models_and_conditions(self):
        """Scores are bucketed separately per (model, condition, dimension)."""
        items = [
            _blind_item("a", model="gpt-4", condition="dodar"),
            _blind_item("b", model="gpt-4", condition="zero_shot"),
            _blind_item("c", model="claude-3", condition="dodar"),
        ]
        scores = {
            "a": _score_card("a", {"Diagnosis Quality": 5}),
            "b": _score_card("b", {"Diagnosis Quality": 3}),
            "c": _score_card("c", {"Diagnosis Quality": 1}),
        }
        session = _session(items, scores)

        result = aggregate_scores([session])

        lookup = {(s.model, s.condition): s for s in result}
        assert lookup[("gpt-4", "dodar")].mean == 5.0
        assert lookup[("gpt-4", "zero_shot")].mean == 3.0
        assert lookup[("claude-3", "dodar")].mean == 1.0

    def test_multiple_sessions_merged(self):
        """Scores from multiple sessions aggregate into the same buckets."""
        items_a = [_blind_item("a1", model="gpt-4", condition="dodar")]
        scores_a = {"a1": _score_card("a1", {"Diagnosis Quality": 2})}
        sess_a = _session(items_a, scores_a, session_id="sess-a")

        items_b = [_blind_item("b1", model="gpt-4", condition="dodar")]
        scores_b = {"b1": _score_card("b1", {"Diagnosis Quality": 4})}
        sess_b = _session(items_b, scores_b, session_id="sess-b")

        result = aggregate_scores([sess_a, sess_b])

        assert len(result) == 1
        stat = result[0]
        assert stat.count == 2
        assert stat.mean == 3.0  # (2+4)/2

    def test_empty_sessions_list(self):
        """No sessions => no stats."""
        result = aggregate_scores([])
        assert result == []

    def test_session_with_no_scores(self):
        """Session has items but no scores submitted yet."""
        items = [_blind_item("a")]
        session = _session(items, scores={})

        result = aggregate_scores([session])
        assert result == []

    def test_single_item(self):
        """Single score: mean equals the score, std is 0 (variance / 1 branch => 0)."""
        items = [_blind_item("only")]
        scores = {"only": _score_card("only", {"Diagnosis Quality": 3})}
        session = _session(items, scores)

        result = aggregate_scores([session])

        assert len(result) == 1
        stat = result[0]
        assert stat.mean == 3.0
        # n=1, variance branch: sum()/n with n>1 false => variance=0
        assert stat.std == 0.0
        assert stat.count == 1

    def test_all_same_scores(self):
        """When all scores are identical, std should be 0."""
        items = [_blind_item(f"i{n}") for n in range(5)]
        scores = {
            f"i{n}": _score_card(f"i{n}", {"Diagnosis Quality": 4})
            for n in range(5)
        }
        session = _session(items, scores)

        result = aggregate_scores([session])

        assert result[0].mean == 4.0
        assert result[0].std == 0.0

    def test_prompt_version_filter_includes(self):
        """Only items matching prompt_version are included."""
        items = [
            _blind_item("v1_item", prompt_version="v1"),
            _blind_item("v2_item", prompt_version="v2"),
        ]
        scores = {
            "v1_item": _score_card("v1_item", {"Diagnosis Quality": 5}),
            "v2_item": _score_card("v2_item", {"Diagnosis Quality": 1}),
        }
        session = _session(items, scores)

        result = aggregate_scores([session], prompt_version="v1")

        assert len(result) == 1
        assert result[0].mean == 5.0
        assert result[0].count == 1

    def test_prompt_version_filter_excludes_all(self):
        """If no items match the prompt_version, result is empty."""
        items = [_blind_item("a", prompt_version="v1")]
        scores = {"a": _score_card("a", {"Diagnosis Quality": 3})}
        session = _session(items, scores)

        result = aggregate_scores([session], prompt_version="v99")
        assert result == []

    def test_prompt_version_none_includes_all(self):
        """When prompt_version is None, all items are included."""
        items = [
            _blind_item("a", prompt_version="v1"),
            _blind_item("b", prompt_version="v2"),
        ]
        scores = {
            "a": _score_card("a", {"Diagnosis Quality": 2}),
            "b": _score_card("b", {"Diagnosis Quality": 4}),
        }
        session = _session(items, scores)

        result = aggregate_scores([session], prompt_version=None)

        assert len(result) == 1
        assert result[0].count == 2
        assert result[0].mean == 3.0

    def test_score_for_missing_item_ignored(self):
        """A score whose item_id has no matching BlindItem is silently ignored."""
        items = [_blind_item("exists")]
        scores = {
            "exists": _score_card("exists", {"Diagnosis Quality": 4}),
            "ghost": _score_card("ghost", {"Diagnosis Quality": 1}),
        }
        session = _session(items, scores)

        result = aggregate_scores([session])

        assert len(result) == 1
        assert result[0].count == 1
        assert result[0].mean == 4.0

    def test_results_are_sorted(self):
        """Stats list is sorted by (model, condition, dimension) tuple."""
        items = [
            _blind_item("a", model="z-model", condition="dodar"),
            _blind_item("b", model="a-model", condition="zero_shot"),
        ]
        scores = {
            "a": _score_card("a", {"Diagnosis Quality": 3}),
            "b": _score_card("b", {"Diagnosis Quality": 4}),
        }
        session = _session(items, scores)

        result = aggregate_scores([session])

        models = [s.model for s in result]
        assert models == sorted(models)


# ---------------------------------------------------------------------------
# compute_effect_sizes tests
# ---------------------------------------------------------------------------

class TestComputeEffectSizes:
    """Tests for compute_effect_sizes."""

    def _make_stat(
        self,
        dim: str,
        model: str,
        condition: str,
        mean: float,
        std: float,
        count: int = 10,
    ) -> DimensionStats:
        return DimensionStats(
            dimension=dim,
            model=model,
            condition=condition,
            mean=mean,
            std=std,
            count=count,
        )

    def test_basic_cohens_d(self):
        """Manual Cohen's d check.

        dodar:     mean=4.0, std=0.5
        zero_shot: mean=3.0, std=0.5
        pooled_std = sqrt((0.5^2 + 0.5^2) / 2) = sqrt(0.25) = 0.5
        d = (4.0 - 3.0) / 0.5 = 2.0
        """
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "dodar", 4.0, 0.5),
            self._make_stat("Diagnosis Quality", "gpt-4", "zero_shot", 3.0, 0.5),
        ]

        effects = compute_effect_sizes(stats)

        assert len(effects) == 1
        e = effects[0]
        assert e.dimension == "Diagnosis Quality"
        assert e.model == "gpt-4"
        assert e.baseline_condition == "zero_shot"
        assert e.cohens_d == 2.0
        assert e.dodar_mean == 4.0
        assert e.baseline_mean == 3.0

    def test_second_manual_cohens_d(self):
        """Second manual verification.

        dodar:         mean=3.5, std=1.0
        length_matched: mean=2.5, std=0.5
        pooled_std = sqrt((1.0^2 + 0.5^2) / 2) = sqrt(1.25/2) = sqrt(0.625) ~ 0.7906
        d = (3.5 - 2.5) / 0.7906 ~ 1.265
        """
        stats = [
            self._make_stat("Option Breadth", "claude-3", "dodar", 3.5, 1.0),
            self._make_stat("Option Breadth", "claude-3", "length_matched", 2.5, 0.5),
        ]

        effects = compute_effect_sizes(stats)

        assert len(effects) == 1
        e = effects[0]
        expected_pooled = math.sqrt((1.0**2 + 0.5**2) / 2)
        expected_d = round((3.5 - 2.5) / expected_pooled, 3)
        assert e.cohens_d == expected_d

    def test_negative_effect_size(self):
        """When dodar mean is lower than baseline, Cohen's d is negative."""
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "dodar", 2.0, 1.0),
            self._make_stat("Diagnosis Quality", "gpt-4", "zero_shot", 4.0, 1.0),
        ]

        effects = compute_effect_sizes(stats)

        assert len(effects) == 1
        assert effects[0].cohens_d == -2.0

    def test_multiple_baselines(self):
        """Effect sizes computed for every available baseline condition."""
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "dodar", 4.0, 1.0),
            self._make_stat("Diagnosis Quality", "gpt-4", "zero_shot", 3.0, 1.0),
            self._make_stat("Diagnosis Quality", "gpt-4", "cot", 3.5, 1.0),
            self._make_stat("Diagnosis Quality", "gpt-4", "length_matched", 2.5, 1.0),
        ]

        effects = compute_effect_sizes(stats)

        baselines = {e.baseline_condition for e in effects}
        assert baselines == {"zero_shot", "cot", "length_matched"}

    def test_skip_when_dodar_missing(self):
        """No effect sizes produced when there is no dodar condition."""
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "zero_shot", 3.0, 1.0),
            self._make_stat("Diagnosis Quality", "gpt-4", "cot", 3.5, 1.0),
        ]

        effects = compute_effect_sizes(stats)
        assert effects == []

    def test_skip_when_baseline_missing(self):
        """No effect sizes produced when there are no baseline conditions."""
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "dodar", 4.0, 1.0),
        ]

        effects = compute_effect_sizes(stats)
        assert effects == []

    def test_skip_when_count_less_than_2(self):
        """Conditions with count < 2 are excluded from effect size computation."""
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "dodar", 4.0, 1.0, count=1),
            self._make_stat("Diagnosis Quality", "gpt-4", "zero_shot", 3.0, 1.0, count=10),
        ]

        effects = compute_effect_sizes(stats)
        assert effects == []

    def test_skip_when_baseline_count_less_than_2(self):
        """Baseline with count < 2 is skipped."""
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "dodar", 4.0, 1.0, count=10),
            self._make_stat("Diagnosis Quality", "gpt-4", "zero_shot", 3.0, 1.0, count=1),
        ]

        effects = compute_effect_sizes(stats)
        assert effects == []

    def test_zero_pooled_std(self):
        """When both stds are 0, Cohen's d should be 0 (not a division error)."""
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "dodar", 4.0, 0.0),
            self._make_stat("Diagnosis Quality", "gpt-4", "zero_shot", 3.0, 0.0),
        ]

        effects = compute_effect_sizes(stats)

        assert len(effects) == 1
        assert effects[0].cohens_d == 0.0

    def test_empty_stats(self):
        """Empty stats list => no effect sizes."""
        assert compute_effect_sizes([]) == []

    def test_only_known_dimensions_used(self):
        """compute_effect_sizes only iterates SCORING_DIMENSIONS, so unknown
        dimensions are ignored even if present in stats."""
        stats = [
            self._make_stat("Made Up Dimension", "gpt-4", "dodar", 5.0, 0.5),
            self._make_stat("Made Up Dimension", "gpt-4", "zero_shot", 2.0, 0.5),
        ]

        effects = compute_effect_sizes(stats)
        assert effects == []

    def test_multiple_models(self):
        """Effect sizes computed independently per model."""
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "dodar", 4.0, 1.0),
            self._make_stat("Diagnosis Quality", "gpt-4", "zero_shot", 3.0, 1.0),
            self._make_stat("Diagnosis Quality", "claude-3", "dodar", 5.0, 1.0),
            self._make_stat("Diagnosis Quality", "claude-3", "zero_shot", 2.0, 1.0),
        ]

        effects = compute_effect_sizes(stats)

        by_model = {e.model: e for e in effects}
        assert by_model["gpt-4"].cohens_d == 1.0
        assert by_model["claude-3"].cohens_d == 3.0

    def test_effect_size_across_dimensions(self):
        """Multiple dimensions produce separate EffectSize entries."""
        stats = [
            self._make_stat("Diagnosis Quality", "gpt-4", "dodar", 4.0, 1.0),
            self._make_stat("Diagnosis Quality", "gpt-4", "zero_shot", 3.0, 1.0),
            self._make_stat("Option Breadth", "gpt-4", "dodar", 5.0, 1.0),
            self._make_stat("Option Breadth", "gpt-4", "zero_shot", 2.0, 1.0),
        ]

        effects = compute_effect_sizes(stats)

        dims = {e.dimension for e in effects}
        assert dims == {"Diagnosis Quality", "Option Breadth"}
        by_dim = {e.dimension: e for e in effects}
        assert by_dim["Diagnosis Quality"].cohens_d == 1.0
        assert by_dim["Option Breadth"].cohens_d == 3.0
