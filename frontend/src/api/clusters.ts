import client from "./client";
import type { NewsCluster } from "../types/news";

export const clustersApi = {
  toggleRead: (id: string) =>
    client.patch<NewsCluster>(`/clusters/${id}/read`).then((r) => r.data),

  toggleRelevant: (id: string) =>
    client.patch<NewsCluster>(`/clusters/${id}/relevant`).then((r) => r.data),

  toggleReadLater: (id: string) =>
    client.patch<NewsCluster>(`/clusters/${id}/read-later`).then((r) => r.data),

  dislike: (id: string) =>
    client.patch(`/clusters/${id}/dislike`).then((r) => r.data),

  delete: (id: string) =>
    client.delete(`/clusters/${id}`).then((r) => r.data),
};
