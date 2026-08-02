import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { podcastsApi } from "../api/podcasts";
import type { PodcastShowCreate, PodcastShowUpdate, PodcastEpisodePage } from "../types/podcast";

// Poll while any episode in the result is still being generated, so the UI
// picks up the ready/failed transition without a manual refresh.
const _pollWhileGenerating = (query: { state: { data?: PodcastEpisodePage } }) =>
  query.state.data?.items.some((e) => e.status === "pending" || e.status === "generating") ? 4000 : false;

export function usePodcastShows() {
  return useQuery({ queryKey: ["podcast-shows"], queryFn: podcastsApi.listShows });
}

export function useCreatePodcastShow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PodcastShowCreate) => podcastsApi.createShow(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["podcast-shows"] }),
  });
}

export function useUpdatePodcastShow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PodcastShowUpdate }) => podcastsApi.updateShow(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["podcast-shows"] }),
  });
}

export function useDeletePodcastShow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: podcastsApi.deleteShow,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["podcast-shows"] });
      qc.invalidateQueries({ queryKey: ["podcast-episodes"] });
    },
  });
}

export function useGeneratePodcastNow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: podcastsApi.generateNow,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["podcast-episodes"] }),
  });
}

export function useEnablePublicFeed() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: podcastsApi.enablePublicFeed,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["podcast-shows"] }),
  });
}

export function useDisablePublicFeed() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: podcastsApi.disablePublicFeed,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["podcast-shows"] }),
  });
}

export function useRegeneratePublicFeed() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: podcastsApi.regeneratePublicFeed,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["podcast-shows"] }),
  });
}

export function usePodcastEpisodes(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["podcast-episodes", page, pageSize],
    queryFn: () => podcastsApi.listEpisodes({ page, page_size: pageSize }),
    refetchInterval: _pollWhileGenerating,
  });
}

export function useShowEpisodes(showId: string | undefined) {
  return useQuery({
    queryKey: ["podcast-episodes", "show", showId],
    queryFn: () => podcastsApi.listShowEpisodes(showId as string),
    enabled: !!showId,
  });
}

export function useDeletePodcastEpisode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: podcastsApi.deleteEpisode,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["podcast-episodes"] }),
  });
}

export function usePodcastVoices(language: string) {
  return useQuery({
    queryKey: ["podcast-voices", language],
    queryFn: () => podcastsApi.listVoices(language),
    enabled: !!language,
  });
}
