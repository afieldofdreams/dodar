from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from dodar.config import CONDITION_IDS
from dodar.engine.cost import estimate_run_cost, CostEstimate
from dodar.engine.executor import execute_benchmark
from dodar.engine.progress import ProgressTracker
from dodar.models.run import RunConfig, RunStatus, RunSummary
from dodar.runners.registry import available_models
from dodar.storage.runs import load_all_run_summaries, load_run_summary, load_all_results, delete_run
from dodar.storage.scenarios import load_scenarios_filtered

router = APIRouter(tags=["runs"])


class StartRunRequest(BaseModel):
    scenario_ids: list[str] = []
    models: list[str] = []
    conditions: list[str] = []
    skip_completed: bool = True


class EstimateRequest(BaseModel):
    scenario_ids: list[str] = []
    models: list[str] = []
    conditions: list[str] = []


@router.get("/runs", response_model=list[RunSummary])
async def list_runs() -> list[RunSummary]:
    return load_all_run_summaries()


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> RunSummary:
    summary = load_run_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Run not found")
    return summary


@router.get("/runs/{run_id}/results")
async def get_run_results(run_id: str) -> list[dict]:
    """Get all individual results for a run."""
    summary = load_run_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Run not found")

    # Load all results that match this run's config and version
    all_results = load_all_results(prompt_version=summary.prompt_version)
    config = summary.config

    matching = [
        {
            "run_id": r.run_id,
            "scenario_id": r.scenario_id,
            "model": r.model,
            "condition": r.condition,
            "prompt_version": r.prompt_version,
            "response_text": r.response_text,
            "prompt_sent": r.prompt_sent,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "latency_seconds": r.latency_seconds,
            "cost_usd": r.cost_usd,
        }
        for r in all_results
        if r.scenario_id in config.scenario_ids
        and r.model in config.models
        and r.condition in config.conditions
    ]

    return matching


@router.post("/runs")
async def start_run(req: StartRunRequest, request: Request) -> dict:
    models = req.models or available_models()
    conditions = req.conditions or CONDITION_IDS

    scenarios = load_scenarios_filtered(ids=req.scenario_ids if req.scenario_ids else None)
    if not scenarios:
        raise HTTPException(status_code=400, detail="No scenarios matched")

    config = RunConfig(
        scenario_ids=[s.id for s in scenarios],
        models=models,
        conditions=conditions,
        skip_completed=req.skip_completed,
    )

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    tracker = ProgressTracker()

    # Store tracker for WebSocket access
    if not hasattr(request.app.state, "run_trackers"):
        request.app.state.run_trackers = {}
    request.app.state.run_trackers[run_id] = tracker

    # Launch as background task
    task = asyncio.create_task(execute_benchmark(run_id, scenarios, config, tracker))
    request.app.state.active_runs[run_id] = task

    return {"run_id": run_id, "total_items": len(scenarios) * len(models) * len(conditions)}


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str, request: Request) -> dict:
    """Cancel a running benchmark (does not delete files)."""
    task = request.app.state.active_runs.get(run_id)
    if task and not task.done():
        task.cancel()
        return {"status": "cancelled"}
    raise HTTPException(status_code=404, detail="No active run found")


@router.delete("/runs/{run_id}")
async def delete_run_endpoint(run_id: str, request: Request) -> dict:
    """Delete a run and all its result files."""
    # Cancel if still running
    task = request.app.state.active_runs.get(run_id)
    if task and not task.done():
        task.cancel()

    deleted = delete_run(run_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"status": "deleted", "files_removed": deleted}


@router.post("/runs/estimate")
async def estimate_cost(req: EstimateRequest) -> list[dict]:
    models = req.models or available_models()
    conditions = req.conditions or CONDITION_IDS

    scenarios = load_scenarios_filtered(ids=req.scenario_ids if req.scenario_ids else None)
    if not scenarios:
        raise HTTPException(status_code=400, detail="No scenarios matched")

    estimates = estimate_run_cost(scenarios, models, conditions)
    return [
        {
            "model": e.model,
            "condition": e.condition,
            "scenario_count": e.scenario_count,
            "estimated_input_tokens": e.estimated_input_tokens,
            "estimated_output_tokens": e.estimated_output_tokens,
            "estimated_cost_usd": e.estimated_cost_usd,
        }
        for e in estimates
    ]
