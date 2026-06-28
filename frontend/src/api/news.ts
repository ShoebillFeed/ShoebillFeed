import client from "./client";
import type { NewsPage } from "../types/news";

export type ApiTab = "newest" | "relevant" | "impact";

export interface NewsParams {
  tab: ApiTab;
  category_ids?: string[];
  source_ids?: string[];
  is_read?: boolean;
  read_later?: boolean;
  uncategorized?: boolean;
  page?: number;
  page_size?: number;
}

export const newsApi = {
  list: (params: NewsParams) =>
    client.get<NewsPage>("/news", { params }).then((r) => r.data),

  search: (q: string, page_size = 50) =>
    client.get<import("../types/news").NewsItem[]>("/news/search", { params: { q, page_size } }).then((r) => r.data),

  toggleRead: (id: string) =>
    client.patch(`/news/${id}/read`).then((r) => r.data),

  toggleRelevant: (id: string) =>
    client.patch(`/news/${id}/relevant`).then((r) => r.data),

  toggleReadLater: (id: string) =>
    client.patch(`/news/${id}/read-later`).then((r) => r.data),

  dislike: (id: string) =>
    client.patch(`/news/${id}/dislike`).then((r) => r.data),

  markAllRead: (category_id?: string) =>
    client.post("/news/mark-all-read", null, { params: { category_id } }).then((r) => r.data),

  markShown: (payload: { item_ids: string[]; cluster_ids: string[] }) =>
    client.post("/news/mark-shown", payload).then((r) => r.data),

  reprocess: (id: string) =>
    client.post(`/news/${id}/reprocess`).then((r) => r.data),

  delete: (id: string) =>
    client.delete(`/news/${id}`).then((r) => r.data),
};
