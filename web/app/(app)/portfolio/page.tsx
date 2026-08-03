"use client";

import { usePortfolios } from "@/hooks/use-portfolio";
import { MetricCard } from "@/components/metric-card";
import { CardGridSkeleton } from "@/components/skeletons";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Wallet, Plus, PieChart, Building2, ArrowRight } from "lucide-react";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function PortfolioPage() {
  const portfolios = usePortfolios();

  const loading = portfolios.isLoading;
  const totalValue =
    portfolios.data?.reduce((s, p) => s + (p.total_value ?? 0), 0) ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Portfolio</h2>
          <p className="text-sm text-muted-foreground">
            Holdings, allocation, and performance across your portfolios.
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" aria-hidden />
          New Portfolio
        </Button>
      </div>

      {loading ? (
        <CardGridSkeleton count={3} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <MetricCard
            label="Total Portfolio Value"
            value={formatCurrency(totalValue, { compact: true })}
            sublabel="Across all portfolios"
            icon={<Wallet className="h-4 w-4" aria-hidden />}
            accent="emerald"
          />
          <MetricCard
            label="Portfolios"
            value={portfolios.data?.length ?? 0}
            sublabel="Active"
            icon={<Building2 className="h-4 w-4" aria-hidden />}
            accent="blue"
          />
          <MetricCard
            label="Primary"
            value={portfolios.data?.some((p) => p.is_primary) ? "Yes" : "No"}
            sublabel="Primary portfolio set"
            icon={<PieChart className="h-4 w-4" aria-hidden />}
            accent="violet"
          />
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {portfolios.data?.map((portfolio) => (
          <Card key={portfolio.id}>
            <CardHeader className="flex-row items-start justify-between space-y-0">
              <div>
                <CardTitle className="text-base">{portfolio.name}</CardTitle>
                <CardDescription>
                  {portfolio.description || "Personal portfolio"}
                </CardDescription>
              </div>
              {portfolio.is_primary ? (
                <Badge>Primary</Badge>
              ) : null}
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-muted-foreground">Total value</p>
                <p className="text-2xl font-bold tracking-tight">
                  {formatCurrency(portfolio.total_value, { compact: true })}
                </p>
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Updated {formatDate(portfolio.updated_at, { day: "numeric", month: "short" })}</span>
                <Button variant="ghost" size="sm" asChild>
                  <a href={`/app/portfolio/${portfolio.id}`}>
                    View <ArrowRight className="ml-1 h-3 w-3" aria-hidden />
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {!loading && !portfolios.data?.length ? (
        <Card>
          <CardContent className="py-16 text-center">
            <PieChart className="mx-auto h-12 w-12 text-muted-foreground/40" aria-hidden />
            <h3 className="mt-4 text-lg font-medium">No portfolios yet</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Create your first portfolio and start tracking your investments.
            </p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
