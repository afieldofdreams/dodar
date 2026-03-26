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

const SOURCES = ["MedQA-USMLE", "MMLU", "GSM8K", "BBH", "ARC-Challenge"] as const;

const CONDITION_COLORS: Record<string, string> = {
  A: "text-zinc-400", B: "text-blue-400", C: "text-orange-400", D: "text-violet-400",
  E: "text-pink-400", F: "text-teal-400", G: "text-yellow-400",
};

export default function NewBenchmarkRunPage() {
  const navigate = useNavigate();
  const [selectedSource, setSelectedSource] = useState("");
  const [selectedTaskIds, setSelectedTaskIds] = useState<string[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>(["gpt-4.1-mini"]);
  const [selectedConditions, setSelectedConditions] = useState<string[]>(["A", "B", "C"]);
  const [runsPerTask, setRunsPerTask] = useState(1);
  const [skipCompleted, setSkipCompleted] = useState(true);
  const [estimate, setEstimate] = useState<{
    total_calls: number;
    total_estimated_cost_usd: number;
    models: Array<{ model: string; calls: number; estimated_cost_usd: number }>;
  } | null>(null);

  const { data: tasks = [] } = useQuery({
    queryKey: ["benchmark-tasks"],
    queryFn: fetchBenchmarkTasks,
  });

  const { data: conditions = [] } = useQuery({
    queryKey: ["benchmark-conditions"],
    queryFn: fetchBenchmarkConditions,
  });

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

      {/* Tasks */}
      <Section title="Tasks">
        <div className="flex gap-2 mb-2">
          <select
            value={selectedSource}
            onChange={(e) => { setSelectedSource(e.target.value); setSelectedTaskIds([]); }}
            className="bg-surface-2 border border-border rounded-md px-3 py-1.5 text-sm text-zinc-300 focus:outline-none focus:border-accent"
          >
            <option value="">All Sources ({tasks.length})</option>
            {SOURCES.map((s) => (
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
          {conditions.map((c) => (
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
                <th className="px-4 py-2">Model</th>
                <th className="px-4 py-2">Calls</th>
                <th className="px-4 py-2">Est. Cost</th>
              </tr>
            </thead>
            <tbody>
              {estimate.models.map((e, i) => (
                <tr key={i} className="border-t border-border/50">
                  <td className="px-4 py-2 text-zinc-300">{e.model}</td>
                  <td className="px-4 py-2 text-zinc-400">{e.calls}</td>
                  <td className="px-4 py-2 text-zinc-300">${e.estimated_cost_usd.toFixed(4)}</td>
                </tr>
              ))}
              <tr className="border-t border-border font-semibold text-white">
                <td className="px-4 py-2">Total</td>
                <td className="px-4 py-2">{estimate.total_calls}</td>
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
