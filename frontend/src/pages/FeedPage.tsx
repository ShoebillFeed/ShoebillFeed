import { useFilterStore } from "../stores/filterStore";
import { useNews, useMarkAllRead } from "../hooks/useNews";
import FeedTabs from "../components/feed/FeedTabs";
import CategoryFilter from "../components/feed/CategoryFilter";
import SourceFilter from "../components/feed/SourceFilter";
import NewsFeed from "../components/feed/NewsFeed";
import { CheckCheck, RefreshCw } from "lucide-react";
import { sourcesApi } from "../api/sources";
import { useQueryClient } from "@tanstack/react-query";

export default function FeedPage() {
  const { activeTab, setTab, selectedCategoryIds, selectedSourceIds, showUnreadOnly, setShowUnreadOnly } =
    useFilterStore();
  const qc = useQueryClient();
  const markAllRead = useMarkAllRead();

  const categoryId = selectedCategoryIds.length === 1 ? selectedCategoryIds[0] : undefined;
  const sourceId = selectedSourceIds.length === 1 ? selectedSourceIds[0] : undefined;

  const isReadLater = activeTab === "read_later";
  const { data, isLoading } = useNews({
    tab: isReadLater ? "newest" : activeTab,
    category_id: categoryId,
    source_id: sourceId,
    is_read: showUnreadOnly ? false : undefined,
    read_later: isReadLater ? true : undefined,
  });

  const handleFetchAll = async () => {
    await sourcesApi.fetchAll();
    setTimeout(() => qc.invalidateQueries({ queryKey: ["news"] }), 2000);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">News Feed</h1>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={(e) => setShowUnreadOnly(e.target.checked)}
              className="rounded"
            />
            Unread only
          </label>

          <button
            onClick={handleFetchAll}
            title="Fetch all sources now"
            className="p-1.5 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <RefreshCw size={15} />
          </button>
          <button
            onClick={() => markAllRead.mutate(categoryId)}
            title="Mark all as read"
            className="p-1.5 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <CheckCheck size={15} />
          </button>
        </div>
      </div>

      <FeedTabs active={activeTab} onChange={setTab} />
      <CategoryFilter />
      <SourceFilter />

      {data && (
        <p className="text-xs text-gray-400 mb-3">
          {data.total} articles
        </p>
      )}

      <NewsFeed items={data?.items ?? []} isLoading={isLoading} />
    </div>
  );
}
