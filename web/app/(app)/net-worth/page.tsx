"use client";

import { usePortfolios } from "@/hooks/use-portfolio";
import { useFinancialPlan } from "@/hooks/use-planner";
import { MetricCard } from "@/components/metric-card";
import { CardGridSkeleton } from "@/components/skeletons";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wallet, TrendingUp, TrendingDown, IndianRupee, Building, PiggyBank, CreditCard } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

export default function NetWorthPage() {
  const portfolios = usePortfolios();
  const plan = useFinancialPlan();

  const loading = portfolios.isLoading;

  const totalValue = portfolios.data?.reduce((s, p) => s + (p.total_value ?? 0), 0) ?? 0;
  const totalCost = portfolios.data?.reduce((s, p) => s + (p.total_value ?? 0), 0) ?? 0;
  const gain = totalValue - totalCost;
  const gainPercent = totalCost > 0 ? gain / totalCost : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Net Worth</h2>
        <p className="text-sm text-muted-foreground">
          Your total financial picture across all portfolios.
        </p>
      </div>

      {loading ? (
        <CardGridSkeleton count={4} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            label="Total Net Worth"
            value={formatCurrency(totalValue, { compact: true })}
            sublabel="Across all portfolios"
            icon={<Wallet className="h-4 w-4" aria-hidden />}
            accent="emerald"
          />
          <MetricCard
            label="Total Gain / Loss"
            value={formatCurrency(gain, { compact: true })}
            sublabel={gain >= 0 ? `${(gainPercent * 100).toFixed(1)}% gain` : `${(Math.abs(gainPercent) * 100).toFixed(1)}% loss`}
            icon={gain >= 0 ? <TrendingUp className="h-4 w-4" aria-hidden /> : <TrendingDown className="h-4 w-4" aria-hidden />}
            accent={gain >= 0 ? "emerald" : "red"}
          />
          <MetricCard
            label="Portfolios"
            value={portfolios.data?.length ?? 0}
            sublabel="Active portfolios"
            icon={<Building className="h-4 w-4" aria-hidden />}
            accent="blue"
          />
          <MetricCard
            label="Monthly Savings Rate"
            value={plan.data?.cashflow?.savings_rate !== undefined ? `${(plan.data.cashflow.savings_rate * 100).toFixed(0)}%` : "—"}
            sublabel={plan.data?.cashflow?.monthly_surplus ? formatCurrency(plan.data.cashflow.monthly_surplus, { compact: true }) + " surplus" : ""}
            icon={<PiggyBank className="h-4 w-4" aria-hidden />}
            accent="violet"
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <IndianRupee className="h-4 w-4 text-primary" aria-hidden />
              Asset Breakdown (placeholder)
            </CardTitle>
            <CardDescription>
              Full asset/liability breakdown from the financial profile.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Connect your financial profile and portfolios to see a complete
              breakdown of assets, liabilities and net worth over time.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-primary" aria-hidden />
              Liabilities (placeholder)
            </CardTitle>
            <CardDescription>
              Debt, EMIs and other liabilities from the engine.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Total debt and monthly EMI details will appear here once your
              financial profile is complete.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
