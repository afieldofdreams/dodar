"""
DODAR SDK — Structured reasoning for AI agents.

Usage:
    from dodar import DODAR

    dodar = DODAR(provider="anthropic", model="claude-sonnet-4-5")
    result = dodar.analyze("Your scenario here...")

    # Access structured phases
    print(result.diagnosis.hypotheses)
    print(result.options.alternatives)
    print(result.decision.recommendation)
    print(result.action.steps)
    print(result.review.failure_modes)

    # Or get the full text
    print(result.text)

    # Compare with baseline
    baseline = dodar.analyze("Same scenario...", mode="zero_shot")
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Literal

from dodar.prompts.templates import DODAR_TEMPLATE, ZERO_SHOT_TEMPLATE, COT_TEMPLATE
from dodar.runners.registry import get_runner, available_models


# --------------------------------------------------------------------------- #
# Result dataclasses — structured access to each DODAR phase
# --------------------------------------------------------------------------- #

@dataclass
class DiagnosisResult:
    """Structured output from the Diagnose phase."""
    raw_text: str = ""
    hypotheses: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)


@dataclass
class OptionsResult:
    """Structured output from the Options phase."""
    raw_text: str = ""
    alternatives: list[str] = field(default_factory=list)
    core_tension: str = ""
    trade_offs: list[str] = field(default_factory=list)


@dataclass
class DecisionResult:
    """Structured output from the Decide phase."""
    raw_text: str = ""
    recommendation: str = ""
    confidence: str = ""
    falsifiability: str = ""


@dataclass
class ActionResult:
    """Structured output from the Action phase."""
    raw_text: str = ""
    steps: list[str] = field(default_factory=list)
    reversible_steps: list[str] = field(default_factory=list)
    irreversible_steps: list[str] = field(default_factory=list)


@dataclass
class ReviewResult:
    """Structured output from the Review phase."""
    raw_text: str = ""
    failure_modes: list[str] = field(default_factory=list)
    assumptions_to_validate: list[str] = field(default_factory=list)
    abort_conditions: list[str] = field(default_factory=list)


@dataclass
class DODARResult:
    """Complete DODAR analysis result with structured phase access."""
    text: str = ""
    diagnosis: DiagnosisResult = field(default_factory=DiagnosisResult)
    options: OptionsResult = field(default_factory=OptionsResult)
    decision: DecisionResult = field(default_factory=DecisionResult)
    action: ActionResult = field(default_factory=ActionResult)
    review: ReviewResult = field(default_factory=ReviewResult)
    input_tokens: int = 0
    output_tokens: int = 0
    latency_seconds: float = 0.0
    model: str = ""
    mode: str = "dodar"


# --------------------------------------------------------------------------- #
# Phase parser — extracts structured data from DODAR output
# --------------------------------------------------------------------------- #

def _split_phases(text: str) -> dict[str, str]:
    """Split a DODAR response into its five phases by header."""
    phases: dict[str, str] = {}
    phase_names = ["DIAGNOSE", "OPTIONS", "DECIDE", "ACTION", "REVIEW"]

    # Match ## Phase N: NAME or just ## DIAGNOSE etc.
    pattern = r"##\s*(?:Phase\s*\d+\s*:\s*)?(" + "|".join(phase_names) + r")\b"
    matches = list(re.finditer(pattern, text, re.IGNORECASE))

    for i, match in enumerate(matches):
        name = match.group(1).upper()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        phases[name] = text[start:end].strip()

    return phases


def _extract_list_items(text: str) -> list[str]:
    """Extract numbered or bulleted list items from text."""
    items = []
    for line in text.split("\n"):
        line = line.strip()
        # Match "1. ...", "- ...", "* ...", "• ..."
        m = re.match(r"^(?:\d+[\.\)]\s*|\-\s+|\*\s+|•\s+)(.+)", line)
        if m:
            items.append(m.group(1).strip())
    return items


def _parse_diagnosis(text: str) -> DiagnosisResult:
    result = DiagnosisResult(raw_text=text)
    items = _extract_list_items(text)
    result.hypotheses = items[:10]  # First set of list items are typically hypotheses

    # Look for assumption/unknown sections
    lower = text.lower()
    if "assumption" in lower or "assuming" in lower:
        for line in text.split("\n"):
            if any(kw in line.lower() for kw in ["assumption", "assuming", "presuppose"]):
                result.assumptions.append(line.strip().lstrip("-*• "))
    if "unknown" in lower or "missing" in lower:
        for line in text.split("\n"):
            if any(kw in line.lower() for kw in ["unknown", "missing", "don't know", "unclear"]):
                result.unknowns.append(line.strip().lstrip("-*• "))

    return result


def _parse_options(text: str) -> OptionsResult:
    result = OptionsResult(raw_text=text)
    result.alternatives = _extract_list_items(text)

    # Look for tension statement
    lower = text.lower()
    for line in text.split("\n"):
        if any(kw in line.lower() for kw in ["core tension", "fundamental trade-off", "key tension"]):
            result.core_tension = line.strip().lstrip("-*• :").strip()
            break

    return result


def _parse_decision(text: str) -> DecisionResult:
    result = DecisionResult(raw_text=text)

    # First substantive paragraph is usually the recommendation
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if paragraphs:
        result.recommendation = paragraphs[0]

    # Look for confidence
    for line in text.split("\n"):
        lower = line.lower()
        if "confidence" in lower:
            result.confidence = line.strip().lstrip("-*• :").strip()
        if any(kw in lower for kw in ["change my mind", "falsif", "prove wrong", "would change"]):
            result.falsifiability = line.strip().lstrip("-*• :").strip()

    return result


def _parse_action(text: str) -> ActionResult:
    result = ActionResult(raw_text=text)
    result.steps = _extract_list_items(text)

    for step in result.steps:
        lower = step.lower()
        if any(kw in lower for kw in ["reversible", "can undo", "can revert", "low risk"]):
            result.reversible_steps.append(step)
        if any(kw in lower for kw in ["irreversible", "cannot undo", "permanent", "point of no return"]):
            result.irreversible_steps.append(step)

    return result


def _parse_review(text: str) -> ReviewResult:
    result = ReviewResult(raw_text=text)
    result.failure_modes = _extract_list_items(text)

    for line in text.split("\n"):
        lower = line.lower()
        if any(kw in lower for kw in ["assumption", "validate", "verify", "check whether"]):
            result.assumptions_to_validate.append(line.strip().lstrip("-*• "))
        if any(kw in lower for kw in ["abandon", "abort", "switch to", "pivot", "bail"]):
            result.abort_conditions.append(line.strip().lstrip("-*• "))

    return result


def _parse_dodar_response(text: str) -> DODARResult:
    """Parse a full DODAR response into structured phases."""
    result = DODARResult(text=text)
    phases = _split_phases(text)

    if "DIAGNOSE" in phases:
        result.diagnosis = _parse_diagnosis(phases["DIAGNOSE"])
    if "OPTIONS" in phases:
        result.options = _parse_options(phases["OPTIONS"])
    if "DECIDE" in phases:
        result.decision = _parse_decision(phases["DECIDE"])
    if "ACTION" in phases:
        result.action = _parse_action(phases["ACTION"])
    if "REVIEW" in phases:
        result.review = _parse_review(phases["REVIEW"])

    return result


# --------------------------------------------------------------------------- #
# Main DODAR class
# --------------------------------------------------------------------------- #

Mode = Literal["dodar", "zero_shot", "cot"]


class DODAR:
    """DODAR reasoning framework for AI agents.

    Args:
        model: Model ID to use (e.g., "claude-sonnet-4-5", "gpt-4o", "llama3.1:8b").
            See dodar.available_models() for full list.

    Example:
        >>> dodar = DODAR(model="claude-sonnet-4-5")
        >>> result = dodar.analyze("Your scenario...")
        >>> print(result.diagnosis.hypotheses)
        >>> print(result.decision.recommendation)
    """

    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        if model not in available_models():
            raise ValueError(
                f"Unknown model: {model}. Available: {available_models()}"
            )
        self._model = model
        self._runner = get_runner(model)

    @property
    def model(self) -> str:
        return self._model

    def analyze(self, scenario: str, mode: Mode = "dodar") -> DODARResult:
        """Analyze a scenario using DODAR (or a baseline mode).

        Args:
            scenario: The scenario text to analyze.
            mode: "dodar" for full framework, "zero_shot" for baseline,
                  "cot" for chain-of-thought.

        Returns:
            DODARResult with structured phase access.
        """
        return asyncio.get_event_loop().run_until_complete(
            self.analyze_async(scenario, mode)
        )

    async def analyze_async(self, scenario: str, mode: Mode = "dodar") -> DODARResult:
        """Async version of analyze."""
        prompt = self._build_prompt(scenario, mode)
        response = await self._runner.run(prompt)

        if mode == "dodar":
            result = _parse_dodar_response(response.text)
        else:
            result = DODARResult(text=response.text)

        result.input_tokens = response.input_tokens
        result.output_tokens = response.output_tokens
        result.latency_seconds = response.latency_seconds
        result.model = self._model
        result.mode = mode

        return result

    def _build_prompt(self, scenario: str, mode: Mode) -> str:
        match mode:
            case "dodar":
                return DODAR_TEMPLATE.format(prompt_text=scenario)
            case "zero_shot":
                return ZERO_SHOT_TEMPLATE.format(prompt_text=scenario)
            case "cot":
                return COT_TEMPLATE.format(prompt_text=scenario)
            case _:
                raise ValueError(f"Unknown mode: {mode}")

    def __repr__(self) -> str:
        return f"DODAR(model={self._model!r})"
