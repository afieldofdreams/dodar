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
    anthropic_model: str = "claude-3-haiku-20240307"
    openai_model: str = "gpt-4o"
    google_model: str = "gemini-2.0-flash"
    autoscore_model: str = "claude-3-haiku-20240307"  # Model used for auto-scoring

    # Pricing (per 1M tokens)
    model_pricing: dict[str, dict[str, float]] = {
        "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
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
    "claude-sonnet-4-5": "claude-sonnet-4-5",
    "gpt-4o": "gpt-4o",
    "gemini-2.0-flash": "gemini-2.0-flash",
}

CONDITION_IDS = ["zero_shot", "cot", "length_matched", "dodar"]

SCORING_DIMENSIONS = [
    "Diagnosis Quality",
    "Option Breadth",
    "Decision Justification",
    "Action Specificity",
    "Review / Self-Correction",
    "Overall Trustworthiness",
]
