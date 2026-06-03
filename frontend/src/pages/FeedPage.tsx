import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useFilterStore } from "../stores/filterStore";
import { useInfiniteNews, useMarkAllRead } from "../hooks/useNews";
import { useUserTabs } from "../hooks/useTabs";
import FeedTabs from "../components/feed/FeedTabs";
import CategoryFilter from "../components/feed/CategoryFilter";
import SourceFilter from "../components/feed/SourceFilter";
import NewsFeed from "../components/feed/NewsFeed";
import { CheckCheck, RefreshCw } from "lucide-react";
import { sourcesApi } from "../api/sources";
import { useQueryClient } from "@tanstack/react-query";
import type { FeedEntry } from "../types/news";
import type { ApiTab } from "../api/news";

export default function FeedPage() {
  const { t } = useTranslation();
  const {
    activeTab, activeCustomTabId,
    setTab, setCustomTab,
    selectedCategoryIds, selectedSourceIds,
    showUnreadOnly, setShowUnreadOnly,
  } = useFilterStore();
  const qc = useQueryClient();
  const markAllRead = useMarkAllRead();
  const { data: customTabs } = useUserTabs();

  const activeCustomTab = activeCustomTabId
    ? customTabs?.find((t) => t.id === activeCustomTabId) ?? null
    : null;

  // When a custom tab is active, its config overrides the manual filters.
  const effectiveTab = (activeCustomTab?.sort ?? (activeTab === "read_later" ? "newest" : activeTab)) as ApiTab;
  const effectiveCategoryIds = activeCustomTab ? activeCustomTab.category_ids : selectedCategoryIds;
  const effectiveSourceIds = activeCustomTab ? activeCustomTab.source_ids : selectedSourceIds;
  const effectiveIsRead = (activeCustomTab ? activeCustomTab.unread_only : showUnreadOnly) ? false : undefined;
  const effectiveReadLater = !activeCustomTab && activeTab === "read_later" ? true : undefined;

  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteNews({
    tab: effectiveTab,
    category_ids: effectiveCategoryIds.length ? effectiveCategoryIds : undefined,
    source_ids: effectiveSourceIds.length ? effectiveSourceIds : undefined,
    is_read: effectiveIsRead,
    read_later: effectiveReadLater,
  });

  const items = useMemo<FeedEntry[]>(
    () => data?.pages.flatMap((p) => p.items) ?? [],
    [data],
  );
  const total = data?.pages[0]?.total ?? 0;

  const handleFetchAll = async () => {
    await sourcesApi.fetchAll();
    setTimeout(() => qc.invalidateQueries({ queryKey: ["news"] }), 2000);
  };

  const handleRefresh = useCallback(() => {
    qc.invalidateQueries({ queryKey: ["news"] });
  }, [qc]);

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{t("feed.title")}</h1>
        <div className="flex items-center gap-2">
          {!activeCustomTab && (
            <label className="flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={showUnreadOnly}
                onChange={(e) => setShowUnreadOnly(e.target.checked)}
                className="rounded"
              />
              {t("feed.unreadOnly")}
            </label>
          )}

          <button
            onClick={handleFetchAll}
            title={t("feed.fetchAll")}
            className="p-1.5 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <RefreshCw size={15} />
          </button>
          <button
            onClick={() => markAllRead.mutate(undefined)}
            title={t("feed.markAllRead")}
            className="p-1.5 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <CheckCheck size={15} />
          </button>
        </div>
      </div>

      <FeedTabs
        active={activeTab}
        activeCustomTabId={activeCustomTabId}
        onChange={setTab}
        onCustomTabChange={setCustomTab}
      />

      {/* Category/source filters only for built-in tabs */}
      {!activeCustomTab && (
        <>
          <CategoryFilter />
          <SourceFilter />
        </>
      )}

      {/* Custom tab filter summary */}
      {activeCustomTab && (
        <div className="flex flex-wrap gap-1.5 mb-3 text-xs text-gray-400 dark:text-gray-500">
          {activeCustomTab.category_ids.length === 0 && activeCustomTab.source_ids.length === 0 && !activeCustomTab.unread_only && (
            <span>{t("feed.allArticles", { sort: activeCustomTab.sort })}</span>
          )}
          {activeCustomTab.category_ids.length > 0 && (
            <span>{t("feed.categoriesCount", { count: activeCustomTab.category_ids.length })}</span>
          )}
          {activeCustomTab.source_ids.length > 0 && (
            <span>{t("feed.sourcesCount", { count: activeCustomTab.source_ids.length })}</span>
          )}
          {activeCustomTab.unread_only && <span>{t("feed.unreadOnlyFilter")}</span>}
        </div>
      )}

      {data && (
        <p className="text-xs text-gray-400 mb-3">
          {t("feed.articleCount", { loaded: items.length, total })}
        </p>
      )}

      <NewsFeed
        items={items}
        isLoading={isLoading}
        hasMore={!!hasNextPage}
        isLoadingMore={isFetchingNextPage}
        onLoadMore={fetchNextPage}
        onRefresh={handleRefresh}
      />
    </div>
  );
}
