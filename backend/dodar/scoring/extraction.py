"""Answer extraction and correctness checking for benchmark tasks.

Implements the extraction protocol from experiment-conditions-FINAL.json:
  - Primary: FINAL ANSWER line via regex
  - Fallback: last stated answer
  - Normalisation per answer type
"""

from __future__ import annotations

import re


def extract_answer(response: str, answer_type: str) -> str | None:
    """Extract the model's answer from a response.

    Primary: 'FINAL ANSWER: X' line.
    Fallback: last clearly stated answer based on answer type.

    Returns None if no answer can be extracted (abstention).
    """
    # Primary extraction: FINAL ANSWER line
    match = re.search(r"(?i)final\s*answer\s*:?\s*(.+)", response)
    if match:
        raw = match.group(1).strip()
        return _normalise(raw, answer_type)

    # Fallback extraction
    return _fallback_extract(response, answer_type)


def _fallback_extract(response: str, answer_type: str) -> str | None:
    """Fallback extraction when no FINAL ANSWER line is found."""
    if answer_type == "multiple_choice":
        # Find the last standalone letter [A-E]
        matches = re.findall(r"\b([A-E])\b", response)
        if matches:
            return matches[-1].upper()

    elif answer_type == "numeric_exact":
        # Find the last number after '=' or 'is' or standalone
        # First try after '=' or 'is'
        eq_matches = re.findall(r"(?:=|is)\s*\$?([\d,]+(?:\.\d+)?)", response)
        if eq_matches:
            return _normalise_numeric(eq_matches[-1])
        # Then any standalone number
        num_matches = re.findall(r"\b(\d[\d,]*(?:\.\d+)?)\b", response)
        if num_matches:
            return _normalise_numeric(num_matches[-1])

    elif answer_type == "exact_match":
        # Last sentence or last line with content
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        if lines:
            last = lines[-1]
            # Strip common prefixes
            last = re.sub(r"^(?:The answer is|Answer:|So,?)\s*", "", last, flags=re.IGNORECASE)
            return last.strip().rstrip(".")

    return None


def _normalise(raw: str, answer_type: str) -> str:
    """Normalise an extracted answer based on answer type."""
    if answer_type == "multiple_choice":
        return _normalise_mc(raw)
    elif answer_type == "numeric_exact":
        return _normalise_numeric(raw)
    elif answer_type == "exact_match":
        return _normalise_exact(raw)
    return raw.strip()


def _normalise_mc(raw: str) -> str:
    """Normalise multiple choice answer to single uppercase letter.

    Accepts: 'A', '(A)', 'Option A', 'a', 'A: Throat culture', etc.
    """
    raw = raw.strip()
    # Try to extract a single letter
    match = re.match(r"^\(?([A-Ea-e])\)?", raw)
    if match:
        return match.group(1).upper()
    # Try "Option X"
    match = re.match(r"(?i)option\s+([A-Ea-e])", raw)
    if match:
        return match.group(1).upper()
    # Last resort: first letter if it's A-E
    if raw and raw[0].upper() in "ABCDE":
        return raw[0].upper()
    return raw.strip()


def _normalise_numeric(raw: str) -> str:
    """Normalise numeric answer.

    Strips currency symbols, commas, units, whitespace.
    '5,600' = '5600' = '$5,600'
    """
    raw = raw.strip()
    # Strip currency and common units
    raw = re.sub(r"[$£€]", "", raw)
    raw = re.sub(r"\s*(dollars|pounds|euros|cupcakes|hours|tickets|money|lbs?|kg)\b.*", "", raw, flags=re.IGNORECASE)
    # Strip commas
    raw = raw.replace(",", "")
    # Try to extract a number
    match = re.match(r"([-]?\d+(?:\.\d+)?)", raw.strip())
    if match:
        return match.group(1)
    return raw.strip()


def _normalise_exact(raw: str) -> str:
    """Normalise exact match answer.

    Case-insensitive, strip leading/trailing whitespace and punctuation.
    """
    raw = raw.strip().strip(".")
    # Strip parentheses wrapping like "(E)"
    match = re.match(r"^\(([^)]+)\)$", raw)
    if match:
        raw = match.group(1)
    return raw.strip()


def check_correctness(
    extracted: str | None,
    correct_answer: str,
    answer_type: str,
) -> bool:
    """Check if an extracted answer matches the correct answer.

    Returns False for None (abstention) or incorrect answers.
    """
    if extracted is None:
        return False

    if answer_type == "multiple_choice":
        return extracted.upper() == correct_answer.upper()

    elif answer_type == "numeric_exact":
        try:
            extracted_num = float(extracted.replace(",", ""))
            correct_num = float(correct_answer.replace(",", ""))
            # Within 0.5% rounding tolerance
            if correct_num == 0:
                return extracted_num == 0
            return abs(extracted_num - correct_num) / abs(correct_num) <= 0.005
        except (ValueError, ZeroDivisionError):
            return extracted.strip() == correct_answer.strip()

    elif answer_type == "exact_match":
        # Case-insensitive, strip whitespace and punctuation
        e = extracted.strip().lower().rstrip(".")
        c = correct_answer.strip().lower().rstrip(".")
        # Also handle parenthesised answers like "(E)"
        e = re.sub(r"^\((.+)\)$", r"\1", e)
        c = re.sub(r"^\((.+)\)$", r"\1", c)
        return e == c

    return extracted.strip() == correct_answer.strip()
