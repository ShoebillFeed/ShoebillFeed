import { useState } from "react";
import { Check, Copy, Trash2 } from "lucide-react";
import { Accordion } from "./Accordion";
import { useTranslation } from "react-i18next";
import { formatDistanceToNow } from "date-fns";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";
import { useChangePassword } from "../../hooks/useAuth";
import { usePreferencesStore } from "../../stores/preferencesStore";
import { useTokens, useCreateToken, useDeleteToken } from "../../hooks/useTokens";
import type { ApiTokenCreated } from "../../api/tokens";
import { Field } from "./SettingsControls";

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
  );
}

// ─── API Tokens section ───────────────────────────────────────────────────────

function ApiTokensContent() {
  const { t } = useTranslation();
  const { data: tokens = [] } = useTokens();
  const createToken = useCreateToken();
  const deleteToken = useDeleteToken();

  const [name, setName] = useState("");
  const [newToken, setNewToken] = useState<ApiTokenCreated | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    const result = await createToken.mutateAsync(trimmed);
    setNewToken(result);
    setName("");
  };

  const handleCopy = async () => {
    if (!newToken) return;
    await navigator.clipboard.writeText(newToken.token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const apiUrl = window.location.origin;
  const mcpConfig = JSON.stringify(
    {
      mcpServers: {
        "shoebill-feed": {
          command: "uv",
          args: ["run", "--with", "mcp", "--with", "httpx", "/path/to/shoebill_feed/mcp_server/server.py"],
          env: {
            SHOEBILL_API_URL: `${apiUrl}/api`,
            SHOEBILL_API_TOKEN: "<your-token>",
          },
        },
      },
    },
    null,
    2
  );

  return (
    <div className="flex flex-col gap-6">
      <p className="text-xs text-gray-500 dark:text-gray-400">{t("advanced.apiTokensDesc")}</p>

      {/* Create new token */}
      <form onSubmit={handleCreate} className="flex gap-2 items-end max-w-sm">
        <div className="flex-1">
          <label className="block text-xs font-medium mb-1 text-gray-700 dark:text-gray-300">
            {t("advanced.tokenName")}
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={t("advanced.tokenNamePlaceholder")}
            className="w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            maxLength={100}
          />
        </div>
        <button
          type="submit"
          disabled={createToken.isPending || !name.trim()}
          className="px-3 py-2 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors shrink-0"
        >
          {createToken.isPending ? "…" : t("advanced.generateToken")}
        </button>
      </form>

      {/* Newly created token — show-once banner */}
      {newToken && (
        <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/40 border border-green-200 dark:border-green-700 flex flex-col gap-2">
          <p className="text-xs font-medium text-green-800 dark:text-green-300">
            {t("advanced.tokenCreated")}
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-xs font-mono bg-white dark:bg-gray-900 rounded px-2 py-1.5 border border-green-200 dark:border-green-700 break-all text-gray-800 dark:text-gray-200">
              {newToken.token}
            </code>
            <button
              type="button"
              onClick={handleCopy}
              className="shrink-0 p-1.5 rounded text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/40 transition-colors"
              title={t("advanced.copyToken")}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>
      )}

      {/* Token list */}
      {tokens.length === 0 ? (
        <p className="text-sm text-gray-400">{t("advanced.noTokens")}</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {tokens.map((tok) => (
            <li
              key={tok.id}
              className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                  {tok.name}
                </p>
                <p className="text-xs text-gray-400">
                  {tok.last_used_at
                    ? t("advanced.tokenLastUsed", {
                        date: formatDistanceToNow(new Date(tok.last_used_at), { addSuffix: true }),
                      })
                    : t("advanced.tokenNeverUsed")}
                </p>
              </div>
              <button
                type="button"
                onClick={() => deleteToken.mutate(tok.id)}
                disabled={deleteToken.isPending}
                className="shrink-0 p-1.5 rounded text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                title={t("advanced.revokeToken")}
              >
                <Trash2 size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* MCP setup instructions */}
      <div>
        <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
          {t("advanced.mcpSetup")}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
          {t("advanced.mcpSetupDesc")}
        </p>
        <pre className="text-xs font-mono bg-gray-100 dark:bg-gray-800 rounded-lg p-3 overflow-x-auto border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 whitespace-pre">
          {mcpConfig}
        </pre>
      </div>
    </div>
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
      <Accordion title={t("preferences.interfaceTitle")} defaultOpen>
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
      </Accordion>

      <Accordion title={t("preferences.contentTitle")}>
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
        {update.isSuccess && (
          <p className="text-xs text-green-600 dark:text-green-400">
            {t("preferences.settingsSaved")}
          </p>
        )}
        {update.isError && (
          <p className="text-xs text-red-500">{t("preferences.settingsFailed")}</p>
        )}
      </Accordion>

      <Accordion title={t("advanced.security")}>
        <ChangePasswordSection />
      </Accordion>

      <Accordion title={t("advanced.apiTokens")} description={t("advanced.apiTokensDesc")}>
        <ApiTokensContent />
      </Accordion>
    </div>
  );
}
