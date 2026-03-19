from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from dodar.models.scenario import Scenario
from dodar.storage.scenarios import get_scenario_by_id, load_scenarios_filtered
from dodar.storage.runs import load_all_results

router = APIRouter(tags=["scenarios"])


@router.get("/scenarios", response_model=list[Scenario])
async def list_scenarios(
    category: str | None = Query(None),
    difficulty: str | None = Query(None),
    domain: str | None = Query(None),
    search: str | None = Query(None),
) -> list[Scenario]:
    return load_scenarios_filtered(
        category=category, difficulty=difficulty, domain=domain, search=search
    )


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> dict:
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Build run status matrix for this scenario
    results = load_all_results()
    run_matrix: dict[str, dict[str, str]] = {}
    for r in results:
        if r.scenario_id == scenario_id:
            run_matrix.setdefault(r.model, {})[r.condition] = "completed"

    return {
        **scenario.model_dump(),
        "run_matrix": run_matrix,
    }
