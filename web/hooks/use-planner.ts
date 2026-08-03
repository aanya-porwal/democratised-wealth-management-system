import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";

export const plannerKeys = {
  all: ["planner"] as const,
  plan: () => [...plannerKeys.all, "plan"] as const,
};

export function useFinancialPlan() {
  return useQuery({
    queryKey: plannerKeys.plan(),
    queryFn: () => api.getPlan(),
    staleTime: 5 * 60_000,
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: ["system", "health"],
    queryFn: () => api.systemHealth(),
    refetchInterval: 60_000,
  });
}

export function useSystemReady() {
  return useQuery({
    queryKey: ["system", "ready"],
    queryFn: () => api.systemReady(),
    refetchInterval: 30_000,
  });
}
