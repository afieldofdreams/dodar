import { Outlet, NavLink } from "react-router-dom";

const NAV_SECTIONS = [
  {
    label: "Framework",
    items: [
      { to: "/", label: "Playground", icon: "▸" },
      { to: "/docs", label: "Documentation", icon: "◆" },
    ],
  },
  {
    label: "Benchmark",
    items: [
      { to: "/dashboard", label: "Results", icon: "◉" },
      { to: "/scenarios", label: "Scenarios", icon: "▦" },
      { to: "/runs", label: "Runs", icon: "↻" },
      { to: "/scoring", label: "Scoring", icon: "★" },
      { to: "/export", label: "Export", icon: "↓" },
    ],
  },
];

export default function AppShell() {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <nav
        style={{
          width: 240,
          background: "var(--bg-surface)",
          borderRight: "1px solid var(--border)",
          padding: "1.5rem 0",
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Logo */}
        <div style={{ padding: "0 1.25rem 1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                background: "linear-gradient(135deg, var(--accent), #a78bfa)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.9rem",
                fontWeight: 800,
                color: "#fff",
              }}
            >
              D
            </div>
            <div>
              <h1 style={{ fontSize: "1.05rem", margin: 0, color: "#fff", fontWeight: 700, letterSpacing: "-0.02em" }}>
                DODAR
              </h1>
              <p style={{ fontSize: "0.65rem", margin: 0, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                Reasoning Framework
              </p>
            </div>
          </div>
        </div>

        {/* Nav sections */}
        <div style={{ flex: 1 }}>
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} style={{ marginBottom: "0.5rem" }}>
              <div
                style={{
                  padding: "0.5rem 1.25rem 0.3rem",
                  fontSize: "0.65rem",
                  color: "var(--text-muted)",
                  textTransform: "uppercase",
                  letterSpacing: "0.12em",
                  fontWeight: 600,
                }}
              >
                {section.label}
              </div>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {section.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.to === "/"}
                      style={({ isActive }) => ({
                        display: "flex",
                        alignItems: "center",
                        gap: "0.6rem",
                        padding: "0.5rem 1.25rem",
                        color: isActive ? "#fff" : "var(--text-secondary)",
                        background: isActive ? "var(--accent-dim)" : "transparent",
                        textDecoration: "none",
                        fontSize: "0.85rem",
                        borderLeft: isActive ? "2px solid var(--accent)" : "2px solid transparent",
                        transition: "all 0.15s",
                      })}
                    >
                      <span style={{ opacity: 0.6, fontSize: "0.75rem" }}>{item.icon}</span>
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "1rem 1.25rem",
            borderTop: "1px solid var(--border)",
            fontSize: "0.75rem",
            color: "var(--text-muted)",
          }}
        >
          <a
            href="https://github.com/afieldofdreams/dodar"
            target="_blank"
            rel="noopener"
            style={{ color: "var(--text-secondary)", textDecoration: "none" }}
          >
            GitHub ↗
          </a>
          <span style={{ margin: "0 0.5rem" }}>·</span>
          <span>pip install dodar</span>
        </div>
      </nav>

      <main style={{ flex: 1, padding: "2rem 3rem", overflow: "auto", maxHeight: "100vh" }}>
        <Outlet />
      </main>
    </div>
  );
}
