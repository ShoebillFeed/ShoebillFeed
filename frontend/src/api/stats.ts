import client from "./client";

export interface ActivityPoint {
  date: string;
  fetched: number;
  seen: number;
  read: number;
  relevant: number;
  disliked: number;
}

export interface CategoryCount {
  id: string;
  name: string;
  color: string;
  count: number;
}

export interface SourceCategoryCount {
  id: string;
  name: string;
  color: string;
  count: number;
}

export interface SourceCount {
  id: string;
  name: string;
  source_type: string;
  total: number;
  categories: SourceCategoryCount[];
}

export interface WeightSnapshot {
  date: string;
  weight: number;
  total_marked: number;
}

export interface CategoryWeightHistory {
  id: string;
  name: string;
  color: string;
  snapshots: WeightSnapshot[];
}

export interface SourceClusterCategory {
  name: string;
  count: number;
  color: string;
}

export interface SourceMeta {
  id: string;
  name: string;
  source_type: string;
}

export interface SourceClusterPair {
  source_a: SourceMeta;
  source_b: SourceMeta;
  total: number;
  categories: SourceClusterCategory[];
}

export interface KeywordInCluster {
  keyword: string;
  score: number;
  weight: number;
}

export interface KeywordClusterMapEntry {
  category_name: string;
  category_color: string;
  cluster_label: string;
  cluster_size: number;
  keywords: KeywordInCluster[];
}

export interface PodcastEpisodeCategoryCount {
  id: string;
  name: string;
  color: string;
  count: number;
}

export interface PodcastEpisodeKeywordCount {
  keyword: string;
  count: number;
}

export interface PodcastEpisodeSourceCount {
  name: string;
  count: number;
}

export interface PodcastEpisodeStat {
  id: string;
  generated_at: string;
  total_stories: number;
  categories: PodcastEpisodeCategoryCount[];
  top_keywords: PodcastEpisodeKeywordCount[];
  top_sources: PodcastEpisodeSourceCount[];
}

export interface KeywordTrendTopicRequest {
  label: string;
  keywords: string[];
}

export interface KeywordTrendRequest {
  topics: KeywordTrendTopicRequest[];
  category_ids?: string[];
  source_ids?: string[];
  // null means all time -- no lower bound on the query.
  days?: number | null;
}

export interface KeywordTrendPoint {
  date: string;
  count: number;
}

export interface KeywordTrendResult {
  label: string;
  points: KeywordTrendPoint[];
}

export interface CategoryTrendPoint {
  date: string;
  count: number;
}

export interface CategoryTrendResult {
  id: string;
  name: string;
  color: string;
  points: CategoryTrendPoint[];
}

export const statsApi = {
  activity: (days: number) =>
    client.get<ActivityPoint[]>("/stats/activity", { params: { days } }).then((r) => r.data),
  byCategory: (days: number) =>
    client.get<CategoryCount[]>("/stats/by-category", { params: { days } }).then((r) => r.data),
  bySource: (days: number) =>
    client.get<SourceCount[]>("/stats/by-source", { params: { days } }).then((r) => r.data),
  weightHistory: (days: number) =>
    client.get<CategoryWeightHistory[]>("/stats/weight-history", { params: { days } }).then((r) => r.data),
  sourceClusters: (days: number) =>
    client.get<SourceClusterPair[]>("/stats/source-clusters", { params: { days } }).then((r) => r.data),
  keywordClusterMap: () =>
    client.get<KeywordClusterMapEntry[]>("/stats/keyword-cluster-map").then((r) => r.data),
  refreshClusters: () =>
    client.post("/stats/refresh-clusters").then((r) => r.data),
  podcastEpisodes: (showId: string, limit = 20) =>
    client
      .get<PodcastEpisodeStat[]>("/stats/podcast-episodes", { params: { show_id: showId, limit } })
      .then((r) => r.data),
  keywordTrend: (payload: KeywordTrendRequest) =>
    client.post<KeywordTrendResult[]>("/stats/keyword-trend", payload).then((r) => r.data),
  categoryTrend: (days: number, sourceIds: string[]) =>
    client
      .get<CategoryTrendResult[]>("/stats/category-trend", {
        params: { days, ...(sourceIds.length ? { source_ids: sourceIds } : {}) },
        paramsSerializer: { indexes: null },
      })
      .then((r) => r.data),
};
