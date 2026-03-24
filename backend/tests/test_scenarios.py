"""Tests for scenario loading and validation."""

from __future__ import annotations

from dodar.storage.scenarios import load_all_scenarios

REQUIRED_FIELDS = {
    "id",
    "category",
    "title",
    "prompt_text",
    "expected_pitfalls",
    "gold_standard_elements",
    "discriminators",
}


def test_all_scenarios_load():
    """All YAML scenario files load without errors."""
    scenarios = load_all_scenarios()
    assert len(scenarios) > 0


def test_exactly_20_scenarios():
    """The benchmark contains exactly 20 scenarios."""
    scenarios = load_all_scenarios()
    assert len(scenarios) == 20


def test_scenario_ids_are_unique():
    """Every scenario has a unique ID."""
    scenarios = load_all_scenarios()
    ids = [s.id for s in scenarios]
    assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"


def test_scenarios_have_required_fields():
    """Each scenario has all required fields with non-empty values."""
    scenarios = load_all_scenarios()
    for s in scenarios:
        for field in REQUIRED_FIELDS:
            value = getattr(s, field)
            assert value, f"Scenario {s.id} missing or empty field: {field}"


def test_scenarios_have_expected_pitfalls():
    """Each scenario has at least one expected pitfall."""
    for s in load_all_scenarios():
        assert len(s.expected_pitfalls) >= 1, f"{s.id} has no expected_pitfalls"


def test_scenarios_have_gold_standard_elements():
    """Each scenario has at least one gold standard element."""
    for s in load_all_scenarios():
        assert len(s.gold_standard_elements) >= 1, f"{s.id} has no gold_standard_elements"


def test_scenarios_have_discriminators():
    """Each scenario has at least one discriminator."""
    for s in load_all_scenarios():
        assert len(s.discriminators) >= 1, f"{s.id} has no discriminators"


def test_scenario_categories():
    """Scenarios belong to known categories."""
    scenarios = load_all_scenarios()
    categories = {s.category for s in scenarios}
    assert categories == {"AMB", "TRD"}, f"Unexpected categories: {categories}"


def test_scenario_difficulty_values():
    """Difficulty is one of easy, medium, hard."""
    for s in load_all_scenarios():
        assert s.difficulty in {"easy", "medium", "hard"}, (
            f"{s.id} has invalid difficulty: {s.difficulty}"
        )
