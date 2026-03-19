"""Score aggregation and statistical analysis."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from dodar.config import SCORING_DIMENSIONS
from dodar.models.scoring import ScoringSession
from dodar.storage.runs import load_result


@dataclass
class DimensionStats:
    dimension: str
    model: str
    condition: str
    mean: float
    std: float
    count: int


@dataclass
class EffectSize:
    dimension: str
    model: str
    baseline_condition: str
    dodar_condition: str = "dodar"
    cohens_d: float = 0.0
    baseline_mean: float = 0.0
    dodar_mean: float = 0.0


def aggregate_scores(
    sessions: list[ScoringSession],
    prompt_version: str | None = None,
) -> list[DimensionStats]:
    """Aggregate scores across sessions into per-(model, condition, dimension) stats."""
    # Collect scores by (model, condition, dimension)
    buckets: dict[tuple[str, str, str], list[int]] = defaultdict(list)

    for session in sessions:
        item_map = {item.item_id: item for item in session.items}
        for item_id, score_card in session.scores.items():
            item = item_map.get(item_id)
            if not item:
                continue
            if prompt_version and item.prompt_version != prompt_version:
                continue
            for ds in score_card.scores:
                key = (item.model, item.condition, ds.dimension)
                buckets[key].append(ds.score)

    stats: list[DimensionStats] = []
    for (model, condition, dimension), values in sorted(buckets.items()):
        n = len(values)
        mean = sum(values) / n if n > 0 else 0
        variance = sum((v - mean) ** 2 for v in values) / n if n > 1 else 0
        std = math.sqrt(variance)
        stats.append(
            DimensionStats(
                dimension=dimension,
                model=model,
                condition=condition,
                mean=round(mean, 2),
                std=round(std, 2),
                count=n,
            )
        )

    return stats


def compute_effect_sizes(
    stats: list[DimensionStats],
) -> list[EffectSize]:
    """Compute Cohen's d effect sizes: DODAR vs each baseline condition."""
    # Index stats by (model, condition, dimension)
    idx: dict[tuple[str, str, str], DimensionStats] = {}
    for s in stats:
        idx[(s.model, s.condition, s.dimension)] = s

    effects: list[EffectSize] = []
    baselines = ["zero_shot", "cot", "length_matched"]

    models = sorted({s.model for s in stats})
    for model in models:
        for dim in SCORING_DIMENSIONS:
            dodar_stat = idx.get((model, "dodar", dim))
            if not dodar_stat or dodar_stat.count < 2:
                continue
            for baseline in baselines:
                base_stat = idx.get((model, baseline, dim))
                if not base_stat or base_stat.count < 2:
                    continue

                pooled_std = math.sqrt(
                    (dodar_stat.std**2 + base_stat.std**2) / 2
                )
                d = (dodar_stat.mean - base_stat.mean) / pooled_std if pooled_std > 0 else 0

                effects.append(
                    EffectSize(
                        dimension=dim,
                        model=model,
                        baseline_condition=baseline,
                        cohens_d=round(d, 3),
                        baseline_mean=base_stat.mean,
                        dodar_mean=dodar_stat.mean,
                    )
                )

    return effects
