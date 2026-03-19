from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Discriminator(BaseModel):
    dimension: str
    description: str


class Scenario(BaseModel):
    id: str
    category: str
    title: str
    domain: str
    difficulty: Literal["easy", "medium", "hard"]
    prompt_text: str
    expected_pitfalls: list[str]
    gold_standard_elements: list[str]
    discriminators: list[Discriminator]


class ScenarioFile(BaseModel):
    """Top-level wrapper for a YAML scenario file."""

    scenarios: list[Scenario]
