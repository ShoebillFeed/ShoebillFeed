import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Loader } from "lucide-react";
import client from "../../api/client";

interface LLMConfig {
  llm_provider: string;
  anthropic_model: string;
  ollama_base_url: string;
  ollama_model: string;
}

interface Health {
  db: boolean;
  redis: boolean;
  llm: boolean;
}

const inputClass =
  "w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";

export default function LLMConfigPanel() {
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

  if (!config) return <p className="text-sm text-gray-400">Loading…</p>;

  return (
    <div>
      <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">LLM Configuration</h2>

      <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-sm text-amber-700 dark:text-amber-300 mb-4">
        LLM provider settings are controlled via the <code className="font-mono">.env</code> file and environment variables. Changes here are read-only — restart the stack to apply new settings.
      </div>

      <div className="flex flex-col gap-3 mb-6">
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-500">Provider</label>
          <input className={inputClass} value={config.llm_provider} readOnly />
        </div>

        {config.llm_provider === "anthropic" && (
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-500">Model</label>
            <input className={inputClass} value={config.anthropic_model} readOnly />
          </div>
        )}

        {config.llm_provider === "ollama" && (
          <>
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-500">Ollama URL</label>
              <input className={inputClass} value={config.ollama_base_url} readOnly />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-500">Ollama Model</label>
              <input className={inputClass} value={config.ollama_model} readOnly />
            </div>
          </>
        )}
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium text-sm">Service Health</h3>
          <button
            onClick={checkHealth}
            disabled={healthLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            {healthLoading ? <Loader size={14} className="animate-spin" /> : null}
            Check
          </button>
        </div>

        {health && (
          <div className="flex flex-col gap-2">
            <HealthRow label="Database" ok={health.db} />
            <HealthRow label="Redis" ok={health.redis} />
            <HealthRow label="LLM" ok={health.llm} />
          </div>
        )}
      </div>
    </div>
  );
}

function HealthRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
      {ok ? (
        <CheckCircle size={16} className="text-green-500 shrink-0" />
      ) : (
        <XCircle size={16} className="text-red-500 shrink-0" />
      )}
      <span className="text-sm font-medium">{label}</span>
      <span className={`ml-auto text-xs font-medium ${ok ? "text-green-600" : "text-red-500"}`}>
        {ok ? "healthy" : "unreachable"}
      </span>
    </div>
  );
}
