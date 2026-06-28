import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Loader } from "lucide-react";
import { useTranslation } from "react-i18next";
import client from "../../api/client";
import { Accordion } from "./Accordion";

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

const PROVIDER_LABEL: Record<string, string> = {
  anthropic: "Anthropic",
  ollama: "Ollama",
};

export default function LLMConfigPanel() {
  const { t } = useTranslation();
  const [config, setConfig] = useState<LLMConfig | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  useEffect(() => {
    client.get<LLMConfig>("/settings/llm").then((r) => setConfig(r.data));
  }, []);

  const checkHealth = async () => {
    setHealthLoading(true);
    try {
      const r = await client.get<Health>("/settings/health");
      setHealth(r.data);
    } finally {
      setHealthLoading(false);
    }
  };

  if (!config) return <p className="text-sm text-gray-400">{t("common.loading")}</p>;

  return (
    <div>
      <Accordion title={t("llm.configuredProviders")} defaultOpen>
        <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-sm text-amber-700 dark:text-amber-300">
          {t("llm.readOnlyNotice")}
        </div>
        <div className="flex flex-col gap-2">
          {config.providers.map((p) => (
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
              </div>
            </div>
          ))}
        </div>
      </Accordion>

      <Accordion
        title={t("llm.serviceHealth")}
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
          </div>
        ) : null}
      </Accordion>
    </div>
  );
}

function HealthRow({ label, ok }: { label: string; ok: boolean }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
      {ok ? (
        <CheckCircle size={16} className="text-green-500 shrink-0" />
      ) : (
        <XCircle size={16} className="text-red-500 shrink-0" />
      )}
      <span className="text-sm font-medium">{label}</span>
      <span className={`ml-auto text-xs font-medium ${ok ? "text-green-600 dark:text-green-400" : "text-red-500"}`}>
        {ok ? t("llm.healthy") : t("llm.unreachable")}
      </span>
    </div>
  );
}
