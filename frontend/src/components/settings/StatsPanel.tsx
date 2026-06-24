import { useState, Component } from "react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import {
  AreaChart, Area,
  BarChart, Bar,
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";
import { format, parseISO } from "date-fns";
import { PauseCircle } from "lucide-react";
import {
  useActivityStats, useCategoryStats, useSourceStats,
  useWeightHistory, useSourceClusters,
  useKeywordClusterHistory, useKeywordClusterMap,
} from "../../hooks/useStats";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";

class ChartErrorBoundary extends Component<{ children: ReactNode }, { crashed: boolean }> {
  state = { crashed: false };
  static getDerivedStateFromError() { return { crashed: true }; }
  render() {
    if (this.state.crashed) {
      return <ChartCrashMessage />;
    }
    return this.props.children;
  }
}

const SOURCE_TYPE_LABEL: Record<string, string> = {
  rss: "RSS",
  reddit: "Reddit",
  youtube: "YouTube",
  email: "Email",
  mastodon: "Mastodon",
  arxiv: "arXiv",
  scholar: "Scholar",
};

const RANGE_OPTIONS = [
  { label: "7 d", days: 7 },
  { label: "30 d", days: 30 },
  { label: "90 d", days: 90 },
];

function RangePicker({ value, onChange }: { value: number; onChange: (d: number) => void }) {
  return (
    <div className="flex gap-1">
      {RANGE_OPTIONS.map(({ label, days }) => (
        <button
          key={days}
          onClick={() => onChange(days)}
          className={`px-2.5 py-1 text-xs rounded transition-colors ${
            value === days
              ? "bg-indigo-600 text-white"
              : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function ChartCard({
  title,
  description,
  children,
  action,
}: {
  title: string;
  description: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-start justify-between gap-4 mb-1">
        <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100">{title}</h3>
        {action}
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 leading-relaxed">{description}</p>
      <ChartErrorBoundary>{children}</ChartErrorBoundary>
    </div>
  );
}

function ChartCrashMessage() {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-center h-40 text-sm text-red-400 dark:text-red-500">
      {t("stats.chartFailed")}
    </div>
  );
}

function WeightHistoryEmpty() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center h-40 gap-1 text-sm text-gray-400">
      <span>{t("stats.noWeightHistory")}</span>
      <span className="text-xs">{t("stats.starToStart")}</span>
    </div>
  );
}

function Empty() {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-center h-40 text-sm text-gray-400">
      {t("stats.noData")}
    </div>
  );
}

function Loading() {
  const { t } = useTranslation();
  return <div className="flex items-center justify-center h-40 text-sm text-gray-400">{t("common.loading")}</div>;
}

// ── Shared tooltip shell ──────────────────────────────────────────────────────

function TooltipBox({ label, children }: { label?: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-xl px-3 py-2.5 text-xs min-w-[140px]">
      {label && (
        <p className="font-semibold text-gray-700 dark:text-gray-200 mb-2 pb-1.5 border-b border-gray-100 dark:border-gray-800">
          {label}
        </p>
      )}
      {children}
    </div>
  );
}

function TooltipRow({
  color,
  name,
  value,
}: {
  color?: string;
  name: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center justify-between gap-5 py-0.5">
      <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
        {color && (
          <span className="w-2 h-2 rounded-full shrink-0" style={{ background: color }} />
        )}
        {name}
      </span>
      <span className="font-medium tabular-nums text-gray-900 dark:text-gray-100">{value}</span>
    </div>
  );
}

// Mini progress bars used inside BySource and SourceClusters tooltips
function CategoryBars({
  entries,
  total,
}: {
  entries: Array<{ name: string; color: string; count: number }>;
  total: number;
}) {
  return (
    <div className="space-y-2 mt-2 pt-2 border-t border-gray-100 dark:border-gray-800 min-w-[180px]">
      {entries.map((e) => {
        const pct = total > 0 ? (e.count / total) * 100 : 0;
        return (
          <div key={e.name}>
            <div className="flex justify-between text-xs mb-0.5">
              <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: e.color }} />
                {e.name}
              </span>
              <span className="text-gray-500 dark:text-gray-400 ml-3 tabular-nums">{e.count}</span>
            </div>
            <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${pct}%`, background: e.color }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function fmtDate(iso: string, days: number) {
  try {
    return format(parseISO(iso), days <= 7 ? "EEE d" : "MMM d");
  } catch {
    return iso;
  }
}

const CURSOR_STYLE = { fill: "rgba(99,102,241,0.06)" };
const WRAPPER_STYLE = { background: "none", border: "none", boxShadow: "none", zIndex: 50 } as const;

// ── Reading activity ──────────────────────────────────────────────────────────

const ACTIVITY_SERIES = [
  { key: "fetched",  name: "Fetched",    color: "#818cf8", axis: "left"  },
  { key: "seen",     name: "Seen",       color: "#60a5fa", axis: "left"  },
  { key: "read",     name: "Read",       color: "#34d399", axis: "right" },
  { key: "relevant", name: "Liked ▲",    color: "#fbbf24", axis: "right" },
  { key: "disliked", name: "Disliked ▼", color: "#f87171", axis: "right" },
] as const;

function ActivityChart({ days }: { days: number }) {
  const { data, isLoading } = useActivityStats(days);
  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  const points = data.map((d) => ({ ...d, date: fmtDate(d.date, days) }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={points} margin={{ top: 4, right: 44, left: 0, bottom: 0 }}>
        <defs>
          {ACTIVITY_SERIES.map(({ key, color }) => (
            <linearGradient key={key} id={`g_${key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.25} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          allowDecimals={false}
          width={28}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          allowDecimals={false}
          width={28}
        />
        <Tooltip
          cursor={CURSOR_STYLE}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const ordered = ACTIVITY_SERIES.map((s) =>
              payload.find((p) => p.dataKey === s.key)
            ).filter(Boolean);
            return (
              <TooltipBox label={label as string}>
                {ordered.map((p) => (
                  <TooltipRow key={String(p!.dataKey)} color={p!.color} name={String(p!.name ?? "")} value={p!.value as number} />
                ))}
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
        {ACTIVITY_SERIES.map(({ key, name, color, axis }) => (
          <Area
            key={key}
            yAxisId={axis}
            type="monotone"
            dataKey={key}
            name={name}
            stroke={color}
            fill={`url(#g_${key})`}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ── Volume by category ────────────────────────────────────────────────────────

function ByCategoryChart({ days }: { days: number }) {
  const { data, isLoading } = useCategoryStats(days);
  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, data.length * 36 + 40)}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 32, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
        <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={90} />
        <Tooltip
          cursor={false}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload }) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload;
            return (
              <TooltipBox>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: d.color }} />
                  <span className="font-semibold text-gray-800 dark:text-gray-100">{d.name}</span>
                </div>
                <TooltipRow name="Articles" value={d.count} />
              </TooltipBox>
            );
          }}
        />
        <Bar dataKey="count" name="Articles" radius={[0, 4, 4, 0]}>
          {data.map((entry) => (
            <Cell key={entry.id} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Volume by source ──────────────────────────────────────────────────────────

function BySourceChart({ days }: { days: number }) {
  const { data, isLoading } = useSourceStats(days);
  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  const seenCatIds = new Set<string>();
  const allCategories: { id: string; name: string; color: string }[] = [];
  for (const source of data) {
    for (const cat of source.categories) {
      if (!seenCatIds.has(cat.id)) {
        seenCatIds.add(cat.id);
        allCategories.push({ id: cat.id, name: cat.name, color: cat.color });
      }
    }
  }

  const chartData = data.map((source) => {
    const row: Record<string, string | number> = {
      name: source.name,
      source_type: source.source_type,
      _total: source.total,
    };
    for (const cat of source.categories) {
      row[cat.name] = cat.count;
    }
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, data.length * 36 + 40)}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={120}
          tickFormatter={(name: string) => {
            const entry = data.find((d) => d.name === name);
            const type = entry ? (SOURCE_TYPE_LABEL[entry.source_type] ?? entry.source_type) : "";
            return type ? `${name} (${type})` : name;
          }}
        />
        <Tooltip
          cursor={false}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload }) => {
            if (!active || !payload?.[0]) return null;
            const row = payload[0].payload as Record<string, string | number>;
            const total = row._total as number;
            const typeLabel = SOURCE_TYPE_LABEL[row.source_type as string] ?? row.source_type as string;
            const entries = allCategories
              .map((cat) => ({ ...cat, count: (row[cat.name] ?? 0) as number }))
              .filter((e) => e.count > 0)
              .sort((a, b) => b.count - a.count);
            return (
              <TooltipBox>
                <div className="flex items-center justify-between gap-4 mb-1">
                  <span className="font-semibold text-gray-800 dark:text-gray-100">{row.name}</span>
                  <span className="text-gray-400 dark:text-gray-500">{typeLabel}</span>
                </div>
                <TooltipRow name="Total" value={total} />
                {entries.length > 0 && <CategoryBars entries={entries} total={total} />}
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
        {allCategories.map((cat, i) => (
          <Bar
            key={cat.id}
            dataKey={cat.name}
            stackId="stack"
            fill={cat.color}
            radius={i === allCategories.length - 1 ? [0, 4, 4, 0] : [0, 0, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Category weight history ───────────────────────────────────────────────────

function WeightHistoryChart({ days }: { days: number }) {
  const { data, isLoading } = useWeightHistory(days);
  if (isLoading) return <Loading />;
  if (!data?.length) {
    return <WeightHistoryEmpty />;
  }

  const allDates = Array.from(
    new Set(data.flatMap((c) => c.snapshots.map((s) => s.date.slice(0, 10))))
  ).sort();

  const chartData = allDates.map((date) => {
    const point: Record<string, string | number> = { date: fmtDate(date, days) };
    for (const cat of data) {
      const snap = [...cat.snapshots].reverse().find((s) => s.date.slice(0, 10) <= date);
      if (snap) point[cat.name] = snap.weight;
    }
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ stroke: "rgba(99,102,241,0.2)", strokeWidth: 1 }}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            return (
              <TooltipBox label={label as string}>
                {payload
                  .filter((p) => p.value !== undefined)
                  .sort((a, b) => (b.value as number) - (a.value as number))
                  .map((p) => (
                    <TooltipRow
                      key={String(p.name)}
                      color={p.color}
                      name={`${p.name ?? ""}`}
                      value={typeof p.value === "number" ? p.value.toFixed(3) : ""}
                    />
                  ))}
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, left: 0, width: "100%", textAlign: "center" }} />
        {data.map((cat) => (
          <Line key={cat.id} type="monotone" dataKey={cat.name} stroke={cat.color} strokeWidth={2} dot={false} connectNulls />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── Source cluster co-occurrence ──────────────────────────────────────────────

function SourceClustersChart({ days }: { days: number }) {
  const { data, isLoading } = useSourceClusters(days);
  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  // Collect unique categories across all pairs (stable order by first appearance)
  const seenCats = new Set<string>();
  const allCats: { name: string; color: string }[] = [];
  for (const pair of data) {
    for (const cat of pair.categories) {
      if (!seenCats.has(cat.name)) {
        seenCats.add(cat.name);
        allCats.push({ name: cat.name, color: cat.color });
      }
    }
  }

  const chartData = data.map((pair) => {
    const row: Record<string, string | number> = {
      pair: `${pair.source_a.name} + ${pair.source_b.name}`,
      _total: pair.total,
      _a_type: pair.source_a.source_type,
      _b_type: pair.source_b.source_type,
    };
    for (const cat of pair.categories) {
      row[cat.name] = cat.count;
    }
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, data.length * 40 + 40)}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
        <YAxis
          type="category"
          dataKey="pair"
          tick={{ fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          width={170}
        />
        <Tooltip
          cursor={false}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload }) => {
            if (!active || !payload?.[0]) return null;
            const row = payload[0].payload as Record<string, string | number>;
            const total = row._total as number;
            const aType = SOURCE_TYPE_LABEL[row._a_type as string] ?? row._a_type as string;
            const bType = SOURCE_TYPE_LABEL[row._b_type as string] ?? row._b_type as string;
            const [nameA, nameB] = (row.pair as string).split(" + ");
            const entries = allCats
              .map((cat) => ({ ...cat, count: (row[cat.name] ?? 0) as number }))
              .filter((e) => e.count > 0)
              .sort((a, b) => b.count - a.count);
            return (
              <TooltipBox>
                <div className="mb-1.5 pb-1.5 border-b border-gray-100 dark:border-gray-800">
                  <div className="font-semibold text-gray-800 dark:text-gray-100">{nameA}</div>
                  <div className="text-gray-400 dark:text-gray-500 text-xs">{aType}</div>
                  <div className="font-semibold text-gray-800 dark:text-gray-100 mt-1">{nameB}</div>
                  <div className="text-gray-400 dark:text-gray-500 text-xs">{bType}</div>
                </div>
                <TooltipRow name="Co-clustered" value={total} />
                {entries.length > 0 && <CategoryBars entries={entries} total={total} />}
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
        {allCats.map((cat, i) => (
          <Bar
            key={cat.name}
            dataKey={cat.name}
            stackId="stack"
            fill={cat.color}
            radius={i === allCats.length - 1 ? [0, 4, 4, 0] : [0, 0, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Keyword cluster score history ────────────────────────────────────────────

function KeywordClusterHistoryChart({ days }: { days: number }) {
  const { t } = useTranslation();
  const { data, isLoading } = useKeywordClusterHistory(days);
  if (isLoading) return <Loading />;
  if (!data?.length) {
    return (
      <div className="flex flex-col items-center justify-center h-40 gap-1 text-sm text-gray-400">
        <span>{t("stats.noClusterHistory")}</span>
        <span className="text-xs">{t("stats.clusterHistoryHint")}</span>
      </div>
    );
  }

  const hasSnapshots = data.some((c) => c.snapshots.length > 0);
  if (!hasSnapshots) {
    // We have clusters but no snapshot history yet — show current weights as a simple bar
    return (
      <ResponsiveContainer width="100%" height={Math.max(160, data.length * 32 + 40)}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 60, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} domain={[1, "auto"]} />
          <YAxis type="category" dataKey="cluster_label" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={130} />
          <Tooltip
            cursor={false}
            wrapperStyle={WRAPPER_STYLE}
            content={({ active, payload }) => {
              if (!active || !payload?.[0]) return null;
              const d = payload[0].payload as { cluster_label: string; category_name: string; category_color: string; current_weight: number };
              return (
                <TooltipBox>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: d.category_color }} />
                    <span className="font-semibold text-gray-800 dark:text-gray-100">{d.cluster_label}</span>
                  </div>
                  <TooltipRow name={d.category_name} value={d.current_weight.toFixed(3)} />
                </TooltipBox>
              );
            }}
          />
          <Bar dataKey="current_weight" name="Weight" radius={[0, 4, 4, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.category_color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  }

  const allDates = Array.from(
    new Set(data.flatMap((c) => c.snapshots.map((s) => s.date.slice(0, 10))))
  ).sort();

  const chartData = allDates.map((date) => {
    const point: Record<string, string | number> = { date: fmtDate(date, days) };
    for (const cluster of data) {
      const snap = [...cluster.snapshots].reverse().find((s) => s.date.slice(0, 10) <= date);
      if (snap) point[cluster.cluster_label] = snap.weight;
    }
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ stroke: "rgba(99,102,241,0.2)", strokeWidth: 1 }}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const sorted = [...payload]
              .filter((p) => p.value !== undefined)
              .sort((a, b) => (b.value as number) - (a.value as number));
            return (
              <TooltipBox label={label as string}>
                {sorted.map((p) => (
                  <TooltipRow key={String(p.name)} color={p.color} name={String(p.name)} value={typeof p.value === "number" ? p.value.toFixed(3) : ""} />
                ))}
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, left: 0, width: "100%", textAlign: "center" }} />
        {data.map((cluster) => (
          <Line
            key={`${cluster.category_name}:${cluster.cluster_label}`}
            type="monotone"
            dataKey={cluster.cluster_label}
            stroke={cluster.category_color}
            strokeWidth={2}
            dot={false}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── Keyword cluster map ───────────────────────────────────────────────────────

function KeywordClusterMapChart() {
  const { t } = useTranslation();
  const { data, isLoading } = useKeywordClusterMap();
  if (isLoading) return <Loading />;
  if (!data?.length) {
    return (
      <div className="flex flex-col items-center justify-center h-40 gap-1 text-sm text-gray-400">
        <span>{t("stats.noClusterMap")}</span>
        <span className="text-xs">{t("stats.clusterMapHint")}</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {data.map((cluster, i) => {
        const maxScore = Math.max(...cluster.keywords.map((k) => k.score), 0.01);
        const maxWeight = Math.max(...cluster.keywords.map((k) => k.weight), 1.0);
        return (
          <div
            key={i}
            className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 bg-white dark:bg-gray-900"
          >
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="flex items-center gap-1.5 min-w-0">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: cluster.category_color }} />
                <span className="text-xs text-gray-500 dark:text-gray-400 truncate">{cluster.category_name}</span>
              </div>
              <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0 tabular-nums">
                {cluster.cluster_size} ★
              </span>
            </div>
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 truncate" title={cluster.cluster_label}>
              {cluster.cluster_label}
            </p>
            <div className="flex flex-wrap gap-1">
              {cluster.keywords.map((kw) => {
                const relSize = kw.score / maxScore;
                const hasWeight = kw.weight > 1.0;
                const weightIntensity = Math.min((kw.weight - 1.0) / (maxWeight - 1.0 || 1), 1);
                return (
                  <span
                    key={kw.keyword}
                    title={`score: ${kw.score.toFixed(3)}${hasWeight ? ` · weight: ${kw.weight.toFixed(2)}` : ""}`}
                    className="inline-flex items-center px-1.5 py-0.5 rounded text-gray-700 dark:text-gray-300 transition-colors"
                    style={{
                      fontSize: `${Math.round(10 + relSize * 4)}px`,
                      backgroundColor: hasWeight
                        ? `color-mix(in srgb, ${cluster.category_color} ${Math.round(weightIntensity * 25 + 8)}%, transparent)`
                        : undefined,
                      borderWidth: "1px",
                      borderStyle: "solid",
                      borderColor: hasWeight ? cluster.category_color + "60" : "rgb(229 231 235 / 1)",
                    }}
                  >
                    {kw.keyword}
                    {hasWeight && (
                      <span className="ml-1 text-[9px] font-medium tabular-nums opacity-70">
                        ×{kw.weight.toFixed(1)}
                      </span>
                    )}
                  </span>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

export default function StatsPanel() {
  const { t } = useTranslation();
  const [activityDays, setActivityDays] = useState(30);
  const [categoryDays, setCategoryDays] = useState(30);
  const [sourceDays, setSourceDays] = useState(30);
  const [weightDays, setWeightDays] = useState(60);
  const [clusterDays, setClusterDays] = useState(30);
  const [kwClusterHistoryDays, setKwClusterHistoryDays] = useState(60);

  const { data: settings } = useAdvancedSettings();
  const update = useUpdateAdvancedSettings();
  const statsEnabled = settings?.stats_enabled ?? true;

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="font-semibold text-gray-900 dark:text-gray-100">{t("stats.title")}</h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {t("stats.description")}
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0 ml-4">
          {!statsEnabled && (
            <span className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
              <PauseCircle size={13} /> {t("stats.recordingPaused")}
            </span>
          )}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">{t("stats.recordHistory")}</span>
            <button
              role="switch"
              aria-checked={statsEnabled}
              title={statsEnabled ? t("stats.pauseRecording") : t("stats.resumeRecording")}
              onClick={() => update.mutate({ stats_enabled: !statsEnabled })}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none ${statsEnabled ? "bg-indigo-600" : "bg-gray-300 dark:bg-gray-600"}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${statsEnabled ? "translate-x-4" : "translate-x-0"}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-6">
        <ChartCard
          title={t("stats.activityTitle")}
          description={t("stats.activityDesc")}
          action={<RangePicker value={activityDays} onChange={setActivityDays} />}
        >
          <ActivityChart key={activityDays} days={activityDays} />
        </ChartCard>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ChartCard
            title={t("stats.byCategoryTitle")}
            description={t("stats.byCategoryDesc")}
            action={<RangePicker value={categoryDays} onChange={setCategoryDays} />}
          >
            <ByCategoryChart key={categoryDays} days={categoryDays} />
          </ChartCard>

          <ChartCard
            title={t("stats.bySourceTitle")}
            description={t("stats.bySourceDesc")}
            action={<RangePicker value={sourceDays} onChange={setSourceDays} />}
          >
            <BySourceChart key={sourceDays} days={sourceDays} />
          </ChartCard>
        </div>

        <ChartCard
          title={t("stats.sourceClusterTitle")}
          description={t("stats.sourceClusterDesc")}
          action={<RangePicker value={clusterDays} onChange={setClusterDays} />}
        >
          <SourceClustersChart key={clusterDays} days={clusterDays} />
        </ChartCard>

        <ChartCard
          title={t("stats.weightHistoryTitle")}
          description={t("stats.weightHistoryDesc")}
          action={<RangePicker value={weightDays} onChange={setWeightDays} />}
        >
          <WeightHistoryChart key={weightDays} days={weightDays} />
        </ChartCard>

        <ChartCard
          title={t("stats.kwClusterHistoryTitle")}
          description={t("stats.kwClusterHistoryDesc")}
          action={<RangePicker value={kwClusterHistoryDays} onChange={setKwClusterHistoryDays} />}
        >
          <KeywordClusterHistoryChart key={kwClusterHistoryDays} days={kwClusterHistoryDays} />
        </ChartCard>

        <ChartCard
          title={t("stats.kwClusterMapTitle")}
          description={t("stats.kwClusterMapDesc")}
        >
          <KeywordClusterMapChart />
        </ChartCard>
      </div>
    </div>
  );
}
