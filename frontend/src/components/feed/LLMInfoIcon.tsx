import { Info } from "lucide-react";
import { cn } from "../../lib/utils";

interface Props {
  provider: string | null;
  model: string | null;
  fields?: string;
  hasImage?: boolean;
}

export function LLMInfoIcon({ provider, model, fields = "Abstract · Keywords · Categories", hasImage = false }: Props) {
  if (!provider) return null;

  const label = model ? `${provider} · ${model}` : provider;

  return (
    <span className="relative group/llm inline-flex items-center">
      <Info
        size={11}
        className={cn(
          "cursor-default",
          hasImage ? "text-white/40 group-hover/llm:text-white/70" : "text-gray-300 dark:text-gray-600 group-hover/llm:text-gray-400 dark:group-hover/llm:text-gray-400"
        )}
      />
      <span className={cn(
        "pointer-events-none absolute z-50 bottom-full right-0 mb-1.5",
        "w-max max-w-52 rounded-md px-2.5 py-1.5 text-xs shadow-lg",
        "bg-gray-900 text-white dark:bg-gray-700",
        "opacity-0 group-hover/llm:opacity-100 transition-opacity duration-150",
      )}>
        <span className="block font-medium">{label}</span>
        <span className="block text-gray-400 mt-0.5">{fields}</span>
      </span>
    </span>
  );
}
