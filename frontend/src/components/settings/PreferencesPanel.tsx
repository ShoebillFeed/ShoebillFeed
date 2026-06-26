import { useState, useEffect } from "react";
import { BellOff, Check, AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "../../lib/utils";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";
import { useChangePassword } from "../../hooks/useAuth";
import { usePreferencesStore } from "../../stores/preferencesStore";
import { useUserTabs } from "../../hooks/useTabs";
import { useCategories } from "../../hooks/useCategories";
import { useSources } from "../../hooks/useSources";
import {
  useVapidPublicKey,
  subscribeToPush,
  getExistingSubscription,
  useSavePushSubscription,
  useDeletePushSubscription,
} from "../../hooks/usePush";

// ─── Language arrays ──────────────────────────────────────────────────────────

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
  { code: "ar", label: "Arabic", native: "العربية" },
];

const UI_LANGUAGES = SHARED_LANGUAGES;

// ─── Layout primitives ────────────────────────────────────────────────────────

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-8">
      <div className="mb-3">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
        )}
      </div>
      <div className="border-t border-gray-200 dark:border-gray-700 pt-4 flex flex-col gap-4">
        {children}
      </div>
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
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{label}</p>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}

function Toggle({
  checked,
  onChange,
  disabled,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500",
        checked ? "bg-indigo-600" : "bg-gray-200 dark:bg-gray-700",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <span
        className={cn(
          "pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform transition duration-200",
          checked ? "translate-x-5" : "translate-x-0"
        )}
      />
    </button>
  );
}

function ScoreSlider({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center gap-3 w-full max-w-xs">
      <input
        type="range"
        min={1}
        max={10}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 h-2 appearance-none bg-gray-200 dark:bg-gray-700 rounded-full cursor-pointer accent-indigo-600"
      />
      <span className="text-sm font-medium w-10 text-right shrink-0 text-gray-800 dark:text-gray-200">
        {value}/10
      </span>
    </div>
  );
}

// ─── Change password section ──────────────────────────────────────────────────

const pwInputClass =
  "w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";

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
    if (next !== confirm) {
      setError(t("advanced.passwordMismatch"));
      return;
    }
    try {
      await changePassword.mutateAsync({ current_password: current, new_password: next });
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? t("advanced.passwordChangeFailed"));
    }
  };

  return (
    <Section title={t("advanced.security")}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 max-w-sm">
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-800 dark:text-gray-200">
            {t("advanced.currentPassword")}
          </label>
          <input
            type="password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            required
            className={pwInputClass}
            placeholder="••••••"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-800 dark:text-gray-200">
            {t("advanced.newPassword")}
          </label>
          <input
            type="password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            required
            minLength={6}
            className={pwInputClass}
            placeholder={t("users.passwordPlaceholder")}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-800 dark:text-gray-200">
            {t("advanced.confirmPassword")}
          </label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
            minLength={6}
            className={pwInputClass}
            placeholder={t("users.passwordPlaceholder")}
          />
        </div>
        {error && <p className="text-xs text-red-500">{error}</p>}
        {changePassword.isSuccess && (
          <p className="text-xs text-green-600 dark:text-green-400">
            {t("advanced.passwordChanged")}
          </p>
        )}
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

// ─── Push notifications section ───────────────────────────────────────────────

const TOP_CATEGORY_PERCENT_OPTIONS = [100, 75, 50, 25, 10, 5];

function PushNotificationsSection() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useAdvancedSettings();
  const updateSettings = useUpdateAdvancedSettings();
  const { data: vapid } = useVapidPublicKey();
  const { data: userTabs = [] } = useUserTabs();
  const { data: categories = [] } = useCategories();
  const { data: sources = [] } = useSources();
  const saveSub = useSavePushSubscription();
  const deleteSub = useDeletePushSubscription();

  const [permissionState, setPermissionState] = useState<NotificationPermission | "unsupported">("default");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [saved, setSaved] = useState(false);

  const supported =
    "Notification" in window && "serviceWorker" in navigator && "PushManager" in window;

  useEffect(() => {
    if (!supported) {
      setPermissionState("unsupported");
      return;
    }
    setPermissionState(Notification.permission);
    getExistingSubscription().then((sub) => setIsSubscribed(!!sub));
  }, [supported]);

  if (isLoading || !settings) return null;

  const save = (patch: Parameters<typeof updateSettings.mutate>[0]) => {
    updateSettings.mutate(patch, {
      onSuccess: () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      },
    });
  };

  const handleTogglePush = async (enable: boolean) => {
    if (toggling) return;
    setToggling(true);
    try {
      if (enable) {
        const permission = await Notification.requestPermission();
        setPermissionState(permission);
        if (permission !== "granted") {
          setToggling(false);
          return;
        }
        const sub = await subscribeToPush(vapid!.public_key);
        if (sub) {
          await saveSub.mutateAsync(sub);
          setIsSubscribed(true);
        }
        save({ push_enabled: true });
      } else {
        await deleteSub.mutateAsync();
        setIsSubscribed(false);
        save({ push_enabled: false });
      }
    } catch (err) {
      console.error("Push toggle failed:", err);
    } finally {
      setToggling(false);
    }
  };

  const toggleTabId = (id: string) => {
    const current = Array.isArray(settings.push_tab_ids) ? settings.push_tab_ids : [];
    const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
    save({ push_tab_ids: next });
  };

  const toggleCategory = (id: string) => {
    const current = Array.isArray(settings.push_category_ids) ? settings.push_category_ids : [];
    const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
    save({ push_category_ids: next });
  };

  const toggleSource = (id: string) => {
    const current = Array.isArray(settings.push_source_ids) ? settings.push_source_ids : [];
    const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
    save({ push_source_ids: next });
  };

  const notConfigured = vapid && !vapid.configured;

  const builtinTabs = [
    { id: "relevant", label: t("tabs.relevant") },
    { id: "impact", label: t("tabs.impact") },
  ];
  const customTabs = userTabs.filter((tab) => tab.sort !== "newest");
  const allSelectableTabs = [
    ...builtinTabs,
    ...customTabs.map((tab) => ({ id: tab.id, label: tab.name })),
  ];
  const selectedTabIds = Array.isArray(settings.push_tab_ids) ? settings.push_tab_ids : [];

  return (
    <>
      {notConfigured && (
        <div className="mb-4 flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 text-amber-800 dark:text-amber-300 text-sm">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <span>{t("notifications.vapidNotConfigured")}</span>
        </div>
      )}

      {permissionState === "unsupported" && (
        <div className="mb-4 flex items-start gap-2 p-3 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 text-sm">
          <BellOff size={16} className="mt-0.5 shrink-0" />
          <span>{t("notifications.notSupported")}</span>
        </div>
      )}

      {permissionState === "denied" && (
        <div className="mb-4 flex items-start gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-400 text-sm">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <span>{t("notifications.permissionDenied")}</span>
        </div>
      )}

      <Section title={t("notifications.general")}>
        <Field label={t("notifications.enable")} description={t("notifications.enableDesc")}>
          <Toggle
            checked={settings.push_enabled && isSubscribed}
            onChange={handleTogglePush}
            disabled={
              toggling ||
              permissionState === "unsupported" ||
              permissionState === "denied" ||
              notConfigured
            }
          />
        </Field>
      </Section>

      {settings.push_enabled && (
        <>
          <Section
            title={t("notifications.scoreThreshold")}
            description={t("notifications.scoreThresholdDesc")}
          >
            <Field
              label={t("notifications.minScore")}
              description={t("notifications.minScoreDesc")}
            >
              <ScoreSlider
                value={settings.push_min_relevance}
                onChange={(v) => save({ push_min_relevance: v })}
              />
            </Field>

            <Field
              label={t("notifications.topCategoryPercent")}
              description={t("notifications.topCategoryPercentDesc")}
            >
              <select
                value={settings.push_top_category_percent}
                onChange={(e) => save({ push_top_category_percent: Number(e.target.value) })}
                className="px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {TOP_CATEGORY_PERCENT_OPTIONS.map((p) => (
                  <option key={p} value={p}>
                    {p === 100
                      ? t("notifications.topCategoryPercentAll")
                      : t("notifications.topCategoryPercentOption", { percent: p })}
                  </option>
                ))}
              </select>
            </Field>
          </Section>

          <Section
            title={t("notifications.categories")}
            description={t("notifications.categoriesDesc")}
          >
            <Field label={t("notifications.allCategories")} description="">
              <Toggle
                checked={settings.push_all_categories}
                onChange={(v) => save({ push_all_categories: v })}
              />
            </Field>

            {!settings.push_all_categories && (
              <div className="flex flex-wrap gap-2 mt-1">
                {categories.filter((c) => c.is_active).map((cat) => {
                  const selected = settings.push_category_ids?.includes(cat.id) ?? false;
                  return (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => toggleCategory(cat.id)}
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                        selected
                          ? "text-white border-transparent"
                          : "bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-gray-400"
                      )}
                      style={selected ? { backgroundColor: cat.color, borderColor: cat.color } : undefined}
                    >
                      {selected && <Check size={10} />}
                      {cat.name}
                    </button>
                  );
                })}
                {categories.filter((c) => c.is_active).length === 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t("notifications.noCategories")}
                  </p>
                )}
              </div>
            )}
          </Section>

          <Section
            title={t("notifications.sources")}
            description={t("notifications.sourcesDesc")}
          >
            <Field label={t("notifications.allSources")} description="">
              <Toggle
                checked={settings.push_all_sources}
                onChange={(v) => save({ push_all_sources: v })}
              />
            </Field>

            {!settings.push_all_sources && (
              <div className="flex flex-wrap gap-2 mt-1">
                {sources.filter((s) => s.is_active).map((source) => {
                  const selected = settings.push_source_ids?.includes(source.id) ?? false;
                  return (
                    <button
                      key={source.id}
                      type="button"
                      onClick={() => toggleSource(source.id)}
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                        selected
                          ? "bg-indigo-600 text-white border-transparent"
                          : "bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-gray-400"
                      )}
                    >
                      {selected && <Check size={10} />}
                      {source.name}
                    </button>
                  );
                })}
                {sources.filter((s) => s.is_active).length === 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t("notifications.noSources")}
                  </p>
                )}
              </div>
            )}
          </Section>

          <Section
            title={t("notifications.feedTabs")}
            description={t("notifications.feedTabsDesc")}
          >
            <Field label={t("notifications.allTabs")} description="">
              <Toggle
                checked={settings.push_all_tabs}
                onChange={(v) => save({ push_all_tabs: v })}
              />
            </Field>

            {!settings.push_all_tabs && (
              <div className="flex flex-wrap gap-2 mt-1">
                {allSelectableTabs.map((tab) => {
                  const selected = selectedTabIds.includes(tab.id);
                  return (
                    <button
                      key={tab.id}
                      onClick={() => toggleTabId(tab.id)}
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                        selected
                          ? "bg-indigo-600 text-white border-transparent"
                          : "bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-gray-400"
                      )}
                    >
                      {selected && <Check size={10} />}
                      {tab.label}
                    </button>
                  );
                })}
                {allSelectableTabs.length === 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t("notifications.noTabs")}
                  </p>
                )}
              </div>
            )}
          </Section>

          <Section title={t("notifications.multiSource")}>
            <Field
              label={t("notifications.clusterPerSource")}
              description={t("notifications.clusterPerSourceDesc")}
            >
              <Toggle
                checked={settings.push_cluster_per_source}
                onChange={(v) => save({ push_cluster_per_source: v })}
              />
            </Field>
          </Section>
        </>
      )}

      {saved && (
        <p className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1 mt-2">
          <Check size={14} /> {t("advanced.settingsSaved")}
        </p>
      )}
    </>
  );
}

// ─── Main panel ───────────────────────────────────────────────────────────────

const selectClass =
  "px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";

export default function PreferencesPanel() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useAdvancedSettings();
  const update = useUpdateAdvancedSettings();
  const { uiLocale, setUiLocale } = usePreferencesStore();

  if (isLoading) return <p className="text-sm text-gray-400">{t("common.loading")}</p>;
  if (!settings) return null;

  return (
    <div>
      {/* Section 1: Interface */}
      <Section title={t("preferences.interfaceTitle")}>
        <Field label={t("preferences.uiLanguage")} description={t("preferences.uiLanguageDesc")}>
          <select
            value={uiLocale ?? ""}
            onChange={(e) => setUiLocale(e.target.value || null)}
            className={selectClass}
          >
            <option value="">{t("preferences.browserDefault")}</option>
            {UI_LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.native}
              </option>
            ))}
          </select>
        </Field>
      </Section>

      {/* Section 2: Content */}
      <Section title={t("preferences.contentTitle")}>
        <Field
          label={t("preferences.outputLanguage")}
          description={t("preferences.outputLanguageDesc")}
        >
          <select
            value={settings.output_language ?? ""}
            onChange={(e) => update.mutate({ output_language: e.target.value || null })}
            className={selectClass}
          >
            <option value="">{t("preferences.keepOriginal")}</option>
            {CONTENT_LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </Field>


      </Section>

      {/* Section 3: Push Notifications */}
      <div className="mb-8">
        <div className="mb-3">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">{t("notifications.title")}</h3>
        </div>
        <PushNotificationsSection />
      </div>

      {/* Section 4: Security */}
      <ChangePasswordSection />

      {update.isSuccess && (
        <p className="text-xs text-green-600 dark:text-green-400 mt-2">
          {t("preferences.settingsSaved")}
        </p>
      )}
      {update.isError && (
        <p className="text-xs text-red-500 mt-2">{t("preferences.settingsFailed")}</p>
      )}
    </div>
  );
}
