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
from dodar.prompts.conditions import BENCHMARK_CONDITION_CODES, ALL_CONDITION_CODES, CONDITIONS
from dodar.runners.registry import available_models
from dodar.scoring.analysis import full_analysis
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
    task_version: str | None = None  # "v1" or "v2" (None = default/v2)


class BenchmarkEstimateRequest(BaseModel):
    task_ids: list[str] | None = None
    models: list[str] = []
    conditions: list[str] = []
    runs_per_task: int = 1


# --- Endpoints ---


@router.get("/tasks")
async def list_tasks(task_version: str | None = Query(None)) -> list[dict]:
    """List all benchmark tasks. Use task_version=v1 or v2 to select task bank."""
    tasks = load_benchmark_tasks(version=task_version)
    return [
        {
            "id": t.id,
            "source": t.source,
            "category": t.category,
            "answer_type": t.effective_answer_type,
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
async def list_conditions(include_deprecated: bool = False) -> list[dict]:
    """List available experimental conditions."""
    codes = ALL_CONDITION_CODES if include_deprecated else BENCHMARK_CONDITION_CODES
    return [
        {
            "code": code,
            "name": CONDITION_NAMES.get(code, code),
            "deprecated": code not in BENCHMARK_CONDITION_CODES,
        }
        for code in codes
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

    # Validate conditions against all registered (including deprecated)
    for c in conditions:
        if c not in CONDITIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid condition code: {c}. Valid: {ALL_CONDITION_CODES}",
            )

    # Validate task IDs
    if req.task_ids:
        all_tasks = load_benchmark_tasks(version=req.task_version)
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
        task_version=req.task_version,
    )

    run_id = f"bench-{uuid.uuid4().hex[:8]}"
    tracker = ProgressTracker()

    # Store tracker for WebSocket access
    if not hasattr(request.app.state, "run_trackers"):
        request.app.state.run_trackers = {}
    request.app.state.run_trackers[run_id] = tracker

    # Calculate total items for the response
    tasks = load_benchmark_tasks(version=req.task_version)
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

    # Rough estimate: ~500 input tokens + ~1000 output tokens per benchmark call
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

    benchmark_cost = round(sum(e["estimated_cost_usd"] for e in estimates), 4)

    # Error classification estimate (dual-LLM scoring on ~15-20% incorrect responses)
    # ~1500 input tokens + ~300 output tokens per classification call
    est_error_rate = 0.175
    est_incorrect = int(total_calls * est_error_rate)
    scorer_a = "claude-opus-4-6"
    scorer_b = "gpt-5.4"
    classification_calls = est_incorrect * 2  # both scorers

    pricing_a = settings.model_pricing.get(scorer_a, {"input": 0, "output": 0})
    pricing_b = settings.model_pricing.get(scorer_b, {"input": 0, "output": 0})
    cls_cost_a = est_incorrect * (1500 / 1_000_000 * pricing_a["input"] + 300 / 1_000_000 * pricing_a["output"])
    cls_cost_b = est_incorrect * (1500 / 1_000_000 * pricing_b["input"] + 300 / 1_000_000 * pricing_b["output"])
    classification_cost = round(cls_cost_a + cls_cost_b, 4)

    return {
        "total_calls": total_calls,
        "models": estimates,
        "benchmark_cost_usd": benchmark_cost,
        "error_classification": {
            "estimated_incorrect": est_incorrect,
            "classification_calls": classification_calls,
            "scorers": [scorer_a, scorer_b],
            "estimated_cost_usd": classification_cost,
        },
        "total_estimated_cost_usd": round(benchmark_cost + classification_cost, 4),
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


@router.get("/analysis")
async def get_analysis(
    run_id: str | None = Query(None),
    model_id: str | None = Query(None),
    prompt_version: str | None = Query(None),
) -> dict:
    """Full protocol analysis: accuracy, McNemar's tests, task-level, token efficiency, error distribution."""
    if run_id:
        summary = load_benchmark_run_summary(run_id)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        results = load_all_benchmark_results(prompt_version=summary.config.prompt_version)
        results = [
            r for r in results
            if r.model_id in summary.config.models
            and r.condition in summary.config.conditions
            and (summary.config.task_ids is None or r.task_id in summary.config.task_ids)
        ]
    else:
        results = load_all_benchmark_results(
            model_id=model_id, prompt_version=prompt_version
        )

    if not results:
        return {"error": "No results found"}

    # Load error classifications if available
    from dodar.models.benchmark import ErrorClassification
    cls_dir = get_settings().data_dir / "benchmark" / "classifications"
    all_cls: list[dict] = []
    if cls_dir.exists():
        for path in cls_dir.glob("classifications_*.json"):
            try:
                for item in json.loads(path.read_text()):
                    all_cls.append(item)
            except Exception:
                continue

    return full_analysis(results, error_classifications=all_cls if all_cls else None)


@router.get("/export")
async def export_benchmark_data(
    format: str = Query("json", pattern="^(json|csv)$"),
    run_id: str | None = Query(None),
    model_id: str | None = Query(None),
    condition: str | None = Query(None),
    prompt_version: str | None = Query(None),
) -> StreamingResponse:
    """Export benchmark results as JSON or CSV. Filter by run_id to export a specific run."""
    # If filtering by run, get the run config to scope results
    if run_id:
        summary = load_benchmark_run_summary(run_id)
        if not summary:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        results = load_all_benchmark_results(prompt_version=summary.config.prompt_version)
        results = [
            r for r in results
            if r.model_id in summary.config.models
            and r.condition in summary.config.conditions
            and (summary.config.task_ids is None or r.task_id in summary.config.task_ids)
        ]
    else:
        results = load_all_benchmark_results(
            model_id=model_id,
            condition=condition,
            prompt_version=prompt_version,
        )

    # Load all error classifications
    from dodar.models.benchmark import ErrorClassification
    from dodar.scoring.error_classifier import compute_inter_rater_agreement
    from collections import defaultdict, Counter

    cls_dir = get_settings().data_dir / "benchmark" / "classifications"
    all_classifications: list[ErrorClassification] = []
    if cls_dir.exists():
        for path in cls_dir.glob("classifications_*.json"):
            try:
                for item in json.loads(path.read_text()):
                    all_classifications.append(ErrorClassification.model_validate(item))
            except Exception:
                continue

    # Build classification lookup: (task_id, condition, model_id, run_number) -> list of classifications
    cls_lookup: dict[tuple, list[dict]] = defaultdict(list)
    for c in all_classifications:
        key = (c.task_id, c.condition, c.model_id, c.run_number)
        cls_lookup[key].append({
            "rater": c.rater,
            "classification": c.classification.value,
            "reasoning": c.reasoning,
            "root_cause_quote": c.root_cause_quote,
            "confidence": c.confidence,
        })

    # Compute inter-rater agreement
    agreement = compute_inter_rater_agreement(all_classifications) if all_classifications else None

    # Error distribution by condition (aggregated across both raters)
    error_by_condition: dict[str, Counter] = defaultdict(Counter)
    for c in all_classifications:
        error_by_condition[c.condition][c.classification.value] += 1

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "task_id", "source", "category", "condition", "condition_name",
            "model_id", "run_number", "prompt_version",
            "is_correct", "extracted_answer", "correct_answer", "answer_type",
            "input_tokens", "output_tokens", "total_tokens",
            "latency_seconds", "cost_usd", "timestamp",
            "error_class_rater_1", "error_class_rater_2",
            "error_reasoning_rater_1", "error_reasoning_rater_2",
            "error_confidence_rater_1", "error_confidence_rater_2",
            "question", "raw_response",
        ])
        for r in sorted(results, key=lambda x: (x.task_id, x.condition, x.model_id)):
            key = (r.task_id, r.condition, r.model_id, r.run_number)
            cls_entries = cls_lookup.get(key, [])
            rater_1 = cls_entries[0] if len(cls_entries) > 0 else {}
            rater_2 = cls_entries[1] if len(cls_entries) > 1 else {}
            writer.writerow([
                r.task_id, r.source, r.answer_type, r.condition,
                CONDITION_NAMES.get(r.condition, r.condition),
                r.model_id, r.run_number, r.prompt_version,
                r.is_correct, r.extracted_answer, r.correct_answer, r.answer_type,
                r.input_tokens, r.output_tokens,
                (r.input_tokens or 0) + (r.output_tokens or 0),
                r.latency_seconds, r.cost_usd,
                r.timestamp.isoformat() if r.timestamp else None,
                rater_1.get("classification"), rater_2.get("classification"),
                rater_1.get("reasoning"), rater_2.get("reasoning"),
                rater_1.get("confidence"), rater_2.get("confidence"),
                r.question, r.raw_response,
            ])
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=dodar_benchmark_results.csv"},
        )
    else:
        # Run full protocol analysis
        cls_dicts = [
            {"condition": c.condition, "classification": c.classification.value, "rater": c.rater}
            for c in all_classifications
        ]
        analysis = full_analysis(results, error_classifications=cls_dicts if cls_dicts else None)

        export = {
            "export_meta": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "protocol": "Does Reasoning Structure Shape Failure, Not Just Accuracy? v5-FINAL",
                "filters": {
                    "run_id": run_id,
                    "model_id": model_id,
                    "condition": condition,
                    "prompt_version": prompt_version,
                },
                "total_results": len(results),
                "total_correct": sum(1 for r in results if r.is_correct),
                "total_classified": len(set(
                    (c.task_id, c.condition, c.model_id, c.run_number)
                    for c in all_classifications
                )),
            },
            # Part I: Accuracy + McNemar's paired tests
            "accuracy_by_condition": analysis.get("accuracy_by_condition", {}),
            "mcnemar_paired_tests": analysis.get("mcnemar_paired_tests", {}),
            # Part II: Error taxonomy
            "error_classification": {
                "inter_rater_agreement": agreement,
                "error_distribution_by_condition": {
                    k: {**dict(v), "condition_name": CONDITION_NAMES.get(k, k)}
                    for k, v in sorted(error_by_condition.items())
                },
                "error_distribution_test": analysis.get("error_distribution_test"),
                "total_classifications": len(all_classifications),
            },
            # Efficiency
            "token_efficiency": analysis.get("token_efficiency", {}),
            # Task-level
            "task_level_analysis": analysis.get("task_level_analysis", {}),
            # Per-result detail
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
                    "error_classifications": cls_lookup.get(
                        (r.task_id, r.condition, r.model_id, r.run_number), []
                    ),
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


# --- Error classification endpoints ---


class ClassifyErrorsRequest(BaseModel):
    run_id: str | None = None  # None = classify all incorrect results
    scorer_a: str = "claude-opus-4-6"
    scorer_b: str = "gpt-5.4"
    concurrency: int = 3


@router.post("/classify-errors")
async def classify_errors(req: ClassifyErrorsRequest, request: Request) -> dict:
    """Run dual-LLM error classification on incorrect responses."""
    from dodar.scoring.error_classifier import classify_errors_dual, compute_inter_rater_agreement

    # Load results, optionally filtered by run
    if req.run_id:
        summary = load_benchmark_run_summary(req.run_id)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Run {req.run_id} not found")
        all_results = load_all_benchmark_results(prompt_version=summary.config.prompt_version)
        results = [
            r for r in all_results
            if r.model_id in summary.config.models
            and r.condition in summary.config.conditions
            and (summary.config.task_ids is None or r.task_id in summary.config.task_ids)
        ]
    else:
        results = load_all_benchmark_results()

    incorrect = [r for r in results if not r.is_correct]
    if not incorrect:
        return {"message": "No incorrect results to classify", "total": len(results), "incorrect": 0}

    # Run classification
    classifications = await classify_errors_dual(
        incorrect,
        scorer_a=req.scorer_a,
        scorer_b=req.scorer_b,
        concurrency=req.concurrency,
    )

    # Save classifications
    cls_dir = get_settings().data_dir / "benchmark" / "classifications"
    cls_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    cls_file = cls_dir / f"classifications_{timestamp}.json"
    cls_data = [c.model_dump() for c in classifications]
    cls_file.write_text(json.dumps(cls_data, indent=2, default=str))

    # Compute agreement
    agreement = compute_inter_rater_agreement(classifications)

    # Summarise by category per rater
    from collections import Counter
    by_rater: dict[str, Counter] = {}
    for c in classifications:
        by_rater.setdefault(c.rater, Counter())[c.classification.value] += 1

    # Summarise by condition
    by_condition: dict[str, Counter] = {}
    for c in classifications:
        by_condition.setdefault(c.condition, Counter())[c.classification.value] += 1

    return {
        "total_results": len(results),
        "incorrect": len(incorrect),
        "classifications": len(classifications),
        "file": str(cls_file),
        "agreement": agreement,
        "by_rater": {k: dict(v) for k, v in by_rater.items()},
        "by_condition": {k: dict(v) for k, v in sorted(by_condition.items())},
    }


@router.get("/error-classifications")
async def get_error_classifications() -> list[dict]:
    """Get all saved error classification files."""
    cls_dir = get_settings().data_dir / "benchmark" / "classifications"
    if not cls_dir.exists():
        return []

    files = []
    for path in sorted(cls_dir.glob("classifications_*.json"), reverse=True):
        try:
            data = json.loads(path.read_text())
            files.append({
                "file": path.name,
                "count": len(data),
                "timestamp": path.name.replace("classifications_", "").replace(".json", ""),
            })
        except Exception:
            continue
    return files


@router.get("/error-classifications/{filename}")
async def get_error_classification_detail(filename: str) -> dict:
    """Get detailed error classifications from a specific file."""
    cls_dir = get_settings().data_dir / "benchmark" / "classifications"
    path = cls_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Classification file not found")

    data = json.loads(path.read_text())

    from dodar.scoring.error_classifier import compute_inter_rater_agreement
    from dodar.models.benchmark import ErrorClassification

    classifications = [ErrorClassification.model_validate(c) for c in data]
    agreement = compute_inter_rater_agreement(classifications)

    # By condition × category
    from collections import Counter
    by_condition: dict[str, dict[str, int]] = {}
    for c in classifications:
        by_condition.setdefault(c.condition, Counter())[c.classification.value] += 1

    return {
        "classifications": data,
        "agreement": agreement,
        "by_condition": {k: dict(v) for k, v in sorted(by_condition.items())},
        "total": len(data),
    }
