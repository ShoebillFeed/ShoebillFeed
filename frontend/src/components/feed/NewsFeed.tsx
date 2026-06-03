import { useRef, useEffect, useState, useCallback } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ArrowDown } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { FeedEntry } from "../../types/news";
import NewsCard from "./NewsCard";
import ClusterCard from "./ClusterCard";
import NewsCardSkeleton from "./NewsCardSkeleton";
import { cn } from "../../lib/utils";

const PULL_THRESHOLD = 80;
const INDICATOR_MAX_H = 48;

export default function NewsFeed({
  items,
  isLoading,
  hasMore = false,
  isLoadingMore = false,
  onLoadMore,
  onRefresh,
}: {
  items: FeedEntry[];
  isLoading: boolean;
  hasMore?: boolean;
  isLoadingMore?: boolean;
  onLoadMore?: () => void;
  onRefresh?: () => void;
}) {
  const { t } = useTranslation();
  const parentRef = useRef<HTMLDivElement>(null);
  const [pullY, setPullY] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const onRefreshRef = useRef(onRefresh);
  onRefreshRef.current = onRefresh;
  const isRefreshingRef = useRef(isRefreshing);
  isRefreshingRef.current = isRefreshing;

  const triggerRefresh = useCallback(() => {
    if (isRefreshingRef.current) return;
    setIsRefreshing(true);
    setPullY(0);
    onRefreshRef.current?.();
    setTimeout(() => setIsRefreshing(false), 900);
  }, []);

  // Attach pull-to-refresh listeners once; parentRef is always mounted.
  useEffect(() => {
    const el = parentRef.current;
    if (!el) return;

    // Use local vars instead of reading React state in event callbacks (avoids stale closures).
    let touchStartY = 0;
    let pulling = false;
    let currentPull = 0;

    const onTouchStart = (e: TouchEvent) => {
      if (el.scrollTop === 0) {
        touchStartY = e.touches[0].clientY;
        pulling = true;
      }
    };

    const onTouchMove = (e: TouchEvent) => {
      if (!pulling) return;
      const dy = e.touches[0].clientY - touchStartY;
      if (dy > 0) {
        currentPull = Math.min(dy * 0.55, PULL_THRESHOLD * 1.4);
        setPullY(currentPull);
        if (dy > 8) e.preventDefault();
      } else {
        pulling = false;
        currentPull = 0;
        setPullY(0);
      }
    };

    const onTouchEnd = () => {
      if (!pulling) return;
      pulling = false;
      if (currentPull >= PULL_THRESHOLD) {
        triggerRefresh();
      } else {
        setPullY(0);
      }
      currentPull = 0;
    };

    let wheelAcc = 0;
    let wheelTimer: ReturnType<typeof setTimeout> | null = null;

    const onWheel = (e: WheelEvent) => {
      if (isRefreshingRef.current) return;
      if (el.scrollTop === 0 && e.deltaY < 0) {
        wheelAcc = Math.min(wheelAcc + -e.deltaY * 0.35, PULL_THRESHOLD * 1.4);
        setPullY(wheelAcc);
        if (wheelTimer) clearTimeout(wheelTimer);
        wheelTimer = setTimeout(() => {
          if (wheelAcc >= PULL_THRESHOLD) {
            triggerRefresh();
          } else {
            setPullY(0);
          }
          wheelAcc = 0;
        }, 160);
      } else if (wheelAcc > 0) {
        wheelAcc = 0;
        setPullY(0);
        if (wheelTimer) clearTimeout(wheelTimer);
      }
    };

    el.addEventListener("touchstart", onTouchStart, { passive: true });
    el.addEventListener("touchmove", onTouchMove, { passive: false });
    el.addEventListener("touchend", onTouchEnd, { passive: true });
    el.addEventListener("wheel", onWheel, { passive: true });

    return () => {
      el.removeEventListener("touchstart", onTouchStart);
      el.removeEventListener("touchmove", onTouchMove);
      el.removeEventListener("touchend", onTouchEnd);
      el.removeEventListener("wheel", onWheel);
      if (wheelTimer) clearTimeout(wheelTimer);
    };
  }, [triggerRefresh]);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 180,
    overscan: 5,
    getItemKey: (index) => items[index].id,
  });

  const virtualItems = virtualizer.getVirtualItems();
  const lastVirtualItem = virtualItems[virtualItems.length - 1];

  useEffect(() => {
    if (!lastVirtualItem || !hasMore || isLoadingMore) return;
    if (lastVirtualItem.index >= items.length - 1) {
      onLoadMore?.();
    }
  }, [lastVirtualItem?.index, items.length, hasMore, isLoadingMore, onLoadMore]);

  const progress = Math.min(pullY / PULL_THRESHOLD, 1);
  const atThreshold = pullY >= PULL_THRESHOLD;
  const indicatorH = isRefreshing
    ? INDICATOR_MAX_H
    : Math.round(progress * INDICATOR_MAX_H);

  return (
    <div className="relative">
      {/* Pull-to-refresh indicator — overlays the top of the feed while pulling */}
      <div
        className="absolute inset-x-0 top-0 z-10 overflow-hidden bg-gray-50/95 dark:bg-gray-950/95 backdrop-blur-sm"
        style={{
          height: indicatorH,
          transition: !isRefreshing && pullY === 0 ? "height 0.2s ease" : undefined,
          borderBottom: indicatorH > 0 ? "1px solid rgba(128,128,128,0.2)" : undefined,
        }}
      >
        <div
          className={cn(
            "h-0.5 transition-colors",
            atThreshold || isRefreshing ? "bg-indigo-500" : "bg-gray-300 dark:bg-gray-700",
          )}
          style={{
            width: isRefreshing ? "100%" : `${progress * 100}%`,
            transition: isRefreshing ? "width 0.4s ease" : undefined,
          }}
        />
        <div
          className={cn(
            "flex items-center justify-center gap-1.5 text-xs font-medium select-none",
            "h-[calc(100%-2px)]",
            atThreshold || isRefreshing
              ? "text-indigo-500 dark:text-indigo-400"
              : "text-gray-400 dark:text-gray-600",
          )}
        >
          {isRefreshing ? (
            <div className="w-3 h-3 border-[1.5px] border-current border-t-transparent rounded-full animate-spin" />
          ) : (
            <ArrowDown
              size={13}
              style={{
                transform: `rotate(${atThreshold ? 180 : progress * 180}deg)`,
                transition: "transform 0.15s",
              }}
            />
          )}
          <span>
            {isRefreshing ? t("newsfeed.refreshing") : atThreshold ? t("newsfeed.releaseToRefresh") : t("newsfeed.pullToRefresh")}
          </span>
        </div>
      </div>

      {/*
        Scroll container is always in the DOM so parentRef stays stable across
        tab switches and loading states. Event listeners never need re-attaching.
      */}
      <div ref={parentRef} className="overflow-auto" style={{ height: "calc(100vh - 200px)" }}>
        {isLoading ? (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <NewsCardSkeleton key={i} />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-600">
            <p className="text-lg font-medium">{t("newsfeed.noArticles")}</p>
            <p className="text-sm mt-1">{t("newsfeed.noArticlesHint")}</p>
          </div>
        ) : (
          <>
            <div
              style={{
                height: `${virtualizer.getTotalSize()}px`,
                width: "100%",
                position: "relative",
              }}
            >
              {virtualizer.getVirtualItems().map((virtualItem) => {
                const entry = items[virtualItem.index];
                return (
                  <div
                    key={virtualItem.key}
                    data-index={virtualItem.index}
                    ref={virtualizer.measureElement}
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      transform: `translateY(${virtualItem.start}px)`,
                      paddingBottom: "12px",
                    }}
                  >
                    {entry.kind === "cluster" ? (
                      <ClusterCard cluster={entry} />
                    ) : (
                      <NewsCard item={entry} />
                    )}
                  </div>
                );
              })}
            </div>
            {isLoadingMore && (
              <div className="flex justify-center py-4">
                <div className="w-5 h-5 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
