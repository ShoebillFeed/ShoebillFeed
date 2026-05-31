import { useState, Component } from "react";
import type { ReactNode } from "react";
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
} from "../../hooks/useStats";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";

class ChartErrorBoundary extends Component<{ children: ReactNode }, { crashed: boolean }> {
  state = { crashed: false };
  static getDerivedStateFromError() { return { crashed: true }; }
  render() {
    if (this.state.crashed) {
      return (
        <div className="flex items-center justify-center h-40 text-sm text-red-400 dark:text-red-500">
          Chart failed to render.
        </div>
      );
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

function Empty() {
  return (
    <div className="flex items-center justify-center h-40 text-sm text-gray-400">
      No data for this period yet.
    </div>
  );
}

function Loading() {
  return <div className="flex items-center justify-center h-40 text-sm text-gray-400">Loading…</div>;
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

function ActivityChart({ days }: { days: number }) {
  const { data, isLoading } = useActivityStats(days);
  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  const points = data.map((d) => ({ ...d, date: fmtDate(d.date, days) }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={points} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <defs>
          {[["gFetched", "#818cf8"], ["gRead", "#34d399"], ["gStarred", "#fbbf24"]].map(([id, color]) => (
            <linearGradient key={id} id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" strokeOpacity={0.5} />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
        <Tooltip
          cursor={CURSOR_STYLE}
          wrapperStyle={WRAPPER_STYLE}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            return (
              <TooltipBox label={label as string}>
                {payload.map((p) => (
                  <TooltipRow key={String(p.name)} color={p.color} name={String(p.name ?? "")} value={p.value as number} />
                ))}
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
        <Area type="monotone" dataKey="fetched" name="Fetched" stroke="#818cf8" fill="url(#gFetched)" strokeWidth={2} dot={false} />
        <Area type="monotone" dataKey="read" name="Read" stroke="#34d399" fill="url(#gRead)" strokeWidth={2} dot={false} />
        <Area type="monotone" dataKey="starred" name="Starred ★" stroke="#fbbf24" fill="url(#gStarred)" strokeWidth={2} dot={false} />
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
    return (
      <div className="flex flex-col items-center justify-center h-40 gap-1 text-sm text-gray-400">
        <span>No weight history yet.</span>
        <span className="text-xs">Star some articles to start recording.</span>
      </div>
    );
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
                      name={String(p.name ?? "")}
                      value={typeof p.value === "number" ? p.value.toFixed(3) : ""}
                    />
                  ))}
              </TooltipBox>
            );
          }}
        />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
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

// ── Main panel ────────────────────────────────────────────────────────────────

export default function StatsPanel() {
  const [activityDays, setActivityDays] = useState(30);
  const [categoryDays, setCategoryDays] = useState(30);
  const [sourceDays, setSourceDays] = useState(30);
  const [weightDays, setWeightDays] = useState(60);
  const [clusterDays, setClusterDays] = useState(30);

  const { data: settings } = useAdvancedSettings();
  const update = useUpdateAdvancedSettings();
  const statsEnabled = settings?.stats_enabled ?? true;

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="font-semibold text-gray-900 dark:text-gray-100">Statistics</h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Insight into your reading habits and feed activity.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0 ml-4">
          {!statsEnabled && (
            <span className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
              <PauseCircle size={13} /> Recording paused
            </span>
          )}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">Record history</span>
            <button
              role="switch"
              aria-checked={statsEnabled}
              title={statsEnabled ? "Pause statistics recording" : "Resume statistics recording"}
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
          title="Reading activity"
          description="Daily count of articles fetched, read, and starred. The gap between Fetched and Read shows your backlog; the Starred line reflects how often you find content worth keeping."
          action={<RangePicker value={activityDays} onChange={setActivityDays} />}
        >
          <ActivityChart key={activityDays} days={activityDays} />
        </ChartCard>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ChartCard
            title="Articles by category"
            description="How many articles were assigned to each category in the selected period."
            action={<RangePicker value={categoryDays} onChange={setCategoryDays} />}
          >
            <ByCategoryChart key={categoryDays} days={categoryDays} />
          </ChartCard>

          <ChartCard
            title="Articles by source"
            description="Volume per source. Hover a bar to see the category breakdown for that source."
            action={<RangePicker value={sourceDays} onChange={setSourceDays} />}
          >
            <BySourceChart key={sourceDays} days={sourceDays} />
          </ChartCard>
        </div>

        <ChartCard
          title="Source co-clustering"
          description="Which pairs of sources most often cover the same story (appear in the same cluster), broken down by category. High overlap means two sources report on the same topics."
          action={<RangePicker value={clusterDays} onChange={setClusterDays} />}
        >
          <SourceClustersChart key={clusterDays} days={clusterDays} />
        </ChartCard>

        <ChartCard
          title="Category weight history"
          description="How each category's learned relevance score has grown over time. Steeper curves mean you're consistently finding that category relevant. Requires recording to be enabled."
          action={<RangePicker value={weightDays} onChange={setWeightDays} />}
        >
          <WeightHistoryChart key={weightDays} days={weightDays} />
        </ChartCard>
      </div>
    </div>
  );
}
