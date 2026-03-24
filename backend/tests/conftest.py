"""Shared fixtures for DODAR tests."""

from __future__ import annotations

import pytest

from dodar.models.scenario import Discriminator, Scenario


@pytest.fixture
def sample_scenario() -> Scenario:
    """A minimal valid scenario for unit tests."""
    return Scenario(
        id="TEST-01",
        category="TEST",
        title="Test Scenario",
        domain="business",
        difficulty="medium",
        prompt_text="You face a complex decision. What do you do?",
        expected_pitfalls=[
            "Anchors on the obvious answer",
            "Ignores second-order effects",
        ],
        gold_standard_elements=[
            "Considers multiple hypotheses",
            "Proposes diagnostic steps",
        ],
        discriminators=[
            Discriminator(
                dimension="Diagnosis Quality",
                description="Holds diagnosis open with 3+ hypotheses",
            ),
            Discriminator(
                dimension="Option Breadth",
                description="Generates genuinely distinct alternatives",
            ),
        ],
    )
