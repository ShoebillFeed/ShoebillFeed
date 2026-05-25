import { useSources } from "../../hooks/useSources";
import { useFilterStore } from "../../stores/filterStore";
import { cn } from "../../lib/utils";

const TYPE_ICON: Record<string, string> = {
  rss: "📰",
  reddit: "🔴",
  youtube: "▶️",
  email: "✉️",
};

export default function SourceFilter() {
  const { data: sources } = useSources();
  const { selectedSourceIds, toggleSource, clearSources } = useFilterStore();

  const active = sources?.filter((s) => s.is_active) ?? [];
  if (active.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <button
        onClick={clearSources}
        className={cn(
          "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
          selectedSourceIds.length === 0
            ? "bg-gray-800 text-white border-gray-800 dark:bg-gray-200 dark:text-gray-900"
            : "bg-white text-gray-600 border-gray-300 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600"
        )}
      >
        All sources
      </button>
      {active.map((source) => {
        const isSelected = selectedSourceIds.includes(source.id);
        return (
          <button
            key={source.id}
            onClick={() => toggleSource(source.id)}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
              isSelected
                ? "bg-gray-800 text-white border-gray-800 dark:bg-gray-200 dark:text-gray-900"
                : "bg-white text-gray-600 border-gray-300 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600"
            )}
          >
            {TYPE_ICON[source.source_type] ?? "📄"} {source.name}
          </button>
        );
      })}
    </div>
  );
}
