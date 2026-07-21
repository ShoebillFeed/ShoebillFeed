import { cn } from "../../lib/utils";

export function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-4">
      <div className="mb-3">
        <h4 className="font-medium text-sm text-gray-800 dark:text-gray-200">{title}</h4>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
        )}
      </div>
      <div className="border-t border-gray-200 dark:border-gray-700 pt-3 flex flex-col gap-3">
        {children}
      </div>
    </div>
  );
}

export function Field({
  label,
  description,
  stacked,
  children,
}: {
  label: string;
  description?: string;
  stacked?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={stacked ? "flex flex-col gap-2" : "flex items-start gap-4"}>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{label}</p>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}

export function Toggle({
  checked,
  onChange,
  disabled,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500",
        checked ? "bg-indigo-600" : "bg-gray-200 dark:bg-gray-700",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <span
        className={cn(
          "pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform transition duration-200",
          checked ? "translate-x-5" : "translate-x-0"
        )}
      />
    </button>
  );
}

export function ScoreSlider({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center gap-3 w-full max-w-xs">
      <input
        type="range"
        min={1}
        max={10}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 h-4 appearance-none bg-gray-200 dark:bg-gray-700 rounded-full cursor-pointer accent-indigo-600"
      />
      <span className="text-sm font-medium w-10 text-right shrink-0 text-gray-800 dark:text-gray-200">
        {value}/10
      </span>
    </div>
  );
}
