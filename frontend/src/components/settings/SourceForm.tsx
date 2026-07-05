import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronRight, Wand2 } from "lucide-react";
import { isAxiosError } from "axios";
import type { Source, SourceCreate, SourceType } from "../../types/source";
import { useCreateSource, useUpdateSource } from "../../hooks/useSources";
import { sourcesApi } from "../../api/sources";
import { cn } from "../../lib/utils";

const SOURCE_TYPES: { id: SourceType; label: string }[] = [
  { id: "rss", label: "RSS / Atom" },
  { id: "reddit", label: "Reddit" },
  { id: "email", label: "Email (IMAP)" },
  { id: "mastodon", label: "Mastodon" },
  { id: "arxiv", label: "arXiv" },
  { id: "lemmy", label: "Lemmy (experimental)" },
  { id: "github", label: "GitHub" },
  { id: "bluesky", label: "Bluesky (experimental)" },
  { id: "telegram", label: "Telegram" },
  { id: "scraper", label: "Web Scraper" },
];

const DEFAULT_INTERVALS = [
  { label: "15 min", value: 900 },
  { label: "30 min", value: 1800 },
  { label: "1 hour", value: 3600 },
  { label: "6 hours", value: 21600 },
  { label: "24 hours", value: 86400 },
];

interface Props {
  source?: Source;
  onClose: () => void;
}

export default function SourceForm({ source, onClose }: Props) {
  const { t } = useTranslation();
  const isEdit = Boolean(source);
  const create = useCreateSource();
  const update = useUpdateSource();

  const [name, setName] = useState(source?.name ?? "");
  const [type, setType] = useState<SourceType>(source?.source_type ?? "rss");
  const [config, setConfig] = useState<Record<string, string>>(() => {
    if (!source) return {};
    return Object.fromEntries(Object.entries(source.config).map(([k, v]) => [k, String(v)]));
  });
  const [interval, setInterval] = useState(source?.fetch_interval ?? 3600);
  const [isActive, setIsActive] = useState(source?.is_active ?? true);
  const [formError, setFormError] = useState<string | null>(null);

  const setConfigField = (key: string, value: string) =>
    setConfig((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (type === "scraper" && !(config["item_selector"] ?? "").trim()) {
      setFormError(t("sourceForm.scraperConfigRequired"));
      return;
    }
    const parsedConfig = Object.fromEntries(
      Object.entries(config).filter(([, v]) => v.trim() !== "")
    );
    try {
      if (isEdit && source) {
        await update.mutateAsync({ id: source.id, data: { name, config: parsedConfig, is_active: isActive, fetch_interval: interval } });
      } else {
        const payload: SourceCreate = { name, source_type: type, config: parsedConfig, is_active: isActive, fetch_interval: interval };
        await create.mutateAsync(payload);
      }
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 403) {
        setFormError(t("sourceForm.scraperRobotsDisallowed"));
        return;
      }
      throw err;
    }
    onClose();
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div>
        <label className="block text-sm font-medium mb-1">{t("sourceForm.name")}</label>
        <input
          className={inputClass}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder={t("sourceForm.namePlaceholder")}
        />
      </div>

      {!isEdit && (
        <div>
          <label className="block text-sm font-medium mb-1">{t("sourceForm.type")}</label>
          <div className="grid grid-cols-2 gap-2">
            {SOURCE_TYPES.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => { setType(id); setConfig({}); }}
                className={cn(
                  "px-3 py-2 text-sm rounded border transition-colors",
                  type === id
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "border-gray-300 dark:border-gray-600 hover:border-gray-400"
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      )}

      <ConfigFields type={type} config={config} onChange={setConfigField} />

      <div>
        <label className="block text-sm font-medium mb-1">{t("sourceForm.fetchInterval")}</label>
        <select
          className={inputClass}
          value={interval}
          onChange={(e) => setInterval(Number(e.target.value))}
        >
          {DEFAULT_INTERVALS.map(({ label, value }) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={isActive}
          onChange={(e) => setIsActive(e.target.checked)}
          className="rounded"
        />
        {t("sourceForm.active")}
      </label>

      {formError && <p className="text-sm text-red-500">{formError}</p>}

      <div className="flex gap-2 mt-2">
        <button type="button" onClick={onClose} className={cn(btnClass, "flex-1 bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300")}>
          {t("common.cancel")}
        </button>
        <button type="submit" className={cn(btnClass, "flex-1 bg-indigo-600 text-white hover:bg-indigo-700")}>
          {isEdit ? t("common.save") : t("sourceForm.addSource")}
        </button>
      </div>
    </form>
  );
}

function ConfigFields({
  type,
  config,
  onChange,
}: {
  type: SourceType;
  config: Record<string, string>;
  onChange: (k: string, v: string) => void;
}) {
  const { t } = useTranslation();
  if (type === "rss") return (
    <Field label={t("sourceForm.feedUrl")} field="url" config={config} onChange={onChange} placeholder="https://example.com/feed.xml" required />
  );
  if (type === "reddit") return (
    <>
      <Field label={t("sourceForm.subreddit")} field="subreddit" config={config} onChange={onChange} placeholder="MachineLearning" required />
      <Field label={t("sourceForm.redditSort")} field="sort" config={config} onChange={onChange} placeholder="hot" />
      <Field label={t("sourceForm.limit")} field="limit" config={config} onChange={onChange} placeholder="25" />
    </>
  );
  if (type === "youtube") return (
    <>
      <Field label={t("sourceForm.channelId")} field="channel_id" config={config} onChange={onChange} placeholder="UCxxxxxxxxxxxxx" required />
      <Field label={t("sourceForm.maxResults")} field="max_results" config={config} onChange={onChange} placeholder="10" />
    </>
  );
  if (type === "email") return (
    <>
      <Field label={t("sourceForm.imapHost")} field="imap_host" config={config} onChange={onChange} placeholder="imap.gmail.com" required />
      <Field label={t("sourceForm.imapPort")} field="imap_port" config={config} onChange={onChange} placeholder="993" />
      <Field label={t("sourceForm.username")} field="username" config={config} onChange={onChange} placeholder="you@example.com" required />
      <Field label={t("sourceForm.password")} field="password" config={config} onChange={onChange} placeholder="app password" type="password" required />
      <Field label={t("sourceForm.folder")} field="folder" config={config} onChange={onChange} placeholder="INBOX" />
      <Field label={t("sourceForm.subjectFilter")} field="subject_filter" config={config} onChange={onChange} placeholder="" />
    </>
  );
  if (type === "mastodon") return (
    <>
      <Field label={t("sourceForm.instanceUrl")} field="instance_url" config={config} onChange={onChange} placeholder="mastodon.social" required />
      <div>
        <label className="block text-sm font-medium mb-1">{t("sourceForm.feedType")}</label>
        <select
          className={inputClass}
          value={config["feed_type"] ?? "hashtag"}
          onChange={(e) => onChange("feed_type", e.target.value)}
        >
          <option value="hashtag">{t("sourceForm.hashtag")}</option>
          <option value="user">{t("sourceForm.userTimeline")}</option>
          <option value="local">{t("sourceForm.localTimeline")}</option>
        </select>
      </div>
      {(config["feed_type"] ?? "hashtag") !== "local" && (
        <Field
          label={(config["feed_type"] ?? "hashtag") === "user" ? t("sourceForm.usernameWithout") : t("sourceForm.hashtagWithout")}
          field="name"
          config={config}
          onChange={onChange}
          placeholder={(config["feed_type"] ?? "hashtag") === "user" ? "username" : "technology"}
          required
        />
      )}
    </>
  );
  if (type === "arxiv" || type === "scholar") return (
    <>
      <Field label={t("sourceForm.searchQuery")} field="query" config={config} onChange={onChange} placeholder="e.g. transformer architecture" required />
      <p className="text-xs text-gray-400 dark:text-gray-500 -mt-2">
        {t("sourceForm.arxivExamples")} <span className="font-mono">large language models</span> · <span className="font-mono">quantum computing error correction</span> · <span className="font-mono">CRISPR gene editing</span> · <span className="font-mono">reinforcement learning robotics</span>
        <br />{t("sourceForm.arxivTip")}
      </p>
    </>
  );
  if (type === "lemmy") return (
    <>
      <Field label={t("sourceForm.instanceUrl")} field="instance_url" config={config} onChange={onChange} placeholder="lemmy.world" required />
      <Field label={t("sourceForm.community")} field="community" config={config} onChange={onChange} placeholder="technology" required />
      <div>
        <label className="block text-sm font-medium mb-1">{t("sourceForm.lemmySort")}</label>
        <select className={inputClass} value={config["sort"] ?? "Hot"} onChange={(e) => onChange("sort", e.target.value)}>
          <option value="Hot">Hot</option>
          <option value="New">New</option>
          <option value="TopDay">Top (day)</option>
          <option value="TopWeek">Top (week)</option>
        </select>
      </div>
      <Field label={t("sourceForm.limit")} field="limit" config={config} onChange={onChange} placeholder="25" />
    </>
  );
  if (type === "github") return (
    <>
      <div>
        <label className="block text-sm font-medium mb-1">{t("sourceForm.githubMode")}</label>
        <select className={inputClass} value={config["mode"] ?? "releases"} onChange={(e) => onChange("mode", e.target.value)}>
          <option value="releases">{t("sourceForm.githubReleases")}</option>
          <option value="trending">{t("sourceForm.githubTrending")}</option>
        </select>
      </div>
      {(config["mode"] ?? "releases") === "releases" ? (
        <>
          <Field label={t("sourceForm.githubRepo")} field="repo" config={config} onChange={onChange} placeholder="openai/openai-python" required />
          <Field label={t("sourceForm.limit")} field="limit" config={config} onChange={onChange} placeholder="20" />
          <Field label={t("sourceForm.githubToken")} field="token" config={config} onChange={onChange} placeholder={t("sourceForm.githubTokenPlaceholder")} />
        </>
      ) : (
        <>
          <Field label={t("sourceForm.githubLanguage")} field="language" config={config} onChange={onChange} placeholder="python" />
          <div>
            <label className="block text-sm font-medium mb-1">{t("sourceForm.githubSince")}</label>
            <select className={inputClass} value={config["since"] ?? "daily"} onChange={(e) => onChange("since", e.target.value)}>
              <option value="daily">{t("sourceForm.githubDaily")}</option>
              <option value="weekly">{t("sourceForm.githubWeekly")}</option>
              <option value="monthly">{t("sourceForm.githubMonthly")}</option>
            </select>
          </div>
        </>
      )}
    </>
  );
  if (type === "bluesky") return (
    <>
      <div>
        <label className="block text-sm font-medium mb-1">{t("sourceForm.feedType")}</label>
        <select className={inputClass} value={config["feed_type"] ?? "user"} onChange={(e) => onChange("feed_type", e.target.value)}>
          <option value="user">{t("sourceForm.userTimeline")}</option>
          <option value="search">{t("sourceForm.searchFeed")}</option>
        </select>
      </div>
      {(config["feed_type"] ?? "user") === "user" ? (
        <Field label={t("sourceForm.bskyHandle")} field="handle" config={config} onChange={onChange} placeholder="bsky.app" required />
      ) : (
        <Field label={t("sourceForm.searchQuery")} field="query" config={config} onChange={onChange} placeholder="#AI" required />
      )}
      <Field label={t("sourceForm.limit")} field="limit" config={config} onChange={onChange} placeholder="20" />
    </>
  );
  if (type === "telegram") return (
    <Field label={t("sourceForm.telegramChannel")} field="channel" config={config} onChange={onChange} placeholder="bbcnews" required />
  );
  if (type === "scraper") return <ScraperConfigFields config={config} onChange={onChange} />;
  return null;
}

function ScraperConfigFields({
  config,
  onChange,
}: {
  config: Record<string, string>;
  onChange: (k: string, v: string) => void;
}) {
  const { t } = useTranslation();
  const [advancedOpen, setAdvancedOpen] = useState(Boolean(config["item_selector"]));
  const [detecting, setDetecting] = useState(false);
  const [detectError, setDetectError] = useState<string | null>(null);
  const [robotsBlocked, setRobotsBlocked] = useState(false);
  const [detectedSelectors, setDetectedSelectors] = useState<{ item: string; title: string; link: string; content: string } | null>(null);
  const [preview, setPreview] = useState<{ title: string; url: string; content: string }[] | null>(null);
  const [itemCount, setItemCount] = useState<number | null>(null);

  const url = (config["url"] ?? "").trim();
  const fetchFull = config["fetch_full_articles"] !== "false";

  const handleDetect = async () => {
    if (!url || detecting) return;
    setDetecting(true);
    setDetectError(null);
    setRobotsBlocked(false);
    setPreview(null);
    setItemCount(null);
    setDetectedSelectors(null);
    try {
      const result = await sourcesApi.suggestScraperConfig(url);
      onChange("item_selector", result.config.item_selector);
      onChange("title_selector", result.config.title_selector);
      onChange("link_selector", result.config.link_selector);
      onChange("content_selector", result.config.content_selector);
      setDetectedSelectors({
        item: result.config.item_selector,
        title: result.config.title_selector,
        link: result.config.link_selector,
        content: result.config.content_selector,
      });
      setPreview(result.preview);
      setItemCount(result.item_count);
      if (result.item_count === 0) setAdvancedOpen(true);
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 403) {
        setRobotsBlocked(true);
      } else {
        setDetectError(t("sourceForm.scraperDetectError"));
        setAdvancedOpen(true);
      }
    } finally {
      setDetecting(false);
    }
  };

  return (
    <>
      <Field label={t("sourceForm.scraperUrl")} field="url" config={config} onChange={onChange} placeholder="https://example.com/news" required />

      <div>
        <button
          type="button"
          onClick={handleDetect}
          disabled={!url || detecting}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded transition-colors",
            !url || detecting
              ? "bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600"
              : "bg-indigo-50 text-indigo-600 hover:bg-indigo-100 dark:bg-indigo-950 dark:text-indigo-400 dark:hover:bg-indigo-900"
          )}
        >
          <Wand2 size={14} className={detecting ? "animate-pulse" : ""} />
          {detecting ? t("sourceForm.scraperDetecting") : t("sourceForm.scraperDetect")}
        </button>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1.5">{t("sourceForm.scraperDetectHint")}</p>
      </div>

      {robotsBlocked && (
        <div className="rounded border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 px-3 py-2.5 flex gap-2">
          <span className="text-amber-500 shrink-0 mt-0.5">⚠</span>
          <div>
            <p className="text-xs font-medium text-amber-700 dark:text-amber-400">{t("sourceForm.scraperRobotsTitle")}</p>
            <p className="text-xs text-amber-600 dark:text-amber-500 mt-0.5">{t("sourceForm.scraperRobotsBody")}</p>
          </div>
        </div>
      )}

      {detectError && <p className="text-xs text-red-500">{detectError}</p>}

      {itemCount !== null && itemCount > 0 && preview && detectedSelectors && (
        <div className="rounded border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/30 p-3 flex flex-col gap-2">
          <div>
            <p className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1">
              {t("sourceForm.scraperFoundItems", { count: itemCount })}
            </p>
            <p className="text-xs text-green-600 dark:text-green-500">
              {t("sourceForm.scraperPreviewDesc", {
                item: detectedSelectors.item,
                title: detectedSelectors.title,
                link: detectedSelectors.link,
              })}
            </p>
          </div>
          <ul className="flex flex-col gap-2">
            {preview.slice(0, 5).map((item, i) => (
              <li key={i} className="flex flex-col gap-0.5">
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">{item.title}</span>
                {item.content && (
                  <span className="text-xs text-gray-400 dark:text-gray-500 line-clamp-2">{item.content}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {itemCount === 0 && (
        <p className="text-xs text-amber-500">{t("sourceForm.scraperNoItemsFound")}</p>
      )}

      <div>
        <label className="flex items-start gap-2.5 cursor-pointer">
          <input
            type="checkbox"
            checked={fetchFull}
            onChange={(e) => onChange("fetch_full_articles", e.target.checked ? "true" : "false")}
            className="mt-0.5 rounded shrink-0"
          />
          <div>
            <span className="text-sm font-medium">{t("sourceForm.scraperFetchFull")}</span>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{t("sourceForm.scraperFetchFullDesc")}</p>
          </div>
        </label>
      </div>

      <div>
        <button
          type="button"
          onClick={() => setAdvancedOpen((v) => !v)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          {advancedOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          {t("sourceForm.scraperAdvanced")}
        </button>
        {advancedOpen && (
          <div className="flex flex-col gap-3 mt-2">
            <Field label={t("sourceForm.scraperItemSelector")} field="item_selector" config={config} onChange={onChange} placeholder="article.post" />
            <Field label={t("sourceForm.scraperTitleSelector")} field="title_selector" config={config} onChange={onChange} placeholder="h2.title" />
            <Field label={t("sourceForm.scraperLinkSelector")} field="link_selector" config={config} onChange={onChange} placeholder="a.read-more" />
            <Field label={t("sourceForm.scraperContentSelector")} field="content_selector" config={config} onChange={onChange} placeholder="p.summary" />
            <p className="text-xs text-gray-400 dark:text-gray-500">{t("sourceForm.scraperTip")}</p>
          </div>
        )}
      </div>
    </>
  );
}

function Field({
  label, field, config, onChange, placeholder, required, type = "text",
}: {
  label: string; field: string; config: Record<string, string>;
  onChange: (k: string, v: string) => void; placeholder?: string; required?: boolean; type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      <input
        className={inputClass}
        type={type}
        value={config[field] ?? ""}
        onChange={(e) => onChange(field, e.target.value)}
        placeholder={placeholder}
        required={required}
      />
    </div>
  );
}

const inputClass = "w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";
const btnClass = "px-4 py-2 text-sm font-medium rounded transition-colors";
