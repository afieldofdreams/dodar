import { Outlet, NavLink } from "react-router-dom";

const NAV_SECTIONS = [
  {
    label: "Framework",
    items: [
      { to: "/", label: "Playground" },
      { to: "/docs", label: "Documentation" },
    ],
  },
  {
    label: "Benchmark",
    items: [
      { to: "/benchmark/new", label: "New Run" },
      { to: "/benchmark/results", label: "Results" },
    ],
  },
  {
    label: "Scenarios",
    items: [
      { to: "/runs/new", label: "New Run" },
      { to: "/dashboard", label: "Results" },
      { to: "/scenarios", label: "Browse" },
      { to: "/runs", label: "Run History" },
      { to: "/scoring", label: "Scoring" },
      { to: "/export", label: "Export" },
    ],
  },
];

export default function AppShell() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <nav className="w-56 shrink-0 bg-surface border-r border-border flex flex-col">
        {/* Logo */}
        <div className="px-5 pt-5 pb-6">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-purple-400 flex items-center justify-center text-sm font-extrabold text-white">
              D
            </div>
            <div>
              <h1 className="text-[15px] font-bold text-white tracking-tight leading-none">
                DODAR
              </h1>
              <p className="text-[10px] text-zinc-500 uppercase tracking-widest mt-0.5">
                Reasoning Framework
              </p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <div className="flex-1 overflow-y-auto">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} className="mb-2">
              <div className="px-5 pt-3 pb-1.5 text-[10px] font-semibold text-zinc-500 uppercase tracking-[0.12em]">
                {section.label}
              </div>
              <ul className="space-y-0.5">
                {section.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.to === "/"}
                      className={({ isActive }) =>
                        `block px-5 py-2 text-[13px] transition-colors border-l-2 ${
                          isActive
                            ? "bg-accent-dim text-white font-medium border-accent"
                            : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03] border-transparent"
                        }`
                      }
                    >
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-border text-xs text-zinc-500">
          <a
            href="https://github.com/afieldofdreams/dodar"
            target="_blank"
            rel="noopener"
            className="text-zinc-400 hover:text-zinc-200 no-underline"
          >
            GitHub ↗
          </a>
          <span className="mx-2">·</span>
          <span className="text-zinc-600">pip install dodar</span>
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto max-h-screen p-8">
        <Outlet />
      </main>
    </div>
  );
}
