import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { newsApi } from "../api/news";
import { clustersApi } from "../api/clusters";
import type { ApiTab } from "../api/news";

export function useNews(params: {
  tab: ApiTab;
  category_id?: string;
  source_id?: string;
  is_read?: boolean;
  read_later?: boolean;
  page?: number;
}) {
  return useQuery({
    queryKey: ["news", params],
    queryFn: () => newsApi.list({ page_size: 50, ...params }),
    refetchInterval: 60_000,
  });
}

export function useInfiniteNews(params: {
  tab: ApiTab;
  category_id?: string;
  source_id?: string;
  is_read?: boolean;
  read_later?: boolean;
}) {
  return useInfiniteQuery({
    queryKey: ["news", "infinite", params],
    queryFn: ({ pageParam }) => newsApi.list({ page_size: 50, ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined,
    refetchInterval: 60_000,
  });
}

export function useToggleRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: newsApi.toggleRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["news"] }),
  });
}

export function useToggleRelevant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: newsApi.toggleRelevant,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["news"] }),
  });
}

export function useToggleReadLater() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: newsApi.toggleReadLater,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["news"] }),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (category_id?: string) => newsApi.markAllRead(category_id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["news"] }),
  });
}

export function useDeleteNewsItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: newsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["news"] }),
  });
}

export function useToggleClusterRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clustersApi.toggleRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["news"] }),
  });
}

export function useToggleClusterRelevant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clustersApi.toggleRelevant,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["news"] }),
  });
}

export function useToggleClusterReadLater() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clustersApi.toggleReadLater,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["news"] }),
  });
}

export function useDeleteCluster() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clustersApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["news"] }),
  });
}
