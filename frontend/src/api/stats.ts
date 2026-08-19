import client from "./client";

export interface ActivityPoint {
  date: string;
  fetched: number;
  seen: number;
  read: number;
  relevant: number;
  disliked: number;
}

export interface ImpactTrendPoint {
  date: string;
  count: number;
  // null only when count is 0, which can't happen for a returned point
  // (points with no data aren't included at all) -- typed nullable to
  // mirror the backend response shape exactly.
  avg_impact: number | null;
  high_impact_count: number;
}

export interface ImpactTrendResponse {
  points: ImpactTrendPoint[];
  // The user's UserSettings.push_min_relevance -- same threshold that
  // gates push notifications, reused here so "high impact" means the same
  // thing in this chart as it does in a push alert.
  high_impact_threshold: number;
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

export interface SourceSignalQuality {
  id: string;
  name: string;
  source_type: string;
  total: number;
  relevant: number;
  disliked: number;
  read: number;
}

export interface RelevanceCalibrationBucket {
  score: number;
  count: number;
  relevant_count: number;
  // null when count is 0 -- no data yet for this score, distinct from a
  // real 0% rate.
  relevant_rate: number | null;
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

export interface CategoryTrendResponse {
  categories: CategoryTrendResult[];
  // Distinct-article count per day across *all* categories combined (same
  // source filter, no category restriction) -- can't be derived by summing
  // `categories[].points` client-side, since an article with two categories
  // would double-count in that sum but only counts once here.
  totals: CategoryTrendPoint[];
}

export type KeywordMomentumDirection = "rising" | "falling";

export interface KeywordMomentumPoint {
  date: string;
  count: number;
}

export interface KeywordMomentumResult {
  keyword: string;
  total_mentions: number;
  // is_newcomer only applies to direction="rising" (zero history before the
  // most recent bucket); is_dormant only to direction="falling" (nonzero
  // history but zero in the most recent bucket) -- both are always present
  // in the response regardless of direction, since they're cheap to compute
  // from the same monthly series either way.
  is_newcomer: boolean;
  is_dormant: boolean;
  // Relative (rate-of-change-vs-own-mean) slopes, not raw counts -- see the
  // backend's _relative_slope docstring. weekly catches sudden spikes/
  // drop-offs, monthly catches slow sustained movement a weekly window is
  // too short to show.
  weekly_slope: number;
  monthly_slope: number;
  weekly_points: KeywordMomentumPoint[];
  monthly_points: KeywordMomentumPoint[];
}

export const statsApi = {
  activity: (days: number) =>
    client.get<ActivityPoint[]>("/stats/activity", { params: { days } }).then((r) => r.data),
  impactTrend: (days: number, sourceIds: string[]) =>
    client
      .get<ImpactTrendResponse>("/stats/impact-trend", {
        params: { days, ...(sourceIds.length ? { source_ids: sourceIds } : {}) },
        paramsSerializer: { indexes: null },
      })
      .then((r) => r.data),
  byCategory: (days: number) =>
    client.get<CategoryCount[]>("/stats/by-category", { params: { days } }).then((r) => r.data),
  bySource: (days: number) =>
    client.get<SourceCount[]>("/stats/by-source", { params: { days } }).then((r) => r.data),
  sourceSignalQuality: (days: number) =>
    client
      .get<SourceSignalQuality[]>("/stats/source-signal-quality", { params: { days } })
      .then((r) => r.data),
  weightHistory: (days: number) =>
    client.get<CategoryWeightHistory[]>("/stats/weight-history", { params: { days } }).then((r) => r.data),
  relevanceCalibration: (days: number) =>
    client
      .get<RelevanceCalibrationBucket[]>("/stats/relevance-calibration", { params: { days } })
      .then((r) => r.data),
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
      .get<CategoryTrendResponse>("/stats/category-trend", {
        params: { days, ...(sourceIds.length ? { source_ids: sourceIds } : {}) },
        paramsSerializer: { indexes: null },
      })
      .then((r) => r.data),
  keywordMomentum: (sourceIds: string[], categoryIds: string[], direction: KeywordMomentumDirection) =>
    client
      .get<KeywordMomentumResult[]>("/stats/keyword-momentum", {
        params: {
          direction,
          ...(sourceIds.length ? { source_ids: sourceIds } : {}),
          ...(categoryIds.length ? { category_ids: categoryIds } : {}),
        },
        paramsSerializer: { indexes: null },
      })
      .then((r) => r.data),
};
