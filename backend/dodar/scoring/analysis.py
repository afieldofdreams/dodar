"""Statistical analysis for benchmark results per protocol v5 FINAL.

Three layers:
  1. Accuracy comparison + extraction recovery
  2. McNemar's paired tests (Part I hypotheses H1-H4)
  3. Task-level analysis (contestability, paired outcomes)
  4. Token efficiency (cost per correct answer)
  5. Error distribution chi-squared test (Part II hypotheses H3/H5)
"""

from __future__ import annotations

from collections import Counter, defaultdict

from dodar.models.benchmark import BenchmarkResult, CONDITION_NAMES


def mcnemar_test(results: list[BenchmarkResult], cond_a: str, cond_b: str) -> dict:
    """McNemar's exact test for paired comparison on the same tasks."""
    by_task: dict[str, dict[str, bool]] = defaultdict(dict)
    for r in results:
        if r.condition in (cond_a, cond_b):
            by_task[r.task_id][r.condition] = bool(r.is_correct)

    rr, rw, wr, ww = 0, 0, 0, 0
    for scores in by_task.values():
        if cond_a in scores and cond_b in scores:
            a, b = scores[cond_a], scores[cond_b]
            if a and b: rr += 1
            elif a and not b: rw += 1
            elif not a and b: wr += 1
            else: ww += 1

    n_total = rr + rw + wr + ww
    n_discordant = rw + wr

    p_value = None
    if n_discordant > 0:
        try:
            from scipy.stats import binomtest
            result = binomtest(rw, rw + wr, 0.5)
            p_value = round(float(result.pvalue), 6)
        except (ImportError, AttributeError):
            try:
                from scipy.stats import binom_test
                p_value = round(float(binom_test(rw, rw + wr, 0.5)), 6)
            except ImportError:
                # Chi-squared approximation
                if rw + wr > 0:
                    stat = (abs(rw - wr) - 1) ** 2 / (rw + wr)
                    p_value = round(float(stat), 4)  # approximate

    return {
        "condition_a": cond_a,
        "condition_a_name": CONDITION_NAMES.get(cond_a, cond_a),
        "condition_b": cond_b,
        "condition_b_name": CONDITION_NAMES.get(cond_b, cond_b),
        "n_tasks_paired": n_total,
        "both_correct": rr,
        "a_only_correct": rw,
        "b_only_correct": wr,
        "both_wrong": ww,
        "n_discordant": n_discordant,
        "p_value": p_value,
        "significant_at_05": bool(p_value < 0.05) if isinstance(p_value, (int, float)) else None,
    }


def run_protocol_tests(results: list[BenchmarkResult]) -> dict:
    """Run all pre-registered McNemar's tests from the protocol."""
    conditions = set(r.condition for r in results)

    key_pairs = [
        ("C", "B", "H1: PGR vs Zero-Shot CoT (token-matched)"),
        ("C", "G", "H2: PGR vs Few-Shot CoT (information density)"),
        ("C", "F", "H4: PGR vs Shuffled PGR (sequence test)"),
        ("C", "A", "PGR vs Baseline"),
        ("C", "D", "PGR vs ReAct"),
        ("C", "E", "PGR vs Step-Back"),
        ("C", "C_previous", "Late vs Early Commitment PGR"),
        ("C", "H", "H_anchoring: PGR vs Anti-Anchoring PGR"),
        ("H", "B", "Anti-Anchoring PGR vs Zero-Shot CoT"),
        ("A", "B", "CoT lift: Baseline vs Zero-Shot CoT"),
    ]

    tests = {}
    for ca, cb, label in key_pairs:
        if ca in conditions and cb in conditions:
            test = mcnemar_test(results, ca, cb)
            test["hypothesis"] = label
            tests[f"{ca}_vs_{cb}"] = test

    return tests


def task_level_analysis(results: list[BenchmarkResult]) -> dict:
    """Per-task breakdown: which tasks differentiate between conditions."""
    by_task: dict[str, list[BenchmarkResult]] = defaultdict(list)
    for r in results:
        by_task[r.task_id].append(r)

    tasks = {}
    for task_id, task_results in sorted(by_task.items()):
        correct_count = sum(1 for r in task_results if r.is_correct)
        total_count = len(task_results)
        tasks[task_id] = {
            "correct": correct_count,
            "total": total_count,
            "accuracy": round(100 * correct_count / max(total_count, 1), 1),
            "category": (
                "trivial" if correct_count == total_count else
                "impossible" if correct_count == 0 else
                "contestable"
            ),
            "source": task_results[0].source,
            "conditions_correct": sorted(set(
                r.condition for r in task_results if r.is_correct
            )),
            "conditions_wrong": sorted(set(
                r.condition for r in task_results if not r.is_correct
            )),
        }

    trivial = sum(1 for t in tasks.values() if t["category"] == "trivial")
    impossible = sum(1 for t in tasks.values() if t["category"] == "impossible")
    contestable = sum(1 for t in tasks.values() if t["category"] == "contestable")

    return {
        "tasks": tasks,
        "contestability": {
            "trivial": trivial,
            "contestable": contestable,
            "impossible": impossible,
            "total": len(tasks),
        },
    }


def token_efficiency(results: list[BenchmarkResult]) -> dict:
    """Cost per correct answer, avg tokens, avg latency per condition."""
    by_condition: dict[str, list[BenchmarkResult]] = defaultdict(list)
    for r in results:
        by_condition[r.condition].append(r)

    efficiency = {}
    for cond in sorted(by_condition):
        cond_results = by_condition[cond]
        total_cost = sum(r.cost_usd for r in cond_results)
        correct_count = sum(1 for r in cond_results if r.is_correct)
        total_tokens = sum(r.output_tokens for r in cond_results)
        total_latency = sum(r.latency_seconds for r in cond_results)
        n = len(cond_results)

        efficiency[cond] = {
            "condition_name": CONDITION_NAMES.get(cond, cond),
            "total_cost_usd": round(total_cost, 6),
            "correct_answers": correct_count,
            "total_answers": n,
            "accuracy_pct": round(100 * correct_count / max(n, 1), 1),
            "cost_per_correct": round(total_cost / max(correct_count, 1), 6),
            "cost_per_query": round(total_cost / max(n, 1), 6),
            "avg_output_tokens": round(total_tokens / max(n, 1)),
            "avg_latency_s": round(total_latency / max(n, 1), 2),
        }

    return efficiency


def error_distribution_chi_squared(
    classifications: list[dict],
) -> dict:
    """Chi-squared test on error type distribution across conditions.

    Tests H3/H5: whether error type distribution differs across conditions.
    """
    ERROR_CATS = [
        "PREMATURE_CLOSURE", "ANCHORING_ERROR", "INCOMPLETE_SEARCH",
        "FAILURE_TO_REVISE", "EXECUTION_ERROR", "COMPREHENSION_FAILURE",
        "ABSTENTION",
    ]

    by_condition: dict[str, Counter] = defaultdict(Counter)
    for c in classifications:
        cond = c.get("condition", "?")
        cat = c.get("classification", "UNCLASSIFIED")
        by_condition[cond][cat] += 1

    conditions = sorted(by_condition)
    if len(conditions) < 2:
        return {"error": "Need at least 2 conditions with classified errors"}

    observed = {
        cond: {cat: by_condition[cond].get(cat, 0) for cat in ERROR_CATS}
        for cond in conditions
    }

    try:
        from scipy.stats import chi2_contingency
        import numpy as np

        table = [[observed[cond][cat] for cat in ERROR_CATS] for cond in conditions]
        table = np.array(table)

        # Remove zero columns
        nonzero = table.sum(axis=0) > 0
        table = table[:, nonzero]
        active_cats = [c for c, nz in zip(ERROR_CATS, nonzero) if nz]

        if table.shape[1] < 2:
            return {"error": "Not enough error categories with observations", "observed": observed}

        chi2, p, dof, expected = chi2_contingency(table)

        return {
            "conditions": conditions,
            "categories_tested": active_cats,
            "observed": observed,
            "chi2": round(float(chi2), 4),
            "p_value": round(float(p), 6),
            "degrees_of_freedom": int(dof),
            "significant_at_05": bool(p < 0.05),
            "note": "Tests H3/H5: whether error type distribution differs across conditions",
        }
    except ImportError:
        return {
            "observed": observed,
            "error": "scipy required for chi-squared test",
        }


def full_analysis(
    results: list[BenchmarkResult],
    error_classifications: list[dict] | None = None,
) -> dict:
    """Run the complete protocol analysis pipeline."""
    conditions = sorted(set(r.condition for r in results))

    # Accuracy by condition
    accuracy: dict[str, dict] = {}
    for cond in conditions:
        cond_results = [r for r in results if r.condition == cond]
        correct = sum(1 for r in cond_results if r.is_correct)
        total = len(cond_results)
        accuracy[cond] = {
            "name": CONDITION_NAMES.get(cond, cond),
            "correct": correct,
            "total": total,
            "accuracy_pct": round(100 * correct / max(total, 1), 1),
        }

    output = {
        "summary": {
            "total_results": len(results),
            "total_tasks": len(set(r.task_id for r in results)),
            "total_conditions": len(conditions),
            "conditions": conditions,
        },
        "accuracy_by_condition": accuracy,
        "mcnemar_paired_tests": run_protocol_tests(results),
        "token_efficiency": token_efficiency(results),
        "task_level_analysis": task_level_analysis(results),
    }

    if error_classifications:
        output["error_distribution_test"] = error_distribution_chi_squared(
            error_classifications
        )

    return output
