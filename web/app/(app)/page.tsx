"use client";

import Link from "next/link";
import {
  useFinancialPlan,
  useSystemHealth,
} from "@/hooks/use-planner";
import { useGoals, useGoalAnalysis } from "@/hooks/use-goals";
import { usePortfolios } from "@/hooks/use-portfolio";
import { useAllocation } from "@/hooks/use-allocation";
import { useHealthScore } from "@/hooks/use-health";
import { useRecommendations } from "@/hooks/use-recommendations";
import { MetricCard } from "@/components/metric-card";
import { CardGridSkeleton } from "@/components/skeletons";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Wallet,
  HeartPulse,
  Target,
  PieChart,
  Sparkles,
  ArrowRight,
  Bot,
  Activity,
  TrendingUp,
  ShieldCheck,
  FileSearch,
  Bell,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { formatCurrency, formatPercent, formatRatio, formatDate } from "@/lib/utils";

export default function CommandCenterPage() {
  const plan = useFinancialPlan();
  const goals = useGoals();
  const goalAnalysis = useGoalAnalysis();
  const portfolios = usePortfolios();
  const allocation = useAllocation();
  const health = useHealthScore();
  const recommendations = useRecommendations(10);
  const system = useSystemHealth();

  const loading = plan.isLoading || goals.isLoading || portfolios.isLoading;

  const totalNetWorth =
    portfolios.data?.reduce((sum, p) => sum + (p.total_value ?? 0), 0) ?? 0;
  const healthScore = health.data?.[0]?.score ?? plan.data?.health?.score;
  const healthGrade = health.data?.[0]?.grade ?? plan.data?.health?.grade;
  const pendingRecs =
    recommendations.data?.filter((r) => r.status === "pending") ?? [];
  const topGoal = goalAnalysis.data?.[0];
  const riskCategory = plan.data?.risk?.risk_category ?? "—";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            {plan.data?.user_name ? `Welcome back, ${plan.data.user_name.split(" ")[0]}` : "Command Center"}
          </h2>
          <p className="text-sm text-muted-foreground">
            Your entire financial life in one place — updated in real time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1.5">
            <Activity className="h-3 w-3 text-emerald-500" aria-hidden />
            {system.data?.status ?? "…"}
          </Badge>
          <Button variant="outline" size="sm" asChild>
            <Link href="/app/coach">
              <Bot className="mr-2 h-4 w-4" aria-hidden /> Ask AI Coach
            </Link>
          </Button>
        </div>
      </div>

      {/* Metric grid */}
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
            sublabel={topGoal ? `Top: ${topGoal.name}` : "Add your first goal"}
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

      {/* Top row: Allocation + Health */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-4 w-4 text-primary" aria-hidden />
                Asset Allocation
              </CardTitle>
              <CardDescription>
                Strategic target weights from the allocation engine
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/app/allocation">
                View <ArrowRight className="ml-1 h-3 w-3" aria-hidden />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {allocation.isLoading ? (
              <div className="space-y-3">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="h-4 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : allocation.data?.buckets?.length ? (
              <div className="space-y-4">
                {allocation.data.buckets.map((b) => (
                  <div key={b.bucket}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium capitalize">{b.bucket.replace(/_/g, " ")}</span>
                      <span className="text-muted-foreground">{formatPercent(b.weight)}</span>
                    </div>
                    <Progress value={b.weight * 100} className="h-2" />
                  </div>
                ))}
                <p className="text-xs text-muted-foreground">
                  {allocation.data.explanation}
                </p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No allocation yet.{" "}
                <Link href="/app/allocation" className="text-primary hover:underline">
                  Compute your target allocation
                </Link>
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HeartPulse className="h-4 w-4 text-primary" aria-hidden />
              Financial Health
            </CardTitle>
            <CardDescription>Latest engine score</CardDescription>
          </CardHeader>
          <CardContent>
            {healthScore !== undefined ? (
              <div className="flex flex-col items-center gap-4 py-4">
                <div className="relative flex h-28 w-28 items-center justify-center rounded-full border-4 border-primary/30">
                  <span className="text-3xl font-bold">{Math.round(healthScore)}</span>
                </div>
                <Badge variant="secondary">{healthGrade}</Badge>
                <p className="text-center text-xs text-muted-foreground">
                  {health.data?.[0]?.weaknesses?.[0] ?? "Your score is computed by the health engine."}
                </p>
                <Button variant="outline" size="sm" asChild>
                  <Link href="/app/health">See details</Link>
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4 py-8 text-center">
                <p className="text-sm text-muted-foreground">
                  Run a health check to see your score.
                </p>
                <Button size="sm" asChild>
                  <Link href="/app/health">Run health check</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Bottom row: Goals + Recommendations + AI */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Goals */}
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-4 w-4 text-primary" aria-hidden />
                Goals
              </CardTitle>
              <CardDescription>Progress toward your targets</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/app/goals">
                Manage <ArrowRight className="ml-1 h-3 w-3" aria-hidden />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {goals.isLoading ? (
              <div className="space-y-3">
                {[0, 1].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : goals.data?.length ? (
              goals.data.slice(0, 3).map((goal) => {
                const analysis = goalAnalysis.data?.find(
                  (a) => a.name === goal.name
                );
                const progress = analysis?.current_progress ?? 0;
                return (
                  <div key={goal.id} className="rounded-lg border p-3">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-sm font-medium">{goal.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(goal.target_date)}
                      </span>
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
                <p className="text-sm text-muted-foreground">
                  No goals yet. Start by adding your first financial goal.
                </p>
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
            {recommendations.isLoading ? (
              <div className="space-y-3">
                {[0, 1].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : pendingRecs.length ? (
              pendingRecs.slice(0, 3).map((rec) => (
                <div key={rec.id} className="flex items-start gap-3 rounded-lg border p-3">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
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

        {/* AI Coach CTA */}
        <Card className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-brand-500/10 via-transparent to-transparent" aria-hidden />
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-primary" aria-hidden />
              AI Financial Coach
            </CardTitle>
            <CardDescription>
              Ask anything about your plan, portfolio or goals
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2 rounded-lg border bg-background/50 p-3 text-sm">
              <p className="text-muted-foreground">Try asking:</p>
              <ul className="space-y-1.5 text-sm">
                <li>• “Am I on track for retirement?”</li>
                <li>• “What should I do with my surplus?”</li>
                <li>• “Run a market-crash scenario for me.”</li>
              </ul>
            </div>
            <Button className="w-full" asChild>
              <Link href="/app/coach">
                <Bot className="mr-2 h-4 w-4" aria-hidden />
                Open AI Coach
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick actions strip */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { href: "/app/research", icon: FileSearch, label: "Research Reports" },
          { href: "/app/compare", icon: TrendingUp, label: "Compare Securities" },
          { href: "/app/monte-carlo", icon: Activity, label: "Monte Carlo" },
          { href: "/app/notifications", icon: Bell, label: "Notifications" },
        ].map((q) => (
          <Link
            key={q.href}
            href={q.href}
            className="group flex items-center gap-3 rounded-xl border bg-card p-4 transition-colors hover:bg-accent"
          >
            <q.icon className="h-4 w-4 text-primary" aria-hidden />
            <span className="text-sm font-medium">{q.label}</span>
            <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" aria-hidden />
          </Link>
        ))}
      </div>
    </div>
  );
}
