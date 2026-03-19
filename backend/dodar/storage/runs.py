from __future__ import annotations

import json
from pathlib import Path

from dodar.config import get_settings
from dodar.models.run import RunResult, RunSummary


def make_run_id(scenario_id: str, model: str, condition: str, prompt_version: str = "v1") -> str:
    if prompt_version == "v1":
        return f"{scenario_id}_{model}_{condition}"
    return f"{scenario_id}_{model}_{condition}_{prompt_version}"


def result_path(run_id: str) -> Path:
    return get_settings().runs_dir / f"{run_id}.json"


def result_exists(run_id: str) -> bool:
    return result_path(run_id).exists()


def save_result(result: RunResult) -> None:
    path = result_path(result.run_id)
    path.write_text(result.model_dump_json(indent=2))


def load_result(run_id: str) -> RunResult | None:
    path = result_path(run_id)
    if not path.exists():
        return None
    return RunResult.model_validate_json(path.read_text())


def load_all_results(prompt_version: str | None = None) -> list[RunResult]:
    settings = get_settings()
    results: list[RunResult] = []
    for path in sorted(settings.runs_dir.glob("*.json")):
        if path.name.startswith("_run_"):
            continue  # skip run summary files
        try:
            r = RunResult.model_validate_json(path.read_text())
            if prompt_version and r.prompt_version != prompt_version:
                continue
            results.append(r)
        except Exception:
            continue
    return results


def save_run_summary(summary: RunSummary) -> None:
    path = get_settings().runs_dir / f"_run_{summary.run_id}.json"
    path.write_text(summary.model_dump_json(indent=2))


def load_run_summary(run_id: str) -> RunSummary | None:
    path = get_settings().runs_dir / f"_run_{run_id}.json"
    if not path.exists():
        return None
    return RunSummary.model_validate_json(path.read_text())


def load_all_run_summaries() -> list[RunSummary]:
    settings = get_settings()
    summaries: list[RunSummary] = []
    for path in sorted(settings.runs_dir.glob("_run_*.json")):
        try:
            summaries.append(RunSummary.model_validate_json(path.read_text()))
        except Exception:
            continue
    return summaries


def delete_run(run_id: str) -> int:
    """Delete a run summary and all its result files. Returns count of files deleted."""
    settings = get_settings()
    deleted = 0

    # Delete summary
    summary_path = settings.runs_dir / f"_run_{run_id}.json"
    summary = load_run_summary(run_id)
    if summary_path.exists():
        summary_path.unlink()
        deleted += 1

    # Delete result files matching this run's config
    if summary:
        for path in settings.runs_dir.glob("*.json"):
            if path.name.startswith("_run_"):
                continue
            try:
                r = RunResult.model_validate_json(path.read_text())
                if (
                    r.scenario_id in summary.config.scenario_ids
                    and r.model in summary.config.models
                    and r.condition in summary.config.conditions
                    and r.prompt_version == summary.prompt_version
                ):
                    path.unlink()
                    deleted += 1
            except Exception:
                continue

    return deleted
