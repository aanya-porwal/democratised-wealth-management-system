"use client";

import { useAllocation } from "@/hooks/use-allocation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { PieChart as PieIcon, RefreshCw } from "lucide-react";
import { formatPercent } from "@/lib/utils";

export default function AllocationPage() {
  const allocation = useAllocation();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Asset Allocation</h2>
          <p className="text-sm text-muted-foreground">
            Strategic target weights from the allocation engine.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => allocation.refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" aria-hidden />
          Refresh
        </Button>
      </div>

      {allocation.isLoading ? (
        <Card>
          <CardContent className="space-y-4 py-6">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="h-8 animate-pulse rounded bg-muted" />
            ))}
          </CardContent>
        </Card>
      ) : allocation.data ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieIcon className="h-4 w-4 text-primary" aria-hidden />
                Target Allocation
              </CardTitle>
              <CardDescription>
                Risk score {allocation.data.risk_score.toFixed(0)} · {allocation.data.risk_category}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {allocation.data.buckets.map((bucket) => (
                <div key={bucket.bucket}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium capitalize">
                      {bucket.bucket.replace(/_/g, " ")}
                    </span>
                    <span className="text-muted-foreground">
                      {bucket.instruments?.length
                        ? bucket.instruments.join(", ")
                        : formatPercent(bucket.weight)}
                    </span>
                  </div>
                  <Progress value={bucket.weight * 100} className="h-2.5" />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Why this allocation?</CardTitle>
              <CardDescription>Engine explanation</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {allocation.data.explanation}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {allocation.data.buckets.map((bucket) => (
                  <Badge key={bucket.bucket} variant="secondary">
                    {bucket.bucket.replace(/_/g, " ")} · {formatPercent(bucket.weight)}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <Card>
          <CardContent className="py-16 text-center">
            <p className="text-sm text-muted-foreground">
              No allocation computed yet. Set up your financial profile to get a
              target allocation.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
