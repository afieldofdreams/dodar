import { Outlet, NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard" },
  { to: "/scenarios", label: "Scenarios" },
  { to: "/runs", label: "Runs" },
  { to: "/scoring", label: "Scoring" },
  { to: "/export", label: "Export" },
];

export default function AppShell() {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <nav
        style={{
          width: 220,
          background: "#1a1a2e",
          color: "#e0e0e0",
          padding: "1.5rem 0",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: "0 1.25rem 1.5rem",
            borderBottom: "1px solid #2a2a4a",
            marginBottom: "1rem",
          }}
        >
          <h1 style={{ fontSize: "1.1rem", margin: 0, color: "#fff" }}>DODAR Benchmark</h1>
          <p style={{ fontSize: "0.75rem", margin: "0.25rem 0 0", opacity: 0.6 }}>
            Validation Suite
          </p>
        </div>
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                style={({ isActive }) => ({
                  display: "block",
                  padding: "0.6rem 1.25rem",
                  color: isActive ? "#fff" : "#a0a0c0",
                  background: isActive ? "#2a2a4a" : "transparent",
                  textDecoration: "none",
                  fontSize: "0.9rem",
                  borderLeft: isActive ? "3px solid #6c63ff" : "3px solid transparent",
                })}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <main style={{ flex: 1, padding: "2rem", background: "#f5f5f8", overflow: "auto" }}>
        <Outlet />
      </main>
    </div>
  );
}
