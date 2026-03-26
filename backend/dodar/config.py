from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings

# Resolve paths relative to backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DATA_DIR = _BACKEND_DIR / "data"


class Settings(BaseSettings):
    # API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # Data directories
    data_dir: Path = _DATA_DIR
    scenarios_dir: Path = _DATA_DIR / "scenarios"
    runs_dir: Path = _DATA_DIR / "runs"
    scores_dir: Path = _DATA_DIR / "scores"

    # Execution
    default_concurrency: int = 5
    request_timeout_seconds: int = 120
    max_retries: int = 3

    # Models
    anthropic_model: str = "claude-sonnet-4-5"
    openai_model: str = "gpt-4o"
    google_model: str = "gemini-2.0-flash"
    autoscore_model: str = "claude-opus-4-6"  # Model used for auto-scoring

    # Pricing (per 1M tokens)
    model_pricing: dict[str, dict[str, float]] = {
        "claude-opus-4-6": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
        "claude-haiku-4-5": {"input": 0.80, "output": 4.0},
        "gpt-5.4": {"input": 2.5, "output": 10.0},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
        "gpt-4.1": {"input": 2.0, "output": 8.0},
        "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
        "o4-mini": {"input": 1.10, "output": 4.40},
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "qwen2.5:32b": {"input": 0.0, "output": 0.0},
        "qwen2.5:14b": {"input": 0.0, "output": 0.0},
        "qwen2.5:7b": {"input": 0.0, "output": 0.0},
        "llama3.1:8b": {"input": 0.0, "output": 0.0},
        "phi3:3.8b": {"input": 0.0, "output": 0.0},
    }

    model_config = {
        "env_file": [
            _BACKEND_DIR / ".env",
            _BACKEND_DIR.parent / ".env",
        ],
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        # Ensure data dirs exist
        _settings.runs_dir.mkdir(parents=True, exist_ok=True)
        _settings.scores_dir.mkdir(parents=True, exist_ok=True)
    return _settings


# Canonical model identifiers
MODEL_IDS = {
    "claude-opus-4-6": "claude-opus-4-6",
    "claude-sonnet-4-5": "claude-sonnet-4-5",
    "claude-haiku-4-5": "claude-haiku-4-5",
    "gpt-5.4": "gpt-5.4",
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-4.1-mini": "gpt-4.1-mini",
    "gpt-4.1": "gpt-4.1",
    "gpt-4.1-nano": "gpt-4.1-nano",
    "o4-mini": "o4-mini",
    "gemini-2.0-flash": "gemini-2.0-flash",
    "qwen2.5:32b": "qwen2.5:32b",
    "qwen2.5:14b": "qwen2.5:14b",
    "qwen2.5:7b": "qwen2.5:7b",
    "llama3.1:8b": "llama3.1:8b",
    "phi3:3.8b": "phi3:3.8b",
}

# Phase 1 scenario-based conditions
CONDITION_IDS = ["zero_shot", "cot", "length_matched", "dodar", "dodar_pipeline"]

# Phase 2 benchmark conditions (letter codes from protocol)
BENCHMARK_CONDITION_CODES = ["A", "B", "C", "D", "E", "F", "G"]

SCORING_DIMENSIONS = [
    "Diagnosis Quality",
    "Option Breadth",
    "Decision Justification",
    "Action Specificity",
    "Review / Self-Correction",
    "Overall Trustworthiness",
]
