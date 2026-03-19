"""Cost estimation for benchmark runs."""

from __future__ import annotations

from dataclasses import dataclass

from dodar.config import get_settings
from dodar.models.scenario import Scenario
from dodar.prompts.builder import build_prompt
from dodar.prompts.token_budget import count_tokens


@dataclass
class CostEstimate:
    model: str
    condition: str
    scenario_count: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float


def estimate_run_cost(
    scenarios: list[Scenario],
    models: list[str],
    conditions: list[str],
) -> list[CostEstimate]:
    """Estimate cost for a benchmark run without executing."""
    settings = get_settings()
    estimates: list[CostEstimate] = []

    for model in models:
        pricing = settings.model_pricing.get(model, {"input": 0, "output": 0})
        for condition in conditions:
            total_input = 0
            for scenario in scenarios:
                prompt = build_prompt(scenario, condition)
                total_input += count_tokens(prompt, model)

            # Estimate output at ~2000 tokens per response
            est_output = len(scenarios) * 2000
            cost = (total_input / 1_000_000 * pricing["input"]) + (
                est_output / 1_000_000 * pricing["output"]
            )

            estimates.append(
                CostEstimate(
                    model=model,
                    condition=condition,
                    scenario_count=len(scenarios),
                    estimated_input_tokens=total_input,
                    estimated_output_tokens=est_output,
                    estimated_cost_usd=round(cost, 4),
                )
            )

    return estimates
