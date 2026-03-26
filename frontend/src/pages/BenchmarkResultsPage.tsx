import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchBenchmarkRuns, fetchAccuracySummary } from "../api/benchmark";

const CONDITION_NAMES: Record<string, string> = {
  A: "Baseline", B: "Zero-Shot CoT", C: "PGR", D: "ReAct",
  E: "Step-Back", F: "Shuffled PGR", G: "Few-Shot CoT",
};

const COND_COLOR: Record<string, string> = {
  A: "text-zinc-400", B: "text-blue-400", C: "text-orange-400", D: "text-violet-400",
  E: "text-pink-400", F: "text-teal-400", G: "text-yellow-400",
};

const STATUS_STYLE: Record<string, string> = {
  running: "bg-blue-500/10 text-blue-400",
  completed: "bg-green/10 text-green",
  failed: "bg-red/10 text-red",
  pending: "bg-orange/10 text-orange",
};

export default function BenchmarkResultsPage() {
  const { data: runs = [] } = useQuery({
    queryKey: ["benchmark-runs"],
    queryFn: fetchBenchmarkRuns,
  });

  const { data: accuracy } = useQuery({
    queryKey: ["benchmark-accuracy"],
    queryFn: () => fetchAccuracySummary(),
  });

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Benchmark Results</h1>
        <Link
          to="/benchmark/new"
          className="px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent-hover no-underline"
        >
          New Run
        </Link>
      </div>

      {/* Accuracy overview */}
      {accuracy && accuracy.total > 0 && (
        <div className="mb-8">
          {/* Top-level stats */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="bg-surface-2 rounded-lg px-4 py-3 text-center">
              <div className="text-[11px] text-zinc-500 mb-1">Responses</div>
              <div className="text-lg font-bold">{accuracy.total}</div>
            </div>
            <div className="bg-surface-2 rounded-lg px-4 py-3 text-center">
              <div className="text-[11px] text-zinc-500 mb-1">Overall Accuracy</div>
              <div className="text-lg font-bold">{accuracy.overall_accuracy}%</div>
            </div>
            <div className="bg-surface-2 rounded-lg px-4 py-3 text-center">
              <div className="text-[11px] text-zinc-500 mb-1">Correct</div>
              <div className="text-lg font-bold">{accuracy.total_correct}</div>
            </div>
          </div>

          {/* By condition */}
          <h3 className="text-sm font-semibold text-zinc-400 mb-2">By Condition</h3>
          <div className="flex gap-2 flex-wrap mb-6">
            {Object.entries(accuracy.by_condition)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([code, data]) => (
                <div key={code} className="bg-surface-2 border border-border rounded-lg px-4 py-3 text-center min-w-[90px]">
                  <div className={`text-lg font-bold ${COND_COLOR[code] || "text-zinc-300"}`}>
                    {data.accuracy}%
                  </div>
                  <div className="text-xs font-semibold text-zinc-500">{code}</div>
                  <div className="text-[10px] text-zinc-600">{data.name}</div>
                  <div className="text-[10px] text-zinc-700">{data.correct}/{data.total}</div>
                </div>
              ))}
          </div>

          {/* By source */}
          <h3 className="text-sm font-semibold text-zinc-400 mb-2">By Source</h3>
          <div className="flex gap-2 flex-wrap mb-6">
            {Object.entries(accuracy.by_source)
              .sort(([, a], [, b]) => b.accuracy - a.accuracy)
              .map(([source, data]) => (
                <div key={source} className="bg-surface-2 border border-border rounded-lg px-4 py-3 text-center min-w-[100px]">
                  <div className="text-lg font-bold">{data.accuracy}%</div>
                  <div className="text-[11px] text-zinc-500">{source}</div>
                  <div className="text-[10px] text-zinc-700">{data.correct}/{data.total}</div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Run history */}
      <h3 className="text-sm font-semibold text-zinc-400 mb-2">Run History</h3>
      {runs.length === 0 ? (
        <p className="text-zinc-500 text-sm">
          No runs yet. <Link to="/benchmark/new" className="text-accent hover:underline">Start one</Link>.
        </p>
      ) : (
        <div className="bg-surface-2 rounded-lg border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-zinc-500 border-b border-border">
                <th className="px-4 py-2.5">Run</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Stage</th>
                <th className="px-4 py-2.5">Progress</th>
                <th className="px-4 py-2.5">Correct</th>
                <th className="px-4 py-2.5">Cost</th>
                <th className="px-4 py-2.5">Date</th>
              </tr>
            </thead>
            <tbody>
              {[...runs].reverse().map((run) => (
                <tr key={run.run_id} className="border-t border-border/40 hover:bg-white/[0.02]">
                  <td className="px-4 py-2.5">
                    <Link to={`/benchmark/runs/${run.run_id}`} className="text-accent hover:underline font-medium no-underline">
                      {run.run_id}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${STATUS_STYLE[run.status] || "bg-zinc-800 text-zinc-400"}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-zinc-400">{run.config.stage}</td>
                  <td className="px-4 py-2.5 text-zinc-400">
                    {run.completed_items}/{run.total_items}
                  </td>
                  <td className="px-4 py-2.5">
                    {run.correct_items}
                    {run.completed_items > 0 && (
                      <span className="text-zinc-500 text-xs ml-1">
                        ({Math.round(run.correct_items / run.completed_items * 100)}%)
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-zinc-400">${run.total_cost_usd.toFixed(4)}</td>
                  <td className="px-4 py-2.5 text-xs text-zinc-500">
                    {new Date(run.created_at).toLocaleDateString()}{" "}
                    {new Date(run.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
