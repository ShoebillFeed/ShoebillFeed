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
import { sourceTypeIcon } from "../../lib/sourceTypeIcon";

function uniqueSources(items: NewsCluster["items"]) {
  const seen = new Set<string>();
  return items.flatMap((i) => i.source ? (seen.has(i.source.id) ? [] : (seen.add(i.source.id), [i.source])) : []);
}

export default function ClusterCard({ cluster }: { cluster: NewsCluster }) {
  const [expanded, setExpanded] = useState(false);
  const [localRelevant, setLocalRelevant] = useState(cluster.is_relevant);
  const coverImageUrl = cluster.items.find((i) => i.image_url)?.image_url ?? null;
  const [hasImage, setHasImage] = useState(!!coverImageUrl);
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
        "relative rounded-lg border overflow-hidden transition-opacity",
        hasImage ? "min-h-48 border-transparent" : "p-4 bg-white dark:bg-gray-900",
        !hasImage && (cluster.is_read
          ? "border-gray-100 dark:border-gray-800"
          : "border-indigo-200 dark:border-indigo-800"),
        cluster.is_read && "opacity-70",
      )}
    >
      {hasImage && (
        <>
          <img
            src={coverImageUrl!}
            alt=""
            className="absolute inset-0 w-full h-full object-cover"
            loading="lazy"
            onError={() => setHasImage(false)}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/55 to-black/15" />
        </>
      )}

      <div className={cn("relative z-10 flex flex-col h-full", hasImage && "p-4")}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap min-w-0">
          {uniqueSources(cluster.items).map((source) => (
            <span key={source.id} className={cn(
              "inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded shrink-0",
              hasImage
                ? "bg-black/50 text-white backdrop-blur-sm"
                : "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
            )}>
              {sourceTypeIcon(source.source_type)} {source.name}
            </span>
          ))}
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
        <span className={cn("text-xs shrink-0 mt-0.5", hasImage ? "text-white/60" : "text-gray-400")}>{timeAgo}</span>
      </div>

      {/* Title */}
      {cluster.title && (
        <h3 className={cn(
          "text-sm font-semibold leading-snug mb-1",
          hasImage
            ? "text-white"
            : cluster.is_read ? "text-gray-500 dark:text-gray-400" : "text-gray-900 dark:text-gray-100"
        )}>
          {cluster.title}
        </h3>
      )}

      {/* Unified abstract */}
      {cluster.unified_abstract ? (
        <p className={cn(
          "text-sm leading-relaxed",
          hasImage ? "text-white/75" : (cluster.is_read ? "text-gray-500 dark:text-gray-400" : "text-gray-900 dark:text-gray-100")
        )}>
          {cluster.unified_abstract}
        </p>
      ) : !cluster.llm_processed ? (
        <p className="text-xs text-amber-400 italic">Processing…</p>
      ) : null}

      {cluster.extracted_keywords && cluster.extracted_keywords.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {cluster.extracted_keywords.map((kw) => (
            <span
              key={kw}
              className={cn(
                "text-xs px-1.5 py-0.5 rounded",
                hasImage
                  ? "bg-black/30 text-white/70 backdrop-blur-sm"
                  : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
              )}
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
            className={cn(
              "flex items-center gap-1 text-xs transition-colors",
              hasImage
                ? "text-white/50 hover:text-white"
                : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            )}
          >
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {expanded ? "Hide sources" : "Show sources"}
          </button>

          {expanded && (
            <ul className="mt-2 space-y-2">
              {cluster.items.map((item) => (
                <li key={item.id} className={cn(
                  "border-l-2 pl-3",
                  hasImage ? "border-white/30" : "border-gray-200 dark:border-gray-700"
                )}>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group inline-flex items-start gap-1"
                    onClick={() => !cluster.is_read && markRead()}
                  >
                    <span className={cn(
                      "text-xs font-medium transition-colors leading-snug",
                      hasImage
                        ? "text-white/80 group-hover:text-indigo-300"
                        : "text-gray-800 dark:text-gray-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400"
                    )}>
                      {item.source && (
                        <span className={cn(
                          "mr-1",
                          hasImage ? "text-white/40" : "text-gray-400 dark:text-gray-500"
                        )}>
                          {sourceTypeIcon(item.source.source_type)} {item.source.name} —
                        </span>
                      )}
                      {item.title}
                    </span>
                    <ExternalLink size={10} className="shrink-0 mt-0.5 opacity-0 group-hover:opacity-60 transition-opacity text-indigo-400" />
                  </a>
                  {item.source_summary && (
                    <p className={cn(
                      "text-xs mt-0.5 leading-relaxed",
                      hasImage ? "text-white/50" : "text-gray-500 dark:text-gray-400"
                    )}>
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
          activeColor="text-yellow-400"
          inactiveColor={hasImage ? "text-white/50 hover:text-white" : undefined}
          onClick={handleToggleRelevant}
          title={localRelevant ? "Unmark relevant" : "Mark relevant"}
        >
          <Star size={14} fill={localRelevant ? "currentColor" : "none"} />
        </ActionButton>

        <ActionButton
          active={cluster.read_later}
          activeColor="text-indigo-400"
          inactiveColor={hasImage ? "text-white/50 hover:text-white" : undefined}
          onClick={() => toggleReadLater.mutate(cluster.id)}
          title={cluster.read_later ? "Remove from read later" : "Read later"}
        >
          <Bookmark size={14} fill={cluster.read_later ? "currentColor" : "none"} />
        </ActionButton>

        <ActionButton
          active={cluster.is_read}
          activeColor="text-green-400"
          inactiveColor={hasImage ? "text-white/50 hover:text-white" : undefined}
          onClick={markRead}
          title={cluster.is_read ? "Mark unread" : "Mark read"}
        >
          <Check size={14} />
        </ActionButton>

        <div className="flex-1" />

        {cluster.impact_score && (
          <span className={cn(
            "inline-flex items-center gap-0.5 text-xs",
            hasImage ? "text-white/60" : "text-gray-400"
          )} title="Impact score">
            <TrendingUp size={12} /> {cluster.impact_score}/10
          </span>
        )}

        <ActionButton
          active={false}
          activeColor="text-red-400"
          inactiveColor={hasImage ? "text-white/50 hover:text-red-400" : "hover:text-red-400"}
          onClick={() => deleteCluster.mutate(cluster.id)}
          title="Delete cluster"
          className="ml-1"
        >
          <Trash2 size={14} />
        </ActionButton>
      </div>
      </div>
    </article>
  );
}

function ActionButton({
  children,
  active,
  activeColor,
  inactiveColor,
  onClick,
  title,
  className,
}: {
  children: React.ReactNode;
  active: boolean;
  activeColor: string;
  inactiveColor?: string;
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
          : inactiveColor ?? "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300",
        className
      )}
    >
      {children}
    </button>
  );
}

