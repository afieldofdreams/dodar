"""CLI for headless benchmark execution."""

from __future__ import annotations

import asyncio

import click

from dodar.config import CONDITION_IDS
from dodar.engine.executor import execute_benchmark
from dodar.engine.progress import EventType, ProgressEvent, ProgressTracker
from dodar.runners.registry import available_models
from dodar.storage.scenarios import load_all_scenarios, load_scenarios_filtered
from dodar.models.run import RunConfig


@click.group()
def main():
    """DODAR Validation Benchmark CLI."""
    pass


@main.command()
@click.option("--scenarios", "-s", multiple=True, help="Scenario IDs to run")
@click.option("--models", "-m", multiple=True, help="Model IDs to run")
@click.option("--conditions", "-c", multiple=True, help="Conditions to run")
@click.option("--concurrency", default=5, help="Max concurrent API calls")
def run(scenarios, models, conditions, concurrency):
    """Execute benchmark runs."""
    import uuid
    from dodar.config import get_settings

    settings = get_settings()
    settings.default_concurrency = concurrency

    model_list = list(models) or available_models()
    condition_list = list(conditions) or CONDITION_IDS
    scenario_list = load_scenarios_filtered(ids=list(scenarios) if scenarios else None)

    if not scenario_list:
        click.echo("No scenarios found.")
        return

    config = RunConfig(
        scenario_ids=[s.id for s in scenario_list],
        models=model_list,
        conditions=condition_list,
    )

    total = len(scenario_list) * len(model_list) * len(condition_list)
    click.echo(f"Running {total} items: {len(scenario_list)} scenarios × {len(model_list)} models × {len(condition_list)} conditions")

    tracker = ProgressTracker()

    def on_progress(event: ProgressEvent):
        if event.type == EventType.ITEM_COMPLETE:
            click.echo(
                f"  [{event.completed}/{event.total}] {event.scenario_id} / {event.model} / {event.condition} "
                f"({event.tokens_used} tokens, ${event.cost_usd:.4f})"
            )
        elif event.type == EventType.ITEM_ERROR:
            click.echo(f"  [ERROR] {event.scenario_id} / {event.model} / {event.condition}: {event.error}")
        elif event.type == EventType.RUN_COMPLETE:
            s = event.summary or {}
            click.echo(f"\nComplete! Cost: ${s.get('total_cost_usd', 0):.4f}, Tokens: {s.get('total_tokens', 0)}")

    tracker.add_listener(on_progress)

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    asyncio.run(execute_benchmark(run_id, scenario_list, config, tracker))


@main.command("list")
@click.option("--category", "-c", help="Filter by category")
def list_scenarios(category):
    """List loaded scenarios."""
    scenarios = load_scenarios_filtered(category=category)
    for s in scenarios:
        click.echo(f"  {s.id:<10} {s.difficulty:<8} {s.domain:<12} {s.title}")


@main.command()
def validate():
    """Validate all scenario YAML files."""
    try:
        scenarios = load_all_scenarios()
        click.echo(f"Loaded {len(scenarios)} scenarios successfully.")
        categories = {}
        for s in scenarios:
            categories[s.category] = categories.get(s.category, 0) + 1
        for cat, count in sorted(categories.items()):
            click.echo(f"  {cat}: {count} scenarios")
    except Exception as e:
        click.echo(f"Validation error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
