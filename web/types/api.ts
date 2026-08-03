// Types mirroring the backend Pydantic schemas (app/schemas/*).

// ─── Common ────────────────────────────────────────────────────────

export interface MessageResponse {
  message: string;
}

export interface PaginationMeta {
  page: number;
  size: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PageOut<T> {
  items: T[];
  pagination: PaginationMeta;
}

// ─── Auth ──────────────────────────────────────────────────────────

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  tokens: TokenPair;
  user_id: string;
  role: "user" | "admin" | "advisor";
  full_name: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export type RefreshResponse = TokenPair;

// ─── Users / Profiles ──────────────────────────────────────────────

export interface UserOut {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin" | "advisor";
  is_active: boolean;
  is_email_verified: boolean;
  created_at: string;
}

export interface UserProfileOut {
  id: string;
  name: string;
  age: number;
  date_of_birth: string;
  dependents: number;
  life_stage?: string | null;
  marital_status?: string | null;
  city?: string | null;
  occupation?: string | null;
}

export interface UserProfileCreate {
  name: string;
  age: number;
  date_of_birth: string;
  dependents: number;
}

export interface FinancialProfileOut {
  id: string;
  monthly_income: number;
  employment_type: string;
  income_stability: number;
  secondary_income: boolean;
  secondary_monthly_income: number;
  monthly_fixed_expenses: number;
  monthly_variable_expenses: number;
  emergency_fund_months: number;
  existing_investments: number;
  provident_fund_balance: number;
  real_estate_value: number;
  gold_value: number;
  total_debt: number;
  monthly_emi_total: number;
  tax_bracket_percent: number;
  has_term_life_insurance: boolean;
  has_health_insurance: boolean;
  existing_monthly_sip: number;
}

export interface FinancialProfileCreate {
  monthly_income: number;
  employment_type?: string;
  income_stability?: number;
  secondary_income?: boolean;
  secondary_monthly_income?: number;
  monthly_fixed_expenses?: number;
  monthly_variable_expenses?: number;
  emergency_fund_months?: number;
  existing_investments?: number;
  provident_fund_balance?: number;
  real_estate_value?: number;
  gold_value?: number;
  total_debt?: number;
  monthly_emi_total?: number;
  tax_bracket_percent?: number;
  has_term_life_insurance?: boolean;
  has_health_insurance?: boolean;
  existing_monthly_sip?: number;
}

export interface BehavioralProfileOut {
  id: string;
  risk_tolerance: string;
  drawdown_reaction_score: number;
  has_invested_before: boolean;
  has_experienced_market_crash: boolean;
  financial_literacy_score: number;
  loss_aversion_score: number;
  risk_score?: number | null;
  risk_category?: string | null;
}

export interface BehavioralProfileCreate {
  risk_tolerance?: string;
  drawdown_reaction_score?: number;
  has_invested_before?: boolean;
  has_experienced_market_crash?: boolean;
  financial_literacy_score?: number;
  loss_aversion_score?: number;
}

export interface RiskAssessment {
  score: number;
  risk_score?: number;
  risk_category: string;
  capacity_score?: number;
  tolerance_score?: number;
  capacity_was_binding?: boolean;
  explanation?: string;
  [key: string]: unknown;
}

export interface FullProfile {
  user_id: string;
  profile?: UserProfileOut | null;
  financial_profile?: FinancialProfileOut | null;
  behavioral_profile?: BehavioralProfileOut | null;
  risk: RiskAssessment;
}

// ─── Goals ─────────────────────────────────────────────────────────

export type GoalType =
  | "emergency_fund"
  | "home_purchase"
  | "vehicle"
  | "education_self"
  | "education_child"
  | "wedding"
  | "travel"
  | "retirement"
  | "wealth_creation"
  | "other";

export type GoalPriority = "critical" | "high" | "aspirational";

export interface GoalCreate {
  name: string;
  goal_type: GoalType;
  priority: GoalPriority;
  target_amount: number;
  target_date: string; // YYYY-MM-DD
  current_savings_for_goal?: number;
  current_monthly_contribution?: number;
  notes?: string;
}

export interface GoalUpdate {
  name?: string;
  goal_type?: GoalType;
  priority?: GoalPriority;
  target_amount?: number;
  target_date?: string;
  current_savings_for_goal?: number;
  current_monthly_contribution?: number;
  notes?: string;
}

export interface GoalOut {
  id: string;
  user_id: string;
  name: string;
  goal_type: GoalType;
  priority: GoalPriority;
  target_amount: number;
  target_date: string;
  current_savings_for_goal: number;
  current_monthly_contribution: number;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface GoalProgressOut {
  id: string;
  goal_id: string;
  recorded_at: string;
  current_savings: number;
  progress_percent: number;
  probability_of_success?: number | null;
  required_sip?: number | null;
  remaining_gap?: number | null;
}

export interface GoalAnalysisOut {
  name: string;
  goal_type: GoalType;
  priority: GoalPriority;
  current_amount: number;
  target_amount: number;
  current_progress: number;
  target_date: string;
  years_remaining: number;
  inflation_rate: number;
  expected_return: number;
  inflation_adjusted_target: number;
  future_value: number;
  present_value: number;
  required_sip: number;
  remaining_gap: number;
  expected_corpus?: number | null;
  probability_of_success?: number | null;
  verdict: string;
  notes: string[];
}

// ─── Portfolio ─────────────────────────────────────────────────────

export interface PortfolioCreate {
  name: string;
  description?: string | null;
  target_allocation?: Record<string, number> | null;
}

export interface PortfolioOut {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  total_value: number;
  target_allocation?: Record<string, number> | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface HoldingCreate {
  asset_class: string;
  bucket?: string | null;
  market_value: number;
  cost_basis?: number;
  quantity?: number | null;
  currency?: string;
}

export interface HoldingOut {
  id: string;
  portfolio_id: string;
  asset_class: string;
  bucket?: string | null;
  market_value: number;
  cost_basis: number;
  quantity?: number | null;
  currency: string;
  created_at: string;
}

export interface PortfolioSnapshotOut {
  id: string;
  portfolio_id: string;
  captured_at: string;
  total_value: number;
  weights?: Record<string, number> | null;
  cash_flow?: number | null;
  notes?: string | null;
}

// ─── Allocation ────────────────────────────────────────────────────

export interface AllocationRequest {
  risk_score?: number | null;
  horizon_years?: number | null;
  liquidity_need?: string | null;
  monthly_investment?: number | null;
}

export interface BucketOut {
  bucket: string;
  weight: number; // 0-1
  instruments: string[];
}

export interface AllocationOut {
  buckets: BucketOut[];
  risk_score: number;
  risk_category: string;
  explanation: string;
}

// ─── Rebalance ─────────────────────────────────────────────────────

export interface RebalanceActionOut {
  bucket: string;
  direction: string;
  current_weight: number;
  target_weight: number;
  drift: number;
  trade_amount: number;
  reason: string;
}

export interface RebalanceTradeOut {
  asset_class: string;
  amount: number;
  reason: string;
  estimated_tax_impact: number;
  estimated_transaction_cost: number;
}

export interface RebalanceOut {
  rebalance_required: boolean;
  actions: RebalanceActionOut[];
  trades: RebalanceTradeOut[];
  total_transaction_cost: number;
  total_tax_impact: number;
  portfolio_value: number;
  notes: string[];
}

// ─── Recommendations ───────────────────────────────────────────────

export type RecommendationStatus = "pending" | "accepted" | "dismissed" | "completed";

export interface RecommendationOut {
  id: string;
  recommendation_type: string;
  title: string;
  description: string;
  confidence: string;
  reasons?: string[] | null;
  action?: string | null;
  impact?: string | null;
  priority?: number | null;
  status: RecommendationStatus;
  created_at: string;
}

// ─── Health Score ──────────────────────────────────────────────────

export interface HealthFactorOut {
  name: string;
  score: number;
  max_points: number;
  severity: string;
  message: string;
  percentage: number;
}

export interface HealthScoreOut {
  id?: string | null;
  user_id?: string | null;
  scored_at?: string | null;
  score: number;
  grade: string;
  factors: HealthFactorOut[];
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
}

// ─── Simulation / Scenario ─────────────────────────────────────────

export interface SimulationCreate {
  expected_return: number;
  volatility: number;
  monthly_investment?: number;
  inflation?: number;
  horizon_years: number;
  initial_corpus?: number;
  target_amount?: number | null;
  simulations?: number;
  goal_id?: string | null;
  simulation_type?: string;
}

export interface SimulationStatisticsOut {
  median: number;
  percentile_5: number;
  percentile_25: number;
  percentile_75: number;
  percentile_95: number;
  worst_case: number;
  best_case: number;
  mean: number;
  std_dev: number;
  probability_of_success: number;
}

export interface SimulationOut {
  id: string;
  user_id: string;
  goal_id?: string | null;
  run_at: string;
  simulations: number;
  horizon_years: number;
  expected_return: number;
  volatility: number;
  inflation: number;
  monthly_investment: number;
  initial_corpus: number;
  target_amount?: number | null;
  statistics?: SimulationStatisticsOut | null;
  percentiles?: Record<string, number> | null;
}

export type ScenarioType =
  | "salary_increase"
  | "salary_decrease"
  | "market_crash"
  | "early_retirement"
  | "delayed_retirement"
  | "house_purchase"
  | "child_education"
  | "marriage"
  | "emergency_expense";

export interface ScenarioCreate {
  scenario_type: ScenarioType;
  name?: string | null;
  description?: string | null;
  income_multiplier?: number | null;
  expense_multiplier?: number | null;
  portfolio_drawdown?: number | null;
  one_time_expense?: number | null;
  monthly_contribution_adjustment?: number | null;
  emergency_fund_months?: number | null;
  retirement_age?: number | null;
  target_date_shift_years?: number | null;
  simulations?: number;
}

export interface ScenarioOut {
  id?: string | null;
  run_at?: string | null;
  scenario_type: ScenarioType;
  name: string;
  description?: string | null;
  goal_probabilities: Record<string, number>;
  total_required_sip?: number | null;
  net_worth?: number | null;
  allocation: Record<string, number>;
  summary: string;
}

// ─── Planner ───────────────────────────────────────────────────────

export interface PlannerCashflow {
  monthly_surplus: number;
  savings_rate: number;
  emergency_fund_months: number;
  emergency_fund_target_months: number;
  emergency_fund_amount_needed: number;
  emergency_fund_priority: string;
}

export interface PlannerGoalPlan {
  goal_type: string;
  priority: string;
  target_amount: number;
  current_savings: number;
  monthly_contribution: number;
  years: number;
  projected_value: number;
  probability: number;
  required_monthly: number;
  shortfall: number;
  feasible: boolean;
}

export interface PlannerProbability {
  goal_type: string;
  probability: number;
  median_outcome: number;
  shortfall_median: number;
  verdict: string;
}

export interface PlannerAction {
  action: string;
  reason: string;
  priority: string;
}

export interface PlannerPortfolio {
  [key: string]: unknown;
}

export interface FinancialPlan {
  user_name: string;
  summary: string;
  cashflow: PlannerCashflow;
  health: { score: number; grade: string };
  risk: {
    final_score_100: number;
    risk_category: string;
    capacity_was_binding: boolean;
  };
  portfolio: PlannerPortfolio;
  goals: {
    surplus_after_foundations: number;
    goal_plans: PlannerGoalPlan[];
  };
  probabilities: PlannerProbability[];
  actions: PlannerAction[];
}

// ─── Chat / AI ─────────────────────────────────────────────────────

export interface ChatMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  created_at?: string;
  tool_name?: string | null;
  metadata?: Record<string, unknown>;
}

export interface ChatRequest {
  session_id?: string | null;
  message: string;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  tool_calls: Array<Record<string, unknown>>;
  agents_used: string[];
  memories_retrieved: number;
  documents_retrieved: number;
  provider: string;
  model: string;
  requires_followup: boolean;
  followup_questions: string[];
  disclaimer: string;
  metadata: Record<string, unknown>;
}

export interface ToolResult {
  ok: boolean;
  tool: string;
  data: Record<string, unknown>;
  error?: string | null;
  warning?: string | null;
  latency_ms: number;
  executed_at: string;
  confirmed: boolean;
}

export interface ChatSessionOut {
  id: string;
  title: string;
  context?: Record<string, unknown> | null;
  status: string;
  messages?: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
}

// ─── AI-First Workspace (Phase 11) ─────────────────────────────────

export type AiToolStatus = "pending" | "running" | "done" | "error";

export interface AiToolCall {
  id: string;
  name: string;
  friendlyName?: string;
  status: AiToolStatus;
  arguments?: Record<string, unknown>;
  summary?: string;
  latencyMs?: number;
}

export interface AiAction {
  id: string;
  type:
    | "increase_sip"
    | "apply_allocation"
    | "view_research"
    | "compare_securities"
    | "run_simulation"
    | "run_scenario"
    | "accept_recommendation"
    | "decline_recommendation"
    | "update_goal"
    | "schedule_review"
    | "rebalance"
    | "generate_recommendations"
    | "navigate"
    | "apply_plan";
  label: string;
  description?: string;
  primary?: boolean;
  meta?: Record<string, unknown>;
}

export interface AiContextEntry {
  key: string;
  value: string;
  label?: string;
}

export interface AiExplainability {
  agentsUsed: string[];
  toolsUsed: string[];
  dataSources: AiContextEntry[];
  calculations: string[];
  confidence?: number;
  disclaimer?: string;
}

export type AiChartType = "line" | "bar" | "area" | "pie" | "donut";

export interface AiChartSeries {
  name: string;
  data: Array<Record<string, string | number>>;
  xKey: string;
  yKeys: string[];
  type?: AiChartType;
  colors?: string[];
  title?: string;
}

export interface AiTableColumn {
  key: string;
  header: string;
}

export interface AiTable {
  title?: string;
  columns: AiTableColumn[];
  rows: Array<Record<string, string | number>>;
}

export type AiMessageBlockType =
  | "text"
  | "chart"
  | "table"
  | "actionCard"
  | "toolTrace"
  | "followups"
  | "explainability"
  | "research"
  | "memory";

export interface AiMessageBlock {
  id: string;
  type: AiMessageBlockType;
  text?: string;
  chart?: AiChartSeries;
  table?: AiTable;
  actions?: AiAction[];
  toolCalls?: AiToolCall[];
  followups?: string[];
  research?: Record<string, unknown>;
  memory?: { content: string; type: string }[];
  explainability?: AiExplainability;
}

export interface AiRichMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  blocks: AiMessageBlock[];
  createdAt: string;
  pending?: boolean;
}

export interface AiMemoryEntry {
  id: string;
  memory_type: string;
  content: string;
  created_at: string;
}

export interface AiBubblePart {
  kind: "text" | "chart" | "table" | "actions" | "followups" | "tool" | "memory";
  text?: string;
  chart?: AiChartSeries;
  table?: AiTable;
  actions?: AiAction[];
  followups?: string[];
  tool?: AiToolCall;
  memory?: { content: string; type: string }[];
}

// ─── System ────────────────────────────────────────────────────────

export interface SystemHealth {
  status: string;
  app: string;
  version: string;
  environment: string;
}

export interface SystemReady {
  status: string;
  database: string;
  redis: string;
}

export interface SystemInfo {
  app: string;
  version: string;
  api_prefix: string;
  rate_limit_enabled: boolean;
}

