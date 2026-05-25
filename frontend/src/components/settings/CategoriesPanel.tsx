import { useState, useRef } from "react";
import { Plus, Trash2, Pencil, RotateCcw } from "lucide-react";
import { useCategories, useDeleteCategory, useResetWeights, useSetManualWeight } from "../../hooks/useCategories";
import CategoryForm from "./CategoryForm";
import type { Category } from "../../types/category";

export default function CategoriesPanel() {
  const { data: categories, isLoading } = useCategories();
  const deleteCategory = useDeleteCategory();
  const resetWeights = useResetWeights();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100">Categories</h2>
        <div className="flex gap-2">
          <button
            onClick={() => {
              if (confirm("Reset all category weights to 1.0? This will re-start relevance learning."))
                resetWeights.mutate();
            }}
            title="Reset relevance weights"
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-600 dark:text-gray-400"
          >
            <RotateCcw size={14} /> Reset weights
          </button>
          <button
            onClick={() => { setEditing(null); setShowForm(true); }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
          >
            <Plus size={14} /> Add Category
          </button>
        </div>
      </div>

      {(showForm || editing) && (
        <div className="mb-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
          <h3 className="font-medium text-sm mb-3">{editing ? "Edit Category" : "Add New Category"}</h3>
          <CategoryForm
            category={editing ?? undefined}
            onClose={() => { setShowForm(false); setEditing(null); }}
          />
        </div>
      )}

      {isLoading && <p className="text-sm text-gray-400">Loading…</p>}

      <div className="flex flex-col gap-2">
        {categories?.map((cat) => (
          <CategoryRow
            key={cat.id}
            cat={cat}
            onEdit={() => { setEditing(cat); setShowForm(false); }}
            onDelete={() => {
              if (confirm(`Delete category "${cat.name}"? Articles will be uncategorized.`))
                deleteCategory.mutate(cat.id);
            }}
          />
        ))}

        {categories?.length === 0 && !isLoading && (
          <p className="text-sm text-gray-400 text-center py-8">
            No categories yet. Add some to auto-classify your articles.
          </p>
        )}
      </div>
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
  const setManualWeight = useSetManualWeight();
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [localWeight, setLocalWeight] = useState(cat.weight?.manual_weight ?? 1.0);

  const handleSliderChange = (value: number) => {
    setLocalWeight(value);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      setManualWeight.mutate({ id: cat.id, manual_weight: value });
    }, 400);
  };

  const learnedWeight = cat.weight?.weight ?? 1.0;
  const effectiveWeight = learnedWeight * localWeight;

  return (
    <div className="p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
      <div className="flex items-center gap-3">
        <div
          className="w-4 h-4 rounded-full shrink-0"
          style={{ backgroundColor: cat.color }}
        />
        <div className="flex-1 min-w-0">
          <span className="text-sm font-medium">{cat.name}</span>
          <p className="text-xs text-gray-400">
            {cat.item_count} articles
            {cat.weight?.total_marked ? ` · ${cat.weight.total_marked} ★ marks` : ""}
          </p>
          {cat.keywords.length > 0 && (
            <p className="text-xs text-gray-400 truncate">{cat.keywords.join(", ")}</p>
          )}
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <button
            title="Edit"
            onClick={onEdit}
            className="p-1.5 rounded text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Pencil size={14} />
          </button>
          <button
            title="Delete"
            onClick={onDelete}
            className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Weight slider */}
      <div className="mt-2.5 flex items-center gap-3">
        <span className="text-xs text-gray-400 w-12 shrink-0">Weight</span>
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
        manual × learned {learnedWeight.toFixed(2)}
      </p>
    </div>
  );
}
