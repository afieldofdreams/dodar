import { get, post } from "./client";

export interface BenchmarkTaskSummary {
  id: string;
  source: string;
  category: string;
  answer_type: string;
  word_count: number | null;
  question_preview: string;
}

export interface BenchmarkCondition {
  code: string;
  name: string;
  deprecated?: boolean;
}

export interface BenchmarkRunSummary {
  run_id: string;
  config: {
    task_ids: string[] | null;
    models: string[];
    conditions: string[];
    runs_per_task: number;
    skip_completed: boolean;
    prompt_version: string;
    execution_seed: number;
    stage: string;
  };
  status: string;
  created_at: string;
  completed_at: string | null;
  total_items: number;
  completed_items: number;
  correct_items: number;
  total_cost_usd: number;
  total_tokens: number;
  accuracy_by_condition: Record<string, number>;
  dropouts: Array<{ task_id: string; model: string; condition: string; error: string }>;
}

export interface BenchmarkResult {
  task_id: string;
  condition: string;
  model_id: string;
  run_number: number;
  timestamp: string;
  latency_seconds: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  raw_response: string;
  extracted_answer: string | null;
  is_correct: boolean | null;
  correct_answer: string;
  answer_type: string;
  question: string | null;
  source: string | null;
}

export interface AccuracySummary {
  total: number;
  total_correct: number;
  overall_accuracy: number;
  by_condition: Record<string, { correct: number; total: number; accuracy: number; name: string }>;
  by_source: Record<string, { correct: number; total: number; accuracy: number }>;
  by_model: Record<string, { correct: number; total: number; accuracy: number }>;
}

export function fetchBenchmarkTasks(taskVersion?: string): Promise<BenchmarkTaskSummary[]> {
  const qs = taskVersion ? `?task_version=${taskVersion}` : "";
  return get<BenchmarkTaskSummary[]>(`/benchmark/tasks${qs}`);
}

export function fetchBenchmarkConditions(includeDeprecated: boolean = true): Promise<BenchmarkCondition[]> {
  return get<BenchmarkCondition[]>(`/benchmark/conditions?include_deprecated=${includeDeprecated}`);
}

export function fetchBenchmarkRuns(): Promise<BenchmarkRunSummary[]> {
  return get<BenchmarkRunSummary[]>("/benchmark/runs");
}

export function fetchBenchmarkRun(runId: string): Promise<BenchmarkRunSummary> {
  return get<BenchmarkRunSummary>(`/benchmark/runs/${runId}`);
}

export function fetchBenchmarkRunResults(runId: string): Promise<BenchmarkResult[]> {
  return get<BenchmarkResult[]>(`/benchmark/runs/${runId}/results`);
}

export function startBenchmarkRun(config: {
  task_ids?: string[] | null;
  models: string[];
  conditions: string[];
  runs_per_task?: number;
  skip_completed?: boolean;
  stage?: string;
  task_version?: string;
}): Promise<{ run_id: string; total_items: number; models: string[]; conditions: string[]; stage: string }> {
  return post("/benchmark/runs", config);
}

export function cancelBenchmarkRun(runId: string): Promise<{ status: string }> {
  return post(`/benchmark/runs/${runId}/cancel`, {});
}

export function fetchAccuracySummary(params?: { model_id?: string; prompt_version?: string }): Promise<AccuracySummary> {
  const qs = new URLSearchParams();
  if (params?.model_id) qs.set("model_id", params.model_id);
  if (params?.prompt_version) qs.set("prompt_version", params.prompt_version);
  const suffix = qs.toString() ? `?${qs}` : "";
  return get<AccuracySummary>(`/benchmark/accuracy${suffix}`);
}

export interface BenchmarkEstimate {
  total_calls: number;
  models: Array<{ model: string; calls: number; estimated_cost_usd: number }>;
  benchmark_cost_usd: number;
  error_classification: {
    estimated_incorrect: number;
    classification_calls: number;
    scorers: string[];
    estimated_cost_usd: number;
  };
  total_estimated_cost_usd: number;
}

export interface ErrorClassificationResult {
  total_results: number;
  incorrect: number;
  classifications: number;
  file: string;
  agreement: {
    kappa: number | null;
    exact_agreement: number;
    n_pairs: number;
    exact_matches: number;
    raters: string[];
  };
  by_rater: Record<string, Record<string, number>>;
  by_condition: Record<string, Record<string, number>>;
}

export function classifyErrors(config: {
  run_id?: string;
  scorer_a?: string;
  scorer_b?: string;
}): Promise<ErrorClassificationResult> {
  return post("/benchmark/classify-errors", config);
}

export function fetchErrorClassifications(): Promise<Array<{ file: string; count: number; timestamp: string }>> {
  return get("/benchmark/error-classifications");
}

export function fetchErrorClassificationDetail(filename: string): Promise<{
  classifications: Array<{
    task_id: string;
    condition: string;
    model_id: string;
    classification: string;
    reasoning: string;
    root_cause_quote: string | null;
    confidence: string;
    rater: string;
  }>;
  agreement: { kappa: number | null; exact_agreement: number; n_pairs: number; raters: string[] };
  by_condition: Record<string, Record<string, number>>;
  total: number;
}> {
  return get(`/benchmark/error-classifications/${filename}`);
}

export function fetchAnalysis(params?: { run_id?: string }): Promise<Record<string, any>> {
  const qs = new URLSearchParams();
  if (params?.run_id) qs.set("run_id", params.run_id);
  const suffix = qs.toString() ? `?${qs}` : "";
  return get(`/benchmark/analysis${suffix}`);
}

export function estimateBenchmarkCost(config: {
  task_ids?: string[] | null;
  models: string[];
  conditions: string[];
  runs_per_task?: number;
}): Promise<BenchmarkEstimate> {
  return post("/benchmark/estimate", config);
}
