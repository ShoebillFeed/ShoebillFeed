import { useState, useEffect } from "react";
import { ThumbsUp, ThumbsDown, Bookmark, Check, ExternalLink, Trash2, ChevronDown, ChevronUp, TrendingUp, Share2, CheckCheck } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useTranslation } from "react-i18next";
import { cn } from "../../lib/utils";
import type { NewsCluster } from "../../types/news";
import {
  useToggleClusterRead,
  useToggleClusterRelevant,
  useToggleClusterReadLater,
  useDeleteCluster,
  useDislikeCluster,
} from "../../hooks/useNews";
import { usePreferencesStore } from "../../stores/preferencesStore";
import { sourceTypeIcon } from "../../lib/sourceTypeIcon";
import { LLMInfoIcon } from "./LLMInfoIcon";

function uniqueSources(items: NewsCluster["items"]) {
  const seen = new Set<string>();
  return items.flatMap((i) => i.source ? (seen.has(i.source.id) ? [] : (seen.add(i.source.id), [i.source])) : []);
}

export default function ClusterCard({ cluster }: { cluster: NewsCluster }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const [localRelevant, setLocalRelevant] = useState(cluster.is_relevant);
  const [copied, setCopied] = useState(false);
  const coverImageUrl = cluster.items.find((i) => i.image_url)?.image_url ?? null;
  const [hasImage, setHasImage] = useState(!!coverImageUrl);
  const toggleRead = useToggleClusterRead();
  const toggleRelevant = useToggleClusterRelevant();
  const toggleReadLater = useToggleClusterReadLater();
  const deleteCluster = useDeleteCluster();
  const dislikeCluster = useDislikeCluster();
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

  const handleShare = async () => {
    const heading = [cluster.title, cluster.unified_abstract].filter(Boolean).join("\n\n");
    const sourceLines = cluster.items
      .map((i) => i.source ? `${i.source.name}: ${i.url}` : i.url)
      .join("\n");
    const text = [heading, sourceLines].filter(Boolean).join("\n\n");
    const firstUrl = cluster.items[0]?.url;
    if (navigator.share) {
      try {
        await navigator.share({ title: cluster.title || "", text, url: firstUrl });
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        }
      }
    } else {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const timeAgo = cluster.published_at
    ? formatDistanceToNow(new Date(cluster.published_at), { addSuffix: true })
    : "";

  return (
    <article
      className={cn(
        "relative rounded-lg border transition-opacity",
        hasImage ? "min-h-48 border-transparent" : "p-4 bg-white dark:bg-gray-900",
        !hasImage && (cluster.is_read
          ? "border-gray-100 dark:border-gray-800"
          : "border-indigo-200 dark:border-indigo-800"),
        cluster.is_read && "opacity-70",
      )}
    >
      {hasImage && (
        <div className="absolute inset-0 overflow-hidden rounded-lg">
          <img
            src={coverImageUrl!}
            alt=""
            className="absolute inset-0 w-full h-full object-cover"
            loading="lazy"
            onError={() => setHasImage(false)}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/55 to-black/15" />
        </div>
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
        <span className={cn("inline-flex items-center gap-1 text-xs shrink-0 mt-0.5", hasImage ? "text-white/60" : "text-gray-400")}>
          {timeAgo}
          {cluster.llm_processed && (
            <LLMInfoIcon
              provider={cluster.llm_provider}
              model={cluster.llm_model}
              fields="Abstract · Keywords · Categories"
              hasImage={hasImage}
            />
          )}
        </span>
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
        <p className="text-xs text-amber-400 italic">{t("cluster.processing")}</p>
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
          {(() => {
            const newCount = cluster.last_read_at
              ? cluster.items.filter((i) => new Date(i.fetched_at) > new Date(cluster.last_read_at!)).length
              : 0;
            return (
              <button
                onClick={() => setExpanded((v) => !v)}
                className={cn(
                  "flex items-center gap-1.5 text-xs transition-colors",
                  hasImage
                    ? "text-white/50 hover:text-white"
                    : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                )}
              >
                {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                {expanded ? t("cluster.hideSources") : t("cluster.showSources")}
                {!expanded && newCount > 0 && (
                  <span className="ml-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400">
                    {t("cluster.newItems", { count: newCount })}
                  </span>
                )}
              </button>
            );
          })()}

          {expanded && (
            <ul className="mt-2 space-y-2">
              {cluster.items.map((item) => {
                const isNew = !!cluster.last_read_at &&
                  new Date(item.fetched_at) > new Date(cluster.last_read_at);
                return (
                  <li key={item.id} className={cn(
                    "border-l-2 pl-3",
                    hasImage ? "border-white/30" : "border-gray-200 dark:border-gray-700"
                  )}>
                    <div className="flex items-start gap-1.5">
                      {isNew && (
                        <span
                          className="mt-1.5 w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0"
                          title="Added since you last read this cluster"
                        />
                      )}
                      <div className="min-w-0">
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group block"
                          onClick={() => !cluster.is_read && markRead()}
                        >
                          <div className="inline-flex items-start gap-1">
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
                          </div>
                          {item.source_summary && (
                            <p className={cn(
                              "inline-flex items-center gap-1 text-xs mt-0.5 leading-relaxed",
                              hasImage ? "text-white/50" : "text-gray-500 dark:text-gray-400"
                            )}>
                              {item.source_summary}
                              <LLMInfoIcon
                                provider={cluster.llm_provider}
                                model={cluster.llm_model}
                                fields="Source summary"
                                hasImage={hasImage}
                              />
                            </p>
                          )}
                        </a>
                      </div>
                    </div>
                  </li>
                );
              })}
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
          title={localRelevant ? t("card.unmarkRelevant") : t("card.markRelevant")}
        >
          <ThumbsUp size={14} fill={localRelevant ? "currentColor" : "none"} />
        </ActionButton>

        <ActionButton
          active={false}
          activeColor="text-red-400"
          inactiveColor={hasImage ? "text-white/50 hover:text-red-400" : "text-gray-400 hover:text-red-500"}
          onClick={() => dislikeCluster.mutate(cluster.id)}
          title={t("card.dislike")}
        >
          <ThumbsDown size={14} />
        </ActionButton>

        <ActionButton
          active={cluster.read_later}
          activeColor="text-indigo-400"
          inactiveColor={hasImage ? "text-white/50 hover:text-white" : undefined}
          onClick={() => toggleReadLater.mutate(cluster.id)}
          title={cluster.read_later ? t("card.removeReadLater") : t("card.readLater")}
        >
          <Bookmark size={14} fill={cluster.read_later ? "currentColor" : "none"} />
        </ActionButton>

        <ActionButton
          active={cluster.is_read}
          activeColor="text-green-400"
          inactiveColor={hasImage ? "text-white/50 hover:text-white" : undefined}
          onClick={markRead}
          title={cluster.is_read ? t("card.markUnread") : t("card.markRead")}
        >
          <Check size={14} />
        </ActionButton>

        <ActionButton
          active={copied}
          activeColor="text-green-400"
          inactiveColor={hasImage ? "text-white/50 hover:text-white" : undefined}
          onClick={handleShare}
          title={copied ? t("card.copied") : t("card.share")}
        >
          {copied ? <CheckCheck size={14} /> : <Share2 size={14} />}
        </ActionButton>

        <div className="flex-1" />

        {cluster.impact_score && (
          <span className={cn(
            "inline-flex items-center gap-0.5 text-xs",
            hasImage ? "text-white/60" : "text-gray-400"
          )} title={t("card.impactScore")}>
            <TrendingUp size={12} /> {cluster.impact_score}/10
          </span>
        )}

        <ActionButton
          active={false}
          activeColor="text-red-400"
          inactiveColor={hasImage ? "text-white/50 hover:text-red-400" : "hover:text-red-400"}
          onClick={() => deleteCluster.mutate(cluster.id)}
          title={t("cluster.delete")}
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

