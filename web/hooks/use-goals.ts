import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type {
  GoalAnalysisOut,
  GoalCreate,
  GoalOut,
  GoalUpdate,
} from "@/types/api";

export const goalKeys = {
  all: ["goals"] as const,
  lists: () => [...goalKeys.all, "list"] as const,
  list: () => [...goalKeys.lists()] as const,
  details: () => [...goalKeys.all, "detail"] as const,
  detail: (id: string) => [...goalKeys.details(), id] as const,
  analysis: () => [...goalKeys.all, "analysis"] as const,
  progress: (id: string) => [...goalKeys.detail(id), "progress"] as const,
};

export function useGoals() {
  return useQuery({
    queryKey: goalKeys.list(),
    queryFn: () => api.listGoals(),
  });
}

export function useGoal(id: string) {
  return useQuery({
    queryKey: goalKeys.detail(id),
    queryFn: () => api.getGoal(id),
    enabled: Boolean(id),
  });
}

export function useGoalAnalysis() {
  return useQuery({
    queryKey: goalKeys.analysis(),
    queryFn: () => api.analyseGoals(),
  });
}

export function useCreateGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: GoalCreate) => api.createGoal(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: goalKeys.list() });
      qc.invalidateQueries({ queryKey: goalKeys.analysis() });
    },
  });
}

export function useUpdateGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: GoalUpdate }) =>
      api.updateGoal(id, body),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: goalKeys.list() });
      if (updated?.id) {
        qc.invalidateQueries({ queryKey: goalKeys.detail(updated.id) });
      }
      qc.invalidateQueries({ queryKey: goalKeys.analysis() });
    },
  });
}

export function useDeleteGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteGoal(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: goalKeys.list() });
      qc.invalidateQueries({ queryKey: goalKeys.analysis() });
    },
  });
}

export function useRecordGoalProgress() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.recordGoalProgress(id),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: goalKeys.progress(id) });
      qc.invalidateQueries({ queryKey: goalKeys.analysis() });
    },
  });
}

export type { GoalAnalysisOut, GoalOut };
