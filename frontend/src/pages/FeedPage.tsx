import { useCallback, useMemo, useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useFilterStore } from "../stores/filterStore";
import { useInfiniteNews, useSearchNews } from "../hooks/useNews";
import { useUserTabs } from "../hooks/useTabs";
import FeedTabs from "../components/feed/FeedTabs";
import CategoryFilter from "../components/feed/CategoryFilter";
import SourceFilter from "../components/feed/SourceFilter";
import NewsFeed from "../components/feed/NewsFeed";
import NewsCard from "../components/feed/NewsCard";
import NewsCardSkeleton from "../components/feed/NewsCardSkeleton";
import { Eye, RefreshCw, Search, Tag, X } from "lucide-react";
import { sourcesApi } from "../api/sources";
import { useQueryClient } from "@tanstack/react-query";
import type { FeedEntry } from "../types/news";
import type { ApiTab } from "../api/news";

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export default function FeedPage() {
  const { t } = useTranslation();
  const {
    activeTab, activeCustomTabId,
    setTab, setCustomTab,
    selectedCategoryIds, selectedSourceIds,
    showUnreadOnly, setShowUnreadOnly,
    showUncategorizedOnly, setShowUncategorizedOnly,
  } = useFilterStore();
  const qc = useQueryClient();

  const { data: customTabs } = useUserTabs();

  const [searchInput, setSearchInput] = useState("");
  const searchQuery = useDebounce(searchInput, 300);
  const [isFetching, setIsFetching] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  const isSearching = searchQuery.trim().length > 0;

  const activeCustomTab = activeCustomTabId
    ? customTabs?.find((t) => t.id === activeCustomTabId) ?? null
    : null;

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
    uncategorized: !activeCustomTab && showUncategorizedOnly ? true : undefined,
  });

  const { data: searchResults, isLoading: isSearchLoading } = useSearchNews(searchQuery, {
    sort: effectiveTab,
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
    if (isFetching) return;
    setIsFetching(true);
    qc.invalidateQueries({ queryKey: ["news"] });
    try {
      await sourcesApi.fetchAll();
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: ["news"] });
        setIsFetching(false);
      }, 5000);
    } catch {
      setIsFetching(false);
    }
  };

  const handleRefresh = useCallback(() => {
    qc.invalidateQueries({ queryKey: ["news"] });
  }, [qc]);

  return (
    <div>
      <div className="mb-3">
        <div className="flex items-center justify-between gap-3 mb-2">
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{t("feed.title")}</h1>
          <div className="flex items-center gap-2">
          {!activeCustomTab && (
            <>
              <button
                type="button"
                onClick={() => setShowUnreadOnly(!showUnreadOnly)}
                title={t("feed.unreadOnly")}
                aria-label={t("feed.unreadOnly")}
                className={`p-1.5 rounded transition-colors ${showUnreadOnly ? "text-indigo-500 bg-indigo-50 dark:bg-indigo-900/30" : "text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"}`}
              >
                <Eye size={15} />
              </button>
              <button
                type="button"
                onClick={() => setShowUncategorizedOnly(!showUncategorizedOnly)}
                title={t("feed.uncategorizedOnly")}
                aria-label={t("feed.uncategorizedOnly")}
                className={`p-1.5 rounded transition-colors ${showUncategorizedOnly ? "text-indigo-500 bg-indigo-50 dark:bg-indigo-900/30" : "text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"}`}
              >
                <Tag size={15} />
              </button>
            </>
          )}

          <button
            onClick={handleFetchAll}
            title={t("feed.fetchAll")}
            aria-label={t("feed.fetchAll")}
            disabled={isFetching}
            className="p-1.5 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={15} className={isFetching ? "animate-spin" : ""} />
          </button>

          </div>
        </div>

        {/* Search bar */}
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            ref={searchRef}
            type="search"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder={t("feed.searchPlaceholder")}
            className="w-full pl-9 pr-9 py-2 text-sm rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-gray-400"
          />
          {searchInput && (
            <button
              type="button"
              onClick={() => setSearchInput("")}
              aria-label="Clear search"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-0.5"
            >
              <X size={13} />
            </button>
          )}
        </div>
      </div>

      <FeedTabs
        active={activeTab}
        activeCustomTabId={activeCustomTabId}
        onChange={setTab}
        onCustomTabChange={setCustomTab}
      />

      {!activeCustomTab && (
        <>
          <CategoryFilter />
          <SourceFilter />
        </>
      )}

      {/* Search results */}
      {isSearching ? (
        <div>
          {isSearchLoading ? (
            <div className="flex flex-col gap-4">
              {Array.from({ length: 5 }).map((_, i) => <NewsCardSkeleton key={i} />)}
            </div>
          ) : searchResults && searchResults.length > 0 ? (
            <>
              <p className="text-xs text-gray-400 mb-3">
                {t("feed.searchResults", { count: searchResults.length })}
              </p>
              <div className="flex flex-col gap-4">
                {searchResults.map((item) => (
                  <NewsCard key={item.id} item={item} />
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-400 mt-8 text-center">
              {t("feed.searchNoResults", { query: searchQuery })}
            </p>
          )}
        </div>
      ) : (
        <>
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
        </>
      )}
    </div>
  );
}
