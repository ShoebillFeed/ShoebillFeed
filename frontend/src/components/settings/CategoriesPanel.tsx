import { useState, useRef } from "react";
import { Plus, Trash2, Pencil, RotateCcw, Download, Upload } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useCategories, useDeleteCategory, useResetWeights, useSetManualWeight, useImportCategories, useUpdateCategory } from "../../hooks/useCategories";
import { categoriesApi } from "../../api/categories";
import CategoryForm from "./CategoryForm";
import TaxonomyBrowser from "./TaxonomyBrowser";
import { Accordion } from "./Accordion";
import type { Category } from "../../types/category";
import type { TaxonomyNode } from "./iptcTaxonomy";
import { findNode } from "./iptcTaxonomy";

type PendingNode = { node: TaxonomyNode; color: string };

function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function CategoriesPanel() {
  const { t } = useTranslation();
  const { data: categories, isLoading } = useCategories();
  const deleteCategory = useDeleteCategory();
  const resetWeights = useResetWeights();
  const importCategories = useImportCategories();
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [pendingNode, setPendingNode] = useState<PendingNode | null>(null);

  const existingNames = new Set((categories ?? []).map((c) => c.name.toLowerCase()));
  const existingTaxonomyIds = new Set(
    (categories ?? []).map((c) => c.taxonomy_id).filter(Boolean) as string[]
  );

  const handleTaxonomyAdd = (node: TaxonomyNode, color: string) => {
    setShowCustomForm(false);
    setEditing(null);
    setPendingNode({ node, color });
  };

  const handleExport = async () => {
    const data = await categoriesApi.export();
    downloadJson(data, "categories.json");
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target?.result as string);
        importCategories.mutate(data);
      } catch {
        alert(t("categories.invalidJson"));
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  return (
    <div>
      <Accordion
        title={t("categories.title")}
        defaultOpen
        action={
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={handleExport}
              title={t("categories.exportTitle")}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
            >
              <Download size={13} /> {t("common.export")}
            </button>
            <label
              title={t("categories.importTitle")}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400 cursor-pointer"
            >
              <Upload size={13} /> {t("common.import")}
              <input type="file" accept=".json" className="hidden" onChange={handleImport} />
            </label>
            <button
              onClick={() => {
                if (confirm(t("categories.resetWeightsConfirm")))
                  resetWeights.mutate();
              }}
              title={t("categories.resetWeights")}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
            >
              <RotateCcw size={13} /> {t("categories.resetWeights")}
            </button>
            <button
              onClick={() => {
                setPendingNode(null);
                setEditing(null);
                setShowCustomForm((v) => !v);
              }}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
            >
              <Plus size={13} /> {t("categories.addCustom")}
            </button>
          </div>
        }
      >
        {/* Custom create form */}
        {showCustomForm && !editing && (
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
            <h3 className="font-medium text-sm mb-3">{t("categories.addNewCategory")}</h3>
            <CategoryForm
              onClose={() => setShowCustomForm(false)}
            />
          </div>
        )}

        {/* Taxonomy node quick-add form */}
        {pendingNode && !editing && (
          <div className="p-4 border border-indigo-200 dark:border-indigo-800 rounded-lg bg-indigo-50/40 dark:bg-indigo-900/10">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="font-medium text-sm text-indigo-700 dark:text-indigo-300">
                {t("categories.addFromTaxonomy")}
              </h3>
            </div>
            <CategoryForm
              taxonomyName={pendingNode.node.name}
              taxonomyId={pendingNode.node.id}
              defaultColor={pendingNode.color}
              defaultKeywords={pendingNode.node.keywords}
              defaultPrompt={pendingNode.node.prompt}
              onClose={() => setPendingNode(null)}
            />
          </div>
        )}

        {isLoading && <p className="text-sm text-gray-400">{t("common.loading")}</p>}

        {/* Category list */}
        <div className="flex flex-col gap-2">
          {categories?.map((cat) =>
            editing?.id === cat.id ? (
              <div key={cat.id} className="p-4 border border-indigo-200 dark:border-indigo-800 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <h3 className="font-medium text-sm mb-3 text-indigo-600 dark:text-indigo-400">
                  {t("categories.editingCategory", { name: cat.name })}
                </h3>
                <CategoryForm
                  category={cat}
                  isTaxonomy={Boolean(cat.taxonomy_id)}
                  onClose={() => setEditing(null)}
                />
              </div>
            ) : (
              <CategoryRow
                key={cat.id}
                cat={cat}
                onEdit={() => { setEditing(cat); setPendingNode(null); setShowCustomForm(false); }}
                onDelete={() => {
                  if (confirm(t("categories.deleteConfirm", { name: cat.name })))
                    deleteCategory.mutate(cat.id);
                }}
              />
            )
          )}

          {categories?.length === 0 && !isLoading && (
            <p className="text-sm text-gray-400 text-center py-8">{t("categories.empty")}</p>
          )}
        </div>
      </Accordion>

      <Accordion title={t("categories.taxonomyTitle")} description={t("categories.taxonomyDesc")}>
        <TaxonomyBrowser
          onAddNode={handleTaxonomyAdd}
          existingTaxonomyIds={existingTaxonomyIds}
          existingNames={existingNames}
        />
      </Accordion>
    </div>
  );
}

function CategoryRow({
  cat,
  onEdit,
  onDelete,
}: {
  cat: Category;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const { t } = useTranslation();
  const setManualWeight = useSetManualWeight();
  const updateCategory = useUpdateCategory();
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [localWeight, setLocalWeight] = useState(cat.weight?.manual_weight ?? 1.0);

  const handleSliderChange = (value: number) => {
    setLocalWeight(value);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      setManualWeight.mutate({ id: cat.id, manual_weight: value });
    }, 400);
  };

  const handleToggleActive = () => {
    updateCategory.mutate({ id: cat.id, data: { is_active: !cat.is_active } });
  };

  const learnedWeight = cat.weight?.weight ?? 1.0;
  const effectiveWeight = learnedWeight * localWeight;
  const inactive = !cat.is_active;

  const taxonomyNode = cat.taxonomy_id ? findNode(cat.taxonomy_id) : null;

  return (
    <div className={`p-3 bg-white dark:bg-gray-900 border rounded-lg transition-opacity ${inactive ? "opacity-50 border-gray-100 dark:border-gray-800" : "border-gray-200 dark:border-gray-700"}`}>
      <div className="flex items-center gap-3">
        <div
          className="w-4 h-4 rounded-full shrink-0"
          style={{ backgroundColor: inactive ? "#9ca3af" : cat.color }}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className={`text-sm font-medium ${inactive ? "text-gray-400 dark:text-gray-500" : ""}`}>
              {cat.name}
            </span>
            {cat.taxonomy_id ? (
              <span
                className="text-[10px] font-medium px-1 py-0.5 rounded bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 leading-none"
                title={taxonomyNode ? `IPTC: ${taxonomyNode.name} (${cat.taxonomy_id})` : `IPTC ${cat.taxonomy_id}`}
              >
                Default
              </span>
            ) : (
              <span className="text-[10px] font-medium px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 leading-none">
                Custom
              </span>
            )}
          </div>
          <p className="text-xs text-gray-400">
            {t("categories.articles", { count: cat.item_count })}
            {cat.weight?.total_marked ? ` · ${t("categories.starMarks", { count: cat.weight.total_marked })}` : ""}
          </p>
          {cat.keywords.length > 0 && (
            <p className="text-xs text-gray-400 truncate">{cat.keywords.join(", ")}</p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            role="switch"
            aria-checked={cat.is_active}
            title={cat.is_active ? t("categories.disable") : t("categories.enable")}
            onClick={handleToggleActive}
            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none ${cat.is_active ? "bg-indigo-600" : "bg-gray-300 dark:bg-gray-600"}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${cat.is_active ? "translate-x-4" : "translate-x-0"}`}
            />
          </button>
          <button
            title={t("common.edit")}
            onClick={onEdit}
            className="p-1.5 rounded text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Pencil size={14} />
          </button>
          <button
            title={t("common.delete")}
            onClick={onDelete}
            className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {cat.is_active && (
        <>
          <div className="mt-2.5 flex items-center gap-3">
            <span className="text-xs text-gray-400 w-12 shrink-0">{t("categories.weight")}</span>
            <input
              type="range"
              min={0}
              max={5}
              step={0.1}
              value={localWeight}
              onChange={(e) => handleSliderChange(parseFloat(e.target.value))}
              className="flex-1 h-1.5 accent-indigo-600 cursor-pointer"
            />
            <span className="text-xs font-mono text-gray-500 dark:text-gray-400 w-20 shrink-0 text-right">
              ×{localWeight.toFixed(1)}
              <span className="text-gray-400 dark:text-gray-600"> = {effectiveWeight.toFixed(2)}</span>
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-0.5 pl-[3.25rem]">
            {t("categories.manualLearned", { weight: learnedWeight.toFixed(2) })}
          </p>
        </>
      )}
    </div>
  );
}
