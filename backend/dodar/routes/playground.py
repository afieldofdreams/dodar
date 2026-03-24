"""Playground API — live DODAR analysis for the web UI."""

from __future__ import annotations

import re

from fastapi import APIRouter
from pydantic import BaseModel

from dodar.prompts.templates import DODAR_TEMPLATE, ZERO_SHOT_TEMPLATE, COT_TEMPLATE
from dodar.runners.registry import get_runner

router = APIRouter(tags=["playground"])


class AnalyzeRequest(BaseModel):
    scenario: str
    model: str = "claude-sonnet-4-5"
    mode: str = "dodar"  # dodar, zero_shot, cot


class AnalyzeResponse(BaseModel):
    text: str
    phases: dict[str, str] | None = None
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    model: str
    mode: str


def _split_phases(text: str) -> dict[str, str] | None:
    """Extract DODAR phases from response text."""
    phase_names = ["DIAGNOSE", "OPTIONS", "DECIDE", "ACTION", "REVIEW"]
    pattern = r"##\s*(?:Phase\s*\d+\s*:\s*)?(" + "|".join(phase_names) + r")\b"
    matches = list(re.finditer(pattern, text, re.IGNORECASE))

    if len(matches) < 3:  # Need at least 3 phases to consider it structured
        return None

    phases: dict[str, str] = {}
    for i, match in enumerate(matches):
        name = match.group(1).upper().lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        phases[name] = text[start:end].strip()

    return phases


def _build_prompt(scenario: str, mode: str) -> str:
    match mode:
        case "dodar":
            return DODAR_TEMPLATE.format(prompt_text=scenario)
        case "zero_shot":
            return ZERO_SHOT_TEMPLATE.format(prompt_text=scenario)
        case "cot":
            return COT_TEMPLATE.format(prompt_text=scenario)
        case _:
            raise ValueError(f"Unknown mode: {mode}")


@router.post("/analyze")
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    runner = get_runner(req.model)
    prompt = _build_prompt(req.scenario, req.mode)
    response = await runner.run(prompt)

    phases = _split_phases(response.text) if req.mode == "dodar" else None

    return AnalyzeResponse(
        text=response.text,
        phases=phases,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        latency_seconds=round(response.latency_seconds, 2),
        model=req.model,
        mode=req.mode,
    )
