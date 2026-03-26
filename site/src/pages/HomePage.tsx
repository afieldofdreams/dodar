import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="container">
          <h1>DODAR</h1>
          <p className="subtitle">
            A structured reasoning framework for AI agents, adapted from aviation
            Crew Resource Management. Five phases. Explicit gates. Auditable decisions.
          </p>
          <div className="hero-stat">
            <span className="number">
              Does reasoning structure shape failure, not just accuracy?
            </span>
            <span className="label">
              Seven prompting frameworks compared across 100 established benchmark tasks,
              controlling for compute at prompt, output, and truncation levels.
            </span>
          </div>
          <div className="btn-group">
            <Link to="/framework" className="btn btn-primary">Learn the framework</Link>
            <Link to="/research" className="btn btn-secondary">Read the research</Link>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-header">
            <h2>Five phases, five gates</h2>
            <p>
              DODAR prevents the reasoning failures that LLMs share with humans
              under pressure: premature anchoring, option narrowing, and treating
              decisions as final.
            </p>
          </div>
          <div className="phases">
            <div className="phase">
              <div className="phase-number">Phase 1</div>
              <h3>Diagnose</h3>
              <p>Hold diagnosis open. List competing hypotheses. Surface assumptions. Challenge the first answer.</p>
            </div>
            <div className="phase">
              <div className="phase-number">Phase 2</div>
              <h3>Options</h3>
              <p>Generate distinct alternatives. Name core tensions. Quantify opportunity costs.</p>
            </div>
            <div className="phase">
              <div className="phase-number">Phase 3</div>
              <h3>Decide</h3>
              <p>Commit with transparent reasoning. Justify against alternatives. State confidence levels.</p>
            </div>
            <div className="phase">
              <div className="phase-number">Phase 4</div>
              <h3>Action</h3>
              <p>Concrete, sequenced steps. Identify dependencies. Distinguish reversible from irreversible.</p>
            </div>
            <div className="phase">
              <div className="phase-number">Phase 5</div>
              <h3>Review</h3>
              <p>Identify failure modes. Validate assumptions. Specify conditions for abandoning the plan.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section section-alt">
        <div className="container">
          <div className="section-header">
            <h2>Quick start</h2>
          </div>
          <div className="code-block">
            <span className="code-label">Install</span>
            <pre><code>pip install dodar</code></pre>
          </div>
          <div className="code-block">
            <span className="code-label">Usage</span>
            <pre><code>{`from dodar import DODAR

dodar = DODAR(model="gpt-4.1-mini")
result = dodar.analyze("Your scenario here...")

# Structured access to each reasoning phase
result.diagnosis.hypotheses       # Ranked competing causes
result.options.alternatives       # Distinct paths with trade-offs
result.decision.recommendation    # The call + justification
result.action.steps               # Sequenced implementation plan
result.review.failure_modes       # Self-critique`}</code></pre>
          </div>
          <div style={{ textAlign: "center", marginTop: "2rem" }}>
            <Link to="/framework" className="btn btn-primary">Full SDK documentation</Link>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-header">
            <h2>Phase 2: Rigorous benchmark evaluation</h2>
            <p>
              Moving beyond custom scenarios. 100 tasks from established benchmarks
              (MedQA, MMLU, GSM8K, BIG-Bench Hard, ARC-Challenge) with ground-truth
              answers and automated scoring.
            </p>
          </div>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-value">100</div>
              <div className="stat-label">Benchmark tasks with ground truth</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">7</div>
              <div className="stat-label">Prompting conditions (A-G)</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">7</div>
              <div className="stat-label">Models across 4 capability tiers</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">3</div>
              <div className="stat-label">Compute control layers</div>
            </div>
          </div>

          <h3 style={{ marginTop: "2rem" }}>Seven experimental conditions</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Condition</th>
                <th>What it controls</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>A</td><td>Baseline (no prompt)</td><td>Accuracy floor</td></tr>
              <tr><td>B</td><td>Zero-Shot CoT (token-matched)</td><td>Same tokens as PGR, no structure</td></tr>
              <tr><td>G</td><td>Few-Shot CoT (worked example)</td><td>Information density without phase gates</td></tr>
              <tr><td>C</td><td>Phase-Gated Reasoning (PGR)</td><td>The framework under test</td></tr>
              <tr><td>F</td><td>Shuffled-Phase PGR</td><td>Same phases, different order</td></tr>
              <tr><td>D</td><td>ReAct (Closed-Book)</td><td>Iterative reasoning loops</td></tr>
              <tr><td>E</td><td>Step-Back Prompting</td><td>Abstraction-first reasoning</td></tr>
            </tbody>
          </table>

          <div style={{ textAlign: "center", marginTop: "2rem" }}>
            <Link to="/research" className="btn btn-secondary">Explore the full protocol</Link>
          </div>
        </div>
      </section>

      <section className="section section-alt">
        <div className="container">
          <div className="section-header">
            <h2>The core question</h2>
            <p>
              When a structured framework improves LLM performance, what is doing the work:
              the architecture, the additional tokens, or the richer information content?
            </p>
          </div>
          <div className="card-grid">
            <div className="card">
              <h3>Compute control</h3>
              <p>
                Zero-Shot CoT (B) is token-matched to PGR (C) within 3%. Same input
                compute, different structure. Three independent tests: prompt matching,
                output-token regression, and forced truncation.
              </p>
            </div>
            <div className="card">
              <h3>Information density control</h3>
              <p>
                Few-Shot CoT (G) provides a worked reasoning example — matching PGR's
                information density without phase gates. If PGR beats a longer, richer
                prompt, structure is doing the work.
              </p>
            </div>
            <div className="card">
              <h3>Sequence control</h3>
              <p>
                Shuffled PGR (F) uses the same five phases with identical instructions
                but in randomised order. Tests whether DODAR's specific sequence matters
                or if any labelled sections suffice.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-header">
            <h2>Help expand the research</h2>
            <p>
              The protocol is designed for independent replication. All tasks, prompts,
              and analysis code are open-source.
            </p>
          </div>
          <div className="card-grid">
            <div className="card">
              <h3>Replicate the benchmark</h3>
              <p>
                Run the 100-task benchmark on your own models. The harness handles
                prompt assembly, answer extraction, and correctness checking automatically.
              </p>
            </div>
            <div className="card">
              <h3>Classify errors</h3>
              <p>
                The primary contribution is the error taxonomy. Help classify incorrect
                responses into seven failure categories using the blinded scoring protocol.
              </p>
            </div>
            <div className="card">
              <h3>Add conditions</h3>
              <p>
                Test additional frameworks (Tree-of-Thought, Self-Discover, OODA) using
                the same task set and analysis pipeline.
              </p>
            </div>
          </div>
          <div style={{ textAlign: "center", marginTop: "1.5rem" }}>
            <a href="https://github.com/afieldofdreams/dodar/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener noreferrer" className="btn btn-primary">
              Contributing guide
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
