import { useState } from "react";
import { Plus, Trash2, Play, Pencil, RefreshCw, Download, Upload, Search } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useToast } from "../ui/Toaster";
import { Accordion } from "./Accordion";
import { useSources, useDeleteSource, useFetchSource, useImportSources, useToggleSourceActive, useSharedSources, useAdoptSource } from "../../hooks/useSources";
import { sourcesApi } from "../../api/sources";
import SourceForm from "./SourceForm";
import type { Source } from "../../types/source";
import { formatDistanceToNow } from "date-fns";

function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function SourcesPanel() {
  const { t } = useTranslation();
  const toast = useToast();
  const { data: sourcesRaw, isLoading } = useSources();
  const sources = sourcesRaw ? [...sourcesRaw].sort((a, b) => a.name.localeCompare(b.name)) : sourcesRaw;
  const { data: sharedSources } = useSharedSources();
  const deleteSource = useDeleteSource();
  const fetchSource = useFetchSource();
  const importSources = useImportSources();
  const toggleActive = useToggleSourceActive();
  const adoptSource = useAdoptSource();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Source | null>(null);
  const [sharedSearch, setSharedSearch] = useState("");
  const [fetchingIds, setFetchingIds] = useState<Set<string>>(new Set());

  const handleFetchSource = (id: string) => {
    setFetchingIds((prev) => new Set(prev).add(id));
    fetchSource.mutate(id, {
      onSettled: () => setTimeout(() => setFetchingIds((prev) => { const s = new Set(prev); s.delete(id); return s; }), 5000),
    });
  };

  const handleExport = async () => {
    const data = await sourcesApi.export();
    downloadJson(data, "sources.json");
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target?.result as string);
        importSources.mutate(data);
      } catch {
        alert(t("sources.invalidJson"));
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  return (
    <div>
      <Accordion
        title={t("sources.title")}
        defaultOpen
        action={
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={handleExport}
              title={t("sources.exportTitle")}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
            >
              <Download size={13} /> {t("common.export")}
            </button>
            <label
              title={t("sources.importTitle")}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400 cursor-pointer"
            >
              <Upload size={13} /> {t("common.import")}
              <input type="file" accept=".json" className="hidden" onChange={handleImport} />
            </label>
            <button
              onClick={() => { setEditing(null); setShowForm(true); }}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
            >
              <Plus size={13} /> {t("sources.addSource")}
            </button>
          </div>
        }
      >
        {showForm && (
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
            <h3 className="font-medium text-sm mb-3">{t("sources.addNewSource")}</h3>
            <SourceForm onClose={() => setShowForm(false)} />
          </div>
        )}

        {isLoading && <p className="text-sm text-gray-400">{t("common.loading")}</p>}

        <div className="flex flex-col gap-2">
          {sources?.map((source) => (
            editing?.id === source.id ? (
              <div key={source.id} className="p-4 border border-indigo-200 dark:border-indigo-800 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <h3 className="font-medium text-sm mb-3 text-indigo-600 dark:text-indigo-400">{t("sources.editingSource", { name: source.name })}</h3>
                <SourceForm source={source} onClose={() => setEditing(null)} />
              </div>
            ) : (
              <div
                key={source.id}
                className="flex items-center gap-3 p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleActive.mutate({ id: source.id, is_active: !source.is_active })}
                      title={source.is_active ? t("sources.deactivate") : t("sources.activate")}
                      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                        source.is_active ? "bg-indigo-600" : "bg-gray-300 dark:bg-gray-600"
                      }`}
                    >
                      <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform ${
                        source.is_active ? "translate-x-4" : "translate-x-0"
                      }`} />
                    </button>
                    <span className={`text-sm font-medium truncate ${!source.is_active ? "text-gray-400 dark:text-gray-500" : ""}`}>
                      {source.name}
                    </span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">
                      {source.source_type}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {t("sources.itemCount", { count: source.item_count })} ·{" "}
                    {source.last_fetched_at
                      ? t("sources.fetched", { timeAgo: formatDistanceToNow(new Date(source.last_fetched_at), { addSuffix: true }) })
                      : t("sources.neverFetched")}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <IconButton title={t("sources.fetchNow")} onClick={() => handleFetchSource(source.id)} disabled={fetchingIds.has(source.id)}>
                    {fetchingIds.has(source.id) ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                  </IconButton>
                  <IconButton title={t("common.edit")} onClick={() => { setEditing(source); setShowForm(false); }}>
                    <Pencil size={14} />
                  </IconButton>
                  <IconButton
                    title={t("common.delete")}
                    onClick={() => toast.confirm(t("sources.deleteConfirm", { name: source.name }), () => deleteSource.mutate(source.id))}
                    className="hover:text-red-500"
                  >
                    <Trash2 size={14} />
                  </IconButton>
                </div>
              </div>
            )
          ))}
          {sources?.length === 0 && !isLoading && (
            <p className="text-sm text-gray-400 text-center py-4">{t("sources.empty")}</p>
          )}
        </div>
      </Accordion>

      {sharedSources && sharedSources.length > 0 && (
        <Accordion title={t("sources.sharedTitle")} description={t("sources.sharedDesc")}>
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              type="text"
              placeholder={t("sources.sharedSearch")}
              value={sharedSearch}
              onChange={(e) => setSharedSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div className="flex flex-col gap-1.5 max-h-72 overflow-y-auto pr-1">
            {sharedSources
              .filter((s) => s.name.toLowerCase().includes(sharedSearch.toLowerCase()))
              .map((source) => (
                <div
                  key={source.id}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700"
                >
                  <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 shrink-0">
                    {source.source_type}
                  </span>
                  <span className="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate">{source.name}</span>
                  <span className="text-xs text-gray-400 shrink-0">{source.item_count.toLocaleString()}</span>
                  <button
                    title={t("sources.adoptSource")}
                    onClick={() => adoptSource.mutate({ name: source.name, source_type: source.source_type, config: source.config, is_active: true, fetch_interval: source.fetch_interval })}
                    disabled={adoptSource.isPending}
                    className="p-1 rounded text-indigo-500 hover:text-indigo-700 dark:hover:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition-colors disabled:opacity-40 shrink-0"
                  >
                    <Plus size={14} />
                  </button>
                </div>
              ))}
            {sharedSources.filter((s) => s.name.toLowerCase().includes(sharedSearch.toLowerCase())).length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">{t("sources.sharedNoMatch")}</p>
            )}
          </div>
        </Accordion>
      )}
    </div>
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
