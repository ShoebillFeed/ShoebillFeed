import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";
import { useChangePassword } from "../../hooks/useAuth";
import { usePreferencesStore } from "../../stores/preferencesStore";

// Shared language set — UI translations and content output stay in sync.
// Arabic is content-only (RTL layout not yet supported in the UI).
const SHARED_LANGUAGES = [
  { code: "en", label: "English",    native: "English" },
  { code: "de", label: "German",     native: "Deutsch" },
  { code: "fr", label: "French",     native: "Français" },
  { code: "es", label: "Spanish",    native: "Español" },
  { code: "it", label: "Italian",    native: "Italiano" },
  { code: "nl", label: "Dutch",      native: "Nederlands" },
  { code: "pl", label: "Polish",     native: "Polski" },
  { code: "pt", label: "Portuguese", native: "Português" },
  { code: "ro", label: "Romanian",   native: "Română" },
  { code: "ru", label: "Russian",    native: "Русский" },
  { code: "uk", label: "Ukrainian",  native: "Українська" },
  { code: "zh", label: "Chinese",    native: "中文" },
  { code: "ja", label: "Japanese",   native: "日本語" },
  { code: "ko", label: "Korean",     native: "한국어" },
  { code: "tr", label: "Turkish",    native: "Türkçe" },
  { code: "sv", label: "Swedish",    native: "Svenska" },
  { code: "da", label: "Danish",     native: "Dansk" },
  { code: "nb", label: "Norwegian",  native: "Norsk" },
  { code: "fi", label: "Finnish",    native: "Suomi" },
  { code: "cs", label: "Czech",      native: "Čeština" },
  { code: "hu", label: "Hungarian",  native: "Magyar" },
];

const CONTENT_LANGUAGES = [
  ...SHARED_LANGUAGES,
  { code: "ar", label: "Arabic", native: "العربية" }, // content-only, RTL UI not yet supported
];

const UI_LANGUAGES = SHARED_LANGUAGES;

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

function ChangePasswordSection() {
  const { t } = useTranslation();
  const changePassword = useChangePassword();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (next !== confirm) { setError(t("advanced.passwordMismatch")); return; }
    try {
      await changePassword.mutateAsync({ current_password: current, new_password: next });
      setCurrent(""); setNext(""); setConfirm("");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? t("advanced.passwordChangeFailed"));
    }
  };

  return (
    <Section title={t("advanced.security")}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 max-w-sm">
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-800 dark:text-gray-200">{t("advanced.currentPassword")}</label>
          <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required className={pwInputClass} placeholder="••••••" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-800 dark:text-gray-200">{t("advanced.newPassword")}</label>
          <input type="password" value={next} onChange={(e) => setNext(e.target.value)} required minLength={6} className={pwInputClass} placeholder={t("users.passwordPlaceholder")} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-800 dark:text-gray-200">{t("advanced.confirmPassword")}</label>
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={6} className={pwInputClass} placeholder={t("users.passwordPlaceholder")} />
        </div>
        {error && <p className="text-xs text-red-500">{error}</p>}
        {changePassword.isSuccess && <p className="text-xs text-green-600 dark:text-green-400">{t("advanced.passwordChanged")}</p>}
        <button
          type="submit"
          disabled={changePassword.isPending}
          className="self-start px-4 py-2 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {changePassword.isPending ? "…" : t("advanced.changePassword")}
        </button>
      </form>
    </Section>
  );
}

const pwInputClass =
  "w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";

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
                {l.native}
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
        <NumericField
          label={t("advanced.learningWindow")}
          description={t("advanced.learningWindowDesc")}
          value={settings.learning_window_days ?? 90}
          min={0}
          max={3650}
          step={1}
          onChange={(v) => update.mutate({ learning_window_days: v })}
        />
        <NumericField
          label={t("advanced.ignorePenalty")}
          description={t("advanced.ignorePenaltyDesc")}
          value={settings.ignore_penalty_weight ?? 0.1}
          min={0}
          max={5}
          step={0.05}
          onChange={(v) => update.mutate({ ignore_penalty_weight: v })}
        />
        <NumericField
          label={t("advanced.weightDecayDays")}
          description={t("advanced.weightDecayDaysDesc")}
          value={settings.weight_decay_days ?? 60}
          min={0}
          max={3650}
          step={1}
          onChange={(v) => update.mutate({ weight_decay_days: v })}
        />
      </Section>

      <Section
        title={t("advanced.feedDiversity")}
        description={t("advanced.feedDiversityDesc")}
      >
        <NumericField
          label={t("advanced.maxPerCategory")}
          description={t("advanced.maxPerCategoryDesc")}
          value={settings.max_per_category ?? 8}
          min={0}
          max={50}
          step={1}
          onChange={(v) => update.mutate({ max_per_category: v })}
        />
        <NumericField
          label={t("advanced.maxPerSource")}
          description={t("advanced.maxPerSourceDesc")}
          value={settings.max_per_source ?? 5}
          min={0}
          max={50}
          step={1}
          onChange={(v) => update.mutate({ max_per_source: v })}
        />
        <NumericField
          label={t("advanced.explorationFraction")}
          description={t("advanced.explorationFractionDesc")}
          value={settings.exploration_fraction ?? 0.05}
          min={0}
          max={0.5}
          step={0.05}
          onChange={(v) => update.mutate({ exploration_fraction: v })}
        />
      </Section>

      <Section
        title={t("advanced.relevantTabRanking")}
        description={t("advanced.relevantTabRankingDesc")}
      >
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
        <NumericField
          label={t("advanced.showDecayRate")}
          description={t("advanced.showDecayRateDesc", {
            ex1:  (1 / (1 + 1  * (settings.show_decay_param ?? 0))).toFixed(2),
            ex3:  (1 / (1 + 3  * (settings.show_decay_param ?? 0))).toFixed(2),
            ex10: (1 / (1 + 10 * (settings.show_decay_param ?? 0))).toFixed(2),
          })}
          value={settings.show_decay_param ?? 0}
          min={0}
          max={10}
          step={0.1}
          onChange={(v) => update.mutate({ show_decay_param: v })}
        />
        <NumericField
          label={t("advanced.markShownDelay")}
          description={t("advanced.markShownDelayDesc")}
          value={settings.mark_shown_delay_seconds ?? 5}
          min={1}
          max={60}
          step={1}
          onChange={(v) => update.mutate({ mark_shown_delay_seconds: v })}
        />
      </Section>

      {update.isSuccess && (
        <p className="text-xs text-green-600 dark:text-green-400 mt-2">{t("advanced.settingsSaved")}</p>
      )}
      {update.isError && (
        <p className="text-xs text-red-500 mt-2">{t("advanced.settingsFailed")}</p>
      )}

      <ChangePasswordSection />
    </div>
  );
}
