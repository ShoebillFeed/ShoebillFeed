import { useState, useEffect } from "react";
import { X, ChevronDown, ChevronUp, RotateCcw } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useLearningProfile, useSetCategoryWeight, useDeleteKeyword } from "../../hooks/useLearning";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";
import { cn } from "../../lib/utils";
import type { CategoryProfile } from "../../api/learning";

const WEIGHT_PRESETS = [
  { label: "learning.muted", value: 0 },
  { label: "learning.normal", value: 1 },
  { label: "learning.boost", value: 2 },
] as const;

// ─── Shared layout primitives ────────────────────────────────────────────────

function Section({
  title,
  description,
  children,
  action,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <section>
      <div className="flex items-start justify-between mb-1">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
        {action}
      </div>
      {description && (
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{description}</p>
      )}
      {children}
    </section>
  );
}

function Field({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-4">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{label}</p>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}

// ─── PresetSelector ───────────────────────────────────────────────────────────

function PresetSelector({
  presets,
  value,
  onChange,
}: {
  presets: readonly { label: string; value: number }[];
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex gap-1">
      {presets.map(({ label, value: v }) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          className={cn(
            "px-2.5 py-1 text-xs rounded transition-colors whitespace-nowrap",
            value === v
              ? "bg-indigo-600 text-white"
              : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

// ─── NumericField ─────────────────────────────────────────────────────────────

function NumericField({
  label,
  description,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  description?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  const [local, setLocal] = useState(String(value));

  useEffect(() => setLocal(String(value)), [value]);

  const commit = () => {
    const n = parseFloat(local);
    if (!isNaN(n) && n >= min && n <= max) onChange(n);
    else setLocal(String(value));
  };

  return (
    <Field label={label} description={description}>
      <input
        type="number"
        className="w-24 px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        value={local}
        min={min}
        max={max}
        step={step}
        onChange={(e) => setLocal(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => e.key === "Enter" && commit()}
      />
    </Field>
  );
}

// ─── CategoryRow ──────────────────────────────────────────────────────────────

function CategoryRow({
  cat,
  onSetWeight,
}: {
  cat: CategoryProfile;
  onSetWeight: (w: number) => void;
}) {
  const { t } = useTranslation();

  const learnedPct = Math.min(100, Math.max(0, (cat.learned_weight - 1) / 3 * 100));
  const effective = cat.manual_weight === 0 ? 0 : cat.learned_weight * Math.max(1, cat.manual_weight);
  const effectivePct = Math.min(100, Math.max(0, (effective - 1) / 3 * 100));
  const boostPct = cat.manual_weight === 2 ? Math.max(0, effectivePct - learnedPct) : 0;

  let weightLabel: string;
  if (cat.manual_weight === 0) {
    weightLabel = t("learning.muted");
  } else if (cat.manual_weight === 2) {
    weightLabel = `${cat.learned_weight.toFixed(1)}× learned · ${(cat.learned_weight * 2).toFixed(1)}× effective`;
  } else {
    weightLabel = `${cat.learned_weight.toFixed(1)}× learned`;
  }

  return (
    <div
      className={cn(
        "p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900",
        cat.manual_weight === 0 && "opacity-60"
      )}
    >
      {/* Header row */}
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

      {/* Two-layer bar */}
      <div className="mb-1 h-1.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden relative">
        {learnedPct > 0 && (
          <div
            className="absolute left-0 top-0 h-full transition-all duration-300"
            style={{
              width: `${learnedPct}%`,
              backgroundColor: cat.color,
              opacity: cat.manual_weight === 0 ? 0.2 : 0.45,
            }}
          />
        )}
        {boostPct > 0 && (
          <div
            className="absolute top-0 h-full transition-all duration-300"
            style={{
              left: `${learnedPct}%`,
              width: `${boostPct}%`,
              backgroundColor: cat.color,
              opacity: 1,
            }}
          />
        )}
      </div>

      {/* Weight label */}
      <p className="text-xs text-gray-400 dark:text-gray-500 mb-2">{weightLabel}</p>

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

// ─── Main panel ───────────────────────────────────────────────────────────────

export default function LearningPanel() {
  const { t } = useTranslation();
  const { data: profile, isLoading: profileLoading } = useLearningProfile();
  const { data: settings, isLoading: settingsLoading } = useAdvancedSettings();
  const setCategoryWeight = useSetCategoryWeight();
  const deleteKeyword = useDeleteKeyword();
  const update = useUpdateAdvancedSettings();

  const [accordionOpen, setAccordionOpen] = useState(false);

  if (profileLoading || settingsLoading) {
    return <p className="text-sm text-gray-400">{t("common.loading")}</p>;
  }
  if (!profile || !settings) return null;

  // Variety presets
  const varietyPresets = [
    { label: t("learning.varietyLow"), value: 0.05 },
    { label: t("learning.varietyBalanced"), value: 0.10 },
    { label: t("learning.varietyHigh"), value: 0.20 },
  ] as const;

  // Learning speed presets
  const speedPresets = [
    { label: t("learning.slow"), value: 0.15 },
    { label: t("learning.balanced"), value: 0.30 },
    { label: t("learning.fast"), value: 0.50 },
  ] as const;

  // Memory window presets
  const memoryPresets = [
    { label: "30 d", value: 30 },
    { label: "60 d", value: 60 },
    { label: "90 d", value: 90 },
    { label: "6 mo", value: 180 },
    { label: "Never", value: 0 },
  ] as const;

  const score = (n: number) =>
    (settings.weight_base + Math.log1p(n) * settings.weight_log_multiplier).toFixed(2);

  const ex = (d: number) =>
    (1 / (0.5 * (d * settings.time_decay_param + 2))).toFixed(2);

  const r = (n: number) =>
    (1 / (1 + n * settings.show_decay_param)).toFixed(2);

  return (
    <div className="flex flex-col gap-8">
      {/* Section 1: Category Preferences */}
      <Section
        title={t("learning.categoriesTitle")}
        description={t("learning.categoriesDesc")}
      >
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
      </Section>

      {/* Section 2: Learned Keywords */}
      <Section
        title={t("learning.keywordsTitle")}
        description={t("learning.keywordsDesc")}
      >
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
                <span className="text-xs text-gray-400 dark:text-gray-500 tabular-nums">
                  ×{kw.weight.toFixed(1)}
                </span>
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
      </Section>

      {/* Section 3: Feed Behavior */}
      <Section
        title={t("learning.feedBehaviorTitle")}
        description={t("learning.feedBehaviorDesc")}
        action={
          <button
            onClick={() =>
              update.mutate({
                max_per_category: 6,
                max_per_source: 5,
                exploration_fraction: 0.1,
              })
            }
            className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-indigo-600 transition-colors"
          >
            <RotateCcw size={11} />
            {t("learning.resetToDefaults")}
          </button>
        }
      >
        <div className="flex flex-col gap-4">
          <Field
            label={t("learning.varietyLabel")}
            description={t("learning.varietyDesc")}
          >
            <PresetSelector
              presets={varietyPresets}
              value={settings.exploration_fraction}
              onChange={(v) => update.mutate({ exploration_fraction: v })}
            />
          </Field>

          <NumericField
            label={t("learning.maxPerCategory")}
            description={t("learning.maxPerCategoryDesc")}
            value={settings.max_per_category}
            min={0}
            max={50}
            step={1}
            onChange={(v) => update.mutate({ max_per_category: v })}
          />

          <NumericField
            label={t("learning.maxPerSource")}
            description={t("learning.maxPerSourceDesc")}
            value={settings.max_per_source}
            min={0}
            max={50}
            step={1}
            onChange={(v) => update.mutate({ max_per_source: v })}
          />
        </div>

        {update.isSuccess && (
          <p className="text-xs text-green-600 dark:text-green-400 mt-3">
            {t("advanced.settingsSaved")}
          </p>
        )}
        {update.isError && (
          <p className="text-xs text-red-500 mt-3">{t("advanced.settingsFailed")}</p>
        )}
      </Section>

      {/* Section 4: Algorithm Tuning (collapsible) */}
      <section>
        <button
          aria-expanded={accordionOpen}
          onClick={() => setAccordionOpen((o) => !o)}
          className="w-full flex items-center justify-between px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors text-left"
        >
          <div>
            <span className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
              {t("learning.algorithmTitle")}
            </span>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {t("learning.algorithmDesc")}
            </p>
          </div>
          {accordionOpen ? (
            <ChevronUp size={16} className="shrink-0 text-gray-400" />
          ) : (
            <ChevronDown size={16} className="shrink-0 text-gray-400" />
          )}
        </button>

        {accordionOpen && (
          <div className="mt-4 flex flex-col gap-8 px-1">
            {/* Sub-section A: Learning */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 mb-4">
                Learning
              </h3>
              <div className="flex flex-col gap-4">
                <Field
                  label={t("learning.learningSpeed")}
                  description={t("learning.learningSpeedDesc")}
                >
                  <div className="flex flex-col items-end gap-1">
                    <PresetSelector
                      presets={speedPresets}
                      value={settings.weight_log_multiplier}
                      onChange={(v) => update.mutate({ weight_log_multiplier: v })}
                    />
                    <span className="text-xs text-gray-400 tabular-nums">
                      5 likes → {score(5)}× · 20 → {score(20)}× · 100 → {score(100)}×
                    </span>
                  </div>
                </Field>

                <Field
                  label={t("learning.memoryWindow")}
                  description={t("learning.memoryWindowDesc")}
                >
                  <PresetSelector
                    presets={memoryPresets}
                    value={settings.weight_decay_days}
                    onChange={(v) => update.mutate({ weight_decay_days: v })}
                  />
                </Field>

                <NumericField
                  label={t("learning.startingScore")}
                  description={t("learning.startingScoreDesc")}
                  value={settings.weight_base}
                  min={0}
                  max={10}
                  step={0.1}
                  onChange={(v) => update.mutate({ weight_base: v })}
                />

                <NumericField
                  label={t("learning.learningRate")}
                  description={t("learning.learningRateDesc")}
                  value={settings.weight_log_multiplier}
                  min={0}
                  max={5}
                  step={0.05}
                  onChange={(v) => update.mutate({ weight_log_multiplier: v })}
                />

                <NumericField
                  label={t("learning.learningWindow")}
                  description={t("learning.learningWindowDesc")}
                  value={settings.learning_window_days ?? 90}
                  min={0}
                  max={3650}
                  step={1}
                  onChange={(v) => update.mutate({ learning_window_days: v })}
                />

                <NumericField
                  label={t("learning.skipPenalty")}
                  description={t("learning.skipPenaltyDesc")}
                  value={settings.ignore_penalty_weight ?? 0.1}
                  min={0}
                  max={5}
                  step={0.05}
                  onChange={(v) => update.mutate({ ignore_penalty_weight: v })}
                />
              </div>
            </div>

            {/* Sub-section B: Ranking */}
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500 mb-4">
                {t("learning.rankingTitle")}
              </h3>
              <div className="flex flex-col gap-4">
                <NumericField
                  label={t("learning.learningInfluence")}
                  description={t("learning.learningInfluenceDesc")}
                  value={settings.relevance_learning_weight}
                  min={0}
                  max={5}
                  step={0.1}
                  onChange={(v) => update.mutate({ relevance_learning_weight: v })}
                />

                <NumericField
                  label={t("learning.trendingBonus")}
                  description={t("learning.trendingBonusDesc")}
                  value={settings.relevance_cluster_weight}
                  min={0}
                  max={5}
                  step={0.05}
                  onChange={(v) => update.mutate({ relevance_cluster_weight: v })}
                />

                <NumericField
                  label={t("learning.preferRecent")}
                  description={t("learning.preferRecentDesc", {
                    examples: `1d → ${ex(1)}, 7d → ${ex(7)}, 30d → ${ex(30)}`,
                  })}
                  value={settings.time_decay_param ?? 2.0}
                  min={0}
                  max={20}
                  step={0.1}
                  onChange={(v) => update.mutate({ time_decay_param: v })}
                />

                <NumericField
                  label={t("learning.reduceRepeats")}
                  description={t("learning.reduceRepeatsDesc", {
                    ex1: r(1),
                    ex3: r(3),
                    ex10: r(10),
                  })}
                  value={settings.show_decay_param ?? 0}
                  min={0}
                  max={10}
                  step={0.1}
                  onChange={(v) => update.mutate({ show_decay_param: v })}
                />

                <NumericField
                  label={t("learning.markShownDelay")}
                  description={t("learning.markShownDelayDesc")}
                  value={settings.mark_shown_delay_seconds ?? 5}
                  min={1}
                  max={60}
                  step={1}
                  onChange={(v) => update.mutate({ mark_shown_delay_seconds: v })}
                />
              </div>
            </div>

            {/* Accordion reset */}
            <div className="flex justify-end pb-2">
              <button
                onClick={() =>
                  update.mutate({
                    weight_base: 1.0,
                    weight_log_multiplier: 0.5,
                    learning_window_days: 90,
                    ignore_penalty_weight: 0.1,
                    weight_decay_days: 60,
                    relevance_learning_weight: 1.0,
                    relevance_cluster_weight: 0.5,
                    time_decay_param: 2.0,
                    show_decay_param: 0.0,
                    mark_shown_delay_seconds: 5,
                  })
                }
                className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-indigo-600 transition-colors"
              >
                <RotateCcw size={11} />
                {t("learning.resetToDefaults")}
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
