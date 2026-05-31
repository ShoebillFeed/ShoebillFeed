import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useCategories } from "../../hooks/useCategories";
import { useFilterStore } from "../../stores/filterStore";
import { cn } from "../../lib/utils";

const CHIP_BASE = "px-3 py-1 rounded-full text-xs font-medium border transition-colors";
const CHIP_INACTIVE = "bg-white text-gray-600 border-gray-300 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600";

export default function CategoryFilter() {
  const { data: categories } = useCategories();
  const { selectedCategoryIds, toggleCategory, clearCategories } = useFilterStore();
  const [expanded, setExpanded] = useState(false);

  if (!categories?.length) return null;

  const selected = categories.filter((c) => selectedCategoryIds.includes(c.id));
  const unselected = categories.filter((c) => !selectedCategoryIds.includes(c.id));
  const hasSelection = selected.length > 0;
  const showToggle = unselected.length > 0 || expanded;

  return (
    <div className="flex flex-wrap gap-1.5 mb-3 items-center">
      {expanded && (
        <button
          onClick={clearCategories}
          className={cn(
            CHIP_BASE,
            !hasSelection
              ? "bg-gray-800 text-white border-gray-800 dark:bg-gray-200 dark:text-gray-900"
              : CHIP_INACTIVE,
          )}
        >
          All
        </button>
      )}

      {selected.map((cat) => (
        <button
          key={cat.id}
          onClick={() => toggleCategory(cat.id)}
          style={{ backgroundColor: cat.color, borderColor: cat.color }}
          className={cn(CHIP_BASE, "text-white")}
        >
          {cat.name}
          {cat.item_count > 0 && <span className="ml-1.5 opacity-70">{cat.item_count}</span>}
        </button>
      ))}

      {expanded && unselected.map((cat) => (
        <button
          key={cat.id}
          onClick={() => toggleCategory(cat.id)}
          className={cn(CHIP_BASE, CHIP_INACTIVE)}
        >
          {cat.name}
          {cat.item_count > 0 && <span className="ml-1.5 opacity-70">{cat.item_count}</span>}
        </button>
      ))}

      {showToggle && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border transition-colors text-gray-400 border-gray-200 hover:text-gray-600 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600 dark:text-gray-500 dark:hover:text-gray-400"
        >
          {expanded ? (
            <ChevronUp size={11} />
          ) : (
            <>
              {!hasSelection && <span>Categories</span>}
              {hasSelection && unselected.length > 0 && <span>+{unselected.length}</span>}
              <ChevronDown size={11} />
            </>
          )}
        </button>
      )}
    </div>
  );
}
