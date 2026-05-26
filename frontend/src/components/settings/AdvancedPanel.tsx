import { useState, useEffect } from "react";
import { useAdvancedSettings, useUpdateAdvancedSettings } from "../../hooks/useSettings";
import { usePreferencesStore } from "../../stores/preferencesStore";

const inputClass =
  "w-24 px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <div className="mb-3">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
        {description && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>}
      </div>
      <div className="border-t border-gray-200 dark:border-gray-700 pt-4 flex flex-col gap-4">{children}</div>
    </div>
  );
}

function Field({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-4">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{label}</p>
        {description && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</p>}
      </div>
      {children}
    </div>
  );
}

function NumericField({
  label,
  description,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  description?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  const [local, setLocal] = useState(String(value));

  useEffect(() => setLocal(String(value)), [value]);

  const commit = () => {
    const n = parseFloat(local);
    if (!isNaN(n) && n >= min && n <= max) {
      onChange(n);
    } else {
      setLocal(String(value));
    }
  };

  return (
    <Field label={label} description={description}>
      <input
        type="number"
        className={inputClass}
        value={local}
        min={min}
        max={max}
        step={step}
        onChange={(e) => setLocal(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => e.key === "Enter" && commit()}
      />
    </Field>
  );
}

export default function AdvancedPanel() {
  const { data: settings, isLoading } = useAdvancedSettings();
  const update = useUpdateAdvancedSettings();
  const { autoLabelOnRead, setAutoLabelOnRead } = usePreferencesStore();

  if (isLoading) return <p className="text-sm text-gray-400">Loading…</p>;
  if (!settings) return null;

  const base = settings.weight_base;
  const mult = settings.weight_log_multiplier;

  return (
    <div>
      <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-6">Advanced</h2>

      <Section title="Reading">
        <Field
          label="Auto-star on read"
          description="Automatically mark an article as relevant (★) when you open it. The star is highlighted so you can undo immediately."
        >
          <input
            type="checkbox"
            checked={autoLabelOnRead}
            onChange={(e) => setAutoLabelOnRead(e.target.checked)}
            className="mt-1 rounded accent-indigo-600 cursor-pointer"
          />
        </Field>
      </Section>


      <Section
        title="Category Learning"
        description={`Each time you star an article, its categories gain a learned score: base + log(1 + stars) × rate. With current settings: ${[1, 5, 10, 25].map((n) => `${n}★ → ${(base + Math.log1p(n) * mult).toFixed(2)}`).join(", ")}.`}
      >
        <NumericField
          label="Starting score"
          description="Score a category has before you've starred anything. Higher values make all categories carry more weight from the start. Default: 1.0"
          value={settings.weight_base}
          min={0}
          max={10}
          step={0.1}
          onChange={(v) => update.mutate({ weight_base: v })}
        />
        <NumericField
          label="Learning rate"
          description="How fast a category's score grows as you star more articles. Higher = steeper curve. Default: 0.5"
          value={settings.weight_log_multiplier}
          min={0}
          max={5}
          step={0.05}
          onChange={(v) => update.mutate({ weight_log_multiplier: v })}
        />
      </Section>

      <Section
        title="Relevant Tab Ranking"
        description="The Relevant tab score combines the AI's rating, your reading history, and a bonus for widely-covered stories. Each factor can be scaled or disabled independently."
      >
        <NumericField
          label="AI rating influence"
          description="How much the AI's 1–10 relevance score counts. Set to 0 to rank purely by your own history. Default: 1.0"
          value={settings.relevance_llm_weight}
          min={0}
          max={5}
          step={0.1}
          onChange={(v) => update.mutate({ relevance_llm_weight: v })}
        />
        <NumericField
          label="Learning influence"
          description="How strongly your starred articles and keywords shape the ranking. 0 = off, 1 = normal, 2 = amplified. Default: 1.0"
          value={settings.relevance_learning_weight}
          min={0}
          max={5}
          step={0.1}
          onChange={(v) => update.mutate({ relevance_learning_weight: v })}
        />
        <NumericField
          label="Multi-source bonus"
          description="Extra score for stories covered by several sources simultaneously. 0 = disabled. Default: 0.5"
          value={settings.relevance_cluster_weight}
          min={0}
          max={5}
          step={0.05}
          onChange={(v) => update.mutate({ relevance_cluster_weight: v })}
        />
      </Section>

      {update.isSuccess && (
        <p className="text-xs text-green-600 dark:text-green-400 mt-2">Settings saved.</p>
      )}
      {update.isError && (
        <p className="text-xs text-red-500 mt-2">Failed to save settings.</p>
      )}
    </div>
  );
}
