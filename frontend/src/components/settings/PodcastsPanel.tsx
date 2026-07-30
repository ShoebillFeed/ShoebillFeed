import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus, Trash2, Pencil, Play, RefreshCw } from "lucide-react";
import { Accordion } from "./Accordion";
import { useToast } from "../ui/Toaster";
import {
  usePodcastShows,
  useDeletePodcastShow,
  useGeneratePodcastNow,
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
            <div
              key={show.id}
              className="flex items-center gap-3 p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium truncate ${!show.is_active ? "text-gray-400 dark:text-gray-500" : ""}`}>
                    {show.name}
                  </span>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">
                    {t("podcastForm.hostCount", { count: show.hosts.length })}
                  </span>
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
