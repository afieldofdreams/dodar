"""Prompt builder for Phase 2 benchmark tasks.

Assembles system prompt + user message for each (task, condition) pair.
Returns a PromptPair so the executor can pass system and user messages separately.
"""

from __future__ import annotations

from dataclasses import dataclass

from dodar.models.benchmark import BenchmarkTask
from dodar.prompts.conditions import (
    CONDITIONS,
    get_universal_suffix,
    get_worked_example,
)


@dataclass
class PromptPair:
    """System prompt and user message, kept separate for proper API usage."""

    system_prompt: str | None
    user_message: str


def build_benchmark_prompt(task: BenchmarkTask, condition_code: str) -> PromptPair:
    """Build the full prompt pair for a benchmark task under a condition.

    Returns separate system_prompt and user_message for proper API message structure.
    """
    condition = CONDITIONS.get(condition_code)
    if condition is None:
        raise ValueError(
            f"Unknown condition code: {condition_code}. "
            f"Available: {list(CONDITIONS.keys())}"
        )

    # --- System prompt ---
    system_prompt = condition.system_prompt  # None for baseline (A)

    # --- User message assembly ---
    parts: list[str] = []

    # Condition instruction (if any)
    if condition.condition_instruction:
        parts.append(condition.condition_instruction)

    # Few-shot example (Condition G only)
    if condition.few_shot:
        example = get_worked_example(task.source, task.category)
        parts.append(
            f"Here is an example of careful step-by-step reasoning on a different problem:\n\n"
            f"{example}\n\n"
            f"Now solve the following problem using the same careful reasoning approach."
        )

    # Question text
    parts.append(task.question)

    # Formatted options (for multiple choice)
    if task.options:
        options_text = "\n".join(f"  {k}: {v}" for k, v in task.options.items())
        parts.append(options_text)

    # Universal suffix (FINAL ANSWER format)
    parts.append(get_universal_suffix(task.answer_type))

    user_message = "\n\n".join(parts)

    return PromptPair(system_prompt=system_prompt, user_message=user_message)
