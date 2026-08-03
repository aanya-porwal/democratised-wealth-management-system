import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { AllocationRequest } from "@/types/api";

export const allocationKeys = {
  all: ["allocation"] as const,
  result: () => [...allocationKeys.all, "result"] as const,
};

export function useAllocation() {
  return useQuery({
    queryKey: allocationKeys.result(),
    queryFn: () => api.computeAllocation(),
    staleTime: 5 * 60_000,
  });
}

export function useComputeAllocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: AllocationRequest = {}) => api.computeAllocation(body),
    onSuccess: (data) => {
      qc.setQueryData(allocationKeys.result(), data);
    },
  });
}
