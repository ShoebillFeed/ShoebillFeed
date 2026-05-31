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
import { useActivityStats, useCategoryStats, useSourceStats, useWeightHistory } from "../../hooks/useStats";
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
  children: React.ReactNode;
  action?: React.ReactNode;
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
  return (
    <div className="flex items-center justify-center h-40 text-sm text-gray-400">Loading…</div>
  );
}

const TOOLTIP_STYLE = {
  contentStyle: {
    border: "1px solid #e5e7eb",
    borderRadius: 6,
    fontSize: 12,
  },
};

function fmtDate(iso: string, days: number) {
  try {
    return format(parseISO(iso), days <= 7 ? "EEE d" : "MMM d");
  } catch {
    return iso;
  }
}

// ── Reading activity ─────────────────────────────────────────────────────────

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
        <Tooltip {...TOOLTIP_STYLE} />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
        <Area type="monotone" dataKey="fetched" name="Fetched" stroke="#818cf8" fill="url(#gFetched)" strokeWidth={2} dot={false} />
        <Area type="monotone" dataKey="read" name="Read" stroke="#34d399" fill="url(#gRead)" strokeWidth={2} dot={false} />
        <Area type="monotone" dataKey="starred" name="Starred ★" stroke="#fbbf24" fill="url(#gStarred)" strokeWidth={2} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ── Volume by category ───────────────────────────────────────────────────────

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
        <Tooltip {...TOOLTIP_STYLE} formatter={(v) => [v, "articles"]} />
        <Bar dataKey="count" name="Articles" radius={[0, 4, 4, 0]}>
          {data.map((entry) => (
            <Cell key={entry.id} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Volume by source ─────────────────────────────────────────────────────────

function BySourceChart({ days }: { days: number }) {
  const { data, isLoading } = useSourceStats(days);

  if (isLoading) return <Loading />;
  if (!data?.length) return <Empty />;

  // Collect all unique categories across all sources (stable order: by first appearance)
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

  // Shape data for recharts stacked bar: one row per source, one key per category name
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
          {...TOOLTIP_STYLE}
          formatter={(value, catName, props) => {
            const p = props.payload as Record<string, unknown> | undefined;
            const sourceType = p ? (SOURCE_TYPE_LABEL[p.source_type as string] ?? p.source_type as string) : "";
            const label = sourceType ? `${catName} — ${p?.name} (${sourceType})` : String(catName);
            return [value, label];
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

// ── Category weight history ──────────────────────────────────────────────────

function WeightHistoryChart({ days }: { days: number }) {
  const { data, isLoading } = useWeightHistory(days);

  if (isLoading) return <Loading />;
  if (!data?.length) return (
    <div className="flex flex-col items-center justify-center h-40 gap-1 text-sm text-gray-400">
      <span>No weight history yet.</span>
      <span className="text-xs">Star some articles to start recording.</span>
    </div>
  );

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
        <Tooltip {...TOOLTIP_STYLE} formatter={(v) => [typeof v === "number" ? v.toFixed(3) : "", ""]} />
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
        {data.map((cat) => (
          <Line key={cat.id} type="monotone" dataKey={cat.name} stroke={cat.color} strokeWidth={2} dot={false} connectNulls />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── Main panel ───────────────────────────────────────────────────────────────

export default function StatsPanel() {
  const [activityDays, setActivityDays] = useState(30);
  const [categoryDays, setCategoryDays] = useState(30);
  const [sourceDays, setSourceDays] = useState(30);
  const [weightDays, setWeightDays] = useState(60);

  const { data: settings } = useAdvancedSettings();
  const update = useUpdateAdvancedSettings();
  const statsEnabled = settings?.stats_enabled ?? true;

  const toggleStats = () => {
    update.mutate({ stats_enabled: !statsEnabled });
  };

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="font-semibold text-gray-900 dark:text-gray-100">Statistics</h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Insight into your reading habits and feed activity.
          </p>
        </div>

        {/* Recording toggle */}
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
              onClick={toggleStats}
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
            description="How many articles were assigned to each category in the selected period. Longer bars mean that category's topics are being covered more heavily by your sources."
            action={<RangePicker value={categoryDays} onChange={setCategoryDays} />}
          >
            <ByCategoryChart key={categoryDays} days={categoryDays} />
          </ChartCard>

          <ChartCard
            title="Articles by source"
            description="Volume of articles per source. Use this to spot sources that are too noisy (very high count) or not contributing much (low count) and adjust them in Sources settings."
            action={<RangePicker value={sourceDays} onChange={setSourceDays} />}
          >
            <BySourceChart key={sourceDays} days={sourceDays} />
          </ChartCard>
        </div>

        <ChartCard
          title="Category weight history"
          description="How each category's learned relevance score has grown over time. A score is recorded each time you star an article. Steeper curves mean you're consistently finding that category relevant; flat lines mean little recent activity. Requires recording to be enabled."
          action={<RangePicker value={weightDays} onChange={setWeightDays} />}
        >
          <WeightHistoryChart key={weightDays} days={weightDays} />
        </ChartCard>
      </div>
    </div>
  );
}
