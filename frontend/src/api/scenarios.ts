import { get } from "./client";
import type { Scenario, ScenarioDetail } from "../types";

export function fetchScenarios(params?: {
  category?: string;
  difficulty?: string;
  search?: string;
}): Promise<Scenario[]> {
  const q = new URLSearchParams();
  if (params?.category) q.set("category", params.category);
  if (params?.difficulty) q.set("difficulty", params.difficulty);
  if (params?.search) q.set("search", params.search);
  const qs = q.toString();
  return get<Scenario[]>(`/scenarios${qs ? `?${qs}` : ""}`);
}

export function fetchScenario(id: string): Promise<ScenarioDetail> {
  return get<ScenarioDetail>(`/scenarios/${id}`);
}
