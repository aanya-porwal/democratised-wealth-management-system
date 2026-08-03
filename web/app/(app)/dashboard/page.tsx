"use client";

import Link from "next/link";
import {
  useFinancialPlan,
} from "@/hooks/use-planner";
import { useGoals, useGoalAnalysis } from "@/hooks/use-goals";
import { usePortfolios } from "@/hooks/use-portfolio";
import { useHealthScore } from "@/hooks/use-health";
import { useRecommendations } from "@/hooks/use-recommendations";
import { MetricCard } from "@/components/metric-card";
import { CardGridSkeleton } from "@/components/skeletons";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Wallet,
  HeartPulse,
  Target,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";
import {
  formatCurrency,
  formatPercent,
  formatDate,
} from "@/lib/utils";

export default function DashboardPage() {
  const plan = useFinancialPlan();
  const goals = useGoals();
  const goalAnalysis = useGoalAnalysis();
  const portfolios = usePortfolios();
  const health = useHealthScore();
  const recommendations = useRecommendations(10);

  const loading = plan.isLoading || goals.isLoading || portfolios.isLoading;

  const totalNetWorth =
    portfolios.data?.reduce((sum, p) => sum + (p.total_value ?? 0), 0) ?? 0;
  const healthScore = health.data?.[0]?.score ?? plan.data?.health?.score;
  const healthGrade = health.data?.[0]?.grade ?? plan.data?.health?.grade;
  const pendingRecs =
    recommendations.data?.filter((r) => r.status === "pending") ?? [];
  const riskCategory = plan.data?.risk?.risk_category ?? "—";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          A snapshot of your financial life.
        </p>
      </div>

      {loading ? (
        <CardGridSkeleton count={4} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            label="Net Worth"
            value={formatCurrency(totalNetWorth, { compact: true })}
            sublabel={`${portfolios.data?.length ?? 0} portfolio${(portfolios.data?.length ?? 0) === 1 ? "" : "s"}`}
            icon={<Wallet className="h-4 w-4" aria-hidden />}
            accent="emerald"
          />
          <MetricCard
            label="Financial Health"
            value={healthScore !== undefined ? `${Math.round(healthScore)}/100` : "—"}
            sublabel={healthGrade ? `Grade ${healthGrade}` : "Run a health check"}
            icon={<HeartPulse className="h-4 w-4" aria-hidden />}
            accent="blue"
          />
          <MetricCard
            label="Active Goals"
            value={goals.data?.length ?? 0}
            sublabel={`${pendingRecs.length} pending actions`}
            icon={<Target className="h-4 w-4" aria-hidden />}
            accent="violet"
          />
          <MetricCard
            label="Risk Profile"
            value={riskCategory}
            sublabel="Engine-assessed"
            icon={<ShieldCheck className="h-4 w-4" aria-hidden />}
            accent="amber"
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Goals */}
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-4 w-4 text-primary" aria-hidden />
                Goal Progress
              </CardTitle>
              <CardDescription>How your goals are tracking</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/app/goals">
                Manage <ArrowRight className="ml-1 h-3 w-3" aria-hidden />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {goals.data?.length ? (
              goals.data.slice(0, 4).map((goal) => {
                const analysis = goalAnalysis.data?.find(
                  (a) => a.name === goal.name
                );
                const progress = analysis?.current_progress ?? 0;
                return (
                  <div key={goal.id} className="rounded-lg border p-3">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-sm font-medium">{goal.name}</span>
                      <Badge variant="outline" className="text-[10px]">
                        {goal.priority}
                      </Badge>
                    </div>
                    <Progress value={progress * 100} className="h-2" />
                    <div className="mt-1.5 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{formatCurrency(goal.current_savings_for_goal, { compact: true })}</span>
                      <span>{formatPercent(progress)}</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm text-muted-foreground">No goals yet.</p>
                <Button size="sm" className="mt-4" asChild>
                  <Link href="/app/goals">Add a goal</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recommendations */}
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" aria-hidden />
                AI Recommendations
              </CardTitle>
              <CardDescription>Explainable, engine-driven</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/app/recommendations">
                View all <ArrowRight className="ml-1 h-3 w-3" aria-hidden />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {pendingRecs.length ? (
              pendingRecs.slice(0, 4).map((rec) => (
                <div
                  key={rec.id}
                  className="flex items-start gap-3 rounded-lg border p-3"
                >
                  <CheckCircle2
                    className="mt-0.5 h-4 w-4 shrink-0 text-primary"
                    aria-hidden
                  />
                  <div className="min-w-0">
                    <p className="text-sm font-medium leading-snug">{rec.title}</p>
                    <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                      {rec.description}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm text-muted-foreground">
                  No pending recommendations. Generate a fresh set.
                </p>
                <Button size="sm" variant="outline" className="mt-4" asChild>
                  <Link href="/app/recommendations">Generate</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Plan summary */}
      {plan.data ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" aria-hidden />
              Today&apos;s Plan Summary
            </CardTitle>
            <CardDescription>From the financial planning engine</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{plan.data.summary}</p>
            {plan.data.actions?.length ? (
              <div className="space-y-2">
                {plan.data.actions.slice(0, 4).map((action, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 rounded-lg border p-3"
                  >
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" aria-hidden />
                    <div>
                      <p className="text-sm font-medium">{action.action}</p>
                      <p className="text-xs text-muted-foreground">{action.reason}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
