import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Loader } from "lucide-react";
import { useTranslation } from "react-i18next";
import client from "../../api/client";
import { Accordion } from "../ui/Accordion";

interface ProviderInfo {
  name: string;
  is_primary: boolean;
  model: string | null;
  base_url: string | null;
}

interface LLMConfig {
  providers: ProviderInfo[];
}

interface ProviderHealth {
  name: string;
  healthy: boolean;
}

interface Health {
  db: boolean;
  redis: boolean;
  llm: boolean;
  provider_health: ProviderHealth[];
}

interface ModelUsage {
  model: string;
  hour: number;
  day: number;
}

interface LLMUsage {
  models: ModelUsage[];
}

interface TTSHealth {
  provider: string;
  healthy: boolean;
  base_url: string | null;
  engine: string | null;
}

const PROVIDER_LABEL: Record<string, string> = {
  anthropic: "Anthropic",
  ollama: "Ollama",
};

// "network" on its own says nothing about what actually synthesizes, so the
// card below pairs this label with the engine reported by the remote service.
const TTS_PROVIDER_LABEL: Record<string, string> = {
  piper: "Piper",
  network: "tts_service",
};

export default function LLMConfigPanel() {
  const { t } = useTranslation();
  const [config, setConfig] = useState<LLMConfig | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [ttsHealth, setTtsHealth] = useState<TTSHealth | null>(null);
  const [usage, setUsage] = useState<LLMUsage | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  const checkHealth = async () => {
    setHealthLoading(true);
    try {
      // Two independent endpoints (podcast-health is deliberately not folded
      // into /health -- see backend api/settings.py) fetched together so
      // one "Check" click still covers everything on this tab.
      // allSettled, not all: these report on different services, so an
      // unreachable TTS host must not also discard a perfectly good
      // /settings/health result (and, now that this runs unattended on
      // mount, must not surface as an unhandled rejection either).
      const [healthResp, ttsResp, usageResp] = await Promise.allSettled([
        client.get<Health>("/settings/health"),
        client.get<TTSHealth>("/settings/podcast-health"),
        client.get<LLMUsage>("/settings/llm-usage"),
      ]);
      if (healthResp.status === "fulfilled") setHealth(healthResp.value.data);
      if (ttsResp.status === "fulfilled") setTtsHealth(ttsResp.value.data);
      if (usageResp.status === "fulfilled") setUsage(usageResp.value.data);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    client.get<LLMConfig>("/settings/llm").then((r) => setConfig(r.data));
    // Both accordions start open, so run the check up front: an auto-opened
    // Service Health panel that stays empty until you press "Check" would be
    // worse than not opening it. The Configured providers TTS card needs
    // /settings/podcast-health for its engine/URL rows anyway.
    void checkHealth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const usageFor = (model: string | null) =>
    model ? usage?.models.find((m) => m.model === model) ?? null : null;

  if (!config) return <p className="text-sm text-gray-400">{t("common.loading")}</p>;

  return (
    <div>
      <Accordion title={t("llm.configuredProviders")} defaultOpen>
        <div className="p-4 bg-amber-50 dark:bg-amber-900/40 border border-amber-200 dark:border-amber-800 rounded-lg text-sm text-amber-700 dark:text-amber-300">
          {t("llm.readOnlyNotice")}
        </div>
        <div className="flex flex-col gap-2">
          {config.providers.map((p) => {
            const used = usageFor(p.model);
            return (
            <div
              key={p.name}
              className="p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {PROVIDER_LABEL[p.name] ?? p.name}
                </span>
                {p.is_primary ? (
                  <span className="px-1.5 py-0.5 text-xs font-medium rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300">
                    {t("llm.primary")}
                  </span>
                ) : (
                  <span className="px-1.5 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                    {t("llm.fallback")}
                  </span>
                )}
              </div>
              <div className="flex flex-col gap-1">
                {p.model && (
                  <div className="flex gap-2 text-xs">
                    <span className="text-gray-400 w-16 shrink-0">{t("llm.model")}</span>
                    <span className="font-mono text-gray-700 dark:text-gray-300">{p.model}</span>
                  </div>
                )}
                {p.base_url && (
                  <div className="flex gap-2 text-xs">
                    <span className="text-gray-400 w-16 shrink-0">{t("llm.ollamaUrl")}</span>
                    <span className="font-mono text-gray-700 dark:text-gray-300 break-all">{p.base_url}</span>
                  </div>
                )}
                {used && (
                  <div className="flex gap-2 text-xs">
                    <span className="text-gray-400 w-16 shrink-0">{t("llm.requests")}</span>
                    <span
                      className="font-mono text-gray-700 dark:text-gray-300 tabular-nums"
                      title={t("llm.requestsHint")}
                    >
                      {used.hour.toLocaleString()}
                      <span className="text-gray-400"> / {t("llm.lastHour")}</span>
                      <span className="text-gray-300 dark:text-gray-600"> · </span>
                      {used.day.toLocaleString()}
                      <span className="text-gray-400"> / {t("llm.lastDay")}</span>
                    </span>
                  </div>
                )}
              </div>
            </div>
            );
          })}
          {ttsHealth && (
            <div className="p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {TTS_PROVIDER_LABEL[ttsHealth.provider] ?? ttsHealth.provider}
                </span>
                <span className="px-1.5 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                  {t("llm.podcastTts")}
                </span>
              </div>
              <div className="flex flex-col gap-1">
                {ttsHealth.engine && (
                  <div className="flex gap-2 text-xs">
                    <span className="text-gray-400 w-16 shrink-0">{t("llm.ttsEngine")}</span>
                    <span className="font-mono text-gray-700 dark:text-gray-300">{ttsHealth.engine}</span>
                  </div>
                )}
                {ttsHealth.base_url && (
                  <div className="flex gap-2 text-xs">
                    <span className="text-gray-400 w-16 shrink-0">{t("llm.serviceUrl")}</span>
                    <span className="font-mono text-gray-700 dark:text-gray-300 break-all">{ttsHealth.base_url}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </Accordion>

      <Accordion
        title={t("llm.serviceHealth")}
        defaultOpen
        action={
          <button
            onClick={checkHealth}
            disabled={healthLoading}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400 disabled:opacity-50"
          >
            {healthLoading && <Loader size={13} className="animate-spin" />}
            {t("common.check")}
          </button>
        }
      >
        {health ? (
          <div className="flex flex-col gap-2">
            <HealthRow label={t("llm.database")} ok={health.db} />
            <HealthRow label={t("llm.redis")} ok={health.redis} />
            {health.provider_health.length > 0
              ? health.provider_health.map((ph) => (
                  <HealthRow
                    key={ph.name}
                    label={PROVIDER_LABEL[ph.name] ?? ph.name}
                    ok={ph.healthy}
                  />
                ))
              : <HealthRow label="LLM" ok={health.llm} />
            }
            {ttsHealth && (
              <HealthRow
                label={`${t("llm.podcastTts")} (${ttsHealth.provider})`}
                ok={ttsHealth.healthy}
                detail={ttsHealth.base_url ?? undefined}
              />
            )}
          </div>
        ) : healthLoading ? (
          <p className="text-sm text-gray-400">{t("common.loading")}</p>
        ) : null}
      </Accordion>
    </div>
  );
}

function HealthRow({ label, ok, detail }: { label: string; ok: boolean; detail?: string }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
      {ok ? (
        <CheckCircle size={16} className="text-green-500 shrink-0" />
      ) : (
        <XCircle size={16} className="text-red-500 shrink-0" />
      )}
      <div className="min-w-0">
        <span className="text-sm font-medium">{label}</span>
        {detail && <p className="text-xs text-gray-400 font-mono truncate">{detail}</p>}
      </div>
      <span className={`ml-auto shrink-0 text-xs font-medium px-1.5 py-0.5 rounded ${ok ? "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300" : "bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300"}`}>
        {ok ? t("llm.healthy") : t("llm.unreachable")}
      </span>
    </div>
  );
}
