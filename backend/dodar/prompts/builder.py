"""Prompt builder — generates prompts for each experimental condition."""

from __future__ import annotations

from dodar.models.scenario import Scenario
from dodar.prompts.templates import (
    COT_TEMPLATE,
    DODAR_TEMPLATE,
    LENGTH_MATCHED_FILLERS,
    LENGTH_MATCHED_PREFIX,
    LENGTH_MATCHED_SUFFIX,
    ZERO_SHOT_TEMPLATE,
)
from dodar.prompts.token_budget import count_tokens


def build_prompt(scenario: Scenario, condition: str) -> str:
    """Build the full prompt for a scenario under a given condition."""
    match condition:
        case "zero_shot":
            return ZERO_SHOT_TEMPLATE.format(prompt_text=scenario.prompt_text)
        case "cot":
            return COT_TEMPLATE.format(prompt_text=scenario.prompt_text)
        case "length_matched":
            return _build_length_matched(scenario)
        case "dodar":
            return DODAR_TEMPLATE.format(prompt_text=scenario.prompt_text)
        case _:
            raise ValueError(f"Unknown condition: {condition}")


def _build_length_matched(scenario: Scenario) -> str:
    """Build a length-matched prompt that targets the same token count as DODAR."""
    dodar_prompt = DODAR_TEMPLATE.format(prompt_text=scenario.prompt_text)
    target_tokens = count_tokens(dodar_prompt)

    # Start with base template
    base = LENGTH_MATCHED_PREFIX + f"\n{scenario.prompt_text}\n" + LENGTH_MATCHED_SUFFIX
    current_tokens = count_tokens(base)

    # Add filler sentences until we're within 5% of the DODAR token count
    fillers_used: list[str] = []
    for filler in LENGTH_MATCHED_FILLERS:
        if current_tokens >= target_tokens * 0.95:
            break
        fillers_used.append(filler)
        candidate = (
            LENGTH_MATCHED_PREFIX
            + "\n"
            + " ".join(fillers_used)
            + f"\n\n{scenario.prompt_text}\n"
            + LENGTH_MATCHED_SUFFIX
        )
        current_tokens = count_tokens(candidate)

    # Assemble final prompt
    filler_block = " ".join(fillers_used)
    if filler_block:
        prompt = (
            LENGTH_MATCHED_PREFIX
            + "\n"
            + filler_block
            + f"\n\n{scenario.prompt_text}\n"
            + LENGTH_MATCHED_SUFFIX
        )
    else:
        prompt = base

    return prompt
