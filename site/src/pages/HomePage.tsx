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
              GPT-4.1 Mini + DODAR pipeline scores 104% of frontier quality at 89% lower cost
            </span>
            <span className="label">
              Empirically validated across 8 models, 10 scenarios, dual-evaluator scoring
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
            <h2>Frontier quality at small-model prices</h2>
            <p>
              Structured reasoning frameworks function as cost-efficiency multipliers.
              You don't always need a bigger model — you need better structure.
            </p>
          </div>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-value">$0.015</div>
              <div className="stat-label">GPT-4.1 Mini + pipeline per query</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">$0.142</div>
              <div className="stat-label">Opus 4.6 zero-shot per query</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">104%</div>
              <div className="stat-label">Pipeline quality vs. frontier baseline</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">$12.7K</div>
              <div className="stat-label">Monthly saving at 100K queries</div>
            </div>
          </div>
          <div style={{ textAlign: "center" }}>
            <Link to="/research" className="btn btn-secondary">Explore the full results</Link>
          </div>
        </div>
      </section>

      <section className="section section-alt">
        <div className="container">
          <div className="section-header">
            <h2>Help expand the research</h2>
            <p>
              The current benchmark covers 10 scenarios across 8 models. The findings are
              promising but the sample is small. We need help making them robust.
            </p>
          </div>
          <div className="card-grid">
            <div className="card">
              <h3>Write new scenarios</h3>
              <p>
                We need more scenarios across healthcare, finance, legal, engineering,
                and other domains to test generalisability. Each scenario needs pitfalls,
                gold standards, and DODAR discriminators.
              </p>
            </div>
            <div className="card">
              <h3>Benchmark local models</h3>
              <p>
                Run the benchmark on open-source models via Ollama — Llama, Mistral, Qwen,
                Phi, Gemma, DeepSeek. The harness supports any Ollama model out of the box.
              </p>
            </div>
            <div className="card">
              <h3>Add human evaluation</h3>
              <p>
                All scoring is currently automated. If you have domain expertise, score
                responses manually through the scoring UI to create a human baseline.
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
