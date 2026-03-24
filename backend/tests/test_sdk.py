"""Tests for dodar.sdk — parsing logic and DODAR class."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dodar.runners.base import ModelResponse
from dodar.sdk import (
    DODAR,
    DODARResult,
    DiagnosisResult,
    OptionsResult,
    DecisionResult,
    ActionResult,
    ReviewResult,
    _split_phases,
    _extract_list_items,
    _parse_diagnosis,
    _parse_options,
    _parse_decision,
    _parse_action,
    _parse_review,
    _parse_dodar_response,
)


# =========================================================================== #
# Fixtures — sample DODAR-formatted text
# =========================================================================== #

FULL_DODAR_RESPONSE = """\
## Phase 1: DIAGNOSE

Here is the diagnostic analysis.

1. The system is overloaded due to traffic spike
2. A recent deploy introduced a memory leak
3. The database connection pool is exhausted

Assuming the monitoring data is accurate and up to date.
There is an unknown factor: we don't know if the CDN is healthy.
Missing data on the cache hit rate.

## Phase 2: OPTIONS

Core tension: reliability vs. speed-to-market

1. Roll back the latest deploy immediately
2. Scale horizontally by adding more instances
3. Enable circuit breakers and shed load gracefully
4. Do nothing and wait for the traffic spike to subside

Trade-off: rolling back loses the new feature but restores stability.
Trade-off: scaling costs money but keeps the feature live.

## Phase 3: DECIDE

Roll back the latest deploy.

This is the safest option because it addresses the most likely root cause (memory leak) while preserving the ability to redeploy once fixed. We are NOT choosing horizontal scaling because it would only mask the underlying memory leak. We are NOT choosing the do-nothing approach because customer impact is growing.

Confidence: High — the deploy timing correlates strongly with the incident.
Would change my mind if: the rollback does not reduce memory usage within 15 minutes.

## Phase 4: ACTION

1. Notify the team in #incidents channel [REVERSIBLE]
2. Initiate rollback of deploy v2.3.1 via CI/CD pipeline [REVERSIBLE, can revert]
3. Monitor memory and error rates for 15 minutes
4. If stable, mark incident resolved
5. Publish the binary to production registry [IRREVERSIBLE, cannot undo once published]

## Phase 5: REVIEW

1. Failure mode: rollback does not fix the issue because the root cause is the database
2. Failure mode: the rollback introduces a different regression
3. Failure mode: traffic spike overwhelms the system before rollback completes

We must validate the assumption that the deploy caused the memory leak.
Check whether the database is actually healthy.
Abandon this plan and pivot to horizontal scaling if rollback has no effect after 15 min.
Abort if error rates increase after rollback.
"""


@pytest.fixture
def full_response_text() -> str:
    return FULL_DODAR_RESPONSE


# =========================================================================== #
# _split_phases
# =========================================================================== #

class TestSplitPhases:
    def test_splits_all_five_phases(self, full_response_text: str):
        phases = _split_phases(full_response_text)
        assert set(phases.keys()) == {"DIAGNOSE", "OPTIONS", "DECIDE", "ACTION", "REVIEW"}

    def test_phase_content_is_correct(self, full_response_text: str):
        phases = _split_phases(full_response_text)
        assert "overloaded due to traffic spike" in phases["DIAGNOSE"]
        assert "Core tension" in phases["OPTIONS"]
        assert "Roll back the latest deploy" in phases["DECIDE"]
        assert "Notify the team" in phases["ACTION"]
        assert "rollback does not fix" in phases["REVIEW"]

    def test_handles_no_phase_numbers(self):
        text = "## DIAGNOSE\nSome diagnosis.\n## OPTIONS\nSome options."
        phases = _split_phases(text)
        assert "DIAGNOSE" in phases
        assert "OPTIONS" in phases

    def test_handles_lowercase_headers(self):
        text = "## diagnose\nDiag text.\n## options\nOpt text."
        phases = _split_phases(text)
        assert "DIAGNOSE" in phases
        assert "OPTIONS" in phases

    def test_handles_mixed_formats(self):
        text = "## Phase 1: DIAGNOSE\nA\n## OPTIONS\nB\n## Phase 3: DECIDE\nC"
        phases = _split_phases(text)
        assert len(phases) == 3
        assert "A" in phases["DIAGNOSE"]
        assert "B" in phases["OPTIONS"]
        assert "C" in phases["DECIDE"]

    def test_empty_text_returns_empty(self):
        assert _split_phases("") == {}

    def test_text_with_no_headers_returns_empty(self):
        assert _split_phases("Just some text with no DODAR headers.") == {}

    def test_single_phase(self):
        text = "## DIAGNOSE\nOnly one phase here."
        phases = _split_phases(text)
        assert len(phases) == 1
        assert "Only one phase here." in phases["DIAGNOSE"]

    def test_extra_whitespace_in_header(self):
        text = "##  Phase  2 :  OPTIONS\nSome text."
        phases = _split_phases(text)
        assert "OPTIONS" in phases


# =========================================================================== #
# _extract_list_items
# =========================================================================== #

class TestExtractListItems:
    def test_numbered_dot(self):
        text = "1. First item\n2. Second item\n3. Third item"
        assert _extract_list_items(text) == ["First item", "Second item", "Third item"]

    def test_numbered_paren(self):
        text = "1) Alpha\n2) Beta"
        assert _extract_list_items(text) == ["Alpha", "Beta"]

    def test_dash_bullets(self):
        text = "- Foo\n- Bar\n- Baz"
        assert _extract_list_items(text) == ["Foo", "Bar", "Baz"]

    def test_asterisk_bullets(self):
        text = "* One\n* Two"
        assert _extract_list_items(text) == ["One", "Two"]

    def test_bullet_character(self):
        text = "\u2022 Item A\n\u2022 Item B"
        assert _extract_list_items(text) == ["Item A", "Item B"]

    def test_mixed_formats(self):
        text = "1. First\n- Second\n* Third"
        items = _extract_list_items(text)
        assert len(items) == 3

    def test_empty_text(self):
        assert _extract_list_items("") == []

    def test_no_list_items(self):
        assert _extract_list_items("Just a paragraph with no lists.") == []

    def test_strips_whitespace(self):
        text = "1.   padded item   "
        assert _extract_list_items(text) == ["padded item"]

    def test_ignores_non_list_lines(self):
        text = "Some intro text\n1. Actual item\nMore text\n2. Another item"
        items = _extract_list_items(text)
        assert items == ["Actual item", "Another item"]


# =========================================================================== #
# _parse_diagnosis
# =========================================================================== #

class TestParseDiagnosis:
    def test_extracts_hypotheses(self):
        text = "1. Hypothesis A\n2. Hypothesis B\n3. Hypothesis C"
        result = _parse_diagnosis(text)
        assert len(result.hypotheses) == 3
        assert result.hypotheses[0] == "Hypothesis A"

    def test_stores_raw_text(self):
        text = "Some diagnosis text"
        result = _parse_diagnosis(text)
        assert result.raw_text == text

    def test_extracts_assumptions(self):
        text = "1. Hypo\nAssuming the data is correct.\nAnother assumption about coverage."
        result = _parse_diagnosis(text)
        assert len(result.assumptions) >= 1
        assert any("Assuming" in a for a in result.assumptions)

    def test_extracts_unknowns(self):
        text = "1. Hypo\nThere is an unknown variable.\nMissing information about X."
        result = _parse_diagnosis(text)
        assert len(result.unknowns) == 2

    def test_no_assumptions_or_unknowns(self):
        text = "1. Hypo A\n2. Hypo B"
        result = _parse_diagnosis(text)
        assert result.assumptions == []
        assert result.unknowns == []

    def test_empty_text(self):
        result = _parse_diagnosis("")
        assert result.hypotheses == []
        assert result.raw_text == ""

    def test_caps_hypotheses_at_10(self):
        lines = "\n".join(f"{i}. Hypo {i}" for i in range(1, 15))
        result = _parse_diagnosis(lines)
        assert len(result.hypotheses) <= 10


# =========================================================================== #
# _parse_options
# =========================================================================== #

class TestParseOptions:
    def test_extracts_alternatives(self):
        text = "1. Option A\n2. Option B\n3. Option C\n4. Option D"
        result = _parse_options(text)
        assert len(result.alternatives) == 4

    def test_extracts_core_tension(self):
        text = "Core tension: speed versus safety\n1. Option A"
        result = _parse_options(text)
        assert "speed versus safety" in result.core_tension

    def test_extracts_key_tension(self):
        text = "Key tension: cost vs. quality\n1. Opt"
        result = _parse_options(text)
        assert "cost vs. quality" in result.core_tension

    def test_no_core_tension(self):
        text = "1. Option A\n2. Option B"
        result = _parse_options(text)
        assert result.core_tension == ""

    def test_stores_raw_text(self):
        text = "Some options"
        assert _parse_options(text).raw_text == text

    def test_empty_text(self):
        result = _parse_options("")
        assert result.alternatives == []
        assert result.core_tension == ""


# =========================================================================== #
# _parse_decision
# =========================================================================== #

class TestParseDecision:
    def test_extracts_recommendation(self):
        text = "Go with Option A.\n\nBecause it is best."
        result = _parse_decision(text)
        assert result.recommendation == "Go with Option A."

    def test_extracts_confidence(self):
        text = "Recommend X.\n\nConfidence: High"
        result = _parse_decision(text)
        assert "High" in result.confidence

    def test_extracts_falsifiability(self):
        text = "Recommend X.\n\nWould change my mind if costs exceed $1M."
        result = _parse_decision(text)
        assert "change my mind" in result.falsifiability

    def test_extracts_prove_wrong_variant(self):
        text = "Recommend X.\n\nYou could prove wrong this decision if Y happens."
        result = _parse_decision(text)
        assert "prove wrong" in result.falsifiability

    def test_no_confidence_or_falsifiability(self):
        text = "Just do the thing."
        result = _parse_decision(text)
        assert result.confidence == ""
        assert result.falsifiability == ""

    def test_empty_text(self):
        result = _parse_decision("")
        assert result.recommendation == ""

    def test_stores_raw_text(self):
        text = "Decision text here"
        assert _parse_decision(text).raw_text == text


# =========================================================================== #
# _parse_action
# =========================================================================== #

class TestParseAction:
    def test_extracts_steps(self):
        text = "1. Step one\n2. Step two\n3. Step three"
        result = _parse_action(text)
        assert len(result.steps) == 3

    def test_identifies_reversible_steps(self):
        text = "1. Do something reversible that can undo later\n2. Regular step"
        result = _parse_action(text)
        assert len(result.reversible_steps) == 1
        assert "reversible" in result.reversible_steps[0].lower()

    def test_identifies_irreversible_steps(self):
        text = "1. Regular step\n2. This is irreversible and cannot undo"
        result = _parse_action(text)
        assert len(result.irreversible_steps) == 1

    def test_permanent_keyword(self):
        text = "1. Deploy permanent database migration"
        result = _parse_action(text)
        assert len(result.irreversible_steps) == 1

    def test_point_of_no_return(self):
        text = "1. This is the point of no return step"
        result = _parse_action(text)
        assert len(result.irreversible_steps) == 1

    def test_low_risk_reversible(self):
        text = "1. A low risk configuration change"
        result = _parse_action(text)
        assert len(result.reversible_steps) == 1

    def test_no_reversibility_markers(self):
        text = "1. Just do something\n2. Then do another thing"
        result = _parse_action(text)
        assert result.reversible_steps == []
        assert result.irreversible_steps == []

    def test_empty_text(self):
        result = _parse_action("")
        assert result.steps == []

    def test_stores_raw_text(self):
        assert _parse_action("text").raw_text == "text"


# =========================================================================== #
# _parse_review
# =========================================================================== #

class TestParseReview:
    def test_extracts_failure_modes(self):
        text = "1. System crashes under load\n2. Data corruption\n3. Timeout errors"
        result = _parse_review(text)
        assert len(result.failure_modes) == 3

    def test_extracts_assumptions_to_validate(self):
        text = "1. Failure\nWe must validate the assumption that X is true.\nCheck whether Y holds."
        result = _parse_review(text)
        assert len(result.assumptions_to_validate) >= 1

    def test_extracts_abort_conditions(self):
        text = "1. Failure\nAbandon this plan if X happens.\nAbort if error rate exceeds 5%."
        result = _parse_review(text)
        assert len(result.abort_conditions) == 2

    def test_pivot_keyword(self):
        text = "1. F\nPivot to plan B if metrics decline."
        result = _parse_review(text)
        assert len(result.abort_conditions) == 1

    def test_bail_keyword(self):
        text = "1. F\nBail on this approach if it fails."
        result = _parse_review(text)
        assert len(result.abort_conditions) == 1

    def test_switch_to_keyword(self):
        text = "1. F\nSwitch to alternative if costs rise."
        result = _parse_review(text)
        assert len(result.abort_conditions) == 1

    def test_no_special_sections(self):
        text = "1. Failure mode one\n2. Failure mode two"
        result = _parse_review(text)
        assert result.assumptions_to_validate == []
        assert result.abort_conditions == []

    def test_empty_text(self):
        result = _parse_review("")
        assert result.failure_modes == []

    def test_stores_raw_text(self):
        assert _parse_review("text").raw_text == "text"


# =========================================================================== #
# _parse_dodar_response (integration of parsing)
# =========================================================================== #

class TestParseDODARResponse:
    def test_full_parse(self, full_response_text: str):
        result = _parse_dodar_response(full_response_text)
        assert isinstance(result, DODARResult)
        assert result.text == full_response_text
        # Diagnosis
        assert len(result.diagnosis.hypotheses) == 3
        assert any("overloaded" in h for h in result.diagnosis.hypotheses)
        # Options
        assert len(result.options.alternatives) == 4
        assert "reliability" in result.options.core_tension.lower()
        # Decision
        assert "Roll back" in result.decision.recommendation
        assert "High" in result.decision.confidence
        assert "change my mind" in result.decision.falsifiability
        # Action
        assert len(result.action.steps) == 5
        assert len(result.action.reversible_steps) >= 1
        assert len(result.action.irreversible_steps) >= 1
        # Review
        assert len(result.review.failure_modes) == 3
        assert len(result.review.assumptions_to_validate) >= 1
        assert len(result.review.abort_conditions) >= 1

    def test_missing_phases_returns_defaults(self):
        text = "## DIAGNOSE\n1. Only diagnosis here."
        result = _parse_dodar_response(text)
        assert len(result.diagnosis.hypotheses) == 1
        # Other phases should be default (empty)
        assert result.options.alternatives == []
        assert result.decision.recommendation == ""
        assert result.action.steps == []
        assert result.review.failure_modes == []

    def test_empty_text(self):
        result = _parse_dodar_response("")
        assert result.text == ""
        assert result.diagnosis.hypotheses == []

    def test_no_dodar_headers(self):
        result = _parse_dodar_response("Just a plain answer with no structure.")
        assert result.text == "Just a plain answer with no structure."
        assert result.diagnosis.hypotheses == []


# =========================================================================== #
# DODARResult dataclass access patterns
# =========================================================================== #

class TestDODARResultDataclass:
    def test_default_values(self):
        result = DODARResult()
        assert result.text == ""
        assert result.input_tokens == 0
        assert result.output_tokens == 0
        assert result.latency_seconds == 0.0
        assert result.model == ""
        assert result.mode == "dodar"
        assert isinstance(result.diagnosis, DiagnosisResult)
        assert isinstance(result.options, OptionsResult)
        assert isinstance(result.decision, DecisionResult)
        assert isinstance(result.action, ActionResult)
        assert isinstance(result.review, ReviewResult)

    def test_metadata_fields(self):
        result = DODARResult(
            input_tokens=100,
            output_tokens=500,
            latency_seconds=1.5,
            model="claude-sonnet-4-5",
            mode="dodar",
        )
        assert result.input_tokens == 100
        assert result.output_tokens == 500
        assert result.latency_seconds == 1.5
        assert result.model == "claude-sonnet-4-5"


# =========================================================================== #
# DODAR class — mocked runner
# =========================================================================== #

def _make_mock_response(text: str = "mock response") -> ModelResponse:
    return ModelResponse(
        text=text,
        input_tokens=100,
        output_tokens=500,
        latency_seconds=1.2,
    )


class TestDODARClass:
    """Test the DODAR class with mocked runners (no real API calls)."""

    @patch("dodar.sdk.get_runner")
    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5", "gpt-4o"])
    def test_init_valid_model(self, mock_models, mock_get_runner):
        mock_get_runner.return_value = MagicMock()
        dodar = DODAR(model="claude-sonnet-4-5")
        assert dodar.model == "claude-sonnet-4-5"

    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5"])
    def test_init_invalid_model_raises(self, mock_models):
        with pytest.raises(ValueError, match="Unknown model"):
            DODAR(model="nonexistent-model")

    @patch("dodar.sdk.get_runner")
    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5"])
    def test_repr(self, mock_models, mock_get_runner):
        mock_get_runner.return_value = MagicMock()
        dodar = DODAR(model="claude-sonnet-4-5")
        assert repr(dodar) == "DODAR(model='claude-sonnet-4-5')"

    @pytest.mark.asyncio
    @patch("dodar.sdk.get_runner")
    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5"])
    async def test_analyze_async_dodar_mode(self, mock_models, mock_get_runner):
        mock_runner = AsyncMock()
        mock_runner.run.return_value = _make_mock_response(FULL_DODAR_RESPONSE)
        mock_get_runner.return_value = mock_runner

        dodar = DODAR(model="claude-sonnet-4-5")
        result = await dodar.analyze_async("Test scenario", mode="dodar")

        assert isinstance(result, DODARResult)
        assert result.mode == "dodar"
        assert result.model == "claude-sonnet-4-5"
        assert result.input_tokens == 100
        assert result.output_tokens == 500
        assert result.latency_seconds == 1.2
        # Parsed phases
        assert len(result.diagnosis.hypotheses) == 3
        assert len(result.options.alternatives) == 4

    @pytest.mark.asyncio
    @patch("dodar.sdk.get_runner")
    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5"])
    async def test_analyze_async_zero_shot_mode(self, mock_models, mock_get_runner):
        mock_runner = AsyncMock()
        mock_runner.run.return_value = _make_mock_response("Simple answer without structure.")
        mock_get_runner.return_value = mock_runner

        dodar = DODAR(model="claude-sonnet-4-5")
        result = await dodar.analyze_async("Test scenario", mode="zero_shot")

        assert result.mode == "zero_shot"
        assert result.text == "Simple answer without structure."
        # No parsing for non-dodar modes
        assert result.diagnosis.hypotheses == []

    @pytest.mark.asyncio
    @patch("dodar.sdk.get_runner")
    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5"])
    async def test_analyze_async_cot_mode(self, mock_models, mock_get_runner):
        mock_runner = AsyncMock()
        mock_runner.run.return_value = _make_mock_response("Step-by-step reasoning...")
        mock_get_runner.return_value = mock_runner

        dodar = DODAR(model="claude-sonnet-4-5")
        result = await dodar.analyze_async("Test scenario", mode="cot")

        assert result.mode == "cot"
        assert result.text == "Step-by-step reasoning..."

    @pytest.mark.asyncio
    @patch("dodar.sdk.get_runner")
    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5"])
    async def test_analyze_async_calls_runner_with_prompt(self, mock_models, mock_get_runner):
        mock_runner = AsyncMock()
        mock_runner.run.return_value = _make_mock_response("resp")
        mock_get_runner.return_value = mock_runner

        dodar = DODAR(model="claude-sonnet-4-5")
        await dodar.analyze_async("My scenario text", mode="dodar")

        mock_runner.run.assert_called_once()
        prompt_arg = mock_runner.run.call_args[0][0]
        assert "My scenario text" in prompt_arg
        assert "DODAR" in prompt_arg

    @pytest.mark.asyncio
    @patch("dodar.sdk.get_runner")
    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5"])
    async def test_analyze_async_zero_shot_prompt_content(self, mock_models, mock_get_runner):
        mock_runner = AsyncMock()
        mock_runner.run.return_value = _make_mock_response("resp")
        mock_get_runner.return_value = mock_runner

        dodar = DODAR(model="claude-sonnet-4-5")
        await dodar.analyze_async("Scenario X", mode="zero_shot")

        prompt_arg = mock_runner.run.call_args[0][0]
        assert "Scenario X" in prompt_arg
        assert "expert analyst" in prompt_arg.lower()

    @pytest.mark.asyncio
    @patch("dodar.sdk.get_runner")
    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5"])
    async def test_analyze_async_cot_prompt_content(self, mock_models, mock_get_runner):
        mock_runner = AsyncMock()
        mock_runner.run.return_value = _make_mock_response("resp")
        mock_get_runner.return_value = mock_runner

        dodar = DODAR(model="claude-sonnet-4-5")
        await dodar.analyze_async("Scenario Y", mode="cot")

        prompt_arg = mock_runner.run.call_args[0][0]
        assert "Scenario Y" in prompt_arg
        assert "step by step" in prompt_arg.lower()

    @patch("dodar.sdk.get_runner")
    @patch("dodar.sdk.available_models", return_value=["claude-sonnet-4-5"])
    def test_build_prompt_invalid_mode(self, mock_models, mock_get_runner):
        mock_get_runner.return_value = MagicMock()
        dodar = DODAR(model="claude-sonnet-4-5")
        with pytest.raises(ValueError, match="Unknown mode"):
            dodar._build_prompt("scenario", "invalid_mode")


# =========================================================================== #
# Edge cases for parsing
# =========================================================================== #

class TestParsingEdgeCases:
    def test_phases_with_extra_content_before_first_header(self):
        text = "Some preamble text\n\n## DIAGNOSE\n1. Hypo"
        phases = _split_phases(text)
        assert "DIAGNOSE" in phases
        # Preamble should not appear in the phase content
        assert "preamble" not in phases["DIAGNOSE"]

    def test_phases_with_subheadings(self):
        text = "## DIAGNOSE\n### Hypotheses\n1. A\n### Assumptions\n- B\n## OPTIONS\n1. X"
        phases = _split_phases(text)
        assert "DIAGNOSE" in phases
        assert "OPTIONS" in phases
        assert "Hypotheses" in phases["DIAGNOSE"]

    def test_diagnosis_with_assuming_keyword(self):
        text = "1. Hypo\nWe are assuming that funding is available."
        result = _parse_diagnosis(text)
        assert len(result.assumptions) >= 1

    def test_diagnosis_missing_keyword_for_unknowns(self):
        text = "1. Hypo\nIt is unknown whether the team has capacity."
        result = _parse_diagnosis(text)
        assert len(result.unknowns) >= 1

    def test_options_fundamental_trade_off_keyword(self):
        text = "The fundamental trade-off here is speed vs quality.\n1. Opt A"
        result = _parse_options(text)
        assert "speed" in result.core_tension.lower()

    def test_review_verify_keyword(self):
        text = "1. Failure\nVerify that the backup system works."
        result = _parse_review(text)
        assert len(result.assumptions_to_validate) >= 1

    def test_action_can_revert_keyword(self):
        text = "1. Change config (can revert easily)"
        result = _parse_action(text)
        assert len(result.reversible_steps) == 1

    def test_extract_list_items_with_leading_spaces(self):
        text = "  1. Indented item\n  - Another indented"
        items = _extract_list_items(text)
        assert len(items) == 2

    def test_decision_with_multiple_paragraphs(self):
        text = "Paragraph one is the recommendation.\n\nParagraph two elaborates.\n\nParagraph three has more detail."
        result = _parse_decision(text)
        assert result.recommendation == "Paragraph one is the recommendation."

    def test_split_phases_repeated_phase_name_takes_last(self):
        """If a phase header appears twice, later one overwrites."""
        text = "## DIAGNOSE\nFirst diag\n## OPTIONS\nOpts\n## DIAGNOSE\nSecond diag"
        phases = _split_phases(text)
        # The second DIAGNOSE overwrites the first because dict key collision
        assert "DIAGNOSE" in phases
        # Content between second DIAGNOSE and end
        assert "Second diag" in phases["DIAGNOSE"]
