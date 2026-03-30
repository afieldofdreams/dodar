import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getExportUrl } from "../api/reports";
import { fetchBenchmarkRuns } from "../api/benchmark";

function getBenchmarkExportUrl(format: "json" | "csv", runId?: string): string {
  let url = `/api/benchmark/export?format=${format}`;
  if (runId) url += `&run_id=${runId}`;
  return url;
}

export default function ExportPage() {
  const [selectedBenchRun, setSelectedBenchRun] = useState<string>("");

  const { data: benchRuns = [] } = useQuery({
    queryKey: ["benchmark-runs-export"],
    queryFn: fetchBenchmarkRuns,
  });

  const completedRuns = benchRuns.filter((r) => r.status === "completed");
  const selectedRun = completedRuns.find((r) => r.run_id === selectedBenchRun);

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold mb-6">Export Data</h1>

      {/* Benchmark export */}
      <div className="bg-surface-2 border border-border rounded-lg p-5 mb-5">
        <h2 className="text-base font-semibold mb-1">Benchmark Results (Phase 2)</h2>
        <p className="text-sm text-zinc-500 mb-4">
          Export benchmark task results with questions, model responses, extracted answers, correctness, tokens, latency, and cost.
        </p>

        {/* Run selector */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-zinc-400 mb-1.5">Select run to export</label>
          <select
            value={selectedBenchRun}
            onChange={(e) => setSelectedBenchRun(e.target.value)}
            className="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-accent"
          >
            <option value="">All results (every run combined)</option>
            {completedRuns.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} — {r.config.stage} — {r.correct_items}/{r.completed_items} correct ({r.config.models.join(", ")}) — {new Date(r.created_at).toLocaleDateString()}
              </option>
            ))}
          </select>
          {selectedRun && (
            <div className="mt-2 text-xs text-zinc-500 bg-surface rounded-md px-3 py-2 space-y-0.5">
              <div>Models: <span className="text-zinc-300">{selectedRun.config.models.join(", ")}</span></div>
              <div>Conditions: <span className="text-zinc-300">{selectedRun.config.conditions.join(", ")}</span></div>
              <div>Results: <span className="text-zinc-300">{selectedRun.completed_items}</span> — Correct: <span className="text-zinc-300">{selectedRun.correct_items}</span> — Cost: <span className="text-zinc-300">${selectedRun.total_cost_usd.toFixed(4)}</span></div>
            </div>
          )}
        </div>

        <div className="flex gap-3 flex-wrap mb-4">
          <a
            href={getBenchmarkExportUrl("csv", selectedBenchRun || undefined)}
            download="dodar_benchmark_results.csv"
            className="inline-block bg-accent text-white px-5 py-2 rounded-lg text-sm font-medium no-underline hover:bg-accent-hover"
          >
            Download CSV
          </a>
          <a
            href={getBenchmarkExportUrl("json", selectedBenchRun || undefined)}
            download="dodar_benchmark_results.json"
            className="inline-block bg-surface-2 text-accent border border-accent px-5 py-2 rounded-lg text-sm font-medium no-underline hover:bg-accent/10"
          >
            Download JSON
          </a>
        </div>

        <details className="text-sm text-zinc-500">
          <summary className="cursor-pointer font-medium text-zinc-300 hover:text-white">
            What's included
          </summary>
          <ul className="mt-2 space-y-1 ml-1">
            <li><strong className="text-zinc-300">Tasks</strong> — task ID, source, question text, correct answer, answer type</li>
            <li><strong className="text-zinc-300">Results</strong> — condition (A-G), model, extracted answer, is_correct, raw response</li>
            <li><strong className="text-zinc-300">Prompts</strong> — system prompt sent, user prompt sent (full audit trail)</li>
            <li><strong className="text-zinc-300">Metrics</strong> — input/output tokens, latency, cost per call</li>
            <li><strong className="text-zinc-300">Aggregates</strong> — accuracy by condition, accuracy by source (JSON only)</li>
          </ul>
        </details>
      </div>

      {/* Scenario export */}
      <div className="bg-surface-2 border border-border rounded-lg p-5 mb-5">
        <h2 className="text-base font-semibold mb-1">Scenario Results (Phase 1)</h2>
        <p className="text-sm text-zinc-500 mb-4">
          10 custom scenarios across 5 prompting conditions with dual-evaluator scoring.
        </p>

        <div className="flex gap-3 flex-wrap mb-4">
          <a
            href={getExportUrl("csv")}
            download="dodar_scenario_results.csv"
            className="inline-block bg-accent text-white px-5 py-2 rounded-lg text-sm font-medium no-underline hover:bg-accent-hover"
          >
            Download CSV
          </a>
          <a
            href={getExportUrl("json")}
            download="dodar_scenario_results.json"
            className="inline-block bg-surface-2 text-accent border border-accent px-5 py-2 rounded-lg text-sm font-medium no-underline hover:bg-accent/10"
          >
            Download JSON
          </a>
        </div>

        <details className="text-sm text-zinc-500">
          <summary className="cursor-pointer font-medium text-zinc-300 hover:text-white">
            What's included
          </summary>
          <ul className="mt-2 space-y-1 ml-1">
            <li><strong className="text-zinc-300">Scenarios</strong> — prompt text, expected pitfalls, gold standard elements, discriminators</li>
            <li><strong className="text-zinc-300">Responses</strong> — full prompt sent, full response text, token counts, latency, cost</li>
            <li><strong className="text-zinc-300">Scores</strong> — per-dimension scores (1-5) with scorer rationales</li>
            <li><strong className="text-zinc-300">Aggregates</strong> — mean/std per dimension/model/condition</li>
            <li><strong className="text-zinc-300">Effect sizes</strong> — Cohen's d for DODAR vs. each baseline</li>
          </ul>
        </details>
      </div>
    </div>
  );
}
