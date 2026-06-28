import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { InfiniteData, QueryKey } from "@tanstack/react-query";
import { newsApi } from "../api/news";
import { clustersApi } from "../api/clusters";
import type { ApiTab, SearchParams } from "../api/news";
import type { FeedEntry, NewsPage } from "../types/news";

type SnapCtx = { snapshots: [QueryKey, InfiniteData<NewsPage> | undefined][] };

function snapshotInfinite(qc: ReturnType<typeof useQueryClient>): SnapCtx {
  return {
    snapshots: qc.getQueriesData<InfiniteData<NewsPage>>({ queryKey: ["news", "infinite"] }),
  };
}

function restoreSnapshots(qc: ReturnType<typeof useQueryClient>, ctx: SnapCtx | undefined) {
  ctx?.snapshots.forEach(([key, data]) => qc.setQueryData(key, data));
}

function patchInfiniteItem(
  qc: ReturnType<typeof useQueryClient>,
  id: string,
  patcher: (item: FeedEntry) => FeedEntry,
) {
  qc.setQueriesData<InfiniteData<NewsPage>>(
    { queryKey: ["news", "infinite"] },
    (old) => {
      if (!old) return old;
      return {
        ...old,
        pages: old.pages.map((page) => ({
          ...page,
          items: page.items.map((item) => (item.id === id ? patcher(item) : item)),
        })),
      };
    },
  );
}

function removeInfiniteItem(qc: ReturnType<typeof useQueryClient>, id: string) {
  qc.setQueriesData<InfiniteData<NewsPage>>(
    { queryKey: ["news", "infinite"] },
    (old) => {
      if (!old) return old;
      return {
        ...old,
        pages: old.pages.map((page) => ({
          ...page,
          items: page.items.filter((item) => item.id !== id),
        })),
      };
    },
  );
}

export function useNews(params: {
  tab: ApiTab;
  category_ids?: string[];
  source_ids?: string[];
  is_read?: boolean;
  read_later?: boolean;
  page?: number;
}) {
  return useQuery({
    queryKey: ["news", params],
    queryFn: () => newsApi.list({ page_size: 50, ...params }),
  });
}

export function useInfiniteNews(params: {
  tab: ApiTab;
  category_ids?: string[];
  source_ids?: string[];
  is_read?: boolean;
  read_later?: boolean;
  uncategorized?: boolean;
}) {
  return useInfiniteQuery({
    queryKey: ["news", "infinite", params],
    queryFn: ({ pageParam }) => newsApi.list({ page_size: 50, ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined,
  });
}

const invalidateFeeds = (qc: ReturnType<typeof useQueryClient>) =>
  qc.invalidateQueries({ queryKey: ["news", "infinite"], refetchType: "none" });

export function useToggleRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: newsApi.toggleRead,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      patchInfiniteItem(qc, id, (item) => ({ ...item, is_read: !item.is_read }));
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
    onSettled: () => invalidateFeeds(qc),
  });
}

export function useToggleRelevant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: newsApi.toggleRelevant,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      patchInfiniteItem(qc, id, (item) => ({ ...item, is_relevant: !item.is_relevant }));
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
    onSettled: () => invalidateFeeds(qc),
  });
}

export function useToggleReadLater() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: newsApi.toggleReadLater,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      patchInfiniteItem(qc, id, (item) => ({ ...item, read_later: !item.read_later }));
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
    onSettled: () => invalidateFeeds(qc),
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
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      removeInfiniteItem(qc, id);
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
  });
}

export function useDislikeItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: newsApi.dislike,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      removeInfiniteItem(qc, id);
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
  });
}

export function useDislikeCluster() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clustersApi.dislike,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      removeInfiniteItem(qc, id);
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
  });
}

export function useToggleClusterRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clustersApi.toggleRead,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      patchInfiniteItem(qc, id, (item) => ({ ...item, is_read: !item.is_read }));
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
    onSettled: () => invalidateFeeds(qc),
  });
}

export function useToggleClusterRelevant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clustersApi.toggleRelevant,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      patchInfiniteItem(qc, id, (item) => ({ ...item, is_relevant: !item.is_relevant }));
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
    onSettled: () => invalidateFeeds(qc),
  });
}

export function useToggleClusterReadLater() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clustersApi.toggleReadLater,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      patchInfiniteItem(qc, id, (item) => ({ ...item, read_later: !item.read_later }));
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
    onSettled: () => invalidateFeeds(qc),
  });
}

export function useDeleteCluster() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: clustersApi.delete,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["news", "infinite"] });
      const ctx = snapshotInfinite(qc);
      removeInfiniteItem(qc, id);
      return ctx;
    },
    onError: (_err, _id, ctx) => restoreSnapshots(qc, ctx),
  });
}

export function useMarkShown() {
  return useMutation({ mutationFn: newsApi.markShown });
}

export function useSearchNews(query: string, params?: SearchParams) {
  return useQuery({
    queryKey: ["news", "search", query, params],
    queryFn: () => newsApi.search(query, params),
    enabled: query.trim().length > 0,
    staleTime: 30_000,
  });
}
