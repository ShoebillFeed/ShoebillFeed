import { useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../lib/utils";
import {
  AnalyseActivityTab,
  AnalyseCategoriesTab,
  AnalyseLearningTab,
  AnalysePodcastTab,
  AnalyseTrendsTab,
  StatsRecordingToggle,
} from "../components/analyse/AnalyseCharts";

type Tab = "activity" | "categories" | "trends" | "learning" | "podcast";

export default function AnalysePage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<Tab>("activity");

  const tabs: { id: Tab; label: string }[] = [
    { id: "activity", label: t("analyse.tabs.activity") },
    { id: "categories", label: t("analyse.tabs.categories") },
    { id: "trends", label: t("analyse.tabs.trends") },
    { id: "learning", label: t("analyse.tabs.learning") },
    { id: "podcast", label: t("analyse.tabs.podcast") },
  ];

  return (
    <div>
      <div className="flex items-center justify-between gap-4 mb-4">
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{t("analyse.title")}</h1>
        <StatsRecordingToggle />
      </div>

      <div className="relative mb-6">
        <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 overflow-x-auto scrollbar-none">
          {tabs.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={cn(
                "px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap shrink-0",
                activeTab === id
                  ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-10 bg-gradient-to-l from-gray-50 dark:from-gray-950 to-transparent" />
      </div>

      {activeTab === "activity" && <AnalyseActivityTab />}
      {activeTab === "categories" && <AnalyseCategoriesTab />}
      {activeTab === "trends" && <AnalyseTrendsTab />}
      {activeTab === "learning" && <AnalyseLearningTab />}
      {activeTab === "podcast" && <AnalysePodcastTab />}
    </div>
  );
}
