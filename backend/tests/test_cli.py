"""Tests for the DODAR CLI commands."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from dodar.cli import main
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


@pytest.fixture
def runner():
    return CliRunner()


# ===========================================================================
# list command
# ===========================================================================

class TestListCommand:

    @patch("dodar.cli.load_scenarios_filtered")
    def test_list_all(self, mock_load, runner):
        mock_load.return_value = [
            _make_scenario("S1"),
            _make_scenario("S2"),
        ]
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "S1" in result.output
        assert "S2" in result.output

    @patch("dodar.cli.load_scenarios_filtered")
    def test_list_empty(self, mock_load, runner):
        mock_load.return_value = []
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0

    @patch("dodar.cli.load_scenarios_filtered")
    def test_list_with_category_filter(self, mock_load, runner):
        mock_load.return_value = [_make_scenario()]
        result = runner.invoke(main, ["list", "--category", "TEST"])
        assert result.exit_code == 0
        mock_load.assert_called_once_with(category="TEST")

    @patch("dodar.cli.load_scenarios_filtered")
    def test_list_outputs_scenario_details(self, mock_load, runner):
        mock_load.return_value = [_make_scenario("MED-01")]
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "MED-01" in result.output
        assert "medium" in result.output
        assert "business" in result.output
        assert "Test Scenario" in result.output


# ===========================================================================
# validate command
# ===========================================================================

class TestValidateCommand:

    @patch("dodar.cli.load_all_scenarios")
    def test_validate_success(self, mock_load, runner):
        mock_load.return_value = [
            _make_scenario("S1"),
            _make_scenario("S2"),
        ]
        result = runner.invoke(main, ["validate"])
        assert result.exit_code == 0
        assert "Loaded 2 scenarios" in result.output

    @patch("dodar.cli.load_all_scenarios")
    def test_validate_shows_categories(self, mock_load, runner):
        s1 = _make_scenario("S1")
        s1.category = "MEDICAL"
        s2 = _make_scenario("S2")
        s2.category = "BUSINESS"
        mock_load.return_value = [s1, s2]
        result = runner.invoke(main, ["validate"])
        assert result.exit_code == 0
        assert "MEDICAL" in result.output
        assert "BUSINESS" in result.output

    @patch("dodar.cli.load_all_scenarios")
    def test_validate_error(self, mock_load, runner):
        mock_load.side_effect = ValueError("Invalid YAML at line 42")
        result = runner.invoke(main, ["validate"])
        assert result.exit_code == 1
        assert "Validation error" in result.output


# ===========================================================================
# run command
# ===========================================================================

class TestRunCommand:

    @patch("dodar.cli.execute_benchmark")
    @patch("dodar.cli.load_scenarios_filtered")
    @patch("dodar.cli.available_models")
    def test_run_no_scenarios(self, mock_models, mock_scenarios, mock_exec, runner):
        mock_models.return_value = ["gpt-4o"]
        mock_scenarios.return_value = []
        result = runner.invoke(main, ["run"])
        assert result.exit_code == 0
        assert "No scenarios found" in result.output
        mock_exec.assert_not_called()

    @patch("dodar.cli.asyncio")
    @patch("dodar.cli.load_scenarios_filtered")
    @patch("dodar.cli.available_models")
    def test_run_with_scenarios(self, mock_models, mock_scenarios, mock_asyncio, runner):
        mock_models.return_value = ["gpt-4o"]
        mock_scenarios.return_value = [_make_scenario()]
        mock_asyncio.run = MagicMock()

        result = runner.invoke(main, ["run", "-s", "TEST-01", "-m", "gpt-4o", "-c", "zero_shot"])
        assert result.exit_code == 0
        assert "Running 1 items" in result.output
        mock_asyncio.run.assert_called_once()

    @patch("dodar.cli.asyncio")
    @patch("dodar.cli.load_scenarios_filtered")
    @patch("dodar.cli.available_models")
    def test_run_displays_count(self, mock_models, mock_scenarios, mock_asyncio, runner):
        mock_models.return_value = ["gpt-4o", "claude-sonnet-4-5"]
        s1 = _make_scenario("S1")
        s2 = _make_scenario("S2")
        mock_scenarios.return_value = [s1, s2]
        mock_asyncio.run = MagicMock()

        result = runner.invoke(main, ["run"])
        assert result.exit_code == 0
        # 2 scenarios * 2 models * 5 conditions = 20
        assert "2 scenarios" in result.output
        assert "2 models" in result.output
