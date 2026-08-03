"use client";

import {
  useRecommendations,
  useGenerateRecommendations,
} from "@/hooks/use-recommendations";
import { CardGridSkeleton } from "@/components/skeletons";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  RefreshCw,
  CheckCircle2,
  XCircle,
  ArrowRight,
  AlertTriangle,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

export default function RecommendationsPage() {
  const recommendations = useRecommendations(100);
  const generate = useGenerateRecommendations();

  const loading = recommendations.isLoading || generate.isPending;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Recommendations</h2>
          <p className="text-sm text-muted-foreground">
            Explainable, engine-driven recommendations for your financial plan.
          </p>
        </div>
        <Button onClick={() => generate.mutate(24)} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${generate.isPending ? "animate-spin" : ""}`} aria-hidden />
          Generate
        </Button>
      </div>

      {loading ? (
        <CardGridSkeleton count={3} />
      ) : recommendations.data?.length ? (
        <div className="grid gap-4 md:grid-cols-2">
          {recommendations.data.map((rec) => (
            <Card key={rec.id}>
              <CardHeader className="flex-row items-start justify-between space-y-0">
                <div className="min-w-0">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Sparkles className="h-4 w-4 shrink-0 text-primary" aria-hidden />
                    <span className="truncate">{rec.title}</span>
                  </CardTitle>
                  <CardDescription>
                    {rec.recommendation_type.replace(/_/g, " ")} ·{" "}
                    {formatRelativeTime(rec.created_at)}
                  </CardDescription>
                </div>
                <Badge
                  variant={
                    rec.status === "accepted"
                      ? "default"
                      : rec.status === "pending"
                      ? "secondary"
                      : "outline"
                  }
                >
                  {rec.status}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">{rec.description}</p>
                {rec.reasons?.length ? (
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {rec.reasons.map((reason, i) => (
                      <li key={i}>• {reason}</li>
                    ))}
                  </ul>
                ) : null}
                {rec.action ? (
                  <div className="flex items-start gap-2 rounded-lg border p-2.5 text-sm">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" aria-hidden />
                    <span>{rec.action}</span>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-16 text-center">
            <Sparkles className="mx-auto h-12 w-12 text-muted-foreground/40" aria-hidden />
            <h3 className="mt-4 text-lg font-medium">No recommendations yet</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Generate a fresh set of AI recommendations based on your financial plan.
            </p>
            <Button className="mt-6" onClick={() => generate.mutate(24)}>
              Generate recommendations
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
