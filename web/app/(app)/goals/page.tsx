"use client";

import Link from "next/link";
import { useGoals, useGoalAnalysis } from "@/hooks/use-goals";
import { MetricCard } from "@/components/metric-card";
import { CardGridSkeleton } from "@/components/skeletons";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Target, Plus, ArrowRight, Trash2, Activity } from "lucide-react";
import { formatCurrency, formatPercent, formatDate } from "@/lib/utils";
import { useRef, useState } from "react";

export default function GoalsPage() {
  const goals = useGoals();
  const goalAnalysis = useGoalAnalysis();
  const [showCreate, setShowCreate] = useState(false);

  const loading = goals.isLoading || goalAnalysis.isLoading;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Financial Goals</h2>
          <p className="text-sm text-muted-foreground">
            Create, track and prioritise your financial targets.
          </p>
        </div>
        <Button onClick={() => setShowCreate((v) => !v)}>
          <Plus className="mr-2 h-4 w-4" aria-hidden />
          New Goal
        </Button>
      </div>

      {/* Summary cards */}
      {loading ? (
        <CardGridSkeleton count={3} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          <MetricCard
            label="Total Goals"
            value={goals.data?.length ?? 0}
            sublabel="Across all priorities"
            icon={<Target className="h-4 w-4" aria-hidden />}
            accent="violet"
          />
          <MetricCard
            label="Target Corpus"
            value={formatCurrency(
              goals.data?.reduce((s, g) => s + g.target_amount, 0) ?? 0,
              { compact: true }
            )}
            sublabel="Combined target amount"
            icon={<Target className="h-4 w-4" aria-hidden />}
            accent="emerald"
          />
          <MetricCard
            label="Total Saved"
            value={formatCurrency(
              goals.data?.reduce((s, g) => s + g.current_savings_for_goal, 0) ?? 0,
              { compact: true }
            )}
            sublabel="Across all goals"
            icon={<Activity className="h-4 w-4" aria-hidden />}
            accent="blue"
          />
        </div>
      )}

      {/* Goal list */}
      <div className="grid gap-4 md:grid-cols-2">
        {goals.data?.map((goal) => {
          const analysis = goalAnalysis.data?.find((a) => a.name === goal.name);
          const progress = analysis?.current_progress ?? 0;
          return (
            <Card key={goal.id}>
              <CardHeader className="flex-row items-start justify-between space-y-0">
                <div>
                  <CardTitle className="text-base">{goal.name}</CardTitle>
                  <CardDescription>
                    {goal.goal_type.replace(/_/g, " ")} · {goal.priority}
                  </CardDescription>
                </div>
                <Badge
                  variant={
                    goal.priority === "critical"
                      ? "destructive"
                      : goal.priority === "high"
                      ? "default"
                      : "secondary"
                  }
                >
                  {goal.priority}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-3">
                <Progress value={progress * 100} className="h-2.5" />
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {formatCurrency(goal.current_savings_for_goal, { compact: true })}
                    {" / "}
                    {formatCurrency(goal.target_amount, { compact: true })}
                  </span>
                  <span>{formatPercent(progress)}</span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-lg border p-2">
                    <p className="text-muted-foreground">Target date</p>
                    <p className="font-medium">{formatDate(goal.target_date)}</p>
                  </div>
                  <div className="rounded-lg border p-2">
                    <p className="text-muted-foreground">Monthly SIP</p>
                    <p className="font-medium">
                      {formatCurrency(goal.current_monthly_contribution, { compact: true })}
                    </p>
                  </div>
                  {analysis ? (
                    <>
                      <div className="rounded-lg border p-2">
                        <p className="text-muted-foreground">Required SIP</p>
                        <p className="font-medium">
                          {formatCurrency(analysis.required_sip, { compact: true })}
                        </p>
                      </div>
                      <div className="rounded-lg border p-2">
                        <p className="text-muted-foreground">Success Prob.</p>
                        <p className="font-medium">
                          {analysis.probability_of_success !== null && analysis.probability_of_success !== undefined
                            ? formatPercent(analysis.probability_of_success)
                            : "—"}
                        </p>
                      </div>
                    </>
                  ) : null}
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" asChild className="flex-1">
                    <Link href={`/app/goals/${goal.id}`}>
                      Details <ArrowRight className="ml-1 h-3 w-3" aria-hidden />
                    </Link>
                  </Button>
                  <Button variant="ghost" size="icon" aria-label="Delete goal">
                    <Trash2 className="h-4 w-4 text-muted-foreground" aria-hidden />
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {!loading && !goals.data?.length ? (
        <div className="py-16 text-center">
          <Target className="mx-auto h-12 w-12 text-muted-foreground/40" aria-hidden />
          <h3 className="mt-4 text-lg font-medium">No goals yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Add your first goal — retirement, home, education, or anything that matters.
          </p>
          <Button className="mt-6" onClick={() => setShowCreate(true)}>
            <Plus className="mr-2 h-4 w-4" aria-hidden />
            Create your first goal
          </Button>
        </div>
      ) : null}
    </div>
  );
}
