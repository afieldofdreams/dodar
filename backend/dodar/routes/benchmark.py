"""API routes for Phase 2 benchmark runs."""

from __future__ import annotations

import asyncio
import csv
import io
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from dodar.config import get_settings
from dodar.engine.benchmark_executor import execute_benchmark_run
from dodar.engine.progress import ProgressTracker
from dodar.models.benchmark import BenchmarkRunConfig, CONDITION_NAMES
from dodar.prompts.conditions import BENCHMARK_CONDITION_CODES
from dodar.runners.registry import available_models
from dodar.storage.benchmark import (
    load_all_benchmark_results,
    load_all_benchmark_run_summaries,
    load_benchmark_run_summary,
    load_benchmark_tasks,
)

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


# --- Request models ---


class StartBenchmarkRequest(BaseModel):
    task_ids: list[str] | None = None  # None = all 100
    models: list[str] = []
    conditions: list[str] = []  # condition codes: ["A", "B", "C", ...]
    runs_per_task: int = 1
    skip_completed: bool = True
    stage: str = "triage"
    execution_seed: int = 42


class BenchmarkEstimateRequest(BaseModel):
    task_ids: list[str] | None = None
    models: list[str] = []
    conditions: list[str] = []
    runs_per_task: int = 1


# --- Endpoints ---


@router.get("/tasks")
async def list_tasks() -> list[dict]:
    """List all benchmark tasks."""
    tasks = load_benchmark_tasks()
    return [
        {
            "id": t.id,
            "source": t.source,
            "category": t.category,
            "answer_type": t.answer_type,
            "word_count": t.word_count,
            "question_preview": t.question[:120] + "..." if len(t.question) > 120 else t.question,
        }
        for t in tasks
    ]


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    """Get a single benchmark task."""
    tasks = load_benchmark_tasks()
    for t in tasks:
        if t.id == task_id:
            return t.model_dump()
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@router.get("/conditions")
async def list_conditions() -> list[dict]:
    """List available experimental conditions."""
    return [
        {"code": code, "name": CONDITION_NAMES.get(code, code)}
        for code in BENCHMARK_CONDITION_CODES
    ]


@router.get("/runs")
async def list_benchmark_runs() -> list[dict]:
    """List all benchmark runs."""
    summaries = load_all_benchmark_run_summaries()
    return [s.model_dump() for s in summaries]


@router.get("/runs/{run_id}")
async def get_benchmark_run(run_id: str) -> dict:
    """Get a benchmark run summary."""
    summary = load_benchmark_run_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Run not found")
    return summary.model_dump()


@router.get("/runs/{run_id}/results")
async def get_benchmark_results(run_id: str) -> list[dict]:
    """Get all results for a benchmark run."""
    summary = load_benchmark_run_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Run not found")

    results = load_all_benchmark_results(prompt_version=summary.config.prompt_version)
    # Filter to this run's config
    matching = [
        r.model_dump()
        for r in results
        if r.model_id in summary.config.models
        and r.condition in summary.config.conditions
        and (summary.config.task_ids is None or r.task_id in summary.config.task_ids)
    ]
    return matching


@router.post("/runs")
async def start_benchmark_run(req: StartBenchmarkRequest, request: Request) -> dict:
    """Start a new benchmark run."""
    models = req.models or ["gpt-4.1-mini"]
    conditions = req.conditions or BENCHMARK_CONDITION_CODES

    # Validate conditions
    for c in conditions:
        if c not in BENCHMARK_CONDITION_CODES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid condition code: {c}. Valid: {BENCHMARK_CONDITION_CODES}",
            )

    # Validate task IDs
    if req.task_ids:
        all_tasks = load_benchmark_tasks()
        valid_ids = {t.id for t in all_tasks}
        invalid = set(req.task_ids) - valid_ids
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid task IDs: {invalid}")

    config = BenchmarkRunConfig(
        task_ids=req.task_ids,
        models=models,
        conditions=conditions,
        runs_per_task=req.runs_per_task,
        skip_completed=req.skip_completed,
        execution_seed=req.execution_seed,
        stage=req.stage,
    )

    run_id = f"bench-{uuid.uuid4().hex[:8]}"
    tracker = ProgressTracker()

    # Store tracker for WebSocket access
    if not hasattr(request.app.state, "run_trackers"):
        request.app.state.run_trackers = {}
    request.app.state.run_trackers[run_id] = tracker

    # Calculate total items for the response
    tasks = load_benchmark_tasks()
    task_count = len(req.task_ids) if req.task_ids else len(tasks)
    total = task_count * len(models) * len(conditions) * req.runs_per_task

    # Launch as background task
    task = asyncio.create_task(execute_benchmark_run(run_id, config, tracker))
    if not hasattr(request.app.state, "active_runs"):
        request.app.state.active_runs = {}
    request.app.state.active_runs[run_id] = task

    return {
        "run_id": run_id,
        "total_items": total,
        "models": models,
        "conditions": conditions,
        "stage": req.stage,
    }


@router.post("/runs/{run_id}/cancel")
async def cancel_benchmark_run(run_id: str, request: Request) -> dict:
    task = request.app.state.active_runs.get(run_id)
    if task and not task.done():
        task.cancel()
        return {"status": "cancelled"}
    raise HTTPException(status_code=404, detail="No active run found")


@router.post("/estimate")
async def estimate_benchmark_cost(req: BenchmarkEstimateRequest) -> dict:
    """Estimate cost for a benchmark run."""
    settings = get_settings()

    models = req.models or ["gpt-4.1-mini"]
    conditions = req.conditions or BENCHMARK_CONDITION_CODES

    tasks = load_benchmark_tasks()
    task_count = len(req.task_ids) if req.task_ids else len(tasks)
    total_calls = task_count * len(models) * len(conditions) * req.runs_per_task

    # Rough estimate: ~500 input tokens + ~1000 output tokens per call
    estimates = []
    for model in models:
        pricing = settings.model_pricing.get(model, {"input": 0, "output": 0})
        calls = task_count * len(conditions) * req.runs_per_task
        est_input = calls * 500
        est_output = calls * 1000
        cost = (est_input / 1_000_000 * pricing["input"]) + (
            est_output / 1_000_000 * pricing["output"]
        )
        estimates.append({
            "model": model,
            "calls": calls,
            "estimated_cost_usd": round(cost, 4),
        })

    return {
        "total_calls": total_calls,
        "models": estimates,
        "total_estimated_cost_usd": round(sum(e["estimated_cost_usd"] for e in estimates), 4),
    }


@router.get("/results")
async def get_all_results(
    model_id: str | None = None,
    condition: str | None = None,
    prompt_version: str | None = None,
) -> list[dict]:
    """Get all benchmark results, with optional filters."""
    results = load_all_benchmark_results(
        model_id=model_id,
        condition=condition,
        prompt_version=prompt_version,
    )
    return [r.model_dump() for r in results]


@router.get("/accuracy")
async def get_accuracy_summary(
    model_id: str | None = None,
    prompt_version: str | None = None,
) -> dict:
    """Get accuracy summary across conditions."""
    results = load_all_benchmark_results(
        model_id=model_id, prompt_version=prompt_version
    )

    if not results:
        return {"total": 0, "by_condition": {}, "by_source": {}, "by_model": {}}

    # By condition
    by_condition: dict[str, dict] = {}
    for r in results:
        key = r.condition
        if key not in by_condition:
            by_condition[key] = {"correct": 0, "total": 0, "name": CONDITION_NAMES.get(key, key)}
        by_condition[key]["total"] += 1
        if r.is_correct:
            by_condition[key]["correct"] += 1

    for v in by_condition.values():
        v["accuracy"] = round(v["correct"] / max(v["total"], 1) * 100, 1)

    # By source
    by_source: dict[str, dict] = {}
    for r in results:
        key = r.source or "unknown"
        if key not in by_source:
            by_source[key] = {"correct": 0, "total": 0}
        by_source[key]["total"] += 1
        if r.is_correct:
            by_source[key]["correct"] += 1

    for v in by_source.values():
        v["accuracy"] = round(v["correct"] / max(v["total"], 1) * 100, 1)

    # By model
    by_model: dict[str, dict] = {}
    for r in results:
        key = r.model_id
        if key not in by_model:
            by_model[key] = {"correct": 0, "total": 0}
        by_model[key]["total"] += 1
        if r.is_correct:
            by_model[key]["correct"] += 1

    for v in by_model.values():
        v["accuracy"] = round(v["correct"] / max(v["total"], 1) * 100, 1)

    total_correct = sum(1 for r in results if r.is_correct)
    return {
        "total": len(results),
        "total_correct": total_correct,
        "overall_accuracy": round(total_correct / max(len(results), 1) * 100, 1),
        "by_condition": by_condition,
        "by_source": by_source,
        "by_model": by_model,
    }


@router.get("/export")
async def export_benchmark_data(
    format: str = Query("json", pattern="^(json|csv)$"),
    model_id: str | None = Query(None),
    condition: str | None = Query(None),
    prompt_version: str | None = Query(None),
) -> StreamingResponse:
    """Export benchmark results as JSON or CSV."""
    results = load_all_benchmark_results(
        model_id=model_id,
        condition=condition,
        prompt_version=prompt_version,
    )

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "task_id", "source", "category", "condition", "condition_name",
            "model_id", "run_number", "prompt_version",
            "is_correct", "extracted_answer", "correct_answer", "answer_type",
            "input_tokens", "output_tokens", "total_tokens",
            "latency_seconds", "cost_usd", "timestamp",
            "question", "raw_response",
        ])
        for r in sorted(results, key=lambda x: (x.task_id, x.condition, x.model_id)):
            writer.writerow([
                r.task_id, r.source, r.answer_type, r.condition,
                CONDITION_NAMES.get(r.condition, r.condition),
                r.model_id, r.run_number, r.prompt_version,
                r.is_correct, r.extracted_answer, r.correct_answer, r.answer_type,
                r.input_tokens, r.output_tokens,
                (r.input_tokens or 0) + (r.output_tokens or 0),
                r.latency_seconds, r.cost_usd,
                r.timestamp.isoformat() if r.timestamp else None,
                r.question, r.raw_response,
            ])
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=dodar_benchmark_results.csv"},
        )
    else:
        # Compute accuracy summary inline
        by_condition: dict[str, dict] = {}
        by_source: dict[str, dict] = {}
        for r in results:
            for key, bucket in [(r.condition, by_condition), (r.source or "unknown", by_source)]:
                if key not in bucket:
                    bucket[key] = {"correct": 0, "total": 0}
                bucket[key]["total"] += 1
                if r.is_correct:
                    bucket[key]["correct"] += 1
        for bucket in [by_condition, by_source]:
            for v in bucket.values():
                v["accuracy_pct"] = round(v["correct"] / max(v["total"], 1) * 100, 1)

        export = {
            "export_meta": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "filters": {
                    "model_id": model_id,
                    "condition": condition,
                    "prompt_version": prompt_version,
                },
                "total_results": len(results),
                "total_correct": sum(1 for r in results if r.is_correct),
            },
            "accuracy_by_condition": {
                k: {**v, "name": CONDITION_NAMES.get(k, k)}
                for k, v in sorted(by_condition.items())
            },
            "accuracy_by_source": dict(sorted(by_source.items())),
            "results": [
                {
                    "task_id": r.task_id,
                    "source": r.source,
                    "condition": r.condition,
                    "condition_name": CONDITION_NAMES.get(r.condition, r.condition),
                    "model_id": r.model_id,
                    "run_number": r.run_number,
                    "prompt_version": r.prompt_version,
                    "is_correct": r.is_correct,
                    "extracted_answer": r.extracted_answer,
                    "correct_answer": r.correct_answer,
                    "answer_type": r.answer_type,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "latency_seconds": r.latency_seconds,
                    "cost_usd": r.cost_usd,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "question": r.question,
                    "system_prompt_sent": r.system_prompt_sent,
                    "user_prompt_sent": r.user_prompt_sent,
                    "raw_response": r.raw_response,
                }
                for r in sorted(results, key=lambda x: (x.task_id, x.condition, x.model_id))
            ],
        }
        data = json.dumps(export, indent=2, ensure_ascii=False)
        return StreamingResponse(
            io.StringIO(data),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=dodar_benchmark_results.json"},
        )
