import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Bookmark, ChevronDown, ChevronRight, ExternalLink, Podcast, Trash2 } from "lucide-react";
import { usePodcastEpisodes, useDeletePodcastEpisode } from "../hooks/usePodcasts";
import { useToast } from "../components/ui/Toaster";
import { cn } from "../lib/utils";
import { formatDuration } from "../lib/podcastFormat";
import type { PodcastEpisode, PodcastEpisodeStatus } from "../types/podcast";

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
  const [transcriptExpanded, setTranscriptExpanded] = useState(false);
  const [shownotesExpanded, setShownotesExpanded] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const seekTo = (seconds: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = seconds;
    audio.play().catch(() => {});
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-900">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          {episode.show_cover_image_url && (
            <img
              src={episode.show_cover_image_url}
              alt=""
              className="w-10 h-10 rounded-md object-cover border border-gray-200 dark:border-gray-700 shrink-0"
            />
          )}
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
        <audio
          ref={audioRef}
          controls
          preload="none"
          className="w-full mt-3"
          src={`/api/podcasts/episodes/${episode.id}/audio`}
        />
      )}

      {episode.status === "failed" && episode.error_message && (
        <p className="mt-3 text-xs text-red-600 dark:text-red-400">{episode.error_message}</p>
      )}

      {episode.shownotes && episode.shownotes.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setShownotesExpanded((v) => !v)}
            className="flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-100"
          >
            {shownotesExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            {t("podcast.shownotes")}
          </button>
          {shownotesExpanded && (
            <div className="mt-2">
              {episode.description && (
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-2 whitespace-pre-line">
                  {episode.description}
                </p>
              )}
              <ul className="flex flex-col gap-1.5">
                {episode.shownotes.map((note, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    {episode.status === "ready" ? (
                      <button
                        type="button"
                        onClick={() => seekTo(note.start_seconds)}
                        className="flex items-center gap-1 text-xs font-mono text-indigo-600 dark:text-indigo-400 hover:underline shrink-0 mt-0.5"
                        title={t("podcast.jumpToStory")}
                      >
                        <Bookmark size={11} />
                        {formatDuration(note.start_seconds)}
                      </button>
                    ) : (
                      <span className="text-xs font-mono text-gray-400 shrink-0 mt-0.5">
                        {formatDuration(note.start_seconds)}
                      </span>
                    )}
                    <span className="text-gray-700 dark:text-gray-300 min-w-0">
                      {note.title}
                      <span className="text-gray-400 dark:text-gray-500"> — {note.source_name}</span>
                      {note.url && (
                        <a
                          href={note.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center ml-1 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400"
                          title={t("podcast.openSource")}
                        >
                          <ExternalLink size={11} />
                        </a>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {episode.script && episode.script.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setTranscriptExpanded((v) => !v)}
            className="flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-100"
          >
            {transcriptExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            {t("podcast.transcript")}
          </button>
          {transcriptExpanded && (
            <div className="mt-2 space-y-2 text-sm text-gray-700 dark:text-gray-300 max-h-64 overflow-y-auto pr-2">
              {episode.script.map((turn, i) => (
                <p key={i}>
                  <span className="font-medium">{turn.host_name || turn.host_id}: </span>
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
