from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunConfig(BaseModel):
    scenario_ids: list[str]
    models: list[str]
    conditions: list[str]
    skip_completed: bool = True
    prompt_version: str = "v1"


class RunResult(BaseModel):
    run_id: str  # {scenario_id}_{model}_{condition}
    scenario_id: str
    model: str
    condition: str
    prompt_version: str = "v1"
    timestamp: datetime
    prompt_sent: str
    response_text: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    cost_usd: float


class RunItemProgress(BaseModel):
    scenario_id: str
    model: str
    condition: str
    status: RunStatus = RunStatus.PENDING
    tokens_used: int = 0
    cost_usd: float = 0.0
    error: str | None = None


class RunSummary(BaseModel):
    run_id: str
    config: RunConfig
    status: RunStatus
    created_at: datetime
    completed_at: datetime | None = None
    prompt_version: str = "v1"
    total_items: int
    completed_items: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    items: list[RunItemProgress] = []
