import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronRight, Podcast, Trash2 } from "lucide-react";
import { usePodcastEpisodes, useDeletePodcastEpisode } from "../hooks/usePodcasts";
import { useToast } from "../components/ui/Toaster";
import { cn } from "../lib/utils";
import type { PodcastEpisode, PodcastEpisodeStatus } from "../types/podcast";

function formatDuration(seconds: number | null): string {
  if (!seconds && seconds !== 0) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function StatusBadge({ status }: { status: PodcastEpisodeStatus }) {
  const { t } = useTranslation();
  const styles: Record<PodcastEpisodeStatus, string> = {
    pending: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
    generating: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
    ready: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
    failed: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  };
  return (
    <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", styles[status])}>
      {t(`podcast.status.${status}`)}
    </span>
  );
}

function EpisodeCard({ episode }: { episode: PodcastEpisode }) {
  const { t } = useTranslation();
  const toast = useToast();
  const deleteEpisode = useDeletePodcastEpisode();
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-900">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">{episode.show_name}</h3>
            <StatusBadge status={episode.status} />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {new Date(episode.created_at).toLocaleString()}
            {episode.duration_seconds != null && ` · ${formatDuration(episode.duration_seconds)}`}
          </p>
        </div>
        <button
          onClick={() =>
            toast.confirm(t("podcast.confirmDeleteEpisode"), () => deleteEpisode.mutate(episode.id))
          }
          className="p-1.5 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 transition-colors shrink-0"
          title={t("common.delete")}
        >
          <Trash2 size={14} />
        </button>
      </div>

      {episode.status === "ready" && (
        <audio controls preload="none" className="w-full mt-3" src={`/api/podcasts/episodes/${episode.id}/audio`} />
      )}

      {episode.status === "failed" && episode.error_message && (
        <p className="mt-3 text-xs text-red-600 dark:text-red-400">{episode.error_message}</p>
      )}

      {episode.script && episode.script.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-100"
          >
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            {t("podcast.transcript")}
          </button>
          {expanded && (
            <div className="mt-2 space-y-2 text-sm text-gray-700 dark:text-gray-300 max-h-64 overflow-y-auto pr-2">
              {episode.script.map((turn, i) => (
                <p key={i}>
                  <span className="font-medium">{turn.host_id}: </span>
                  {turn.text}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PodcastsPage() {
  const { t } = useTranslation();
  const { data, isLoading } = usePodcastEpisodes(1, 30);
  const episodes = data?.items ?? [];

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">{t("podcast.title")}</h1>

      {isLoading && <p className="text-sm text-gray-400">{t("common.loading")}</p>}

      {!isLoading && episodes.length === 0 && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <Podcast size={32} className="text-gray-300 dark:text-gray-600" />
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("podcast.empty")}</p>
          <Link
            to="/settings"
            className="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            {t("podcast.emptyCta")}
          </Link>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {episodes.map((episode) => (
          <EpisodeCard key={episode.id} episode={episode} />
        ))}
      </div>
    </div>
  );
}
