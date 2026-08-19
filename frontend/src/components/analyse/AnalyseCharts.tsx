import { useState, useMemo, useEffect, useRef, Component } from "react";
import type { ReactNode } from "react";
import { usePreferencesStore } from "../../stores/preferencesStore";
import { useTranslation } from "react-i18next";
import {
  AreaChart, Area,
  BarChart, Bar,
  LineChart, Line,
  ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, ReferenceLine,
} from "recharts";
import { format, parseISO } from "date-fns";
import { Check, Download, PauseCircle, Plus, RefreshCw, ThumbsUp, X } from "lucide-react";
import { cn } from "../../lib/utils";
import { Accordion } from "../ui/Accordion";
import {
  useActivityStats, useImpactTrend, useReadLaterBacklog, useCategoryStats, useSourceStats, useSourceSignalQuality,
  useWeightHistory, useRelevanceCalibration, useSourceClusters,
  useKeywordClusterMap, usePodcastEpisodeStats, usePodcastEpisodeTrend, useKeywordTrend, useCategoryTrend, useKeywordMomentum,
} from "../../hooks/useStats";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";
import { usePodcastShows } from "../../hooks/usePodcasts";
import { useCategories } from "../../hooks/useCategories";
import { useSources } from "../../hooks/useSources";
import { useAnalyseTrendsStore } from "../../stores/analyseTrendsStore";
import type { TrendTopicConfig } from "../../stores/analyseTrendsStore";
import { statsApi } from "../../api/stats";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { BacklogBucketKey, KeywordClusterMapEntry, KeywordMomentumDirection, KeywordTrendResult, PodcastEpisodeStat } from "../../api/stats";

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
  email: "Email",
  mastodon: "Mastodon",
  arxiv: "arXiv",
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
    <Accordion title={title} description={description} action={action} defaultOpen>
      <ChartErrorBoundary>{children}</ChartErrorBoundary>
    </Accordion>
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

function useGridColor() {
  const theme = usePreferencesStore((s) => s.theme);
  return theme === "dark" ? "#374151" : "#e5e7eb";
}

const CURSOR_STYLE = { fill: "rgba(99,102,241,0.06)" };
const WRAPPER_STYLE = { background: "none", border: "none", boxShadow: "none", zIndex: 50 } as const;

// A static 0-100% domain makes real-world rates (often single digits) render
// as barely-visible slivers. Scales the axis to the data instead: 20%
// headroom above the largest value, rounded up to a clean tick step, capped
// at 100 since these are all percentages. Passed as the domain's max --
// Recharts calls it with the computed data max across every series sharing
// the axis.
function percentAxisMax(dataMax: number): number {
  if (!isFinite(dataMax) || dataMax <= 0) return 10;
  const padded = dataMax * 1.2;
  if (padded >= 100) return 100;
  const step = padded <= 10 ? 1 : padded <= 20 ? 2 : padded <= 50 ? 5 : 10;
  return Math.ceil(padded / step) * step;
}

// ── Reading activity ──────────────────────────────────────────────────────────

const ACTIVITY_SERIES = [
  { key: "fetched",  name: "Fetched",    color: "#818cf8", axis: "left"  },
  { key: "seen",     name: "Seen",       color: "#60a5fa", axis: "left"  },
  { key: "read",     name: "Read",       color: "#34d399", axis: "right" },
  { key: "relevant", name: "Liked ▲",    color: "#fbbf24", axis: "right" },
  { key: "disliked", name: "Disliked ▼", color: "#f87171", axis: "right" },
] as const;

function ActivityChart({ days }: { days: number }) {
  const gridColor = useGridColor();
  const { data, isLoading } = useActivityStats(days);
  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  const points = data.map((d) => ({ ...d, date: fmtDate(d.date, days) }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={points} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <defs>
          {ACTIVITY_SERIES.map(({ key, color }) => (
            <linearGradient key={key} id={`g_${key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.25} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} />
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

// ── Impact score trend ────────────────────────────────────────────────────────

function ImpactTrendChart({ days, sourceIds }: { days: number; sourceIds: string[] }) {
  const { t } = useTranslation();
  const gridColor = useGridColor();
  const { data, isLoading } = useImpactTrend(days, sourceIds);
  if (isLoading) return <Loading />;
  if (!data?.points.length) return <Empty />;

  const points = data.points.map((p) => ({ ...p, date: fmtDate(p.date, days) }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart data={points} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis
          yAxisId="left"
          domain={[0, 10]}
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
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
            const d = payload[0].payload as (typeof points)[number];
            return (
              <TooltipBox label={label as string}>
                <TooltipRow color="#6366f1" name={t("stats.impactAvgLabel")} value={(d.avg_impact ?? 0).toFixed(1)} />
                <TooltipRow
                  color="#f59e0b"
                  name={t("stats.impactHighLabel", { threshold: data.high_impact_threshold })}
                  value={d.high_impact_count}
                />
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
        <Area
          yAxisId="left"
          type="monotone"
          dataKey="avg_impact"
          name={t("stats.impactAvgLabel")}
          stroke="#6366f1"
          fill="#6366f1"
          fillOpacity={0.15}
          strokeWidth={2}
          dot={false}
        />
        <Bar
          yAxisId="right"
          dataKey="high_impact_count"
          name={t("stats.impactHighLabel", { threshold: data.high_impact_threshold })}
          fill="#f59e0b"
          radius={[3, 3, 0, 0]}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// ── Read-later backlog health ─────────────────────────────────────────────────

const BACKLOG_BUCKET_KEYS: BacklogBucketKey[] = ["under_1d", "1_3d", "3_7d", "7_14d", "14_30d", "over_30d"];
const BACKLOG_BUCKET_COLORS: Record<BacklogBucketKey, string> = {
  under_1d: "#10b981",
  "1_3d": "#84cc16",
  "3_7d": "#f59e0b",
  "7_14d": "#f97316",
  "14_30d": "#ef4444",
  over_30d: "#991b1b",
};

function ReadLaterBacklogChart() {
  const { t } = useTranslation();
  const gridColor = useGridColor();
  const { data, isLoading } = useReadLaterBacklog();
  if (isLoading) return <Loading />;
  if (!data || data.total === 0) return <Empty />;

  const byKey = new Map(data.buckets.map((b) => [b.key, b.count]));
  const chartData = BACKLOG_BUCKET_KEYS.map((key) => ({
    key,
    label: t(`stats.backlogBucket_${key}`),
    count: byKey.get(key) ?? 0,
    color: BACKLOG_BUCKET_COLORS[key],
  }));

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline gap-4 text-sm">
        <span className="text-gray-700 dark:text-gray-200">
          <span className="font-semibold text-lg">{data.total}</span> {t("stats.backlogTotalLabel")}
        </span>
        {data.oldest_days !== null && (
          <span className="text-gray-400 dark:text-gray-500">
            {t("stats.backlogOldestLabel", { days: Math.floor(data.oldest_days) })}
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 32, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
          <YAxis type="category" dataKey="label" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={90} />
          <Tooltip
            cursor={false}
            wrapperStyle={WRAPPER_STYLE}
            content={({ active, payload }) => {
              if (!active || !payload?.[0]) return null;
              const d = payload[0].payload as (typeof chartData)[number];
              return (
                <TooltipBox>
                  <TooltipRow color={d.color} name={d.label} value={d.count} />
                </TooltipBox>
              );
            }}
          />
          <Bar dataKey="count" name={t("stats.backlogTotalLabel")} radius={[0, 4, 4, 0]}>
            {chartData.map((entry) => (
              <Cell key={entry.key} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Volume by category ────────────────────────────────────────────────────────

function ByCategoryChart({ days }: { days: number }) {
  const gridColor = useGridColor();
  const { data, isLoading } = useCategoryStats(days);
  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, data.length * 36 + 40)}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 32, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} horizontal={false} />
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
  const gridColor = useGridColor();
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
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={160}
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

// ── Source signal quality ─────────────────────────────────────────────────────

function SourceSignalQualityChart({ days }: { days: number }) {
  const { t } = useTranslation();
  const gridColor = useGridColor();
  const { data, isLoading } = useSourceSignalQuality(days);
  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  const chartData = data.map((s) => ({
    name: s.name,
    source_type: s.source_type,
    total: s.total,
    relevant: s.relevant,
    disliked: s.disliked,
    read: s.read,
    relevant_rate: s.total > 0 ? (s.relevant / s.total) * 100 : 0,
    dislike_rate: s.total > 0 ? (s.disliked / s.total) * 100 : 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, chartData.length * 36 + 40)}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} horizontal={false} />
        <XAxis
          type="number"
          domain={[0, percentAxisMax]}
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={160}
          tickFormatter={(name: string) => {
            const entry = chartData.find((d) => d.name === name);
            const type = entry ? (SOURCE_TYPE_LABEL[entry.source_type] ?? entry.source_type) : "";
            return type ? `${name} (${type})` : name;
          }}
        />
        <Tooltip
          cursor={false}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload }) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload as (typeof chartData)[number];
            return (
              <TooltipBox>
                <div className="font-semibold text-gray-800 dark:text-gray-100 mb-1.5">{d.name}</div>
                <TooltipRow
                  color="#10b981"
                  name={t("stats.signalRelevant")}
                  value={`${d.relevant_rate.toFixed(0)}% (${t("stats.categoryTrendRawCount", { count: d.relevant, total: d.total })})`}
                />
                <TooltipRow
                  color="#ef4444"
                  name={t("stats.signalDisliked")}
                  value={`${d.dislike_rate.toFixed(0)}% (${t("stats.categoryTrendRawCount", { count: d.disliked, total: d.total })})`}
                />
                <TooltipRow name={t("stats.signalRead")} value={`${d.read} / ${d.total}`} />
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
        <Bar dataKey="relevant_rate" name={t("stats.signalRelevant")} fill="#10b981" radius={[0, 4, 4, 0]} />
        <Bar dataKey="dislike_rate" name={t("stats.signalDisliked")} fill="#ef4444" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Category weight history ───────────────────────────────────────────────────

function WeightHistoryChart({ days }: { days: number }) {
  const gridColor = useGridColor();
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
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} />
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

// ── Relevance-score calibration ───────────────────────────────────────────────

function RelevanceCalibrationChart({ days }: { days: number }) {
  const { t } = useTranslation();
  const gridColor = useGridColor();
  const { data, isLoading } = useRelevanceCalibration(days);
  if (isLoading) return <Loading />;
  if (!data || data.every((b) => b.count === 0)) return <Empty />;

  const chartData = data.map((b) => ({
    score: String(b.score),
    percent: b.relevant_rate === null ? undefined : b.relevant_rate * 100,
    count: b.count,
    relevant_count: b.relevant_count,
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} />
        <XAxis
          dataKey="score"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          label={{ value: t("stats.calibrationScoreAxis"), position: "insideBottom", offset: -2, fontSize: 11, fill: gridColor }}
        />
        <YAxis
          domain={[0, percentAxisMax]}
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => `${v}%`}
          width={36}
        />
        <Tooltip
          cursor={CURSOR_STYLE}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload }) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload as (typeof chartData)[number];
            return (
              <TooltipBox label={t("stats.calibrationScoreLabel", { score: d.score })}>
                {d.count > 0 ? (
                  <TooltipRow
                    name={t("stats.signalRelevant")}
                    value={`${((d.percent as number) ?? 0).toFixed(0)}% (${t("stats.categoryTrendRawCount", { count: d.relevant_count, total: d.count })})`}
                  />
                ) : (
                  <div className="text-gray-400">{t("stats.noData")}</div>
                )}
              </TooltipBox>
            );
          }}
        />
        <Bar dataKey="percent" name={t("stats.signalRelevant")} fill="#6366f1" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Source cluster co-occurrence ──────────────────────────────────────────────

function SourceClustersChart({ days }: { days: number }) {
  const gridColor = useGridColor();
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
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} horizontal={false} />
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

// ── Category coverage over time ───────────────────────────────────────────────

function SourceFilterPills({
  sourceIds,
  onToggle,
}: {
  sourceIds: string[];
  onToggle: (id: string) => void;
}) {
  const { t } = useTranslation();
  const { data: sources = [] } = useSources();
  const active = sources.filter((s) => s.is_active);
  if (active.length === 0) return null;
  return (
    <div>
      <p className="text-xs font-medium text-gray-600 dark:text-gray-300 mb-1.5">{t("stats.filterBySource")}</p>
      <div className="flex flex-wrap gap-1.5">
        {active.map((source) => {
          const selected = sourceIds.includes(source.id);
          return (
            <button
              key={source.id}
              type="button"
              onClick={() => onToggle(source.id)}
              className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border transition-colors",
                selected
                  ? "bg-indigo-600 text-white border-transparent"
                  : "bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-gray-400"
              )}
            >
              {selected && <Check size={9} />}
              {source.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function CategoryTrendChart({ days, sourceIds }: { days: number; sourceIds: string[] }) {
  const { t } = useTranslation();
  const gridColor = useGridColor();
  const { data, isLoading } = useCategoryTrend(days, sourceIds);
  if (isLoading) return <Loading />;

  const categories = data?.categories ?? [];
  // Categories with zero coverage in this window/filter would otherwise
  // render as a flat line at 0 -- excluded so the legend only lists
  // categories that actually had something happen. Filtered on the raw
  // count, not the derived percentage, so this is unaffected by the % math
  // below.
  const covered = categories.filter((r) => r.points.some((p) => p.count > 0));
  if (covered.length === 0) return <Empty />;

  const totalByDate = new Map((data?.totals ?? []).map((p) => [p.date, p.count]));
  const allDates = Array.from(new Set(covered.flatMap((r) => r.points.map((p) => p.date)))).sort();
  const chartData = allDates.map((date) => {
    const total = totalByDate.get(date) ?? 0;
    const row: Record<string, string | number> = { date: fmtDate(date, days), __total: total };
    for (const r of covered) {
      const count = r.points.find((p) => p.date === date)?.count ?? 0;
      row[r.name] = total > 0 ? (count / total) * 100 : 0;
      row[`${r.name}__raw`] = count;
    }
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => `${v}%`}
          width={36}
        />
        <Tooltip
          cursor={{ stroke: "rgba(99,102,241,0.2)", strokeWidth: 1 }}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const total = (payload[0].payload as Record<string, number>).__total ?? 0;
            return (
              <TooltipBox label={label as string}>
                {payload
                  .filter((p) => p.value !== undefined)
                  .sort((a, b) => (b.value as number) - (a.value as number))
                  .map((p) => {
                    const row = p.payload as Record<string, number>;
                    const raw = row[`${p.name}__raw`] ?? 0;
                    return (
                      <TooltipRow
                        key={String(p.name)}
                        color={p.color}
                        name={`${p.name ?? ""}`}
                        value={`${(p.value as number).toFixed(1)}% (${t("stats.categoryTrendRawCount", { count: raw, total })})`}
                      />
                    );
                  })}
                <TooltipRow name={t("stats.categoryTrendTotalRow")} value={total} />
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, left: 0, width: "100%", textAlign: "center" }} />
        {covered.map((r) => (
          <Line key={r.id} type="monotone" dataKey={r.name} stroke={r.color} strokeWidth={2} dot={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── Keyword cluster map ───────────────────────────────────────────────────────

const SIM_W = 560;
const SIM_H = 320;
const MIN_R = 18;
const MAX_R = 52;

function jaccardSim(a: Set<string>, b: Set<string>): number {
  let inter = 0;
  for (const k of a) if (b.has(k)) inter++;
  const union = a.size + b.size - inter;
  return union > 0 ? inter / union : 0;
}

function truncLabel(s: string, maxLen: number) {
  return s.length > maxLen ? s.slice(0, maxLen - 1) + "…" : s;
}

function ClusterBubbleMap({ data }: { data: KeywordClusterMapEntry[] }) {
  const { t } = useTranslation();
  const [hovered, setHovered] = useState<number | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const activeIdx = selected !== null ? selected : hovered;

  const kwSets = useMemo(
    () => data.map((d) => new Set(d.keywords.map((k) => k.keyword))),
    [data],
  );

  const nodes = useMemo(() => {
    const maxSize = Math.max(...data.map((d) => d.cluster_size), 1);
    const ns = data.map((d, i) => {
      const angle = (2 * Math.PI * i) / data.length - Math.PI / 2;
      const r = MIN_R + (d.cluster_size / maxSize) * (MAX_R - MIN_R);
      const initR = 100 + r;
      return {
        x: SIM_W / 2 + Math.cos(angle) * initR,
        y: SIM_H / 2 + Math.sin(angle) * initR,
        vx: 0, vy: 0, r,
      };
    });

    for (let t = 0; t < 280; t++) {
      const alpha = Math.max(0.01, 1 - t / 200);
      for (const n of ns) { n.vx = 0; n.vy = 0; }

      for (let i = 0; i < ns.length; i++) {
        // Centering
        ns[i].vx += (SIM_W / 2 - ns[i].x) * 0.04 * alpha;
        ns[i].vy += (SIM_H / 2 - ns[i].y) * 0.04 * alpha;

        for (let j = i + 1; j < ns.length; j++) {
          const dx = ns[j].x - ns[i].x;
          const dy = ns[j].y - ns[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
          const nx_ = dx / dist, ny_ = dy / dist;

          // Collision repulsion
          const minDist = ns[i].r + ns[j].r + 8;
          if (dist < minDist) {
            const push = (minDist - dist) * 0.6 * alpha;
            ns[i].vx -= nx_ * push;
            ns[i].vy -= ny_ * push;
            ns[j].vx += nx_ * push;
            ns[j].vy += ny_ * push;
          }

          // General charge repulsion
          const repel = Math.min(4000 / (dist * dist), 18) * alpha;
          ns[i].vx -= nx_ * repel;
          ns[i].vy -= ny_ * repel;
          ns[j].vx += nx_ * repel;
          ns[j].vy += ny_ * repel;

          // Similarity attraction — pull similar clusters together
          const sim = jaccardSim(kwSets[i], kwSets[j]);
          if (sim > 0) {
            const idealDist = minDist + (1 - sim) * 160;
            const err = (dist - idealDist) * 0.08 * alpha * sim;
            ns[i].vx += nx_ * err;
            ns[i].vy += ny_ * err;
            ns[j].vx -= nx_ * err;
            ns[j].vy -= ny_ * err;
          }
        }

        ns[i].x = Math.max(ns[i].r + 3, Math.min(SIM_W - ns[i].r - 3, ns[i].x + ns[i].vx));
        ns[i].y = Math.max(ns[i].r + 3, Math.min(SIM_H - ns[i].r - 3, ns[i].y + ns[i].vy));
      }
    }
    return ns;
  }, [data, kwSets]);

  const active = activeIdx !== null ? data[activeIdx] : null;

  return (
    <div>
      <svg
        viewBox={`0 0 ${SIM_W} ${SIM_H}`}
        className="w-full"
        style={{ height: SIM_H * 0.85 }}
        onClick={(e) => { if (e.target === e.currentTarget) setSelected(null); }}
      >
        {nodes.map((n, i) => {
          const d = data[i];
          const isActive = activeIdx === i;
          const fontSize = Math.max(9, Math.min(13, n.r * 0.38));
          const maxChars = Math.max(4, Math.floor(n.r * 1.5 / (fontSize * 0.6)));
          return (
            <g
              key={i}
              transform={`translate(${n.x},${n.y})`}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              onClick={(e) => { e.stopPropagation(); setSelected(selected === i ? null : i); }}
            >
              <circle
                r={n.r}
                fill={d.category_color}
                fillOpacity={isActive ? 0.92 : 0.65}
                stroke={d.category_color}
                strokeWidth={isActive ? 2.5 : 1}
                strokeOpacity={isActive ? 1 : 0.4}
              />
              {n.r >= 22 && (
                <text
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={fontSize}
                  fill="white"
                  fontWeight="600"
                  style={{ pointerEvents: "none", userSelect: "none" }}
                >
                  {truncLabel(d.cluster_label, maxChars)}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {active ? (
        <div className="mt-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div>
              <div className="flex items-center gap-1.5 mb-0.5">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: active.category_color }} />
                <span className="text-xs text-gray-500 dark:text-gray-400">{active.category_name}</span>
              </div>
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{active.cluster_label}</p>
            </div>
            <span
              className="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500 shrink-0 mt-0.5"
              title={t("stats.clusterSizeHint")}
            >
              <ThumbsUp size={11} />
              {active.cluster_size}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {active.keywords.map((kw) => {
              const hasWeight = kw.weight > 1.0;
              return (
                <span
                  key={kw.keyword}
                  title={`TF-IDF: ${kw.score.toFixed(3)}${hasWeight ? ` · liked ×${kw.weight.toFixed(1)}` : ""}`}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs text-gray-700 dark:text-gray-300"
                  style={{
                    borderWidth: "1px",
                    borderStyle: "solid",
                    borderColor: hasWeight ? active.category_color + "80" : "rgb(229 231 235)",
                    backgroundColor: hasWeight ? active.category_color + "18" : undefined,
                  }}
                >
                  {kw.keyword}
                  {hasWeight && (
                    <span className="text-[10px] font-semibold tabular-nums" style={{ color: active.category_color }}>
                      ×{kw.weight.toFixed(1)}
                    </span>
                  )}
                </span>
              );
            })}
          </div>
        </div>
      ) : (
        <p className="mt-2 text-center text-xs text-gray-400">{t("stats.clusterClickHint")}</p>
      )}
    </div>
  );
}

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
  return <ClusterBubbleMap data={data} />;
}

// ── Podcast episode topics ────────────────────────────────────────────────────

function ShowPicker({
  shows,
  value,
  onChange,
}: {
  shows: { id: string; name: string }[];
  value: string | null;
  onChange: (id: string) => void;
}) {
  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
      className="text-xs rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-2 py-1 text-gray-700 dark:text-gray-300"
    >
      {shows.map((s) => (
        <option key={s.id} value={s.id}>{s.name}</option>
      ))}
    </select>
  );
}

function EpisodeTagList({ title, tags }: { title: string; tags: { label: string; count: number }[] }) {
  if (!tags.length) return null;
  return (
    <div>
      <p className="text-xs font-medium text-gray-600 dark:text-gray-300 mb-1.5">{title}</p>
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => (
          <span
            key={tag.label}
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700"
          >
            {tag.label}
            {tag.count > 1 && <span className="text-[10px] text-gray-400 dark:text-gray-500">×{tag.count}</span>}
          </span>
        ))}
      </div>
    </div>
  );
}

function EpisodeDetailPanel({ episode }: { episode: PodcastEpisodeStat }) {
  const { t } = useTranslation();
  return (
    <div className="mt-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
          {format(parseISO(episode.generated_at), "MMM d, yyyy")}
        </span>
        <span className="text-xs text-gray-400 dark:text-gray-500">
          {t("stats.storiesCount", { count: episode.total_stories })}
        </span>
      </div>
      <EpisodeTagList
        title={t("stats.topKeywords")}
        tags={episode.top_keywords.map((k) => ({ label: k.keyword, count: k.count }))}
      />
      <EpisodeTagList
        title={t("stats.topSources")}
        tags={episode.top_sources.map((s) => ({ label: s.name, count: s.count }))}
      />
    </div>
  );
}

function PodcastEpisodesChart({ showId }: { showId: string }) {
  const { t } = useTranslation();
  const gridColor = useGridColor();
  const { data, isLoading } = usePodcastEpisodeStats(showId);
  const [activeId, setActiveId] = useState<string | null>(null);

  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  const seenCatIds = new Set<string>();
  const allCategories: { id: string; name: string; color: string }[] = [];
  for (const ep of data) {
    for (const cat of ep.categories) {
      if (!seenCatIds.has(cat.id)) {
        seenCatIds.add(cat.id);
        allCategories.push({ id: cat.id, name: cat.name, color: cat.color });
      }
    }
  }

  const chartData = data.map((ep) => {
    const row: Record<string, string | number> = {
      id: ep.id,
      date: format(parseISO(ep.generated_at), "MMM d"),
      _total: ep.total_stories,
    };
    for (const cat of ep.categories) {
      row[cat.name] = cat.count;
    }
    return row;
  });

  const active = data.find((ep) => ep.id === activeId) ?? data[data.length - 1];
  const handleBarClick = (bar: { payload?: Record<string, string | number> }) => {
    if (bar.payload?.id) setActiveId(String(bar.payload.id));
  };

  return (
    <div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} width={28} />
          <Tooltip
            cursor={CURSOR_STYLE}
            wrapperStyle={WRAPPER_STYLE}
            content={({ active, payload, label }) => {
              if (!active || !payload?.[0]) return null;
              const row = payload[0].payload as Record<string, string | number>;
              const total = row._total as number;
              const entries = allCategories
                .map((cat) => ({ ...cat, count: (row[cat.name] ?? 0) as number }))
                .filter((e) => e.count > 0)
                .sort((a, b) => b.count - a.count);
              return (
                <TooltipBox label={label as string}>
                  <TooltipRow name={t("stats.stories")} value={total} />
                  {entries.length > 0 && <CategoryBars entries={entries} total={total} />}
                </TooltipBox>
              );
            }}
          />
          {allCategories.map((cat, i) => (
            <Bar
              key={cat.id}
              dataKey={cat.name}
              stackId="stack"
              fill={cat.color}
              radius={i === allCategories.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
              cursor="pointer"
              onClick={handleBarClick}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
      {active && <EpisodeDetailPanel episode={active} />}
    </div>
  );
}

function PodcastEpisodesEmpty() {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-center h-40 text-sm text-gray-400 text-center px-4">
      {t("stats.noPodcastShows")}
    </div>
  );
}

function PodcastEpisodeTrendChart({ showId }: { showId: string }) {
  const { t } = useTranslation();
  const gridColor = useGridColor();
  const { data, isLoading } = usePodcastEpisodeTrend(showId);
  if (isLoading) return <Loading />;
  if (!data?.episodes.length) return <Empty />;

  const points = data.episodes.map((ep, i) => ({
    ...ep,
    label: t("stats.podcastEpisodeLabel", { n: i + 1 }),
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart data={points} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={28}
          label={{ value: t("stats.podcastMinutesAxis"), angle: -90, position: "insideLeft", fontSize: 11, fill: gridColor }}
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
        <ReferenceLine
          yAxisId="left"
          y={data.target_minutes}
          stroke="#9ca3af"
          strokeDasharray="4 4"
          label={{ value: t("stats.podcastTargetLabel", { minutes: data.target_minutes }), fontSize: 10, fill: "#9ca3af", position: "insideTopRight" }}
        />
        <Tooltip
          cursor={CURSOR_STYLE}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0].payload as (typeof points)[number];
            return (
              <TooltipBox label={label as string}>
                <TooltipRow color="#6366f1" name={t("stats.podcastActualLabel")} value={`${d.actual_minutes} min`} />
                <TooltipRow color="#f59e0b" name={t("stats.podcastStoryCountLabel")} value={d.story_count} />
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
        <Bar yAxisId="left" dataKey="actual_minutes" name={t("stats.podcastActualLabel")} fill="#6366f1" radius={[3, 3, 0, 0]} />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="story_count"
          name={t("stats.podcastStoryCountLabel")}
          stroke="#f59e0b"
          strokeWidth={2}
          dot={{ r: 3 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function PodcastEpisodesSection() {
  const { t } = useTranslation();
  const { data: shows = [] } = usePodcastShows();
  const [selectedShowId, setSelectedShowId] = useState<string | null>(null);
  const effectiveShowId = selectedShowId ?? shows[0]?.id ?? null;
  const showPicker = shows.length > 0 && (
    <ShowPicker shows={shows} value={effectiveShowId} onChange={setSelectedShowId} />
  );

  return (
    <div className="flex flex-col gap-6">
      <ChartCard
        title={t("stats.podcastEpisodesTitle")}
        description={t("stats.podcastEpisodesDesc")}
        action={showPicker}
      >
        {shows.length === 0 ? (
          <PodcastEpisodesEmpty />
        ) : (
          <PodcastEpisodesChart key={effectiveShowId} showId={effectiveShowId as string} />
        )}
      </ChartCard>

      <ChartCard
        title={t("stats.podcastTrendTitle")}
        description={t("stats.podcastTrendDesc")}
        action={showPicker}
      >
        {shows.length === 0 ? (
          <PodcastEpisodesEmpty />
        ) : (
          <PodcastEpisodeTrendChart key={effectiveShowId} showId={effectiveShowId as string} />
        )}
      </ChartCard>
    </div>
  );
}

// ── Recording toggle (rendered in the Analyse page header) ────────────────────

export function StatsRecordingToggle() {
  const { t } = useTranslation();
  const { data: settings } = useAdvancedSettings();
  const update = useUpdateAdvancedSettings();
  const statsEnabled = settings?.stats_enabled ?? true;

  return (
    <div className="flex items-center gap-2">
      {!statsEnabled && (
        <span className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
          <PauseCircle size={13} /> {t("stats.recordingPaused")}
        </span>
      )}
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
  );
}

// ── Tabs (composed by pages/AnalysePage.tsx) ───────────────────────────────────

export function AnalyseActivityTab() {
  const { t } = useTranslation();
  const [activityDays, setActivityDays] = useState(30);
  const [impactDays, setImpactDays] = useState(30);
  const [impactSourceIds, setImpactSourceIds] = useState<string[]>([]);
  const toggleImpactSource = (id: string) =>
    setImpactSourceIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  return (
    <div className="flex flex-col gap-6">
      <ChartCard
        title={t("stats.activityTitle")}
        description={t("stats.activityDesc")}
        action={<RangePicker value={activityDays} onChange={setActivityDays} />}
      >
        <ActivityChart key={activityDays} days={activityDays} />
      </ChartCard>

      <ChartCard
        title={t("stats.impactTrendTitle")}
        description={t("stats.impactTrendDesc")}
        action={<RangePicker value={impactDays} onChange={setImpactDays} />}
      >
        <div className="flex flex-col gap-4">
          <SourceFilterPills sourceIds={impactSourceIds} onToggle={toggleImpactSource} />
          <ImpactTrendChart
            key={`${impactDays}-${impactSourceIds.join(",")}`}
            days={impactDays}
            sourceIds={impactSourceIds}
          />
        </div>
      </ChartCard>

      <ChartCard title={t("stats.backlogTitle")} description={t("stats.backlogDesc")}>
        <ReadLaterBacklogChart />
      </ChartCard>
    </div>
  );
}

export function AnalyseCategoriesTab() {
  const { t } = useTranslation();
  const [categoryDays, setCategoryDays] = useState(30);
  const [sourceDays, setSourceDays] = useState(30);
  const [signalDays, setSignalDays] = useState(30);
  const [clusterDays, setClusterDays] = useState(30);
  const [categoryTrendDays, setCategoryTrendDays] = useState(30);
  const [categoryTrendSourceIds, setCategoryTrendSourceIds] = useState<string[]>([]);
  const toggleCategoryTrendSource = (id: string) =>
    setCategoryTrendSourceIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  return (
    <div className="flex flex-col gap-6">
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
        title={t("stats.signalQualityTitle")}
        description={t("stats.signalQualityDesc")}
        action={<RangePicker value={signalDays} onChange={setSignalDays} />}
      >
        <SourceSignalQualityChart key={signalDays} days={signalDays} />
      </ChartCard>

      <ChartCard
        title={t("stats.sourceClusterTitle")}
        description={t("stats.sourceClusterDesc")}
        action={<RangePicker value={clusterDays} onChange={setClusterDays} />}
      >
        <SourceClustersChart key={clusterDays} days={clusterDays} />
      </ChartCard>

      <ChartCard
        title={t("stats.categoryTrendTitle")}
        description={t("stats.categoryTrendDesc")}
        action={<RangePicker value={categoryTrendDays} onChange={setCategoryTrendDays} />}
      >
        <div className="flex flex-col gap-4">
          <SourceFilterPills sourceIds={categoryTrendSourceIds} onToggle={toggleCategoryTrendSource} />
          <CategoryTrendChart
            key={`${categoryTrendDays}-${categoryTrendSourceIds.join(",")}`}
            days={categoryTrendDays}
            sourceIds={categoryTrendSourceIds}
          />
        </div>
      </ChartCard>
    </div>
  );
}

export function AnalyseLearningTab() {
  const { t } = useTranslation();
  const [weightDays, setWeightDays] = useState(60);
  const [calibrationDays, setCalibrationDays] = useState(90);
  const qc = useQueryClient();
  const refreshClusters = useMutation({
    mutationFn: () => statsApi.refreshClusters(),
    onSuccess: () => {
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: ["stats", "keyword-cluster-map"] });
      }, 3000);
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <ChartCard
        title={t("stats.weightHistoryTitle")}
        description={t("stats.weightHistoryDesc")}
        action={<RangePicker value={weightDays} onChange={setWeightDays} />}
      >
        <WeightHistoryChart key={weightDays} days={weightDays} />
      </ChartCard>

      <ChartCard
        title={t("stats.calibrationTitle")}
        description={t("stats.calibrationDesc")}
        action={<RangePicker value={calibrationDays} onChange={setCalibrationDays} />}
      >
        <RelevanceCalibrationChart key={calibrationDays} days={calibrationDays} />
      </ChartCard>

      <ChartCard
        title={t("stats.kwClusterMapTitle")}
        description={t("stats.kwClusterMapDesc")}
        action={
          <button
            onClick={() => refreshClusters.mutate()}
            disabled={refreshClusters.isPending}
            title={t("stats.refreshClusters")}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-indigo-600 transition-colors disabled:opacity-40"
          >
            <RefreshCw size={12} className={refreshClusters.isPending ? "animate-spin" : ""} />
            {t("stats.refreshClusters")}
          </button>
        }
      >
        <KeywordClusterMapChart />
      </ChartCard>
    </div>
  );
}

export function AnalysePodcastTab() {
  return <PodcastEpisodesSection />;
}

// ── Keyword/topic coverage trends ─────────────────────────────────────────────

const MAX_TOPICS = 6;
const TOPIC_COLORS = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#0ea5e9", "#a855f7"];

function generateTopicId(): string {
  // Local React key only, not security-sensitive -- see the identical
  // fallback comment in PodcastShowForm.tsx's generateHostId.
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `topic-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function emptyTopic(index: number): TrendTopicConfig {
  return { id: generateTopicId(), label: "", keywords: [], color: TOPIC_COLORS[index % TOPIC_COLORS.length] };
}

// Topics persisted before the color field existed fall back to a palette
// color derived from position, same as the old index-only behavior.
function topicColor(topic: TrendTopicConfig, index: number): string {
  return topic.color ?? TOPIC_COLORS[index % TOPIC_COLORS.length];
}

function TopicRow({
  topic,
  color,
  canRemove,
  onChange,
  onRemove,
}: {
  topic: TrendTopicConfig;
  color: string;
  canRemove: boolean;
  onChange: (patch: Partial<TrendTopicConfig>) => void;
  onRemove: () => void;
}) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState("");

  const commitDraft = () => {
    const value = draft.trim();
    if (value && !topic.keywords.some((k) => k.toLowerCase() === value.toLowerCase())) {
      onChange({ keywords: [...topic.keywords, value] });
    }
    setDraft("");
  };

  const removeKeyword = (kw: string) =>
    onChange({ keywords: topic.keywords.filter((k) => k !== kw) });

  return (
    <div className="flex flex-col gap-2 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={color}
          onChange={(e) => onChange({ color: e.target.value })}
          title={t("stats.trendTopicColor")}
          className="w-4 h-4 rounded-full shrink-0 border-0 p-0 cursor-pointer overflow-hidden [&::-webkit-color-swatch-wrapper]:p-0 [&::-webkit-color-swatch]:border-0 [&::-webkit-color-swatch]:rounded-full [&::-moz-color-swatch]:border-0 [&::-moz-color-swatch]:rounded-full"
        />
        <input
          value={topic.label}
          onChange={(e) => onChange({ label: e.target.value })}
          placeholder={t("stats.trendTopicLabelPlaceholder")}
          maxLength={100}
          className="flex-1 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-2 py-1 text-gray-800 dark:text-gray-100"
        />
        {canRemove && (
          <button
            type="button"
            onClick={onRemove}
            title={t("common.delete")}
            className="text-gray-400 hover:text-red-500 transition-colors"
          >
            <X size={14} />
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {topic.keywords.map((kw) => (
          <span
            key={kw}
            className="inline-flex items-center gap-1 pl-2 pr-1 py-0.5 rounded-full text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
          >
            {kw}
            <button type="button" onClick={() => removeKeyword(kw)} className="text-gray-400 hover:text-red-500">
              <X size={11} />
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault();
              commitDraft();
            } else if (e.key === "Backspace" && draft === "" && topic.keywords.length > 0) {
              onChange({ keywords: topic.keywords.slice(0, -1) });
            }
          }}
          onBlur={commitDraft}
          placeholder={t("stats.trendKeywordPlaceholder")}
          className="flex-1 min-w-[100px] text-xs bg-transparent outline-none text-gray-800 dark:text-gray-100 placeholder:text-gray-400"
        />
      </div>
    </div>
  );
}

function TrendFilterPills({
  title,
  items,
  selectedIds,
  onToggle,
  colorOf,
}: {
  title: string;
  items: { id: string; name: string }[];
  selectedIds: string[];
  onToggle: (id: string) => void;
  colorOf?: (id: string) => string | undefined;
}) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="text-xs font-medium text-gray-600 dark:text-gray-300 mb-1.5">{title}</p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item) => {
          const selected = selectedIds.includes(item.id);
          const color = colorOf?.(item.id);
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onToggle(item.id)}
              className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border transition-colors",
                selected
                  ? "text-white border-transparent"
                  : "bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-gray-400"
              )}
              style={selected ? { backgroundColor: color ?? "#4f46e5", borderColor: color ?? "#4f46e5" } : undefined}
            >
              {selected && <Check size={9} />}
              {item.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Trend range covers up to 10 years (see TREND_RANGE_OPTIONS below), well
// past the point where the shared fmtDate's "MMM d" (no year) is
// unambiguous -- a distinct formatter that adds the year once the range is
// wide enough to actually span one.
function fmtTrendDate(iso: string, days: number | null) {
  try {
    const d = parseISO(iso);
    if (days !== null && days <= 7) return format(d, "EEE d");
    if (days !== null && days <= 120) return format(d, "MMM d");
    return format(d, "MMM d, yy");
  } catch {
    return iso;
  }
}

const TREND_RANGE_OPTIONS: { label: string; days: number | null }[] = [
  { label: "7 d", days: 7 },
  { label: "30 d", days: 30 },
  { label: "90 d", days: 90 },
  { label: "180 d", days: 180 },
  { label: "1 y", days: 365 },
  { label: "All", days: null },
];

function TrendRangePicker({ value, onChange }: { value: number | null; onChange: (d: number | null) => void }) {
  return (
    <div className="flex gap-1">
      {TREND_RANGE_OPTIONS.map(({ label, days }) => (
        <button
          key={label}
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

function csvEscape(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

function keywordTrendToCsv(results: KeywordTrendResult[]): string {
  const allDates = Array.from(new Set(results.flatMap((r) => r.points.map((p) => p.date)))).sort();
  const header = ["date", ...results.map((r) => csvEscape(r.label))].join(",");
  const rows = allDates.map((date) => {
    const counts = results.map((r) => String(r.points.find((p) => p.date === date)?.count ?? 0));
    return [date, ...counts].join(",");
  });
  return [header, ...rows].join("\n");
}

function downloadCsv(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function KeywordTrendChart({
  results,
  colors,
  days,
}: {
  results: KeywordTrendResult[];
  colors: string[];
  days: number | null;
}) {
  const gridColor = useGridColor();

  const allDates = Array.from(new Set(results.flatMap((r) => r.points.map((p) => p.date)))).sort();
  const chartData = allDates.map((date) => {
    const row: Record<string, string | number> = { date: fmtTrendDate(date, days) };
    for (const r of results) {
      const point = r.points.find((p) => p.date === date);
      row[r.label] = point?.count ?? 0;
    }
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} strokeOpacity={0.5} />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
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
                    <TooltipRow key={String(p.name)} color={p.color} name={`${p.name ?? ""}`} value={p.value as number} />
                  ))}
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12, left: 0, width: "100%", textAlign: "center" }} />
        {results.map((r, i) => (
          <Line
            key={r.label}
            type="monotone"
            dataKey={r.label}
            stroke={colors[i] ?? TOPIC_COLORS[i % TOPIC_COLORS.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── Keyword momentum (rising / falling) ───────────────────────────────────────

const MOMENTUM_TOP_N = 10;

const MOMENTUM_CONFIG: Record<
  KeywordMomentumDirection,
  {
    color: string;
    percentClass: string;
    badgeClass: string;
    titleKey: string;
    descKey: string;
    emptyKey: string;
    flagKey: string;
    flagField: "is_newcomer" | "is_dormant";
  }
> = {
  rising: {
    color: "#10b981",
    percentClass: "text-emerald-600 dark:text-emerald-400",
    badgeClass: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400",
    titleKey: "stats.risingKeywordsTitle",
    descKey: "stats.risingKeywordsDesc",
    emptyKey: "stats.risingEmpty",
    flagKey: "stats.risingNewcomer",
    flagField: "is_newcomer",
  },
  falling: {
    color: "#f87171",
    percentClass: "text-red-500 dark:text-red-400",
    badgeClass: "bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
    titleKey: "stats.fallingKeywordsTitle",
    descKey: "stats.fallingKeywordsDesc",
    emptyKey: "stats.fallingEmpty",
    flagKey: "stats.fallingDormant",
    flagField: "is_dormant",
  },
};

function Sparkline({ points, color }: { points: number[]; color: string }) {
  const w = 60, h = 20, pad = 2;
  const max = Math.max(...points, 1);
  const min = Math.min(...points, 0);
  const range = max - min || 1;
  const stepX = points.length > 1 ? (w - pad * 2) / (points.length - 1) : 0;
  const coords = points
    .map((v, i) => {
      const x = pad + i * stepX;
      const y = h - pad - ((v - min) / range) * (h - pad * 2);
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="shrink-0">
      <polyline
        points={coords}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

function KeywordMomentumPanel({ direction }: { direction: KeywordMomentumDirection }) {
  const { t } = useTranslation();
  const config = MOMENTUM_CONFIG[direction];
  const [period, setPeriod] = useState<"weekly" | "monthly">("weekly");
  const [sourceIds, setSourceIds] = useState<string[]>([]);
  const [categoryIds, setCategoryIds] = useState<string[]>([]);
  const toggleSource = (id: string) =>
    setSourceIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  const toggleCategory = (id: string) =>
    setCategoryIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  const { data: categories = [] } = useCategories();
  const { data, isLoading } = useKeywordMomentum(sourceIds, categoryIds, direction);

  const topics = useAnalyseTrendsStore((s) => s.topics);
  const setTopics = useAnalyseTrendsStore((s) => s.setTopics);
  const isTracked = (keyword: string) =>
    topics.some((topic) => topic.keywords.some((k) => k.toLowerCase() === keyword.toLowerCase()));
  const addToTrends = (keyword: string) => {
    if (topics.length >= MAX_TOPICS || isTracked(keyword)) return;
    setTopics([
      ...topics,
      { id: generateTopicId(), label: keyword, keywords: [keyword], color: TOPIC_COLORS[topics.length % TOPIC_COLORS.length] },
    ]);
  };

  const rows = (data ?? [])
    .map((r) => ({
      ...r,
      slope: period === "weekly" ? r.weekly_slope : r.monthly_slope,
      points: (period === "weekly" ? r.weekly_points : r.monthly_points).map((p) => p.count),
    }))
    .filter((r) => (direction === "rising" ? r.slope > 0 : r.slope < 0))
    .sort((a, b) => (direction === "rising" ? b.slope - a.slope : a.slope - b.slope))
    .slice(0, MOMENTUM_TOP_N);

  return (
    <Accordion
      title={t(config.titleKey)}
      description={t(config.descKey)}
      defaultOpen
      action={
        <div className="flex gap-1">
          <button
            onClick={() => setPeriod("weekly")}
            className={`px-2.5 py-1 text-xs rounded transition-colors ${period === "weekly" ? "bg-indigo-600 text-white" : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"}`}
          >
            {t("stats.risingWeekly")}
          </button>
          <button
            onClick={() => setPeriod("monthly")}
            className={`px-2.5 py-1 text-xs rounded transition-colors ${period === "monthly" ? "bg-indigo-600 text-white" : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"}`}
          >
            {t("stats.risingMonthly")}
          </button>
        </div>
      }
    >
      <div className="flex flex-col gap-3">
        <TrendFilterPills
          title={t("stats.filterByCategory")}
          items={categories.filter((c) => c.is_active)}
          selectedIds={categoryIds}
          onToggle={toggleCategory}
          colorOf={(id) => categories.find((c) => c.id === id)?.color}
        />
        <SourceFilterPills sourceIds={sourceIds} onToggle={toggleSource} />
      </div>

      {isLoading ? (
        <Loading />
      ) : rows.length === 0 ? (
        <div className="flex items-center justify-center h-20 text-sm text-gray-400 text-center px-4">
          {t(config.emptyKey)}
        </div>
      ) : (
        <div className="flex flex-col divide-y divide-gray-100 dark:divide-gray-800">
          {rows.map((r) => {
            const tracked = isTracked(r.keyword);
            const flagged = r[config.flagField];
            return (
              <div key={r.keyword} className="flex items-center gap-3 py-2">
                <Sparkline points={r.points} color={config.color} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{r.keyword}</span>
                    {flagged && (
                      <span className={`shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${config.badgeClass}`}>
                        {t(config.flagKey)}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    {t("stats.risingMentions", { count: r.total_mentions })}
                  </span>
                </div>
                <span className={`text-xs font-semibold tabular-nums shrink-0 ${config.percentClass}`}>
                  {r.slope >= 0 ? "+" : ""}
                  {Math.round(r.slope * 100)}%
                </span>
                <button
                  type="button"
                  onClick={() => addToTrends(r.keyword)}
                  disabled={tracked || topics.length >= MAX_TOPICS}
                  title={tracked ? t("stats.risingAlreadyTracked") : t("stats.risingAddToTrends")}
                  className="shrink-0 text-gray-400 hover:text-indigo-600 disabled:opacity-30 disabled:hover:text-gray-400 transition-colors"
                >
                  <Plus size={16} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </Accordion>
  );
}

export function AnalyseTrendsTab() {
  const { t } = useTranslation();
  const { data: categories = [] } = useCategories();
  const { data: sources = [] } = useSources();
  const { data: clusterMap = [] } = useKeywordClusterMap();
  // Persisted (localStorage) so a user's configured topics/filters/range
  // survive a reload or navigating away from this tab -- see
  // stores/analyseTrendsStore.ts.
  const topics = useAnalyseTrendsStore((s) => s.topics);
  const setTopics = useAnalyseTrendsStore((s) => s.setTopics);
  const categoryIds = useAnalyseTrendsStore((s) => s.categoryIds);
  const setCategoryIds = useAnalyseTrendsStore((s) => s.setCategoryIds);
  const sourceIds = useAnalyseTrendsStore((s) => s.sourceIds);
  const setSourceIds = useAnalyseTrendsStore((s) => s.setSourceIds);
  const days = useAnalyseTrendsStore((s) => s.days);
  const setDays = useAnalyseTrendsStore((s) => s.setDays);
  const trend = useKeywordTrend();
  const lastRequestKey = useRef<string | null>(null);

  // First-ever visit (nothing persisted yet) starts with one empty topic row
  // so there's something to type into, rather than baking a randomly-ID'd
  // topic into the store's static default state.
  useEffect(() => {
    if (topics.length === 0) setTopics([emptyTopic(0)]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateTopic = (id: string, patch: Partial<TrendTopicConfig>) =>
    setTopics(topics.map((topic) => (topic.id === id ? { ...topic, ...patch } : topic)));
  const removeTopic = (id: string) => setTopics(topics.filter((topic) => topic.id !== id));
  const addTopic = () => {
    if (topics.length < MAX_TOPICS) setTopics([...topics, emptyTopic(topics.length)]);
  };
  const addTopicFromCluster = (entry: KeywordClusterMapEntry) => {
    if (topics.length < MAX_TOPICS) {
      setTopics([
        ...topics,
        {
          id: generateTopicId(),
          label: entry.cluster_label,
          keywords: entry.keywords.map((k) => k.keyword),
          color: TOPIC_COLORS[topics.length % TOPIC_COLORS.length],
        },
      ]);
    }
  };
  const toggleCategory = (id: string) =>
    setCategoryIds(categoryIds.includes(id) ? categoryIds.filter((x) => x !== id) : [...categoryIds, id]);
  const toggleSource = (id: string) =>
    setSourceIds(sourceIds.includes(id) ? sourceIds.filter((x) => x !== id) : [...sourceIds, id]);

  const requestTopics = topics.filter((topic) => topic.keywords.length > 0);

  useEffect(() => {
    if (requestTopics.length === 0) return;
    const payload = {
      topics: requestTopics.map((topic) => ({
        label: topic.label.trim() || topic.keywords[0],
        keywords: topic.keywords,
      })),
      category_ids: categoryIds,
      source_ids: sourceIds,
      days,
    };
    const key = JSON.stringify(payload);
    if (key === lastRequestKey.current) return;
    lastRequestKey.current = key;
    trend.mutate(payload);
    // trend.mutate is stable across renders (react-query); only the payload should retrigger this.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestTopics, categoryIds, sourceIds, days]);

  return (
    <div className="flex flex-col gap-6">
      <KeywordMomentumPanel direction="rising" />
      <KeywordMomentumPanel direction="falling" />

      <Accordion
        title={t("stats.trendsTitle")}
        description={t("stats.trendsDesc")}
        defaultOpen
        action={<TrendRangePicker value={days} onChange={setDays} />}
      >
        <div className="flex flex-col gap-2">
          {topics.map((topic, i) => (
            <TopicRow
              key={topic.id}
              topic={topic}
              color={topicColor(topic, i)}
              canRemove={topics.length > 1}
              onChange={(patch) => updateTopic(topic.id, patch)}
              onRemove={() => removeTopic(topic.id)}
            />
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {topics.length < MAX_TOPICS && (
            <button
              type="button"
              onClick={addTopic}
              className="flex items-center gap-1 text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              <Plus size={13} /> {t("stats.addTrendTopic")}
            </button>
          )}
          {topics.length < MAX_TOPICS && clusterMap.length > 0 && (
            <select
              value=""
              onChange={(e) => {
                const entry = clusterMap.find((c) => c.cluster_label === e.target.value);
                if (entry) addTopicFromCluster(entry);
              }}
              className="text-xs rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-2 py-1 text-gray-500 dark:text-gray-400"
            >
              <option value="">{t("stats.importFromCluster")}</option>
              {clusterMap.map((c) => (
                <option key={c.cluster_label} value={c.cluster_label}>{c.cluster_label}</option>
              ))}
            </select>
          )}
        </div>

        <div className="flex flex-col gap-3 pt-2 border-t border-gray-100 dark:border-gray-800">
          <TrendFilterPills
            title={t("stats.filterByCategory")}
            items={categories.filter((c) => c.is_active)}
            selectedIds={categoryIds}
            onToggle={toggleCategory}
            colorOf={(id) => categories.find((c) => c.id === id)?.color}
          />
          <TrendFilterPills
            title={t("stats.filterBySource")}
            items={sources.filter((s) => s.is_active)}
            selectedIds={sourceIds}
            onToggle={toggleSource}
          />
        </div>

        {/* Chart section -- lives in the same accordion as its config above
            rather than a separate card, since the two only make sense
            together (the topics/filters/range above are exactly what this
            chart renders). */}
        <div className="flex flex-col gap-3 pt-3 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-start justify-between gap-4">
            <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">{t("stats.trendsChartDesc")}</p>
            {trend.data && (
              <button
                type="button"
                onClick={() =>
                  downloadCsv(
                    keywordTrendToCsv(trend.data),
                    `shoebill-keyword-trends-${new Date().toISOString().slice(0, 10)}.csv`
                  )
                }
                title={t("stats.exportTrendData")}
                className="shrink-0 flex items-center gap-1 text-xs text-gray-400 hover:text-indigo-600 transition-colors"
              >
                <Download size={12} />
                {t("stats.exportTrendData")}
              </button>
            )}
          </div>
          <ChartErrorBoundary>
            {requestTopics.length === 0 ? (
              <div className="flex items-center justify-center h-40 text-sm text-gray-400 text-center px-4">
                {t("stats.trendsAddTopicHint")}
              </div>
            ) : trend.isPending && !trend.data ? (
              <Loading />
            ) : trend.data && trend.data.every((r) => r.points.every((p) => p.count === 0)) ? (
              <Empty />
            ) : trend.data ? (
              <KeywordTrendChart
                results={trend.data}
                colors={requestTopics.map((topic, i) => topicColor(topic, i))}
                days={days}
              />
            ) : (
              <Loading />
            )}
          </ChartErrorBoundary>
        </div>
      </Accordion>
    </div>
  );
}
