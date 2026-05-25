import { useState } from "react";
import { cn } from "../lib/utils";
import SourcesPanel from "../components/settings/SourcesPanel";
import CategoriesPanel from "../components/settings/CategoriesPanel";
import LLMConfigPanel from "../components/settings/LLMConfigPanel";
import UsersPanel from "../components/settings/UsersPanel";
import { useMe } from "../hooks/useAuth";

const BASE_TABS = [
  { id: "sources", label: "Sources" },
  { id: "categories", label: "Categories" },
  { id: "llm", label: "LLM" },
] as const;

const ADMIN_TAB = { id: "users", label: "Users" } as const;

type BaseTab = (typeof BASE_TABS)[number]["id"];
type Tab = BaseTab | "users";

export default function SettingsPage() {
  const { data: me } = useMe();
  const [activeTab, setActiveTab] = useState<Tab>("sources");

  const tabs = me?.is_admin ? [...BASE_TABS, ADMIN_TAB] : BASE_TABS;

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Settings</h1>

      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6">
        {tabs.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as Tab)}
            className={cn(
              "px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors",
              activeTab === id
                ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        {activeTab === "sources" && <SourcesPanel />}
        {activeTab === "categories" && <CategoriesPanel />}
        {activeTab === "llm" && <LLMConfigPanel />}
        {activeTab === "users" && me?.is_admin && <UsersPanel />}
      </div>
    </div>
  );
}
