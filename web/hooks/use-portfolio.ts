import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type {
  AllocationOut,
  HoldingCreate,
  PortfolioCreate,
  RebalanceOut,
} from "@/types/api";

export const portfolioKeys = {
  all: ["portfolio"] as const,
  lists: () => [...portfolioKeys.all, "list"] as const,
  list: () => [...portfolioKeys.lists()] as const,
  details: () => [...portfolioKeys.all, "detail"] as const,
  detail: (id: string) => [...portfolioKeys.details(), id] as const,
  holdings: (id: string) => [...portfolioKeys.detail(id), "holdings"] as const,
};

export function usePortfolios() {
  return useQuery({
    queryKey: portfolioKeys.list(),
    queryFn: () => api.listPortfolios(),
  });
}

export function usePortfolio(id: string) {
  return useQuery({
    queryKey: portfolioKeys.detail(id),
    queryFn: () => api.getPortfolio(id),
    enabled: Boolean(id),
  });
}

export function useHoldings(portfolioId: string) {
  return useQuery({
    queryKey: portfolioKeys.holdings(portfolioId),
    queryFn: () => api.listHoldings(portfolioId),
    enabled: Boolean(portfolioId),
  });
}

export function useCreatePortfolio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PortfolioCreate) => api.createPortfolio(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: portfolioKeys.list() });
    },
  });
}

export function useAddHolding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      portfolioId,
      body,
    }: {
      portfolioId: string;
      body: HoldingCreate;
    }) => api.addHolding(portfolioId, body),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: portfolioKeys.holdings(vars.portfolioId) });
      qc.invalidateQueries({ queryKey: portfolioKeys.list() });
      qc.invalidateQueries({ queryKey: portfolioKeys.detail(vars.portfolioId) });
    },
  });
}

export function useRebalance(portfolioId: string) {
  return useMutation({
    mutationFn: (target?: Record<string, number> | null) =>
      api.rebalance(portfolioId, target),
  });
}

export type { AllocationOut, RebalanceOut };
