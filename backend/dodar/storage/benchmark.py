"""Storage layer for benchmark tasks and results."""

from __future__ import annotations

import json
from pathlib import Path

from dodar.config import get_settings
from dodar.models.benchmark import (
    BenchmarkResult,
    BenchmarkRunSummary,
    BenchmarkTask,
    BenchmarkTaskSet,
)

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


def _benchmark_dir() -> Path:
    """Get the benchmark data directory, creating it if needed."""
    d = get_settings().data_dir / "benchmark"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _results_dir() -> Path:
    d = _benchmark_dir() / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- Task loading ---


def load_benchmark_tasks(
    task_file: str | Path | None = None,
) -> list[BenchmarkTask]:
    """Load benchmark tasks from JSON file."""
    if task_file is None:
        # Look in project root first, then backend/data
        candidates = [
            _BACKEND_DIR.parent / "benchmark-tasks-100.json",
            _BACKEND_DIR / "data" / "benchmark-tasks-100.json",
        ]
        for c in candidates:
            if c.exists():
                task_file = c
                break
        if task_file is None:
            raise FileNotFoundError(
                "benchmark-tasks-100.json not found. "
                f"Searched: {[str(c) for c in candidates]}"
            )

    path = Path(task_file)
    data = json.loads(path.read_text())
    task_set = BenchmarkTaskSet.model_validate(data)
    return task_set.tasks


def load_benchmark_tasks_by_id(
    task_file: str | Path | None = None,
) -> dict[str, BenchmarkTask]:
    """Load benchmark tasks indexed by task ID."""
    return {t.id: t for t in load_benchmark_tasks(task_file)}


# --- Result storage ---


def make_benchmark_result_id(
    task_id: str, condition: str, model_id: str, run_number: int = 1
) -> str:
    return f"{task_id}_{model_id}_{condition}_run{run_number}"


def benchmark_result_path(result_id: str) -> Path:
    return _results_dir() / f"{result_id}.json"


def benchmark_result_exists(result_id: str) -> bool:
    return benchmark_result_path(result_id).exists()


def save_benchmark_result(result: BenchmarkResult) -> None:
    rid = make_benchmark_result_id(
        result.task_id, result.condition, result.model_id, result.run_number
    )
    path = benchmark_result_path(rid)
    path.write_text(result.model_dump_json(indent=2))


def load_benchmark_result(result_id: str) -> BenchmarkResult | None:
    path = benchmark_result_path(result_id)
    if not path.exists():
        return None
    return BenchmarkResult.model_validate_json(path.read_text())


def load_all_benchmark_results(
    *,
    model_id: str | None = None,
    condition: str | None = None,
    prompt_version: str | None = None,
) -> list[BenchmarkResult]:
    """Load all benchmark results, optionally filtered."""
    results: list[BenchmarkResult] = []
    for path in sorted(_results_dir().glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            r = BenchmarkResult.model_validate_json(path.read_text())
            if model_id and r.model_id != model_id:
                continue
            if condition and r.condition != condition:
                continue
            if prompt_version and r.prompt_version != prompt_version:
                continue
            results.append(r)
        except Exception:
            continue
    return results


# --- Run summary storage ---


def save_benchmark_run_summary(summary: BenchmarkRunSummary) -> None:
    path = _benchmark_dir() / f"_run_{summary.run_id}.json"
    path.write_text(summary.model_dump_json(indent=2))


def load_benchmark_run_summary(run_id: str) -> BenchmarkRunSummary | None:
    path = _benchmark_dir() / f"_run_{run_id}.json"
    if not path.exists():
        return None
    return BenchmarkRunSummary.model_validate_json(path.read_text())


def load_all_benchmark_run_summaries() -> list[BenchmarkRunSummary]:
    summaries: list[BenchmarkRunSummary] = []
    for path in sorted(_benchmark_dir().glob("_run_*.json")):
        try:
            summaries.append(
                BenchmarkRunSummary.model_validate_json(path.read_text())
            )
        except Exception:
            continue
    return summaries
