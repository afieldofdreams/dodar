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

const CONDITION_COLORS: Record<string, string> = {
  A: "#94a3b8",
  B: "#60a5fa",
  C: "#f97316",
  D: "#8b5cf6",
  E: "#ec4899",
  F: "#14b8a6",
  G: "#eab308",
};

export default function ResearchPage() {
  const [data, setData] = useState<BenchmarkData | null>(null);
  const [activeTab, setActiveTab] = useState<"phase2" | "phase1">("phase2");

  useEffect(() => {
    fetch("/data/benchmark.json")
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(null));
  }, []);

  return (
    <div className="container">
      <section style={{ padding: "3rem 0 1rem" }}>
        <h1>Research</h1>
        <p style={{ fontSize: "1.125rem", color: "var(--text-light)", maxWidth: 640 }}>
          Does reasoning structure shape failure, not just accuracy? Seven prompting
          frameworks compared across 100 established benchmark tasks.
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

      {/* Tab switcher */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem", borderBottom: "2px solid var(--border)" }}>
        <button
          onClick={() => setActiveTab("phase2")}
          style={{
            padding: "0.75rem 1.5rem",
            background: "none",
            border: "none",
            borderBottom: activeTab === "phase2" ? "3px solid var(--primary)" : "3px solid transparent",
            fontWeight: activeTab === "phase2" ? 600 : 400,
            cursor: "pointer",
            fontSize: "1rem",
          }}
        >
          Phase 2: Benchmark evaluation
        </button>
        <button
          onClick={() => setActiveTab("phase1")}
          style={{
            padding: "0.75rem 1.5rem",
            background: "none",
            border: "none",
            borderBottom: activeTab === "phase1" ? "3px solid var(--primary)" : "3px solid transparent",
            fontWeight: activeTab === "phase1" ? 600 : 400,
            cursor: "pointer",
            fontSize: "1rem",
          }}
        >
          Phase 1: Scenario evaluation
        </button>
      </div>

      {activeTab === "phase2" && <Phase2Content />}
      {activeTab === "phase1" && data && <Phase1Content data={data} />}
      {activeTab === "phase1" && !data && (
        <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-light)" }}>
          Loading Phase 1 data...
        </div>
      )}
    </div>
  );
}


function Phase2Content() {
  return (
    <>
      <section className="section">
        <h2>Protocol overview</h2>
        <p style={{ color: "var(--text-light)", marginBottom: "2rem", maxWidth: 720 }}>
          This protocol tests whether structured prompting frameworks produce
          measurably different reasoning failures from generic chain-of-thought,
          independent of the additional compute they elicit.
        </p>

        <h3>The question</h3>
        <div className="finding-highlight" style={{ borderLeftWidth: 6, padding: "1.5rem 2rem", marginBottom: "2rem" }}>
          <p style={{ fontSize: "1.05rem", lineHeight: 1.7, margin: 0 }}>
            When a structured framework improves LLM performance, what is doing the work:
            the framework's architecture, the additional tokens it forces the model to
            generate, or the richer information content it provides?
          </p>
        </div>

        <h3>Seven conditions</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Condition</th>
              <th>Tokens</th>
              <th>Structure</th>
              <th>Part</th>
            </tr>
          </thead>
          <tbody>
            <tr><td><span style={{ color: CONDITION_COLORS.A, fontWeight: 700 }}>A</span></td><td>Baseline</td><td>0</td><td>None</td><td>I + II</td></tr>
            <tr><td><span style={{ color: CONDITION_COLORS.B, fontWeight: 700 }}>B</span></td><td>Zero-Shot CoT (token-matched)</td><td>~228</td><td>Unstructured elaboration</td><td>I + II</td></tr>
            <tr><td><span style={{ color: CONDITION_COLORS.G, fontWeight: 700 }}>G</span></td><td>Few-Shot CoT (worked example)</td><td>~280-400</td><td>Demonstration of reasoning</td><td>I + II</td></tr>
            <tr><td><span style={{ color: CONDITION_COLORS.C, fontWeight: 700 }}>C</span></td><td>Phase-Gated Reasoning (PGR)</td><td>~236</td><td>Five sequential phase gates</td><td>I + II</td></tr>
            <tr><td><span style={{ color: CONDITION_COLORS.F, fontWeight: 700 }}>F</span></td><td>Shuffled-Phase PGR</td><td>~236</td><td>Same phases, random order</td><td>I</td></tr>
            <tr><td><span style={{ color: CONDITION_COLORS.D, fontWeight: 700 }}>D</span></td><td>ReAct (Closed-Book)</td><td>~149</td><td>Iterative T-A-O loops</td><td>II</td></tr>
            <tr><td><span style={{ color: CONDITION_COLORS.E, fontWeight: 700 }}>E</span></td><td>Step-Back Prompting</td><td>~120</td><td>Abstraction then reasoning</td><td>II</td></tr>
          </tbody>
        </table>
      </section>

      <section className="section">
        <h3>Task sources (100 tasks)</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Domain</th>
              <th>n</th>
              <th>Answer type</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>MedQA (USMLE)</td><td>Clinical reasoning</td><td>20</td><td>Multiple choice (4 options)</td></tr>
            <tr><td>MMLU Professional</td><td>Medicine, Law, Accounting</td><td>20</td><td>Multiple choice (4 options)</td></tr>
            <tr><td>GSM8K</td><td>Mathematical reasoning</td><td>20</td><td>Numeric (exact)</td></tr>
            <tr><td>BIG-Bench Hard</td><td>Causal, Logical, Tracking, Lies</td><td>20</td><td>Exact match</td></tr>
            <tr><td>ARC-Challenge</td><td>Science reasoning</td><td>20</td><td>Multiple choice (4 options)</td></tr>
          </tbody>
        </table>
      </section>

      <section className="section">
        <h3>Three compute controls</h3>
        <div className="card-grid">
          <div className="card">
            <h3>1. Prompt-level</h3>
            <p>B and C token-matched within 3%. C and F have identical token counts. Same input compute, different structure.</p>
          </div>
          <div className="card">
            <h3>2. Output-level (statistical)</h3>
            <p>Logistic regression: accuracy ~ condition + output_tokens + interaction. Does the condition still predict accuracy after controlling for response length?</p>
          </div>
          <div className="card">
            <h3>3. Output-level (truncation)</h3>
            <p>Truncate PGR responses to CoT median length. Re-extract answers. Re-score. Zero additional API calls.</p>
          </div>
        </div>
      </section>

      <section className="section">
        <h3>Pre-registered hypotheses</h3>
        <div className="finding-highlight">
          <p><strong>H1:</strong> PGR produces higher accuracy than token-matched zero-shot CoT, even after controlling for output token count.</p>
        </div>
        <div className="finding-highlight">
          <p><strong>H2:</strong> PGR produces higher accuracy than few-shot CoT, demonstrating that phase gates outperform a worked example.</p>
        </div>
        <div className="finding-highlight">
          <p><strong>H3:</strong> PGR produces a different distribution of failure types compared to CoT, with significantly fewer premature closure errors.</p>
        </div>
        <div className="finding-highlight">
          <p><strong>H4:</strong> PGR outperforms shuffled-phase PGR, demonstrating that the specific sequence matters.</p>
        </div>
        <div className="finding-highlight">
          <p><strong>H5:</strong> Different frameworks produce different error distributions, even when overall accuracy is similar.</p>
        </div>
      </section>

      <section className="section">
        <h3>Error taxonomy (primary contribution)</h3>
        <p style={{ color: "var(--text-light)", marginBottom: "1.5rem" }}>
          Every incorrect response is classified into one of seven failure types. The taxonomy
          is derived from clinical decision-making literature, not from any prompting condition.
        </p>
        <table className="data-table">
          <thead>
            <tr>
              <th>Failure type</th>
              <th>Definition</th>
            </tr>
          </thead>
          <tbody>
            <tr><td style={{ fontWeight: 500 }}>Premature closure</td><td>Commits before adequately exploring the problem space</td></tr>
            <tr><td style={{ fontWeight: 500 }}>Anchoring error</td><td>Fixates on one detail, fails to adjust despite contradictory evidence</td></tr>
            <tr><td style={{ fontWeight: 500 }}>Incomplete search</td><td>Considers too few options or approaches</td></tr>
            <tr><td style={{ fontWeight: 500 }}>Failure to revise</td><td>Identifies an error but does not correct the final answer</td></tr>
            <tr><td style={{ fontWeight: 500 }}>Execution error</td><td>Correct approach, mechanical error in implementation</td></tr>
            <tr><td style={{ fontWeight: 500 }}>Comprehension failure</td><td>Fundamentally misunderstands what is being asked</td></tr>
            <tr><td style={{ fontWeight: 500 }}>Abstention</td><td>Declines to answer or produces no extractable answer</td></tr>
          </tbody>
        </table>
      </section>

      <section className="section">
        <h3>Staged execution</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Stage</th>
              <th>Models</th>
              <th>Conditions</th>
              <th>Runs</th>
              <th>Calls</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ fontWeight: 500 }}>1: Triage</td>
              <td>GPT-4.1 Mini</td>
              <td>All 7</td>
              <td>1</td>
              <td>700</td>
              <td>~$15-25</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 500 }}>2: Validate</td>
              <td>Mini + Sonnet + o4-mini</td>
              <td>Survivors + controls</td>
              <td>3</td>
              <td>~2,100-3,150</td>
              <td>~$60-130</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 500 }}>3: Full</td>
              <td>All 7 models</td>
              <td>Retained</td>
              <td>3</td>
              <td>Up to 6,300</td>
              <td>~$250-500+</td>
            </tr>
          </tbody>
        </table>
        <p style={{ color: "var(--text-light)", fontSize: "0.875rem", marginTop: "1rem" }}>
          Stage 1 alone is publishable. Each subsequent stage is conditional on previous findings.
          If Stage 1 shows no differentiation, the negative result is published.
        </p>
      </section>

      <section className="section" style={{ textAlign: "center", paddingBottom: "4rem" }}>
        <p style={{ color: "var(--text-light)", marginBottom: "1.5rem" }}>
          Results will be published here as each stage completes. All data, code, and analysis
          scripts are open-source.
        </p>
        <a href="https://github.com/afieldofdreams/dodar" target="_blank" rel="noopener noreferrer" className="btn btn-primary">
          Follow on GitHub
        </a>
      </section>
    </>
  );
}


function Phase1Content({ data }: { data: BenchmarkData }) {
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
    <>
      <section className="section">
        <h2>Phase 1: Scenario evaluation</h2>
        <p style={{ color: "var(--text-light)", marginBottom: "1.5rem" }}>
          Initial evaluation across 10 custom scenarios, 8 models, 5 prompting conditions,
          with dual-evaluator scoring. These results motivated the expanded Phase 2 protocol.
        </p>

        <h3>Key finding</h3>
        <div className="finding-highlight" style={{ borderLeftWidth: 6, padding: "1.5rem 2rem", marginBottom: "2rem" }}>
          <p style={{ fontSize: "1.125rem", lineHeight: 1.7, margin: 0 }}>
            GPT-4.1 Mini + DODAR pipeline achieves <strong>104% of Claude Opus 4.6 zero-shot quality</strong> at{" "}
            <strong>89% lower real API cost</strong> — $0.0155 per query vs. $0.1424. At 100,000 queries per month,
            that translates to approximately $1,554 vs. $14,236, a saving of $12,682/month.
          </p>
        </div>

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
            <div className="stat-label">Responses dual-scored</div>
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
        <h2>Phase 1 limitations</h2>
        <p>These findings motivated the expanded Phase 2 protocol.</p>
        <div className="limitation">
          <p><strong>Small effective sample size.</strong> Only 10 custom scenarios. n=10 per model-condition cell.</p>
        </div>
        <div className="limitation">
          <p><strong>No ground truth.</strong> Custom scenarios with subjective scoring (1-5 Likert). No objectively correct answers.</p>
        </div>
        <div className="limitation">
          <p><strong>No human evaluation baseline.</strong> All scoring automated by LLM evaluators.</p>
        </div>
        <div className="limitation">
          <p><strong>Evaluator-model overlap.</strong> Claude evaluates Anthropic models, GPT evaluates OpenAI models.</p>
        </div>
        <div className="limitation">
          <p><strong>Single framework tested.</strong> No comparison with ReAct, Step-Back, or other structured approaches.</p>
        </div>
      </section>
    </>
  );
}
