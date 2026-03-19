import { get, post, del as apiDel } from "./client";
import type { ScoringSessionSummary, BlindItem, DimensionScore } from "../types";

export function fetchSessions(): Promise<ScoringSessionSummary[]> {
  return get<ScoringSessionSummary[]>("/scoring/sessions");
}

export function createSession(config: {
  scorer: string;
  run_id: string;
  auto_score?: boolean;
}): Promise<{ session_id: string; run_id: string; total_items: number; scorer: string; auto_score: boolean }> {
  return post("/scoring/sessions", config);
}

export function deleteSession(sessionId: string): Promise<{ status: string }> {
  return apiDel(`/scoring/sessions/${sessionId}`);
}

export function fetchNextItem(
  sessionId: string
): Promise<BlindItem | { complete: true; total: number; scored: number }> {
  return get(`/scoring/sessions/${sessionId}/next`);
}

export function submitScore(
  sessionId: string,
  itemId: string,
  scores: DimensionScore[]
): Promise<{ scored: number; total: number }> {
  return post(`/scoring/sessions/${sessionId}/items/${itemId}/score`, { scores });
}

export function fetchProgress(
  sessionId: string
): Promise<{ scored: number; total: number }> {
  return get(`/scoring/sessions/${sessionId}/progress`);
}

export function retrySession(
  sessionId: string
): Promise<{ status: string; unscored?: number; total?: number }> {
  return post(`/scoring/sessions/${sessionId}/retry`, {});
}

export function stopSession(
  sessionId: string
): Promise<{ status: string; session_id: string }> {
  return post(`/scoring/sessions/${sessionId}/stop`, {});
}

export function revealSession(sessionId: string): Promise<{ revealed: boolean; items: any[] }> {
  return post(`/scoring/sessions/${sessionId}/reveal`, {});
}
