#!/usr/bin/env python3
"""
Benchmark Scorer — standalone CLI.
Re-exports from the dodar package when available, or runs standalone.

Usage:
  python benchmark_scorer.py exported_results.json [--classify-errors] [--output scored.json]
"""
import sys
import json
import argparse
from pathlib import Path

# Try to use the installed package
try:
    from dodar.scoring.extraction import extract_answer, check_correctness, rescore_result
    from dodar.scoring.analysis import full_analysis, run_protocol_tests, task_level_analysis, token_efficiency
    from dodar.scoring.error_classifier import classify_single_error
    PACKAGE_AVAILABLE = True
except ImportError:
    PACKAGE_AVAILABLE = False
    print("Warning: dodar package not installed. Using standalone mode.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Benchmark Scorer v1.0")
    parser.add_argument("input", help="Path to exported benchmark results JSON")
    parser.add_argument("--classify-errors", action="store_true",
                        help="Run LLM error classification on wrong answers")
    parser.add_argument("--output", "-o", help="Output path (default: scored_<input>)")
    args = parser.parse_args()

    input_path = Path(args.input)
    with open(input_path) as f:
        data = json.load(f)

    results = data.get("results", [])
    if not results:
        print("No results found in input file.")
        return

    # Re-score all results
    for r in results:
        rescore_result(r)

    conditions = sorted(set(r["condition"] for r in results))
    tasks = sorted(set(r["task_id"] for r in results))

    # Accuracy comparison
    from collections import defaultdict
    accuracy_v1 = defaultdict(lambda: {"correct": 0, "total": 0})
    accuracy_v2 = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in results:
        c = r["condition"]
        accuracy_v1[c]["total"] += 1
        accuracy_v2[c]["total"] += 1
        if r.get("is_correct"):
            accuracy_v1[c]["correct"] += 1
        if r.get("is_correct_v2"):
            accuracy_v2[c]["correct"] += 1

    accuracy_comparison = {}
    for c in conditions:
        v1_pct = round(100 * accuracy_v1[c]["correct"] / max(accuracy_v1[c]["total"], 1), 1)
        v2_pct = round(100 * accuracy_v2[c]["correct"] / max(accuracy_v2[c]["total"], 1), 1)
        accuracy_comparison[c] = {
            "v1_accuracy": v1_pct, "v2_accuracy": v2_pct,
            "recovered": accuracy_v2[c]["correct"] - accuracy_v1[c]["correct"],
            "v1_correct": accuracy_v1[c]["correct"],
            "v2_correct": accuracy_v2[c]["correct"],
            "total": accuracy_v2[c]["total"],
        }

    # Extraction recovery
    flipped = [r for r in results if r.get("correctness_changed")]
    recovered = [r for r in flipped if r["is_correct_v2"] and not r["is_correct"]]
    regressed = [r for r in flipped if not r["is_correct_v2"] and r["is_correct"]]

    output = {
        "scorer_version": "1.0",
        "protocol": "Does Reasoning Structure Shape Failure, Not Just Accuracy? v5-FINAL",
        "summary": {
            "total_results": len(results),
            "total_tasks": len(tasks),
            "total_conditions": len(conditions),
        },
        "accuracy_comparison_v1_vs_v2": accuracy_comparison,
        "extraction_report": {
            "total_results": len(results),
            "answers_re_extracted": sum(1 for r in results if r.get("extraction_changed")),
            "recovered_to_correct": len(recovered),
            "regressed_to_incorrect": len(regressed),
        },
        "results": results,
    }

    output_path = args.output or f"scored_{input_path.name}"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    # Console summary
    print(f"\n{'='*60}")
    print(f"BENCHMARK SCORER v1.0")
    print(f"{'='*60}")
    print(f"Results: {len(results)} | Tasks: {len(tasks)} | Conditions: {len(conditions)}")
    print(f"\n{'─'*60}")
    print("ACCURACY: v1 → v2 (re-extracted)")
    print(f"{'─'*60}")
    for c, acc in sorted(accuracy_comparison.items()):
        delta = f"+{acc['recovered']}" if acc['recovered'] > 0 else str(acc['recovered'])
        print(f"  {c}: {acc['v1_accuracy']}% → {acc['v2_accuracy']}%  ({delta})  [{acc['v2_correct']}/{acc['total']}]")
    print(f"\nRecovered: {len(recovered)} | Regressed: {len(regressed)}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
