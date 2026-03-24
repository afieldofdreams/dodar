import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { post, get } from "../api/client";
import { MODELS } from "../types";

interface AnalyzeRequest {
  scenario: string;
  model: string;
  mode: "dodar" | "zero_shot" | "cot";
}

interface AnalyzeResponse {
  text: string;
  phases?: {
    diagnose?: string;
    options?: string;
    decide?: string;
    action?: string;
    review?: string;
  };
  input_tokens: number;
  output_tokens: number;
  latency_seconds: number;
  model: string;
  mode: string;
}

const EXAMPLE_SCENARIOS = [
  {
    label: "SaaS Churn Spike",
    text: "Your Series B SaaS platform has experienced a 40% increase in monthly churn over the past 8 weeks. Your Head of Customer Success flags that it's correlated with your pricing tier restructure 10 weeks ago. However, your Product lead notes that your main competitor launched a cheaper alternative 6 weeks ago. Your VP of Onboarding separately reports that onboarding completion rate dropped sharply 8 weeks ago after a platform UI redesign. All three events cluster within a narrow window. What is driving the churn?",
  },
  {
    label: "Startup Hire vs. Cut Burn",
    text: "You founded a SaaS startup 8 months ago. You have $180K remaining from a $250K pre-seed raise. Monthly burn is $25K (runway = 7 months). You have 20 paying customers ($2K MRR). You have three pressing choices: (1) Hire a senior engineer ($15K/month), (2) Hire a sales/marketing person ($12K/month), (3) Cut burn to $12K/month by reducing your own salary. Your biggest customers say they'd pay 5x if you added a specific feature (3-month build). Series A fundraising is getting harder. What should you do?",
  },
  {
    label: "Intermittent 500 Errors",
    text: "Your API is intermittently returning 500 errors to 0.5-1% of requests with no clear pattern. The issue began 10 days ago. Your DevOps team recently completed three changes: (1) upgraded the load balancer firmware, (2) increased database connection pool size from 100 to 200, and (3) deployed a new caching layer. Application logs show no errors; infrastructure logs show occasional database connection timeouts. The rate of errors does not correlate with traffic spikes. What is causing this?",
  },
];

const PHASE_LABELS: Record<string, { label: string; color: string; icon: string }> = {
  diagnose: { label: "Diagnose", color: "#f97316", icon: "🔍" },
  options: { label: "Options", color: "#06b6d4", icon: "⚖️" },
  decide: { label: "Decide", color: "#8b5cf6", icon: "✓" },
  action: { label: "Action", color: "#22c55e", icon: "→" },
  review: { label: "Review", color: "#ef4444", icon: "↻" },
};

export default function PlaygroundPage() {
  const [scenario, setScenario] = useState("");
  const [model, setModel] = useState("claude-sonnet-4-5");
  const [compareMode, setCompareMode] = useState(false);
  const [activePhase, setActivePhase] = useState<string | null>(null);

  const dodarMutation = useMutation({
    mutationFn: (req: AnalyzeRequest) => post<AnalyzeResponse>("/analyze", req),
    onSuccess: () => setActivePhase("diagnose"),
  });

  const baselineMutation = useMutation({
    mutationFn: (req: AnalyzeRequest) => post<AnalyzeResponse>("/analyze", req),
  });

  const handleAnalyze = () => {
    dodarMutation.mutate({ scenario, model, mode: "dodar" });
    if (compareMode) {
      baselineMutation.mutate({ scenario, model, mode: "zero_shot" });
    }
  };

  const isLoading = dodarMutation.isPending || baselineMutation.isPending;
  const dodarResult = dodarMutation.data;
  const baselineResult = baselineMutation.data;

  return (
    <div style={{ maxWidth: 1200 }}>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.8rem", margin: "0 0 0.5rem", fontWeight: 700, letterSpacing: "-0.03em" }}>
          DODAR Playground
        </h1>
        <p style={{ color: "var(--text-secondary)", margin: 0, fontSize: "0.95rem", maxWidth: 600 }}>
          Test the DODAR reasoning framework on any scenario.
          Watch how structured gates improve diagnosis, trade-off analysis, and self-critique.
        </p>
      </div>

      {/* Input area */}
      <div style={{ background: "var(--bg-surface)", borderRadius: 12, padding: "1.5rem", border: "1px solid var(--border)", marginBottom: "1.5rem" }}>
        {/* Example pills */}
        <div style={{ marginBottom: "0.75rem", display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginRight: "0.25rem" }}>Try:</span>
          {EXAMPLE_SCENARIOS.map((ex) => (
            <button
              key={ex.label}
              onClick={() => setScenario(ex.text)}
              style={{
                background: "var(--bg-surface-3)",
                border: "1px solid var(--border)",
                color: "var(--text-secondary)",
                padding: "0.3rem 0.75rem",
                borderRadius: 6,
                fontSize: "0.75rem",
                cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              {ex.label}
            </button>
          ))}
        </div>

        <textarea
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          placeholder="Describe a complex scenario with ambiguous diagnosis, competing options, or real trade-offs..."
          style={{
            width: "100%",
            minHeight: 120,
            padding: "0.75rem",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg-surface-2)",
            color: "var(--text)",
            fontSize: "0.9rem",
            lineHeight: 1.6,
            resize: "vertical",
            outline: "none",
          }}
        />

        <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            style={{
              padding: "0.5rem 0.75rem",
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--bg-surface-2)",
              color: "var(--text)",
              fontSize: "0.85rem",
            }}
          >
            {MODELS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>

          <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem", color: "var(--text-secondary)", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={compareMode}
              onChange={(e) => setCompareMode(e.target.checked)}
              style={{ accentColor: "var(--accent)" }}
            />
            Compare with zero-shot baseline
          </label>

          <div style={{ flex: 1 }} />

          <button
            onClick={handleAnalyze}
            disabled={!scenario.trim() || isLoading}
            style={{
              background: !scenario.trim() ? "var(--bg-surface-3)" : "var(--accent)",
              color: !scenario.trim() ? "var(--text-muted)" : "#fff",
              border: "none",
              padding: "0.5rem 1.5rem",
              borderRadius: 8,
              fontSize: "0.9rem",
              fontWeight: 600,
              cursor: !scenario.trim() ? "default" : "pointer",
              transition: "all 0.15s",
            }}
          >
            {isLoading ? "Analyzing..." : "Analyze with DODAR"}
          </button>
        </div>
      </div>

      {/* Results */}
      {dodarResult && (
        <div style={{ display: "flex", gap: "1.5rem" }}>
          {/* DODAR result */}
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
              <h2 style={{ margin: 0, fontSize: "1.1rem" }}>DODAR Analysis</h2>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", background: "var(--accent-dim)", padding: "2px 8px", borderRadius: 4 }}>
                {dodarResult.model} · {dodarResult.output_tokens} tokens · {dodarResult.latency_seconds.toFixed(1)}s
              </span>
            </div>

            {/* Phase tabs */}
            {dodarResult.phases && (
              <>
                <div style={{ display: "flex", gap: "0.25rem", marginBottom: "1rem" }}>
                  {Object.entries(PHASE_LABELS).map(([key, { label, color }]) => (
                    <button
                      key={key}
                      onClick={() => setActivePhase(key)}
                      style={{
                        padding: "0.4rem 0.75rem",
                        borderRadius: 6,
                        border: activePhase === key ? `1px solid ${color}` : "1px solid var(--border)",
                        background: activePhase === key ? `${color}15` : "var(--bg-surface)",
                        color: activePhase === key ? color : "var(--text-secondary)",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        cursor: "pointer",
                        transition: "all 0.15s",
                      }}
                    >
                      {label}
                    </button>
                  ))}
                  <button
                    onClick={() => setActivePhase(null)}
                    style={{
                      padding: "0.4rem 0.75rem",
                      borderRadius: 6,
                      border: activePhase === null ? "1px solid var(--accent)" : "1px solid var(--border)",
                      background: activePhase === null ? "var(--accent-dim)" : "var(--bg-surface)",
                      color: activePhase === null ? "var(--accent)" : "var(--text-secondary)",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Full
                  </button>
                </div>

                {/* Phase content */}
                <div
                  style={{
                    background: "var(--bg-surface)",
                    border: "1px solid var(--border)",
                    borderRadius: 12,
                    padding: "1.25rem",
                    maxHeight: 600,
                    overflow: "auto",
                  }}
                >
                  {activePhase && dodarResult.phases[activePhase as keyof typeof dodarResult.phases] ? (
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
                        <span style={{ fontSize: "1rem" }}>{PHASE_LABELS[activePhase].icon}</span>
                        <h3 style={{ margin: 0, fontSize: "0.95rem", color: PHASE_LABELS[activePhase].color }}>
                          {PHASE_LABELS[activePhase].label}
                        </h3>
                      </div>
                      <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem", lineHeight: 1.7, margin: 0, color: "var(--text)" }}>
                        {dodarResult.phases[activePhase as keyof typeof dodarResult.phases]}
                      </pre>
                    </div>
                  ) : (
                    <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem", lineHeight: 1.7, margin: 0, color: "var(--text)" }}>
                      {dodarResult.text}
                    </pre>
                  )}
                </div>
              </>
            )}

            {/* Fallback: no phases parsed */}
            {!dodarResult.phases && (
              <div
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 12,
                  padding: "1.25rem",
                  maxHeight: 600,
                  overflow: "auto",
                }}
              >
                <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem", lineHeight: 1.7, margin: 0 }}>
                  {dodarResult.text}
                </pre>
              </div>
            )}
          </div>

          {/* Baseline comparison */}
          {compareMode && baselineResult && (
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
                <h2 style={{ margin: 0, fontSize: "1.1rem", color: "var(--text-secondary)" }}>Zero-Shot Baseline</h2>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", background: "var(--bg-surface-3)", padding: "2px 8px", borderRadius: 4 }}>
                  {baselineResult.output_tokens} tokens · {baselineResult.latency_seconds.toFixed(1)}s
                </span>
              </div>
              <div
                style={{
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 12,
                  padding: "1.25rem",
                  maxHeight: 600,
                  overflow: "auto",
                }}
              >
                <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem", lineHeight: 1.7, margin: 0, color: "var(--text-secondary)" }}>
                  {baselineResult.text}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SDK snippet */}
      {!dodarResult && (
        <div style={{ marginTop: "2rem" }}>
          <h3 style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>Or use the Python SDK</h3>
          <pre
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: "1.25rem",
              fontSize: "0.85rem",
              lineHeight: 1.7,
              color: "var(--text-secondary)",
              overflow: "auto",
            }}
          >
{`from dodar import DODAR

dodar = DODAR(model="claude-sonnet-4-5")
result = dodar.analyze("Your scenario here...")

# Structured access to each reasoning phase
result.diagnosis.hypotheses      # Ranked competing causes
result.options.alternatives      # Distinct paths with trade-offs
result.decision.recommendation   # The call + justification
result.action.steps              # Sequenced implementation
result.review.failure_modes      # Self-critique + abort conditions`}
          </pre>
        </div>
      )}
    </div>
  );
}
