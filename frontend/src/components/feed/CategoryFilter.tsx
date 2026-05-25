import { useCategories } from "../../hooks/useCategories";
import { useFilterStore } from "../../stores/filterStore";
import { cn } from "../../lib/utils";

export default function CategoryFilter() {
  const { data: categories } = useCategories();
  const { selectedCategoryIds, toggleCategory, clearCategories } = useFilterStore();

  if (!categories?.length) return null;

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <button
        onClick={clearCategories}
        className={cn(
          "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
          selectedCategoryIds.length === 0
            ? "bg-gray-800 text-white border-gray-800 dark:bg-gray-200 dark:text-gray-900"
            : "bg-white text-gray-600 border-gray-300 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600"
        )}
      >
        All
      </button>
      {categories.map((cat) => {
        const active = selectedCategoryIds.includes(cat.id);
        return (
          <button
            key={cat.id}
            onClick={() => toggleCategory(cat.id)}
            style={active ? { backgroundColor: cat.color, borderColor: cat.color } : {}}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
              active
                ? "text-white"
                : "bg-white text-gray-600 border-gray-300 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600"
            )}
          >
            {cat.name}
            {cat.item_count > 0 && (
              <span className={cn("ml-1.5 opacity-70")}>
                {cat.item_count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
