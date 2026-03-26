"""Data models for Phase 2 benchmark tasks and results."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel


class AnswerType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    NUMERIC_EXACT = "numeric_exact"
    EXACT_MATCH = "exact_match"


class BenchmarkTask(BaseModel):
    """A single benchmark task from the 100-task set."""

    id: str  # e.g., "MED-001", "GSM-041"
    source: str  # e.g., "MedQA-USMLE", "GSM8K"
    source_index: int | None = None
    category: str  # e.g., "clinical_reasoning", "mathematical_reasoning"
    question: str
    options: dict[str, str] | None = None  # e.g., {"A": "...", "B": "..."}
    correct_answer: str  # e.g., "A", "5600", "Yes"
    correct_answer_text: str | None = None  # e.g., "Throat culture"
    answer_type: AnswerType
    reasoning_steps: int | None = None  # for GSM8K
    word_count: int | None = None


class BenchmarkTaskSet(BaseModel):
    """Top-level wrapper for the benchmark tasks JSON file."""

    metadata: dict
    tasks: list[BenchmarkTask]


# --- Experimental conditions (Phase 2 protocol) ---

class ConditionCode(str, Enum):
    BASELINE = "A"
    ZERO_SHOT_COT = "B"
    PGR = "C"
    REACT = "D"
    STEP_BACK = "E"
    SHUFFLED_PGR = "F"
    FEW_SHOT_COT = "G"


CONDITION_NAMES: dict[str, str] = {
    "A": "Baseline",
    "B": "Zero-Shot CoT",
    "C": "PGR",
    "D": "ReAct",
    "E": "Step-Back",
    "F": "Shuffled PGR",
    "G": "Few-Shot CoT",
}


# --- Benchmark run results ---

class BenchmarkResult(BaseModel):
    """Result of running one benchmark task under one condition with one model."""

    task_id: str
    condition: str  # condition code: A-G
    model_id: str
    run_number: int = 1  # for multi-run stages (1, 2, or 3)
    prompt_version: str = "v3"

    # Timing and cost
    timestamp: datetime
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    cost_usd: float

    # Prompt sent (for debugging/audit)
    system_prompt_sent: str | None = None
    user_prompt_sent: str

    # Response
    raw_response: str
    extracted_answer: str | None = None
    is_correct: bool | None = None

    # Ground truth (copied from task for convenience)
    correct_answer: str
    answer_type: str

    # Metadata
    question: str | None = None  # stored for blinding script convenience
    source: str | None = None


class BenchmarkRunConfig(BaseModel):
    """Configuration for a benchmark run."""

    task_ids: list[str] | None = None  # None = all 100 tasks
    models: list[str]
    conditions: list[str]  # condition codes: ["A", "B", "C", ...]
    runs_per_task: int = 1
    skip_completed: bool = True
    prompt_version: str = "v3"
    execution_seed: int = 42  # for shuffling execution order
    stage: Literal["triage", "validate", "full"] = "triage"


class BenchmarkRunSummary(BaseModel):
    """Summary of a benchmark run."""

    run_id: str
    config: BenchmarkRunConfig
    status: str = "pending"
    created_at: datetime
    completed_at: datetime | None = None

    total_items: int = 0
    completed_items: int = 0
    correct_items: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0

    # Accuracy by condition
    accuracy_by_condition: dict[str, float] = {}
    # Dropout tracking
    dropouts: list[dict] = []


# --- Error classification ---

class ErrorCategory(str, Enum):
    PREMATURE_CLOSURE = "PREMATURE_CLOSURE"
    ANCHORING_ERROR = "ANCHORING_ERROR"
    INCOMPLETE_SEARCH = "INCOMPLETE_SEARCH"
    FAILURE_TO_REVISE = "FAILURE_TO_REVISE"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    COMPREHENSION_FAILURE = "COMPREHENSION_FAILURE"
    ABSTENTION = "ABSTENTION"


class ErrorClassification(BaseModel):
    """Error classification for an incorrect response."""

    task_id: str
    condition: str
    model_id: str
    run_number: int = 1

    classification: ErrorCategory
    reasoning: str
    root_cause_quote: str | None = None
    confidence: Literal["high", "medium", "low"] = "medium"
    rater: str = "human"  # "human", "claude-opus-4-6", "gpt-5.4"
