#!/usr/bin/env python3
"""
Benchmark task generator — pulls from published datasets via HuggingFace.

Produces benchmark-tasks-100.json with full provenance tracking.
Requires: datasets (pip install datasets)

Usage:
  python scripts/generate_tasks.py
  python scripts/generate_tasks.py --output benchmark-tasks-v3.json
"""

import json
import random
import re
import argparse
from typing import Any, Dict, List, Optional

from datasets import load_dataset

SEED = 42
random.seed(SEED)


# ----------------------------
# Helpers
# ----------------------------

def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def clean_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def option_letter(idx: int) -> str:
    return ["A", "B", "C", "D", "E", "F"][idx]


def normalise_mc_answer(answer: Any) -> str:
    if isinstance(answer, int):
        return option_letter(answer)

    s = clean_text(answer).upper()

    if s in {"A", "B", "C", "D", "E", "F"}:
        return s

    m = re.match(r"^\(?([A-F])\)?$", s)
    if m:
        return m.group(1)

    if s in {"0", "1", "2", "3", "4", "5"}:
        return option_letter(int(s))

    raise ValueError(f"Could not normalise MC answer {answer!r}")


def extract_last_number(text: str) -> str:
    text = clean_text(text)

    m = re.search(r"####\s*([-+]?\d[\d,]*(?:\.\d+)?)", text)
    if m:
        return m.group(1).replace(",", "")

    matches = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
    if matches:
        return matches[-1].replace(",", "")

    raise ValueError(f"Could not extract numeric answer from {text!r}")


def normalise_exact_match_answer(answer: Any) -> str:
    s = clean_text(answer)

    if s.lower() == "yes":
        return "Yes"
    if s.lower() == "no":
        return "No"

    s = re.sub(r"^\s*['\"(]+", "", s)
    s = re.sub(r"['\")]+\s*$", "", s)
    return s.strip()


def infer_reasoning_steps_gsm8k(question: str) -> int:
    q = question.lower()
    triggers = [
        "then", "after", "before", "remaining", "left", "each", "every",
        "total", "altogether", "twice", "half", "percent", "more than",
        "less than", "per", "in all", "how many", "how much"
    ]
    return sum(1 for t in triggers if t in q)


def build_task(
    *,
    task_id: str,
    question: str,
    correct_answer: str,
    answer_type: str,
    source: str,
    options: Optional[List[str]] = None,
    option_labels: Optional[List[str]] = None,
    dataset_name: str,
    dataset_config: str,
    dataset_split: str,
    dataset_index: int,
    selection_notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    task: Dict[str, Any] = {
        "id": task_id,
        "question": clean_text(question),
        "correct_answer": correct_answer,
        "answer_type": answer_type,
        "source": source,
        "provenance": {
            "dataset_name": dataset_name,
            "dataset_config": dataset_config,
            "dataset_split": dataset_split,
            "dataset_index": dataset_index,
        },
    }

    if options is not None:
        task["options"] = [clean_text(x) for x in options]

    if option_labels is not None:
        task["option_labels"] = [clean_text(x) for x in option_labels]

    if selection_notes:
        task["selection_notes"] = selection_notes

    # Scorer hints
    if answer_type == "multiple_choice":
        task["scoring"] = {
            "match_type": "letter_exact",
            "normalisation": "uppercase_letter",
        }
    elif answer_type == "numeric":
        task["scoring"] = {
            "match_type": "numeric_tolerance",
            "tolerance_relative": 0.005,
        }
    elif answer_type == "exact_match":
        task["scoring"] = {
            "match_type": "case_insensitive_exact",
        }

    return task


# ----------------------------
# Source loaders
# ----------------------------

def load_medqa_20() -> List[Dict[str, Any]]:
    ds_name = "GBaker/MedQA-USMLE-4-options"
    ds = load_dataset(ds_name, split="test")

    pool = []
    for i, row in enumerate(ds):
        question = clean_text(row.get("question"))
        if word_count(question) <= 80:
            continue

        options = None
        option_labels = None
        if "options" in row:
            opts = row["options"]
            if isinstance(opts, dict):
                # MedQA format: {"A": "text", "B": "text", ...}
                option_labels = sorted(opts.keys())
                options = [opts[k] for k in option_labels]
            elif isinstance(opts, list):
                options = opts
        elif "choices" in row:
            ch = row["choices"]
            if isinstance(ch, dict) and "text" in ch:
                options = ch["text"]
            elif isinstance(ch, list):
                options = ch
        else:
            endings = [row[k] for k in ["ending0", "ending1", "ending2", "ending3"] if k in row]
            if endings:
                options = endings

        if not options or len(options) != 4:
            continue

        if option_labels is None:
            option_labels = ["A", "B", "C", "D"]

        answer_raw = row.get("answer_idx", row.get("label", row.get("answer")))
        correct_answer = normalise_mc_answer(answer_raw)

        pool.append(
            build_task(
                task_id="",
                question=question,
                correct_answer=correct_answer,
                answer_type="multiple_choice",
                source="MedQA-USMLE",
                options=options,
                option_labels=option_labels,
                dataset_name=ds_name,
                dataset_config="default",
                dataset_split="test",
                dataset_index=i,
                selection_notes=["clinical vignette >80 words", "4 options"],
            )
        )

    random.Random(SEED).shuffle(pool)
    return pool[:20]


def load_mmlu_professional_20() -> List[Dict[str, Any]]:
    specs = [
        ("professional_medicine", 7),
        ("professional_law", 7),
        ("professional_accounting", 6),
    ]

    out = []
    rng = random.Random(SEED)

    for subject, n in specs:
        ds = load_dataset("cais/mmlu", subject, split="test")
        pool = []
        for i, row in enumerate(ds):
            question = clean_text(row["question"])
            choices = [clean_text(x) for x in row["choices"]]
            if len(choices) != 4:
                continue

            correct_answer = normalise_mc_answer(row["answer"])

            pool.append(
                build_task(
                    task_id="",
                    question=question,
                    correct_answer=correct_answer,
                    answer_type="multiple_choice",
                    source=f"MMLU/{subject}",
                    options=choices,
                    option_labels=["A", "B", "C", "D"],
                    dataset_name="cais/mmlu",
                    dataset_config=subject,
                    dataset_split="test",
                    dataset_index=i,
                    selection_notes=["protocol professional subject"],
                )
            )
        rng.shuffle(pool)
        out.extend(pool[:n])

    return out


def load_gsm8k_20() -> List[Dict[str, Any]]:
    ds_name = "openai/gsm8k"
    ds = load_dataset(ds_name, "main", split="test")

    pool = []
    for i, row in enumerate(ds):
        question = clean_text(row["question"])
        if infer_reasoning_steps_gsm8k(question) < 4:
            continue

        correct_answer = extract_last_number(row["answer"])

        pool.append(
            build_task(
                task_id="",
                question=question,
                correct_answer=correct_answer,
                answer_type="numeric",
                source="GSM8K",
                dataset_name=ds_name,
                dataset_config="main",
                dataset_split="test",
                dataset_index=i,
                selection_notes=["estimated 4+ reasoning steps"],
            )
        )

    random.Random(SEED).shuffle(pool)
    return pool[:20]


def load_bbh_20() -> List[Dict[str, Any]]:
    # lukaemon/bbh uses full subject names for five-object variants
    specs = [
        ("causal_judgement", "BBH/causal_judgement", 5),
        ("logical_deduction_five_objects", "BBH/logical_deduction", 5),
        ("tracking_shuffled_objects_five_objects", "BBH/tracking_shuffled_objects", 5),
        ("web_of_lies", "BBH/web_of_lies", 5),
    ]

    out = []
    rng = random.Random(SEED)

    for hf_config, source_label, n in specs:
        ds = load_dataset("lukaemon/bbh", hf_config, split="test")
        pool = []
        for i, row in enumerate(ds):
            question = clean_text(row.get("input"))
            if not question:
                continue

            target = row.get("target")
            if isinstance(target, list):
                target = target[0]

            correct_answer = normalise_exact_match_answer(target)

            pool.append(
                build_task(
                    task_id="",
                    question=question,
                    correct_answer=correct_answer,
                    answer_type="exact_match",
                    source=source_label,
                    dataset_name="lukaemon/bbh",
                    dataset_config=hf_config,
                    dataset_split="test",
                    dataset_index=i,
                    selection_notes=["official BBH item"],
                )
            )

        rng.shuffle(pool)
        out.extend(pool[:n])

    return out


def load_arc_20() -> List[Dict[str, Any]]:
    ds_name = "allenai/ai2_arc"
    ds = load_dataset(ds_name, "ARC-Challenge", split="test")

    pool = []
    for i, row in enumerate(ds):
        question = clean_text(row["question"])
        choices = row["choices"]["text"]
        labels = row["choices"]["label"]
        answer = clean_text(row["answerKey"]).upper()

        if len(choices) != 4:
            continue
        if word_count(question) < 12:
            continue

        correct_answer = normalise_mc_answer(answer)

        pool.append(
            build_task(
                task_id="",
                question=question,
                correct_answer=correct_answer,
                answer_type="multiple_choice",
                source="ARC-Challenge",
                options=choices,
                option_labels=labels,
                dataset_name=ds_name,
                dataset_config="ARC-Challenge",
                dataset_split="test",
                dataset_index=i,
                selection_notes=["4-option challenge item", "prefer multi-hop"],
            )
        )

    random.Random(SEED).shuffle(pool)
    return pool[:20]


# ----------------------------
# Assembly
# ----------------------------

def assign_ids(tasks: List[Dict[str, Any]]) -> None:
    counters: Dict[str, int] = {}
    prefixes = {
        "MedQA-USMLE": "MED",
        "MMLU/professional_medicine": "MMLU-MED",
        "MMLU/professional_law": "MMLU-LAW",
        "MMLU/professional_accounting": "MMLU-ACC",
        "GSM8K": "GSM",
        "BBH/causal_judgement": "BBH-CJ",
        "BBH/logical_deduction": "BBH-LD",
        "BBH/tracking_shuffled_objects": "BBH-TSO",
        "BBH/web_of_lies": "BBH-WL",
        "ARC-Challenge": "ARC",
    }

    for task in tasks:
        src = task["source"]
        counters[src] = counters.get(src, 0) + 1
        task["id"] = f"{prefixes[src]}-{counters[src]:03d}"


def validate(tasks: List[Dict[str, Any]]) -> None:
    assert len(tasks) == 100, f"Expected 100, got {len(tasks)}"

    seen = set()
    for t in tasks:
        assert t["id"] and t["id"] not in seen, f"ID issue: {t.get('id')}"
        seen.add(t["id"])
        assert t["question"], f"Missing question: {t['id']}"
        assert t["correct_answer"] != "", f"Missing answer: {t['id']}"
        assert t["answer_type"] in {"multiple_choice", "numeric", "exact_match"}

        if t["answer_type"] == "multiple_choice":
            assert "options" in t and len(t["options"]) == 4, f"MC needs 4 options: {t['id']}"
            assert t["correct_answer"] in {"A", "B", "C", "D"}, f"MC answer not normalised: {t['id']}"
        elif t["answer_type"] == "numeric":
            float(str(t["correct_answer"]).replace(",", ""))

    print(f"Validation passed: {len(tasks)} tasks, {len(seen)} unique IDs")


def build_all(output_path: str = "benchmark-tasks-v3.json") -> None:
    tasks = []
    tasks.extend(load_medqa_20())
    tasks.extend(load_mmlu_professional_20())
    tasks.extend(load_gsm8k_20())
    tasks.extend(load_bbh_20())
    tasks.extend(load_arc_20())

    assign_ids(tasks)
    validate(tasks)

    # Build metadata
    by_source: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    for t in tasks:
        by_source[t["source"]] = by_source.get(t["source"], 0) + 1
        by_type[t["answer_type"]] = by_type.get(t["answer_type"], 0) + 1

    output = {
        "metadata": {
            "version": "v3-protocol-faithful",
            "seed": SEED,
            "total_tasks": len(tasks),
            "generated_by": "scripts/generate_tasks.py",
            "sources": by_source,
            "answer_types": by_type,
            "selection_policy": {
                "MedQA-USMLE": "20 test items, clinical vignette >80 words, 4 options",
                "MMLU-Professional": "20 test items: 7 medicine, 7 law, 6 accounting",
                "GSM8K": "20 test items, heuristic 4+ reasoning-step filter",
                "BIG-Bench-Hard": "20 items: 5 causal_judgement, 5 logical_deduction, 5 tracking_shuffled_objects, 5 web_of_lies",
                "ARC-Challenge": "20 test items, 4 options, challenge subset",
            },
        },
        "tasks": tasks,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Wrote {output_path} with {len(tasks)} tasks")
    print(f"  Sources: {by_source}")
    print(f"  Types: {by_type}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate benchmark tasks from published datasets")
    parser.add_argument("--output", "-o", default="benchmark-tasks-v3.json", help="Output path")
    args = parser.parse_args()
    build_all(args.output)
