import { get } from "./client";
import type { DashboardData } from "../types";

export function fetchVersions(): Promise<string[]> {
  return get<string[]>("/reports/versions");
}

export function fetchDashboard(promptVersion?: string): Promise<DashboardData> {
  const q = promptVersion ? `?prompt_version=${promptVersion}` : "";
  return get<DashboardData>(`/reports/dashboard${q}`);
}

export function fetchComparison(promptVersion?: string): Promise<{
  pivot: Record<string, Record<string, Record<string, number>>>;
  dimensions: string[];
}> {
  const q = promptVersion ? `?prompt_version=${promptVersion}` : "";
  return get(`/reports/comparison${q}`);
}

export function fetchStats(promptVersion?: string): Promise<{ effect_sizes: any[] }> {
  const q = promptVersion ? `?prompt_version=${promptVersion}` : "";
  return get(`/reports/stats${q}`);
}

export function getExportUrl(format: "json" | "csv" = "json", promptVersion?: string): string {
  let url = `/api/reports/export?format=${format}`;
  if (promptVersion) url += `&prompt_version=${promptVersion}`;
  return url;
}
