import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, ReferenceLine,
} from "recharts";

interface BenchmarkData {
  table2: Record<string, { tier: string; zero_shot: number; cot: number; dodar: number; pipeline: number; length_matched: number }>;
  pipeline_lift: Record<string, Record<string, number>>;
  cost_data: Array<{ model: string; quality: number; pct_opus: number; cost_per_query: number; vs_opus: string; latency_s: number }>;
  cot_lift: Record<string, number>;
  inter_rater: { exact_agreement: number; within_one_point: number; mean_abs_diff: number; signed_diff: number };
}

const COLORS = {
  zero_shot: "#94a3b8",
  cot: "#60a5fa",
  dodar: "#f97316",
  pipeline: "#22c55e",
  length_matched: "#a78bfa",
};

export default function ResearchPage() {
  const [data, setData] = useState<BenchmarkData | null>(null);

  useEffect(() => {
    fetch("/data/benchmark.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return <div className="container" style={{ padding: "4rem 0" }}>Loading...</div>;

  const barData = Object.entries(data.table2).map(([model, scores]) => ({
    model,
    ...scores,
  }));

  const cotData = Object.entries(data.cot_lift).map(([model, lift]) => ({
    model,
    lift,
    fill: lift >= 0 ? "#22c55e" : "#ef4444",
  }));

  return (
    <div className="container">
      <section style={{ padding: "3rem 0 1rem" }}>
        <h1>Research</h1>
        <p style={{ fontSize: "1.125rem", color: "var(--text-light)", maxWidth: 640 }}>
          Empirical evaluation of DODAR scaffolding across eight language models,
          five prompting conditions, and ten decision scenarios with dual-evaluator scoring.
        </p>
        <div className="btn-group" style={{ justifyContent: "flex-start", marginTop: "1.5rem" }}>
          <a href="/data/DODAR_Whitepaper_Structured_Reasoning_Cost_Efficiency.pdf" download className="btn btn-primary">
            Download whitepaper (PDF)
          </a>
          <a href="https://github.com/afieldofdreams/dodar" target="_blank" rel="noopener noreferrer" className="btn btn-secondary">
            View data on GitHub
          </a>
        </div>
      </section>

      <section className="section">
        <h2>Key finding</h2>

        <div className="finding-highlight" style={{ borderLeftWidth: 6, padding: "1.5rem 2rem", marginBottom: "2rem" }}>
          <p style={{ fontSize: "1.125rem", lineHeight: 1.7, margin: 0 }}>
            GPT-4.1 Mini + DODAR pipeline achieves <strong>104% of Claude Opus 4.6 zero-shot quality</strong> at{" "}
            <strong>89% lower real API cost</strong> — $0.0155 per query vs. $0.1424. At 100,000 queries per month,
            that translates to approximately $1,554 vs. $14,236, a saving of $12,682/month.
          </p>
        </div>

        <p style={{ color: "var(--text-light)", marginBottom: "2rem" }}>
          Structured reasoning frameworks, when applied as engineering scaffolds rather than pedagogical
          tools, function as cost-efficiency multipliers that enable small language models to approach
          frontier-level performance on complex decision tasks.
        </p>

        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-value">$0.015</div>
            <div className="stat-label">GPT-4.1 Mini pipeline cost per query</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">$0.142</div>
            <div className="stat-label">Opus 4.6 zero-shot cost per query</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">4.80</div>
            <div className="stat-label">Pipeline quality (5-point scale)</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">4.62</div>
            <div className="stat-label">Opus zero-shot quality (baseline)</div>
          </div>
        </div>

        <h2 style={{ marginTop: "3rem" }}>Three findings</h2>

        <div className="finding-highlight">
          <p>
            <strong>1. Structure is a cost-efficiency multiplier.</strong> The optimal production configuration
            is not always the most capable model — it is often the smallest model that can reliably
            follow the framework, paired with a pipeline that provides the reasoning discipline the model
            would not deploy on its own.
          </p>
        </div>
        <div className="finding-highlight">
          <p>
            <strong>2. The pipeline outperforms the single prompt.</strong> A five-phase pipeline where each
            DODAR phase runs as a separate model call with specialised personas consistently outperforms
            cramming all five phases into one instruction. The pipeline also reduces output variance,
            making results more consistent and predictable for production deployment.
          </p>
        </div>
        <div className="finding-highlight">
          <p>
            <strong>3. Chain-of-thought underperforms zero-shot.</strong> Under dual-evaluator scoring,
            CoT prompting underperforms zero-shot for 6 of 8 models. The standard assumption that
            "think step by step" either helps or is neutral does not hold for structured decision tasks
            when evaluated by multiple scorers.
          </p>
        </div>

        <h3 style={{ marginTop: "2rem" }}>Study scope</h3>
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-value">8</div>
            <div className="stat-label">Models across 4 capability tiers</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">5</div>
            <div className="stat-label">Prompting conditions</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">10</div>
            <div className="stat-label">Scenarios across 7 domains</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">400</div>
            <div className="stat-label">Responses dual-scored (from 10 core scenarios)</div>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Results</h2>

        <div className="chart-container">
          <h3>Quality scores by model and condition</h3>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", marginBottom: "1rem" }}>
            Mean quality score (1-5 scale) averaged across six dimensions and both evaluators.
            Dashed line shows Opus 4.6 zero-shot baseline (4.62).
          </p>
          <ResponsiveContainer width="100%" height={480}>
            <BarChart data={barData} margin={{ top: 30, right: 20, bottom: 80, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="model" angle={-40} textAnchor="end" fontSize={11} interval={0} height={80} />
              <YAxis domain={[0, 5]} fontSize={12} />
              <Tooltip />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: 12, paddingBottom: 8 }} />
              <ReferenceLine y={4.62} stroke="#1B2559" strokeDasharray="4 4" label={{ value: "Opus ZS (4.62)", fontSize: 10, fill: "#1B2559", position: "right" }} />
              <Bar dataKey="zero_shot" name="Zero-shot" fill={COLORS.zero_shot} />
              <Bar dataKey="cot" name="CoT" fill={COLORS.cot} />
              <Bar dataKey="dodar" name="DODAR" fill={COLORS.dodar} />
              <Bar dataKey="pipeline" name="Pipeline" fill={COLORS.pipeline} />
              <Bar dataKey="length_matched" name="Length-matched" fill={COLORS.length_matched} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Pipeline lift over zero-shot by dimension</h3>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", marginBottom: "1rem" }}>
            Score improvement when using the DODAR pipeline vs. zero-shot prompting.
            Review / Self-Correction shows the largest and most consistent gains.
          </p>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table" style={{ minWidth: 700 }}>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Diagnosis</th>
                  <th>Options</th>
                  <th>Decision</th>
                  <th>Action</th>
                  <th>Review</th>
                  <th>Overall</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data.pipeline_lift).map(([model, dims]) => (
                  <tr key={model}>
                    <td style={{ fontWeight: 500 }}>{model}</td>
                    {["Diagnosis Quality", "Option Breadth", "Decision Justification", "Action Specificity", "Review / Self-Correction", "Overall Trustworthiness"].map((dim) => {
                      const v = dims[dim];
                      const bg = v > 0 ? `rgba(34, 197, 94, ${Math.min(v / 2.6, 1) * 0.3})` : v < 0 ? `rgba(239, 68, 68, ${Math.min(Math.abs(v) / 0.5, 1) * 0.2})` : "transparent";
                      return (
                        <td key={dim} style={{ background: bg, fontWeight: 500, textAlign: "center" }}>
                          {v > 0 ? "+" : ""}{v.toFixed(1)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="chart-container">
          <h3>Chain-of-thought vs. zero-shot</h3>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", marginBottom: "1rem" }}>
            CoT lift over zero-shot baseline. Red bars indicate CoT underperformed.
            Under dual scoring, CoT hurts more often than it helps.
          </p>
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={cotData} margin={{ top: 10, right: 20, bottom: 80, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="model" angle={-40} textAnchor="end" fontSize={11} interval={0} height={80} />
              <YAxis fontSize={12} />
              <Tooltip />
              <ReferenceLine y={0} stroke="#374151" />
              <Bar dataKey="lift" name="CoT lift">
                {cotData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Cost vs. quality (pipeline)</h3>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", marginBottom: "1rem" }}>
            Real API cost per query from benchmark runs, not estimates. Pipeline configurations shown.
          </p>
          <table className="data-table">
            <thead>
              <tr>
                <th>Model + Pipeline</th>
                <th>Quality</th>
                <th>% Opus ZS</th>
                <th>$/Query</th>
                <th>vs Opus</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {data.cost_data.map((row) => (
                <tr key={row.model}>
                  <td style={{ fontWeight: 500 }}>{row.model}</td>
                  <td className={row.quality >= 4.6 ? "highlight" : ""}>{row.quality.toFixed(2)}</td>
                  <td className={row.pct_opus >= 100 ? "highlight" : ""}>{row.pct_opus}%</td>
                  <td>${row.cost_per_query.toFixed(4)}</td>
                  <td>{row.vs_opus}</td>
                  <td>{row.latency_s}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>Methodology</h2>
        <h3>Models</h3>
        <p>
          Eight models spanning four capability tiers: GPT-4.1 Nano (nano),
          GPT-4o Mini / GPT-4.1 Mini / Haiku 4.5 (small), GPT-4o (mid),
          Sonnet 4.5 (mid-frontier), GPT-5.4 and Opus 4.6 (frontier).
          Only Anthropic and OpenAI models were tested.
        </p>

        <h3>Scenarios</h3>
        <p>
          The scenario bank defines twenty scenarios across two categories, but only ten
          were fully evaluated (AMB-01 to AMB-05 and TRD-01 to TRD-05). These ten core
          scenarios form the basis of all reported results, spanning business, medical,
          legal, technical, personal, startup, career, policy, investment, and operations domains.
          This limited scenario count is a significant constraint on generalisability.
        </p>

        <h3>Conditions</h3>
        <p>
          Five prompting conditions: zero-shot (baseline), chain-of-thought,
          DODAR single prompt, DODAR pipeline (five sequential calls with
          specialised personas), and length-matched control (same token budget
          as DODAR, unstructured).
        </p>

        <h3>Scoring</h3>
        <p>
          Six dimensions scored on a 1-5 Likert scale: Diagnosis Quality,
          Option Breadth, Decision Justification, Action Specificity,
          Review / Self-Correction, and Overall Trustworthiness. Every response
          scored independently by Claude Opus 4.6 and GPT-5.4. Final scores
          averaged across both evaluators.
        </p>

        <h3>Sample sizes</h3>
        <p>
          The full dataset contains 449 response items, of which 400 from the 10 core
          scenarios were scored by both evaluators. Each model-condition combination has
          10 response items (one per scenario), yielding n=20 individual scores per cell
          (scored by two evaluators). The effective sample size for independence is 10.
          The DODAR single-prompt condition has n=40 because items were scored in two
          separate evaluation runs. This is a small base for robust conclusions.
        </p>

        <h3>Dual-evaluator agreement</h3>
        <p>
          Across 1200 paired comparisons: {data.inter_rater.exact_agreement * 100}% exact agreement,{" "}
          {data.inter_rater.within_one_point * 100}% agreement within one point.
          Mean absolute difference: {data.inter_rater.mean_abs_diff} points.
          Claude scores marginally higher than GPT-5.4 (signed difference: +{data.inter_rater.signed_diff}).
          Agreement is highest on Review / Self-Correction (80% exact) and lowest on
          Overall Trustworthiness (58% exact).
        </p>
      </section>

      <section className="section">
        <h2>Limitations</h2>
        <p>These findings come with substantial caveats, presented in approximate order of severity.</p>

        <div className="limitation">
          <p><strong>Ceiling effects and scale sensitivity.</strong> The 5-point scale cannot discriminate well at the top end. 10% of cells score 4.90 or above. A wider scale would provide better resolution.</p>
        </div>
        <div className="limitation">
          <p><strong>No human evaluation baseline.</strong> All scoring was automated. We have no human expert scores to anchor what a 4.80 means in practice.</p>
        </div>
        <div className="limitation">
          <p><strong>Evaluator-model overlap.</strong> Despite dual scoring, Claude evaluates Anthropic models and GPT-5.4 evaluates OpenAI models. Averaging partially mitigates but does not eliminate potential bias.</p>
        </div>
        <div className="limitation">
          <p><strong>Prompt sensitivity untested.</strong> A single version of each prompt was tested. We do not know how sensitive results are to prompt wording.</p>
        </div>
        <div className="limitation">
          <p><strong>Small effective sample size.</strong> Only 10 scenarios were fully evaluated. The effective sample size for independence is 10 per model-condition cell. n=20 reflects 10 items scored twice, not 20 independent responses. This is a small base for robust conclusions.</p>
        </div>
        <div className="limitation">
          <p><strong>Model selection bias.</strong> Only OpenAI and Anthropic models were tested. Results may not generalise to Google, Meta, Mistral, or DeepSeek models.</p>
        </div>
        <div className="limitation">
          <p><strong>Scenario design not validated.</strong> The ten scenarios were authored for this study and have not been independently validated. With only ten scenarios, there is limited coverage of any single domain.</p>
        </div>
        <div className="limitation">
          <p><strong>Single framework tested.</strong> Only DODAR was evaluated. Other structured frameworks (OODA, Six Thinking Hats) might produce different results.</p>
        </div>
      </section>

      <section className="section" style={{ textAlign: "center", paddingBottom: "4rem" }}>
        <a href="/data/DODAR_Whitepaper_Structured_Reasoning_Cost_Efficiency.pdf" download className="btn btn-primary">
          Download the full whitepaper (PDF)
        </a>
      </section>
    </div>
  );
}
