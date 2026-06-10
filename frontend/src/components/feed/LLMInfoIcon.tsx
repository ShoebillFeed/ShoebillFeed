import { useEffect, useRef, useState } from "react";
import { Info } from "lucide-react";
import { cn } from "../../lib/utils";

interface Props {
  provider: string | null;
  model: string | null;
  fields?: string;
  hasImage?: boolean;
}

export function LLMInfoIcon({ provider, model, fields = "Abstract · Keywords · Categories", hasImage = false }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleOutside = (e: Event) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutside);
    document.addEventListener("touchstart", handleOutside);
    return () => {
      document.removeEventListener("mousedown", handleOutside);
      document.removeEventListener("touchstart", handleOutside);
    };
  }, [open]);

  if (!provider) return null;

  const label = model ? `${provider} · ${model}` : provider;

  return (
    <span ref={ref} className="relative group/llm inline-flex items-center">
      <button
        type="button"
        aria-label="LLM info"
        onClick={(e) => {
          e.stopPropagation();
          e.preventDefault();
          setOpen((v) => !v);
        }}
        className={cn(
          "inline-flex items-center cursor-pointer",
          hasImage ? "text-white/40 group-hover/llm:text-white/70" : "text-gray-400 dark:text-gray-500 group-hover/llm:text-gray-500 dark:group-hover/llm:text-gray-400"
        )}
      >
        <Info size={11} />
      </button>
      <span className={cn(
        "pointer-events-none absolute z-50 bottom-full right-0 mb-1.5",
        "w-max max-w-52 rounded-md px-2.5 py-1.5 text-xs shadow-lg",
        "bg-gray-900 text-white dark:bg-gray-700",
        "transition-opacity duration-150",
        open ? "opacity-100" : "opacity-0 group-hover/llm:opacity-100",
      )}>
        <span className="block font-medium">{label}</span>
        <span className="block text-gray-400 mt-0.5">{fields}</span>
      </span>
    </span>
  );
}
