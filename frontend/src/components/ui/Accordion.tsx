import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

export function Accordion({
  title,
  description,
  defaultOpen = false,
  action,
  children,
}: {
  title: string;
  description?: string;
  defaultOpen?: boolean;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden mb-3">
      <div className="bg-gray-50 dark:bg-gray-800/60 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="w-full flex items-center justify-between px-4 py-3 text-left"
        >
          <div className="min-w-0 pr-3">
            <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">{title}</h3>
            {description && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
            )}
          </div>
          {open ? (
            <ChevronDown size={16} className="text-gray-400 shrink-0" />
          ) : (
            <ChevronRight size={16} className="text-gray-400 shrink-0" />
          )}
        </button>
        {action && (
          <div className="px-4 pb-3 flex flex-wrap gap-2" onClick={(e) => e.stopPropagation()}>
            {action}
          </div>
        )}
      </div>
      {open && (
        <div className="px-4 py-4 flex flex-col gap-4 border-t border-gray-200 dark:border-gray-700">
          {children}
        </div>
      )}
    </div>
  );
}
