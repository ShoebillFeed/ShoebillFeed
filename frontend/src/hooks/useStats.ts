import { useQuery } from "@tanstack/react-query";
import { statsApi } from "../api/stats";

export function useActivityStats(days: number) {
  return useQuery({
    queryKey: ["stats", "activity", days],
    queryFn: () => statsApi.activity(days),
  });
}

export function useCategoryStats(days: number) {
  return useQuery({
    queryKey: ["stats", "by-category", days],
    queryFn: () => statsApi.byCategory(days),
  });
}

export function useSourceStats(days: number) {
  return useQuery({
    queryKey: ["stats", "by-source", days],
    queryFn: () => statsApi.bySource(days),
  });
}

export function useWeightHistory(days: number) {
  return useQuery({
    queryKey: ["stats", "weight-history", days],
    queryFn: () => statsApi.weightHistory(days),
  });
}

export function useSourceClusters(days: number) {
  return useQuery({
    queryKey: ["stats", "source-clusters", days],
    queryFn: () => statsApi.sourceClusters(days),
  });
}
