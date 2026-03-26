"""Benchmark execution engine for Phase 2 protocol.

Runs 100 benchmark tasks across 7 conditions and multiple models.
Handles answer extraction, correctness checking, and progress tracking.
"""

from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timezone

from dodar.config import get_settings
from dodar.engine.progress import EventType, ProgressEvent, ProgressTracker
from dodar.models.benchmark import (
    BenchmarkResult,
    BenchmarkRunConfig,
    BenchmarkRunSummary,
    BenchmarkTask,
)
from dodar.prompts.benchmark_builder import build_benchmark_prompt
from dodar.runners.registry import get_runner
from dodar.scoring.extraction import check_correctness, extract_answer
from dodar.storage.benchmark import (
    load_benchmark_tasks,
    make_benchmark_result_id,
    benchmark_result_exists,
    save_benchmark_result,
    save_benchmark_run_summary,
)


async def execute_benchmark_run(
    run_id: str,
    config: BenchmarkRunConfig,
    tracker: ProgressTracker | None = None,
) -> BenchmarkRunSummary:
    """Execute a full benchmark run across tasks × models × conditions × runs."""
    settings = get_settings()

    # Load tasks
    all_tasks = load_benchmark_tasks()
    if config.task_ids:
        tasks_by_id = {t.id: t for t in all_tasks}
        tasks = [tasks_by_id[tid] for tid in config.task_ids if tid in tasks_by_id]
    else:
        tasks = all_tasks

    # Local models serialize internally
    LOCAL_PREFIXES = ("qwen", "llama", "phi", "mistral", "gemma", "codellama")
    has_local = any(m.startswith(LOCAL_PREFIXES) for m in config.models)
    has_cloud = any(not m.startswith(LOCAL_PREFIXES) for m in config.models)
    concurrency = 1 if has_local and not has_cloud else settings.default_concurrency
    semaphore = asyncio.Semaphore(concurrency)

    # Build work items: (task, model, condition, run_number)
    work_items: list[tuple[BenchmarkTask, str, str, int]] = []
    for task in tasks:
        for model in config.models:
            for condition in config.conditions:
                for run_num in range(1, config.runs_per_task + 1):
                    rid = make_benchmark_result_id(
                        task.id, condition, model, run_num
                    )
                    if config.skip_completed and benchmark_result_exists(rid):
                        continue
                    work_items.append((task, model, condition, run_num))

    # Shuffle execution order (as per protocol)
    rng = random.Random(config.execution_seed)
    rng.shuffle(work_items)

    total = len(work_items)
    summary = BenchmarkRunSummary(
        run_id=run_id,
        config=config,
        status="running",
        created_at=datetime.now(timezone.utc),
        total_items=total,
    )
    save_benchmark_run_summary(summary)

    completed = 0
    correct = 0
    total_cost = 0.0
    total_tokens = 0
    condition_correct: dict[str, int] = {}
    condition_total: dict[str, int] = {}

    async def run_one(
        task: BenchmarkTask, model: str, condition: str, run_number: int
    ) -> None:
        nonlocal completed, correct, total_cost, total_tokens

        if tracker:
            tracker.emit(
                ProgressEvent(
                    type=EventType.ITEM_START,
                    scenario_id=task.id,
                    model=model,
                    condition=condition,
                    completed=completed,
                    total=total,
                )
            )

        try:
            # Build prompt
            prompt_pair = build_benchmark_prompt(task, condition)

            # Call model
            async with semaphore:
                # Rate limiting: 150ms delay between calls
                await asyncio.sleep(0.15)
                runner = get_runner(model)
                response = await runner.run(
                    prompt_pair.user_message,
                    system_prompt=prompt_pair.system_prompt,
                )

            # Compute cost
            pricing = settings.model_pricing.get(model, {"input": 0, "output": 0})
            cost = (response.input_tokens / 1_000_000 * pricing["input"]) + (
                response.output_tokens / 1_000_000 * pricing["output"]
            )

            # Extract answer and check correctness
            extracted = extract_answer(response.text, task.answer_type)
            is_correct = check_correctness(extracted, task.correct_answer, task.answer_type)

            result = BenchmarkResult(
                task_id=task.id,
                condition=condition,
                model_id=model,
                run_number=run_number,
                prompt_version=config.prompt_version,
                timestamp=datetime.now(timezone.utc),
                latency_seconds=round(response.latency_seconds, 2),
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=round(cost, 6),
                system_prompt_sent=prompt_pair.system_prompt,
                user_prompt_sent=prompt_pair.user_message,
                raw_response=response.text,
                extracted_answer=extracted,
                is_correct=is_correct,
                correct_answer=task.correct_answer,
                answer_type=task.answer_type,
                question=task.question,
                source=task.source,
            )
            save_benchmark_result(result)

            completed += 1
            if is_correct:
                correct += 1
            total_cost += cost
            total_tokens += response.input_tokens + response.output_tokens

            # Track per-condition accuracy
            condition_correct[condition] = condition_correct.get(condition, 0) + (1 if is_correct else 0)
            condition_total[condition] = condition_total.get(condition, 0) + 1

            # Update summary incrementally
            summary.completed_items = completed
            summary.correct_items = correct
            summary.total_cost_usd = round(total_cost, 4)
            summary.total_tokens = total_tokens
            summary.accuracy_by_condition = {
                c: round(condition_correct.get(c, 0) / condition_total[c] * 100, 1)
                for c in condition_total
            }
            save_benchmark_run_summary(summary)

            if tracker:
                tracker.emit(
                    ProgressEvent(
                        type=EventType.ITEM_COMPLETE,
                        scenario_id=task.id,
                        model=model,
                        condition=condition,
                        completed=completed,
                        total=total,
                        tokens_used=response.input_tokens + response.output_tokens,
                        cost_usd=round(cost, 6),
                    )
                )

        except Exception as e:
            completed += 1
            condition_total[condition] = condition_total.get(condition, 0) + 1
            summary.dropouts.append({
                "task_id": task.id,
                "model": model,
                "condition": condition,
                "run_number": run_number,
                "error": str(e),
            })

            if tracker:
                tracker.emit(
                    ProgressEvent(
                        type=EventType.ITEM_ERROR,
                        scenario_id=task.id,
                        model=model,
                        condition=condition,
                        completed=completed,
                        total=total,
                        error=str(e),
                    )
                )

    # Execute all work items concurrently (bounded by semaphore)
    tasks_coros = [run_one(t, m, c, r) for t, m, c, r in work_items]
    await asyncio.gather(*tasks_coros, return_exceptions=True)

    # Finalize
    summary.status = "completed"
    summary.completed_at = datetime.now(timezone.utc)
    summary.completed_items = completed
    summary.correct_items = correct
    summary.total_cost_usd = round(total_cost, 4)
    summary.total_tokens = total_tokens
    summary.accuracy_by_condition = {
        c: round(condition_correct.get(c, 0) / max(condition_total.get(c, 1), 1) * 100, 1)
        for c in condition_total
    }
    save_benchmark_run_summary(summary)

    if tracker:
        tracker.emit(
            ProgressEvent(
                type=EventType.RUN_COMPLETE,
                completed=completed,
                total=total,
                summary={
                    "total_cost_usd": round(total_cost, 4),
                    "total_tokens": total_tokens,
                    "accuracy_by_condition": summary.accuracy_by_condition,
                    "dropout_count": len(summary.dropouts),
                    "duration_seconds": (
                        summary.completed_at - summary.created_at
                    ).total_seconds(),
                },
            )
        )

    return summary
