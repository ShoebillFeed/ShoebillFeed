import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Check, Loader2, Play, Plus, Trash2, Upload, X } from "lucide-react";
import { cn } from "../../lib/utils";
import { CONTENT_LANGUAGES } from "../../lib/languages";
import { useCategories } from "../../hooks/useCategories";
import { useSources } from "../../hooks/useSources";
import {
  useCreatePodcastShow,
  useUpdatePodcastShow,
  usePodcastVoices,
  usePreviewVoice,
  useUploadPodcastCover,
  useDeletePodcastCover,
} from "../../hooks/usePodcasts";
import { usePodcastTtsHealth } from "../../hooks/useSettings";
import { RangeSlider } from "./SettingsControls";
import type { PodcastShow, PodcastHost } from "../../types/podcast";

const MAX_HOSTS = 3;

const TIME_WINDOW_OPTIONS = [
  { hours: 6, key: "6h" },
  { hours: 12, key: "12h" },
  { hours: 24, key: "24h" },
  { hours: 48, key: "48h" },
  { hours: 168, key: "7d" },
];

// Intl.supportedValuesOf isn't in the project's ES2020 lib target yet (widely
// supported at runtime in evergreen browsers since 2022) — narrow local type
// instead of widening the shared tsconfig lib for one call site.
type IntlWithSupportedValuesOf = typeof Intl & { supportedValuesOf?: (input: string) => string[] };
const TIMEZONES: string[] = (Intl as IntlWithSupportedValuesOf).supportedValuesOf?.("timeZone") ?? ["UTC"];
const BROWSER_TIMEZONE = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";

function generateHostId(): string {
  // crypto.randomUUID() only exists in secure contexts (HTTPS or localhost).
  // This id is just a local React key / a way to pair a host with its script
  // turns -- not security-sensitive -- so fall back to Math.random rather
  // than breaking the form when accessed over plain HTTP on a non-localhost
  // address.
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `host-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function newHost(index: number): PodcastHost {
  return {
    id: generateHostId(),
    name: `Host ${index + 1}`,
    character_prompt: "",
    voice: "",
  };
}

interface Props {
  show?: PodcastShow;
  onClose: () => void;
}

export default function PodcastShowForm({ show, onClose }: Props) {
  const { t } = useTranslation();
  const isEdit = Boolean(show);
  const create = useCreatePodcastShow();
  const update = useUpdatePodcastShow();
  const uploadCover = useUploadPodcastCover();
  const deleteCover = useDeletePodcastCover();
  const { data: categories = [] } = useCategories();
  const { data: sources = [] } = useSources();
  const coverInputRef = useRef<HTMLInputElement>(null);

  const [name, setName] = useState(show?.name ?? "");
  const [description, setDescription] = useState(show?.description ?? "");
  const [hosts, setHosts] = useState<PodcastHost[]>(show?.hosts ?? [newHost(0)]);
  const [categoryIds, setCategoryIds] = useState<string[]>(show?.category_ids ?? []);
  const [sourceIds, setSourceIds] = useState<string[]>(show?.source_ids ?? []);
  const [timeWindowHours, setTimeWindowHours] = useState(show?.time_window_hours ?? 24);
  const [targetLengthMinutes, setTargetLengthMinutes] = useState(show?.target_length_minutes ?? 10);
  const [language, setLanguage] = useState(show?.language ?? "en");
  const [scheduleTime, setScheduleTime] = useState(show?.schedule_time ?? "07:00");
  const [timezone, setTimezone] = useState(show?.timezone ?? BROWSER_TIMEZONE);
  const [speechRate, setSpeechRate] = useState(show?.speech_rate ?? 1.0);
  const [isActive, setIsActive] = useState(show?.is_active ?? true);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: voices = [] } = usePodcastVoices(language);
  const { data: ttsHealth } = usePodcastTtsHealth();
  const speechRateSupported = ttsHealth?.supports_speech_rate ?? true;

  const previewVoiceMutation = usePreviewVoice();
  const [previewingHostId, setPreviewingHostId] = useState<string | null>(null);
  const [previewErrorHostId, setPreviewErrorHostId] = useState<string | null>(null);

  const playVoicePreview = (host: PodcastHost) => {
    if (!host.voice || previewingHostId) return;
    setPreviewingHostId(host.id);
    setPreviewErrorHostId(null);
    previewVoiceMutation.mutate(
      { voiceId: host.voice, language },
      {
        onSuccess: (blob) => {
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          const cleanup = () => URL.revokeObjectURL(url);
          audio.addEventListener("ended", cleanup);
          audio.addEventListener("error", cleanup);
          audio.play().catch(cleanup);
        },
        onError: () => setPreviewErrorHostId(host.id),
        onSettled: () => setPreviewingHostId(null),
      }
    );
  };

  const toggleCategory = (id: string) =>
    setCategoryIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  const toggleSource = (id: string) =>
    setSourceIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const updateHost = (id: string, patch: Partial<PodcastHost>) =>
    setHosts((prev) => prev.map((h) => (h.id === id ? { ...h, ...patch } : h)));
  const removeHost = (id: string) => setHosts((prev) => prev.filter((h) => h.id !== id));
  const addHost = () => setHosts((prev) => (prev.length < MAX_HOSTS ? [...prev, newHost(prev.length)] : prev));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (hosts.length === 0) {
      setFormError(t("podcastForm.needAtLeastOneHost"));
      return;
    }
    if (hosts.some((h) => !h.name.trim() || !h.character_prompt.trim() || !h.voice)) {
      setFormError(t("podcastForm.hostFieldsRequired"));
      return;
    }
    const payload = {
      name,
      description: description.trim() || null,
      hosts,
      category_ids: categoryIds,
      source_ids: sourceIds,
      time_window_hours: timeWindowHours,
      target_length_minutes: targetLengthMinutes,
      language,
      schedule_time: scheduleTime,
      timezone,
      speech_rate: speechRate,
      is_active: isActive,
    };
    if (isEdit && show) {
      await update.mutateAsync({ id: show.id, data: payload });
    } else {
      await create.mutateAsync(payload);
    }
    onClose();
  };

  const handleCoverChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && show) uploadCover.mutate({ id: show.id, file });
    e.target.value = "";
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div>
        <label className="block text-sm font-medium mb-1">{t("podcastForm.name")}</label>
        <input
          className={inputClass}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder={t("podcastForm.namePlaceholder")}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">{t("podcastForm.showConcept")}</label>
        <textarea
          className={inputClass}
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={t("podcastForm.showConceptPlaceholder")}
          maxLength={1000}
        />
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{t("podcastForm.showConceptHint")}</p>
      </div>

      {isEdit && show && (
        <div>
          <label className="block text-sm font-medium mb-1">{t("podcastForm.coverImage")}</label>
          <div className="flex items-center gap-3">
            {show.cover_image_url ? (
              <img
                src={show.cover_image_url}
                alt=""
                className="w-16 h-16 rounded-lg object-cover border border-gray-200 dark:border-gray-700"
              />
            ) : (
              <div className="w-16 h-16 rounded-lg border border-dashed border-gray-300 dark:border-gray-600" />
            )}
            <input
              ref={coverInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={handleCoverChange}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => coverInputRef.current?.click()}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <Upload size={13} /> {t("podcastForm.uploadCoverImage")}
            </button>
            {show.cover_image_url && (
              <button
                type="button"
                onClick={() => deleteCover.mutate(show.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded text-red-600 hover:bg-red-50 dark:hover:bg-red-950"
              >
                <X size={13} /> {t("common.delete")}
              </button>
            )}
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium mb-1">{t("podcastForm.language")}</label>
        <select className={inputClass} value={language} onChange={(e) => setLanguage(e.target.value)}>
          {CONTENT_LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>{l.native}</option>
          ))}
        </select>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium">{t("podcastForm.hosts")}</label>
          {hosts.length < MAX_HOSTS && (
            <button
              type="button"
              onClick={addHost}
              className="flex items-center gap-1 text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              <Plus size={13} /> {t("podcastForm.addHost")}
            </button>
          )}
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500 mb-2">{t("podcastForm.characterPromptHint")}</p>
        <div className="flex flex-col gap-3">
          {hosts.map((host, i) => (
            <div key={host.id} className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <input
                  className={cn(inputClass, "flex-1")}
                  value={host.name}
                  onChange={(e) => updateHost(host.id, { name: e.target.value })}
                  placeholder={t("podcastForm.hostName")}
                  required
                />
                {hosts.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeHost(host.id)}
                    className="p-1.5 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
                    title={t("common.delete")}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
              <textarea
                className={inputClass}
                rows={2}
                value={host.character_prompt}
                onChange={(e) => updateHost(host.id, { character_prompt: e.target.value })}
                placeholder={t("podcastForm.characterPromptPlaceholder")}
                required
              />
              <div className="flex items-center gap-2">
                <select
                  className={cn(inputClass, "flex-1")}
                  value={host.voice}
                  onChange={(e) => updateHost(host.id, { voice: e.target.value })}
                  required
                >
                  <option value="" disabled>{t("podcastForm.selectVoice")}</option>
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>{v.label}</option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => playVoicePreview(host)}
                  disabled={!host.voice || previewingHostId === host.id}
                  className="p-2 rounded border border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed shrink-0 transition-colors"
                  title={t("podcastForm.previewVoice")}
                >
                  {previewingHostId === host.id ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                </button>
              </div>
              {previewErrorHostId === host.id && (
                <p className="text-xs text-red-600 dark:text-red-400">{t("podcastForm.previewFailed")}</p>
              )}
              {i === 0 && voices.length === 0 && (
                <p className="text-xs text-amber-600 dark:text-amber-400">{t("podcastForm.noVoicesForLanguage")}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">{t("podcastForm.categories")}</label>
        <div className="flex flex-wrap gap-2">
          {categories.filter((c) => c.is_active).map((cat) => {
            const selected = categoryIds.includes(cat.id);
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
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{t("podcastForm.categoriesHint")}</p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">{t("podcastForm.sources")}</label>
        <div className="flex flex-wrap gap-2">
          {sources.filter((s) => s.is_active).map((source) => {
            const selected = sourceIds.includes(source.id);
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
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{t("podcastForm.sourcesHint")}</p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">{t("podcastForm.timeWindow")}</label>
        <select className={inputClass} value={timeWindowHours} onChange={(e) => setTimeWindowHours(Number(e.target.value))}>
          {TIME_WINDOW_OPTIONS.map(({ hours, key }) => (
            <option key={hours} value={hours}>{t(`podcastForm.timeWindowOptions.${key}`)}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">{t("podcastForm.lengthMinutes")}</label>
        <RangeSlider value={targetLengthMinutes} onChange={setTargetLengthMinutes} min={1} max={15} unit=" min" />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">{t("podcastForm.speechRate")}</label>
        <RangeSlider
          value={speechRate}
          // Range-input float steps (e.g. 0.75 + 0.05*n) can drift to values
          // like 1.0499999999999998 -- round to 2dp before it hits state/API.
          onChange={(v) => setSpeechRate(Math.round(v * 100) / 100)}
          min={0.75}
          max={1.5}
          step={0.05}
          unit="x"
          disabled={!speechRateSupported}
        />
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
          {speechRateSupported ? t("podcastForm.speechRateHint") : t("podcastForm.speechRateUnsupportedHint")}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium mb-1">{t("podcastForm.scheduleTime")}</label>
          <input
            type="time"
            className={inputClass}
            value={scheduleTime}
            onChange={(e) => setScheduleTime(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t("podcastForm.timezone")}</label>
          <select className={inputClass} value={timezone} onChange={(e) => setTimezone(e.target.value)}>
            {TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>{tz}</option>
            ))}
          </select>
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} className="rounded" />
        {t("podcastForm.active")}
      </label>

      {formError && <p className="text-sm text-red-500">{formError}</p>}

      <div className="flex gap-2 mt-2">
        <button type="button" onClick={onClose} className={cn(btnClass, "flex-1 bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300")}>
          {t("common.cancel")}
        </button>
        <button type="submit" className={cn(btnClass, "flex-1 bg-indigo-600 text-white hover:bg-indigo-700")}>
          {isEdit ? t("common.save") : t("podcastForm.addShow")}
        </button>
      </div>
    </form>
  );
}

const inputClass = "w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";
const btnClass = "px-4 py-2 text-sm font-medium rounded transition-colors";
