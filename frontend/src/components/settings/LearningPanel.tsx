import { X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useLearningProfile, useSetCategoryWeight, useDeleteKeyword } from "../../hooks/useLearning";
import { cn } from "../../lib/utils";
import type { CategoryProfile } from "../../api/learning";

const WEIGHT_PRESETS = [
  { label: "learning.muted", value: 0 },
  { label: "learning.normal", value: 1 },
  { label: "learning.boost", value: 2 },
] as const;

export default function LearningPanel() {
  const { t } = useTranslation();
  const { data: profile, isLoading } = useLearningProfile();
  const setCategoryWeight = useSetCategoryWeight();
  const deleteKeyword = useDeleteKeyword();

  if (isLoading) return <p className="text-sm text-gray-400">{t("common.loading")}</p>;
  if (!profile) return null;

  return (
    <div className="flex flex-col gap-8">
      {/* Categories */}
      <section>
        <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">{t("learning.categoriesTitle")}</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{t("learning.categoriesDesc")}</p>
        <div className="flex flex-col gap-2">
          {profile.categories.map((cat) => (
            <CategoryRow
              key={cat.id}
              cat={cat}
              onSetWeight={(w) => setCategoryWeight.mutate({ id: cat.id, weight: w })}
            />
          ))}
          {profile.categories.length === 0 && (
            <p className="text-sm text-gray-400">{t("learning.noCategories")}</p>
          )}
        </div>
      </section>

      {/* Keywords */}
      <section>
        <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">{t("learning.keywordsTitle")}</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{t("learning.keywordsDesc")}</p>
        {profile.keywords.length === 0 ? (
          <p className="text-sm text-gray-400">{t("learning.noKeywords")}</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {profile.keywords.map((kw) => (
              <span
                key={kw.keyword}
                className="inline-flex items-center gap-1.5 pl-2.5 pr-1 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-sm text-gray-700 dark:text-gray-300"
              >
                <span>{kw.keyword}</span>
                <span className="text-xs text-gray-400 dark:text-gray-500 tabular-nums">×{kw.weight.toFixed(1)}</span>
                <button
                  onClick={() => deleteKeyword.mutate(kw.keyword)}
                  title={t("learning.removeKeyword")}
                  className="p-0.5 rounded-full text-gray-400 hover:text-red-500 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                >
                  <X size={11} />
                </button>
              </span>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function CategoryRow({ cat, onSetWeight }: { cat: CategoryProfile; onSetWeight: (w: number) => void }) {
  const { t } = useTranslation();
  const effectiveWeight = cat.learned_weight * cat.manual_weight;
  const barWidth = Math.min(100, ((effectiveWeight - 1) / 3) * 100);

  return (
    <div className="p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="flex items-center gap-3 mb-2">
        <span
          className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
          style={{ backgroundColor: cat.color }}
        />
        <span className="text-sm font-medium flex-1 min-w-0 truncate">{cat.name}</span>
        <span className="text-xs text-gray-400 tabular-nums shrink-0">
          {cat.total_marked} {t("learning.starred")}
        </span>
      </div>

      {/* Weight bar */}
      <div className="mb-2.5 h-1.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{
            width: cat.manual_weight === 0 ? "0%" : `${Math.max(4, barWidth)}%`,
            backgroundColor: cat.color,
            opacity: cat.manual_weight === 0 ? 0.3 : 1,
          }}
        />
      </div>

      {/* Preset buttons */}
      <div className="flex gap-1">
        {WEIGHT_PRESETS.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => onSetWeight(value)}
            className={cn(
              "flex-1 px-2 py-1 text-xs rounded transition-colors",
              cat.manual_weight === value
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
            )}
          >
            {t(label)}
          </button>
        ))}
      </div>
    </div>
  );
}
