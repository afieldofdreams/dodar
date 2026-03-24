import { Link } from "react-router-dom";

export default function FrameworkPage() {
  return (
    <>
      <div className="container">
        <section style={{ padding: "3rem 0 1rem" }}>
          <h1>The DODAR Framework</h1>
        <p style={{ fontSize: "1.125rem", color: "var(--text-light)", maxWidth: 640 }}>
          DODAR is a five-phase structured reasoning framework developed for
          aviation Crew Resource Management. It was designed for cockpit
          environments where premature action under uncertainty leads to fatal
          outcomes. The same structural principles transfer to language models.
        </p>
      </section>

      <section className="section">
        <h2>The five phases</h2>

        <div className="phase-detail">
          <div className="gate-label">Phase 1 — Gate: Hold diagnosis open</div>
          <h3>Diagnose</h3>
          <p>
            List competing hypotheses rather than anchoring on the most obvious
            explanation. Surface assumptions. Identify what information is missing.
            Challenge the first answer that presents itself.
          </p>
          <ul>
            <li>Enumerate 3+ competing root cause hypotheses</li>
            <li>Rank by plausibility, not by order of discovery</li>
            <li>Surface latent assumptions that could bias the diagnosis</li>
            <li>Map the unknowns — what information would change the diagnosis?</li>
            <li>Consider polycontribution — multiple causes interacting</li>
          </ul>
          <p><strong>What this prevents:</strong> Premature anchoring. Models (and humans) tend to commit to the first plausible explanation and stop searching.</p>
        </div>

        <div className="phase-detail">
          <div className="gate-label">Phase 2 — Gate: Force genuine trade-offs</div>
          <h3>Options</h3>
          <p>
            Generate at least four genuinely distinct alternatives. Name the core
            tensions and trade-offs explicitly. Quantify opportunity costs where
            possible. Include unconventional or counterintuitive options.
          </p>
          <ul>
            <li>Generate 4+ genuinely distinct alternatives (not minor variations)</li>
            <li>Name the core tension — the fundamental trade-off the decision hinges on</li>
            <li>Separate different types of risk (financial, reputational, technical, etc.)</li>
            <li>Quantify opportunity costs for each path</li>
            <li>Identify hidden stakeholders and constraints</li>
          </ul>
          <p><strong>What this prevents:</strong> Option narrowing. Models collapse to a single recommendation without acknowledging that other valid paths exist.</p>
        </div>

        <div className="phase-detail">
          <div className="gate-label">Phase 3 — Gate: Commit with transparency</div>
          <h3>Decide</h3>
          <p>
            Commit to a recommendation with transparent reasoning. Justify the
            choice against specific alternatives. State binding constraints,
            confidence levels, and the conditions under which the decision should
            be revisited.
          </p>
          <ul>
            <li>Make a clear recommendation</li>
            <li>Justify against each rejected alternative (not just the chosen one)</li>
            <li>State binding constraints that shaped the decision</li>
            <li>Declare confidence level and what would change your mind</li>
            <li>Quantify the opportunity cost of the chosen path</li>
          </ul>
          <p><strong>What this prevents:</strong> Unjustified confidence. Models present decisions without reasoning or without acknowledging uncertainty.</p>
        </div>

        <div className="phase-detail">
          <div className="gate-label">Phase 4 — Gate: Concrete sequencing</div>
          <h3>Action</h3>
          <p>
            Translate the decision into concrete, sequenced steps. Identify
            dependencies and blockers. Distinguish reversible from irreversible
            actions. Specify timelines and resource requirements.
          </p>
          <ul>
            <li>Define specific implementation steps with ordering</li>
            <li>Identify dependencies between steps</li>
            <li>Mark which actions are reversible vs. irreversible</li>
            <li>Specify timelines and resource requirements</li>
            <li>Identify blockers and prerequisites</li>
          </ul>
          <p><strong>What this prevents:</strong> Vague next steps. "Monitor the situation" is not an action plan.</p>
        </div>

        <div className="phase-detail">
          <div className="gate-label">Phase 5 — Gate: Self-critique</div>
          <h3>Review</h3>
          <p>
            Identify at least three failure modes with detection methods and
            contingency plans. Validate assumptions made during earlier phases.
            Specify conditions for abandoning the plan entirely.
          </p>
          <ul>
            <li>Identify 3+ failure modes with triggers and detection methods</li>
            <li>Specify contingency plans for each failure mode</li>
            <li>Audit assumptions from earlier phases — are they still valid?</li>
            <li>Define abort conditions — when should the plan be abandoned?</li>
            <li>Set review checkpoints at specific milestones</li>
          </ul>
          <p><strong>What this prevents:</strong> Absent self-critique. Models treat decisions as final without considering what could go wrong.</p>
        </div>
      </section>
      </div>

      <section className="section section-alt">
        <div className="container">
        <h2>Implementation: Single prompt vs. Pipeline</h2>
        <p>DODAR can be implemented in two ways, with significantly different performance characteristics.</p>

        <div className="comparison">
          <div className="card">
            <h3>Single prompt</h3>
            <p>All five phases specified in one system instruction. The model works through them sequentially in a single response.</p>
            <div className="code-block">
              <pre><code>{`from dodar import DODAR

dodar = DODAR(model="gpt-4.1-mini")
result = dodar.analyze(scenario)`}</code></pre>
            </div>
            <ul style={{ fontSize: "0.875rem" }}>
              <li>Single API call — lower latency</li>
              <li>Lower token usage</li>
              <li>Phases compete for model attention</li>
              <li>Works well for mid-tier and frontier models</li>
            </ul>
          </div>
          <div className="card">
            <h3>Pipeline (recommended)</h3>
            <p>Each phase runs as a separate model call with specialised personas and accumulated context.</p>
            <div className="code-block">
              <pre><code>{`from dodar import DODAR

dodar = DODAR(
    model="gpt-4.1-mini",
    mode="pipeline"
)
result = dodar.analyze(scenario)`}</code></pre>
            </div>
            <ul style={{ fontSize: "0.875rem" }}>
              <li>5 sequential API calls — higher latency</li>
              <li>Higher token usage (context accumulates)</li>
              <li>Each phase gets dedicated model attention</li>
              <li>Largest quality gains, especially for small models</li>
            </ul>
          </div>
        </div>

        <div className="finding-highlight">
          <p>
            <strong>Research finding:</strong> The pipeline consistently outperforms the single
            prompt. GPT-4.1 Mini with pipeline scores 4.80/5.0, compared to 4.63 with
            single prompt. The pipeline also reduces output variance, making results more
            consistent. <Link to="/research">Read the full analysis.</Link>
          </p>
        </div>
        </div>
      </section>

      <div className="container">
      <section className="section">
        <h2>Agent integration</h2>
        <p>DODAR integrates into AI agent workflows as a decision-making layer.</p>

        <div className="code-block">
          <span className="code-label">Agent decision loop</span>
          <pre><code>{`from dodar import DODAR

dodar = DODAR(model="gpt-4.1-mini", mode="pipeline")

async def agent_decision(context: str) -> dict:
    result = await dodar.analyze_async(context)

    if result.decision.confidence == "low":
        return {
            "action": "gather_info",
            "unknowns": result.diagnosis.unknowns,
        }

    return {
        "action": "execute",
        "steps": result.action.steps,
        "abort_if": result.review.abort_conditions,
    }`}</code></pre>
        </div>

        <h3>Supported models</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Models</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Anthropic</td><td>claude-opus-4-6, claude-sonnet-4-5, claude-haiku-4-5</td></tr>
            <tr><td>OpenAI</td><td>gpt-5.4, gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano</td></tr>
            <tr><td>Google</td><td>gemini-2.0-flash</td></tr>
            <tr><td>Local (Ollama)</td><td>Any model running on localhost:11434</td></tr>
          </tbody>
        </table>
      </section>
      </div>
    </>
  );
}
