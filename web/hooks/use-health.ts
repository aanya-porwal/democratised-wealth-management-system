import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { HealthScoreOut } from "@/types/api";

export const healthKeys = {
  all: ["health"] as const,
  latest: () => [...healthKeys.all, "latest"] as const,
  score: () => [...healthKeys.all, "score"] as const,
};

export function useHealthScore() {
  return useQuery({
    queryKey: healthKeys.latest(),
    queryFn: () => api.latestHealthScores(10),
  });
}

export function useComputeHealthScore() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.computeHealthScore(),
    onSuccess: (data: HealthScoreOut) => {
      qc.setQueryData(healthKeys.score(), data);
      qc.invalidateQueries({ queryKey: healthKeys.latest() });
    },
  });
}
