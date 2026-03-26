#!/usr/bin/env python3
"""
blind_responses.py - FINAL VERSION
Strips condition markers, randomises order, assigns anonymous IDs.
Usage: python blind_responses.py --input outputs/ --tasks benchmark-tasks-100.json --output blinded.csv
"""
import json, csv, random, re, os, argparse
from pathlib import Path
from collections import Counter

def strip_condition_markers(response):
    response = re.sub(r'\b\d+\.\s*(DIAGNOSE|OPTIONS|DECIDE|ACTION|REVIEW)\s*:', '---', response, flags=re.IGNORECASE)
    response = re.sub(r'\b(DIAGNOSE|OPTIONS|DECIDE|ACTION|REVIEW)\s*:', '---', response, flags=re.IGNORECASE)
    response = re.sub(r'\b(Thought|Action|Observation)\s*\d*\s*:', '---', response, flags=re.IGNORECASE)
    response = re.sub(r'\b(STEP\s*BACK|Step\s*1|Step\s*2)\s*[-:]', '---', response, flags=re.IGNORECASE)
    response = re.sub(r'\b(Phase|Step)\s+\d+\s*[-:]', '---', response, flags=re.IGNORECASE)
    response = re.sub(r'(---\s*){2,}', '---\n', response)
    response = re.sub(r'^\s*---\s*\n?', '', response)
    return response.strip()

def extract_incorrect_responses(input_dir, tasks_file):
    with open(tasks_file) as f:
        tasks_by_id = {t["id"]: t for t in json.load(f)["tasks"]}
    incorrect, total = [], 0
    for fp in sorted(Path(input_dir).rglob("*.json")):
        try:
            with open(fp) as f:
                result = json.load(f)
            results = result if isinstance(result, list) else [result]
            for r in results:
                total += 1
                if not r.get("is_correct", True):
                    task = tasks_by_id.get(r.get("task_id", ""), {})
                    q = task.get("question", r.get("question", "NOT FOUND"))
                    if task.get("options"):
                        q += "\n\nOptions:\n" + "\n".join(f"  {k}: {v}" for k,v in task["options"].items())
                    incorrect.append({"task_id": r.get("task_id","?"), "condition": r.get("condition","?"),
                        "model_id": r.get("model_id","?"), "run_number": r.get("run_number",1),
                        "raw_response": r.get("raw_response",""), "extracted_answer": r.get("extracted_answer",""),
                        "correct_answer": r.get("correct_answer", task.get("correct_answer","")),
                        "correct_answer_text": task.get("correct_answer_text",""),
                        "question": q, "source": task.get("source","?")})
        except Exception as e:
            print(f"  Skip {fp}: {e}")
    print(f"  Total: {total}, Incorrect: {len(incorrect)} ({len(incorrect)/max(total,1)*100:.0f}%)")
    return incorrect

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--tasks", default="benchmark-tasks-100.json")
    ap.add_argument("--output", default="blinded_responses.csv")
    ap.add_argument("--key", default="blind_key.json")
    ap.add_argument("--sample", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)
    print(f"Loading from {args.input}...")
    incorrect = extract_incorrect_responses(args.input, args.tasks)
    if not incorrect: print("No errors found."); return
    conds = Counter(r["condition"] for r in incorrect)
    print(f"\n  By condition: {dict(sorted(conds.items()))}")
    n = max(1, int(len(incorrect) * args.sample))
    sampled = random.sample(incorrect, min(n, len(incorrect)))
    random.shuffle(sampled)
    blinded, key = [], []
    warns = 0
    for i, resp in enumerate(sampled):
        bid = f"R-{i+1:04d}"
        stripped = strip_condition_markers(resp["raw_response"])
        sects = stripped.count('---')
        if sects >= 4: warns += 1
        ca = f"{resp['correct_answer']} ({resp['correct_answer_text']})" if resp['correct_answer_text'] else resp['correct_answer']
        blinded.append({"blind_id": bid, "question": resp["question"], "correct_answer": ca,
            "model_answer": resp["extracted_answer"], "model_response": stripped,
            "your_classification": "", "your_justification": ""})
        key.append({"blind_id": bid, "task_id": resp["task_id"], "condition": resp["condition"],
            "model_id": resp["model_id"], "run_number": resp["run_number"],
            "source": resp["source"], "structural_sections": sects})
    if warns:
        print(f"\n  WARNING: {warns}/{len(sampled)} responses have 4+ sections (structural signature visible)")
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["blind_id","question","correct_answer","model_answer","model_response","your_classification","your_justification"])
        w.writeheader(); w.writerows(blinded)
    with open(args.key, "w") as f:
        json.dump({"WARNING": "DO NOT OPEN until classification complete", "seed": args.seed,
            "sample_pct": args.sample, "total_incorrect": len(incorrect),
            "total_sampled": len(blinded), "key": key}, f, indent=2)
    hrs = len(blinded) * 2.5 / 60
    print(f"\n  Output: {args.output} ({len(blinded)} responses, ~{hrs:.1f} hours)")
    print(f"  Key: {args.key} (DO NOT OPEN)")
    print(f"\n  Categories: premature_closure | anchoring_error | incomplete_search")
    print(f"              failure_to_revise | execution_error | comprehension_failure | abstention")

if __name__ == "__main__": main()
