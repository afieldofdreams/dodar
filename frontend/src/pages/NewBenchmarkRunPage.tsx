import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  fetchBenchmarkTasks,
  fetchBenchmarkConditions,
  startBenchmarkRun,
  estimateBenchmarkCost,
} from "../api/benchmark";

const BENCHMARK_MODELS = [
  "gpt-4.1-mini",
  "gpt-4.1",
  "claude-sonnet-4-5",
  "o4-mini",
  "gpt-4o-mini",
  "claude-haiku-4-5",
  "llama3.1:8b",
] as const;

// Sources are derived from loaded tasks — no hardcoded list needed

const CONDITION_COLORS: Record<string, string> = {
  A: "text-zinc-400", B: "text-blue-400", C: "text-orange-400", D: "text-violet-400",
  E: "text-pink-400", F: "text-teal-400", G: "text-yellow-400",
};

export default function NewBenchmarkRunPage() {
  const navigate = useNavigate();
  const [taskVersion, setTaskVersion] = useState<string>("v3");
  const [selectedSource, setSelectedSource] = useState("");
  const [selectedTaskIds, setSelectedTaskIds] = useState<string[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>(["gpt-4.1-mini"]);
  const [selectedConditions, setSelectedConditions] = useState<string[]>(["A", "B", "C"]);
  const [runsPerTask, setRunsPerTask] = useState(1);
  const [skipCompleted, setSkipCompleted] = useState(true);
  const [estimate, setEstimate] = useState<import("../api/benchmark").BenchmarkEstimate | null>(null);

  const { data: tasks = [] } = useQuery({
    queryKey: ["benchmark-tasks", taskVersion],
    queryFn: () => fetchBenchmarkTasks(taskVersion),
  });

  const { data: conditions = [] } = useQuery({
    queryKey: ["benchmark-conditions"],
    queryFn: () => fetchBenchmarkConditions(true),
  });

  // Derive unique sources from loaded tasks
  const sources = [...new Set(tasks.map((t) => t.source))].sort();

  const filteredTasks = selectedSource
    ? tasks.filter((t) => t.source === selectedSource)
    : tasks;

  const estimateMutation = useMutation({
    mutationFn: () =>
      estimateBenchmarkCost({
        task_ids: selectedTaskIds.length > 0 ? selectedTaskIds : null,
        models: selectedModels,
        conditions: selectedConditions,
        runs_per_task: runsPerTask,
      }),
    onSuccess: (data) => setEstimate(data),
  });

  const runMutation = useMutation({
    mutationFn: () =>
      startBenchmarkRun({
        task_ids: selectedTaskIds.length > 0 ? selectedTaskIds : null,
        models: selectedModels,
        conditions: selectedConditions,
        runs_per_task: runsPerTask,
        skip_completed: skipCompleted,
        stage: runsPerTask === 1 ? "triage" : "validate",
        task_version: taskVersion,
      }),
    onSuccess: (data) => navigate(`/benchmark/runs/${data.run_id}`),
  });

  const toggleItem = (list: string[], item: string, setter: (v: string[]) => void) => {
    setter(list.includes(item) ? list.filter((i) => i !== item) : [...list, item]);
  };

  const taskCount = selectedTaskIds.length > 0 ? selectedTaskIds.length : tasks.length;
  const totalCalls = taskCount * selectedModels.length * selectedConditions.length * runsPerTask;

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold mb-1">New Benchmark Run</h1>
      <p className="text-zinc-500 text-sm mb-6">
        100 tasks from MedQA, MMLU, GSM8K, BBH, ARC-Challenge. Seven experimental conditions.
      </p>

      {/* Task Bank */}
      <Section title="Task Bank">
        <div className="flex gap-3 mb-3 flex-wrap">
          {([
            ["v3", "v3 — Dataset-sourced (100 tasks)"],
            ["v2", "v2 — Hand-curated (100 tasks)"],
            ["v1", "v1 — Original (100 tasks)"],
          ] as const).map(([ver, label]) => (
            <button
              key={ver}
              onClick={() => { setTaskVersion(ver); setSelectedSource(""); setSelectedTaskIds([]); }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                taskVersion === ver
                  ? "bg-accent text-white"
                  : "bg-surface-2 text-zinc-400 border border-border hover:text-zinc-200"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <p className="text-xs text-zinc-500 mb-3">
          {taskVersion === "v3"
            ? "Generated from HuggingFace datasets with full provenance. MedQA, MMLU Professional, GSM8K, BBH, ARC-Challenge."
            : taskVersion === "v2"
            ? "Hand-curated for framework differentiation. More BBH, harder MedQA, new snarks/disambiguation/navigate/logic/physics."
            : "Original benchmark from protocol v5. MedQA, MMLU, GSM8K, BBH, ARC-Challenge."}
        </p>
      </Section>

      {/* Tasks */}
      <Section title="Tasks">
        <div className="flex gap-2 mb-2">
          <select
            value={selectedSource}
            onChange={(e) => { setSelectedSource(e.target.value); setSelectedTaskIds([]); }}
            className="bg-surface-2 border border-border rounded-md px-3 py-1.5 text-sm text-zinc-300 focus:outline-none focus:border-accent"
          >
            <option value="">All Sources ({tasks.length})</option>
            {sources.map((s) => (
              <option key={s} value={s}>{s} ({tasks.filter((t) => t.source === s).length})</option>
            ))}
          </select>
          {selectedTaskIds.length > 0 && (
            <button
              onClick={() => setSelectedTaskIds([])}
              className="text-xs text-accent hover:text-accent-hover px-2"
            >
              Clear selection
            </button>
          )}
        </div>
        <div className="max-h-48 overflow-y-auto border border-border rounded-lg p-2 bg-surface-2/50">
          <label className="flex items-center gap-2 p-1 text-sm font-medium text-zinc-300 cursor-pointer">
            <input
              type="checkbox"
              checked={selectedTaskIds.length === 0}
              onChange={() => setSelectedTaskIds([])}
              className="accent-accent"
            />
            All tasks ({filteredTasks.length})
          </label>
          {filteredTasks.map((t) => (
            <label key={t.id} className="flex items-start gap-2 p-1 text-xs cursor-pointer hover:bg-white/[0.02] rounded">
              <input
                type="checkbox"
                checked={selectedTaskIds.length === 0 || selectedTaskIds.includes(t.id)}
                onChange={() => toggleItem(selectedTaskIds, t.id, setSelectedTaskIds)}
                className="accent-accent mt-0.5"
              />
              <span>
                <span className="font-medium text-accent">{t.id}</span>
                <span className="text-zinc-500 ml-1.5">
                  {t.answer_type === "multiple_choice" ? "MC" : t.answer_type === "numeric_exact" ? "NUM" : "MATCH"}
                </span>
                <span className="text-zinc-600 ml-1.5">{t.question_preview}</span>
              </span>
            </label>
          ))}
        </div>
        <div className="text-xs text-zinc-500 mt-1">
          {selectedTaskIds.length > 0 ? `${selectedTaskIds.length} selected` : `All ${filteredTasks.length} tasks`}
        </div>
      </Section>

      {/* Models */}
      <Section title="Models">
        <div className="grid grid-cols-2 gap-1">
          {BENCHMARK_MODELS.map((m) => (
            <label key={m} className="flex items-center gap-2 py-1 text-sm text-zinc-300 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={selectedModels.includes(m)}
                onChange={() => toggleItem(selectedModels, m, setSelectedModels)}
                className="accent-accent"
              />
              {m}
            </label>
          ))}
        </div>
      </Section>

      {/* Conditions */}
      <Section title="Conditions">
        <div className="grid grid-cols-2 gap-1">
          {conditions.filter((c) => !c.deprecated).map((c) => (
            <label key={c.code} className="flex items-center gap-2 py-1 text-sm cursor-pointer hover:text-white text-zinc-300">
              <input
                type="checkbox"
                checked={selectedConditions.includes(c.code)}
                onChange={() => toggleItem(selectedConditions, c.code, setSelectedConditions)}
                className="accent-accent"
              />
              <span className={`font-bold ${CONDITION_COLORS[c.code] || "text-zinc-400"}`}>{c.code}</span>
              <span>{c.name}</span>
            </label>
          ))}
        </div>
        {conditions.some((c) => c.deprecated) && (
          <div className="mt-3 pt-3 border-t border-border/50">
            <div className="text-xs text-zinc-600 mb-1">Deprecated (for comparison)</div>
            <div className="grid grid-cols-2 gap-1">
              {conditions.filter((c) => c.deprecated).map((c) => (
                <label key={c.code} className="flex items-center gap-2 py-1 text-sm cursor-pointer hover:text-zinc-300 text-zinc-500">
                  <input
                    type="checkbox"
                    checked={selectedConditions.includes(c.code)}
                    onChange={() => toggleItem(selectedConditions, c.code, setSelectedConditions)}
                    className="accent-zinc-500"
                  />
                  <span className="font-bold text-zinc-500">{c.code}</span>
                  <span>{c.name}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </Section>

      {/* Options */}
      <Section title="Options">
        <div className="flex items-center gap-6 mb-2">
          <label className="text-sm text-zinc-300">
            Runs/task:{" "}
            <select
              value={runsPerTask}
              onChange={(e) => setRunsPerTask(Number(e.target.value))}
              className="bg-surface-2 border border-border rounded px-2 py-1 text-sm text-zinc-300 ml-1"
            >
              <option value={1}>1 (triage)</option>
              <option value={3}>3 (validate)</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm text-zinc-300 cursor-pointer">
            <input type="checkbox" checked={skipCompleted} onChange={() => setSkipCompleted(!skipCompleted)} className="accent-accent" />
            Skip completed
          </label>
        </div>
        <div className="bg-surface-2 rounded-lg px-4 py-3 text-sm text-zinc-400">
          Total API calls: <span className="text-white font-semibold">{totalCalls}</span>
          <span className="text-zinc-500 ml-2">
            ({taskCount} tasks × {selectedModels.length} model{selectedModels.length !== 1 ? "s" : ""} × {selectedConditions.length} condition{selectedConditions.length !== 1 ? "s" : ""} × {runsPerTask} run{runsPerTask !== 1 ? "s" : ""})
          </span>
        </div>
      </Section>

      {/* Actions */}
      <div className="flex gap-3 mt-6">
        <button
          onClick={() => estimateMutation.mutate()}
          disabled={estimateMutation.isPending || selectedModels.length === 0 || selectedConditions.length === 0}
          className="px-5 py-2.5 rounded-lg border border-accent text-accent text-sm font-medium hover:bg-accent/10 disabled:opacity-50 transition-colors cursor-pointer"
        >
          {estimateMutation.isPending ? "Estimating..." : "Estimate Cost"}
        </button>
        <button
          onClick={() => runMutation.mutate()}
          disabled={runMutation.isPending || selectedModels.length === 0 || selectedConditions.length === 0}
          className="px-5 py-2.5 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent-hover disabled:opacity-50 transition-colors cursor-pointer"
        >
          {runMutation.isPending ? "Starting..." : "Start Run"}
        </button>
      </div>

      {runMutation.isError && (
        <p className="text-red-400 text-sm mt-3">
          Error: {(runMutation.error as Error).message}
        </p>
      )}

      {/* Cost estimate */}
      {estimate && (
        <div className="mt-6 bg-surface-2 rounded-lg border border-border overflow-hidden">
          <div className="px-4 py-3 border-b border-border text-sm font-medium text-zinc-300">Cost Estimate</div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-zinc-500">
                <th className="px-4 py-2">Component</th>
                <th className="px-4 py-2">Calls</th>
                <th className="px-4 py-2">Est. Cost</th>
              </tr>
            </thead>
            <tbody>
              {/* Benchmark runs */}
              {estimate.models.map((e, i) => (
                <tr key={i} className="border-t border-border/50">
                  <td className="px-4 py-2 text-zinc-300">Benchmark — {e.model}</td>
                  <td className="px-4 py-2 text-zinc-400">{e.calls}</td>
                  <td className="px-4 py-2 text-zinc-300">${e.estimated_cost_usd.toFixed(4)}</td>
                </tr>
              ))}
              {/* Subtotal benchmark */}
              <tr className="border-t border-border/50 text-zinc-400">
                <td className="px-4 py-1.5 text-xs">Benchmark subtotal</td>
                <td className="px-4 py-1.5 text-xs">{estimate.total_calls}</td>
                <td className="px-4 py-1.5 text-xs">${estimate.benchmark_cost_usd.toFixed(4)}</td>
              </tr>
              {/* Error classification */}
              <tr className="border-t border-border/50">
                <td className="px-4 py-2 text-zinc-300">
                  Error classification
                  <span className="text-xs text-zinc-500 ml-1">
                    (~{estimate.error_classification.estimated_incorrect} errors × {estimate.error_classification.scorers.length} scorers)
                  </span>
                </td>
                <td className="px-4 py-2 text-zinc-400">{estimate.error_classification.classification_calls}</td>
                <td className="px-4 py-2 text-zinc-300">${estimate.error_classification.estimated_cost_usd.toFixed(4)}</td>
              </tr>
              <tr className="border-t border-border/50 text-xs text-zinc-500">
                <td className="px-4 py-1 pl-8" colSpan={3}>
                  Scorers: {estimate.error_classification.scorers.join(" + ")}
                </td>
              </tr>
              {/* Total */}
              <tr className="border-t border-border font-semibold text-white">
                <td className="px-4 py-2">Total (benchmark + scoring)</td>
                <td className="px-4 py-2">{estimate.total_calls + estimate.error_classification.classification_calls}</td>
                <td className="px-4 py-2">${estimate.total_estimated_cost_usd.toFixed(4)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <h3 className="text-sm font-semibold text-zinc-400 mb-2">{title}</h3>
      {children}
    </div>
  );
}
