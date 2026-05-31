import { useState } from "react";
import { Clock, Zap, TrendingUp } from "lucide-react";
import { useCategories } from "../../hooks/useCategories";
import { useSources } from "../../hooks/useSources";
import { cn } from "../../lib/utils";
import type { UserTab, UserTabCreate, TabSort } from "../../types/tabs";

const SORT_OPTIONS: { value: TabSort; label: string; icon: typeof Clock }[] = [
  { value: "newest", label: "Newest", icon: Clock },
  { value: "relevant", label: "Most Relevant", icon: Zap },
  { value: "impact", label: "Most Impact", icon: TrendingUp },
];

export default function TabForm({
  tab,
  onSave,
  onCancel,
}: {
  tab?: UserTab;
  onSave: (data: UserTabCreate) => void;
  onCancel: () => void;
}) {
  const { data: categories } = useCategories();
  const { data: sources } = useSources();

  const [name, setName] = useState(tab?.name ?? "");
  const [sort, setSort] = useState<TabSort>(tab?.sort ?? "newest");
  const [categoryIds, setCategoryIds] = useState<string[]>(tab?.category_ids ?? []);
  const [sourceIds, setSourceIds] = useState<string[]>(tab?.source_ids ?? []);
  const [unreadOnly, setUnreadOnly] = useState(tab?.unread_only ?? false);

  const toggleId = (list: string[], id: string, set: (v: string[]) => void) => {
    set(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onSave({ name: name.trim(), sort, category_ids: categoryIds, source_ids: sourceIds, unread_only: unreadOnly });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {/* Name */}
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
          Tab name
        </label>
        <input
          autoFocus
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My custom tab"
          className="w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Sort */}
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
          Sort by
        </label>
        <div className="flex gap-2">
          {SORT_OPTIONS.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              type="button"
              onClick={() => setSort(value)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium border transition-colors",
                sort === value
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:border-indigo-400",
              )}
            >
              <Icon size={12} /> {label}
            </button>
          ))}
        </div>
      </div>

      {/* Category filter */}
      {!!categories?.length && (
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Filter by categories <span className="font-normal text-gray-400">(empty = all)</span>
          </label>
          <div className="flex flex-wrap gap-1.5">
            {categories.map((cat) => {
              const active = categoryIds.includes(cat.id);
              return (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => toggleId(categoryIds, cat.id, setCategoryIds)}
                  style={active ? { backgroundColor: cat.color, borderColor: cat.color } : {}}
                  className={cn(
                    "px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                    active
                      ? "text-white"
                      : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:border-gray-400",
                  )}
                >
                  {cat.name}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Source filter */}
      {!!sources?.filter((s) => s.is_active).length && (
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Filter by sources <span className="font-normal text-gray-400">(empty = all)</span>
          </label>
          <div className="flex flex-wrap gap-1.5">
            {sources.filter((s) => s.is_active).map((source) => {
              const active = sourceIds.includes(source.id);
              return (
                <button
                  key={source.id}
                  type="button"
                  onClick={() => toggleId(sourceIds, source.id, setSourceIds)}
                  className={cn(
                    "px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                    active
                      ? "bg-gray-800 text-white border-gray-800 dark:bg-gray-200 dark:text-gray-900 dark:border-gray-200"
                      : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:border-gray-400",
                  )}
                >
                  {source.name}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Unread only */}
      <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={unreadOnly}
          onChange={(e) => setUnreadOnly(e.target.checked)}
          className="rounded accent-indigo-600"
        />
        Show unread articles only
      </label>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          disabled={!name.trim()}
          className="px-4 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-40 transition-colors"
        >
          {tab ? "Save" : "Create"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
