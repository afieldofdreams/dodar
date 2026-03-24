"""Tests for prompt building."""

from __future__ import annotations

from dodar.models.scenario import Scenario
from dodar.prompts.builder import build_prompt
from dodar.prompts.templates import PROMPT_VERSION

DODAR_PHASE_HEADERS = [
    "## Phase 1: DIAGNOSE",
    "## Phase 2: OPTIONS",
    "## Phase 3: DECIDE",
    "## Phase 4: ACTION",
    "## Phase 5: REVIEW",
]

CONDITIONS = ["zero_shot", "cot", "length_matched", "dodar"]


def test_build_prompt_returns_string(sample_scenario: Scenario):
    """build_prompt returns a non-empty string for every condition."""
    for cond in CONDITIONS:
        prompt = build_prompt(sample_scenario, cond)
        assert isinstance(prompt, str)
        assert len(prompt) > 0


def test_prompts_differ_across_conditions(sample_scenario: Scenario):
    """Each condition produces a distinct prompt."""
    prompts = {cond: build_prompt(sample_scenario, cond) for cond in CONDITIONS}
    unique_prompts = set(prompts.values())
    assert len(unique_prompts) == len(CONDITIONS), "Some conditions produced identical prompts"


def test_all_prompts_contain_scenario_text(sample_scenario: Scenario):
    """Every prompt includes the scenario's prompt_text."""
    for cond in CONDITIONS:
        prompt = build_prompt(sample_scenario, cond)
        assert sample_scenario.prompt_text.strip() in prompt


def test_dodar_prompt_contains_phase_headers(sample_scenario: Scenario):
    """The DODAR prompt contains all 5 phase headers."""
    prompt = build_prompt(sample_scenario, "dodar")
    for header in DODAR_PHASE_HEADERS:
        assert header in prompt, f"Missing header: {header}"


def test_cot_prompt_contains_step_by_step(sample_scenario: Scenario):
    """The chain-of-thought prompt instructs step-by-step reasoning."""
    prompt = build_prompt(sample_scenario, "cot")
    assert "step by step" in prompt.lower()


def test_prompt_version_is_set():
    """PROMPT_VERSION is a non-empty string."""
    assert isinstance(PROMPT_VERSION, str)
    assert len(PROMPT_VERSION) > 0


def test_unknown_condition_raises(sample_scenario: Scenario):
    """An unknown condition raises ValueError."""
    import pytest

    with pytest.raises(ValueError, match="Unknown condition"):
        build_prompt(sample_scenario, "nonexistent_condition")


def test_length_matched_prompt_is_longer_than_zero_shot(sample_scenario: Scenario):
    """The length-matched prompt should be substantially longer than zero-shot."""
    zero = build_prompt(sample_scenario, "zero_shot")
    length_matched = build_prompt(sample_scenario, "length_matched")
    assert len(length_matched) > len(zero)
