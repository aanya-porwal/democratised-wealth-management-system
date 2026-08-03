import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { RecommendationStatus } from "@/types/api";

export const recKeys = {
  all: ["recommendations"] as const,
  list: () => [...recKeys.all, "list"] as const,
};

export function useRecommendations(limit = 50) {
  return useQuery({
    queryKey: [...recKeys.list(), limit],
    queryFn: () => api.listRecommendations(limit),
  });
}

export function useGenerateRecommendations() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (hoursValid: number) => api.generateRecommendations(hoursValid),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: recKeys.list() });
    },
  });
}

export function useUpdateRecommendationStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: RecommendationStatus }) =>
      api.updateRecommendationStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: recKeys.list() });
    },
  });
}
