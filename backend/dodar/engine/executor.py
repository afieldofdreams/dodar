"""Core benchmark execution engine — shared by CLI and web."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from dodar.config import get_settings
from dodar.engine.progress import EventType, ProgressEvent, ProgressTracker
from dodar.models.run import RunConfig, RunItemProgress, RunStatus, RunSummary
from dodar.models.scenario import Scenario
from dodar.agents import DODARPipeline
from dodar.prompts.builder import build_prompt
from dodar.prompts.templates import PROMPT_VERSION
from dodar.runners.base import ModelRunner
from dodar.runners.registry import get_runner
from dodar.storage.runs import make_run_id, result_exists, save_result, save_run_summary
from dodar.models.run import RunResult


async def execute_benchmark(
    run_id: str,
    scenarios: list[Scenario],
    config: RunConfig,
    tracker: ProgressTracker | None = None,
) -> RunSummary:
    """Execute a full benchmark run across scenarios × models × conditions."""
    settings = get_settings()

    # Local models (Ollama) serialize internally — use concurrency 1 to avoid timeouts
    LOCAL_PREFIXES = ("qwen", "llama", "phi", "mistral", "gemma", "codellama")
    has_local = any(m.startswith(LOCAL_PREFIXES) for m in config.models)
    has_cloud = any(not m.startswith(LOCAL_PREFIXES) for m in config.models)
    concurrency = 1 if has_local and not has_cloud else settings.default_concurrency
    semaphore = asyncio.Semaphore(concurrency)

    # Tag config with current prompt version
    config.prompt_version = PROMPT_VERSION

    # Build work items — run_id includes version to avoid collisions
    work_items: list[tuple[Scenario, str, str]] = []
    for scenario in scenarios:
        for model in config.models:
            for condition in config.conditions:
                rid = make_run_id(scenario.id, model, condition, PROMPT_VERSION)
                if config.skip_completed and result_exists(rid):
                    continue
                work_items.append((scenario, model, condition))

    total = len(work_items)
    summary = RunSummary(
        run_id=run_id,
        config=config,
        status=RunStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        prompt_version=PROMPT_VERSION,
        total_items=total,
    )
    save_run_summary(summary)

    completed = 0
    total_cost = 0.0
    total_tokens = 0

    async def run_one(scenario: Scenario, model: str, condition: str) -> None:
        nonlocal completed, total_cost, total_tokens

        rid = make_run_id(scenario.id, model, condition, PROMPT_VERSION)

        if tracker:
            tracker.emit(
                ProgressEvent(
                    type=EventType.ITEM_START,
                    scenario_id=scenario.id,
                    model=model,
                    condition=condition,
                    completed=completed,
                    total=total,
                )
            )

        try:
            if condition == "dodar_pipeline":
                # Multi-agent pipeline — 5 sequential calls
                async with semaphore:
                    pipeline = DODARPipeline(model=model)
                    pipeline_result = await pipeline.run(scenario.prompt_text)

                result = RunResult(
                    run_id=rid,
                    scenario_id=scenario.id,
                    model=model,
                    condition=condition,
                    prompt_version=PROMPT_VERSION,
                    timestamp=datetime.now(timezone.utc),
                    prompt_sent="[multi-agent pipeline — 5 sequential calls]",
                    response_text=pipeline_result.text,
                    input_tokens=pipeline_result.total_input_tokens,
                    output_tokens=pipeline_result.total_output_tokens,
                    latency_seconds=round(pipeline_result.total_latency_seconds, 2),
                    cost_usd=pipeline_result.total_cost_usd,
                )
                cost = pipeline_result.total_cost_usd
                save_result(result)
            else:
                async with semaphore:
                    runner = get_runner(model)
                    prompt = build_prompt(scenario, condition)
                    response = await runner.run(prompt)

                # Compute cost
                pricing = settings.model_pricing.get(model, {"input": 0, "output": 0})
                cost = (response.input_tokens / 1_000_000 * pricing["input"]) + (
                    response.output_tokens / 1_000_000 * pricing["output"]
                )

                result = RunResult(
                    run_id=rid,
                    scenario_id=scenario.id,
                    model=model,
                    condition=condition,
                    prompt_version=PROMPT_VERSION,
                    timestamp=datetime.now(timezone.utc),
                    prompt_sent=prompt,
                    response_text=response.text,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    latency_seconds=round(response.latency_seconds, 2),
                    cost_usd=round(cost, 6),
                )
                save_result(result)

            completed += 1
            total_cost += cost
            total_tokens += result.input_tokens + result.output_tokens

            # Update summary incrementally so progress survives crashes
            summary.completed_items = completed
            summary.total_cost_usd = round(total_cost, 4)
            summary.total_tokens = total_tokens
            save_run_summary(summary)

            if tracker:
                tracker.emit(
                    ProgressEvent(
                        type=EventType.ITEM_COMPLETE,
                        scenario_id=scenario.id,
                        model=model,
                        condition=condition,
                        completed=completed,
                        total=total,
                        tokens_used=result.input_tokens + result.output_tokens,
                        cost_usd=round(cost, 6),
                    )
                )

        except Exception as e:
            completed += 1
            if tracker:
                tracker.emit(
                    ProgressEvent(
                        type=EventType.ITEM_ERROR,
                        scenario_id=scenario.id,
                        model=model,
                        condition=condition,
                        completed=completed,
                        total=total,
                        error=str(e),
                    )
                )

    # Execute all work items concurrently (bounded by semaphore)
    tasks = [run_one(s, m, c) for s, m, c in work_items]
    await asyncio.gather(*tasks, return_exceptions=True)

    # Finalize
    summary.status = RunStatus.COMPLETED
    summary.completed_at = datetime.now(timezone.utc)
    summary.completed_items = completed
    summary.total_cost_usd = round(total_cost, 4)
    summary.total_tokens = total_tokens
    save_run_summary(summary)

    if tracker:
        tracker.emit(
            ProgressEvent(
                type=EventType.RUN_COMPLETE,
                completed=completed,
                total=total,
                summary={
                    "total_cost_usd": round(total_cost, 4),
                    "total_tokens": total_tokens,
                    "duration_seconds": (
                        summary.completed_at - summary.created_at
                    ).total_seconds(),
                },
            )
        )

    return summary
