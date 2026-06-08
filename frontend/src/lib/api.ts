import axios from "axios";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// ── Types ──────────────────────────────────────────────────────────────────

export interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  model_id: string;
  base_url: string | null;
  is_active: boolean;
  is_local: boolean;
  cost_per_input_token: number | null;
  cost_per_output_token: number | null;
  created_at: string;
}

export interface ModelConfigCreate {
  name: string;
  provider: string;
  model_id: string;
  api_key?: string;
  base_url?: string;
  is_local?: boolean;
  cost_per_input_token?: number;
  cost_per_output_token?: number;
}

export interface EvalResult {
  id: string;
  model_config_id: string;
  response: string | null;
  latency_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_usd: number | null;
  error: string | null;
  created_at: string;
}

export interface Evaluation {
  id: string;
  name: string | null;
  prompt: string;
  status: "pending" | "running" | "completed" | "failed";
  results: EvalResult[];
  created_at: string;
  updated_at: string;
}

export interface EvaluationListItem {
  id: string;
  name: string | null;
  prompt: string;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
}

export interface EvaluationCreate {
  prompt: string;
  model_ids: string[];
  name?: string;
}

export interface Prompt {
  id: string;
  name: string;
  content: string;
  description: string | null;
  version: number;
  parent_id: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export interface PromptCreate {
  name: string;
  content: string;
  description?: string;
  tags?: string;
}

export interface CostSummary {
  total_usd: number;
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
}

export interface TestSuite {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  cases: TestCase[];
  created_at: string;
  updated_at: string;
}

export interface TestCase {
  id: string;
  input: string;
  expected_output: string | null;
  expected_tags: string | null;
  created_at: string;
}

export interface TestSuiteCreate {
  name: string;
  description?: string;
  category?: string;
  cases?: { input: string; expected_output?: string; expected_tags?: string }[];
}

// ── Models API ────────────────────────────────────────────────────────────

export const modelsApi = {
  list: () => apiClient.get<ModelConfig[]>("/api/v1/models").then((r) => r.data),
  create: (data: ModelConfigCreate) =>
    apiClient.post<ModelConfig>("/api/v1/models", data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/api/v1/models/${id}`),
};

// ── Evaluations API ───────────────────────────────────────────────────────

export const evaluationsApi = {
  list: () => apiClient.get<EvaluationListItem[]>("/api/v1/evaluations").then((r) => r.data),
  get: (id: string) => apiClient.get<Evaluation>(`/api/v1/evaluations/${id}`).then((r) => r.data),
  create: (data: EvaluationCreate) =>
    apiClient.post<Evaluation>("/api/v1/evaluations", data).then((r) => r.data),
};

// ── Prompts API ───────────────────────────────────────────────────────────

export const promptsApi = {
  list: () => apiClient.get<Prompt[]>("/api/v1/prompts").then((r) => r.data),
  get: (id: string) => apiClient.get<Prompt>(`/api/v1/prompts/${id}`).then((r) => r.data),
  create: (data: PromptCreate) =>
    apiClient.post<Prompt>("/api/v1/prompts", data).then((r) => r.data),
  update: (id: string, data: PromptCreate) =>
    apiClient.put<Prompt>(`/api/v1/prompts/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/api/v1/prompts/${id}`),
};

// ── Cost API ──────────────────────────────────────────────────────────────

export const costApi = {
  summary: () => apiClient.get<CostSummary>("/api/v1/cost/summary").then((r) => r.data),
};

// ── Test Suites API ───────────────────────────────────────────────────────

export const testSuitesApi = {
  list: () => apiClient.get<TestSuite[]>("/api/v1/test-suites").then((r) => r.data),
  get: (id: string) => apiClient.get<TestSuite>(`/api/v1/test-suites/${id}`).then((r) => r.data),
  create: (data: TestSuiteCreate) =>
    apiClient.post<TestSuite>("/api/v1/test-suites", data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/api/v1/test-suites/${id}`),
};
