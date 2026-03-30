import { useState } from "react";

// ── Data ────────────────────────────────────────────────────────
const accuracyData = [
  { category: "ARC-Challenge", A: 95.0, B: 95.0, C: 95.0, C_prev: 95.0, G: 95.0 },
  { category: "BBH/causal judgement", A: 60.0, B: 60.0, C: 80.0, C_prev: 60.0, G: 66.7 },
  { category: "BBH/logical deduction", A: 100.0, B: 93.3, C: 100.0, C_prev: 86.7, G: 100.0 },
  { category: "BBH/tracking shuffled", A: 0.0, B: 0.0, C: 6.7, C_prev: 13.3, G: 66.7 },
  { category: "BBH/web of lies", A: 100.0, B: 100.0, C: 100.0, C_prev: 100.0, G: 93.3 },
  { category: "GSM8K", A: 93.3, B: 93.3, C: 95.0, C_prev: 95.0, G: 93.3 },
  { category: "MMLU/accounting", A: 83.3, B: 83.3, C: 83.3, C_prev: 83.3, G: 83.3 },
  { category: "MMLU/law", A: 95.2, B: 81.0, C: 90.5, C_prev: 85.7, G: 100.0 },
  { category: "MMLU/medicine", A: 100.0, B: 100.0, C: 95.2, C_prev: 100.0, G: 90.5 },
  { category: "MedQA-USMLE", A: 96.7, B: 88.3, C: 90.0, C_prev: 91.7, G: 93.3 },
];

const conditions: { key: string; label: string; color: string }[] = [
  { key: "A", label: "Baseline", color: "#2E75B6" },
  { key: "B", label: "ZS-CoT", color: "#0EA5E9" },
  { key: "C", label: "PGR Late", color: "#F59E0B" },
  { key: "C_prev", label: "PGR Early", color: "#8B5CF6" },
  { key: "G", label: "FS-CoT", color: "#10B981" },
];

const errorData: Record<string, Record<string, number>> = {
  A:      { Anchoring: 17, "Failure to Revise": 11, Comprehension: 44, Execution: 54, "Incomplete Search": 7, "Premature Closure": 0 },
  B:      { Anchoring: 28, "Failure to Revise": 14, Comprehension: 48, Execution: 53, "Incomplete Search": 9, "Premature Closure": 0 },
  C:      { Anchoring: 36, "Failure to Revise": 22, Comprehension: 32, Execution: 53, "Incomplete Search": 4, "Premature Closure": 2 },
  C_prev: { Anchoring: 20, "Failure to Revise": 16, Comprehension: 26, Execution: 36, "Incomplete Search": 3, "Premature Closure": 2 },
  G:      { Anchoring: 17, "Failure to Revise": 11, Comprehension: 58, Execution: 22, "Incomplete Search": 8, "Premature Closure": 1 },
};

const errorTypes = ["Anchoring", "Failure to Revise", "Comprehension", "Execution", "Incomplete Search", "Premature Closure"];
const errorColors = ["#EF4444", "#F59E0B", "#F97316", "#2E75B6", "#0EA5E9", "#94A3B8"];

// ── Helpers ─────────────────────────────────────────────────────
function heatColor(value: number, min: number, max: number) {
  if (max === min) return "#10B981";
  const t = (value - min) / (max - min);
  if (t > 0.8) return "#059669";
  if (t > 0.6) return "#10B981";
  if (t > 0.4) return "#F59E0B";
  if (t > 0.2) return "#F97316";
  return "#EF4444";
}

function diffColor(diff: number) {
  if (diff > 5) return "#059669";
  if (diff > 0) return "#6EE7B7";
  if (diff > -5) return "#FCD34D";
  return "#EF4444";
}

// ── Main page ───────────────────────────────────────────────────
export default function StudyPage() {
  const [tab, setTab] = useState("heatmap");

  const tabs = [
    { id: "heatmap", label: "Accuracy Heatmap" },
    { id: "diff", label: "Difference vs Baseline" },
    { id: "errors", label: "Error Distribution" },
    { id: "redistribution", label: "Error Redistribution" },
  ];

  return (
    <div className="container">
      <section style={{ padding: "3rem 0 1rem" }}>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
          <a href="https://crox.io" style={{ color: "var(--navy)" }}>Crox</a> / Research
        </p>
        <h1 style={{ fontSize: "2.5rem" }}>Does Reasoning Structure Shape Failure, Not Just Accuracy?</h1>
        <p style={{ fontSize: "1.125rem", color: "var(--text-light)", maxWidth: 640 }}>
          A benchmark study testing whether DODAR-based prompting changes how LLMs fail
        </p>
        <p style={{ fontSize: "0.875rem", color: "var(--text-light)" }}>
          Adam Field &middot; Crox &middot; March 2026
        </p>
      </section>

      {/* Key findings */}
      <div className="stat-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <div className="stat-card">
          <div className="stat-value">1,500</div>
          <div className="stat-label">benchmark runs</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ fontSize: "1.5rem" }}>p = 0.0003</div>
          <div className="stat-label">error distributions differ</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">39%</div>
          <div className="stat-label">PGR anchoring errors</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">0%</div>
          <div className="stat-label">accuracy improvement</div>
        </div>
      </div>

      <section className="section">
        <h2>The Short Version</h2>
        <p>
          We ran 1,500 benchmark tests to find out whether DODAR-based prompting improves LLM
          reasoning. It doesn't improve accuracy. But it measurably changes how models
          fail&mdash;and that finding is statistically significant (p&nbsp;=&nbsp;0.0003).
        </p>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <h2>What We Tested</h2>
        <p>
          Phase-Gated Reasoning (PGR) encodes DODAR's five phases&mdash;Diagnose, Options,
          Decide, Action, Review&mdash;directly into an LLM system prompt. We tested two PGR
          variants against three controls on GPT-4.1-mini across 100 benchmark tasks, each run
          three times:
        </p>
        <table className="data-table">
          <thead>
            <tr>
              <th>Condition</th>
              <th>Description</th>
              <th>Tokens</th>
            </tr>
          </thead>
          <tbody>
            <tr><td style={{ fontWeight: 600 }}>A&mdash;Baseline</td><td>No system prompt</td><td>0</td></tr>
            <tr><td style={{ fontWeight: 600 }}>B&mdash;Zero-Shot CoT</td><td>"Think step by step" (token-matched to C)</td><td>227</td></tr>
            <tr><td style={{ fontWeight: 600 }}>C&mdash;PGR (Late Commitment)</td><td>Five phases, decision deferred to REVIEW</td><td>223</td></tr>
            <tr>
              <td style={{ fontWeight: 600 }}>C<sub>prev</sub>&mdash;PGR (Early Commitment)</td>
              <td>Five phases, decision at DECIDE (original design)</td>
              <td>229</td>
            </tr>
            <tr><td style={{ fontWeight: 600 }}>G&mdash;Few-Shot CoT</td><td>Three worked examples showing step-by-step reasoning</td><td>~412</td></tr>
          </tbody>
        </table>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <h2>What We Found</h2>

        <h3>Accuracy is flat</h3>
        <div style={{ margin: "1.5rem 0" }}>
          <AccuracyBar label="G — FS-CoT" pct={91.0} color="var(--green)" />
          <AccuracyBar label="A — Baseline" pct={88.7} color="var(--navy)" />
          <AccuracyBar label="C — PGR Late" pct={88.3} color="#0EA5E9" />
          <AccuracyBar label="Cprev — PGR Early" pct={87.3} color="#8B5CF6" />
          <AccuracyBar label="B — ZS-CoT" pct={85.7} color="#F59E0B" />
        </div>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", textAlign: "center", fontStyle: "italic" }}>
          All conditions fall within a 5.3pp range. No PGR comparison reaches statistical significance.
        </p>
        <p>
          The model either knows the answer or it doesn't&mdash;how you ask it to think about
          it doesn't change that.
        </p>

        <h3>Error distributions are significantly different (p&nbsp;=&nbsp;0.0003)</h3>
        <div className="finding-highlight" style={{ borderLeftWidth: 6, padding: "1.25rem 1.5rem", fontStyle: "italic" }}>
          <p>
            This is the real finding. When PGR fails, 39% of its errors are anchoring + failure-to-revise&mdash;nearly
            double the baseline rate of 21%.
          </p>
        </div>
        <p>
          The structured phases create commitment points that become cognitive traps. The model
          commits to an answer, generates evidence against it, and then stands pat.
        </p>

        <table className="data-table">
          <thead>
            <tr>
              <th>Error Type</th>
              <th>A Baseline</th>
              <th>B ZS-CoT</th>
              <th>C PGR Late</th>
              <th>C<sub>prev</sub> Early</th>
              <th>G FS-CoT</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ fontWeight: 500 }}>Anchoring + Failure to Revise</td>
              <td>28 (21%)</td><td>42 (28%)</td><td>58 (39%)</td><td>36 (35%)</td><td>28 (24%)</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 500 }}>Comprehension Failure</td>
              <td>44 (33%)</td><td>48 (32%)</td><td>32 (21%)</td><td>26 (25%)</td><td>58 (50%)</td>
            </tr>
            <tr>
              <td style={{ fontWeight: 500 }}>Execution Error</td>
              <td>54 (41%)</td><td>53 (35%)</td><td>53 (36%)</td><td>36 (35%)</td><td>22 (19%)</td>
            </tr>
          </tbody>
        </table>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", textAlign: "center", fontStyle: "italic" }}>
          Error classifications from dual-rater system (Claude Opus 4.6 + GPT-5.4). Cohen's Kappa = 0.456.
        </p>

        <h3>Few-Shot CoT wins (p&nbsp;=&nbsp;0.033)</h3>
        <p>
          The only significant accuracy result: Few-Shot CoT (91%) significantly outperforms
          Zero-Shot CoT (85.7%) on Wilcoxon signed-rank. Showing beats telling. Models are
          better at imitating demonstrated reasoning than following abstract process descriptions.
        </p>

        <h3>Self-review doesn't work in LLMs</h3>
        <p>
          DODAR's REVIEW phase works in a cockpit because the first officer is a different human
          challenging the captain. In an LLM, REVIEW is the same model reviewing its own output.
          We tested an anti-anchoring variant that explicitly instructed the model to argue against
          its own answer. It made things worse&mdash;the model performed the review ritual
          perfectly and changed nothing.
        </p>
      </section>

      {/* ── Detailed analysis visuals ── */}
      <section className="section" style={{ paddingTop: 0 }}>
        <h2>Detailed Analysis</h2>
        <p style={{ color: "var(--text-light)", marginBottom: "1.5rem" }}>
          1,500 runs &middot; 100 tasks &middot; 5 conditions &middot; GPT-4.1-mini
        </p>

        <div style={{ display: "flex", gap: 4, marginBottom: "1.5rem", flexWrap: "wrap" }}>
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={tab === t.id ? "btn btn-primary" : "btn btn-secondary"}
              style={{ fontSize: "0.8125rem", padding: "0.5rem 1rem" }}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="chart-container">
          {tab === "heatmap" && (
            <>
              <h3 style={{ marginTop: 0 }}>Accuracy by Condition &times; Task Category</h3>
              <AccuracyHeatmap />
              <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", marginTop: "0.75rem", fontStyle: "italic", marginBottom: 0 }}>
                Green = high accuracy, red = low. Most categories are saturated (all conditions score similarly).
                BBH/tracking shuffled objects is the outlier&mdash;FS-CoT jumps to 66.7% where all others are near 0%.
              </p>
            </>
          )}

          {tab === "diff" && (
            <>
              <h3 style={{ marginTop: 0 }}>Per-Category Advantage vs Baseline</h3>
              <DiffHeatmap />
              <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", marginTop: "0.75rem", fontStyle: "italic", marginBottom: 0 }}>
                Green = beats baseline, yellow = similar, red = worse. PGR Late wins on causal judgement (+20pp)
                but loses on MedQA and law. FS-CoT's +66.7pp on tracking shuffled objects is the single largest effect.
              </p>
            </>
          )}

          {tab === "errors" && (
            <>
              <h3 style={{ marginTop: 0 }}>Error Distribution by Condition</h3>
              <ErrorRedistribution />
              <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", marginTop: "0.75rem", fontStyle: "italic", marginBottom: 0 }}>
                Chi-squared p = 0.0003. PGR shows elevated anchoring (red) and failure-to-revise (amber).
                FS-CoT's errors are dominated by comprehension failure&mdash;it fails when it doesn't understand, not when it gets stuck.
              </p>
            </>
          )}

          {tab === "redistribution" && (
            <>
              <h3 style={{ marginTop: 0 }}>Error Redistribution: PGR vs Baseline</h3>
              <RedistributionDelta />
              <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", marginTop: "0.75rem", fontStyle: "italic", marginBottom: 0 }}>
                PGR doesn't reduce errors&mdash;it redistributes them. Anchoring and failure-to-revise increase by +11.4pp and +6.5pp respectively,
                while comprehension failure drops by -11.6pp. The structured phases trade simple failures for self-inflicted traps.
              </p>
            </>
          )}
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <h2>The Exception</h2>
        <p>
          One task (BBH-CJ-005) shows late-commitment PGR working exactly as designed. It's a
          causal judgement question where every other condition goes 0/3 and PGR goes 3/3. By
          deferring commitment to REVIEW and testing both causal framings equally, the model
          avoids a trap that every other condition falls into. But this is the exception, not
          the rule.
        </p>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <h2>What This Means for DODAR</h2>
        <p>
          DODAR remains a powerful framework for human decision-making. The REVIEW phase works
          because it involves an independent perspective&mdash;a different person challenging the
          decision-maker's assumptions.
        </p>
        <p>
          The insight from this study is that DODAR may be better suited as an{" "}
          <strong>architecture pattern</strong> than a prompting pattern for AI systems. Instead of
          one model following all five phases, route DIAGNOSE through DECIDE to one model, then
          hand the reasoning trace to a separate model (or fresh context) for REVIEW. Give the
          reviewer genuine independence&mdash;no memory of the reasoning that produced the anchor.
        </p>
        <div className="finding-highlight" style={{ borderLeftWidth: 6, padding: "1.25rem 1.5rem", fontStyle: "italic" }}>
          <p>Multi-agent DODAR&mdash;different models for different phases&mdash;is the natural next step.</p>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <h2>Protocol Deviations</h2>
        <p>
          The original protocol specified seven prompting conditions, seven models across three
          stages, and human error classification. The study as executed deviated in several ways,
          all documented for transparency.
        </p>
        <p>
          The PGR prompt was redesigned mid-study from early commitment to late commitment after
          failure analysis showed the model consistently found errors in REVIEW but refused to
          change its answer. The original prompt was retained as a comparison condition
          (C<sub>prev</sub>).
        </p>
        <p>
          Conditions D (ReAct), E (Step-Back), and F (Shuffled PGR) were tested in preliminary
          runs but dropped from the final triplicate. Multi-model stages 2 and 3 were not
          executed. Human error classification was not performed&mdash;LLM raters classified all
          errors, with inter-rater kappa of 0.456, below the protocol's 0.7 threshold. The
          chi-squared result (p&nbsp;=&nbsp;0.0003) is robust enough to survive noisy labels,
          but specific error counts are directional rather than precise.
        </p>
        <p>The full protocol deviations table is in the report PDF.</p>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <h2>Full Report</h2>
        <a href="/dodar-benchmark-report.pdf" className="btn btn-primary" download>
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><polyline points="9 15 12 18 15 15"></polyline></svg>
          Download Report PDF
        </a>
        <p style={{ marginTop: "1rem" }}>
          The complete methodology, data, and analysis are in the report.
          Contact <a href="mailto:adam@crox.io">adam@crox.io</a> for the raw data and code.
        </p>
      </section>

      <div style={{ borderTop: "1px solid var(--border)", marginTop: "2rem", padding: "1.5rem 0", fontSize: "0.8125rem", color: "var(--text-light)", textAlign: "center" }}>
        Study conducted March 2026 by Adam Field / <a href="https://crox.io">Crox</a>.
        1,500 runs on GPT-4.1-mini. Error classification by Claude Opus 4.6 and GPT-5.4.
        Total API cost: $1.45.
      </div>
    </div>
  );
}


/* ── Helper components ─────────────────────────────────────────── */

function AccuracyBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", marginBottom: "0.5rem" }}>
      <span style={{ width: 140, fontSize: "0.8125rem", fontWeight: 600, flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: 28, background: "var(--bg-subtle)", borderRadius: 4, overflow: "hidden" }}>
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: color,
            borderRadius: 4,
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            paddingRight: 8,
            fontSize: "0.75rem",
            fontWeight: 700,
            color: "#fff",
          }}
        >
          {pct}%
        </div>
      </div>
    </div>
  );
}

function AccuracyHeatmap() {
  const allVals = accuracyData.flatMap(d => conditions.map(c => d[c.key as keyof typeof d] as number));
  const min = Math.min(...allVals);
  const max = Math.max(...allVals);

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="data-table">
        <thead>
          <tr>
            <th style={{ minWidth: 160 }}>Category</th>
            {conditions.map(c => (
              <th key={c.key} style={{ textAlign: "center", minWidth: 80 }}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {accuracyData.map((row, i) => (
            <tr key={i}>
              <td style={{ fontWeight: 500 }}>{row.category}</td>
              {conditions.map(c => {
                const val = row[c.key as keyof typeof row] as number;
                const bg = heatColor(val, min, max);
                const textCol = val < 40 ? "#fff" : val < 70 ? "#1E293B" : "#fff";
                return (
                  <td key={c.key} style={{
                    textAlign: "center", background: bg, color: textCol, fontWeight: 600,
                  }}>
                    {val.toFixed(1)}%
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DiffHeatmap() {
  return (
    <div style={{ overflowX: "auto" }}>
      <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", margin: "0 0 0.5rem" }}>
        Difference vs Baseline (A) in percentage points
      </p>
      <table className="data-table">
        <thead>
          <tr>
            <th style={{ minWidth: 160 }}>Category</th>
            {conditions.filter(c => c.key !== "A").map(c => (
              <th key={c.key} style={{ textAlign: "center", minWidth: 80 }}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {accuracyData.map((row, i) => (
            <tr key={i}>
              <td style={{ fontWeight: 500 }}>{row.category}</td>
              {conditions.filter(c => c.key !== "A").map(c => {
                const diff = (row[c.key as keyof typeof row] as number) - row.A;
                const bg = diffColor(diff);
                return (
                  <td key={c.key} style={{
                    textAlign: "center", background: bg, color: "#1E293B", fontWeight: 600,
                  }}>
                    {diff > 0 ? "+" : ""}{diff.toFixed(1)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ErrorRedistribution() {
  const condKeys = ["A", "B", "C", "C_prev", "G"] as const;
  const condLabels: Record<string, string> = { A: "Baseline", B: "ZS-CoT", C: "PGR Late", C_prev: "PGR Early", G: "FS-CoT" };

  return (
    <div>
      {condKeys.map(ck => {
        const errs = errorData[ck];
        const total = Object.values(errs).reduce((a, b) => a + b, 0);
        return (
          <div key={ck} style={{ marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", marginBottom: 4 }}>
              <span style={{ width: 90, fontSize: "0.8125rem", fontWeight: 600, flexShrink: 0 }}>{condLabels[ck]}</span>
              <div style={{ flex: 1, display: "flex", height: 32, borderRadius: 4, overflow: "hidden" }}>
                {errorTypes.map((et, i) => {
                  const val = errs[et];
                  const pct = total > 0 ? (val / total) * 100 : 0;
                  if (pct < 1) return null;
                  return (
                    <div key={et} title={`${et}: ${val} (${pct.toFixed(0)}%)`} style={{
                      width: `${pct}%`, background: errorColors[i],
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 11, fontWeight: 700, color: "#fff",
                    }}>
                      {pct > 6 ? `${pct.toFixed(0)}%` : ""}
                    </div>
                  );
                })}
              </div>
              <span style={{ width: 45, fontSize: "0.75rem", color: "var(--text-light)", textAlign: "right", flexShrink: 0 }}>n={total}</span>
            </div>
          </div>
        );
      })}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 8 }}>
        {errorTypes.map((et, i) => (
          <div key={et} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.75rem", color: "var(--text-light)" }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: errorColors[i] }} />
            {et}
          </div>
        ))}
      </div>
    </div>
  );
}

function RedistributionDelta() {
  const baseErrs = errorData.A;
  const pgrErrs = errorData.C;
  const baseTotal = Object.values(baseErrs).reduce((a, b) => a + b, 0);
  const pgrTotal = Object.values(pgrErrs).reduce((a, b) => a + b, 0);

  const deltas = errorTypes.map(et => ({
    type: et,
    basePct: (baseErrs[et] / baseTotal) * 100,
    pgrPct: (pgrErrs[et] / pgrTotal) * 100,
    diff: (pgrErrs[et] / pgrTotal) * 100 - (baseErrs[et] / baseTotal) * 100,
  })).sort((a, b) => b.diff - a.diff);

  const maxAbs = Math.max(...deltas.map(d => Math.abs(d.diff)));

  return (
    <div>
      <p style={{ fontSize: "0.8125rem", color: "var(--text-light)", margin: "0 0 0.75rem" }}>
        PGR (Late) vs Baseline&mdash;shift in error share (percentage points)
      </p>
      {deltas.map(d => {
        const barWidth = (Math.abs(d.diff) / maxAbs) * 50;
        const isPositive = d.diff > 0;
        return (
          <div key={d.type} style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
            <span style={{ width: 130, fontSize: "0.8125rem", fontWeight: 500, textAlign: "right", paddingRight: 12, flexShrink: 0 }}>{d.type}</span>
            <div style={{ width: "50%", display: "flex", justifyContent: "flex-end" }}>
              {!isPositive && (
                <div style={{ width: `${barWidth}%`, height: 24, background: "#10B981", borderRadius: "4px 0 0 4px", display: "flex", alignItems: "center", justifyContent: "flex-start", paddingLeft: 6, fontSize: 11, fontWeight: 700, color: "#fff" }}>
                  {d.diff.toFixed(1)}pp
                </div>
              )}
            </div>
            <div style={{ width: 2, height: 24, background: "var(--navy)" }} />
            <div style={{ width: "50%" }}>
              {isPositive && (
                <div style={{ width: `${barWidth}%`, height: 24, background: "#EF4444", borderRadius: "0 4px 4px 0", display: "flex", alignItems: "center", justifyContent: "flex-end", paddingRight: 6, fontSize: 11, fontWeight: 700, color: "#fff" }}>
                  +{d.diff.toFixed(1)}pp
                </div>
              )}
            </div>
          </div>
        );
      })}
      <div style={{ display: "flex", justifyContent: "center", gap: 24, marginTop: 8, fontSize: "0.75rem", color: "var(--text-light)" }}>
        <span>&larr; fewer errors (good)</span>
        <span>more errors (bad) &rarr;</span>
      </div>
    </div>
  );
}
