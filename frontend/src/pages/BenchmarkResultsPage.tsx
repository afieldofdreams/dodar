import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchBenchmarkRuns, fetchAccuracySummary, fetchAnalysis } from "../api/benchmark";

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

      {/* Protocol Analysis */}
      {accuracy && accuracy.total > 0 && <AnalysisSection />}

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


function AnalysisSection() {
  const { data: analysis } = useQuery({
    queryKey: ["benchmark-analysis"],
    queryFn: () => fetchAnalysis(),
  });

  if (!analysis || analysis.error) return null;

  const mcnemar = analysis.mcnemar_paired_tests || {};
  const efficiency = analysis.token_efficiency || {};
  const taskAnalysis = analysis.task_level_analysis || {};
  const errorDist = analysis.error_distribution_test;

  return (
    <div className="mb-8 space-y-6">
      {/* McNemar's tests */}
      {Object.keys(mcnemar).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-zinc-400 mb-2">Part I: McNemar's Paired Tests</h3>
          <div className="bg-surface-2 rounded-lg border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-zinc-500 border-b border-border">
                  <th className="px-4 py-2">Hypothesis</th>
                  <th className="px-4 py-2">Paired</th>
                  <th className="px-4 py-2">Discordant</th>
                  <th className="px-4 py-2">A only</th>
                  <th className="px-4 py-2">B only</th>
                  <th className="px-4 py-2">p-value</th>
                  <th className="px-4 py-2">Sig.</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(mcnemar).map(([key, test]: [string, any]) => (
                  <tr key={key} className="border-t border-border/30">
                    <td className="px-4 py-2 text-zinc-300 text-xs">{test.hypothesis}</td>
                    <td className="px-4 py-2 text-zinc-400">{test.n_tasks_paired}</td>
                    <td className="px-4 py-2 text-zinc-400">{test.n_discordant}</td>
                    <td className="px-4 py-2 text-zinc-400">{test.a_only_correct}</td>
                    <td className="px-4 py-2 text-zinc-400">{test.b_only_correct}</td>
                    <td className="px-4 py-2 font-mono text-xs text-zinc-300">
                      {typeof test.p_value === "number" ? test.p_value.toFixed(4) : test.p_value ?? "—"}
                    </td>
                    <td className="px-4 py-2">
                      {test.significant_at_05 === true && <span className="text-green font-semibold">***</span>}
                      {test.significant_at_05 === false && <span className="text-zinc-500">n.s.</span>}
                      {test.significant_at_05 === null && <span className="text-zinc-600">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Token efficiency */}
      {Object.keys(efficiency).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-zinc-400 mb-2">Token Efficiency</h3>
          <div className="bg-surface-2 rounded-lg border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-zinc-500 border-b border-border">
                  <th className="px-4 py-2">Condition</th>
                  <th className="px-4 py-2">Accuracy</th>
                  <th className="px-4 py-2">$/Correct</th>
                  <th className="px-4 py-2">$/Query</th>
                  <th className="px-4 py-2">Avg Tokens</th>
                  <th className="px-4 py-2">Avg Latency</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(efficiency).sort().map(([cond, eff]: [string, any]) => (
                  <tr key={cond} className="border-t border-border/30">
                    <td className={`px-4 py-2 font-semibold ${COND_COLOR[cond] || "text-zinc-300"}`}>
                      {cond} — {eff.condition_name}
                    </td>
                    <td className="px-4 py-2 text-zinc-300">{eff.accuracy_pct}%</td>
                    <td className="px-4 py-2 font-mono text-xs text-zinc-300">${eff.cost_per_correct.toFixed(4)}</td>
                    <td className="px-4 py-2 font-mono text-xs text-zinc-400">${eff.cost_per_query.toFixed(4)}</td>
                    <td className="px-4 py-2 text-zinc-400">{eff.avg_output_tokens}</td>
                    <td className="px-4 py-2 text-zinc-400">{eff.avg_latency_s}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Task contestability */}
      {taskAnalysis.contestability && (
        <div>
          <h3 className="text-sm font-semibold text-zinc-400 mb-2">Task Contestability</h3>
          <div className="flex gap-3">
            {Object.entries(taskAnalysis.contestability as Record<string, number>)
              .filter(([k]) => k !== "total")
              .map(([cat, count]) => (
                <div key={cat} className="bg-surface-2 border border-border rounded-lg px-4 py-3 text-center min-w-[100px]">
                  <div className="text-lg font-bold">{count}</div>
                  <div className="text-xs text-zinc-500">{cat}</div>
                </div>
              ))}
          </div>
          <p className="text-xs text-zinc-600 mt-1">
            Only contestable tasks differentiate between frameworks. Trivial = all conditions correct. Impossible = all wrong.
          </p>
        </div>
      )}

      {/* Chi-squared error distribution */}
      {errorDist && !errorDist.error && (
        <div>
          <h3 className="text-sm font-semibold text-zinc-400 mb-2">Part II: Error Distribution Test (H3/H5)</h3>
          <div className={`text-sm px-4 py-3 rounded-lg ${
            errorDist.significant_at_05
              ? "bg-green/10 text-green"
              : "bg-zinc-800 text-zinc-400"
          }`}>
            Chi-squared: {errorDist.chi2} | p = {errorDist.p_value} | df = {errorDist.degrees_of_freedom}
            {errorDist.significant_at_05
              ? " — Significant: error distributions differ across conditions"
              : " — Not significant at p < 0.05"}
          </div>
        </div>
      )}
    </div>
  );
}
