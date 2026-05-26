import client from "./client";

export interface ActivityPoint {
  date: string;
  fetched: number;
  read: number;
  starred: number;
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

export const statsApi = {
  activity: (days: number) =>
    client.get<ActivityPoint[]>("/stats/activity", { params: { days } }).then((r) => r.data),
  byCategory: (days: number) =>
    client.get<CategoryCount[]>("/stats/by-category", { params: { days } }).then((r) => r.data),
  bySource: (days: number) =>
    client.get<SourceCount[]>("/stats/by-source", { params: { days } }).then((r) => r.data),
  weightHistory: (days: number) =>
    client.get<CategoryWeightHistory[]>("/stats/weight-history", { params: { days } }).then((r) => r.data),
};
