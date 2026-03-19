import { getExportUrl } from "../api/reports";

export default function ExportPage() {
  return (
    <div style={{ maxWidth: 600 }}>
      <h1 style={{ marginTop: 0 }}>Export Data</h1>

      <div style={{ background: "#fff", padding: "1.5rem", borderRadius: 8 }}>
        <p style={{ color: "#666", marginTop: 0 }}>
          Export aggregated scoring results for external analysis.
        </p>

        <div style={{ display: "flex", gap: "1rem" }}>
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
            Download CSV
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
            Download JSON
          </a>
        </div>
      </div>
    </div>
  );
}
