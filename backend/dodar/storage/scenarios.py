from __future__ import annotations

from pathlib import Path

import yaml

from dodar.config import get_settings
from dodar.models.scenario import Scenario, ScenarioFile


def load_all_scenarios() -> list[Scenario]:
    """Load and validate all scenarios from YAML files."""
    settings = get_settings()
    scenarios: list[Scenario] = []
    for yaml_path in sorted(settings.scenarios_dir.glob("*.yaml")):
        scenarios.extend(_load_file(yaml_path))
    return scenarios


def _load_file(path: Path) -> list[Scenario]:
    with open(path) as f:
        raw = yaml.safe_load(f)
    if raw is None:
        return []
    sf = ScenarioFile.model_validate(raw)
    return sf.scenarios


def load_scenarios_filtered(
    *,
    category: str | None = None,
    difficulty: str | None = None,
    domain: str | None = None,
    search: str | None = None,
    ids: list[str] | None = None,
) -> list[Scenario]:
    """Load scenarios with optional filters."""
    scenarios = load_all_scenarios()
    if ids:
        id_set = set(ids)
        scenarios = [s for s in scenarios if s.id in id_set]
    if category:
        scenarios = [s for s in scenarios if s.category.upper() == category.upper()]
    if difficulty:
        scenarios = [s for s in scenarios if s.difficulty == difficulty.lower()]
    if domain:
        scenarios = [s for s in scenarios if s.domain.lower() == domain.lower()]
    if search:
        q = search.lower()
        scenarios = [
            s
            for s in scenarios
            if q in s.title.lower() or q in s.prompt_text.lower() or q in s.id.lower()
        ]
    return scenarios


def get_scenario_by_id(scenario_id: str) -> Scenario | None:
    for s in load_all_scenarios():
        if s.id == scenario_id:
            return s
    return None
