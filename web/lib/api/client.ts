import type {
  AllocationOut,
  AllocationRequest,
  ChatResponse,
  ChatSessionOut,
  FinancialPlan,
  FullProfile,
  GoalAnalysisOut,
  GoalCreate,
  GoalOut,
  GoalProgressOut,
  GoalUpdate,
  HealthScoreOut,
  HoldingCreate,
  HoldingOut,
  LoginRequest,
  LoginResponse,
  MessageResponse,
  PageOut,
  PortfolioCreate,
  PortfolioOut,
  PortfolioSnapshotOut,
  RebalanceOut,
  RecommendationOut,
  RegisterRequest,
  ScenarioCreate,
  ScenarioOut,
  SimulationCreate,
  SimulationOut,
  SystemHealth,
  SystemInfo,
  SystemReady,
  TokenPair,
  ToolResult,
  AiMemoryEntry,
  UserOut,
} from "@/types/api";

/**
 * Typed API surface. Every function calls the backend — the frontend
 * never performs financial calculations itself. All routes are proxied
 * through Next.js rewrites to the FastAPI backend (see next.config.mjs).
 */
export const api = {
  // ── Auth ──────────────────────────────────────────────────────────
  register: (body: RegisterRequest) =>
    request<LoginResponse>("/auth/register", { method: "POST", body }),

  login: (body: LoginRequest) =>
    request<LoginResponse>("/auth/login", { method: "POST", body }),

  refresh: (refresh_token: string) =>
    request<RefreshResponse>("/auth/refresh", {
      method: "POST",
      body: { refresh_token },
      auth: false,
    }),

  logout: (refresh_token?: string) =>
    request<MessageResponse>("/auth/logout", {
      method: "POST",
      body: { refresh_token },
    }),

  requestPasswordReset: (email: string) =>
    request<MessageResponse>("/auth/password-reset/request", {
      method: "POST",
      body: { email },
      auth: false,
    }),

  confirmPasswordReset: (token: string, new_password: string) =>
    request<MessageResponse>("/auth/password-reset/confirm", {
      method: "POST",
      body: { token, new_password },
      auth: false,
    }),

  // ── System ────────────────────────────────────────────────────────
  systemHealth: () => request<SystemHealth>("/system/health", { auth: false }),
  systemReady: () => request<SystemReady>("/system/ready", { auth: false }),
  systemInfo: () => request<SystemInfo>("/system/info", { auth: false }),

  // ── Profile ───────────────────────────────────────────────────────
  getFullProfile: () => request<FullProfile>("/profile"),
  getUserProfile: () => request<FullProfile["profile"]>("/profile/user"),
  upsertUserProfile: (body: Record<string, unknown>) =>
    request<FullProfile["profile"]>("/profile/user", { method: "PUT", body }),
  getFinancialProfile: () => request<FullProfile["financial_profile"]>("/profile/financial"),
  upsertFinancialProfile: (body: Record<string, unknown>) =>
    request<FullProfile["financial_profile"]>("/profile/financial", { method: "PUT", body }),
  getBehavioralProfile: () => request<FullProfile["behavioral_profile"]>("/profile/behavioral"),
  upsertBehavioralProfile: (body: Record<string, unknown>) =>
    request<FullProfile["behavioral_profile"]>("/profile/behavioral", { method: "PUT", body }),
  getRiskAssessment: () => request<FullProfile["risk"]>("/profile/risk"),

  // ── Goals ─────────────────────────────────────────────────────────
  listGoals: () => request<GoalOut[]>("/goals"),
  getGoal: (id: string) => request<GoalOut>(`/goals/${id}`),
  createGoal: (body: GoalCreate) =>
    request<GoalOut>("/goals", { method: "POST", body }),
  updateGoal: (id: string, body: GoalUpdate) =>
    request<GoalOut>(`/goals/${id}`, { method: "PATCH", body }),
  deleteGoal: (id: string) =>
    request<MessageResponse>(`/goals/${id}`, { method: "DELETE" }),
  analyseGoals: () => request<GoalAnalysisOut[]>("/goals/analysis"),
  analyseGoal: (id: string) => request<GoalAnalysisOut>(`/goals/${id}/analysis`),
  recordGoalProgress: (id: string) =>
    request<GoalProgressOut>(`/goals/${id}/progress`, { method: "POST" }),

  // ── Portfolio ─────────────────────────────────────────────────────
  listPortfolios: () => request<PortfolioOut[]>("/portfolio"),
  getPortfolio: (id: string) => request<PortfolioOut>(`/portfolio/${id}`),
  createPortfolio: (body: PortfolioCreate) =>
    request<PortfolioOut>("/portfolio", { method: "POST", body }),
  addHolding: (portfolioId: string, body: HoldingCreate) =>
    request<HoldingOut>(`/portfolio/${portfolioId}/holdings`, { method: "POST", body }),
  listHoldings: (portfolioId: string) =>
    request<HoldingOut[]>(`/portfolio/${portfolioId}/holdings`),
  deleteHolding: (portfolioId: string, holdingId: string) =>
    request<MessageResponse>(`/portfolio/${portfolioId}/holdings/${holdingId}`, {
      method: "DELETE",
    }),
  captureSnapshot: (portfolioId: string) =>
    request<PortfolioSnapshotOut>(`/portfolio/${portfolioId}/snapshot`, { method: "POST" }),

  // ── Allocation ────────────────────────────────────────────────────
  computeAllocation: (body: AllocationRequest = {}) =>
    request<AllocationOut>("/allocation", { method: "POST", body }),

  // ── Rebalance ─────────────────────────────────────────────────────
  rebalance: (portfolioId: string, target?: Record<string, number> | null) =>
    request<RebalanceOut>(`/rebalance/${portfolioId}`, {
      method: "POST",
      body: target ?? {},
    }),

  // ── Recommendations ───────────────────────────────────────────────
  listRecommendations: (limit = 50) =>
    request<RecommendationOut[]>(`/recommendations?limit=${limit}`),
  generateRecommendations: (hoursValid = 24) =>
    request<RecommendationOut[]>(`/recommendations/generate?hours_valid=${hoursValid}`, {
      method: "POST",
    }),
  updateRecommendationStatus: (id: string, status: string) =>
    request<RecommendationOut>(`/recommendations/${id}`, {
      method: "PATCH",
      body: { status },
    }),
  dismissRecommendation: (id: string) =>
    request<MessageResponse>(`/recommendations/${id}`, { method: "DELETE" }),

  // ── Health Score ──────────────────────────────────────────────────
  computeHealthScore: () =>
    request<HealthScoreOut>("/health-score", { method: "POST" }),
  latestHealthScores: (limit = 10) =>
    request<HealthScoreOut[]>(`/health-score/latest?limit=${limit}`),

  // ── Simulation ────────────────────────────────────────────────────
  runSimulation: (body: SimulationCreate) =>
    request<SimulationOut & Record<string, unknown>>("/simulation", { method: "POST", body }),
  listSimulations: (limit = 50) =>
    request<Array<Record<string, unknown>>>(`/simulation?limit=${limit}`),

  // ── Scenarios ─────────────────────────────────────────────────────
  runScenario: (body: ScenarioCreate) =>
    request<ScenarioOut & Record<string, unknown>>("/scenarios", { method: "POST", body }),
  listScenarios: (limit = 50) =>
    request<Array<Record<string, unknown>>>(`/scenarios?limit=${limit}`),

  // ── Planner ───────────────────────────────────────────────────────
  getPlan: () => request<FinancialPlan>("/planner/plan"),

  // ── Chat / AI ─────────────────────────────────────────────────────
  aiChat: (body: { session_id?: string | null; message: string; context?: Record<string, unknown> }) =>
    request<ChatResponse>("/ai/chat", { method: "POST", body }),
  listChatSessions: () => request<ChatSessionOut[]>("/chat"),
  createChatSession: (title = "New chat") =>
    request<ChatSessionOut>("/chat", { method: "POST", body: { title } }),
  getChatSession: (id: string) => request<ChatSessionOut>(`/chat/${id}`),
  deleteChatSession: (id: string) =>
    request<MessageResponse>(`/chat/${id}`, { method: "DELETE" }),
  listAgents: () => request<Array<Record<string, unknown>>>("/ai/agents"),
  listTools: () => request<Array<Record<string, unknown>>>("/ai/tools"),
  aiExecuteTool: (toolName: string, arguments_: Record<string, unknown> = {}, confirm = false) =>
    request<ToolResult>("/ai/tools/execute", {
      method: "POST",
      body: { tool_name: toolName, arguments: arguments_, confirm },
    }),
  aiHealth: () => request<Record<string, unknown>>("/ai/health"),
  aiMemory: (query = "", limit = 10) =>
    request<AiMemoryEntry[]>(`/ai/memory?query=${encodeURIComponent(query)}&limit=${limit}`),
  aiStoreMemory: (content: string, memoryType = "conversation", metadata: Record<string, unknown> = {}) =>
    request<{ id: string; status: string }>("/ai/memory", {
      method: "POST",
      body: { memory_type: memoryType, content, metadata },
    }),
  research: (query: string, assetClass?: string | null) =>
    request<Record<string, unknown>>("/ai/research", {
      method: "POST",
      body: { query, asset_class: assetClass ?? null },
    }),
  aiChatHistory: (limit = 20) =>
    request<Array<Record<string, unknown>>>(`/ai/chat/history?limit=${limit}`),

  // ── Admin / Users ─────────────────────────────────────────────────
  listUsers: (page = 1, size = 20, q?: string) => {
    const params = new URLSearchParams({ page: String(page), size: String(size) });
    if (q) params.set("q", q);
    return request<PageOut<UserOut>>(`/users?${params.toString()}`);
  },
  getUser: (id: string) => request<UserOut>(`/users/${id}`),
  setUserRole: (id: string, role: string) =>
    request<UserOut>(`/users/${id}/role`, { method: "PATCH", body: { role } }),
  deleteUser: (id: string) =>
    request<MessageResponse>(`/users/${id}`, { method: "DELETE" }),
};

export interface RefreshResponse extends TokenPair {}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean;
  retries?: number;
}

const API_PREFIX = "/api/v1";
const ACCESS_TOKEN_KEY = "wms.access_token";
const REFRESH_TOKEN_KEY = "wms.refresh_token";

// In-flight refresh promise so concurrent 401s share one refresh call.
let refreshPromise: Promise<string | null> | null = null;

export const tokenStore = {
  getAccessToken: (): string | null => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(ACCESS_TOKEN_KEY);
  },
  getRefreshToken: (): string | null => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  setTokens: (tokens: { access_token: string; refresh_token: string }) => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  },
  setAccessToken: (token: string) => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
  },
  clear: () => {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    const refresh = tokenStore.getRefreshToken();
    if (!refresh) return null;
    try {
      const res = await fetch(`${API_PREFIX}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) {
        tokenStore.clear();
        return null;
      }
      const data = (await res.json()) as RefreshResponse;
      tokenStore.setTokens(data);
      return data.access_token;
    } catch {
      tokenStore.clear();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const {
    method = "GET",
    body,
    auth = true,
    retries = 3,
  } = options;

  const url = `${API_PREFIX}${path}`;
  const headers: Record<string, string> = {};

  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = tokenStore.getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const attempt = async (): Promise<T> => {
    const response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (response.status === 401 && auth) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        headers["Authorization"] = `Bearer ${newToken}`;
        const retry = await fetch(url, {
          method,
          headers,
          body: body !== undefined ? JSON.stringify(body) : undefined,
        });
        if (retry.ok) return parseResponse<T>(retry);
        throw await createApiError(retry);
      }
    }

    if (!response.ok) {
      throw await createApiError(response);
    }

    return parseResponse<T>(response);
  };

  for (let i = 0; i < retries; i++) {
    try {
      return await attempt();
    } catch (err) {
      const isRetryable =
        err instanceof ApiError &&
        (err.status === 0 || err.status >= 500 || err.status === 429);
      if (!isRetryable || i === retries - 1) throw err;
      await sleep(100 * 2 ** i + Math.random() * 50);
    }
  }

  throw new Error("Unexpected request failure");
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T;
  const text = await response.text();
  if (!text) return undefined as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}

async function createApiError(response: Response): Promise<ApiError> {
  let message = `Request failed with status ${response.status}`;
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") message = body.detail;
    else if (Array.isArray(body?.detail) && body.detail.length) {
      message = body.detail[0]?.msg ?? message;
    } else if (typeof body?.message === "string") message = body.message;
  } catch {
    // fall back to default message
  }
  return new ApiError(message, response.status);
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

