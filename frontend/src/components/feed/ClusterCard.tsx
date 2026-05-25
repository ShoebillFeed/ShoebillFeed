import { useState, useEffect } from "react";
import { Star, Bookmark, Check, ExternalLink, Trash2, ChevronDown, ChevronUp, TrendingUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "../../lib/utils";
import type { NewsCluster } from "../../types/news";
import {
  useToggleClusterRead,
  useToggleClusterRelevant,
  useToggleClusterReadLater,
  useDeleteCluster,
} from "../../hooks/useNews";
import { usePreferencesStore } from "../../stores/preferencesStore";

export default function ClusterCard({ cluster }: { cluster: NewsCluster }) {
  const [expanded, setExpanded] = useState(false);
  const [localRelevant, setLocalRelevant] = useState(cluster.is_relevant);
  const toggleRead = useToggleClusterRead();
  const toggleRelevant = useToggleClusterRelevant();
  const toggleReadLater = useToggleClusterReadLater();
  const deleteCluster = useDeleteCluster();
  const { autoLabelOnRead } = usePreferencesStore();

  useEffect(() => {
    setLocalRelevant(cluster.is_relevant);
  }, [cluster.is_relevant]);

  const markRead = () => {
    const wasUnread = !cluster.is_read;
    toggleRead.mutate(cluster.id);
    if (wasUnread && autoLabelOnRead && !cluster.is_relevant) {
      toggleRelevant.mutate(cluster.id);
      setLocalRelevant(true);
    }
  };

  const handleToggleRelevant = () => {
    toggleRelevant.mutate(cluster.id);
    setLocalRelevant(!localRelevant);
  };

  const timeAgo = cluster.published_at
    ? formatDistanceToNow(new Date(cluster.published_at), { addSuffix: true })
    : "";

  return (
    <article
      className={cn(
        "bg-white dark:bg-gray-900 rounded-lg border p-4 transition-colors",
        cluster.is_read
          ? "border-gray-100 dark:border-gray-800 opacity-70"
          : "border-indigo-200 dark:border-indigo-800"
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap min-w-0">
          <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 shrink-0">
            🗞 {cluster.items.length} sources
          </span>
          {cluster.categories.map((cat) => (
            <span
              key={cat.id}
              className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded text-white shrink-0"
              style={{ backgroundColor: cat.color }}
            >
              {cat.name}
            </span>
          ))}
        </div>
        <span className="text-xs text-gray-400 shrink-0 mt-0.5">{timeAgo}</span>
      </div>

      {/* Unified abstract */}
      {cluster.unified_abstract ? (
        <p className={cn(
          "text-sm leading-relaxed",
          cluster.is_read ? "text-gray-500 dark:text-gray-400" : "text-gray-900 dark:text-gray-100"
        )}>
          {cluster.unified_abstract}
        </p>
      ) : !cluster.llm_processed ? (
        <p className="text-xs text-amber-500 italic">Processing…</p>
      ) : null}

      {cluster.extracted_keywords && cluster.extracted_keywords.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {cluster.extracted_keywords.map((kw) => (
            <span
              key={kw}
              className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
            >
              {kw}
            </span>
          ))}
        </div>
      )}

      {/* Per-source list (expandable) */}
      {cluster.items.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {expanded ? "Hide sources" : "Show sources"}
          </button>

          {expanded && (
            <ul className="mt-2 space-y-2">
              {cluster.items.map((item) => (
                <li key={item.id} className="border-l-2 border-gray-200 dark:border-gray-700 pl-3">
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group inline-flex items-start gap-1"
                    onClick={() => !cluster.is_read && markRead()}
                  >
                    <span className="text-xs font-medium text-gray-800 dark:text-gray-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors leading-snug">
                      {item.source && (
                        <span className="text-gray-400 dark:text-gray-500 mr-1">
                          {sourceTypeIcon(item.source.source_type)} {item.source.name} —
                        </span>
                      )}
                      {item.title}
                    </span>
                    <ExternalLink size={10} className="shrink-0 mt-0.5 opacity-0 group-hover:opacity-60 transition-opacity text-indigo-500" />
                  </a>
                  {item.source_summary && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">
                      {item.source_summary}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-3 flex items-center gap-1">
        <ActionButton
          active={localRelevant}
          activeColor="text-yellow-500"
          onClick={handleToggleRelevant}
          title={localRelevant ? "Unmark relevant" : "Mark relevant"}
        >
          <Star size={14} fill={localRelevant ? "currentColor" : "none"} />
        </ActionButton>

        <ActionButton
          active={cluster.read_later}
          activeColor="text-indigo-500"
          onClick={() => toggleReadLater.mutate(cluster.id)}
          title={cluster.read_later ? "Remove from read later" : "Read later"}
        >
          <Bookmark size={14} fill={cluster.read_later ? "currentColor" : "none"} />
        </ActionButton>

        <ActionButton
          active={cluster.is_read}
          activeColor="text-green-500"
          onClick={markRead}
          title={cluster.is_read ? "Mark unread" : "Mark read"}
        >
          <Check size={14} />
        </ActionButton>

        <div className="flex-1" />

        {cluster.impact_score && (
          <span className="inline-flex items-center gap-0.5 text-xs text-gray-400" title="Impact score">
            <TrendingUp size={12} /> {cluster.impact_score}/10
          </span>
        )}

        <ActionButton
          active={false}
          activeColor="text-red-500"
          onClick={() => deleteCluster.mutate(cluster.id)}
          title="Delete cluster"
          className="hover:text-red-400 ml-1"
        >
          <Trash2 size={14} />
        </ActionButton>
      </div>
    </article>
  );
}

function ActionButton({
  children,
  active,
  activeColor,
  onClick,
  title,
  className,
}: {
  children: React.ReactNode;
  active: boolean;
  activeColor: string;
  onClick: () => void;
  title: string;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={cn(
        "p-1.5 rounded transition-colors",
        active
          ? activeColor
          : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300",
        className
      )}
    >
      {children}
    </button>
  );
}

function sourceTypeIcon(type: string) {
  const icons: Record<string, string> = {
    rss: "📰",
    reddit: "🔴",
    youtube: "▶️",
    email: "✉️",
  };
  return icons[type] ?? "📄";
}
