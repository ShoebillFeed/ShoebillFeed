import { useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../lib/utils";
import SourcesPanel from "../components/settings/SourcesPanel";
import CategoriesPanel from "../components/settings/CategoriesPanel";
import LLMConfigPanel from "../components/settings/LLMConfigPanel";
import UsersPanel from "../components/settings/UsersPanel";
import AdvancedPanel from "../components/settings/AdvancedPanel";
import NotificationsPanel from "../components/settings/NotificationsPanel";
import StatsPanel from "../components/settings/StatsPanel";
import LearningPanel from "../components/settings/LearningPanel";
import AboutPanel from "../components/settings/AboutPanel";
import { useMe } from "../hooks/useAuth";

type BaseTab = "sources" | "categories" | "llm" | "advanced" | "notifications" | "stats" | "learning" | "about";
type Tab = BaseTab | "users";

export default function SettingsPage() {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const [activeTab, setActiveTab] = useState<Tab>("sources");

  const baseTabs: { id: BaseTab; label: string }[] = [
    { id: "sources", label: t("settings.sources") },
    { id: "categories", label: t("settings.categories") },
    { id: "llm", label: t("settings.llm") },
    { id: "advanced", label: t("settings.advanced") },
    { id: "notifications", label: t("settings.notifications") },
    { id: "stats", label: t("settings.statistics") },
    { id: "learning", label: t("settings.learning") },
    { id: "about", label: t("settings.about") },
  ];
  const tabs = me?.is_admin
    ? [...baseTabs, { id: "users" as Tab, label: t("settings.users") }]
    : baseTabs;

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">{t("settings.title")}</h1>

      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6 overflow-x-auto scrollbar-none">
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

      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-6 overflow-x-auto">
        {activeTab === "sources" && <SourcesPanel />}
        {activeTab === "categories" && <CategoriesPanel />}
        {activeTab === "llm" && <LLMConfigPanel />}
        {activeTab === "advanced" && <AdvancedPanel />}
        {activeTab === "notifications" && <NotificationsPanel />}
        {activeTab === "stats" && <StatsPanel />}
        {activeTab === "learning" && <LearningPanel />}
        {activeTab === "about" && <AboutPanel />}
        {activeTab === "users" && me?.is_admin && <UsersPanel />}
      </div>
    </div>
  );
}
