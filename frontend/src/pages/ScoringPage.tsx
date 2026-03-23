import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchSessions, fetchScorerModels, createSession, fetchNextItem, submitScore, revealSession, retrySession, stopSession, deleteSession } from "../api/scoring";
import { fetchRuns } from "../api/runs";
import type { DimensionScore, BlindItem } from "../types";

export default function ScoringPage() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  if (activeSessionId) {
    return <ScoringInterface sessionId={activeSessionId} onBack={() => setActiveSessionId(null)} />;
  }

  return <SessionList onSelectSession={setActiveSessionId} />;
}

function SessionList({ onSelectSession }: { onSelectSession: (id: string) => void }) {
  const [scorer, setScorer] = useState("");
  const [selectedRunId, setSelectedRunId] = useState("");
  const [autoScore, setAutoScore] = useState(true);
  const [scorerModel, setScorerModel] = useState("claude-opus-4-6");
  const queryClient = useQueryClient();

  const { data: runs = [] } = useQuery({
    queryKey: ["runs"],
    queryFn: fetchRuns,
  });

  const { data: scorerModelsData } = useQuery({
    queryKey: ["scorer-models"],
    queryFn: fetchScorerModels,
  });
  const scorerModels = scorerModelsData?.models || {};

  const completedRuns = runs.filter((r) => r.status === "completed");

  const { data: sessions = [], refetch } = useQuery({
    queryKey: ["scoring-sessions"],
    queryFn: fetchSessions,
    refetchInterval: 5000,
  });

  const createMutation = useMutation({
    mutationFn: () => createSession({ scorer, run_id: selectedRunId, auto_score: autoScore, scorer_model: scorerModel }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["scoring-sessions"] });
      if (!data.auto_score) {
        onSelectSession(data.session_id);
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (sessionId: string) => deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scoring-sessions"] });
    },
  });

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Scoring</h1>

      <div style={{ background: "#fff", padding: "1.25rem", borderRadius: 8, marginBottom: "1.5rem" }}>
        <h3 style={{ margin: "0 0 0.75rem", fontSize: "0.95rem" }}>Create New Session</h3>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
          <select
            value={selectedRunId}
            onChange={(e) => setSelectedRunId(e.target.value)}
            style={{ padding: "0.5rem 0.75rem", borderRadius: 6, border: "1px solid #d0d0d0", minWidth: 200 }}
          >
            <option value="">Select a run...</option>
            {completedRuns.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} ({r.prompt_version}) — {r.config.scenario_ids.length} scenarios
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Scorer name"
            value={scorer}
            onChange={(e) => setScorer(e.target.value)}
            style={{ padding: "0.5rem 0.75rem", borderRadius: 6, border: "1px solid #d0d0d0", flex: 1, minWidth: 150 }}
          />
          <button
            onClick={() => createMutation.mutate()}
            disabled={!scorer || !selectedRunId || createMutation.isPending}
            style={{
              background: !scorer || !selectedRunId ? "#ccc" : autoScore ? "#ff6b35" : "#6c63ff",
              color: "#fff",
              border: "none",
              padding: "0.5rem 1.25rem",
              borderRadius: 6,
              cursor: !scorer || !selectedRunId ? "default" : "pointer",
              whiteSpace: "nowrap",
            }}
          >
            {createMutation.isPending
              ? "Creating..."
              : autoScore
              ? `Auto-Score with ${scorerModels[scorerModel] || scorerModel}`
              : "Create Manual Session"}
          </button>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              fontSize: "0.85rem",
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={autoScore}
              onChange={(e) => setAutoScore(e.target.checked)}
            />
            <span>Auto-score</span>
          </label>
          {autoScore && (
            <select
              value={scorerModel}
              onChange={(e) => setScorerModel(e.target.value)}
              style={{ padding: "0.4rem 0.6rem", borderRadius: 6, border: "1px solid #d0d0d0", fontSize: "0.85rem" }}
            >
              {Object.entries(scorerModels).map(([id, label]) => (
                <option key={id} value={id}>{label}</option>
              ))}
            </select>
          )}
          {autoScore && (
            <span style={{ color: "#888", fontSize: "0.8rem" }}>
              (uses scenario rubrics as evaluation criteria)
            </span>
          )}
        </div>
        {createMutation.isError && (
          <p style={{ color: "#f44336", margin: "0.5rem 0 0", fontSize: "0.85rem" }}>
            {(createMutation.error as Error).message}
          </p>
        )}
        {createMutation.isSuccess && autoScore && (
          <p style={{ color: "#4caf50", margin: "0.5rem 0 0", fontSize: "0.85rem" }}>
            Auto-scoring session created. Scoring in the background...
          </p>
        )}
      </div>

      {sessions.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", background: "#fff", borderRadius: 8 }}>
          <thead>
            <tr>
              <th style={thStyle}>Session</th>
              <th style={thStyle}>Run</th>
              <th style={thStyle}>Scorer</th>
              <th style={thStyle}>Progress</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.session_id}>
                <td style={tdStyle}>{s.session_id}</td>
                <td style={{ ...tdStyle, fontSize: "0.8rem" }}>{s.run_id || "—"}</td>
                <td style={tdStyle}>{s.scorer}</td>
                <td style={tdStyle}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span>{s.scored_items}/{s.total_items}</span>
                    {s.scored_items > 0 && s.scored_items < s.total_items && (
                      <div style={{ background: "#e0e0e0", borderRadius: 4, height: 6, width: 60, overflow: "hidden" }}>
                        <div style={{ background: "#6c63ff", height: "100%", width: `${(s.scored_items / s.total_items) * 100}%` }} />
                      </div>
                    )}
                  </div>
                </td>
                <td style={tdStyle}>
                  {s.revealed
                    ? "Revealed"
                    : s.scored_items === s.total_items
                    ? "Complete"
                    : s.scorer.includes("opus-4.6-auto")
                    ? "Auto-scoring..."
                    : "In Progress"}
                </td>
                <td style={tdStyle}>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button
                      onClick={() => onSelectSession(s.session_id)}
                      style={{ color: "#6c63ff", background: "none", border: "none", cursor: "pointer", textDecoration: "underline", fontSize: "0.85rem" }}
                    >
                      {s.scored_items < s.total_items ? "Continue" : "View"}
                    </button>
                    {s.scored_items < s.total_items && s.scorer.includes("opus-4.6-auto") && (
                      <>
                        <button
                          onClick={async () => { await stopSession(s.session_id); refetch(); }}
                          style={{ color: "#f44336", background: "none", border: "none", cursor: "pointer", textDecoration: "underline", fontSize: "0.85rem" }}
                        >
                          Stop
                        </button>
                        <button
                          onClick={async () => { await retrySession(s.session_id); refetch(); }}
                          style={{ color: "#ff6b35", background: "none", border: "none", cursor: "pointer", textDecoration: "underline", fontSize: "0.85rem" }}
                        >
                          Retry
                        </button>
                      </>
                    )}
                    <button
                      onClick={async () => {
                        if (confirm("Delete this scoring session?")) {
                          await deleteMutation.mutateAsync(s.session_id);
                        }
                      }}
                      style={{ color: "#999", background: "none", border: "none", cursor: "pointer", textDecoration: "underline", fontSize: "0.85rem" }}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function ScoringInterface({ sessionId, onBack }: { sessionId: string; onBack: () => void }) {
  const [scores, setScores] = useState<Record<string, number>>({});
  const [rationale, setRationale] = useState("");

  const { data: item, refetch, isLoading } = useQuery({
    queryKey: ["scoring-next", sessionId],
    queryFn: () => fetchNextItem(sessionId),
  });

  const submitMutation = useMutation({
    mutationFn: (params: { itemId: string; scores: DimensionScore[] }) =>
      submitScore(sessionId, params.itemId, params.scores),
    onSuccess: () => {
      setScores({});
      setRationale("");
      refetch();
    },
  });

  const revealMutation = useMutation({
    mutationFn: () => revealSession(sessionId),
  });

  if (isLoading) return <p>Loading...</p>;

  // Check if complete
  if (item && "complete" in item && item.complete) {
    return (
      <div>
        <button onClick={onBack} style={backBtn}>&larr; Back</button>
        <h2>Scoring Complete</h2>
        <p>All {item.total} items have been scored.</p>
        {!revealMutation.data ? (
          <button
            onClick={() => revealMutation.mutate()}
            style={{ background: "#6c63ff", color: "#fff", border: "none", padding: "0.6rem 1.5rem", borderRadius: 6, cursor: "pointer" }}
          >
            Reveal Results
          </button>
        ) : (
          <div>
            <h3>Revealed Assignments</h3>
            <table style={{ width: "100%", borderCollapse: "collapse", background: "#fff" }}>
              <thead>
                <tr>
                  <th style={thStyle}>Item</th>
                  <th style={thStyle}>Scenario</th>
                  <th style={thStyle}>Model</th>
                  <th style={thStyle}>Condition</th>
                </tr>
              </thead>
              <tbody>
                {revealMutation.data.items.map((r: any) => (
                  <tr key={r.item_id}>
                    <td style={tdStyle}>{r.item_id}</td>
                    <td style={tdStyle}>{r.scenario_id}</td>
                    <td style={tdStyle}>{r.model}</td>
                    <td style={tdStyle}>{r.condition}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  const blindItem = item as BlindItem;

  const allScored = blindItem.dimensions.every((d) => scores[d] !== undefined);

  const handleSubmit = () => {
    const dimensionScores: DimensionScore[] = blindItem.dimensions.map((d) => ({
      dimension: d,
      score: scores[d],
      rationale: rationale || undefined,
    }));
    submitMutation.mutate({ itemId: blindItem.item_id, scores: dimensionScores });
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <button onClick={onBack} style={backBtn}>&larr; Back to Sessions</button>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h2 style={{ margin: 0 }}>Scoring {blindItem.position} of {blindItem.total}</h2>
        <div style={{ background: "#e0e0e0", borderRadius: 8, height: 8, width: 200, overflow: "hidden" }}>
          <div
            style={{
              background: "#6c63ff",
              height: "100%",
              width: `${(blindItem.position / blindItem.total) * 100}%`,
            }}
          />
        </div>
      </div>

      <details style={{ marginBottom: "1rem" }}>
        <summary style={{ cursor: "pointer", fontWeight: 600, color: "#444" }}>
          Scenario Prompt ({blindItem.scenario_id})
        </summary>
        <pre style={preStyle}>{blindItem.scenario_prompt}</pre>
      </details>

      <div style={{ background: "#fff", padding: "1.25rem", borderRadius: 8, border: "1px solid #e0e0e0", marginBottom: "1.5rem" }}>
        <h3 style={{ margin: "0 0 0.75rem", fontSize: "0.95rem", color: "#444" }}>Model Response</h3>
        <div style={{ maxHeight: 400, overflow: "auto", whiteSpace: "pre-wrap", fontSize: "0.9rem", lineHeight: 1.6 }}>
          {blindItem.response_text}
        </div>
      </div>

      <div style={{ background: "#fff", padding: "1.25rem", borderRadius: 8, marginBottom: "1rem" }}>
        <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem" }}>Score Dimensions (1-5)</h3>
        {blindItem.dimensions.map((dim) => (
          <div key={dim} style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.75rem" }}>
            <span style={{ width: 200, fontSize: "0.85rem", fontWeight: 500 }}>{dim}</span>
            <div style={{ display: "flex", gap: "0.25rem" }}>
              {[1, 2, 3, 4, 5].map((v) => (
                <button
                  key={v}
                  onClick={() => setScores((prev) => ({ ...prev, [dim]: v }))}
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 6,
                    border: scores[dim] === v ? "2px solid #6c63ff" : "1px solid #d0d0d0",
                    background: scores[dim] === v ? "#6c63ff" : "#fff",
                    color: scores[dim] === v ? "#fff" : "#333",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>
        ))}

        <textarea
          placeholder="Optional rationale..."
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          style={{
            width: "100%",
            minHeight: 60,
            padding: "0.5rem",
            borderRadius: 6,
            border: "1px solid #d0d0d0",
            marginTop: "0.5rem",
            fontSize: "0.85rem",
            resize: "vertical",
          }}
        />
      </div>

      <button
        onClick={handleSubmit}
        disabled={!allScored || submitMutation.isPending}
        style={{
          background: allScored ? "#6c63ff" : "#ccc",
          color: "#fff",
          border: "none",
          padding: "0.6rem 1.5rem",
          borderRadius: 6,
          cursor: allScored ? "pointer" : "default",
          fontSize: "0.9rem",
        }}
      >
        {submitMutation.isPending ? "Submitting..." : "Submit & Next"}
      </button>
    </div>
  );
}

const backBtn: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "#6c63ff",
  cursor: "pointer",
  marginBottom: "1rem",
  display: "block",
  padding: 0,
  fontSize: "0.85rem",
};

const preStyle: React.CSSProperties = {
  whiteSpace: "pre-wrap",
  background: "#fafafa",
  padding: "1rem",
  borderRadius: 6,
  fontSize: "0.85rem",
  lineHeight: 1.5,
  marginTop: "0.5rem",
};

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
  fontSize: "0.85rem",
};
