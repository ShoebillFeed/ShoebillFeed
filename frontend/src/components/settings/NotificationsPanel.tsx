import { useState, useEffect } from "react";
import { BellOff, Check, AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "../../lib/utils";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";
import { useCategories } from "../../hooks/useCategories";
import { useSources } from "../../hooks/useSources";
import {
  useVapidPublicKey,
  subscribeToPush,
  getExistingSubscription,
  useSavePushSubscription,
  useDeletePushSubscription,
} from "../../hooks/usePush";

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

function Field({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
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

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
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
        disabled && "opacity-50 cursor-not-allowed",
      )}
    >
      <span className={cn(
        "pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform transition duration-200",
        checked ? "translate-x-5" : "translate-x-0",
      )} />
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
    <div className="flex items-center gap-3 w-48">
      <input
        type="range"
        min={1}
        max={10}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 h-2 appearance-none bg-gray-200 dark:bg-gray-700 rounded-full cursor-pointer accent-indigo-600"
      />
      <span className="text-sm font-medium w-8 text-right text-gray-800 dark:text-gray-200">
        {value}/10
      </span>
    </div>
  );
}

export default function NotificationsPanel() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useAdvancedSettings();
  const updateSettings = useUpdateAdvancedSettings();
  const { data: vapid } = useVapidPublicKey();
  const { data: categories = [] } = useCategories();
  const { data: sources = [] } = useSources();
  const saveSub = useSavePushSubscription();
  const deleteSub = useDeletePushSubscription();

  const [permissionState, setPermissionState] = useState<NotificationPermission | "unsupported">("default");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [saved, setSaved] = useState(false);

  const supported = "Notification" in window && "serviceWorker" in navigator && "PushManager" in window;

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

  const toggleCategory = (id: string) => {
    const current = settings.push_category_ids ?? [];
    const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
    save({ push_category_ids: next });
  };

  const toggleSource = (id: string) => {
    const current = settings.push_source_ids ?? [];
    const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
    save({ push_source_ids: next });
  };

  const notConfigured = vapid && !vapid.configured;

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">
        {t("notifications.title")}
      </h2>

      {notConfigured && (
        <div className="mb-6 flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 text-amber-800 dark:text-amber-300 text-sm">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <span>{t("notifications.vapidNotConfigured")}</span>
        </div>
      )}

      {permissionState === "unsupported" && (
        <div className="mb-6 flex items-start gap-2 p-3 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 text-sm">
          <BellOff size={16} className="mt-0.5 shrink-0" />
          <span>{t("notifications.notSupported")}</span>
        </div>
      )}

      {permissionState === "denied" && (
        <div className="mb-6 flex items-start gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-400 text-sm">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <span>{t("notifications.permissionDenied")}</span>
        </div>
      )}

      <Section title={t("notifications.general")}>
        <Field label={t("notifications.enable")} description={t("notifications.enableDesc")}>
          <Toggle
            checked={settings.push_enabled && isSubscribed}
            onChange={handleTogglePush}
            disabled={toggling || permissionState === "unsupported" || permissionState === "denied" || notConfigured}
          />
        </Field>
      </Section>

      {settings.push_enabled && (
        <>
          <Section title={t("notifications.scoreThreshold")} description={t("notifications.scoreThresholdDesc")}>
            <Field label={t("notifications.minScore")} description={t("notifications.minScoreDesc")}>
              <ScoreSlider
                value={settings.push_min_relevance}
                onChange={(v) => save({ push_min_relevance: v })}
              />
            </Field>
          </Section>

          <Section title={t("notifications.categories")} description={t("notifications.categoriesDesc")}>
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
                      onClick={() => toggleCategory(cat.id)}
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors",
                        selected
                          ? "text-white border-transparent"
                          : "bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-gray-400",
                      )}
                      style={selected ? { backgroundColor: cat.color, borderColor: cat.color } : undefined}
                    >
                      {selected && <Check size={10} />}
                      {cat.name}
                    </button>
                  );
                })}
                {categories.filter((c) => c.is_active).length === 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t("notifications.noCategories")}</p>
                )}
              </div>
            )}
          </Section>

          <Section title={t("notifications.sources")} description={t("notifications.sourcesDesc")}>
            <Field label={t("notifications.allSources")} description="">
              <Toggle
                checked={settings.push_all_sources}
                onChange={(v) => save({ push_all_sources: v })}
              />
            </Field>

            {!settings.push_all_sources && (
              <div className="flex flex-col gap-2 mt-1">
                {sources.filter((s) => s.is_active).map((source) => {
                  const selected = settings.push_source_ids?.includes(source.id) ?? false;
                  return (
                    <label
                      key={source.id}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 rounded-lg border cursor-pointer transition-colors",
                        selected
                          ? "border-indigo-400 bg-indigo-50 dark:bg-indigo-950 dark:border-indigo-600"
                          : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600",
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={() => toggleSource(source.id)}
                        className="sr-only"
                      />
                      <span className={cn(
                        "flex h-4 w-4 shrink-0 rounded border items-center justify-center",
                        selected
                          ? "bg-indigo-600 border-indigo-600"
                          : "border-gray-300 dark:border-gray-600",
                      )}>
                        {selected && <Check size={10} className="text-white" />}
                      </span>
                      <span className="text-sm text-gray-800 dark:text-gray-200">{source.name}</span>
                      <span className="text-xs text-gray-400 dark:text-gray-500 ml-auto">{source.source_type}</span>
                    </label>
                  );
                })}
                {sources.filter((s) => s.is_active).length === 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">{t("notifications.noSources")}</p>
                )}
              </div>
            )}
          </Section>

          <Section title={t("notifications.multiSource")}>
            <Field label={t("notifications.clusterPerSource")} description={t("notifications.clusterPerSourceDesc")}>
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
    </div>
  );
}
