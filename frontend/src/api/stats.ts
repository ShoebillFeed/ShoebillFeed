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

export interface KeywordClusterHistory {
  category_name: string;
  category_color: string;
  cluster_label: string;
  current_weight: number;
  snapshots: { date: string; weight: number }[];
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
  keywordClusterHistory: (days: number) =>
    client.get<KeywordClusterHistory[]>("/stats/keyword-cluster-history", { params: { days } }).then((r) => r.data),
  keywordClusterMap: () =>
    client.get<KeywordClusterMapEntry[]>("/stats/keyword-cluster-map").then((r) => r.data),
};
