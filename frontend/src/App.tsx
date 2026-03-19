import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AppShell from "./components/layout/AppShell";
import DashboardPage from "./pages/DashboardPage";
import ScenariosPage from "./pages/ScenariosPage";
import ScenarioDetailPage from "./pages/ScenarioDetailPage";
import RunsPage from "./pages/RunsPage";
import NewRunPage from "./pages/NewRunPage";
import RunProgressPage from "./pages/RunProgressPage";
import ScoringPage from "./pages/ScoringPage";
import ExportPage from "./pages/ExportPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/scenarios" element={<ScenariosPage />} />
            <Route path="/scenarios/:id" element={<ScenarioDetailPage />} />
            <Route path="/runs" element={<RunsPage />} />
            <Route path="/runs/new" element={<NewRunPage />} />
            <Route path="/runs/:id" element={<RunProgressPage />} />
            <Route path="/scoring" element={<ScoringPage />} />
            <Route path="/export" element={<ExportPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
