import { useState, useEffect } from "react";
import { ThumbsUp, ThumbsDown, Bookmark, Check, ExternalLink, Trash2, TrendingUp, Share2, CheckCheck } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useTranslation } from "react-i18next";
import { cn } from "../../lib/utils";
import type { NewsItem } from "../../types/news";
import {
  useToggleRead,
  useToggleRelevant,
  useToggleReadLater,
  useDeleteNewsItem,
  useDislikeItem,
} from "../../hooks/useNews";
import { usePreferencesStore } from "../../stores/preferencesStore";
import { sourceTypeIcon } from "../../lib/sourceTypeIcon";
import { LLMInfoIcon } from "./LLMInfoIcon";

export default function NewsCard({ item }: { item: NewsItem }) {
  const { t } = useTranslation();
  const [hasImage, setHasImage] = useState(!!item.image_url);
  const [localRelevant, setLocalRelevant] = useState(item.is_relevant);
  const [copied, setCopied] = useState(false);
  const toggleRead = useToggleRead();
  const toggleRelevant = useToggleRelevant();
  const toggleReadLater = useToggleReadLater();
  const deleteItem = useDeleteNewsItem();
  const dislikeItem = useDislikeItem();
  const { autoLabelOnRead } = usePreferencesStore();

  useEffect(() => {
    setLocalRelevant(item.is_relevant);
  }, [item.is_relevant]);

  const markRead = () => {
    const wasUnread = !item.is_read;
    toggleRead.mutate(item.id);
    if (wasUnread && autoLabelOnRead && !item.is_relevant) {
      toggleRelevant.mutate(item.id);
      setLocalRelevant(true);
    }
  };

  const handleToggleRelevant = () => {
    toggleRelevant.mutate(item.id);
    setLocalRelevant(!localRelevant);
  };

  const handleShare = async () => {
    const parts = [item.title, item.abstract].filter(Boolean);
    const sourceLine = item.source ? `${item.source.name}: ${item.url}` : item.url;
    const text = [...parts, sourceLine].join("\n\n");
    if (navigator.share) {
      try {
        await navigator.share({ title: item.title, text, url: item.url });
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

  const date = item.published_at || item.fetched_at;
  const timeAgo = formatDistanceToNow(new Date(date), { addSuffix: true });

  return (
    <article
      className={cn(
        "relative rounded-lg border transition-opacity",
        hasImage ? "min-h-48 border-transparent" : "p-4 bg-white dark:bg-gray-900",
        !hasImage && (item.is_read
          ? "border-gray-100 dark:border-gray-800"
          : "border-gray-200 dark:border-gray-700"),
        item.is_read && "opacity-60",
      )}
    >
      {hasImage && (
        <div className="absolute inset-0 overflow-hidden rounded-lg">
          <img
            src={item.image_url!}
            alt=""
            className="absolute inset-0 w-full h-full object-cover"
            loading="lazy"
            onError={() => setHasImage(false)}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/55 to-black/15" />
        </div>
      )}

      <div className={cn("relative z-10 flex flex-col h-full", hasImage && "p-4")}>
        {/* Header row */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2 flex-wrap min-w-0">
            {item.source && (
              <span className={cn(
                "inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded shrink-0",
                hasImage
                  ? "bg-black/50 text-white backdrop-blur-sm"
                  : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300"
              )}>
                {sourceTypeIcon(item.source.source_type)}
                {item.source.name}
              </span>
            )}
            {item.categories.filter((cat, i, arr) => arr.findIndex(c => c.id === cat.id) === i).map((cat) => (
              <span
                key={cat.id}
                className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded text-white shrink-0"
                style={{ backgroundColor: cat.color }}
              >
                {cat.name}
              </span>
            ))}
          </div>
          <span className={cn(
            "inline-flex items-center gap-1 text-xs shrink-0 mt-0.5",
            hasImage ? "text-white/60" : "text-gray-400"
          )}>
            {timeAgo}
            {item.llm_processed && (
              <LLMInfoIcon
                provider={item.llm_provider}
                model={item.llm_model}
                hasImage={hasImage}
              />
            )}
          </span>
        </div>

        {/* Title + abstract */}
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group block"
          onClick={() => !item.is_read && markRead()}
        >
          <div className="inline-flex items-start gap-1">
            <h3 className={cn(
              "text-sm font-semibold leading-snug transition-colors",
              hasImage
                ? "text-white group-hover:text-indigo-300"
                : cn(
                    "group-hover:text-indigo-600 dark:group-hover:text-indigo-400",
                    item.is_read ? "text-gray-500 dark:text-gray-400" : "text-gray-900 dark:text-gray-100"
                  )
            )}>
              {item.title}
            </h3>
            <ExternalLink size={12} className={cn(
              "shrink-0 mt-1 opacity-0 group-hover:opacity-60 transition-opacity",
              hasImage ? "text-white" : "text-indigo-500"
            )} />
          </div>

          {item.abstract && (
            <p className={cn(
              "mt-1.5 text-sm leading-relaxed",
              hasImage ? "text-white/75" : "text-gray-600 dark:text-gray-400"
            )}>
              {item.abstract}
            </p>
          )}
        </a>

        {item.extracted_keywords && item.extracted_keywords.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {item.extracted_keywords.map((kw) => (
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

        {!item.llm_processed && (
          <p className="mt-1.5 text-xs text-amber-400 italic">{t("card.processing")}</p>
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
            onClick={() => dislikeItem.mutate(item.id)}
            title={t("card.dislike")}
          >
            <ThumbsDown size={14} />
          </ActionButton>

          <ActionButton
            active={item.read_later}
            activeColor="text-indigo-400"
            inactiveColor={hasImage ? "text-white/50 hover:text-white" : undefined}
            onClick={() => toggleReadLater.mutate(item.id)}
            title={item.read_later ? t("card.removeReadLater") : t("card.readLater")}
          >
            <Bookmark size={14} fill={item.read_later ? "currentColor" : "none"} />
          </ActionButton>

          <ActionButton
            active={item.is_read}
            activeColor="text-green-400"
            inactiveColor={hasImage ? "text-white/50 hover:text-white" : undefined}
            onClick={markRead}
            title={item.is_read ? t("card.markUnread") : t("card.markRead")}
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

          {item.impact_score && (
            <span className={cn(
              "inline-flex items-center gap-0.5 text-xs",
              hasImage ? "text-white/60" : "text-gray-400"
            )} title={t("card.impactScore")}>
              <TrendingUp size={12} /> {item.impact_score}/10
            </span>
          )}

          <ActionButton
            active={false}
            activeColor="text-red-400"
            inactiveColor={hasImage ? "text-white/50 hover:text-red-400" : "hover:text-red-400"}
            onClick={() => deleteItem.mutate(item.id)}
            title={t("card.delete")}
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

