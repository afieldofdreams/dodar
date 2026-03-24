"""DODAR — Structured reasoning framework for AI agents.

Usage:
    from dodar import DODAR

    dodar = DODAR(model="gpt-4.1-mini")
    result = dodar.analyze("Your scenario here...")

    print(result.diagnosis.hypotheses)
    print(result.decision.recommendation)
    print(result.review.failure_modes)
"""

from dodar.core import (
    DODAR,
    DODARResult,
    DiagnosisResult,
    OptionsResult,
    DecisionResult,
    ActionResult,
    ReviewResult,
)
from dodar.runners import available_models

__version__ = "0.1.0"

__all__ = [
    "DODAR",
    "DODARResult",
    "DiagnosisResult",
    "OptionsResult",
    "DecisionResult",
    "ActionResult",
    "ReviewResult",
    "available_models",
    "__version__",
]
