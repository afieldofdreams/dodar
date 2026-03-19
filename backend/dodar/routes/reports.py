from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from dodar.config import SCORING_DIMENSIONS
from dodar.scoring.stats import aggregate_scores, compute_effect_sizes
from dodar.storage.scores import load_all_sessions
from dodar.storage.runs import load_all_run_summaries

router = APIRouter(tags=["reports"])


@router.get("/reports/versions")
async def list_versions() -> list[str]:
    """List all prompt versions that have run summaries."""
    summaries = load_all_run_summaries()
    versions = sorted({s.prompt_version for s in summaries})
    if not versions:
        versions = ["v1"]
    return versions


@router.get("/reports/dashboard")
async def dashboard(prompt_version: str | None = Query(None)) -> dict:
    sessions = load_all_sessions()
    if not sessions:
        return {"stats": [], "effect_sizes": [], "summary": {"total_sessions": 0}, "prompt_version": prompt_version}

    stats = aggregate_scores(sessions, prompt_version=prompt_version)
    effects = compute_effect_sizes(stats)

    # Count only items matching the version filter
    total_scored = 0
    for s in sessions:
        for item_id in s.scores:
            if prompt_version:
                item = next((i for i in s.items if i.item_id == item_id), None)
                if item and item.prompt_version == prompt_version:
                    total_scored += 1
            else:
                total_scored += 1

    return {
        "stats": [
            {
                "dimension": s.dimension,
                "model": s.model,
                "condition": s.condition,
                "mean": s.mean,
                "std": s.std,
                "count": s.count,
            }
            for s in stats
        ],
        "effect_sizes": [
            {
                "dimension": e.dimension,
                "model": e.model,
                "baseline_condition": e.baseline_condition,
                "cohens_d": e.cohens_d,
                "baseline_mean": e.baseline_mean,
                "dodar_mean": e.dodar_mean,
            }
            for e in effects
        ],
        "summary": {
            "total_sessions": len(sessions),
            "total_scored": total_scored,
            "dimensions": SCORING_DIMENSIONS,
        },
        "prompt_version": prompt_version,
    }


@router.get("/reports/comparison")
async def comparison(prompt_version: str | None = Query(None)) -> dict:
    sessions = load_all_sessions()
    stats = aggregate_scores(sessions, prompt_version=prompt_version)

    pivot: dict[str, dict[str, dict[str, float]]] = {}
    for s in stats:
        pivot.setdefault(s.model, {}).setdefault(s.condition, {})[s.dimension] = s.mean

    return {"pivot": pivot, "dimensions": SCORING_DIMENSIONS}


@router.get("/reports/stats")
async def statistical_analysis(prompt_version: str | None = Query(None)) -> dict:
    sessions = load_all_sessions()
    stats = aggregate_scores(sessions, prompt_version=prompt_version)
    effects = compute_effect_sizes(stats)
    return {
        "effect_sizes": [
            {
                "dimension": e.dimension,
                "model": e.model,
                "baseline_condition": e.baseline_condition,
                "cohens_d": e.cohens_d,
                "baseline_mean": e.baseline_mean,
                "dodar_mean": e.dodar_mean,
            }
            for e in effects
        ]
    }


@router.get("/reports/export")
async def export_data(
    format: str = Query("json", pattern="^(json|csv)$"),
    prompt_version: str | None = Query(None),
) -> StreamingResponse:
    sessions = load_all_sessions()
    stats = aggregate_scores(sessions, prompt_version=prompt_version)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["dimension", "model", "condition", "mean", "std", "count", "prompt_version"])
        for s in stats:
            writer.writerow([s.dimension, s.model, s.condition, s.mean, s.std, s.count, prompt_version or "all"])
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=dodar_results.csv"},
        )
    else:
        data = json.dumps(
            [
                {
                    "dimension": s.dimension,
                    "model": s.model,
                    "condition": s.condition,
                    "mean": s.mean,
                    "std": s.std,
                    "count": s.count,
                    "prompt_version": prompt_version or "all",
                }
                for s in stats
            ],
            indent=2,
        )
        return StreamingResponse(
            io.StringIO(data),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=dodar_results.json"},
        )
