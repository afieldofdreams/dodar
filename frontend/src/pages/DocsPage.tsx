export default function DocsPage() {
  return (
    <div style={{ maxWidth: 800 }}>
      <h1 style={{ fontSize: "1.8rem", margin: "0 0 0.5rem", fontWeight: 700, letterSpacing: "-0.03em" }}>
        DODAR Framework
      </h1>
      <p style={{ color: "var(--text-secondary)", margin: "0 0 2rem", fontSize: "0.95rem" }}>
        Structured reasoning for AI agents — adapted from aviation Crew Resource Management.
      </p>

      {/* The five phases */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "2.5rem" }}>
        {PHASES.map((phase) => (
          <div
            key={phase.name}
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: "1.25rem",
              borderLeft: `3px solid ${phase.color}`,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
              <span style={{ fontSize: "1rem" }}>{phase.icon}</span>
              <h3 style={{ margin: 0, fontSize: "1rem", color: phase.color }}>{phase.name}</h3>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "auto" }}>
                {phase.gate}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
              {phase.description}
            </p>
          </div>
        ))}
      </div>

      {/* When to use */}
      <Section title="When to Use DODAR">
        <ul style={listStyle}>
          <li>The diagnosis is ambiguous — multiple plausible explanations exist</li>
          <li>The decision has real trade-offs — multiple valid paths with different risk/reward profiles</li>
          <li>The stakes are meaningful — consequences are hard or impossible to reverse</li>
          <li>You need to trust the reasoning, not just the answer</li>
        </ul>
      </Section>

      {/* SDK */}
      <Section title="Python SDK">
        <pre style={codeStyle}>
{`pip install dodar`}
        </pre>
        <pre style={{ ...codeStyle, marginTop: "0.75rem" }}>
{`from dodar import DODAR

dodar = DODAR(model="claude-sonnet-4-5")
result = dodar.analyze("Your scenario here...")

# Structured access to each reasoning phase
result.diagnosis.hypotheses       # Ranked competing causes
result.options.alternatives       # Distinct paths with trade-offs
result.options.core_tension       # The fundamental trade-off
result.decision.recommendation    # The call + justification
result.decision.confidence        # Low / medium / high
result.action.steps               # Sequenced implementation
result.action.reversible_steps    # Which steps can be undone
result.review.failure_modes       # Self-critique
result.review.abort_conditions    # When to abandon the plan`}
        </pre>
      </Section>

      {/* Agent integration */}
      <Section title="Agent Integration">
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: "0.75rem" }}>
          Use DODAR as a reasoning step in your agent pipeline:
        </p>
        <pre style={codeStyle}>
{`from dodar import DODAR

dodar = DODAR(model="gpt-4o")

async def agent_decision(context: str) -> dict:
    """Let the agent reason through a decision using DODAR."""
    result = await dodar.analyze_async(context)

    # Use structured output in your agent logic
    if result.decision.confidence == "low":
        # Ask for more information before acting
        return {"action": "gather_info", "unknowns": result.diagnosis.unknowns}

    # Execute the recommended action plan
    return {
        "action": "execute",
        "steps": result.action.steps,
        "abort_if": result.review.abort_conditions,
    }`}
        </pre>
      </Section>

      {/* Supported models */}
      <Section title="Supported Models">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
          {MODEL_GROUPS.map((group) => (
            <div
              key={group.provider}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                padding: "0.75rem 1rem",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                {group.provider}
              </div>
              {group.models.map((m) => (
                <div key={m} style={{ fontSize: "0.85rem", color: "var(--text-secondary)", padding: "0.15rem 0" }}>
                  {m}
                </div>
              ))}
            </div>
          ))}
        </div>
      </Section>

      {/* Links */}
      <div style={{ marginTop: "2rem", padding: "1.25rem", background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 12 }}>
        <div style={{ display: "flex", gap: "2rem", fontSize: "0.85rem" }}>
          <a href="https://github.com/afieldofdreams/dodar" target="_blank" rel="noopener" style={{ color: "var(--accent)" }}>
            GitHub Repository ↗
          </a>
          <a href="https://github.com/afieldofdreams/dodar/blob/main/DODAR.md" target="_blank" rel="noopener" style={{ color: "var(--accent)" }}>
            Full Documentation ↗
          </a>
          <a href="https://github.com/afieldofdreams/dodar/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener" style={{ color: "var(--accent)" }}>
            Contributing Guide ↗
          </a>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "2rem" }}>
      <h2 style={{ fontSize: "1.15rem", marginBottom: "0.75rem", fontWeight: 600 }}>{title}</h2>
      {children}
    </div>
  );
}

const PHASES = [
  {
    name: "Diagnose",
    icon: "🔍",
    color: "#f97316",
    gate: "Hold diagnosis open",
    description: "Resist premature pattern-matching. List 3+ competing hypotheses. Challenge your anchoring. Surface latent assumptions. Map unknowns. Consider polycontribution.",
  },
  {
    name: "Options",
    icon: "⚖️",
    color: "#06b6d4",
    gate: "Force genuine trade-offs",
    description: "Enumerate 4+ genuinely distinct alternatives. Name the core tension. Separate risk types. Test assumptions for each option. Quantify opportunity costs. Surface hidden constraints.",
  },
  {
    name: "Decide",
    icon: "✓",
    color: "#8b5cf6",
    gate: "Commit with transparency",
    description: "Make a clear recommendation. Justify against each alternative. Name binding constraints. State your confidence level and what would change your mind.",
  },
  {
    name: "Action",
    icon: "→",
    color: "#22c55e",
    gate: "Concrete sequencing",
    description: "Define specific steps with dependencies. Identify which are reversible and which are not. Note blockers and prerequisites. Include timeline and resource estimates.",
  },
  {
    name: "Review",
    icon: "↻",
    color: "#ef4444",
    gate: "Self-critique",
    description: "Identify 3+ failure modes with triggers and detection methods. Audit unvalidated assumptions. Specify conditions for abandoning the plan.",
  },
];

const MODEL_GROUPS = [
  {
    provider: "Anthropic",
    models: ["claude-opus-4-6", "claude-sonnet-4-5", "claude-haiku-4-5"],
  },
  {
    provider: "OpenAI",
    models: ["gpt-5.4", "gpt-4o", "gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1-nano"],
  },
  {
    provider: "Google",
    models: ["gemini-2.0-flash"],
  },
  {
    provider: "Local (Ollama)",
    models: ["qwen2.5:14b", "qwen2.5:7b", "llama3.1:8b", "phi3:3.8b"],
  },
];

const listStyle: React.CSSProperties = {
  paddingLeft: "1.25rem",
  margin: 0,
  fontSize: "0.85rem",
  color: "var(--text-secondary)",
  lineHeight: 1.8,
};

const codeStyle: React.CSSProperties = {
  background: "var(--bg-surface)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: "1rem",
  fontSize: "0.8rem",
  lineHeight: 1.6,
  color: "var(--text-secondary)",
  overflow: "auto",
  margin: 0,
  whiteSpace: "pre",
};
