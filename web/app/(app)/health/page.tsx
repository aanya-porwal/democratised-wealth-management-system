"use client";

import { useComputeHealthScore, useHealthScore } from "@/hooks/use-health";
import { MetricCard } from "@/components/metric-card";
import { CardGridSkeleton } from "@/components/skeletons";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { HeartPulse, RefreshCw, CheckCircle2, AlertTriangle, Lightbulb } from "lucide-react";

export default function HealthPage() {
  const health = useHealthScore();
  const compute = useComputeHealthScore();

  const latestScore = health.data?.[0];
  const loading = health.isLoading || compute.isPending;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Financial Health</h2>
          <p className="text-sm text-muted-foreground">
            A comprehensive 0–100 score computed by the health engine.
          </p>
        </div>
        <Button onClick={() => compute.mutate()} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${compute.isPending ? "animate-spin" : ""}`} aria-hidden />
          Compute
        </Button>
      </div>

      {loading ? (
        <CardGridSkeleton count={3} />
      ) : latestScore ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Health Score"
              value={`${Math.round(latestScore.score)}/100`}
              sublabel={`Grade ${latestScore.grade}`}
              icon={<HeartPulse className="h-4 w-4" aria-hidden />}
              accent="emerald"
            />
            <MetricCard
              label="Strengths"
              value={latestScore.strengths?.length ?? 0}
              sublabel="Positive factors"
              icon={<CheckCircle2 className="h-4 w-4" aria-hidden />}
              accent="blue"
            />
            <MetricCard
              label="Weaknesses"
              value={latestScore.weaknesses?.length ?? 0}
              sublabel="Areas to improve"
              icon={<AlertTriangle className="h-4 w-4" aria-hidden />}
              accent="red"
            />
            <MetricCard
              label="Suggestions"
              value={latestScore.suggestions?.length ?? 0}
              sublabel="Actionable items"
              icon={<Lightbulb className="h-4 w-4" aria-hidden />}
              accent="amber"
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Factor Breakdown</CardTitle>
              <CardDescription>Per-factor scores that make up your total</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {latestScore.factors?.map((factor) => (
                <div key={factor.name}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium capitalize">
                      {factor.name.replace(/_/g, " ")}
                    </span>
                    <Badge
                      variant={
                        factor.severity === "good"
                          ? "default"
                          : factor.severity === "warning"
                          ? "secondary"
                          : "destructive"
                      }
                    >
                      {factor.score}/{factor.max_points}
                    </Badge>
                  </div>
                  <Progress
                    value={(factor.score / factor.max_points) * 100}
                    className="h-2"
                  />
                  <p className="mt-0.5 text-xs text-muted-foreground">{factor.message}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="py-16 text-center">
          <HeartPulse className="mx-auto h-12 w-12 text-muted-foreground/40" aria-hidden />
          <h3 className="mt-4 text-lg font-medium">No health score yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Click "Compute" to get your financial health score.
          </p>
        </div>
      )}
    </div>
  );
}
