import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { fetchScenario } from "../api/scenarios";
import { MODELS, CONDITIONS } from "../types";

export default function ScenarioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: scenario, isLoading } = useQuery({
    queryKey: ["scenario", id],
    queryFn: () => fetchScenario(id!),
    enabled: !!id,
  });

  if (isLoading) return <p>Loading...</p>;
  if (!scenario) return <p>Scenario not found.</p>;

  return (
    <div style={{ maxWidth: 900 }}>
      <Link to="/scenarios" style={{ color: "#6c63ff", fontSize: "0.85rem" }}>
        &larr; Back to Scenarios
      </Link>

      <div style={{ display: "flex", gap: "1rem", alignItems: "center", margin: "1rem 0" }}>
        <h1 style={{ margin: 0 }}>{scenario.id}</h1>
        <span style={{ background: "#e8e8f0", padding: "4px 10px", borderRadius: 6, fontSize: "0.85rem" }}>
          {scenario.category}
        </span>
        <span style={{ background: "#e8e8f0", padding: "4px 10px", borderRadius: 6, fontSize: "0.85rem" }}>
          {scenario.domain}
        </span>
        <span style={{ background: "#e8e8f0", padding: "4px 10px", borderRadius: 6, fontSize: "0.85rem" }}>
          {scenario.difficulty}
        </span>
      </div>

      <h2 style={{ fontSize: "1.1rem" }}>{scenario.title}</h2>

      <Section title="Prompt">
        <pre style={preStyle}>{scenario.prompt_text}</pre>
      </Section>

      <Section title="Run Status Matrix">
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Model</th>
              {CONDITIONS.map((c) => (
                <th key={c} style={thStyle}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {MODELS.map((m) => (
              <tr key={m}>
                <td style={tdStyle}>{m}</td>
                {CONDITIONS.map((c) => {
                  const status = scenario.run_matrix?.[m]?.[c];
                  return (
                    <td key={c} style={tdStyle}>
                      {status ? (
                        <span style={{ color: "#4caf50", fontWeight: 600 }}>Done</span>
                      ) : (
                        <span style={{ color: "#ccc" }}>--</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Expected Pitfalls">
        <ul>
          {scenario.expected_pitfalls.map((p, i) => (
            <li key={i}>{p}</li>
          ))}
        </ul>
      </Section>

      <Section title="Gold Standard Elements">
        <ul>
          {scenario.gold_standard_elements.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      </Section>

      <Section title="DODAR Discriminators">
        {scenario.discriminators.map((d, i) => (
          <div
            key={i}
            style={{
              background: "#f0f0ff",
              padding: "0.75rem 1rem",
              borderRadius: 6,
              marginBottom: "0.5rem",
            }}
          >
            <strong>{d.dimension}:</strong> {d.description}
          </div>
        ))}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <h3 style={{ fontSize: "0.95rem", color: "#444", borderBottom: "1px solid #e0e0e0", paddingBottom: 6 }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

const preStyle: React.CSSProperties = {
  whiteSpace: "pre-wrap",
  background: "#fafafa",
  padding: "1rem",
  borderRadius: 6,
  border: "1px solid #e0e0e0",
  fontSize: "0.9rem",
  lineHeight: 1.6,
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: "0.85rem",
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
};
