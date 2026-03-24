from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from dodar.config import SCORING_DIMENSIONS
from dodar.scoring.stats import aggregate_scores, compute_effect_sizes
from dodar.storage.scores import load_all_sessions
from dodar.storage.runs import load_all_run_summaries, load_all_results, load_result
from dodar.storage.scenarios import load_all_scenarios

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
    session_id: str | None = Query(None),
) -> StreamingResponse:
    """Export comprehensive benchmark data including responses, scores, and metadata."""
    sessions = load_all_sessions()
    stats = aggregate_scores(sessions, prompt_version=prompt_version)
    effects = compute_effect_sizes(stats)

    # Build score lookup: (scenario_id, model, condition) -> list of score entries from all sessions
    score_lookup: dict[tuple[str, str, str], list[dict]] = {}
    for sess in sessions:
        if session_id and sess.session_id != session_id:
            continue
        for item in sess.items:
            if prompt_version and item.prompt_version != prompt_version:
                continue
            score_entry = sess.scores.get(item.item_id)
            if score_entry:
                key = (item.scenario_id, item.model, item.condition)
                score_lookup.setdefault(key, []).append({
                    "session_id": sess.session_id,
                    "scorer": sess.scorer,
                    "scores": [
                        {"dimension": s.dimension, "score": s.score, "rationale": s.rationale}
                        for s in score_entry.scores
                    ],
                    "scored_at": score_entry.scored_at.isoformat() if score_entry.scored_at else None,
                })

    # Load scenarios for metadata
    scenarios = load_all_scenarios()
    scenario_map = {s.id: s for s in scenarios}

    # Load all run results
    results = load_all_results(prompt_version=prompt_version)

    # Build comprehensive per-item records
    items = []
    for r in results:
        scenario = scenario_map.get(r.scenario_id)
        score_entries = score_lookup.get((r.scenario_id, r.model, r.condition), [])

        items.append({
            "scenario_id": r.scenario_id,
            "scenario_title": scenario.title if scenario else None,
            "category": scenario.category if scenario else None,
            "domain": scenario.domain if scenario else None,
            "difficulty": scenario.difficulty if scenario else None,
            "model": r.model,
            "condition": r.condition,
            "prompt_version": r.prompt_version,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "prompt_sent": r.prompt_sent,
            "response_text": r.response_text,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "total_tokens": (r.input_tokens or 0) + (r.output_tokens or 0),
            "latency_seconds": r.latency_seconds,
            "cost_usd": r.cost_usd,
            "score_sessions": score_entries,
        })

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "scenario_id", "scenario_title", "category", "domain", "difficulty",
            "model", "condition", "prompt_version", "timestamp",
            "response_text", "input_tokens", "output_tokens", "total_tokens",
            "latency_seconds", "cost_usd",
            "scorer", "session_id",
            "diagnosis_quality", "option_breadth", "decision_justification",
            "action_specificity", "review_self_correction", "overall_trustworthiness",
        ])
        for item in items:
            if item["score_sessions"]:
                for se in item["score_sessions"]:
                    dim_scores = {s["dimension"]: s["score"] for s in se["scores"]}
                    writer.writerow([
                        item["scenario_id"], item["scenario_title"], item["category"],
                        item["domain"], item["difficulty"],
                        item["model"], item["condition"], item["prompt_version"],
                        item["timestamp"],
                        item["response_text"], item["input_tokens"], item["output_tokens"],
                        item["total_tokens"], item["latency_seconds"], item["cost_usd"],
                        se["scorer"], se["session_id"],
                        dim_scores.get("Diagnosis Quality"),
                        dim_scores.get("Option Breadth"),
                        dim_scores.get("Decision Justification"),
                        dim_scores.get("Action Specificity"),
                        dim_scores.get("Review / Self-Correction"),
                        dim_scores.get("Overall Trustworthiness"),
                    ])
            else:
                # Include unscored items too
                writer.writerow([
                    item["scenario_id"], item["scenario_title"], item["category"],
                    item["domain"], item["difficulty"],
                    item["model"], item["condition"], item["prompt_version"],
                    item["timestamp"],
                    item["response_text"], item["input_tokens"], item["output_tokens"],
                    item["total_tokens"], item["latency_seconds"], item["cost_usd"],
                    None, None, None, None, None, None, None, None,
                ])
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=dodar_benchmark_full.csv"},
        )
    else:
        # Full JSON export with all data
        export = {
            "export_meta": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "prompt_version_filter": prompt_version,
                "session_id_filter": session_id,
                "total_items": len(items),
                "total_scored": sum(1 for i in items if i["score_sessions"]),
            },
            "aggregate_stats": [
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
                    "baseline_mean": e.baseline_mean,
                    "dodar_mean": e.dodar_mean,
                    "cohens_d": e.cohens_d,
                }
                for e in effects
            ],
            "scenarios": [
                {
                    "id": s.id,
                    "title": s.title,
                    "category": s.category,
                    "domain": s.domain,
                    "difficulty": s.difficulty,
                    "prompt_text": s.prompt_text,
                    "expected_pitfalls": s.expected_pitfalls,
                    "gold_standard_elements": s.gold_standard_elements,
                    "discriminators": [
                        {"dimension": d.dimension, "description": d.description}
                        for d in s.discriminators
                    ],
                }
                for s in scenarios
            ],
            "items": items,
        }
        data = json.dumps(export, indent=2, ensure_ascii=False)
        return StreamingResponse(
            io.StringIO(data),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=dodar_benchmark_full.json"},
        )
