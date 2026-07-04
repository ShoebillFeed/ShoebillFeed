import { ChevronDown, ChevronUp } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useSources } from "../../hooks/useSources";
import { useFilterStore } from "../../stores/filterStore";
import { cn } from "../../lib/utils";

const TYPE_ICON: Record<string, string> = {
  rss: "📰",
  reddit: "🔴",
  youtube: "▶️",
  email: "✉️",
};

const CHIP_BASE = "px-3 py-2 rounded-full text-xs font-medium border transition-colors";
const CHIP_ACTIVE = "bg-gray-800 text-white border-gray-800 dark:bg-gray-200 dark:text-gray-900";
const CHIP_INACTIVE = "bg-white text-gray-600 border-gray-300 hover:border-gray-400 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600";

export default function SourceFilter() {
  const { t } = useTranslation();
  const { data: sources } = useSources();
  const { selectedSourceIds, toggleSource, clearSources, sourceFilterExpanded: expanded, setSourceFilterExpanded: setExpanded } = useFilterStore();

  const active = (sources?.filter((s) => s.is_active) ?? []).sort((a, b) => a.name.localeCompare(b.name));
  if (active.length === 0) return null;

  const selected = active.filter((s) => selectedSourceIds.includes(s.id));
  const unselected = active.filter((s) => !selectedSourceIds.includes(s.id));
  const hasSelection = selected.length > 0;
  const showToggle = unselected.length > 0 || expanded;

  return (
    <div className="flex flex-wrap gap-1.5 mb-3 items-center">
      {expanded && (
        <button
          onClick={clearSources}
          className={cn(CHIP_BASE, !hasSelection ? CHIP_ACTIVE : CHIP_INACTIVE)}
        >
          {t("filters.allSources")}
        </button>
      )}

      {selected.map((source) => (
        <button
          key={source.id}
          onClick={() => toggleSource(source.id)}
          className={cn(CHIP_BASE, CHIP_ACTIVE)}
        >
          {TYPE_ICON[source.source_type] ?? "📄"} {source.name}
        </button>
      ))}

      {expanded && unselected.map((source) => (
        <button
          key={source.id}
          onClick={() => toggleSource(source.id)}
          className={cn(CHIP_BASE, CHIP_INACTIVE)}
        >
          {TYPE_ICON[source.source_type] ?? "📄"} {source.name}
        </button>
      ))}

      {showToggle && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border transition-colors text-gray-400 border-gray-200 hover:text-gray-600 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600 dark:text-gray-500 dark:hover:text-gray-400"
        >
          {expanded ? (
            <ChevronUp size={11} />
          ) : (
            <>
              {!hasSelection && <span>{t("filters.sources")}</span>}
              {hasSelection && unselected.length > 0 && <span>+{unselected.length}</span>}
              <ChevronDown size={11} />
            </>
          )}
        </button>
      )}
    </div>
  );
}
