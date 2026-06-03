import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";
import { usePreferencesStore } from "../../stores/preferencesStore";

const CONTENT_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "de", label: "German" },
  { code: "fr", label: "French" },
  { code: "es", label: "Spanish" },
  { code: "it", label: "Italian" },
  { code: "pt", label: "Portuguese" },
  { code: "nl", label: "Dutch" },
  { code: "pl", label: "Polish" },
  { code: "ru", label: "Russian" },
  { code: "zh", label: "Chinese" },
  { code: "ja", label: "Japanese" },
  { code: "ar", label: "Arabic" },
  { code: "ko", label: "Korean" },
  { code: "tr", label: "Turkish" },
  { code: "sv", label: "Swedish" },
  { code: "da", label: "Danish" },
  { code: "fi", label: "Finnish" },
  { code: "nb", label: "Norwegian" },
  { code: "cs", label: "Czech" },
  { code: "hu", label: "Hungarian" },
  { code: "ro", label: "Romanian" },
];

const UI_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "de", label: "Deutsch" },
];

const inputClass =
  "w-24 px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <div className="mb-3">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
        {description && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>}
      </div>
      <div className="border-t border-gray-200 dark:border-gray-700 pt-4 flex flex-col gap-4">{children}</div>
    </div>
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
        {description && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>}
      </div>
      {children}
    </div>
  );
}

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
    if (!isNaN(n) && n >= min && n <= max) {
      onChange(n);
    } else {
      setLocal(String(value));
    }
  };

  return (
    <Field label={label} description={description}>
      <input
        type="number"
        className={inputClass}
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

export default function AdvancedPanel() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useAdvancedSettings();
  const update = useUpdateAdvancedSettings();
  const { autoLabelOnRead, setAutoLabelOnRead, uiLocale, setUiLocale } = usePreferencesStore();

  if (isLoading) return <p className="text-sm text-gray-400">{t("common.loading")}</p>;
  if (!settings) return null;

  const base = settings.weight_base;
  const mult = settings.weight_log_multiplier;

  return (
    <div>
      <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-6">{t("advanced.title")}</h2>

      <Section title={t("advanced.uiLanguage")} description={t("advanced.uiLanguageDesc")}>
        <Field label={t("advanced.uiLanguage")}>
          <select
            value={uiLocale ?? ""}
            onChange={(e) => setUiLocale(e.target.value || null)}
            className="px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">{t("advanced.browserDefault")}</option>
            {UI_LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </Field>
      </Section>

      <Section
        title={t("advanced.contentLanguage")}
        description={t("advanced.contentLanguageDesc")}
      >
        <Field
          label={t("advanced.outputLanguage")}
          description={t("advanced.outputLanguageDesc")}
        >
          <select
            value={settings.output_language ?? ""}
            onChange={(e) =>
              update.mutate({ output_language: e.target.value || null })
            }
            className="px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">{t("advanced.keepOriginal")}</option>
            {CONTENT_LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </Field>
      </Section>

      <Section title={t("advanced.reading")}>
        <Field
          label={t("advanced.autoStarOnRead")}
          description={t("advanced.autoStarDesc")}
        >
          <input
            type="checkbox"
            checked={autoLabelOnRead}
            onChange={(e) => setAutoLabelOnRead(e.target.checked)}
            className="mt-1 rounded accent-indigo-600 cursor-pointer"
          />
        </Field>
      </Section>

      <Section
        title={t("advanced.categoryLearning")}
        description={t("advanced.categoryLearningDesc", {
          examples: [1, 5, 10, 25].map((n) => `${n}★ → ${(base + Math.log1p(n) * mult).toFixed(2)}`).join(", "),
        })}
      >
        <NumericField
          label={t("advanced.startingScore")}
          description={t("advanced.startingScoreDesc")}
          value={settings.weight_base}
          min={0}
          max={10}
          step={0.1}
          onChange={(v) => update.mutate({ weight_base: v })}
        />
        <NumericField
          label={t("advanced.learningRate")}
          description={t("advanced.learningRateDesc")}
          value={settings.weight_log_multiplier}
          min={0}
          max={5}
          step={0.05}
          onChange={(v) => update.mutate({ weight_log_multiplier: v })}
        />
      </Section>

      <Section
        title={t("advanced.relevantTabRanking")}
        description={t("advanced.relevantTabRankingDesc")}
      >
        <NumericField
          label={t("advanced.aiRatingInfluence")}
          description={t("advanced.aiRatingDesc")}
          value={settings.relevance_llm_weight}
          min={0}
          max={5}
          step={0.1}
          onChange={(v) => update.mutate({ relevance_llm_weight: v })}
        />
        <NumericField
          label={t("advanced.learningInfluence")}
          description={t("advanced.learningInfluenceDesc")}
          value={settings.relevance_learning_weight}
          min={0}
          max={5}
          step={0.1}
          onChange={(v) => update.mutate({ relevance_learning_weight: v })}
        />
        <NumericField
          label={t("advanced.multiSourceBonus")}
          description={t("advanced.multiSourceBonusDesc")}
          value={settings.relevance_cluster_weight}
          min={0}
          max={5}
          step={0.05}
          onChange={(v) => update.mutate({ relevance_cluster_weight: v })}
        />
        <NumericField
          label={t("advanced.timeDecayRate")}
          description={t("advanced.timeDecayRateDesc", {
            examples: [1, 7, 30].map((d) => `${d}d → ${(1 / (0.5 * (d * (settings.time_decay_param ?? 0.5) + 2))).toFixed(2)}`).join(", "),
          })}
          value={settings.time_decay_param ?? 2.0}
          min={0}
          max={20}
          step={0.1}
          onChange={(v) => update.mutate({ time_decay_param: v })}
        />
      </Section>

      {update.isSuccess && (
        <p className="text-xs text-green-600 dark:text-green-400 mt-2">{t("advanced.settingsSaved")}</p>
      )}
      {update.isError && (
        <p className="text-xs text-red-500 mt-2">{t("advanced.settingsFailed")}</p>
      )}
    </div>
  );
}
