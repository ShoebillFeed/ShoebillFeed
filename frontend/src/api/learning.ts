import client from "./client";

export interface CategoryProfile {
  id: string;
  name: string;
  color: string;
  learned_weight: number;
  manual_weight: number;
  total_marked: number;
}

export interface KeywordProfile {
  keyword: string;
  weight: number;
  total_marked: number;
}

export interface LearningProfile {
  categories: CategoryProfile[];
  keywords: KeywordProfile[];
}

export const learningApi = {
  profile: () =>
    client.get<LearningProfile>("/learning/profile").then((r) => r.data),

  setCategoryWeight: (category_id: string, manual_weight: number) =>
    client.patch(`/learning/categories/${category_id}/weight`, { manual_weight }),

  deleteKeyword: (keyword: string) =>
    client.delete(`/learning/keywords/${encodeURIComponent(keyword)}`),
};
