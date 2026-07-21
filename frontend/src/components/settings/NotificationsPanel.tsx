import { useState, useEffect } from "react";
import { BellOff, Check, AlertTriangle } from "lucide-react";
import { Accordion } from "./Accordion";
import { useTranslation } from "react-i18next";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";
import { useUserTabs } from "../../hooks/useTabs";
import { useCategories } from "../../hooks/useCategories";
import { useSources } from "../../hooks/useSources";
import {
  useVapidPublicKey,
  usePushDryRun,
  subscribeToPush,
  getExistingSubscription,
  useSavePushSubscription,
  useDeletePushSubscription,
} from "../../hooks/usePush";
import { Section, Field, Toggle, ScoreSlider } from "./SettingsControls";
import { cn } from "../../lib/utils";

const TOP_CATEGORY_PERCENT_OPTIONS = [100, 75, 50, 25, 10, 5];
const DRY_RUN_DAYS = 7;

export default function NotificationsPanel() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useAdvancedSettings();
  const updateSettings = useUpdateAdvancedSettings();
  const { data: vapid } = useVapidPublicKey();
  const { data: userTabs = [] } = useUserTabs();
  const { data: categories = [] } = useCategories();
  const { data: sources = [] } = useSources();
  const saveSub = useSavePushSubscription();
  const deleteSub = useDeletePushSubscription();
  const { data: dryRun } = usePushDryRun(!!settings?.push_enabled, DRY_RUN_DAYS);

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
    { id: "relevant", label: t("tabs.relevant"), scoreType: "relevance" as const },
    { id: "impact", label: t("tabs.impact"), scoreType: "impact" as const },
  ];
  const customTabs = userTabs.filter((tab) => tab.sort !== "newest");
  const allSelectableTabs = [
    ...builtinTabs,
    ...customTabs.map((tab) => ({
      id: tab.id,
      label: tab.name,
      scoreType: (tab.sort === "impact" ? "impact" : "relevance") as "relevance" | "impact",
    })),
  ];
  const selectedTabIds = Array.isArray(settings.push_tab_ids) ? settings.push_tab_ids : [];
  const selectedCategoryIds = Array.isArray(settings.push_category_ids) ? settings.push_category_ids : [];
  const selectedSourceIds = Array.isArray(settings.push_source_ids) ? settings.push_source_ids : [];

  // ── Plain-language summary of what the settings below actually combine to ──
  const categoriesPart = settings.push_all_categories
    ? t("notifications.summaryAllCategories")
    : categories.filter((c) => selectedCategoryIds.includes(c.id)).map((c) => c.name).join(", ");
  const sourcesPart = settings.push_all_sources
    ? t("notifications.summaryAllSources")
    : sources.filter((s) => selectedSourceIds.includes(s.id)).map((s) => s.name).join(", ");
  const tabsPart = settings.push_all_tabs
    ? t("notifications.summaryAnyTab")
    : allSelectableTabs.filter((tab) => selectedTabIds.includes(tab.id)).map((tab) => tab.label).join(", ");

  const summaryText = t("notifications.summary", {
    categories: categoriesPart || t("notifications.summaryNothingSelected"),
    sources: sourcesPart || t("notifications.summaryNothingSelected"),
    score: settings.push_min_relevance,
    tabs: tabsPart || t("notifications.summaryNothingSelected"),
  });

  const noCategoriesSelected = !settings.push_all_categories && selectedCategoryIds.length === 0;
  const noSourcesSelected = !settings.push_all_sources && selectedSourceIds.length === 0;
  const noTabsSelected = !settings.push_all_tabs && selectedTabIds.length === 0;
  const blockedEntirely = noCategoriesSelected || noSourcesSelected || noTabsSelected;

  return (
    <Accordion title={t("notifications.title")} description={t("notifications.enableDesc")} defaultOpen>
      {notConfigured && (
        <div className="mb-4 flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/40 border border-amber-200 dark:border-amber-700 text-amber-800 dark:text-amber-300 text-sm">
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
          <div
            className={cn(
              "mb-4 p-3 rounded-lg border text-sm",
              blockedEntirely
                ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-700 text-red-700 dark:text-red-400"
                : "bg-indigo-50 dark:bg-indigo-950/40 border-indigo-100 dark:border-indigo-900 text-indigo-900 dark:text-indigo-200"
            )}
          >
            {blockedEntirely ? (
              <p>{t("notifications.summaryBlocked")}</p>
            ) : (
              <p>{summaryText}</p>
            )}
            {settings.push_top_category_percent < 100 && !blockedEntirely && (
              <p className="mt-1">
                {t("notifications.summaryPercentile", { percent: settings.push_top_category_percent })}
              </p>
            )}
            <p className="mt-1.5 text-xs opacity-80">
              {dryRun
                ? t("notifications.dryRunResult", { count: dryRun.count, days: dryRun.days })
                : t("notifications.dryRunLoading")}
            </p>
          </div>

          <Section
            title={t("notifications.minScoreSection")}
            description={t("notifications.minScoreSectionDesc")}
          >
            <Field label={t("notifications.minScore")} stacked>
              <ScoreSlider
                value={settings.push_min_relevance}
                onChange={(v) => save({ push_min_relevance: v })}
              />
            </Field>
          </Section>

          <Section
            title={t("notifications.topCategorySection")}
            description={t("notifications.topCategorySectionDesc")}
          >
            <Field label={t("notifications.topCategoryPercent")} description="">
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
                  const selected = selectedCategoryIds.includes(cat.id);
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
                {noCategoriesSelected && (
                  <p className="text-sm text-red-500 dark:text-red-400 w-full">
                    {t("notifications.summaryNoCategoriesWarning")}
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
                  const selected = selectedSourceIds.includes(source.id);
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
                {noSourcesSelected && (
                  <p className="text-sm text-red-500 dark:text-red-400 w-full">
                    {t("notifications.summaryNoSourcesWarning")}
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
                      <span className={cn("opacity-70", selected ? "text-white" : "text-gray-400 dark:text-gray-500")}>
                        · {tab.scoreType === "impact" ? t("notifications.tabScoreImpact") : t("notifications.tabScoreRelevance")}
                      </span>
                    </button>
                  );
                })}
                {allSelectableTabs.length === 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t("notifications.noTabs")}
                  </p>
                )}
                {noTabsSelected && (
                  <p className="text-sm text-red-500 dark:text-red-400 w-full">
                    {t("notifications.summaryNoTabsWarning")}
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
    </Accordion>
  );
}
