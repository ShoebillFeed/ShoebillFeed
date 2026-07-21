import { Zap, TrendingUp, Clock, Bookmark, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "../../lib/utils";
import { TAB_ICONS } from "../../lib/tabIcons";
import type { FeedTab } from "../../types/news";
import type { UserTab, UserTabCreate } from "../../types/tabs";
import { useUserTabs } from "../../hooks/useTabs";
import TabForm from "./TabForm";

export type FormMode = { kind: "create" } | { kind: "edit"; tab: UserTab } | null;

const BUILT_IN_TAB_IDS: { id: FeedTab; icon: typeof Clock }[] = [
  { id: "newest", icon: Clock },
  { id: "relevant", icon: Zap },
  { id: "impact", icon: TrendingUp },
  { id: "read_later", icon: Bookmark },
];

export default function FeedTabs({
  active,
  activeCustomTabId,
  onChange,
  onCustomTabChange,
  form,
  onFormChange,
  onSave,
}: {
  active: FeedTab;
  activeCustomTabId: string | null;
  onChange: (tab: FeedTab) => void;
  onCustomTabChange: (id: string | null) => void;
  form: FormMode;
  onFormChange: (form: FormMode) => void;
  onSave: (data: UserTabCreate) => void;
}) {
  const { t } = useTranslation();
  const { data: customTabs } = useUserTabs();

  const TAB_LABELS: Record<FeedTab, string> = {
    newest: t("tabs.newest"),
    relevant: t("tabs.relevant"),
    impact: t("tabs.impact"),
    read_later: t("tabs.readLater"),
  };

  return (
    <div className="mb-4">
      <div className="border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-end gap-0 overflow-x-auto scrollbar-none">
        {/* Built-in tabs */}
        {BUILT_IN_TAB_IDS.map(({ id, icon: Icon }) => (
          <button
            key={id}
            onClick={() => { onChange(id); onFormChange(null); }}
            className={cn(
              "flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors shrink-0 whitespace-nowrap",
              active === id && !activeCustomTabId
                ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
            )}
          >
            <Icon size={14} />
            <span className="hidden sm:inline">{TAB_LABELS[id]}</span>
          </button>
        ))}

        {/* Custom tabs */}
        {customTabs?.map((tab) => {
          const isActive = activeCustomTabId === tab.id;
          const TabIcon = tab.icon ? TAB_ICONS[tab.icon] : null;
          return (
            <button
              key={tab.id}
              onClick={() => { onCustomTabChange(tab.id); onFormChange(null); }}
              className={cn(
                "flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors shrink-0 whitespace-nowrap",
                isActive
                  ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
              )}
            >
              {TabIcon && <TabIcon size={14} />}
              {/* Icon-only on mobile -- but only when there's an icon to fall
                  back on; legacy tabs predating this feature may have none. */}
              <span className={TabIcon ? "hidden sm:inline" : ""}>{tab.name}</span>
            </button>
          );
        })}

        {/* Add tab button */}
        <button
          onClick={() => onFormChange(form?.kind === "create" ? null : { kind: "create" })}
          title={t("tabs.createTab")}
          className={cn(
            "flex items-center justify-center w-8 h-9 mb-0 border-b-2 -mb-px transition-colors shrink-0",
            form?.kind === "create"
              ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
              : "border-transparent text-gray-400 hover:text-gray-600 dark:hover:text-gray-300",
          )}
        >
          <Plus size={15} />
        </button>
      </div>
      </div>

      {/* Inline create/edit form */}
      {form && (
        <div className="mt-3 p-4 border border-indigo-200 dark:border-indigo-800 rounded-lg bg-gray-50 dark:bg-gray-800/50">
          <h3 className="text-sm font-medium text-indigo-600 dark:text-indigo-400 mb-3">
            {form.kind === "edit" ? t("tabs.editing", { name: form.tab.name }) : t("tabs.newTab")}
          </h3>
          <TabForm
            tab={form.kind === "edit" ? form.tab : undefined}
            onSave={onSave}
            onCancel={() => onFormChange(null)}
          />
        </div>
      )}
    </div>
  );
}
