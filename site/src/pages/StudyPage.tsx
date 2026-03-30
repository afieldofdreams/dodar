export default function StudyPage() {
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

        {/* Stacked error distribution bars */}
        <div style={{ margin: "2rem 0" }}>
          <StackedErrorBar
            label="A Baseline"
            segments={[
              { pct: 12.8, color: "var(--red, #dc2626)", label: "13%" },
              { pct: 33.1, color: "#F59E0B", label: "33%" },
              { pct: 40.6, color: "var(--navy)", label: "41%" },
              { pct: 8.3, color: "#8B5CF6", label: "8%" },
              { pct: 5.3, color: "#0EA5E9", label: "" },
            ]}
          />
          <StackedErrorBar
            label="C PGR Late"
            segments={[
              { pct: 24.2, color: "var(--red, #dc2626)", label: "24%" },
              { pct: 21.5, color: "#F59E0B", label: "21%" },
              { pct: 35.6, color: "var(--navy)", label: "36%" },
              { pct: 14.8, color: "#8B5CF6", label: "15%" },
              { pct: 4, color: "#0EA5E9", label: "" },
            ]}
          />
          <StackedErrorBar
            label="G FS-CoT"
            segments={[
              { pct: 14.5, color: "var(--red, #dc2626)", label: "15%" },
              { pct: 49.6, color: "#F59E0B", label: "50%" },
              { pct: 18.8, color: "var(--navy)", label: "19%" },
              { pct: 9.4, color: "#8B5CF6", label: "9%" },
              { pct: 7.7, color: "#0EA5E9", label: "" },
            ]}
          />
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginTop: "0.75rem", fontSize: "0.75rem", color: "var(--text-light)" }}>
            <LegendItem color="var(--red, #dc2626)" label="Anchoring" />
            <LegendItem color="#F59E0B" label="Comprehension" />
            <LegendItem color="var(--navy)" label="Execution" />
            <LegendItem color="#8B5CF6" label="Failure to Revise" />
            <LegendItem color="#0EA5E9" label="Other" />
          </div>
        </div>

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


/* ---- Helper components ---- */

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

function StackedErrorBar({
  label,
  segments,
}: {
  label: string;
  segments: { pct: number; color: string; label: string }[];
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", marginBottom: "0.375rem" }}>
      <span style={{ width: 140, fontSize: "0.8125rem", fontWeight: 600, flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, display: "flex", height: 28, borderRadius: 4, overflow: "hidden" }}>
        {segments.map((seg, i) => (
          <div
            key={i}
            style={{
              width: `${seg.pct}%`,
              background: seg.color,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.6875rem",
              fontWeight: 600,
              color: "#fff",
            }}
          >
            {seg.label}
          </div>
        ))}
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
      <span style={{ width: 10, height: 10, borderRadius: 2, background: color, flexShrink: 0 }} />
      {label}
    </span>
  );
}
