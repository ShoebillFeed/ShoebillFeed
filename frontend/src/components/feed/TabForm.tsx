import { useState } from "react";
import { Clock, Zap, TrendingUp } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useCategories } from "../../hooks/useCategories";
import { useSources } from "../../hooks/useSources";
import { cn } from "../../lib/utils";
import { TAB_ICONS, TAB_ICON_NAMES } from "../../lib/tabIcons";
import type { UserTab, UserTabCreate, TabSort, TabIconName } from "../../types/tabs";

const SORT_IDS: { value: TabSort; icon: typeof Clock }[] = [
  { value: "newest", icon: Clock },
  { value: "relevant", icon: Zap },
  { value: "impact", icon: TrendingUp },
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
  const { t } = useTranslation();
  const { data: categories } = useCategories();
  const { data: sources } = useSources();

  const [name, setName] = useState(tab?.name ?? "");
  const [sort, setSort] = useState<TabSort>(tab?.sort ?? "newest");
  const [categoryIds, setCategoryIds] = useState<string[]>(tab?.category_ids ?? []);
  const [sourceIds, setSourceIds] = useState<string[]>(tab?.source_ids ?? []);
  const [unreadOnly, setUnreadOnly] = useState(tab?.unread_only ?? false);
  const [icon, setIcon] = useState<TabIconName | null>(tab?.icon ?? null);

  const toggleId = (list: string[], id: string, set: (v: string[]) => void) => {
    set(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onSave({
      name: name.trim(),
      sort,
      category_ids: categoryIds,
      source_ids: sourceIds,
      unread_only: unreadOnly,
      icon,
    });
  };

  const SORT_LABELS: Record<TabSort, string> = {
    newest: t("tabs.newest"),
    relevant: t("tabs.relevant"),
    impact: t("tabs.impact"),
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {/* Name */}
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
          {t("tabForm.tabName")}
        </label>
        <input
          autoFocus
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t("tabForm.placeholder")}
          className="w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Icon */}
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          {t("tabForm.icon")}
        </label>
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => setIcon(null)}
            title={t("tabForm.noIcon")}
            className={cn(
              "flex items-center justify-center w-8 h-8 rounded-full border text-[10px] font-medium transition-colors",
              icon === null
                ? "bg-indigo-600 text-white border-indigo-600"
                : "bg-white dark:bg-gray-800 text-gray-400 dark:text-gray-500 border-gray-300 dark:border-gray-600 hover:border-indigo-400",
            )}
          >
            {t("tabForm.noIconAbbr")}
          </button>
          {TAB_ICON_NAMES.map((name) => {
            const Icon = TAB_ICONS[name];
            const selected = icon === name;
            return (
              <button
                key={name}
                type="button"
                onClick={() => setIcon(name)}
                title={name}
                className={cn(
                  "flex items-center justify-center w-8 h-8 rounded-full border transition-colors",
                  selected
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:border-indigo-400",
                )}
              >
                <Icon size={14} />
              </button>
            );
          })}
        </div>
      </div>

      {/* Sort */}
      <div>
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
          {t("tabForm.sortBy")}
        </label>
        <div className="flex gap-2">
          {SORT_IDS.map(({ value, icon: Icon }) => (
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
              <Icon size={12} /> {SORT_LABELS[value]}
            </button>
          ))}
        </div>
      </div>

      {/* Category filter */}
      {!!categories?.length && (
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            {t("tabForm.filterCategories")} <span className="font-normal text-gray-400">{t("tabForm.emptyAll")}</span>
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
            {t("tabForm.filterSources")} <span className="font-normal text-gray-400">{t("tabForm.emptyAll")}</span>
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
        {t("tabForm.unreadOnly")}
      </label>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          disabled={!name.trim()}
          className="px-4 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-40 transition-colors"
        >
          {tab ? t("common.save") : t("common.create")}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          {t("common.cancel")}
        </button>
      </div>
    </form>
  );
}
