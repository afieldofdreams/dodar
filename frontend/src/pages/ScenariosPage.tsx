import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchScenarios } from "../api/scenarios";
import { CATEGORIES } from "../types";

const DIFFICULTY_COLORS = {
  easy: "#4caf50",
  medium: "#ff9800",
  hard: "#f44336",
};

export default function ScenariosPage() {
  const [category, setCategory] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [search, setSearch] = useState("");

  const { data: scenarios = [], isLoading } = useQuery({
    queryKey: ["scenarios", category, difficulty, search],
    queryFn: () =>
      fetchScenarios({
        category: category || undefined,
        difficulty: difficulty || undefined,
        search: search || undefined,
      }),
  });

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Scenarios</h1>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
        <select value={category} onChange={(e) => setCategory(e.target.value)} style={selectStyle}>
          <option value="">All Categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} style={selectStyle}>
          <option value="">All Difficulties</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>

        <input
          type="text"
          placeholder="Search scenarios..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ ...selectStyle, flex: 1, minWidth: 200 }}
        />
      </div>

      {isLoading ? (
        <p>Loading scenarios...</p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
            gap: "1rem",
          }}
        >
          {scenarios.map((s) => (
            <Link
              key={s.id}
              to={`/scenarios/${s.id}`}
              style={{
                textDecoration: "none",
                color: "inherit",
                background: "#fff",
                borderRadius: 8,
                padding: "1.25rem",
                border: "1px solid #e0e0e0",
                transition: "box-shadow 0.2s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.1)")
              }
              onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontWeight: 600, color: "#6c63ff" }}>{s.id}</span>
                <span
                  style={{
                    fontSize: "0.75rem",
                    padding: "2px 8px",
                    borderRadius: 4,
                    background: DIFFICULTY_COLORS[s.difficulty] + "20",
                    color: DIFFICULTY_COLORS[s.difficulty],
                    fontWeight: 600,
                  }}
                >
                  {s.difficulty}
                </span>
              </div>
              <h3 style={{ margin: "0 0 0.5rem", fontSize: "1rem" }}>{s.title}</h3>
              <div style={{ display: "flex", gap: "0.5rem", fontSize: "0.8rem", color: "#666" }}>
                <span
                  style={{
                    background: "#e8e8f0",
                    padding: "2px 6px",
                    borderRadius: 4,
                  }}
                >
                  {s.category}
                </span>
                <span
                  style={{
                    background: "#e8e8f0",
                    padding: "2px 6px",
                    borderRadius: 4,
                  }}
                >
                  {s.domain}
                </span>
                <span>{s.discriminators.length} discriminator{s.discriminators.length !== 1 ? "s" : ""}</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {!isLoading && scenarios.length === 0 && (
        <p style={{ color: "#666" }}>No scenarios match your filters.</p>
      )}
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
