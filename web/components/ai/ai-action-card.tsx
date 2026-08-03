"use client";

// AI action card — a single proposed action from the AI advisor.
// Supports propose → confirm → execute flows. Each action triggers the
// corresponding backend API (never a frontend calculation).

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowRight,
  Check,
  Loader2,
  PieChart,
  RefreshCw,
  Sparkles,
  Target,
  X,
  Zap,
} from "lucide-react";
import type { AiAction } from "@/types/api";
import { api } from "@/lib/api/client";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function AiActionCard({ action }: { action: AiAction }) {
  const router = useRouter();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const iconFor = () => {
    switch (action.type) {
      case "apply_allocation":
      case "rebalance":
        return <PieChart className="h-4 w-4" aria-hidden />;
      case "run_simulation":
      case "run_scenario":
        return <Activity className="h-4 w-4" aria-hidden />;
      case "update_goal":
        return <Target className="h-4 w-4" aria-hidden />;
      case "generate_recommendations":
        return <Sparkles className="h-4 w-4" aria-hidden />;
      case "navigate":
        return <ArrowRight className="h-4 w-4" aria-hidden />;
      default:
        return <Zap className="h-4 w-4" aria-hidden />;
    }
  };

  const execute = async () => {
    setBusy(true);
    try {
      switch (action.type) {
        case "navigate": {
          const href =
            typeof action.meta?.href === "string"
              ? action.meta.href
              : "/app";
          router.push(href);
          break;
        }
        case "run_simulation": {
          await api.runSimulation({
            expected_return: num(action.meta?.expected_return, 0.1),
            volatility: num(action.meta?.volatility, 0.18),
            monthly_investment: num(action.meta?.monthly_investment, 0),
            inflation: num(action.meta?.inflation, 0.06),
            horizon_years: num(action.meta?.horizon_years, 20),
            initial_corpus: num(action.meta?.initial_corpus, 0),
            target_amount: num(action.meta?.target_amount, null),
            simulations: int(action.meta?.simulations, 10_000),
          });
          toast.success("Simulation complete");
          router.push("/app/monte-carlo");
          break;
        }
        case "run_scenario": {
          await api.runScenario({
            scenario_type: "market_crash",
            ...(action.meta?.scenario_type
              ? { scenario_type: action.meta.scenario_type as unknown as "market_crash" }
              : {}),
          });
          toast.success("Scenario analysis complete");
          router.push("/app/scenarios");
          break;
        }
        case "apply_allocation":
        case "rebalance": {
          const portfolios = await api.listPortfolios();
          const primary =
            portfolios.find((p) => p.is_primary) ?? portfolios[0];
          if (primary) {
            await api.rebalance(primary.id, action.meta?.target as Record<string, number> | null);
            toast.success("Rebalance plan generated");
            router.push("/app/allocation");
          } else {
            toast.warning("Create a portfolio first to apply an allocation.");
          }
          break;
        }
        case "generate_recommendations": {
          await api.generateRecommendations(24);
          toast.success("Recommendations generated");
          router.push("/app/recommendations");
          break;
        }
        case "update_goal": {
          router.push("/app/goals");
          break;
        }
        case "accept_recommendation": {
          if (action.meta?.id) {
            await api.updateRecommendationStatus(String(action.meta.id), "accepted");
            toast.success("Recommendation accepted");
          }
          break;
        }
        case "decline_recommendation": {
          if (action.meta?.id) {
            await api.updateRecommendationStatus(String(action.meta.id), "dismissed");
            toast.success("Recommendation dismissed");
          }
          break;
        }
        case "schedule_review": {
          toast.info("Review scheduling is available on the Advisor dashboard.");
          router.push("/app/advisor");
          break;
        }
        case "increase_sip":
        case "apply_plan":
        default: {
          toast.info(`${action.label} — you can action this from the related page.`);
          break;
        }
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
      setConfirmOpen(false);
    }
  };

  const needsConfirmation = !["navigate", "view_research", "compare_securities"].includes(
    action.type
  );
  const viewHref =
    (action.type === "view_research" || action.type === "compare_securities") &&
    typeof action.meta?.href === "string"
      ? action.meta.href
      : null;

  return (
    <>
      <div className="flex items-start gap-2 rounded-lg border bg-card p-2.5 text-sm shadow-sm">
        <div className="mt-0.5 text-primary">{iconFor()}</div>
        <div className="min-w-0 flex-1">
          <p className="font-medium leading-snug">{action.label}</p>
          {action.description ? (
            <p className="mt-0.5 text-xs text-muted-foreground">{action.description}</p>
          ) : null}
        </div>
        <Button
          size="sm"
          variant={action.primary ? "default" : "outline"}
          onClick={() => {
            if (viewHref) {
              router.push(viewHref);
            } else if (needsConfirmation) {
              setConfirmOpen(true);
            } else {
              void execute();
            }
          }}
          disabled={busy}
        >
          {busy ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
          ) : (
            <Check className="h-3.5 w-3.5" aria-hidden />
          )}
          <span className="ml-1.5 sr-only sm:not-sr-only">
            {action.primary ? "Run" : "Open"}
          </span>
        </Button>
      </div>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{action.label}</DialogTitle>
            <DialogDescription>
              {action.description ?? "The AI advisor will run the backend engine and update your plan."}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setConfirmOpen(false)}
              disabled={busy}
            >
              <X className="mr-2 h-4 w-4" aria-hidden /> Cancel
            </Button>
            <Button onClick={() => void execute()} disabled={busy}>
              {busy ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" aria-hidden />
              )}
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function num(v: unknown, fallback: number | null): number {
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : (fallback ?? 0);
}

function int(v: unknown, fallback: number): number {
  return Math.round(num(v, fallback));
}
