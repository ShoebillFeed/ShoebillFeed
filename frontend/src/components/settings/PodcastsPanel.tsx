import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus, Trash2, Pencil, Play, RefreshCw, Rss, Copy, Check } from "lucide-react";
import { Accordion } from "./Accordion";
import { useToast } from "../ui/Toaster";
import {
  usePodcastShows,
  useDeletePodcastShow,
  useGeneratePodcastNow,
  useEnablePublicFeed,
  useDisablePublicFeed,
  useRegeneratePublicFeed,
} from "../../hooks/usePodcasts";
import PodcastShowForm from "./PodcastShowForm";
import type { PodcastShow } from "../../types/podcast";

export default function PodcastsPanel() {
  const { t } = useTranslation();
  const toast = useToast();
  const { data: shows, isLoading } = usePodcastShows();
  const deleteShow = useDeletePodcastShow();
  const generateNow = useGeneratePodcastNow();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<PodcastShow | null>(null);
  const [generatingIds, setGeneratingIds] = useState<Set<string>>(new Set());
  const [feedLinkShowId, setFeedLinkShowId] = useState<string | null>(null);

  const handleGenerateNow = (id: string) => {
    setGeneratingIds((prev) => new Set(prev).add(id));
    generateNow.mutate(id, {
      onSettled: () => setTimeout(() => setGeneratingIds((prev) => { const s = new Set(prev); s.delete(id); return s; }), 5000),
    });
  };

  return (
    <Accordion
      title={t("podcastForm.title")}
      description={t("podcastForm.description")}
      defaultOpen
      action={
        <button
          onClick={() => { setEditing(null); setShowForm(true); }}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
        >
          <Plus size={13} /> {t("podcastForm.addShow")}
        </button>
      }
    >
      {showForm && (
        <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
          <h3 className="font-medium text-sm mb-3">{t("podcastForm.addShow")}</h3>
          <PodcastShowForm onClose={() => setShowForm(false)} />
        </div>
      )}

      {isLoading && <p className="text-sm text-gray-400">{t("common.loading")}</p>}

      <div className="flex flex-col gap-2">
        {shows?.map((show) =>
          editing?.id === show.id ? (
            <div key={show.id} className="p-4 border border-indigo-200 dark:border-indigo-800 rounded-lg bg-gray-50 dark:bg-gray-800/50">
              <h3 className="font-medium text-sm mb-3 text-indigo-600 dark:text-indigo-400">{show.name}</h3>
              <PodcastShowForm show={show} onClose={() => setEditing(null)} />
            </div>
          ) : (
            <div key={show.id} className="flex flex-col gap-2">
              <div className="flex items-center gap-3 p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
                {show.cover_image_url && (
                  <img
                    src={show.cover_image_url}
                    alt=""
                    className="w-10 h-10 rounded-md object-cover border border-gray-200 dark:border-gray-700 shrink-0"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium truncate ${!show.is_active ? "text-gray-400 dark:text-gray-500" : ""}`}>
                      {show.name}
                    </span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">
                      {t("podcastForm.hostCount", { count: show.hosts.length })}
                    </span>
                    {show.public_feed_enabled && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                        {t("podcastForm.feedEnabledBadge")}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {t("podcastForm.summaryLine", {
                      minutes: show.target_length_minutes,
                      time: show.schedule_time,
                      timezone: show.timezone,
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <IconButton
                    title={t("podcastForm.generateNow")}
                    onClick={() => handleGenerateNow(show.id)}
                    disabled={generatingIds.has(show.id)}
                  >
                    {generatingIds.has(show.id) ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                  </IconButton>
                  <IconButton
                    title={t("podcastForm.feedLink")}
                    onClick={() => setFeedLinkShowId(feedLinkShowId === show.id ? null : show.id)}
                    className={feedLinkShowId === show.id ? "text-indigo-600 dark:text-indigo-400" : ""}
                  >
                    <Rss size={14} />
                  </IconButton>
                  <IconButton title={t("common.edit")} onClick={() => { setEditing(show); setShowForm(false); }}>
                    <Pencil size={14} />
                  </IconButton>
                  <IconButton
                    title={t("common.delete")}
                    onClick={() => toast.confirm(t("podcastForm.deleteConfirm", { name: show.name }), () => deleteShow.mutate(show.id))}
                    className="hover:text-red-500"
                  >
                    <Trash2 size={14} />
                  </IconButton>
                </div>
              </div>
              {feedLinkShowId === show.id && <PublicFeedPanel show={show} />}
            </div>
          )
        )}
        {shows?.length === 0 && !isLoading && (
          <p className="text-sm text-gray-400 text-center py-4">{t("podcastForm.empty")}</p>
        )}
      </div>
    </Accordion>
  );
}

function IconButton({
  children,
  title,
  onClick,
  disabled,
  className,
}: {
  children: React.ReactNode;
  title: string;
  onClick: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      title={title}
      onClick={onClick}
      disabled={disabled}
      className={`p-1.5 rounded text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-40 ${className ?? ""}`}
    >
      {children}
    </button>
  );
}

function PublicFeedPanel({ show }: { show: PodcastShow }) {
  const { t } = useTranslation();
  const toast = useToast();
  const enable = useEnablePublicFeed();
  const disable = useDisablePublicFeed();
  const regenerate = useRegeneratePublicFeed();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!show.public_feed_url) return;
    await navigator.clipboard.writeText(show.public_feed_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50 flex flex-col gap-3">
      <div>
        <h4 className="text-sm font-medium">{t("podcastForm.feedLink")}</h4>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{t("podcastForm.feedLinkDesc")}</p>
      </div>

      {show.public_feed_enabled && show.public_feed_url ? (
        <>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-xs font-mono bg-white dark:bg-gray-900 rounded px-2 py-1.5 border border-gray-200 dark:border-gray-700 break-all text-gray-800 dark:text-gray-200">
              {show.public_feed_url}
            </code>
            <button
              type="button"
              onClick={handleCopy}
              className="shrink-0 p-1.5 rounded text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title={t("podcastForm.copyFeedLink")}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => toast.confirm(t("podcastForm.regenerateFeedConfirm"), () => regenerate.mutate(show.id))}
              className="px-3 py-1.5 text-xs font-medium rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {t("podcastForm.regenerateFeedLink")}
            </button>
            <button
              type="button"
              onClick={() => disable.mutate(show.id)}
              disabled={disable.isPending}
              className="px-3 py-1.5 text-xs font-medium rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              {t("podcastForm.disableFeedLink")}
            </button>
          </div>
        </>
      ) : (
        <button
          type="button"
          onClick={() => enable.mutate(show.id)}
          disabled={enable.isPending}
          className="self-start px-3 py-1.5 text-xs font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {t("podcastForm.enableFeedLink")}
        </button>
      )}
      {enable.isError && (
        <p className="text-xs text-red-500">{t("podcastForm.enableFeedError")}</p>
      )}
    </div>
  );
}
