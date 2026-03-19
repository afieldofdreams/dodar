import { get, post, del as apiDel } from "./client";
import type { RunSummary, CostEstimate } from "../types";

export function fetchRuns(): Promise<RunSummary[]> {
  return get<RunSummary[]>("/runs");
}

export function fetchRun(runId: string): Promise<RunSummary> {
  return get<RunSummary>(`/runs/${runId}`);
}

export function startRun(config: {
  scenario_ids?: string[];
  models?: string[];
  conditions?: string[];
  skip_completed?: boolean;
}): Promise<{ run_id: string; total_items: number }> {
  return post("/runs", config);
}

export function cancelRun(runId: string): Promise<{ status: string }> {
  return post(`/runs/${runId}/cancel`, {});
}

export function deleteRun(runId: string): Promise<{ status: string; files_removed: number }> {
  return apiDel(`/runs/${runId}`);
}

export function estimateCost(config: {
  scenario_ids?: string[];
  models?: string[];
  conditions?: string[];
}): Promise<CostEstimate[]> {
  return post("/runs/estimate", config);
}
