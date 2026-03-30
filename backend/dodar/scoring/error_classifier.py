"""Dual-LLM error classification for incorrect benchmark responses.

Uses both Claude and GPT to classify each incorrect response into one of
seven error categories, as specified in the protocol. Responses are blinded
(condition labels stripped) before classification.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime, timezone

from dodar.config import get_settings
from dodar.models.benchmark import BenchmarkResult, ErrorCategory, ErrorClassification
from dodar.runners.registry import get_runner


# System prompt from the protocol
SCORER_SYSTEM_PROMPT = (
    "You are an expert in cognitive error analysis. You will be shown a question, "
    "the correct answer, and an incorrect response from an AI model. You do not know "
    "which prompting method produced this response.\n\n"
    "Your task is to classify the PRIMARY reasoning failure that caused the incorrect "
    "answer. Choose exactly ONE category from the list below. If multiple failures are "
    "present, identify the one that occurred earliest in the reasoning chain (the root "
    "cause).\n\n"
    "IMPORTANT: You must respond with ONLY a JSON object. No other text."
)

SCORER_USER_TEMPLATE = """QUESTION:
{question}

CORRECT ANSWER:
{correct_answer}

MODEL'S ANSWER:
{model_answer}

MODEL'S REASONING:
{model_response}

---

Classify the primary reasoning failure into exactly ONE of these categories:

1. PREMATURE_CLOSURE: The model committed to an answer before adequately exploring the problem space or identifying all relevant constraints. It locked onto an early interpretation without considering alternatives.

2. ANCHORING_ERROR: The model fixated on one piece of information (often a salient but misleading detail) and failed to adjust its reasoning despite contradictory evidence appearing later in its own output.

3. INCOMPLETE_SEARCH: The model considered too few options or approaches before selecting an answer. It tried one path and committed without exploring alternatives that would have revealed the correct answer.

4. FAILURE_TO_REVISE: The model identified an error, inconsistency, or uncertainty during its reasoning but did not correct the final answer. It noticed something was wrong but proceeded anyway.

5. EXECUTION_ERROR: The model reasoned correctly to the right approach but made a mechanical error in implementation (arithmetic mistake, logic error, transcription error, misread option letter).

6. COMPREHENSION_FAILURE: The model fundamentally misunderstood what was being asked. It answered a different question than the one posed, or could not parse the problem structure.

7. ABSTENTION: The model declined to answer, stated it could not determine the answer, or produced no clear final answer.

Respond with a JSON object:
{{
  "classification": "ONE_OF_THE_SEVEN_CATEGORIES",
  "reasoning": "2-3 sentences explaining why this classification applies and why the most plausible alternative classification does not.",
  "root_cause_quote": "Quote the specific sentence or phrase in the model's reasoning where the failure first manifests. If abstention, write 'N/A'.",
  "confidence": "high|medium|low"
}}"""


def _strip_condition_markers(response: str) -> str:
    """Strip phase labels and condition markers for blinding."""
    response = re.sub(
        r"\b\d+\.\s*(DIAGNOSE|OPTIONS|DECIDE|ACTION|REVIEW)\s*:",
        "---", response, flags=re.IGNORECASE,
    )
    response = re.sub(
        r"\b(DIAGNOSE|OPTIONS|DECIDE|ACTION|REVIEW)\s*:",
        "---", response, flags=re.IGNORECASE,
    )
    response = re.sub(
        r"\b(Thought|Action|Observation)\s*\d*\s*:",
        "---", response, flags=re.IGNORECASE,
    )
    response = re.sub(
        r"\b(STEP\s*BACK|Step\s*1|Step\s*2)\s*[-:]",
        "---", response, flags=re.IGNORECASE,
    )
    response = re.sub(
        r"\b(Phase|Step)\s+\d+\s*[-:]",
        "---", response, flags=re.IGNORECASE,
    )
    response = re.sub(r"(---\s*){2,}", "---\n", response)
    return response.strip()


def _build_scorer_prompt(result: BenchmarkResult) -> str:
    """Build the blinded scorer prompt for a single incorrect result."""
    blinded_response = _strip_condition_markers(result.raw_response)

    correct_text = result.correct_answer
    question = result.question or "Question not available"

    return SCORER_USER_TEMPLATE.format(
        question=question,
        correct_answer=correct_text,
        model_answer=result.extracted_answer or "No answer extracted",
        model_response=blinded_response,
    )


def _parse_classification(text: str) -> dict:
    """Parse the JSON classification from a scorer response."""
    # Try to find JSON in the response
    # Sometimes models wrap it in markdown code blocks
    json_match = re.search(r"\{[^}]*\"classification\"[^}]*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Try the whole response as JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Fallback: extract classification from text
    for cat in ErrorCategory:
        if cat.value in text.upper():
            return {
                "classification": cat.value,
                "reasoning": "Extracted from non-JSON response",
                "root_cause_quote": "N/A",
                "confidence": "low",
            }

    return {
        "classification": "COMPREHENSION_FAILURE",
        "reasoning": "Could not parse scorer response",
        "root_cause_quote": "N/A",
        "confidence": "low",
    }


async def classify_single_error(
    result: BenchmarkResult,
    scorer_model: str,
) -> ErrorClassification:
    """Classify a single incorrect response using one scorer model."""
    runner = get_runner(scorer_model)
    prompt = _build_scorer_prompt(result)
    response = await runner.run(prompt, system_prompt=SCORER_SYSTEM_PROMPT)

    parsed = _parse_classification(response.text)

    # Validate classification
    try:
        category = ErrorCategory(parsed["classification"])
    except (ValueError, KeyError):
        category = ErrorCategory.COMPREHENSION_FAILURE

    return ErrorClassification(
        task_id=result.task_id,
        condition=result.condition,
        model_id=result.model_id,
        run_number=result.run_number,
        classification=category,
        reasoning=parsed.get("reasoning", ""),
        root_cause_quote=parsed.get("root_cause_quote"),
        confidence=parsed.get("confidence", "medium"),
        rater=scorer_model,
    )


async def classify_errors_dual(
    results: list[BenchmarkResult],
    scorer_a: str = "claude-opus-4-6",
    scorer_b: str = "gpt-5.4",
    concurrency: int = 3,
) -> list[ErrorClassification]:
    """Classify all incorrect results using two scorer models.

    Returns classifications from both scorers for each result.
    """
    incorrect = [r for r in results if not r.is_correct]
    if not incorrect:
        return []

    semaphore = asyncio.Semaphore(concurrency)
    classifications: list[ErrorClassification] = []

    async def classify_one(result: BenchmarkResult, scorer: str) -> ErrorClassification | None:
        async with semaphore:
            try:
                # Rate limiting
                await asyncio.sleep(0.2)
                return await classify_single_error(result, scorer)
            except Exception as e:
                print(f"  Error classifying {result.task_id}/{result.condition} with {scorer}: {e}")
                return None

    # Build all tasks — both scorers for each incorrect result
    tasks = []
    for r in incorrect:
        tasks.append(classify_one(r, scorer_a))
        tasks.append(classify_one(r, scorer_b))

    results_raw = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results_raw:
        if isinstance(result, ErrorClassification):
            classifications.append(result)

    return classifications


def compute_inter_rater_agreement(
    classifications: list[ErrorClassification],
) -> dict:
    """Compute Cohen's kappa between the two scorer models."""
    # Group by (task_id, condition, model_id, run_number)
    from collections import defaultdict

    by_key: dict[tuple, dict[str, str]] = defaultdict(dict)
    for c in classifications:
        key = (c.task_id, c.condition, c.model_id, c.run_number)
        by_key[key][c.rater] = c.classification.value

    # Find pairs where both raters classified
    raters = list({c.rater for c in classifications})
    if len(raters) < 2:
        return {"kappa": None, "exact_agreement": 0, "n_pairs": 0, "raters": raters}

    rater_a, rater_b = sorted(raters)[:2]
    pairs = []
    for key, ratings in by_key.items():
        if rater_a in ratings and rater_b in ratings:
            pairs.append((ratings[rater_a], ratings[rater_b]))

    if not pairs:
        return {"kappa": None, "exact_agreement": 0, "n_pairs": 0, "raters": [rater_a, rater_b]}

    # Exact agreement
    exact = sum(1 for a, b in pairs if a == b)
    pct_agreement = exact / len(pairs)

    # Cohen's kappa
    categories = [c.value for c in ErrorCategory]
    from collections import Counter

    count_a = Counter(a for a, _ in pairs)
    count_b = Counter(b for _, b in pairs)
    n = len(pairs)

    pe = sum(count_a.get(cat, 0) * count_b.get(cat, 0) for cat in categories) / (n * n)
    po = pct_agreement

    if pe == 1.0:
        kappa = 1.0
    else:
        kappa = (po - pe) / (1 - pe)

    return {
        "kappa": round(kappa, 3),
        "exact_agreement": round(pct_agreement, 3),
        "n_pairs": len(pairs),
        "exact_matches": exact,
        "raters": [rater_a, rater_b],
    }
