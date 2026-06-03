import { useState } from "react";
import { Zap, TrendingUp, Clock, Bookmark, Plus, Pencil, Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "../../lib/utils";
import type { FeedTab } from "../../types/news";
import type { UserTab, UserTabCreate } from "../../types/tabs";
import { useUserTabs, useCreateTab, useUpdateTab, useDeleteTab } from "../../hooks/useTabs";
import TabForm from "./TabForm";

type FormMode = { kind: "create" } | { kind: "edit"; tab: UserTab } | null;

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
}: {
  active: FeedTab;
  activeCustomTabId: string | null;
  onChange: (tab: FeedTab) => void;
  onCustomTabChange: (id: string | null) => void;
}) {
  const { t } = useTranslation();
  const { data: customTabs } = useUserTabs();
  const createTab = useCreateTab();
  const updateTab = useUpdateTab();
  const deleteTab = useDeleteTab();
  const [form, setForm] = useState<FormMode>(null);

  const TAB_LABELS: Record<FeedTab, string> = {
    newest: t("tabs.newest"),
    relevant: t("tabs.relevant"),
    impact: t("tabs.impact"),
    read_later: t("tabs.readLater"),
  };

  const handleSave = (data: UserTabCreate) => {
    if (form?.kind === "edit") {
      updateTab.mutate({ id: form.tab.id, data });
    } else {
      createTab.mutate(data, {
        onSuccess: (newTab) => onCustomTabChange(newTab.id),
      });
    }
    setForm(null);
  };

  const handleDelete = (tab: UserTab) => {
    if (!confirm(t("tabs.deleteConfirm", { name: tab.name }))) return;
    if (activeCustomTabId === tab.id) onCustomTabChange(null);
    deleteTab.mutate(tab.id);
    if (form?.kind === "edit" && form.tab.id === tab.id) setForm(null);
  };

  return (
    <div className="mb-4">
      <div className="flex items-end gap-0 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
        {/* Built-in tabs */}
        {BUILT_IN_TAB_IDS.map(({ id, icon: Icon }) => (
          <button
            key={id}
            onClick={() => { onChange(id); setForm(null); }}
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
          return (
            <div key={tab.id} className="flex items-center shrink-0">
              <button
                onClick={() => { onCustomTabChange(tab.id); setForm(null); }}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap",
                  isActive
                    ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                    : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
                )}
              >
                {tab.name}
              </button>
              <div className={cn(
                "flex items-center gap-0.5 pb-px -ml-1 transition-opacity",
                isActive ? "opacity-100" : "opacity-0 group-hover:opacity-100",
              )}>
                <button
                  onClick={(e) => { e.stopPropagation(); setForm({ kind: "edit", tab }); }}
                  title={t("tabs.editTab")}
                  className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  <Pencil size={11} />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(tab); }}
                  title={t("tabs.deleteTab")}
                  className="p-1 rounded text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 size={11} />
                </button>
              </div>
            </div>
          );
        })}

        {/* Add tab button */}
        <button
          onClick={() => setForm(form?.kind === "create" ? null : { kind: "create" })}
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

      {/* Inline create/edit form */}
      {form && (
        <div className="mt-3 p-4 border border-indigo-200 dark:border-indigo-800 rounded-lg bg-gray-50 dark:bg-gray-800/50">
          <h3 className="text-sm font-medium text-indigo-600 dark:text-indigo-400 mb-3">
            {form.kind === "edit" ? t("tabs.editing", { name: form.tab.name }) : t("tabs.newTab")}
          </h3>
          <TabForm
            tab={form.kind === "edit" ? form.tab : undefined}
            onSave={handleSave}
            onCancel={() => setForm(null)}
          />
        </div>
      )}
    </div>
  );
}
