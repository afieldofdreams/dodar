"""DODAR core — the main DODAR class and result types."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Literal

from dodar.prompts import (
    DODAR_SINGLE, ZERO_SHOT, COT,
    PIPELINE_DIAGNOSE, PIPELINE_OPTIONS, PIPELINE_DECIDE,
    PIPELINE_ACTION, PIPELINE_REVIEW,
)
from dodar.runners import run_model, available_models


# --------------------------------------------------------------------------- #
# Result dataclasses
# --------------------------------------------------------------------------- #

@dataclass
class DiagnosisResult:
    raw_text: str = ""
    hypotheses: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)


@dataclass
class OptionsResult:
    raw_text: str = ""
    alternatives: list[str] = field(default_factory=list)
    core_tension: str = ""
    trade_offs: list[str] = field(default_factory=list)


@dataclass
class DecisionResult:
    raw_text: str = ""
    recommendation: str = ""
    confidence: str = ""
    falsifiability: str = ""


@dataclass
class ActionResult:
    raw_text: str = ""
    steps: list[str] = field(default_factory=list)
    reversible_steps: list[str] = field(default_factory=list)
    irreversible_steps: list[str] = field(default_factory=list)


@dataclass
class ReviewResult:
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
# Parsing
# --------------------------------------------------------------------------- #

def _extract_list_items(text: str) -> list[str]:
    items = []
    for line in text.split("\n"):
        line = line.strip()
        m = re.match(r"^(?:\d+[\.\)]\s*|\-\s+|\*\s+|•\s+)(.+)", line)
        if m:
            items.append(m.group(1).strip())
    return items


def _split_phases(text: str) -> dict[str, str]:
    phases: dict[str, str] = {}
    phase_names = ["DIAGNOSE", "OPTIONS", "DECIDE", "ACTION", "REVIEW"]
    pattern = r"##?\s*(?:Phase\s*\d+\s*[:\-]\s*)?(" + "|".join(phase_names) + r")\b"
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    for i, match in enumerate(matches):
        name = match.group(1).upper()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        phases[name] = text[start:end].strip()
    return phases


def _parse_phase(text: str, phase: str) -> DiagnosisResult | OptionsResult | DecisionResult | ActionResult | ReviewResult:
    items = _extract_list_items(text)
    lower = text.lower()

    if phase == "DIAGNOSE":
        r = DiagnosisResult(raw_text=text, hypotheses=items[:10])
        for line in text.split("\n"):
            if any(kw in line.lower() for kw in ["assumption", "assuming"]):
                r.assumptions.append(line.strip().lstrip("-*• "))
            if any(kw in line.lower() for kw in ["unknown", "missing"]):
                r.unknowns.append(line.strip().lstrip("-*• "))
        return r

    if phase == "OPTIONS":
        r = OptionsResult(raw_text=text, alternatives=items)
        for line in text.split("\n"):
            if any(kw in line.lower() for kw in ["core tension", "fundamental trade-off"]):
                r.core_tension = line.strip().lstrip("-*• :").strip()
                break
        return r

    if phase == "DECIDE":
        r = DecisionResult(raw_text=text)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if paragraphs:
            r.recommendation = paragraphs[0]
        for line in text.split("\n"):
            if "confidence" in line.lower():
                r.confidence = line.strip().lstrip("-*• :").strip()
            if any(kw in line.lower() for kw in ["change my mind", "falsif"]):
                r.falsifiability = line.strip().lstrip("-*• :").strip()
        return r

    if phase == "ACTION":
        r = ActionResult(raw_text=text, steps=items)
        for step in items:
            sl = step.lower()
            if any(kw in sl for kw in ["reversible", "can undo"]):
                r.reversible_steps.append(step)
            if any(kw in sl for kw in ["irreversible", "cannot undo", "permanent"]):
                r.irreversible_steps.append(step)
        return r

    # REVIEW
    r = ReviewResult(raw_text=text, failure_modes=items)
    for line in text.split("\n"):
        ll = line.lower()
        if any(kw in ll for kw in ["assumption", "validate"]):
            r.assumptions_to_validate.append(line.strip().lstrip("-*• "))
        if any(kw in ll for kw in ["abandon", "abort", "pivot"]):
            r.abort_conditions.append(line.strip().lstrip("-*• "))
    return r


def _parse_response(text: str) -> DODARResult:
    result = DODARResult(text=text)
    phases = _split_phases(text)
    if "DIAGNOSE" in phases:
        result.diagnosis = _parse_phase(phases["DIAGNOSE"], "DIAGNOSE")  # type: ignore
    if "OPTIONS" in phases:
        result.options = _parse_phase(phases["OPTIONS"], "OPTIONS")  # type: ignore
    if "DECIDE" in phases:
        result.decision = _parse_phase(phases["DECIDE"], "DECIDE")  # type: ignore
    if "ACTION" in phases:
        result.action = _parse_phase(phases["ACTION"], "ACTION")  # type: ignore
    if "REVIEW" in phases:
        result.review = _parse_phase(phases["REVIEW"], "REVIEW")  # type: ignore
    return result


# --------------------------------------------------------------------------- #
# Main class
# --------------------------------------------------------------------------- #

Mode = Literal["dodar", "pipeline", "zero_shot", "cot"]


class DODAR:
    """DODAR structured reasoning framework for AI agents.

    Args:
        model: Model ID (e.g., "gpt-4.1-mini", "claude-sonnet-4-5").
        mode: Default mode — "dodar" (single prompt), "pipeline" (5 calls),
              "zero_shot", or "cot".
        max_tokens: Maximum tokens per model call.

    Example::

        dodar = DODAR(model="gpt-4.1-mini")
        result = dodar.analyze("Your scenario...")
        print(result.diagnosis.hypotheses)
    """

    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        mode: Mode = "dodar",
        max_tokens: int = 4096,
    ) -> None:
        self._model = model
        self._default_mode = mode
        self._max_tokens = max_tokens

    @property
    def model(self) -> str:
        return self._model

    def analyze(self, scenario: str, mode: Mode | None = None) -> DODARResult:
        """Analyze a scenario synchronously.

        Args:
            scenario: The scenario text to analyze.
            mode: Override the default mode for this call.

        Returns:
            DODARResult with structured phase access.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run, self.analyze_async(scenario, mode)
                ).result()
        return asyncio.run(self.analyze_async(scenario, mode))

    async def analyze_async(self, scenario: str, mode: Mode | None = None) -> DODARResult:
        """Analyze a scenario asynchronously."""
        m = mode or self._default_mode

        if m == "pipeline":
            return await self._run_pipeline(scenario)

        prompt = self._build_prompt(scenario, m)
        response = await run_model(self._model, prompt, max_tokens=self._max_tokens)

        if m == "dodar":
            result = _parse_response(response.text)
        else:
            result = DODARResult(text=response.text)

        result.input_tokens = response.input_tokens
        result.output_tokens = response.output_tokens
        result.latency_seconds = response.latency_seconds
        result.model = self._model
        result.mode = m
        return result

    async def _run_pipeline(self, scenario: str) -> DODARResult:
        """Run the 5-phase DODAR pipeline."""
        total_input = 0
        total_output = 0
        t0 = __import__("time").monotonic()
        context_parts: list[str] = []

        # Phase 1: Diagnose
        r1 = await run_model(
            self._model,
            PIPELINE_DIAGNOSE.format(scenario=scenario),
            max_tokens=self._max_tokens,
        )
        total_input += r1.input_tokens
        total_output += r1.output_tokens
        context_parts.append(f"## DIAGNOSE\n{r1.text}")

        # Phase 2: Options
        r2 = await run_model(
            self._model,
            PIPELINE_OPTIONS.format(scenario=scenario, prior_context="\n\n".join(context_parts)),
            max_tokens=self._max_tokens,
        )
        total_input += r2.input_tokens
        total_output += r2.output_tokens
        context_parts.append(f"## OPTIONS\n{r2.text}")

        # Phase 3: Decide
        r3 = await run_model(
            self._model,
            PIPELINE_DECIDE.format(scenario=scenario, prior_context="\n\n".join(context_parts)),
            max_tokens=self._max_tokens,
        )
        total_input += r3.input_tokens
        total_output += r3.output_tokens
        context_parts.append(f"## DECIDE\n{r3.text}")

        # Phase 4: Action
        r4 = await run_model(
            self._model,
            PIPELINE_ACTION.format(scenario=scenario, prior_context="\n\n".join(context_parts)),
            max_tokens=self._max_tokens,
        )
        total_input += r4.input_tokens
        total_output += r4.output_tokens
        context_parts.append(f"## ACTION\n{r4.text}")

        # Phase 5: Review
        r5 = await run_model(
            self._model,
            PIPELINE_REVIEW.format(scenario=scenario, prior_context="\n\n".join(context_parts)),
            max_tokens=self._max_tokens,
        )
        total_input += r5.input_tokens
        total_output += r5.output_tokens
        context_parts.append(f"## REVIEW\n{r5.text}")

        full_text = "\n\n".join(context_parts)
        result = _parse_response(full_text)
        result.input_tokens = total_input
        result.output_tokens = total_output
        result.latency_seconds = __import__("time").monotonic() - t0
        result.model = self._model
        result.mode = "pipeline"
        return result

    def _build_prompt(self, scenario: str, mode: Mode) -> str:
        match mode:
            case "dodar":
                return DODAR_SINGLE.format(scenario=scenario)
            case "zero_shot":
                return ZERO_SHOT.format(scenario=scenario)
            case "cot":
                return COT.format(scenario=scenario)
            case _:
                raise ValueError(f"Unknown mode: {mode}")

    def __repr__(self) -> str:
        return f"DODAR(model={self._model!r}, mode={self._default_mode!r})"
