import { Zap, TrendingUp, Clock, Bookmark } from "lucide-react";
import { cn } from "../../lib/utils";
import type { FeedTab } from "../../types/news";

const TABS: { id: FeedTab; label: string; shortLabel: string; icon: typeof Clock }[] = [
  { id: "newest", label: "Newest", shortLabel: "New", icon: Clock },
  { id: "relevant", label: "Most Relevant", shortLabel: "Rel.", icon: Zap },
  { id: "impact", label: "Most Impact", shortLabel: "Impact", icon: TrendingUp },
  { id: "read_later", label: "Read Later", shortLabel: "Later", icon: Bookmark },
];

export default function FeedTabs({
  active,
  onChange,
}: {
  active: FeedTab;
  onChange: (tab: FeedTab) => void;
}) {
  return (
    <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-4">
      {TABS.map(({ id, label, shortLabel, icon: Icon }) => (
        <button
          key={id}
          onClick={() => onChange(id)}
          className={cn(
            "flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors",
            active === id
              ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
              : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          )}
        >
          <Icon size={15} />
          <span className="hidden sm:inline">{label}</span>
          <span className="sm:hidden">{shortLabel}</span>
        </button>
      ))}
    </div>
  );
}
