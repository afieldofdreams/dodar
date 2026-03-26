import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchDashboard, fetchVersions } from "../api/reports";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";

const CONDITION_COLORS: Record<string, string> = {
  zero_shot: "#9e9e9e",
  cot: "#ff9800",
  length_matched: "#2196f3",
  dodar: "#6c63ff",
};

export default function DashboardPage() {
  const [selectedVersion, setSelectedVersion] = useState<string | undefined>(undefined);

  const { data: versions = [] } = useQuery({
    queryKey: ["versions"],
    queryFn: fetchVersions,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", selectedVersion],
    queryFn: () => fetchDashboard(selectedVersion),
  });

  if (isLoading) return <p>Loading dashboard...</p>;
  if (!data || data.stats.length === 0) {
    return (
      <div>
        <h1 style={{ marginTop: 0 }}>Dashboard</h1>
        <div style={{ background: "#1e1e32", padding: "3rem", borderRadius: 8, textAlign: "center", color: "#9898b8" }}>
          <p>No scored data available yet.</p>
          <p>Run benchmarks, then score responses to see results here.</p>
        </div>
      </div>
    );
  }

  // Prepare bar chart data: one bar group per dimension, bars per condition
  const dimensions = data.summary.dimensions;
  const models = [...new Set(data.stats.map((s) => s.model))];
  const conditions = [...new Set(data.stats.map((s) => s.condition))];

  // For the bar chart: show average across models per condition per dimension
  const barData = dimensions.map((dim) => {
    const row: Record<string, any> = { dimension: dim.replace(" / ", "\n") };
    for (const cond of conditions) {
      const values = data.stats.filter((s) => s.dimension === dim && s.condition === cond);
      const avg = values.length > 0 ? values.reduce((s, v) => s + v.mean, 0) / values.length : 0;
      row[cond] = parseFloat(avg.toFixed(2));
    }
    return row;
  });

  // Radar chart data per model
  const radarByModel = models.map((model) => {
    return {
      model,
      data: dimensions.map((dim) => {
        const row: Record<string, any> = { dimension: dim.split(" ")[0] };
        for (const cond of conditions) {
          const stat = data.stats.find(
            (s) => s.model === model && s.condition === cond && s.dimension === dim
          );
          row[cond] = stat?.mean ?? 0;
        }
        return row;
      }),
    };
  });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h1 style={{ margin: 0 }}>Dashboard</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <label style={{ fontSize: "0.85rem", color: "#9898b8" }}>Prompt Version:</label>
          <select
            value={selectedVersion ?? ""}
            onChange={(e) => setSelectedVersion(e.target.value || undefined)}
            style={{
              padding: "0.4rem 0.75rem",
              borderRadius: 6,
              border: "1px solid #2e2e50",
              background: "#1e1e32",
              color: "#e8e8f0",
              fontSize: "0.85rem",
              fontWeight: 600,
            }}
          >
            <option value="">All versions</option>
            {versions.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem" }}>
        <StatCard label="Scoring Sessions" value={data.summary.total_sessions} />
        <StatCard label="Total Scored" value={data.summary.total_scored} />
        <StatCard label="Models" value={models.length} />
        <StatCard label="Conditions" value={conditions.length} />
      </div>

      <div style={{ background: "#1e1e32", padding: "1.5rem", borderRadius: 8, marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1rem", margin: "0 0 1rem" }}>Average Score by Dimension & Condition</h2>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="dimension" fontSize={11} interval={0} angle={-20} textAnchor="end" height={60} />
            <YAxis domain={[0, 5]} />
            <Tooltip />
            <Legend />
            {conditions.map((cond) => (
              <Bar
                key={cond}
                dataKey={cond}
                fill={CONDITION_COLORS[cond] || "#333"}
                name={cond.replace(/_/g, " ")}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${Math.min(models.length, 3)}, 1fr)`,
          gap: "1rem",
          marginBottom: "2rem",
        }}
      >
        {radarByModel.map(({ model, data: rData }) => (
          <div key={model} style={{ background: "#1e1e32", padding: "1.25rem", borderRadius: 8 }}>
            <h3 style={{ fontSize: "0.9rem", margin: "0 0 0.5rem", textAlign: "center" }}>{model}</h3>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={rData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="dimension" fontSize={10} />
                <PolarRadiusAxis angle={30} domain={[0, 5]} fontSize={10} />
                {conditions.map((cond) => (
                  <Radar
                    key={cond}
                    name={cond}
                    dataKey={cond}
                    stroke={CONDITION_COLORS[cond] || "#333"}
                    fill={CONDITION_COLORS[cond] || "#333"}
                    fillOpacity={0.15}
                  />
                ))}
                <Legend fontSize={10} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>

      {data.effect_sizes.length > 0 && (
        <div style={{ background: "#1e1e32", padding: "1.5rem", borderRadius: 8 }}>
          <h2 style={{ fontSize: "1rem", margin: "0 0 1rem" }}>Effect Sizes (DODAR vs. Baseline)</h2>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={thStyle}>Model</th>
                <th style={thStyle}>Dimension</th>
                <th style={thStyle}>Baseline</th>
                <th style={thStyle}>Baseline Mean</th>
                <th style={thStyle}>DODAR Mean</th>
                <th style={thStyle}>Cohen's d</th>
              </tr>
            </thead>
            <tbody>
              {data.effect_sizes.map((e, i) => (
                <tr key={i}>
                  <td style={tdStyle}>{e.model}</td>
                  <td style={tdStyle}>{e.dimension}</td>
                  <td style={tdStyle}>{e.baseline_condition}</td>
                  <td style={tdStyle}>{e.baseline_mean.toFixed(2)}</td>
                  <td style={tdStyle}>{e.dodar_mean.toFixed(2)}</td>
                  <td style={tdStyle}>
                    <span
                      style={{
                        fontWeight: 600,
                        color: e.cohens_d > 0.5 ? "#4caf50" : e.cohens_d > 0.2 ? "#ff9800" : "#9898b8",
                      }}
                    >
                      {e.cohens_d.toFixed(3)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ background: "#1e1e32", padding: "1rem 1.5rem", borderRadius: 8, flex: 1, textAlign: "center" }}>
      <div style={{ fontSize: "0.75rem", color: "#9898b8" }}>{label}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#e8e8f0" }}>{value}</div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "0.5rem 0.75rem",
  borderBottom: "2px solid #2e2e50",
  fontSize: "0.8rem",
  color: "#9898b8",
  background: "transparent",
};

const tdStyle: React.CSSProperties = {
  padding: "0.5rem 0.75rem",
  borderBottom: "1px solid #22223a",
  fontSize: "0.85rem",
};
