"""DODAR — Structured reasoning framework for AI agents.

Usage:
    from dodar import DODAR

    dodar = DODAR(model="claude-sonnet-4-5")
    result = dodar.analyze("Your scenario here...")

    print(result.diagnosis.hypotheses)
    print(result.decision.recommendation)
    print(result.review.failure_modes)
"""

from dodar.sdk import (
    DODAR,
    DODARResult,
    DiagnosisResult,
    OptionsResult,
    DecisionResult,
    ActionResult,
    ReviewResult,
)
from dodar.agents import DODARPipeline, PipelineResult
from dodar.runners.registry import available_models

__all__ = [
    "DODAR",
    "DODARResult",
    "DiagnosisResult",
    "OptionsResult",
    "DecisionResult",
    "ActionResult",
    "ReviewResult",
    "DODARPipeline",
    "PipelineResult",
    "available_models",
]
