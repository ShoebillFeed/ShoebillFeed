import { useState, useEffect, useRef } from "react";
import { RefreshCw } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { Category, CategoryCreate } from "../../types/category";
import { useCategories, useCreateCategory, useUpdateCategory } from "../../hooks/useCategories";
import { categoriesApi } from "../../api/categories";
import { cn } from "../../lib/utils";

const PROMPT_MAX_CHARS = 500;

const PRESET_COLORS = [
  "#6366f1", "#ec4899", "#f59e0b", "#10b981", "#3b82f6",
  "#8b5cf6", "#ef4444", "#14b8a6", "#f97316", "#06b6d4",
];

function buildFallbackPrompt(name: string, keywords: string): string {
  const trimmedName = name.trim();
  if (!trimmedName) return "";
  const keywordList = keywords.split(",").map((k) => k.trim()).filter(Boolean);
  const keywordPart = keywordList.length
    ? ` Relevant keywords include: ${keywordList.join(", ")}.`
    : "";
  return `Articles about ${trimmedName}.${keywordPart} Assign this category to content that focuses on ${trimmedName} topics or closely related subjects.`;
}

interface Props {
  category?: Category;
  /** Pre-fill name from a taxonomy node (create mode only) */
  taxonomyName?: string;
  /** IPTC taxonomy_id to attach on create */
  taxonomyId?: string;
  /** Pre-selected color when coming from taxonomy */
  defaultColor?: string;
  /** Pre-fill keywords from a taxonomy node (create mode only) */
  defaultKeywords?: string[];
  /** Pre-fill prompt from a taxonomy node (create mode only) */
  defaultPrompt?: string;
  onClose: () => void;
}

export default function CategoryForm({ category, taxonomyName, taxonomyId, defaultColor, defaultKeywords, defaultPrompt, onClose }: Props) {
  const { t } = useTranslation();
  const isEdit = Boolean(category);
  const create = useCreateCategory();
  const update = useUpdateCategory();
  const { data: allCategories } = useCategories();

  const initialName = category?.name ?? taxonomyName ?? "";
  const initialColor = category?.color ?? defaultColor ?? "#6366f1";
  const initialKeywords = category?.keywords.join(", ") ?? (defaultKeywords ?? []).join(", ");

  const [name, setName] = useState(initialName);
  const [color, setColor] = useState(initialColor);
  const [keywords, setKeywords] = useState(initialKeywords);
  const [prompt, setPrompt] = useState(
    category?.prompt ?? defaultPrompt ?? buildFallbackPrompt(initialName, initialKeywords)
  );
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const promptManuallyEdited = useRef(Boolean(category?.prompt || defaultPrompt));

  useEffect(() => {
    if (!promptManuallyEdited.current) {
      setPrompt(buildFallbackPrompt(name, keywords));
    }
  }, [name, keywords]);

  const handlePromptChange = (value: string) => {
    promptManuallyEdited.current = true;
    setGenerateError(null);
    setPrompt(value);
  };

  const regeneratePrompt = async () => {
    const trimmedName = name.trim();
    if (!trimmedName) return;

    const keywordList = keywords.split(",").map((k) => k.trim()).filter(Boolean);
    const existingNames = (allCategories ?? [])
      .filter((c) => c.id !== category?.id)
      .map((c) => c.name);
    setGenerating(true);
    setGenerateError(null);
    promptManuallyEdited.current = false;

    try {
      const generated = await categoriesApi.generatePrompt(trimmedName, keywordList, PROMPT_MAX_CHARS, existingNames);
      setPrompt(generated);
    } catch {
      setGenerateError(t("categoryForm.generationFailed"));
      setPrompt(buildFallbackPrompt(trimmedName, keywords));
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const keywordList = keywords.split(",").map((k) => k.trim()).filter(Boolean);
    const data: CategoryCreate = {
      name,
      color,
      keywords: keywordList,
      prompt: prompt || null,
      taxonomy_id: taxonomyId ?? null,
    };
    if (isEdit && category) {
      await update.mutateAsync({ id: category.id, data });
    } else {
      await create.mutateAsync(data);
    }
    onClose();
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {taxonomyId && (
        <div className="flex items-center gap-1.5 text-xs text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20 rounded px-2.5 py-1.5">
          <span className="font-medium">IPTC</span>
          <span className="text-indigo-400 dark:text-indigo-500">·</span>
          <span className="font-mono opacity-75">{taxonomyId}</span>
        </div>
      )}
      <div>
        <label className="block text-sm font-medium mb-1">{t("categoryForm.name")}</label>
        <input
          className={inputClass}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder={t("categoryForm.namePlaceholder")}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">{t("categoryForm.color")}</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {PRESET_COLORS.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setColor(c)}
              style={{ backgroundColor: c }}
              className={cn(
                "w-7 h-7 rounded-full border-2 transition-transform",
                color === c ? "border-gray-900 dark:border-white scale-110" : "border-transparent"
              )}
            />
          ))}
        </div>
        <input
          type="color"
          value={color}
          onChange={(e) => setColor(e.target.value)}
          className="w-full h-8 rounded cursor-pointer border border-gray-300 dark:border-gray-600"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">{t("categoryForm.keywords")}</label>
        <input
          className={inputClass}
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          placeholder={t("categoryForm.keywordsPlaceholder")}
        />
        <p className="text-xs text-gray-400 mt-1">{t("categoryForm.keywordsHint")}</p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="block text-sm font-medium">{t("categoryForm.prompt")}</label>
          <button
            type="button"
            onClick={regeneratePrompt}
            disabled={generating || !name.trim()}
            className={cn(
              "flex items-center gap-1 text-xs transition-colors",
              generating || !name.trim()
                ? "text-gray-300 dark:text-gray-600 cursor-not-allowed"
                : "text-indigo-500 hover:text-indigo-700 dark:hover:text-indigo-300"
            )}
            title={t("categoryForm.generateWithLLM")}
          >
            <RefreshCw size={12} className={generating ? "animate-spin" : ""} />
            {generating ? t("categoryForm.generating") : t("categoryForm.regenerate")}
          </button>
        </div>
        <textarea
          className={cn(inputClass, "resize-none", generating && "opacity-50")}
          rows={3}
          maxLength={PROMPT_MAX_CHARS}
          value={generating ? t("categoryForm.generatingText") : prompt}
          onChange={(e) => handlePromptChange(e.target.value)}
          readOnly={generating}
          placeholder={t("categoryForm.promptPlaceholder")}
        />
        <div className="flex items-center justify-between mt-1">
          <p className="text-xs text-gray-400">{t("categoryForm.promptHint")}</p>
          {!generating && (
            <span className={cn(
              "text-xs tabular-nums shrink-0 ml-2",
              prompt.length >= PROMPT_MAX_CHARS
                ? "text-red-500"
                : prompt.length >= PROMPT_MAX_CHARS * 0.9
                ? "text-amber-500"
                : "text-gray-400"
            )}>
              {prompt.length}/{PROMPT_MAX_CHARS}
            </span>
          )}
        </div>
        {generateError && (
          <p className="text-xs text-amber-500 mt-1">{generateError}</p>
        )}
      </div>

      <div className="flex gap-2 mt-2">
        <button
          type="button"
          onClick={onClose}
          className="flex-1 px-4 py-2 text-sm font-medium rounded bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 transition-colors"
        >
          {t("common.cancel")}
        </button>
        <button
          type="submit"
          disabled={generating}
          className="flex-1 px-4 py-2 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {isEdit ? t("common.save") : t("categoryForm.addCategory")}
        </button>
      </div>
    </form>
  );
}

const inputClass =
  "w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";
