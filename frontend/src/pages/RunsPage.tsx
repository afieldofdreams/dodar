import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchRuns, deleteRun } from "../api/runs";

const STATUS_COLORS: Record<string, string> = {
  completed: "#4caf50",
  running: "#2196f3",
  failed: "#f44336",
  cancelled: "#ff9800",
  pending: "#9e9e9e",
};

export default function RunsPage() {
  const queryClient = useQueryClient();

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: fetchRuns,
    refetchInterval: 5000,
  });

  const deleteMutation = useMutation({
    mutationFn: (runId: string) => deleteRun(runId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["runs"] }),
  });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ marginTop: 0 }}>Benchmark Runs</h1>
        <Link
          to="/runs/new"
          style={{
            background: "#6c63ff",
            color: "#fff",
            padding: "0.6rem 1.25rem",
            borderRadius: 6,
            textDecoration: "none",
            fontSize: "0.9rem",
          }}
        >
          New Run
        </Link>
      </div>

      {isLoading ? (
        <p>Loading...</p>
      ) : runs.length === 0 ? (
        <div
          style={{
            background: "#fff",
            padding: "3rem",
            borderRadius: 8,
            textAlign: "center",
            color: "#666",
          }}
        >
          <p>No benchmark runs yet.</p>
          <Link to="/runs/new" style={{ color: "#6c63ff" }}>
            Start your first run
          </Link>
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", background: "#fff", borderRadius: 8 }}>
          <thead>
            <tr>
              <th style={thStyle}>Run ID</th>
              <th style={thStyle}>Version</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Progress</th>
              <th style={thStyle}>Cost</th>
              <th style={thStyle}>Created</th>
              <th style={thStyle}></th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.run_id}>
                <td style={tdStyle}>
                  <Link to={`/runs/${r.run_id}`} style={{ color: "#6c63ff" }}>
                    {r.run_id}
                  </Link>
                </td>
                <td style={tdStyle}>
                  <span
                    style={{
                      background: "#e8e8f0",
                      padding: "2px 8px",
                      borderRadius: 4,
                      fontSize: "0.8rem",
                      fontWeight: 600,
                    }}
                  >
                    {r.prompt_version}
                  </span>
                </td>
                <td style={tdStyle}>
                  <span
                    style={{
                      color: STATUS_COLORS[r.status] || "#666",
                      fontWeight: 600,
                      fontSize: "0.85rem",
                    }}
                  >
                    {r.status}
                  </span>
                </td>
                <td style={tdStyle}>
                  {r.completed_items}/{r.total_items}
                </td>
                <td style={tdStyle}>${r.total_cost_usd.toFixed(4)}</td>
                <td style={tdStyle}>{new Date(r.created_at).toLocaleString()}</td>
                <td style={tdStyle}>
                  <button
                    onClick={() => {
                      if (confirm(`Delete run ${r.run_id} and all its results?`)) {
                        deleteMutation.mutate(r.run_id);
                      }
                    }}
                    style={{ color: "#999", background: "none", border: "none", cursor: "pointer", textDecoration: "underline", fontSize: "0.85rem" }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "0.75rem 1rem",
  borderBottom: "2px solid #e0e0e0",
  fontSize: "0.8rem",
  color: "#666",
};

const tdStyle: React.CSSProperties = {
  padding: "0.75rem 1rem",
  borderBottom: "1px solid #f0f0f0",
  fontSize: "0.9rem",
};
