import client from "./client";
import type {
  PodcastShow,
  PodcastShowCreate,
  PodcastShowUpdate,
  PodcastEpisode,
  PodcastEpisodePage,
  PodcastVoice,
} from "../types/podcast";

export const podcastsApi = {
  listShows: () => client.get<PodcastShow[]>("/podcasts/shows").then((r) => r.data),
  createShow: (data: PodcastShowCreate) => client.post<PodcastShow>("/podcasts/shows", data).then((r) => r.data),
  updateShow: (id: string, data: PodcastShowUpdate) =>
    client.patch<PodcastShow>(`/podcasts/shows/${id}`, data).then((r) => r.data),
  deleteShow: (id: string) => client.delete(`/podcasts/shows/${id}`),
  generateNow: (id: string) => client.post(`/podcasts/shows/${id}/generate`).then((r) => r.data),
  enablePublicFeed: (id: string) => client.post<PodcastShow>(`/podcasts/shows/${id}/public-feed`).then((r) => r.data),
  disablePublicFeed: (id: string) => client.delete<PodcastShow>(`/podcasts/shows/${id}/public-feed`).then((r) => r.data),
  regeneratePublicFeed: (id: string) =>
    client.post<PodcastShow>(`/podcasts/shows/${id}/public-feed/regenerate`).then((r) => r.data),
  listShowEpisodes: (showId: string) =>
    client.get<PodcastEpisode[]>(`/podcasts/shows/${showId}/episodes`).then((r) => r.data),
  listEpisodes: (params: { page?: number; page_size?: number } = {}) =>
    client.get<PodcastEpisodePage>("/podcasts/episodes", { params }).then((r) => r.data),
  getEpisode: (id: string) => client.get<PodcastEpisode>(`/podcasts/episodes/${id}`).then((r) => r.data),
  deleteEpisode: (id: string) => client.delete(`/podcasts/episodes/${id}`),
  listVoices: (language: string) =>
    client.get<PodcastVoice[]>("/podcasts/voices", { params: { language } }).then((r) => r.data),
};
