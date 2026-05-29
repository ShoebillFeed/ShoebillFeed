import { useRef, useEffect } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import type { FeedEntry } from "../../types/news";
import NewsCard from "./NewsCard";
import ClusterCard from "./ClusterCard";
import NewsCardSkeleton from "./NewsCardSkeleton";

export default function NewsFeed({
  items,
  isLoading,
  hasMore = false,
  isLoadingMore = false,
  onLoadMore,
}: {
  items: FeedEntry[];
  isLoading: boolean;
  hasMore?: boolean;
  isLoadingMore?: boolean;
  onLoadMore?: () => void;
}) {
  const parentRef = useRef<HTMLDivElement>(null);

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

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <NewsCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-20 text-gray-400 dark:text-gray-600">
        <p className="text-lg font-medium">No articles yet</p>
        <p className="text-sm mt-1">Add sources in Settings to get started</p>
      </div>
    );
  }

  return (
    <div ref={parentRef} className="overflow-auto" style={{ height: "calc(100vh - 200px)" }}>
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
    </div>
  );
}
