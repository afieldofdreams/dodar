"""Answer extraction and correctness checking for benchmark tasks.

v3 extractor aligned with benchmark_scorer.py v1.0:
  - Takes the LAST match of 'FINAL ANSWER'
  - Handles MC-style answers mislabelled as exact_match: "(B) desc" → "B"
  - Truth-teller/liar pattern for BBH web_of_lies
  - Semantic Yes/No detection for verbose causal judgement answers
  - Markdown stripping before normalisation
  - Handles both "numeric" and "numeric_exact" answer types
"""

from __future__ import annotations

import re

# Lines containing these are review meta-commentary, not answers.
_REVIEW_SKIP_PHRASES = [
    "is complete", "is consistent", "addresses the problem", "meets the",
    "is clear", "no errors found", "review complete", "is correct",
    "confirmed", "no change needed", "no errors",
]


def _is_review_commentary(line: str) -> bool:
    lower = line.lower()
    return any(phrase in lower for phrase in _REVIEW_SKIP_PHRASES)


def extract_answer(response: str, answer_type: str) -> str | None:
    """Extract the model's answer from a response.

    Primary: LAST 'FINAL ANSWER: X' match.
    Fallback: last clearly stated answer based on answer type.
    """
    if not response:
        return None

    # Primary: find ALL 'FINAL ANSWER' matches, take the last one
    matches = re.findall(r"(?i)final\s*answer\s*:?\s*(.+)", response)
    if matches:
        raw = matches[-1].strip().rstrip(".")
        # Strip markdown bold/formatting
        raw = re.sub(r"[\*\#\_\~\`]+", "", raw).strip()
        return _normalise(raw, answer_type)

    # Fallback
    return _fallback_extract(response, answer_type)


def _fallback_extract(response: str, answer_type: str) -> str | None:
    if answer_type == "multiple_choice":
        # "the answer is X" pattern
        answer_is = re.findall(r"(?i)the\s+answer\s+is\s+\(?([A-E])\)?", response)
        if answer_is:
            return answer_is[-1].upper()
        # Last standalone letter on its own line
        mc_matches = re.findall(r"\b([A-E])\b\s*$", response, re.MULTILINE)
        if mc_matches:
            return mc_matches[-1].upper()

    elif answer_type in ("numeric_exact", "numeric"):
        # Last number after '=' or 'is'
        eq_matches = re.findall(r"(?:=|is)\s*\$?([\d,]+(?:\.\d+)?)", response)
        if eq_matches:
            return _normalise_numeric(eq_matches[-1])
        lines = response.strip().split("\n")
        for line in reversed(lines):
            line = line.strip()
            if not line or _is_review_commentary(line):
                continue
            num_matches = re.findall(r"\b(\d[\d,]*(?:\.\d+)?)\b", line)
            if num_matches:
                return _normalise_numeric(num_matches[-1])

    elif answer_type == "exact_match":
        # "the answer is X" pattern
        answer_is = re.findall(r"(?i)the\s+answer\s+is\s+(.+)", response)
        if answer_is:
            return _normalise_exact(answer_is[-1].strip())
        # Last non-review line
        lines = response.strip().split("\n")
        for line in reversed(lines):
            line = line.strip()
            if not line or _is_review_commentary(line):
                continue
            cleaned = re.sub(r"^(?:Answer:|So,?)\s*", "", line, flags=re.IGNORECASE)
            if cleaned:
                return _normalise_exact(cleaned)

    return None


def _normalise(raw: str, answer_type: str) -> str:
    if answer_type == "multiple_choice":
        return _normalise_mc(raw)
    elif answer_type in ("numeric_exact", "numeric"):
        return _normalise_numeric(raw)
    elif answer_type == "exact_match":
        return _normalise_exact(raw)
    return raw.strip()


def _normalise_mc(raw: str) -> str:
    """'A', '(A)', 'Option A', 'A: Throat culture' → 'A'"""
    raw = raw.strip()
    match = re.match(r"^\(?([A-Ea-e])\)?", raw)
    if match:
        return match.group(1).upper()
    match = re.match(r"(?i)option\s+([A-Ea-e])", raw)
    if match:
        return match.group(1).upper()
    m = re.search(r"\b([A-Ea-e])\b", raw)
    if m:
        return m.group(1).upper()
    return raw[:1].upper() if raw else raw


def _normalise_numeric(raw: str) -> str:
    """'$5,600', '5600 dollars' → '5600'"""
    raw = raw.strip()
    raw = re.sub(r"[$£€,\s%]", "", raw)
    raw = re.sub(
        r"(dollars|pounds|euros|cupcakes|hours|tickets|money|lbs?|kg)\b.*",
        "", raw, flags=re.IGNORECASE,
    )
    match = re.search(r"-?[\d.]+", raw.strip())
    if match:
        return match.group(0)
    return raw.strip()


def _normalise_exact(raw: str) -> str:
    """Normalise exact match answers.

    Handles:
      '(E) The robin is second from left' → '(E)' or 'E' depending on context
      'Yes, the red wire caused...' → 'Yes'
      'X tells the truth' → 'Yes' (BBH web_of_lies)
      'X lies' → 'No' (BBH web_of_lies)
      '** (D) blah' → 'D'
      'B' / '(C)' / 'A.' → standalone letter
    """
    # Strip markdown formatting
    raw = re.sub(r"[\*\#\_\~\`]+", "", raw).strip()

    # --- MC-style answers mislabelled as exact_match ---
    # "(B) The bus is the third-newest" → "B"
    mc_match = re.match(r"^\(([A-Ea-e])\)[\s\.]", raw.strip())
    if mc_match:
        return mc_match.group(1).upper()
    # Standalone letter: "B", "(C)", "A."
    if re.match(r"^\(?[A-Ea-e]\)?\.?$", raw.strip()):
        return re.sub(r"[^A-Ea-e]", "", raw.strip()).upper()

    text_lower = raw.lower().strip().rstrip(".")

    # --- Yes/No normalisation (multi-strategy) ---

    # Strategy 0: direct match after stripping non-alpha
    stripped = re.sub(r"[^a-zA-Z]", "", text_lower)
    if stripped in ("yes", "no", "true", "false"):
        return "Yes" if stripped in ("yes", "true") else "No"

    # Strategy 1: first word is yes/no
    first_word = text_lower.split(",")[0].split()[0] if text_lower else ""
    if first_word in ("yes", "no", "true", "false"):
        return "Yes" if first_word in ("yes", "true") else "No"

    # Strategy 1b: truth-teller/liar pattern (BBH web_of_lies)
    if re.search(r"tells the truth", text_lower):
        return "Yes"
    if re.search(r"\blies\b|\bis a liar\b|\bis lying\b", text_lower):
        return "No"

    # Strategy 2: semantic Yes/No for verbose causal answers
    negation_patterns = [
        r"\bdid not\b", r"\bdidn't\b", r"\bnot cause\b", r"\bnot solely\b",
        r"\bwould not\b", r"\bwouldn't\b", r"\bno,?\s", r"\bnot\s+\w+\s+cause",
        r"\bdid not cause\b",
    ]
    affirmation_patterns = [
        r"\bdid cause\b", r"\bcaused\b", r"\bwould say\b.*\bcause",
        r"\byes,?\s", r"\bpartially caused\b",
    ]

    has_negation = any(re.search(p, text_lower) for p in negation_patterns)
    has_affirmation = any(re.search(p, text_lower) for p in affirmation_patterns)

    if has_negation and not has_affirmation:
        return "No"
    if has_negation and has_affirmation:
        if re.search(r"\b(?:did not|didn't|not)\s+(?:\w+\s+)?cause\b", text_lower):
            return "No"
        return "Yes"
    if has_affirmation and not has_negation:
        return "Yes"

    # Strategy 3: strip trailing explanation
    core = re.split(r"[,;]", raw)[0].strip().rstrip(".")
    return core


def check_correctness(
    extracted: str | None,
    correct_answer: str,
    answer_type: str,
) -> bool:
    """Check if an extracted answer matches the correct answer."""
    if extracted is None:
        return False

    correct = correct_answer.strip()

    if answer_type == "multiple_choice":
        # Strip parens from both: "(A)" → "A"
        e = re.sub(r"[^A-Ea-e]", "", extracted).upper()
        c = re.sub(r"[^A-Ea-e]", "", correct).upper()
        return e == c

    elif answer_type in ("numeric_exact", "numeric"):
        try:
            extracted_num = float(extracted.replace(",", ""))
            correct_num = float(correct.replace(",", ""))
            if correct_num == 0:
                return abs(extracted_num) < 0.01
            return abs(extracted_num - correct_num) / abs(correct_num) <= 0.005
        except (ValueError, ZeroDivisionError):
            return extracted.strip() == correct

    elif answer_type == "exact_match":
        return extracted.lower().strip() == correct.lower().strip()

    return extracted.strip() == correct


# --- Re-scoring utility ---

def rescore_result(result: dict) -> dict:
    """Re-score a single result dict with the current extractor.

    Adds fields: extracted_answer_v2, is_correct_v2,
    extraction_changed, correctness_changed.
    """
    raw = result.get("raw_response", "")
    answer_type = result.get("answer_type", "exact_match")
    if answer_type == "numeric":
        answer_type = "numeric_exact"
    correct = result.get("correct_answer", "")

    extracted = extract_answer(raw, answer_type)
    is_correct = check_correctness(extracted, correct, answer_type)

    result["extracted_answer_v2"] = extracted
    result["is_correct_v2"] = is_correct
    result["extraction_changed"] = extracted != result.get("extracted_answer")
    result["correctness_changed"] = is_correct != result.get("is_correct")

    return result
