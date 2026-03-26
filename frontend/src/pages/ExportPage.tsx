import { getExportUrl } from "../api/reports";

function getBenchmarkExportUrl(format: "json" | "csv"): string {
  return `/api/benchmark/export?format=${format}`;
}

export default function ExportPage() {
  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold mb-6">Export Data</h1>

      {/* Benchmark export */}
      <ExportCard
        title="Benchmark Results (Phase 2)"
        description="100 benchmark tasks across 7 experimental conditions. Includes task questions, model responses, extracted answers, correctness, tokens, latency, and cost."
        csvUrl={getBenchmarkExportUrl("csv")}
        jsonUrl={getBenchmarkExportUrl("json")}
        details={[
          { label: "Tasks", text: "task ID, source, question text, correct answer, answer type" },
          { label: "Results", text: "condition (A-G), model, extracted answer, is_correct, raw response" },
          { label: "Prompts", text: "system prompt sent, user prompt sent (full audit trail)" },
          { label: "Metrics", text: "input/output tokens, latency, cost per call" },
          { label: "Aggregates", text: "accuracy by condition, accuracy by source (in JSON)" },
        ]}
        csvFilename="dodar_benchmark_results.csv"
        jsonFilename="dodar_benchmark_results.json"
      />

      {/* Scenario export */}
      <ExportCard
        title="Scenario Results (Phase 1)"
        description="10 custom scenarios across 5 prompting conditions with dual-evaluator scoring. Includes scenario metadata, prompts, responses, per-dimension scores with rationales, and effect sizes."
        csvUrl={getExportUrl("csv")}
        jsonUrl={getExportUrl("json")}
        details={[
          { label: "Scenarios", text: "prompt text, expected pitfalls, gold standard elements, discriminators" },
          { label: "Responses", text: "full prompt sent, full response text, token counts, latency, cost" },
          { label: "Scores", text: "per-dimension scores (1-5) with scorer rationales, from each session" },
          { label: "Aggregates", text: "mean/std per dimension/model/condition" },
          { label: "Effect sizes", text: "Cohen's d for DODAR vs. each baseline" },
        ]}
        csvFilename="dodar_benchmark_full.csv"
        jsonFilename="dodar_benchmark_full.json"
      />
    </div>
  );
}

function ExportCard({
  title,
  description,
  csvUrl,
  jsonUrl,
  details,
  csvFilename,
  jsonFilename,
}: {
  title: string;
  description: string;
  csvUrl: string;
  jsonUrl: string;
  details: Array<{ label: string; text: string }>;
  csvFilename: string;
  jsonFilename: string;
}) {
  return (
    <div className="bg-surface-2 border border-border rounded-lg p-5 mb-5">
      <h2 className="text-base font-semibold mb-1">{title}</h2>
      <p className="text-sm text-zinc-500 mb-4">{description}</p>

      <div className="flex gap-3 flex-wrap mb-4">
        <a
          href={csvUrl}
          download={csvFilename}
          className="inline-block bg-accent text-white px-5 py-2 rounded-lg text-sm font-medium no-underline hover:bg-accent-hover"
        >
          Download CSV
        </a>
        <a
          href={jsonUrl}
          download={jsonFilename}
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
          {details.map((d) => (
            <li key={d.label}>
              <strong className="text-zinc-300">{d.label}</strong> — {d.text}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
