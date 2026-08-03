// lib/ai/context.ts
// Builds per-page contextual summaries that are passed to the backend
// /ai/chat endpoint. The frontend never computes financial figures — it
// only summarises already-fetched backend data so the AI is context-aware.

import type {
  AllocationOut,
  FinancialPlan,
  GoalAnalysisOut,
  GoalOut,
  HealthScoreOut,
  PortfolioOut,
  RecommendationOut,
} from "@/types/api";
import { formatCurrency, formatPercent } from "@/lib/utils";

export interface AiPageContext {
  page: string;
  entries: Array<{ label: string; value: string }>;
  raw?: Record<string, unknown>;
}

function compactGoals(goals: GoalOut[] | undefined): string {
  if (!goals || goals.length === 0) return "No goals yet";
  return goals
    .slice(0, 8)
    .map((g) => `${g.name} (${g.goal_type}, ${g.priority}) target ${formatCurrency(g.target_amount, { compact: true })}`)
    .join("; ");
}

function compactGoalAnalysis(analysis: GoalAnalysisOut[] | undefined): string {
  if (!analysis || analysis.length === 0) return "";
  return analysis
    .map((a) => `${a.name}: ${formatPercent(a.probability_of_success)} success, required SIP ${formatCurrency(a.required_sip)}`)
    .join("; ");
}

function compactPortfolio(portfolios: PortfolioOut[] | undefined): string {
  if (!portfolios || portfolios.length === 0) return "No portfolio yet";
  return portfolios
    .map((p) => `${p.name}: ${formatCurrency(p.total_value, { compact: true })}`)
    .join("; ");
}

function compactHealth(health: HealthScoreOut | undefined): string {
  if (!health) return "Not computed";
  return `score ${health.score} (${health.grade}); weaknesses: ${health.weaknesses?.slice(0, 3).join(", ") ?? "none"}`;
}

function compactAllocation(allocation: AllocationOut | undefined): string {
  if (!allocation) return "Not computed";
  return allocation.buckets
    .map((b) => `${b.bucket}: ${formatPercent(b.weight)}`)
    .join("; ");
}

function compactPlan(plan: FinancialPlan | undefined): string {
  if (!plan) return "No plan";
  return `health ${plan.health?.score}/${plan.health?.grade}, surplus ${formatCurrency(plan.cashflow?.monthly_surplus)}, actions: ${(plan.actions ?? []).map((a) => a.action).join(", ")}`;
}

function compactRecommendations(recommendations: RecommendationOut[] | undefined): string {
  if (!recommendations || recommendations.length === 0) return "";
  return recommendations
    .slice(0, 5)
    .map((r) => `${r.title} [${r.status}]`)
    .join("; ");
}

/**
 * Compose the context object sent with each /ai/chat call.
 * Keep entries short so token usage stays low.
 */
export function buildAiContext(input: {
  page: string;
  goals?: GoalOut[];
  goalAnalysis?: GoalAnalysisOut[];
  portfolios?: PortfolioOut[];
  health?: HealthScoreOut | null;
  allocation?: AllocationOut | null;
  plan?: FinancialPlan | null;
  recommendations?: RecommendationOut[];
  selected?: Record<string, unknown>;
}): Record<string, unknown> {
  const entries: AiPageContext["entries"] = [];
  const goals = compactGoals(input.goals);
  const analysis = compactGoalAnalysis(input.goalAnalysis);
  const portfolios = compactPortfolio(input.portfolios);
  const health = compactHealth(input.health ?? undefined);
  const allocation = compactAllocation(input.allocation ?? undefined);
  const plan = compactPlan(input.plan ?? undefined);
  const recommendations = compactRecommendations(input.recommendations);

  entries.push({ label: "Page", value: input.page });
  if (goals) entries.push({ label: "Goals", value: goals });
  if (analysis) entries.push({ label: "Goal analysis", value: analysis });
  if (portfolios) entries.push({ label: "Portfolio", value: portfolios });
  if (health) entries.push({ label: "Health", value: health });
  if (allocation) entries.push({ label: "Allocation", value: allocation });
  if (plan) entries.push({ label: "Plan", value: plan });
  if (recommendations) entries.push({ label: "Recommendations", value: recommendations });

  const context: Record<string, unknown> = {
    page: input.page,
    summary: entries.map((e) => `${e.label}: ${e.value}`).join("\n"),
  };
  for (const e of entries) context[e.label.toLowerCase()] = e.value;
  if (input.selected) context.selected = input.selected;
  return context;
}

