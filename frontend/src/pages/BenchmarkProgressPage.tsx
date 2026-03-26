import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchBenchmarkRun, fetchBenchmarkRunResults } from "../api/benchmark";
import type { BenchmarkResult } from "../api/benchmark";
import { useRunWebSocket } from "../hooks/useWebSocket";

const CONDITION_NAMES: Record<string, string> = {
  A: "Baseline", B: "Zero-Shot CoT", C: "PGR", D: "ReAct",
  E: "Step-Back", F: "Shuffled PGR", G: "Few-Shot CoT",
};

const COND_COLOR: Record<string, string> = {
  A: "text-zinc-400", B: "text-blue-400", C: "text-orange-400", D: "text-violet-400",
  E: "text-pink-400", F: "text-teal-400", G: "text-yellow-400",
};

export default function BenchmarkProgressPage() {
  const { id } = useParams<{ id: string }>();
  const [expandedItem, setExpandedItem] = useState<string | null>(null);

  const { data: run } = useQuery({
    queryKey: ["benchmark-run", id],
    queryFn: () => fetchBenchmarkRun(id!),
    enabled: !!id,
    refetchInterval: (query) => query.state.data?.status === "running" ? 3000 : false,
  });

  const isRunning = run?.status === "running";
  const { events, latestEvent, connected, cancel } = useRunWebSocket(isRunning ? (id ?? null) : null);

  const { data: results = [] } = useQuery({
    queryKey: ["benchmark-run-results", id],
    queryFn: () => fetchBenchmarkRunResults(id!),
    enabled: !!id && !isRunning,
  });

  const progress = latestEvent?.progress ?? { completed: run?.completed_items ?? 0, total: run?.total_items ?? 0 };
  const pct = progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : 0;

  const byCondition: Record<string, BenchmarkResult[]> = {};
  for (const r of results) (byCondition[r.condition] ??= []).push(r);

  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <h1 className="text-xl font-bold">{id}</h1>
        {run?.config?.stage && (
          <span className="text-xs font-semibold bg-surface-3 text-zinc-400 px-2.5 py-1 rounded-md">{run.config.stage}</span>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <Stat label="Status" value={run?.status ?? "..."} />
        <Stat label="Progress" value={`${progress.completed}/${progress.total}`} />
        <Stat label="Correct" value={`${run?.correct_items ?? 0}`} />
        <Stat label="Cost" value={`$${(run?.total_cost_usd ?? 0).toFixed(4)}`} />
      </div>

      {/* Progress bar */}
      <div className="bg-surface-3 rounded-full h-5 mb-5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 flex items-center justify-center text-[11px] font-semibold text-white ${
            isRunning ? "bg-accent" : "bg-green"
          }`}
          style={{ width: `${pct}%` }}
        >
          {pct > 10 && `${pct}%`}
        </div>
      </div>

      {isRunning && (
        <button onClick={cancel} className="mb-4 px-4 py-2 rounded-lg bg-red text-white text-sm font-medium hover:bg-red-500 cursor-pointer">
          Cancel Run
        </button>
      )}

      {/* Accuracy by condition */}
      {run?.accuracy_by_condition && Object.keys(run.accuracy_by_condition).length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-zinc-400 mb-2">Accuracy by Condition</h3>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(run.accuracy_by_condition).sort().map(([cond, acc]) => (
              <div key={cond} className="bg-surface-2 border border-border rounded-lg px-4 py-3 text-center min-w-[90px]">
                <div className={`text-lg font-bold ${COND_COLOR[cond] || "text-zinc-300"}`}>{acc}%</div>
                <div className="text-xs text-zinc-500 font-medium">{cond} — {CONDITION_NAMES[cond]}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live event log */}
      {isRunning && events.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-zinc-400 mb-2">Event Log</h3>
          <div className="bg-[#0d0d1a] rounded-lg p-4 max-h-80 overflow-y-auto font-mono text-xs leading-relaxed">
            {[...events].reverse().map((e, i) => (
              <div key={i} className="flex gap-2 mb-0.5">
                <span className="text-zinc-600 shrink-0 w-16">
                  {e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : ""}
                </span>
                <span className="shrink-0 w-3">
                  {e.type === "item_complete" ? "✓" : e.type === "item_error" ? "✗" : e.type === "run_complete" ? "★" : "▸"}
                </span>
                <span>
                  {e.type === "item_complete" && (
                    <>
                      <span className="text-green">DONE</span>{" "}
                      <span className="text-white">{e.scenario_id}</span>
                      <span className="text-zinc-600"> / </span>
                      <span className="text-teal-400">{e.model}</span>
                      <span className="text-zinc-600"> / </span>
                      <span className={COND_COLOR[e.condition ?? ""] || "text-zinc-300"}>{e.condition}</span>
                      <span className="text-zinc-600"> — {e.tokens_used?.toLocaleString()} tok</span>
                    </>
                  )}
                  {e.type === "item_start" && (
                    <>
                      <span className="text-blue-400">START</span>{" "}
                      <span className="text-white">{e.scenario_id}</span>
                      <span className="text-zinc-600"> / {e.model} / {e.condition}</span>
                    </>
                  )}
                  {e.type === "item_error" && (
                    <span className="text-red">FAIL {e.scenario_id} — {e.error?.slice(0, 100)}</span>
                  )}
                  {e.type === "run_complete" && <span className="text-green font-semibold">RUN COMPLETE</span>}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {!isRunning && results.length > 0 && (
        <div>
          <h2 className="text-base font-semibold mb-3">
            Results
            <span className="text-zinc-500 font-normal text-sm ml-2">
              {results.filter((r) => r.is_correct).length}/{results.length} correct
            </span>
          </h2>

          {Object.entries(byCondition).sort().map(([cond, items]) => {
            const correct = items.filter((r) => r.is_correct).length;
            return (
              <div key={cond} className="bg-surface-2 rounded-lg border border-border mb-4 overflow-hidden">
                <div className="flex justify-between items-center px-4 py-3 border-b border-border/50">
                  <span className={`font-semibold ${COND_COLOR[cond]}`}>
                    {cond} — {CONDITION_NAMES[cond]}
                  </span>
                  <span className="text-sm text-zinc-500">
                    {correct}/{items.length} ({Math.round(correct / items.length * 100)}%)
                  </span>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-zinc-500">
                      <th className="px-4 py-2">Task</th>
                      <th className="px-4 py-2">Source</th>
                      <th className="px-4 py-2 w-8"></th>
                      <th className="px-4 py-2">Answer</th>
                      <th className="px-4 py-2">Expected</th>
                      <th className="px-4 py-2">Tokens</th>
                      <th className="px-4 py-2 w-12"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.sort((a, b) => a.task_id.localeCompare(b.task_id)).map((r) => {
                      const key = `${r.task_id}_${r.condition}_${r.model_id}_${r.run_number}`;
                      const isExpanded = expandedItem === key;
                      return (
                        <>
                          <tr key={key} className={`border-t border-border/30 ${r.is_correct ? "" : "bg-red/[0.03]"}`}>
                            <td className="px-4 py-2 font-medium text-zinc-300">{r.task_id}</td>
                            <td className="px-4 py-2 text-xs text-zinc-500">{r.source}</td>
                            <td className="px-4 py-2">
                              <span className={r.is_correct ? "text-green" : "text-red"}>
                                {r.is_correct ? "✓" : "✗"}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-zinc-300 font-mono text-xs">{r.extracted_answer ?? "—"}</td>
                            <td className="px-4 py-2 text-zinc-500 font-mono text-xs">{r.correct_answer}</td>
                            <td className="px-4 py-2 text-zinc-500 text-xs">{(r.input_tokens + r.output_tokens).toLocaleString()}</td>
                            <td className="px-4 py-2">
                              <button
                                onClick={() => setExpandedItem(isExpanded ? null : key)}
                                className="text-accent text-xs hover:underline cursor-pointer"
                              >
                                {isExpanded ? "Hide" : "View"}
                              </button>
                            </td>
                          </tr>
                          {isExpanded && (
                            <tr key={key + "-exp"}>
                              <td colSpan={7} className="px-4 py-3 bg-surface/50">
                                <div className="text-xs text-zinc-500 mb-2">
                                  Model: {r.model_id} | Type: {r.answer_type} | Latency: {r.latency_seconds.toFixed(1)}s | Cost: ${r.cost_usd.toFixed(4)}
                                </div>
                                <pre className="whitespace-pre-wrap bg-[#0d0d1a] text-zinc-300 rounded-lg p-4 text-xs leading-relaxed max-h-96 overflow-y-auto border border-border/50">
                                  {r.raw_response}
                                </pre>
                              </td>
                            </tr>
                          )}
                        </>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-2 rounded-lg px-4 py-3 text-center">
      <div className="text-[11px] text-zinc-500 mb-1">{label}</div>
      <div className="font-semibold text-base">{value}</div>
    </div>
  );
}
