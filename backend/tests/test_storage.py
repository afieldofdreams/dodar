"""Comprehensive tests for the DODAR storage layer.

Covers:
  - dodar.storage.runs   (make_run_id, result_path, result_exists, save_result,
                           load_result, load_all_results, save_run_summary,
                           load_run_summary, load_all_run_summaries, delete_run)
  - dodar.storage.scores  (session_path, save_session, load_session,
                           load_all_sessions, delete_session)
  - dodar.storage.scenarios (load_all_scenarios, get_scenario_by_id,
                             load_scenarios_filtered)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from dodar.config import Settings
from dodar.models.run import RunConfig, RunResult, RunStatus, RunSummary, RunItemProgress
from dodar.models.scoring import (
    BlindItem,
    DimensionScore,
    ScoreCard,
    ScoringSession,
)
from dodar.models.scenario import Scenario
from dodar.storage import runs, scores, scenarios


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def _make_settings(tmp_path: Path) -> Settings:
    """Build a Settings object pointing at temp directories."""
    runs_dir = tmp_path / "runs"
    scores_dir = tmp_path / "scores"
    scenarios_dir = tmp_path / "scenarios"
    runs_dir.mkdir()
    scores_dir.mkdir()
    scenarios_dir.mkdir()
    return Settings(
        runs_dir=runs_dir,
        scores_dir=scores_dir,
        scenarios_dir=scenarios_dir,
        data_dir=tmp_path,
    )


@pytest.fixture()
def settings(tmp_path: Path):
    """Yield a Settings wired to tmp_path and patch get_settings globally."""
    s = _make_settings(tmp_path)
    with patch("dodar.storage.runs.get_settings", return_value=s), \
         patch("dodar.storage.scores.get_settings", return_value=s), \
         patch("dodar.storage.scenarios.get_settings", return_value=s):
        yield s


NOW = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


def _sample_run_result(
    scenario_id: str = "sc1",
    model: str = "gpt-4o",
    condition: str = "zero_shot",
    prompt_version: str = "v1",
) -> RunResult:
    run_id = runs.make_run_id(scenario_id, model, condition, prompt_version)
    return RunResult(
        run_id=run_id,
        scenario_id=scenario_id,
        model=model,
        condition=condition,
        prompt_version=prompt_version,
        timestamp=NOW,
        prompt_sent="test prompt",
        response_text="test response",
        input_tokens=100,
        output_tokens=200,
        latency_seconds=1.5,
        cost_usd=0.005,
    )


def _sample_run_config(
    scenario_ids: list[str] | None = None,
    models: list[str] | None = None,
    conditions: list[str] | None = None,
    prompt_version: str = "v1",
) -> RunConfig:
    return RunConfig(
        scenario_ids=scenario_ids or ["sc1"],
        models=models or ["gpt-4o"],
        conditions=conditions or ["zero_shot"],
        prompt_version=prompt_version,
    )


def _sample_run_summary(
    run_id: str = "run-001",
    config: RunConfig | None = None,
    prompt_version: str = "v1",
) -> RunSummary:
    cfg = config or _sample_run_config(prompt_version=prompt_version)
    return RunSummary(
        run_id=run_id,
        config=cfg,
        status=RunStatus.COMPLETED,
        created_at=NOW,
        prompt_version=prompt_version,
        total_items=1,
        completed_items=1,
    )


def _sample_scoring_session(
    session_id: str = "sess-001",
    scorer: str = "tester",
    run_id: str = "run-001",
) -> ScoringSession:
    item = BlindItem(
        item_id="item-1",
        scenario_id="sc1",
        model="gpt-4o",
        condition="zero_shot",
        run_result_file="sc1_gpt-4o_zero_shot.json",
    )
    return ScoringSession(
        session_id=session_id,
        scorer=scorer,
        run_id=run_id,
        created_at=NOW,
        seed=42,
        items=[item],
        order=["item-1"],
    )


def _sample_scenario(
    id: str = "sc1",
    category: str = "MEDICAL",
    domain: str = "healthcare",
    difficulty: str = "medium",
) -> Scenario:
    return Scenario(
        id=id,
        category=category,
        title=f"Scenario {id}",
        domain=domain,
        difficulty=difficulty,
        prompt_text=f"Prompt for {id}",
        expected_pitfalls=["pitfall1"],
        gold_standard_elements=["element1"],
        discriminators=[],
    )


def _write_scenario_yaml(scenarios_dir: Path, filename: str, scenario_list: list[Scenario]) -> None:
    data = {"scenarios": [s.model_dump() for s in scenario_list]}
    (scenarios_dir / filename).write_text(yaml.dump(data, default_flow_style=False))


# ===================================================================
# RUNS MODULE
# ===================================================================


class TestMakeRunId:
    def test_default_v1_omits_version(self):
        assert runs.make_run_id("sc1", "gpt-4o", "cot") == "sc1_gpt-4o_cot"

    def test_explicit_v1_omits_version(self):
        assert runs.make_run_id("sc1", "gpt-4o", "cot", "v1") == "sc1_gpt-4o_cot"

    def test_non_v1_includes_version(self):
        assert runs.make_run_id("sc1", "gpt-4o", "cot", "v2") == "sc1_gpt-4o_cot_v2"


class TestResultPath:
    def test_returns_correct_path(self, settings):
        path = runs.result_path("sc1_gpt-4o_cot")
        assert path == settings.runs_dir / "sc1_gpt-4o_cot.json"


class TestResultExists:
    def test_false_when_missing(self, settings):
        assert runs.result_exists("nonexistent") is False

    def test_true_when_present(self, settings):
        (settings.runs_dir / "existing.json").write_text("{}")
        assert runs.result_exists("existing") is True


class TestSaveAndLoadResult:
    def test_roundtrip(self, settings):
        result = _sample_run_result()
        runs.save_result(result)

        loaded = runs.load_result(result.run_id)
        assert loaded is not None
        assert loaded.run_id == result.run_id
        assert loaded.scenario_id == result.scenario_id
        assert loaded.model == result.model
        assert loaded.condition == result.condition
        assert loaded.prompt_version == result.prompt_version
        assert loaded.response_text == result.response_text
        assert loaded.input_tokens == result.input_tokens

    def test_load_missing_returns_none(self, settings):
        assert runs.load_result("does_not_exist") is None

    def test_save_creates_file(self, settings):
        result = _sample_run_result()
        runs.save_result(result)
        assert (settings.runs_dir / f"{result.run_id}.json").exists()

    def test_save_overwrites(self, settings):
        r1 = _sample_run_result()
        runs.save_result(r1)

        r2 = r1.model_copy(update={"response_text": "updated"})
        runs.save_result(r2)

        loaded = runs.load_result(r1.run_id)
        assert loaded is not None
        assert loaded.response_text == "updated"


class TestLoadAllResults:
    def test_empty_dir(self, settings):
        assert runs.load_all_results() == []

    def test_returns_all(self, settings):
        r1 = _sample_run_result(scenario_id="sc1")
        r2 = _sample_run_result(scenario_id="sc2")
        runs.save_result(r1)
        runs.save_result(r2)
        results = runs.load_all_results()
        assert len(results) == 2

    def test_filter_by_prompt_version(self, settings):
        r1 = _sample_run_result(prompt_version="v1")
        r2 = _sample_run_result(scenario_id="sc2", prompt_version="v2")
        runs.save_result(r1)
        runs.save_result(r2)

        v1_only = runs.load_all_results(prompt_version="v1")
        assert len(v1_only) == 1
        assert v1_only[0].prompt_version == "v1"

        v2_only = runs.load_all_results(prompt_version="v2")
        assert len(v2_only) == 1
        assert v2_only[0].prompt_version == "v2"

    def test_skips_run_summary_files(self, settings):
        r = _sample_run_result()
        runs.save_result(r)
        summary = _sample_run_summary()
        runs.save_run_summary(summary)

        results = runs.load_all_results()
        assert len(results) == 1
        assert results[0].run_id == r.run_id

    def test_skips_invalid_json(self, settings):
        r = _sample_run_result()
        runs.save_result(r)
        (settings.runs_dir / "bad.json").write_text("not json{{{")

        results = runs.load_all_results()
        assert len(results) == 1

    def test_no_filter_returns_all_versions(self, settings):
        r1 = _sample_run_result(prompt_version="v1")
        r2 = _sample_run_result(scenario_id="sc2", prompt_version="v2")
        runs.save_result(r1)
        runs.save_result(r2)

        results = runs.load_all_results(prompt_version=None)
        assert len(results) == 2


class TestRunSummary:
    def test_save_and_load_roundtrip(self, settings):
        summary = _sample_run_summary(run_id="run-42")
        runs.save_run_summary(summary)

        loaded = runs.load_run_summary("run-42")
        assert loaded is not None
        assert loaded.run_id == "run-42"
        assert loaded.status == RunStatus.COMPLETED

    def test_load_missing_returns_none(self, settings):
        assert runs.load_run_summary("nonexistent") is None

    def test_summary_file_naming(self, settings):
        summary = _sample_run_summary(run_id="run-99")
        runs.save_run_summary(summary)
        assert (settings.runs_dir / "_run_run-99.json").exists()

    def test_load_all_summaries_empty(self, settings):
        assert runs.load_all_run_summaries() == []

    def test_load_all_summaries(self, settings):
        s1 = _sample_run_summary(run_id="run-1")
        s2 = _sample_run_summary(run_id="run-2")
        runs.save_run_summary(s1)
        runs.save_run_summary(s2)

        loaded = runs.load_all_run_summaries()
        assert len(loaded) == 2
        ids = {s.run_id for s in loaded}
        assert ids == {"run-1", "run-2"}

    def test_load_all_summaries_skips_invalid(self, settings):
        s = _sample_run_summary(run_id="good")
        runs.save_run_summary(s)
        (settings.runs_dir / "_run_bad.json").write_text("{{invalid json")

        loaded = runs.load_all_run_summaries()
        assert len(loaded) == 1
        assert loaded[0].run_id == "good"

    def test_summary_with_items(self, settings):
        item = RunItemProgress(
            scenario_id="sc1",
            model="gpt-4o",
            condition="zero_shot",
            status=RunStatus.COMPLETED,
            tokens_used=300,
            cost_usd=0.005,
        )
        summary = _sample_run_summary(run_id="run-with-items")
        summary = summary.model_copy(update={"items": [item]})
        runs.save_run_summary(summary)

        loaded = runs.load_run_summary("run-with-items")
        assert loaded is not None
        assert len(loaded.items) == 1
        assert loaded.items[0].scenario_id == "sc1"


class TestDeleteRun:
    def test_delete_summary_and_results(self, settings):
        # Save a result that matches the summary config
        result = _sample_run_result(scenario_id="sc1", model="gpt-4o", condition="zero_shot")
        runs.save_result(result)

        config = _sample_run_config(
            scenario_ids=["sc1"], models=["gpt-4o"], conditions=["zero_shot"]
        )
        summary = _sample_run_summary(run_id="run-del", config=config)
        runs.save_run_summary(summary)

        deleted = runs.delete_run("run-del")
        assert deleted == 2  # summary + 1 result

        assert runs.load_run_summary("run-del") is None
        assert runs.load_result(result.run_id) is None

    def test_delete_nonexistent_run(self, settings):
        deleted = runs.delete_run("no-such-run")
        assert deleted == 0

    def test_delete_summary_only_no_matching_results(self, settings):
        config = _sample_run_config(
            scenario_ids=["sc99"], models=["model-x"], conditions=["cot"]
        )
        summary = _sample_run_summary(run_id="run-no-results", config=config)
        runs.save_run_summary(summary)

        deleted = runs.delete_run("run-no-results")
        assert deleted == 1  # just the summary

    def test_delete_leaves_unrelated_results(self, settings):
        # Result matching the run
        r_match = _sample_run_result(scenario_id="sc1", model="gpt-4o", condition="zero_shot")
        runs.save_result(r_match)
        # Unrelated result
        r_other = _sample_run_result(scenario_id="sc2", model="gpt-4o", condition="cot")
        runs.save_result(r_other)

        config = _sample_run_config(
            scenario_ids=["sc1"], models=["gpt-4o"], conditions=["zero_shot"]
        )
        summary = _sample_run_summary(run_id="run-partial", config=config)
        runs.save_run_summary(summary)

        runs.delete_run("run-partial")
        assert runs.load_result(r_other.run_id) is not None

    def test_delete_skips_invalid_json_files(self, settings):
        config = _sample_run_config(scenario_ids=["sc1"], models=["gpt-4o"], conditions=["zero_shot"])
        summary = _sample_run_summary(run_id="run-bad", config=config)
        runs.save_run_summary(summary)
        (settings.runs_dir / "corrupt.json").write_text("not valid json")

        deleted = runs.delete_run("run-bad")
        assert deleted == 1  # summary only, corrupt file skipped
        assert (settings.runs_dir / "corrupt.json").exists()


# ===================================================================
# SCORES MODULE
# ===================================================================


class TestSessionPath:
    def test_returns_correct_path(self, settings):
        path = scores.session_path("sess-abc")
        assert path == settings.scores_dir / "sess-abc.json"


class TestSaveAndLoadSession:
    def test_roundtrip(self, settings):
        session = _sample_scoring_session()
        scores.save_session(session)

        loaded = scores.load_session(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.scorer == session.scorer
        assert loaded.seed == session.seed
        assert len(loaded.items) == 1
        assert loaded.order == ["item-1"]

    def test_load_missing_returns_none(self, settings):
        assert scores.load_session("nonexistent") is None

    def test_save_creates_file(self, settings):
        session = _sample_scoring_session(session_id="sess-file")
        scores.save_session(session)
        assert (settings.scores_dir / "sess-file.json").exists()

    def test_save_overwrites(self, settings):
        session = _sample_scoring_session()
        scores.save_session(session)

        updated = session.model_copy(update={"scorer": "new-scorer"})
        scores.save_session(updated)

        loaded = scores.load_session(session.session_id)
        assert loaded is not None
        assert loaded.scorer == "new-scorer"

    def test_session_with_scores(self, settings):
        session = _sample_scoring_session()
        card = ScoreCard(
            item_id="item-1",
            scores=[
                DimensionScore(dimension="Diagnosis Quality", score=4, rationale="Good"),
                DimensionScore(dimension="Action Specificity", score=3),
            ],
            scored_at=NOW,
        )
        session = session.model_copy(update={"scores": {"item-1": card}})
        scores.save_session(session)

        loaded = scores.load_session(session.session_id)
        assert loaded is not None
        assert "item-1" in loaded.scores
        assert loaded.scores["item-1"].scores[0].score == 4
        assert loaded.scores["item-1"].scores[0].rationale == "Good"

    def test_session_revealed_flag(self, settings):
        session = _sample_scoring_session()
        session = session.model_copy(update={"revealed": True})
        scores.save_session(session)

        loaded = scores.load_session(session.session_id)
        assert loaded is not None
        assert loaded.revealed is True


class TestLoadAllSessions:
    def test_empty_dir(self, settings):
        assert scores.load_all_sessions() == []

    def test_returns_all(self, settings):
        s1 = _sample_scoring_session(session_id="s1")
        s2 = _sample_scoring_session(session_id="s2")
        scores.save_session(s1)
        scores.save_session(s2)

        loaded = scores.load_all_sessions()
        assert len(loaded) == 2

    def test_skips_invalid_json(self, settings):
        s = _sample_scoring_session(session_id="good")
        scores.save_session(s)
        (settings.scores_dir / "bad.json").write_text("{{not valid")

        loaded = scores.load_all_sessions()
        assert len(loaded) == 1
        assert loaded[0].session_id == "good"

    def test_sorted_by_filename(self, settings):
        s_b = _sample_scoring_session(session_id="b-session")
        s_a = _sample_scoring_session(session_id="a-session")
        scores.save_session(s_b)
        scores.save_session(s_a)

        loaded = scores.load_all_sessions()
        assert loaded[0].session_id == "a-session"
        assert loaded[1].session_id == "b-session"


class TestDeleteSession:
    def test_delete_existing(self, settings):
        session = _sample_scoring_session(session_id="del-me")
        scores.save_session(session)

        assert scores.delete_session("del-me") is True
        assert scores.load_session("del-me") is None

    def test_delete_nonexistent(self, settings):
        assert scores.delete_session("no-such") is False

    def test_delete_idempotent(self, settings):
        session = _sample_scoring_session(session_id="once")
        scores.save_session(session)

        assert scores.delete_session("once") is True
        assert scores.delete_session("once") is False


# ===================================================================
# SCENARIOS MODULE
# ===================================================================


class TestLoadAllScenarios:
    def test_empty_dir(self, settings):
        result = scenarios.load_all_scenarios()
        assert result == []

    def test_loads_from_yaml(self, settings):
        sc = _sample_scenario(id="test-1")
        _write_scenario_yaml(settings.scenarios_dir, "file1.yaml", [sc])

        loaded = scenarios.load_all_scenarios()
        assert len(loaded) == 1
        assert loaded[0].id == "test-1"

    def test_loads_from_multiple_files(self, settings):
        sc1 = _sample_scenario(id="a-1")
        sc2 = _sample_scenario(id="b-1")
        _write_scenario_yaml(settings.scenarios_dir, "a.yaml", [sc1])
        _write_scenario_yaml(settings.scenarios_dir, "b.yaml", [sc2])

        loaded = scenarios.load_all_scenarios()
        assert len(loaded) == 2

    def test_multiple_scenarios_in_one_file(self, settings):
        sc1 = _sample_scenario(id="s1")
        sc2 = _sample_scenario(id="s2")
        _write_scenario_yaml(settings.scenarios_dir, "multi.yaml", [sc1, sc2])

        loaded = scenarios.load_all_scenarios()
        assert len(loaded) == 2

    def test_empty_yaml_file(self, settings):
        (settings.scenarios_dir / "empty.yaml").write_text("")
        loaded = scenarios.load_all_scenarios()
        assert loaded == []

    def test_ignores_non_yaml_files(self, settings):
        sc = _sample_scenario(id="only")
        _write_scenario_yaml(settings.scenarios_dir, "real.yaml", [sc])
        (settings.scenarios_dir / "notes.txt").write_text("ignore me")

        loaded = scenarios.load_all_scenarios()
        assert len(loaded) == 1

    def test_preserves_scenario_fields(self, settings):
        sc = _sample_scenario(
            id="detail",
            category="LEGAL",
            domain="law",
            difficulty="hard",
        )
        _write_scenario_yaml(settings.scenarios_dir, "detail.yaml", [sc])

        loaded = scenarios.load_all_scenarios()
        s = loaded[0]
        assert s.id == "detail"
        assert s.category == "LEGAL"
        assert s.domain == "law"
        assert s.difficulty == "hard"
        assert s.expected_pitfalls == ["pitfall1"]
        assert s.gold_standard_elements == ["element1"]


class TestGetScenarioById:
    def test_found(self, settings):
        sc = _sample_scenario(id="find-me")
        _write_scenario_yaml(settings.scenarios_dir, "sc.yaml", [sc])

        result = scenarios.get_scenario_by_id("find-me")
        assert result is not None
        assert result.id == "find-me"

    def test_not_found(self, settings):
        sc = _sample_scenario(id="other")
        _write_scenario_yaml(settings.scenarios_dir, "sc.yaml", [sc])

        assert scenarios.get_scenario_by_id("missing") is None

    def test_empty_dir(self, settings):
        assert scenarios.get_scenario_by_id("anything") is None


class TestLoadScenariosFiltered:
    @pytest.fixture(autouse=True)
    def _seed_scenarios(self, settings):
        sc_list = [
            _sample_scenario(id="med-1", category="MEDICAL", domain="healthcare", difficulty="easy"),
            _sample_scenario(id="med-2", category="MEDICAL", domain="healthcare", difficulty="hard"),
            _sample_scenario(id="legal-1", category="LEGAL", domain="law", difficulty="medium"),
        ]
        _write_scenario_yaml(settings.scenarios_dir, "all.yaml", sc_list)

    def test_no_filters(self, settings):
        result = scenarios.load_scenarios_filtered()
        assert len(result) == 3

    def test_filter_by_category(self, settings):
        result = scenarios.load_scenarios_filtered(category="MEDICAL")
        assert len(result) == 2
        assert all(s.category == "MEDICAL" for s in result)

    def test_filter_by_category_case_insensitive(self, settings):
        result = scenarios.load_scenarios_filtered(category="medical")
        assert len(result) == 2

    def test_filter_by_difficulty(self, settings):
        result = scenarios.load_scenarios_filtered(difficulty="hard")
        assert len(result) == 1
        assert result[0].id == "med-2"

    def test_filter_by_domain(self, settings):
        result = scenarios.load_scenarios_filtered(domain="Law")
        assert len(result) == 1
        assert result[0].id == "legal-1"

    def test_filter_by_ids(self, settings):
        result = scenarios.load_scenarios_filtered(ids=["med-1", "legal-1"])
        assert len(result) == 2
        ids = {s.id for s in result}
        assert ids == {"med-1", "legal-1"}

    def test_filter_by_search(self, settings):
        result = scenarios.load_scenarios_filtered(search="med-1")
        assert len(result) == 1
        assert result[0].id == "med-1"

    def test_combined_filters(self, settings):
        result = scenarios.load_scenarios_filtered(category="MEDICAL", difficulty="easy")
        assert len(result) == 1
        assert result[0].id == "med-1"

    def test_no_matches(self, settings):
        result = scenarios.load_scenarios_filtered(category="NONEXISTENT")
        assert result == []
