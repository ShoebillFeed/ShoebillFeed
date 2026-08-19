import { useMutation, useQuery } from "@tanstack/react-query";
import { statsApi } from "../api/stats";
import type { KeywordMomentumDirection, KeywordTrendRequest } from "../api/stats";

export function useActivityStats(days: number) {
  return useQuery({
    queryKey: ["stats", "activity", days],
    queryFn: () => statsApi.activity(days),
  });
}

export function useImpactTrend(days: number, sourceIds: string[]) {
  return useQuery({
    queryKey: ["stats", "impact-trend", days, sourceIds],
    queryFn: () => statsApi.impactTrend(days, sourceIds),
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

export function useSourceSignalQuality(days: number) {
  return useQuery({
    queryKey: ["stats", "source-signal-quality", days],
    queryFn: () => statsApi.sourceSignalQuality(days),
  });
}

export function useWeightHistory(days: number) {
  return useQuery({
    queryKey: ["stats", "weight-history", days],
    queryFn: () => statsApi.weightHistory(days),
  });
}

export function useRelevanceCalibration(days: number) {
  return useQuery({
    queryKey: ["stats", "relevance-calibration", days],
    queryFn: () => statsApi.relevanceCalibration(days),
  });
}

export function useSourceClusters(days: number) {
  return useQuery({
    queryKey: ["stats", "source-clusters", days],
    queryFn: () => statsApi.sourceClusters(days),
  });
}

export function useKeywordClusterMap() {
  return useQuery({
    queryKey: ["stats", "keyword-cluster-map"],
    queryFn: () => statsApi.keywordClusterMap(),
  });
}

export function usePodcastEpisodeStats(showId: string | null) {
  return useQuery({
    queryKey: ["stats", "podcast-episodes", showId],
    queryFn: () => statsApi.podcastEpisodes(showId as string),
    enabled: !!showId,
  });
}

// A POST driven by user-configured topics/filters, not a simple GET keyed by
// static params -- a mutation (triggered from an effect) fits better than a
// query key that would have to encode the full topic list.
export function useKeywordTrend() {
  return useMutation({
    mutationFn: (payload: KeywordTrendRequest) => statsApi.keywordTrend(payload),
  });
}

export function useCategoryTrend(days: number, sourceIds: string[]) {
  return useQuery({
    queryKey: ["stats", "category-trend", days, sourceIds],
    queryFn: () => statsApi.categoryTrend(days, sourceIds),
  });
}

export function useKeywordMomentum(sourceIds: string[], categoryIds: string[], direction: KeywordMomentumDirection) {
  return useQuery({
    queryKey: ["stats", "keyword-momentum", sourceIds, categoryIds, direction],
    queryFn: () => statsApi.keywordMomentum(sourceIds, categoryIds, direction),
  });
}
