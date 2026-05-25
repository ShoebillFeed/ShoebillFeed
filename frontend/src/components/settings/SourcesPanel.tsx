import { useState } from "react";
import { Plus, Trash2, Play, Pencil, RefreshCw } from "lucide-react";
import { useSources, useDeleteSource, useFetchSource } from "../../hooks/useSources";
import SourceForm from "./SourceForm";
import type { Source } from "../../types/source";
import { formatDistanceToNow } from "date-fns";

export default function SourcesPanel() {
  const { data: sources, isLoading } = useSources();
  const deleteSource = useDeleteSource();
  const fetchSource = useFetchSource();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Source | null>(null);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100">News Sources</h2>
        <button
          onClick={() => { setEditing(null); setShowForm(true); }}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
        >
          <Plus size={14} /> Add Source
        </button>
      </div>

      {(showForm || editing) && (
        <div className="mb-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
          <h3 className="font-medium text-sm mb-3">{editing ? "Edit Source" : "Add New Source"}</h3>
          <SourceForm
            source={editing ?? undefined}
            onClose={() => { setShowForm(false); setEditing(null); }}
          />
        </div>
      )}

      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}

      <div className="flex flex-col gap-2">
        {sources?.map((source) => (
          <div
            key={source.id}
            className="flex items-center gap-3 p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium truncate">{source.name}</span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">
                  {source.source_type}
                </span>
                {!source.is_active && (
                  <span className="text-xs px-1.5 py-0.5 rounded bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400">
                    inactive
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                {source.item_count} items ·{" "}
                {source.last_fetched_at
                  ? `fetched ${formatDistanceToNow(new Date(source.last_fetched_at), { addSuffix: true })}`
                  : "never fetched"}
              </p>
            </div>

            <div className="flex items-center gap-1">
              <IconButton
                title="Fetch now"
                onClick={() => fetchSource.mutate(source.id)}
                disabled={fetchSource.isPending}
              >
                {fetchSource.isPending ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
              </IconButton>
              <IconButton title="Edit" onClick={() => { setEditing(source); setShowForm(false); }}>
                <Pencil size={14} />
              </IconButton>
              <IconButton
                title="Delete"
                onClick={() => {
                  if (confirm(`Delete source "${source.name}" and all its articles?`)) {
                    deleteSource.mutate(source.id);
                  }
                }}
                className="hover:text-red-500"
              >
                <Trash2 size={14} />
              </IconButton>
            </div>
          </div>
        ))}

        {sources?.length === 0 && !isLoading && (
          <p className="text-sm text-gray-400 text-center py-8">
            No sources yet. Add one to start aggregating news.
          </p>
        )}
      </div>
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
