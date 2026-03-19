from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DimensionScore(BaseModel):
    dimension: str
    score: int  # 1-5
    rationale: str | None = None


class ScoreCard(BaseModel):
    item_id: str
    scores: list[DimensionScore]
    scored_at: datetime


class BlindItem(BaseModel):
    item_id: str
    scenario_id: str
    model: str  # hidden from scorer
    condition: str  # hidden from scorer
    prompt_version: str = "v1"  # which prompt version produced this result
    run_result_file: str  # path to the run result JSON


class BlindAssignment(BaseModel):
    session_id: str
    scorer: str
    created_at: datetime
    seed: int
    items: list[BlindItem]
    order: list[str]  # shuffled item_ids


class ScoringSession(BaseModel):
    session_id: str
    scorer: str
    run_id: str = ""  # which benchmark run this scores
    created_at: datetime
    seed: int
    items: list[BlindItem]
    order: list[str]
    scores: dict[str, ScoreCard] = {}  # keyed by item_id
    revealed: bool = False
