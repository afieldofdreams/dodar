import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { fetchScenarios } from "../api/scenarios";
import { startRun, estimateCost } from "../api/runs";
import { MODELS, CONDITIONS, CATEGORIES } from "../types";
import type { CostEstimate } from "../types";

export default function NewRunPage() {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedScenarioIds, setSelectedScenarioIds] = useState<string[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>([...MODELS]);
  const [selectedConditions, setSelectedConditions] = useState<string[]>([...CONDITIONS]);
  const [skipCompleted, setSkipCompleted] = useState(true);
  const [estimates, setEstimates] = useState<CostEstimate[] | null>(null);

  const { data: scenarios = [] } = useQuery({
    queryKey: ["scenarios", selectedCategory],
    queryFn: () => fetchScenarios({ category: selectedCategory || undefined }),
  });

  const estimateMutation = useMutation({
    mutationFn: () =>
      estimateCost({
        scenario_ids: selectedScenarioIds.length > 0 ? selectedScenarioIds : undefined,
        models: selectedModels,
        conditions: selectedConditions,
      }),
    onSuccess: (data) => setEstimates(data),
  });

  const runMutation = useMutation({
    mutationFn: () =>
      startRun({
        scenario_ids: selectedScenarioIds.length > 0 ? selectedScenarioIds : undefined,
        models: selectedModels,
        conditions: selectedConditions,
        skip_completed: skipCompleted,
      }),
    onSuccess: (data) => navigate(`/runs/${data.run_id}`),
  });

  const toggleItem = (list: string[], item: string, setter: (v: string[]) => void) => {
    setter(list.includes(item) ? list.filter((i) => i !== item) : [...list, item]);
  };

  return (
    <div style={{ maxWidth: 700 }}>
      <h1 style={{ marginTop: 0 }}>New Benchmark Run</h1>

      <Section title="Scenarios">
        <div style={{ marginBottom: "0.5rem" }}>
          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setSelectedScenarioIds([]);
            }}
            style={selectStyle}
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <div style={{ maxHeight: 200, overflow: "auto", border: "1px solid #e0e0e0", borderRadius: 6, padding: "0.5rem" }}>
          <label style={{ display: "block", marginBottom: 4, fontWeight: 600, fontSize: "0.85rem" }}>
            <input
              type="checkbox"
              checked={selectedScenarioIds.length === 0}
              onChange={() => setSelectedScenarioIds([])}
            />{" "}
            All scenarios ({scenarios.length})
          </label>
          {scenarios.map((s) => (
            <label key={s.id} style={{ display: "block", marginBottom: 2, fontSize: "0.85rem" }}>
              <input
                type="checkbox"
                checked={selectedScenarioIds.length === 0 || selectedScenarioIds.includes(s.id)}
                onChange={() => toggleItem(selectedScenarioIds, s.id, setSelectedScenarioIds)}
              />{" "}
              {s.id} — {s.title}
            </label>
          ))}
        </div>
      </Section>

      <Section title="Models">
        {MODELS.map((m) => (
          <label key={m} style={{ display: "block", marginBottom: 4, fontSize: "0.9rem" }}>
            <input
              type="checkbox"
              checked={selectedModels.includes(m)}
              onChange={() => toggleItem(selectedModels, m, setSelectedModels)}
            />{" "}
            {m}
          </label>
        ))}
      </Section>

      <Section title="Conditions">
        {CONDITIONS.map((c) => (
          <label key={c} style={{ display: "block", marginBottom: 4, fontSize: "0.9rem" }}>
            <input
              type="checkbox"
              checked={selectedConditions.includes(c)}
              onChange={() => toggleItem(selectedConditions, c, setSelectedConditions)}
            />{" "}
            {c.replace(/_/g, " ")}
          </label>
        ))}
      </Section>

      <Section title="Options">
        <label style={{ display: "block", fontSize: "0.9rem" }}>
          <input
            type="checkbox"
            checked={skipCompleted}
            onChange={() => setSkipCompleted(!skipCompleted)}
          />{" "}
          Skip already completed items (resume interrupted runs)
        </label>
      </Section>

      <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem" }}>
        <button onClick={() => estimateMutation.mutate()} style={btnSecondary} disabled={estimateMutation.isPending}>
          {estimateMutation.isPending ? "Estimating..." : "Estimate Cost"}
        </button>
        <button
          onClick={() => runMutation.mutate()}
          style={btnPrimary}
          disabled={runMutation.isPending || selectedModels.length === 0 || selectedConditions.length === 0}
        >
          {runMutation.isPending ? "Starting..." : "Start Run"}
        </button>
      </div>

      {runMutation.isError && (
        <p style={{ color: "#f44336", marginTop: "1rem" }}>
          Error: {(runMutation.error as Error).message}
        </p>
      )}

      {estimates && (
        <div style={{ marginTop: "1.5rem" }}>
          <h3 style={{ fontSize: "0.95rem" }}>Cost Estimate</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", background: "#fff", borderRadius: 8 }}>
            <thead>
              <tr>
                <th style={thStyle}>Model</th>
                <th style={thStyle}>Condition</th>
                <th style={thStyle}>Input Tokens</th>
                <th style={thStyle}>Output Tokens</th>
                <th style={thStyle}>Est. Cost</th>
              </tr>
            </thead>
            <tbody>
              {estimates.map((e, i) => (
                <tr key={i}>
                  <td style={tdStyle}>{e.model}</td>
                  <td style={tdStyle}>{e.condition}</td>
                  <td style={tdStyle}>{e.estimated_input_tokens.toLocaleString()}</td>
                  <td style={tdStyle}>{e.estimated_output_tokens.toLocaleString()}</td>
                  <td style={tdStyle}>${e.estimated_cost_usd.toFixed(4)}</td>
                </tr>
              ))}
              <tr style={{ fontWeight: 600 }}>
                <td style={tdStyle} colSpan={4}>Total</td>
                <td style={tdStyle}>
                  ${estimates.reduce((sum, e) => sum + e.estimated_cost_usd, 0).toFixed(4)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "1.25rem" }}>
      <h3 style={{ fontSize: "0.95rem", color: "#444", marginBottom: "0.5rem" }}>{title}</h3>
      {children}
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  padding: "0.5rem 0.75rem",
  borderRadius: 6,
  border: "1px solid #d0d0d0",
  background: "#fff",
  fontSize: "0.9rem",
};

const btnPrimary: React.CSSProperties = {
  background: "#6c63ff",
  color: "#fff",
  border: "none",
  padding: "0.6rem 1.5rem",
  borderRadius: 6,
  fontSize: "0.9rem",
  cursor: "pointer",
};

const btnSecondary: React.CSSProperties = {
  background: "#fff",
  color: "#6c63ff",
  border: "1px solid #6c63ff",
  padding: "0.6rem 1.5rem",
  borderRadius: 6,
  fontSize: "0.9rem",
  cursor: "pointer",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "0.5rem",
  borderBottom: "2px solid #e0e0e0",
  fontSize: "0.8rem",
  color: "#666",
};

const tdStyle: React.CSSProperties = {
  padding: "0.5rem",
  borderBottom: "1px solid #f0f0f0",
  fontSize: "0.85rem",
};
