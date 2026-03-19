export interface Discriminator {
  dimension: string;
  description: string;
}

export interface Scenario {
  id: string;
  category: string;
  title: string;
  domain: string;
  difficulty: "easy" | "medium" | "hard";
  prompt_text: string;
  expected_pitfalls: string[];
  gold_standard_elements: string[];
  discriminators: Discriminator[];
}

export interface ScenarioDetail extends Scenario {
  run_matrix: Record<string, Record<string, string>>;
}

export interface RunSummary {
  run_id: string;
  config: RunConfig;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  created_at: string;
  completed_at: string | null;
  prompt_version: string;
  total_items: number;
  completed_items: number;
  total_cost_usd: number;
  total_tokens: number;
}

export interface RunConfig {
  scenario_ids: string[];
  models: string[];
  conditions: string[];
  skip_completed: boolean;
}

export interface CostEstimate {
  model: string;
  condition: string;
  scenario_count: number;
  estimated_input_tokens: number;
  estimated_output_tokens: number;
  estimated_cost_usd: number;
}

export interface ScoringSessionSummary {
  session_id: string;
  scorer: string;
  run_id: string;
  created_at: string;
  total_items: number;
  scored_items: number;
  revealed: boolean;
}

export interface BlindItem {
  item_id: string;
  position: number;
  total: number;
  scenario_id: string;
  scenario_prompt: string;
  response_text: string;
  dimensions: string[];
}

export interface DimensionScore {
  dimension: string;
  score: number;
  rationale?: string;
}

export interface DashboardStats {
  dimension: string;
  model: string;
  condition: string;
  mean: number;
  std: number;
  count: number;
}

export interface EffectSize {
  dimension: string;
  model: string;
  baseline_condition: string;
  cohens_d: number;
  baseline_mean: number;
  dodar_mean: number;
}

export interface DashboardData {
  stats: DashboardStats[];
  effect_sizes: EffectSize[];
  summary: {
    total_sessions: number;
    total_scored: number;
    dimensions: string[];
  };
  prompt_version: string | null;
}

export interface ProgressEvent {
  type: "item_start" | "item_complete" | "item_error" | "run_complete" | "run_error";
  scenario_id?: string;
  model?: string;
  condition?: string;
  progress: { completed: number; total: number };
  tokens_used?: number;
  cost_usd?: number;
  error?: string;
  summary?: {
    total_cost_usd: number;
    total_tokens: number;
    duration_seconds: number;
  };
}

export const MODELS = ["claude-sonnet-4-5", "gpt-4o", "gemini-2.0-flash"] as const;
export const CONDITIONS = ["zero_shot", "cot", "length_matched", "dodar"] as const;
export const CATEGORIES = ["AMB", "TRD", "IRR", "ETH", "MUL", "CAS", "TIM"] as const;
