import { useState, useMemo } from "react";
import { ChevronRight, Plus, Check, Search } from "lucide-react";
import { useTranslation } from "react-i18next";
import { IPTC_TAXONOMY, getNodeColor, flattenTaxonomy } from "./iptcTaxonomy";
import type { TaxonomyNode } from "./iptcTaxonomy";
import { cn } from "../../lib/utils";

interface Props {
  onAddNode: (node: TaxonomyNode, color: string) => void;
  existingTaxonomyIds: Set<string>;
  existingNames: Set<string>;
  disabled?: boolean;
}

function nodeMatchesSearch(node: TaxonomyNode, q: string): boolean {
  return node.name.toLowerCase().includes(q);
}

function hasMatchingDescendant(node: TaxonomyNode, q: string): boolean {
  if (nodeMatchesSearch(node, q)) return true;
  return node.children?.some((c) => hasMatchingDescendant(c, q)) ?? false;
}

function TreeNode({
  node,
  depth,
  searchQuery,
  expanded,
  onToggle,
  onAdd,
  existingTaxonomyIds,
  existingNames,
  disabled,
}: {
  node: TaxonomyNode;
  depth: number;
  searchQuery: string;
  expanded: Set<string>;
  onToggle: (id: string) => void;
  onAdd: (node: TaxonomyNode) => void;
  existingTaxonomyIds: Set<string>;
  existingNames: Set<string>;
  disabled?: boolean;
}) {
  const { t } = useTranslation();
  const hasChildren = Boolean(node.children?.length);
  const isExpanded = expanded.has(node.id);
  const isAdded = existingTaxonomyIds.has(node.id) || existingNames.has(node.name.toLowerCase());
  const color = getNodeColor(node.id);

  const q = searchQuery.toLowerCase();
  const visible = !q || hasMatchingDescendant(node, q);
  if (!visible) return null;

  const matchesSelf = !q || nodeMatchesSearch(node, q);
  const visibleChildren = node.children?.filter((c) => !q || hasMatchingDescendant(c, q)) ?? [];

  return (
    <div>
      <div
        className={cn(
          "group flex items-center gap-1 py-1 px-1 rounded transition-colors",
          "hover:bg-gray-100 dark:hover:bg-gray-800/60",
          !matchesSelf && q ? "opacity-60" : "",
        )}
        style={{ paddingLeft: `${depth * 14 + 4}px` }}
      >
        <button
          type="button"
          onClick={() => hasChildren && onToggle(node.id)}
          className={cn(
            "w-4 h-4 flex items-center justify-center shrink-0 transition-transform text-gray-400",
            hasChildren ? "cursor-pointer hover:text-gray-600 dark:hover:text-gray-300" : "cursor-default opacity-0",
            isExpanded ? "rotate-90" : "",
          )}
          tabIndex={hasChildren ? 0 : -1}
          aria-expanded={hasChildren ? isExpanded : undefined}
        >
          <ChevronRight size={12} />
        </button>

        <button
          type="button"
          onClick={() => hasChildren && onToggle(node.id)}
          className={cn(
            "flex-1 text-left text-sm leading-tight min-w-0 truncate",
            hasChildren ? "cursor-pointer" : "cursor-default",
            depth === 0 ? "font-medium text-gray-900 dark:text-gray-100" : "text-gray-700 dark:text-gray-300",
            q && matchesSelf ? "text-indigo-700 dark:text-indigo-300 font-medium" : "",
          )}
        >
          <span
            className="inline-block w-2 h-2 rounded-full mr-1.5 shrink-0 align-middle"
            style={{ backgroundColor: color }}
          />
          {node.name}
        </button>

        <button
          type="button"
          title={isAdded ? t("categories.presetsAlreadyAdded") : t("categories.addFromTaxonomy")}
          onClick={() => !isAdded && !disabled && onAdd(node)}
          disabled={isAdded || disabled}
          className={cn(
            "p-1 rounded shrink-0 transition-colors",
            "opacity-50 group-hover:opacity-100 focus:opacity-100",
            isAdded
              ? "text-gray-300 dark:text-gray-600 cursor-default"
              : "text-indigo-500 hover:text-indigo-700 dark:hover:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/30",
          )}
        >
          {isAdded ? <Check size={13} /> : <Plus size={13} />}
        </button>
      </div>

      {hasChildren && (isExpanded || Boolean(q)) && (
        <div>
          {visibleChildren.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              searchQuery={searchQuery}
              expanded={expanded}
              onToggle={onToggle}
              onAdd={onAdd}
              existingTaxonomyIds={existingTaxonomyIds}
              existingNames={existingNames}
              disabled={disabled}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function TaxonomyBrowser({ onAddNode, existingTaxonomyIds, existingNames, disabled }: Props) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");

  const toggleNode = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const matchCount = useMemo(() => {
    if (!search) return 0;
    const q = search.toLowerCase();
    return flattenTaxonomy().filter((n) => nodeMatchesSearch(n, q)).length;
  }, [search]);

  return (
    <div>
      <div className="relative mb-2">
        <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
        <input
          type="text"
          placeholder={t("categories.taxonomySearch")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-8 pr-3 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        {search && (
          <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-gray-400">
            {matchCount}
          </span>
        )}
      </div>

      <div className="max-h-80 overflow-y-auto pr-0.5 border border-gray-200 dark:border-gray-700 rounded-lg p-1.5">
        {IPTC_TAXONOMY.map((node) => (
          <TreeNode
            key={node.id}
            node={node}
            depth={0}
            searchQuery={search}
            expanded={expanded}
            onToggle={toggleNode}
            onAdd={(n) => onAddNode(n, getNodeColor(n.id))}
            existingTaxonomyIds={existingTaxonomyIds}
            existingNames={existingNames}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
}
