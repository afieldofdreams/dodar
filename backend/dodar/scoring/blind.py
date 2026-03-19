"""Blind assignment generation for scoring sessions."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from dodar.models.scoring import BlindItem, ScoringSession
from dodar.storage.runs import load_all_results, load_run_summary


def create_scoring_session(
    scorer: str,
    run_id: str,
    seed: int | None = None,
) -> ScoringSession:
    """Create a blind scoring session for a specific benchmark run."""
    summary = load_run_summary(run_id)
    if not summary:
        raise ValueError(f"Run '{run_id}' not found")

    # Load results matching this run's config and version
    all_results = load_all_results(prompt_version=summary.prompt_version)
    config = summary.config

    results = [
        r for r in all_results
        if r.scenario_id in config.scenario_ids
        and r.model in config.models
        and r.condition in config.conditions
    ]

    if not results:
        raise ValueError(f"No results found for run '{run_id}'")

    if seed is None:
        seed = random.randint(0, 2**31)

    items: list[BlindItem] = []
    for result in results:
        items.append(
            BlindItem(
                item_id=uuid.uuid4().hex[:12],
                scenario_id=result.scenario_id,
                model=result.model,
                condition=result.condition,
                prompt_version=getattr(result, "prompt_version", "v1"),
                run_result_file=f"{result.run_id}.json",
            )
        )

    rng = random.Random(seed)
    order = [item.item_id for item in items]
    rng.shuffle(order)

    session_id = f"sess-{uuid.uuid4().hex[:8]}"

    return ScoringSession(
        session_id=session_id,
        scorer=scorer,
        run_id=run_id,
        created_at=datetime.now(timezone.utc),
        seed=seed,
        items=items,
        order=order,
    )
