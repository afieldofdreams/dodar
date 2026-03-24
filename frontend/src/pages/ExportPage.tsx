import { getExportUrl } from "../api/reports";

export default function ExportPage() {
  return (
    <div style={{ maxWidth: 600 }}>
      <h1 style={{ marginTop: 0 }}>Export Data</h1>

      <div style={{ background: "#fff", padding: "1.5rem", borderRadius: 8 }}>
        <p style={{ color: "#666", marginTop: 0 }}>
          Full benchmark export including scenario metadata, prompts sent, model
          responses, per-item scores with rationales, aggregate statistics, and
          effect sizes.
        </p>

        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <a
            href={getExportUrl("csv")}
            download
            style={{
              display: "inline-block",
              background: "#6c63ff",
              color: "#fff",
              padding: "0.6rem 1.5rem",
              borderRadius: 6,
              textDecoration: "none",
              fontSize: "0.9rem",
            }}
          >
            Download CSV (flat)
          </a>
          <a
            href={getExportUrl("json")}
            download
            style={{
              display: "inline-block",
              background: "#fff",
              color: "#6c63ff",
              border: "1px solid #6c63ff",
              padding: "0.6rem 1.5rem",
              borderRadius: 6,
              textDecoration: "none",
              fontSize: "0.9rem",
            }}
          >
            Download JSON (full)
          </a>
        </div>

        <details style={{ marginTop: "1.5rem", color: "#666", fontSize: "0.85rem" }}>
          <summary style={{ cursor: "pointer", fontWeight: 500, color: "#333" }}>
            What's included
          </summary>
          <ul style={{ lineHeight: 1.8, marginTop: "0.5rem" }}>
            <li><strong>Scenarios</strong> — prompt text, expected pitfalls, gold standard elements, DODAR discriminators</li>
            <li><strong>Responses</strong> — full prompt sent, full response text, token counts, latency, cost</li>
            <li><strong>Scores</strong> — per-dimension scores (1–5) with scorer rationales, from each scoring session</li>
            <li><strong>Aggregates</strong> — mean/std per dimension/model/condition</li>
            <li><strong>Effect sizes</strong> — Cohen's d for DODAR vs. each baseline</li>
          </ul>
          <p>CSV flattens one row per scored item. JSON preserves the full nested structure.</p>
        </details>
      </div>
    </div>
  );
}
