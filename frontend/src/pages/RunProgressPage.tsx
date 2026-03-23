import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchRun } from "../api/runs";
import { get } from "../api/client";
import { useRunWebSocket } from "../hooks/useWebSocket";

interface RunResultItem {
  run_id: string;
  scenario_id: string;
  model: string;
  condition: string;
  prompt_version: string;
  response_text: string;
  prompt_sent: string;
  input_tokens: number;
  output_tokens: number;
  latency_seconds: number;
  cost_usd: number;
}

export default function RunProgressPage() {
  const { id } = useParams<{ id: string }>();
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"response" | "prompt">("response");

  const { data: run } = useQuery({
    queryKey: ["run", id],
    queryFn: () => fetchRun(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" ? 3000 : false;
    },
  });

  const isRunning = run?.status === "running";

  // Only connect WebSocket for active runs
  const { events, latestEvent, connected, cancel } = useRunWebSocket(
    isRunning ? (id ?? null) : null
  );

  // Load results for completed runs
  const { data: results = [] } = useQuery({
    queryKey: ["run-results", id],
    queryFn: () => get<RunResultItem[]>(`/runs/${id}/results`),
    enabled: !!id && !isRunning,
  });

  const progress = latestEvent?.progress ?? {
    completed: run?.completed_items ?? 0,
    total: run?.total_items ?? 0,
  };

  const pct = progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : 0;

  // Group results by scenario
  const resultsByScenario: Record<string, RunResultItem[]> = {};
  for (const r of results) {
    (resultsByScenario[r.scenario_id] ??= []).push(r);
  }
  const scenarioIds = Object.keys(resultsByScenario).sort();

  return (
    <div style={{ maxWidth: 1000 }}>
      <h1 style={{ marginTop: 0 }}>
        Run: {id}
        {run?.prompt_version && (
          <span
            style={{
              fontSize: "0.8rem",
              background: "#e8e8f0",
              padding: "4px 10px",
              borderRadius: 6,
              marginLeft: 12,
              verticalAlign: "middle",
              fontWeight: 600,
            }}
          >
            {run.prompt_version}
          </span>
        )}
      </h1>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <Stat label="Status" value={run?.status ?? "..."} />
        <Stat label="Progress" value={`${progress.completed}/${progress.total}`} />
        <Stat label="Cost" value={`$${(run?.total_cost_usd ?? 0).toFixed(4)}`} />
        {isRunning && <Stat label="WebSocket" value={connected ? "Connected" : "Disconnected"} />}
      </div>

      <div
        style={{
          background: "#e0e0e0",
          borderRadius: 8,
          height: 24,
          marginBottom: "1.5rem",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            background: isRunning ? "#6c63ff" : "#4caf50",
            height: "100%",
            width: `${pct}%`,
            transition: "width 0.3s ease",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontSize: "0.75rem",
            fontWeight: 600,
          }}
        >
          {pct > 10 && `${pct}%`}
        </div>
      </div>

      {isRunning && (
        <button
          onClick={cancel}
          style={{
            background: "#f44336",
            color: "#fff",
            border: "none",
            padding: "0.5rem 1.25rem",
            borderRadius: 6,
            cursor: "pointer",
            marginBottom: "1rem",
          }}
        >
          Cancel Run
        </button>
      )}

      {/* Live event log for running */}
      {isRunning && events.length > 0 && (
        <>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <h3 style={{ fontSize: "0.95rem", color: "#444", margin: 0 }}>Event Log</h3>
            <RunStats events={events} />
          </div>
          <div
            style={{
              background: "#1a1a2e",
              color: "#e0e0e0",
              padding: "1rem",
              borderRadius: 8,
              maxHeight: 400,
              overflow: "auto",
              fontSize: "0.8rem",
              fontFamily: "'SF Mono', 'Fira Code', monospace",
              marginBottom: "2rem",
              lineHeight: 1.7,
            }}
          >
            {[...events].reverse().map((e, i) => (
              <div key={i} style={{ marginBottom: 2, display: "flex", gap: "0.5rem" }}>
                <span style={{ color: "#666", minWidth: 65, flexShrink: 0 }}>
                  {e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : ""}
                </span>
                <span style={{ minWidth: 14 }}>{typeIcon(e.type)}</span>
                <span>
                  {e.type === "item_complete" && (
                    <>
                      <span style={{ color: "#4caf50" }}>DONE</span>{" "}
                      <span style={{ color: "#fff" }}>{e.scenario_id}</span>
                      <span style={{ color: "#888" }}> / </span>
                      <span style={{ color: modelColor(e.model ?? "") }}>{e.model}</span>
                      <span style={{ color: "#888" }}> / </span>
                      <span style={{ color: conditionColor(e.condition ?? "") }}>{e.condition}</span>
                      <span style={{ color: "#666" }}>
                        {" "}
                        — {e.tokens_used?.toLocaleString()} tokens
                        {e.cost_usd != null && e.cost_usd > 0 ? `, $${e.cost_usd.toFixed(4)}` : ""}
                      </span>
                    </>
                  )}
                  {e.type === "item_start" && (
                    <>
                      <span style={{ color: "#2196f3" }}>START</span>{" "}
                      <span style={{ color: "#fff" }}>{e.scenario_id}</span>
                      <span style={{ color: "#888" }}> / </span>
                      <span style={{ color: modelColor(e.model ?? "") }}>{e.model}</span>
                      <span style={{ color: "#888" }}> / </span>
                      <span style={{ color: conditionColor(e.condition ?? "") }}>{e.condition}</span>
                    </>
                  )}
                  {e.type === "item_error" && (
                    <>
                      <span style={{ color: "#f44336" }}>FAIL</span>{" "}
                      <span style={{ color: "#fff" }}>{e.scenario_id}</span>
                      <span style={{ color: "#888" }}> / </span>
                      <span style={{ color: modelColor(e.model ?? "") }}>{e.model}</span>
                      <span style={{ color: "#888" }}> / </span>
                      <span style={{ color: conditionColor(e.condition ?? "") }}>{e.condition}</span>
                      {e.error && (
                        <div style={{ color: "#f44336", marginTop: 2, marginLeft: "2rem", fontSize: "0.75rem" }}>
                          {e.error.length > 120 ? e.error.slice(0, 120) + "..." : e.error}
                        </div>
                      )}
                    </>
                  )}
                  {e.type === "run_complete" && (
                    <span style={{ color: "#4caf50", fontWeight: 600 }}>
                      RUN COMPLETE — {progress.completed}/{progress.total} items
                    </span>
                  )}
                  {e.type === "run_error" && (
                    <span style={{ color: "#f44336", fontWeight: 600 }}>
                      RUN ERROR: {e.error}
                    </span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Results for completed runs */}
      {!isRunning && results.length > 0 && (
        <>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ margin: 0, fontSize: "1.1rem" }}>
              Results ({results.length} responses)
            </h2>
          </div>

          {scenarioIds.map((scenarioId) => {
            const items = resultsByScenario[scenarioId];
            return (
              <div
                key={scenarioId}
                style={{
                  background: "#fff",
                  borderRadius: 8,
                  marginBottom: "1rem",
                  border: "1px solid #e0e0e0",
                }}
              >
                <div
                  style={{
                    padding: "0.75rem 1rem",
                    borderBottom: "1px solid #f0f0f0",
                    fontWeight: 600,
                    color: "#6c63ff",
                  }}
                >
                  {scenarioId}
                </div>
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: "0.85rem",
                  }}
                >
                  <thead>
                    <tr>
                      <th style={thStyle}>Model</th>
                      <th style={thStyle}>Condition</th>
                      <th style={thStyle}>Tokens</th>
                      <th style={thStyle}>Latency</th>
                      <th style={thStyle}>Cost</th>
                      <th style={thStyle}>Response</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items
                      .sort((a, b) =>
                        a.model.localeCompare(b.model) ||
                        a.condition.localeCompare(b.condition)
                      )
                      .map((r) => {
                        const key = r.run_id;
                        const isExpanded = expandedItem === key;
                        return (
                          <>
                            <tr key={key}>
                              <td style={tdStyle}>{r.model}</td>
                              <td style={tdStyle}>
                                <span
                                  style={{
                                    background: conditionColor(r.condition) + "20",
                                    color: conditionColor(r.condition),
                                    padding: "2px 8px",
                                    borderRadius: 4,
                                    fontWeight: 600,
                                    fontSize: "0.8rem",
                                  }}
                                >
                                  {r.condition}
                                </span>
                              </td>
                              <td style={tdStyle}>
                                {(r.input_tokens + r.output_tokens).toLocaleString()}
                              </td>
                              <td style={tdStyle}>{r.latency_seconds.toFixed(1)}s</td>
                              <td style={tdStyle}>${r.cost_usd.toFixed(4)}</td>
                              <td style={tdStyle}>
                                <button
                                  onClick={() =>
                                    setExpandedItem(isExpanded ? null : key)
                                  }
                                  style={{
                                    color: "#6c63ff",
                                    background: "none",
                                    border: "none",
                                    cursor: "pointer",
                                    textDecoration: "underline",
                                  }}
                                >
                                  {isExpanded ? "Hide" : "View"}
                                </button>
                              </td>
                            </tr>
                            {isExpanded && (
                              <tr key={key + "-expanded"}>
                                <td
                                  colSpan={6}
                                  style={{ padding: "0.75rem 1rem" }}
                                >
                                  <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
                                    <button
                                      onClick={() => setViewMode("response")}
                                      style={{
                                        padding: "4px 12px",
                                        borderRadius: 4,
                                        border: "1px solid #d0d0d0",
                                        background: viewMode === "response" ? "#6c63ff" : "#fff",
                                        color: viewMode === "response" ? "#fff" : "#333",
                                        cursor: "pointer",
                                        fontSize: "0.8rem",
                                      }}
                                    >
                                      Response
                                    </button>
                                    <button
                                      onClick={() => setViewMode("prompt")}
                                      style={{
                                        padding: "4px 12px",
                                        borderRadius: 4,
                                        border: "1px solid #d0d0d0",
                                        background: viewMode === "prompt" ? "#6c63ff" : "#fff",
                                        color: viewMode === "prompt" ? "#fff" : "#333",
                                        cursor: "pointer",
                                        fontSize: "0.8rem",
                                      }}
                                    >
                                      Prompt Sent
                                    </button>
                                  </div>
                                  <pre
                                    style={{
                                      whiteSpace: "pre-wrap",
                                      background: "#fafafa",
                                      padding: "1rem",
                                      borderRadius: 6,
                                      border: "1px solid #e0e0e0",
                                      fontSize: "0.85rem",
                                      lineHeight: 1.6,
                                      maxHeight: 500,
                                      overflow: "auto",
                                    }}
                                  >
                                    {viewMode === "response"
                                      ? r.response_text
                                      : r.prompt_sent}
                                  </pre>
                                </td>
                              </tr>
                            )}
                          </>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            );
          })}
        </>
      )}

      {!isRunning && results.length === 0 && run?.status === "completed" && (
        <p style={{ color: "#666" }}>No result files found for this run.</p>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        background: "#fff",
        padding: "0.75rem 1rem",
        borderRadius: 8,
        flex: 1,
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "0.75rem", color: "#666", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontWeight: 600, fontSize: "1rem" }}>{value}</div>
    </div>
  );
}

function RunStats({ events }: { events: any[] }) {
  const completed = events.filter((e) => e.type === "item_complete").length;
  const errors = events.filter((e) => e.type === "item_error").length;
  const totalTokens = events
    .filter((e) => e.type === "item_complete" && e.tokens_used)
    .reduce((sum, e) => sum + (e.tokens_used || 0), 0);

  return (
    <div style={{ display: "flex", gap: "1rem", fontSize: "0.8rem", color: "#666" }}>
      <span><span style={{ color: "#4caf50" }}>{completed}</span> done</span>
      {errors > 0 && <span><span style={{ color: "#f44336" }}>{errors}</span> errors</span>}
      <span>{totalTokens.toLocaleString()} tokens</span>
    </div>
  );
}

function typeIcon(type: string): string {
  switch (type) {
    case "item_complete":
      return "✓";
    case "item_start":
      return "▸";
    case "item_error":
      return "✗";
    case "run_complete":
      return "★";
    default:
      return "·";
  }
}

function modelColor(model: string): string {
  if (model.startsWith("claude")) return "#d4a574";
  if (model.startsWith("gpt")) return "#74b9a5";
  if (model.startsWith("gemini")) return "#7498d4";
  // Local models
  if (model.startsWith("qwen")) return "#c084fc";
  if (model.startsWith("llama")) return "#f97316";
  if (model.startsWith("phi")) return "#06b6d4";
  return "#aaa";
}

function typeColor(type: string): string {
  switch (type) {
    case "item_complete":
      return "#4caf50";
    case "item_start":
      return "#2196f3";
    case "item_error":
      return "#f44336";
    case "run_complete":
      return "#4caf50";
    default:
      return "#ff9800";
  }
}

function conditionColor(condition: string): string {
  switch (condition) {
    case "zero_shot":
      return "#9e9e9e";
    case "cot":
      return "#ff9800";
    case "length_matched":
      return "#2196f3";
    case "dodar":
      return "#6c63ff";
    default:
      return "#333";
  }
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "0.5rem 0.75rem",
  borderBottom: "2px solid #e0e0e0",
  fontSize: "0.8rem",
  color: "#666",
};

const tdStyle: React.CSSProperties = {
  padding: "0.5rem 0.75rem",
  borderBottom: "1px solid #f0f0f0",
};
