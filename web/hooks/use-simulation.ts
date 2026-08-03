import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { ScenarioCreate, SimulationCreate } from "@/types/api";

export const simKeys = {
  all: ["simulation"] as const,
  list: () => [...simKeys.all, "list"] as const,
  scenarioList: () => [...simKeys.all, "scenarios"] as const,
};

export function useSimulations() {
  return useQuery({
    queryKey: simKeys.list(),
    queryFn: () => api.listSimulations(),
  });
}

export function useRunSimulation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SimulationCreate) => api.runSimulation(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: simKeys.list() });
    },
  });
}

export function useScenarios() {
  return useQuery({
    queryKey: simKeys.scenarioList(),
    queryFn: () => api.listScenarios(),
  });
}

export function useRunScenario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ScenarioCreate) => api.runScenario(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: simKeys.scenarioList() });
    },
  });
}
