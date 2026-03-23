"""Automated scoring using Claude Opus 4.6 as evaluator."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone

import anthropic
import openai

from dodar.config import SCORING_DIMENSIONS, get_settings
from dodar.models.scoring import DimensionScore, ScoreCard, ScoringSession
from dodar.storage.runs import load_result
from dodar.storage.scenarios import get_scenario_by_id
from dodar.storage.scores import save_session

def _get_autoscore_model() -> str:
    return get_settings().autoscore_model

AUTOSCORE_SYSTEM_PROMPT = """\
You are an expert evaluator for the DODAR reasoning framework benchmark. \
Your job is to score AI model responses to complex reasoning scenarios.

You will be given:
1. The original scenario prompt
2. The model's response
3. Expected pitfalls (common mistakes)
4. Gold standard elements (what a good response should include)
5. DODAR discriminators (specific behaviors the DODAR framework should surface)

Score the response on each of the 6 dimensions below using a 1-5 scale.

## Scoring Rubric

**Diagnosis Quality (1-5)**
1 = Identifies surface symptom only; commits prematurely to single cause
3 = Identifies 2-3 plausible causes; flags key unknowns
5 = Systematically enumerates root cause candidates; surfaces latent assumptions; acknowledges diagnosis uncertainty

**Option Breadth (1-5)**
1 = Single option or binary choice
3 = 3-4 distinct alternatives with some trade-off language
5 = 5+ genuinely distinct options; novel or counterintuitive approaches; explicit opportunity cost articulation

**Decision Justification (1-5)**
1 = Preference stated without reasoning
3 = Reasoning provided but incomplete (only upside or only downside)
5 = Explicit weighting of trade-offs; acknowledgment of inherent uncertainty; reasoning transparent and falsifiable

**Action Specificity (1-5)**
1 = Vague steps; "monitor the situation"
3 = Concrete steps with rough ordering
5 = Dependency map; critical path; identified blockers; resource/timeline alignment; reversibility of early steps

**Review / Self-Correction (1-5)**
1 = No reflection; decision treated as final
3 = Acknowledges one risk; no follow-up mechanism
5 = Identifies 3+ failure modes; specifies triggers for course correction; flags assumption dependencies; reversibility assessed

**Overall Trustworthiness (1-5)**
1 = Expert would likely reject reasoning or view it as incomplete
3 = Expert would see reasoning as reasonable but with gaps
5 = Expert would view reasoning as rigorous; likely to endorse even if outcome differs

## Important Notes
- Score the REASONING QUALITY, not whether you agree with the conclusion
- Check specifically whether the response falls into the expected pitfalls
- Check whether the response exhibits the DODAR discriminator behaviors
- A response does NOT need to use the DODAR framework explicitly to score well — what matters is whether the reasoning exhibits the qualities each dimension measures
- Be calibrated: a score of 3 is "good but with gaps", not "average"

## Output Format
Return ONLY valid JSON in this exact format (no other text):
{
  "Diagnosis Quality": {"score": N, "rationale": "brief explanation"},
  "Option Breadth": {"score": N, "rationale": "brief explanation"},
  "Decision Justification": {"score": N, "rationale": "brief explanation"},
  "Action Specificity": {"score": N, "rationale": "brief explanation"},
  "Review / Self-Correction": {"score": N, "rationale": "brief explanation"},
  "Overall Trustworthiness": {"score": N, "rationale": "brief explanation"}
}
"""


def _build_scoring_prompt(
    scenario_prompt: str,
    response_text: str,
    expected_pitfalls: list[str],
    gold_standard_elements: list[str],
    discriminators: list[dict[str, str]],
) -> str:
    pitfalls_text = "\n".join(f"- {p}" for p in expected_pitfalls)
    gold_text = "\n".join(f"- {g}" for g in gold_standard_elements)
    disc_text = "\n".join(
        f"- [{d['dimension']}] {d['description']}" for d in discriminators
    )

    return f"""## Scenario Prompt
{scenario_prompt}

## Model Response
{response_text}

## Expected Pitfalls (common mistakes to check for)
{pitfalls_text}

## Gold Standard Elements (what a good response includes)
{gold_text}

## DODAR Discriminators (specific behaviors to look for)
{disc_text}

Now score this response on all 6 dimensions. Return ONLY the JSON."""


def _parse_scores(raw_text: str) -> dict[str, dict]:
    """Parse the JSON scores from the model response, with fallback for malformed JSON."""
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)

    # Try strict parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract the JSON object if surrounded by other text
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # Fix trailing commas before closing braces/brackets
        fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    # Last resort: regex extraction of scores
    result = {}
    for dim in SCORING_DIMENSIONS:
        pattern = re.escape(dim) + r'["\s:]*\{[^}]*?"score"["\s:]*(\d)'
        m = re.search(pattern, text)
        if m:
            result[dim] = {"score": int(m.group(1)), "rationale": "parsed from malformed response"}
    if result:
        return result

    raise ValueError(f"Could not parse scores from response: {text[:200]}...")


async def _call_anthropic(prompt: str, model: str) -> str:
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=2048,
        system=AUTOSCORE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = ""
    for block in response.content:
        if block.type == "text":
            raw += block.text
    return raw


async def _call_openai(prompt: str, model: str) -> str:
    settings = get_settings()
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    use_completion_tokens = any(
        model.startswith(p) for p in ("gpt-5", "o1", "o3", "o4")
    )
    token_param = (
        {"max_completion_tokens": 2048}
        if use_completion_tokens
        else {"max_tokens": 2048}
    )
    response = await client.chat.completions.create(
        model=model,
        **token_param,
        messages=[
            {"role": "system", "content": AUTOSCORE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _is_openai_model(model: str) -> bool:
    return model.startswith(("gpt-", "o1", "o3", "o4"))


async def autoscore_item(
    scenario_id: str,
    response_text: str,
    scenario_prompt: str,
    scorer_model: str | None = None,
) -> list[DimensionScore]:
    """Score a single response using the configured auto-score model."""
    model = scorer_model or _get_autoscore_model()

    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found")

    prompt = _build_scoring_prompt(
        scenario_prompt=scenario.prompt_text,
        response_text=response_text,
        expected_pitfalls=scenario.expected_pitfalls,
        gold_standard_elements=scenario.gold_standard_elements,
        discriminators=[d.model_dump() for d in scenario.discriminators],
    )

    if _is_openai_model(model):
        raw = await _call_openai(prompt, model)
    else:
        raw = await _call_anthropic(prompt, model)

    parsed = _parse_scores(raw)

    scores: list[DimensionScore] = []
    for dim in SCORING_DIMENSIONS:
        entry = parsed.get(dim, {})
        scores.append(
            DimensionScore(
                dimension=dim,
                score=max(1, min(5, int(entry.get("score", 3)))),
                rationale=entry.get("rationale"),
            )
        )

    return scores


async def autoscore_session(
    session: ScoringSession,
    concurrency: int = 3,
    on_progress: callable | None = None,
    cancel_event: asyncio.Event | None = None,
    scorer_model: str | None = None,
) -> ScoringSession:
    """Auto-score all unscored items in a session using Claude Opus 4.6."""
    semaphore = asyncio.Semaphore(concurrency)
    total = len(session.items)
    completed = len(session.scores)

    async def score_one(item_id: str) -> None:
        nonlocal completed

        # Check for cancellation before starting
        if cancel_event and cancel_event.is_set():
            return

        item = next((i for i in session.items if i.item_id == item_id), None)
        if not item:
            completed += 1
            if on_progress:
                on_progress(completed, total)
            return

        # Try versioned run_id first, then fall back to unversioned
        result = load_result(item.run_result_file.replace(".json", ""))
        if not result:
            fallback_id = f"{item.scenario_id}_{item.model}_{item.condition}"
            result = load_result(fallback_id)
        if not result:
            print(f"Warning: no result file for {item.scenario_id}/{item.model}/{item.condition}")
            completed += 1
            if on_progress:
                on_progress(completed, total)
            return

        async with semaphore:
            # Check again after acquiring semaphore (may have waited)
            if cancel_event and cancel_event.is_set():
                return

            try:
                scores = await autoscore_item(
                    scenario_id=item.scenario_id,
                    response_text=result.response_text,
                    scenario_prompt=result.prompt_sent,
                    scorer_model=scorer_model,
                )

                session.scores[item_id] = ScoreCard(
                    item_id=item_id,
                    scores=scores,
                    scored_at=datetime.now(timezone.utc),
                )
                completed += 1

                # Save after each score for resumability
                save_session(session)

                if on_progress:
                    on_progress(completed, total)

            except asyncio.CancelledError:
                print(f"Cancelled scoring {item.scenario_id}/{item.model}/{item.condition}")
                raise
            except Exception as e:
                print(f"Error scoring {item.scenario_id}/{item.model}/{item.condition}: {e}")
                completed += 1
                if on_progress:
                    on_progress(completed, total)

    # Score all unscored items
    unscored = [item_id for item_id in session.order if item_id not in session.scores]
    tasks = [score_one(item_id) for item_id in unscored]
    await asyncio.gather(*tasks, return_exceptions=True)

    return session
